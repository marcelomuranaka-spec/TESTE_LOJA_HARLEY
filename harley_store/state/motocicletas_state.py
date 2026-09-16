"""
State da tela Motocicletas (tabela `motos` no Xano).

Cada registro é UMA motocicleta — estoque é controlado por unidade (status +
em_estoque), não por quantidade. Convive em paralelo com a tela "Motos dos
clientes" (`motos_state.py` / tabela `motos_clientes`), que continua servindo
ordens de serviço e vendas.

Decisões (ver openspec/changes/cadastro-motocicletas/design.md):

- Ao abrir a tela são feitos só 2 GETs (motos + clientes). Busca, filtros,
  opções dos selects e cards são calculados em memória (`@rx.var`), para não
  gastar requisições do plano Free a cada mudança de filtro.
- A foto selecionada fica num arquivo temporário local (`tmp_moto_*`) só para
  a prévia; ela só é enviada ao armazenamento do Xano quando o usuário salva.
  O registro guarda os metadados devolvidos pelo Xano.
- PATCH do Xano exige o registro completo: `salvar` sempre monta o payload
  inteiro, reenviando a foto atual quando ela não mudou.
"""

import datetime
import re
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

import httpx
import reflex as rx

from .. import xano_client as xano

TABELA = "motos"
TABELA_CLIENTES = "clientes"
ROTA_UPLOAD_FOTO = "motos/foto"

STATUS_MOTO = ["Em estoque", "Reservada", "Em manutenção", "Vendida", "Entregue"]
STATUS_FORA_DO_ESTOQUE = {"Vendida", "Entregue"}
STATUS_EM_ESTOQUE = "Em estoque"

SEM_CLIENTE = "Sem cliente"
TODAS_MARCAS = "Todas as marcas"
TODOS_MODELOS = "Todos os modelos"
TODOS_ANOS = "Todos os anos"
TODOS_STATUS = "Todos os status"
TODOS_CLIENTES = "Todos os clientes"
ESTOQUE_TODOS = "Todos"
ESTOQUE_DENTRO = "Em estoque"
ESTOQUE_FORA = "Fora do estoque"
OPCOES_ESTOQUE = [ESTOQUE_TODOS, ESTOQUE_DENTRO, ESTOQUE_FORA]

TIPOS_FOTO_PERMITIDOS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024  # 5 MB — mesmo limite das outras telas
PREFIXO_TEMP_FOTO = "tmp_moto_"
IDADE_MAXIMA_TEMP_SEGUNDOS = 24 * 60 * 60

# Tabelas/campos que referenciam `motos.id`. Vazia hoje: nenhuma tabela tem
# `moto_id`. Quando `ordens_servico.moto_id` existir, acrescentar
# ("ordens_servico", "moto_id") aqui E a precondition no DELETE do Xano.
REFERENCIAS_MOTO: list[tuple[str, str]] = []

REGEX_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")  # AAA9999 ou Mercosul AAA9A99
REGEX_CHASSI = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")  # 17 caracteres, sem I, O e Q

MSG_PLACA_DUPLICADA = "Já existe uma motocicleta cadastrada com esta placa."
MSG_CHASSI_DUPLICADO = "Já existe uma motocicleta cadastrada com este chassi."
MSG_VINCULOS = "Esta motocicleta possui registros vinculados e não pode ser excluída."


def normalizar_identificador(valor: object) -> str:
    """Placa/chassi: maiúsculas, sem espaços e sem hífens."""
    return re.sub(r"[\s\-]", "", xano.texto(valor)).upper()


def interpretar_moeda(valor: str) -> Optional[float]:
    """Converte "12.500,50", "12500,50", "12500.50" ou "R$ 12.500" em float.

    Vazio vira None (campo opcional). Texto inválido levanta ValueError.
    O sinal de menos não é aceito: valores negativos são inválidos.
    """
    bruto = valor.replace("R$", "").replace(" ", "").strip()
    if not bruto:
        return None
    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", bruto):
        bruto = bruto.replace(".", "")  # "12.500" = doze mil e quinhentos
    if not re.fullmatch(r"\d+(\.\d{1,2})?", bruto):
        raise ValueError(valor)
    return float(bruto)


def formatar_moeda(valor: Optional[float]) -> str:
    if valor is None:
        return "—"
    return "R$ " + f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def preco_informado(valor: object) -> Optional[float]:
    """Preço vindo do Xano, ou None se não informado.

    O Xano grava `null` enviado num campo decimal como 0 (conferido em
    2026-09-16), então 0 também significa "sem preço" — moto a preço zero não
    é um caso real da loja.
    """
    numero = xano.numero(valor)
    return numero if numero > 0 else None


def moeda_para_campo(valor: object) -> str:
    """Valor do Xano para o campo de texto do formulário ("12500,50")."""
    numero = preco_informado(valor)
    if numero is None:
        return ""
    return f"{numero:.2f}".replace(".", ",")


def data_para_campo(valor: object) -> str:
    """Epoch ms do Xano para o valor de <input type=date> ("AAAA-MM-DD")."""
    if not valor:
        return ""
    return xano.epoch_ms_para_datetime(valor).strftime("%Y-%m-%d")


def campo_para_epoch_ms(valor: str) -> Optional[int]:
    if not valor:
        return None
    return xano.datetime_para_epoch_ms(datetime.datetime.strptime(valor, "%Y-%m-%d"))


def _opcao_cliente(cliente_id: object, nome: str) -> str:
    return f"{cliente_id} - {nome}"


def _id_da_opcao(opcao: str) -> Optional[int]:
    if not opcao or opcao in (SEM_CLIENTE, TODOS_CLIENTES):
        return None
    try:
        return int(opcao.split(" - ")[0])
    except ValueError:
        return None


class MotocicletasState(rx.State):
    # Dados vindos do Xano (já normalizados para exibição)
    motos: list[dict] = []
    clientes: list[dict] = []  # [{"id": "3", "nome": "João"}]
    carregando: bool = True
    erro_carregamento: bool = False

    # Registros crus do Xano por id — só no servidor (não vai ao navegador)
    _registros: dict[str, dict] = {}

    # Busca e filtros
    busca: str = ""
    filtro_marca: str = TODAS_MARCAS
    filtro_modelo: str = TODOS_MODELOS
    filtro_ano: str = TODOS_ANOS
    filtro_status: str = TODOS_STATUS
    filtro_estoque: str = ESTOQUE_TODOS
    filtro_cliente: str = TODOS_CLIENTES

    # Formulário
    dialogo_aberto: bool = False
    salvando: bool = False
    erro_form: str = ""
    form_id: Optional[int] = None
    marca: str = ""
    modelo: str = ""
    ano: str = ""
    cor: str = ""
    placa: str = ""
    chassi: str = ""
    quilometragem: str = "0"
    status: str = STATUS_EM_ESTOQUE
    em_estoque: bool = True
    preco_compra: str = ""
    preco_venda: str = ""
    cliente_selecionado: str = SEM_CLIENTE
    pesquisa_cliente: str = ""
    data_entrada: str = ""
    data_saida_ms: Optional[int] = None
    observacoes: str = ""

    # Foto: metadados atuais (Xano) + arquivo temporário da prévia
    foto_atual: dict = {}
    foto_atual_url: str = ""
    foto_temp: str = ""
    erro_foto: str = ""

    # Foto ampliada (lightbox)
    foto_ampliada_url: str = ""

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------

    @rx.event
    async def carregar(self):
        self.carregando = True
        yield
        await self._buscar_dados()
        self.carregando = False

    async def _buscar_dados(self):
        _limpar_temporarios_antigos()
        try:
            registros = await xano.listar(TABELA)
        except (httpx.HTTPError, ValueError):
            self.erro_carregamento = True
            self.motos = []
            self._registros = {}
            return
        self.erro_carregamento = False

        try:
            clientes = await xano.listar(TABELA_CLIENTES)
        except (httpx.HTTPError, ValueError):
            clientes = []  # sem clientes a tela ainda funciona; o nome vira "Cliente #id"
        clientes = sorted(clientes, key=lambda c: xano.texto(c.get("nome_cliente")).lower())
        self.clientes = [
            {"id": str(c["id"]), "nome": xano.texto(c.get("nome_cliente"))} for c in clientes
        ]
        nomes_por_id = {c["id"]: c["nome"] for c in self.clientes}

        registros = sorted(
            registros,
            key=lambda r: (xano.texto(r.get("marca")).lower(), xano.texto(r.get("modelo")).lower()),
        )
        self._registros = {str(r["id"]): r for r in registros}
        self.motos = [_linha_da_tabela(r, nomes_por_id) for r in registros]

    # ------------------------------------------------------------------
    # Filtros e resumo (calculados em memória)
    # ------------------------------------------------------------------

    @rx.var
    def motos_filtradas(self) -> list[dict]:
        termo = self.busca.strip().lower()
        id_cliente = _id_da_opcao(self.filtro_cliente)
        resultado = []
        for m in self.motos:
            if termo and termo not in m["texto_busca"]:
                continue
            if self.filtro_marca != TODAS_MARCAS and m["marca"] != self.filtro_marca:
                continue
            if self.filtro_modelo != TODOS_MODELOS and m["modelo"] != self.filtro_modelo:
                continue
            if self.filtro_ano != TODOS_ANOS and m["ano"] != self.filtro_ano:
                continue
            if self.filtro_status != TODOS_STATUS and m["status"] != self.filtro_status:
                continue
            if self.filtro_estoque == ESTOQUE_DENTRO and m["estoque"] != "Sim":
                continue
            if self.filtro_estoque == ESTOQUE_FORA and m["estoque"] == "Sim":
                continue
            if self.filtro_cliente == SEM_CLIENTE and m["cliente_id"] != "":
                continue
            if id_cliente is not None and m["cliente_id"] != str(id_cliente):
                continue
            resultado.append(m)
        return resultado

    @rx.var
    def opcoes_marca(self) -> list[str]:
        return [TODAS_MARCAS] + sorted({m["marca"] for m in self.motos if m["marca"]}, key=str.lower)

    @rx.var
    def opcoes_modelo(self) -> list[str]:
        # Com uma marca escolhida, mostra só os modelos dela
        motos = [
            m for m in self.motos if self.filtro_marca == TODAS_MARCAS or m["marca"] == self.filtro_marca
        ]
        return [TODOS_MODELOS] + sorted({m["modelo"] for m in motos if m["modelo"]}, key=str.lower)

    @rx.var
    def opcoes_ano(self) -> list[str]:
        return [TODOS_ANOS] + sorted({m["ano"] for m in self.motos if m["ano"]}, reverse=True)

    @rx.var
    def opcoes_cliente_filtro(self) -> list[str]:
        return [TODOS_CLIENTES, SEM_CLIENTE] + [_opcao_cliente(c["id"], c["nome"]) for c in self.clientes]

    @rx.var
    def opcoes_cliente_form(self) -> list[str]:
        termo = self.pesquisa_cliente.strip().lower()
        opcoes = [
            _opcao_cliente(c["id"], c["nome"])
            for c in self.clientes
            if not termo or termo in c["nome"].lower()
        ]
        # O cliente já escolhido continua na lista mesmo fora da pesquisa,
        # senão o select fica sem valor visível.
        if self.cliente_selecionado != SEM_CLIENTE and self.cliente_selecionado not in opcoes:
            opcoes.insert(0, self.cliente_selecionado)
        return [SEM_CLIENTE] + opcoes

    @rx.var
    def ha_filtro_ativo(self) -> bool:
        return bool(self.busca.strip()) or (
            self.filtro_marca,
            self.filtro_modelo,
            self.filtro_ano,
            self.filtro_status,
            self.filtro_estoque,
            self.filtro_cliente,
        ) != (TODAS_MARCAS, TODOS_MODELOS, TODOS_ANOS, TODOS_STATUS, ESTOQUE_TODOS, TODOS_CLIENTES)

    @rx.var
    def total_motos(self) -> int:
        return len(self.motos)

    @rx.var
    def total_em_estoque(self) -> int:
        return sum(1 for m in self.motos if m["estoque"] == "Sim")

    @rx.var
    def total_reservadas(self) -> int:
        return sum(1 for m in self.motos if m["status"] == "Reservada")

    @rx.var
    def total_manutencao(self) -> int:
        return sum(1 for m in self.motos if m["status"] == "Em manutenção")

    @rx.var
    def total_vendidas(self) -> int:
        return sum(1 for m in self.motos if m["status"] in STATUS_FORA_DO_ESTOQUE)

    @rx.var
    def status_define_estoque(self) -> bool:
        """Quando o status já determina o estoque, o switch fica travado."""
        return self.status == STATUS_EM_ESTOQUE or self.status in STATUS_FORA_DO_ESTOQUE

    @rx.event
    def definir_filtro_marca(self, valor: str):
        self.filtro_marca = valor
        self.filtro_modelo = TODOS_MODELOS  # o modelo anterior pode não existir na marca nova

    @rx.event
    def limpar_filtros(self):
        self.busca = ""
        self.filtro_marca = TODAS_MARCAS
        self.filtro_modelo = TODOS_MODELOS
        self.filtro_ano = TODOS_ANOS
        self.filtro_status = TODOS_STATUS
        self.filtro_estoque = ESTOQUE_TODOS
        self.filtro_cliente = TODOS_CLIENTES

    # ------------------------------------------------------------------
    # Formulário
    # ------------------------------------------------------------------

    def _limpar_formulario(self):
        self._apagar_temporario()
        self.form_id = None
        self.erro_form = ""
        self.marca = ""
        self.modelo = ""
        self.ano = ""
        self.cor = ""
        self.placa = ""
        self.chassi = ""
        self.quilometragem = "0"
        self.status = STATUS_EM_ESTOQUE
        self.em_estoque = True
        self.preco_compra = ""
        self.preco_venda = ""
        self.cliente_selecionado = SEM_CLIENTE
        self.pesquisa_cliente = ""
        self.data_entrada = datetime.date.today().strftime("%Y-%m-%d")
        self.data_saida_ms = None
        self.observacoes = ""
        self.foto_atual = {}
        self.foto_atual_url = ""
        self.erro_foto = ""

    @rx.event
    def abrir_cadastro(self):
        self._limpar_formulario()
        self.dialogo_aberto = True

    @rx.event
    def abrir_edicao(self, moto_id: str):
        registro = self._registros.get(str(moto_id))
        if registro is None:
            return rx.toast.error("Motocicleta não encontrada. Recarregue a página.")
        self._limpar_formulario()
        self.form_id = int(registro["id"])
        self.marca = xano.texto(registro.get("marca"))
        self.modelo = xano.texto(registro.get("modelo"))
        self.ano = str(xano.inteiro(registro.get("ano"))) if registro.get("ano") else ""
        self.cor = xano.texto(registro.get("cor"))
        self.placa = xano.texto(registro.get("placa"))
        self.chassi = xano.texto(registro.get("chassi"))
        self.quilometragem = str(xano.inteiro(registro.get("quilometragem")))
        self.status = xano.texto(registro.get("status")) or STATUS_EM_ESTOQUE
        self.em_estoque = bool(registro.get("em_estoque"))
        self.preco_compra = moeda_para_campo(registro.get("preco_compra"))
        self.preco_venda = moeda_para_campo(registro.get("preco_venda"))
        cliente_id = registro.get("cliente_id")
        if cliente_id:
            nome = next((c["nome"] for c in self.clientes if c["id"] == str(cliente_id)), f"Cliente #{cliente_id}")
            self.cliente_selecionado = _opcao_cliente(cliente_id, nome)
        self.data_entrada = data_para_campo(registro.get("data_entrada"))
        self.data_saida_ms = xano.inteiro(registro.get("data_saida")) or None
        self.observacoes = xano.texto(registro.get("observacoes"))
        foto = registro.get("foto")
        self.foto_atual = foto if isinstance(foto, dict) else {}
        self.foto_atual_url = xano.url_arquivo(self.foto_atual)
        self.dialogo_aberto = True

    @rx.event
    def cancelar(self):
        self._limpar_formulario()
        self.dialogo_aberto = False

    @rx.event
    def alternar_dialogo(self, aberto: bool):
        # Fechar pelo X, pelo Esc ou clicando fora equivale a cancelar
        if not aberto:
            self.cancelar()

    @rx.event
    def definir_status(self, valor: str):
        self.status = valor
        if valor == STATUS_EM_ESTOQUE:
            self.em_estoque = True
        elif valor in STATUS_FORA_DO_ESTOQUE:
            self.em_estoque = False

    # ------------------------------------------------------------------
    # Foto
    # ------------------------------------------------------------------

    def _apagar_temporario(self):
        if self.foto_temp:
            (rx.get_upload_dir() / self.foto_temp).unlink(missing_ok=True)
            self.foto_temp = ""

    @rx.event
    async def handle_upload_foto(self, files: list[rx.UploadFile]):
        """Guarda a foto escolhida num temporário local só para a prévia.
        Em caso de arquivo inválido, a foto que já estava no formulário fica."""
        self.erro_foto = ""
        if not files:
            return
        arquivo = files[0]
        extensao = Path(arquivo.name or "").suffix.lower()
        if extensao not in TIPOS_FOTO_PERMITIDOS:
            self.erro_foto = "Formato inválido. Use JPG, JPEG, PNG ou WEBP."
            return
        conteudo = await arquivo.read()
        if len(conteudo) > TAMANHO_MAXIMO_FOTO:
            self.erro_foto = "Imagem muito grande (máximo 5 MB)."
            return
        self._apagar_temporario()
        nome_arquivo = f"{PREFIXO_TEMP_FOTO}{uuid4().hex}{extensao}"
        (rx.get_upload_dir() / nome_arquivo).write_bytes(conteudo)
        self.foto_temp = nome_arquivo

    @rx.event
    def remover_foto(self):
        self._apagar_temporario()
        self.foto_atual = {}
        self.foto_atual_url = ""
        self.erro_foto = ""

    @rx.event
    def ampliar_foto(self, url: str):
        self.foto_ampliada_url = url

    @rx.event
    def alternar_foto_ampliada(self, aberto: bool):
        if not aberto:
            self.foto_ampliada_url = ""

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _validar(self) -> tuple[Optional[dict], str]:
        """Valida e normaliza o formulário. Devolve (dados, "") ou (None, erro)."""
        marca = self.marca.strip()
        modelo = self.modelo.strip()
        if not marca or not modelo or not self.ano.strip():
            return None, "Marca, modelo e ano são obrigatórios."

        ano_texto = self.ano.strip()
        ano_maximo = datetime.date.today().year + 1
        if not ano_texto.isdigit() or not 1900 <= int(ano_texto) <= ano_maximo:
            return None, f"Ano inválido: informe um número entre 1900 e {ano_maximo}."

        km_texto = self.quilometragem.strip().replace(".", "")
        if km_texto and not km_texto.isdigit():
            return None, "Quilometragem inválida: use somente números (sem valores negativos)."

        placa = normalizar_identificador(self.placa)
        if placa and not REGEX_PLACA.fullmatch(placa):
            return None, "Placa inválida. Use o formato ABC1234 ou Mercosul ABC1D23."

        chassi = normalizar_identificador(self.chassi)
        if chassi and not REGEX_CHASSI.fullmatch(chassi):
            return None, "Chassi inválido: deve ter 17 letras/números, sem I, O ou Q."

        try:
            preco_compra = interpretar_moeda(self.preco_compra)
        except ValueError:
            return None, "Preço de compra inválido: informe um valor como 12.500,00 (sem negativos)."
        try:
            preco_venda = interpretar_moeda(self.preco_venda)
        except ValueError:
            return None, "Preço de venda inválido: informe um valor como 12.500,00 (sem negativos)."

        try:
            data_entrada = campo_para_epoch_ms(self.data_entrada)
        except ValueError:
            return None, "Data de entrada inválida."

        # Regra de estoque por unidade (spec "Controle de estoque por unidade")
        status = self.status if self.status in STATUS_MOTO else STATUS_EM_ESTOQUE
        if status in STATUS_FORA_DO_ESTOQUE:
            em_estoque = False
            data_saida = self.data_saida_ms or xano.datetime_para_epoch_ms()
        elif status == STATUS_EM_ESTOQUE:
            em_estoque = True
            data_saida = None
        else:
            em_estoque = self.em_estoque
            data_saida = self.data_saida_ms

        dados = {
            "cliente_id": _id_da_opcao(self.cliente_selecionado),
            "marca": marca,
            "modelo": modelo,
            "ano": int(ano_texto),
            "cor": self.cor.strip() or None,
            "placa": placa or None,
            "chassi": chassi or None,
            "quilometragem": int(km_texto) if km_texto else 0,
            "status": status,
            "em_estoque": em_estoque,
            "preco_compra": preco_compra,
            "preco_venda": preco_venda,
            "data_entrada": data_entrada,
            "data_saida": data_saida,
            "observacoes": self.observacoes.strip() or None,
        }
        return dados, ""

    @rx.event
    async def salvar(self):
        dados, erro = self._validar()
        if dados is None:
            self.erro_form = erro
            return
        self.erro_form = ""
        self.salvando = True
        yield

        try:
            # Duplicidade conferida numa lista recém-buscada (a da tela pode estar velha)
            for r in await xano.listar(TABELA):
                if self.form_id is not None and str(r.get("id")) == str(self.form_id):
                    continue
                if dados["placa"] and normalizar_identificador(r.get("placa")) == dados["placa"]:
                    self.erro_form = MSG_PLACA_DUPLICADA
                    return
                if dados["chassi"] and normalizar_identificador(r.get("chassi")) == dados["chassi"]:
                    self.erro_form = MSG_CHASSI_DUPLICADO
                    return

            # Foto: nova → envia ao Xano; sem mudança → reenvia a atual; removida → null
            if self.foto_temp:
                caminho = rx.get_upload_dir() / self.foto_temp
                extensao = caminho.suffix.lower()
                try:
                    dados["foto"] = await xano.enviar_foto(
                        ROTA_UPLOAD_FOTO,
                        caminho.read_bytes(),
                        f"moto{extensao}",
                        TIPOS_FOTO_PERMITIDOS[extensao],
                    )
                except (httpx.HTTPError, ValueError, OSError):
                    self.erro_form = "Não foi possível enviar a foto. A motocicleta não foi salva; tente novamente."
                    return
            else:
                dados["foto"] = self.foto_atual or None

            dados["updated_at"] = xano.datetime_para_epoch_ms()
            if self.form_id is None:
                await xano.criar(TABELA, dados)
                mensagem = "Motocicleta cadastrada com sucesso."
            else:
                await xano.atualizar(TABELA, self.form_id, dados)
                mensagem = "Motocicleta atualizada com sucesso."
        except (httpx.HTTPError, ValueError):
            self.erro_form = "Não foi possível salvar a motocicleta. Verifique a conexão e tente novamente."
            return
        finally:
            self.salvando = False

        self._limpar_formulario()
        self.dialogo_aberto = False
        await self._buscar_dados()
        yield rx.toast.success(mensagem)

    # ------------------------------------------------------------------
    # Excluir
    # ------------------------------------------------------------------

    @rx.event
    async def excluir(self, moto_id: str):
        try:
            for tabela, campo in REFERENCIAS_MOTO:
                if any(xano.inteiro(r.get(campo)) == int(moto_id) for r in await xano.listar(tabela)):
                    yield rx.toast.error(MSG_VINCULOS)
                    return
            await xano.excluir(TABELA, int(moto_id))
        except httpx.HTTPStatusError as erro:
            # Xano recusou (ex.: precondition futura de vínculo com OS)
            mensagem = MSG_VINCULOS if erro.response.status_code in (400, 403, 409) else (
                "Não foi possível excluir a motocicleta. Tente novamente."
            )
            yield rx.toast.error(mensagem)
            return
        except (httpx.HTTPError, ValueError):
            yield rx.toast.error("Não foi possível excluir a motocicleta. Verifique a conexão e tente novamente.")
            return

        await self._buscar_dados()
        yield rx.toast.success("Motocicleta excluída com sucesso.")


def _linha_da_tabela(r: dict, nomes_por_id: dict[str, str]) -> dict:
    """Registro do Xano → linha pronta para exibir (só strings)."""
    cliente_id = str(r["cliente_id"]) if r.get("cliente_id") else ""
    if cliente_id:
        cliente_nome = nomes_por_id.get(cliente_id, f"Cliente #{cliente_id}")
    else:
        cliente_nome = SEM_CLIENTE
    km = xano.inteiro(r.get("quilometragem"))
    linha = {
        "id": str(r["id"]),
        "foto_url": xano.url_arquivo(r.get("foto")),
        "marca": xano.texto(r.get("marca")),
        "modelo": xano.texto(r.get("modelo")),
        "ano": str(xano.inteiro(r.get("ano"))) if r.get("ano") else "",
        "cor": xano.texto(r.get("cor")),
        "placa": xano.texto(r.get("placa")),
        "chassi": xano.texto(r.get("chassi")),
        "cliente_id": cliente_id,
        "cliente_nome": cliente_nome,
        "km": f"{km:,}".replace(",", ".") + " km",
        "status": xano.texto(r.get("status")) or STATUS_EM_ESTOQUE,
        "estoque": "Sim" if r.get("em_estoque") else "Não",
        "preco": formatar_moeda(preco_informado(r.get("preco_venda"))),
    }
    linha["texto_busca"] = " ".join(
        linha[c] for c in ("marca", "modelo", "placa", "chassi", "cor", "cliente_nome")
    ).lower()
    return linha


def _limpar_temporarios_antigos():
    """Apaga prévias de foto abandonadas (sessão caiu antes de salvar/cancelar)."""
    limite = time.time() - IDADE_MAXIMA_TEMP_SEGUNDOS
    for arquivo in rx.get_upload_dir().glob(f"{PREFIXO_TEMP_FOTO}*"):
        try:
            if arquivo.stat().st_mtime < limite:
                arquivo.unlink()
        except OSError:
            pass
