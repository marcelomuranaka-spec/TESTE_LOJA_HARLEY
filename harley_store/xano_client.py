"""
Cliente HTTP para o backend Xano (workspace HARLEY, instância Free).

Os states em `state/` usavam `rx.session()` (SQLModel/SQLite local). Este
módulo troca a fonte de dados pelas APIs REST publicadas no Xano, mantendo
a mesma forma de uso: funções simples que recebem/retornam `dict`.

Detalhes importantes do Xano que este cliente já resolve para quem chama:

- O endpoint PATCH gerado pelo assistente "CRUD Database Operations" do
  Xano exige TODOS os campos obrigatórios da tabela (não é um PATCH
  parcial de verdade) — por isso `update()` espera o registro completo,
  não só os campos alterados.
- Campos de data/hora voltam do Xano como epoch em milissegundos (int),
  não como string ISO. `epoch_ms_para_datetime` / `datetime_para_epoch_ms`
  fazem a conversão nos dois sentidos.
- O plano Free do Xano tem limite de requisições por minuto. Como
  algumas telas (ex.: Painel, Compras, Vendas, Ordens de Serviço) fazem
  várias chamadas em sequência para montar os menus/relatórios, é fácil
  esbarrar nesse limite (erro 429) mesmo em uso normal. `_request` faz
  retentativas automáticas com espera crescente antes de desistir.

Todas as funções aqui são `async` e usam `httpx.AsyncClient` (não
`httpx.request` síncrono). Isso importa especialmente no Reflex: um
event handler síncrono que faz uma chamada de rede bloqueante trava a
única thread do loop de eventos do app inteiro enquanto espera — nesse
tempo o servidor não consegue nem responder ao ping/pong do websocket,
e o navegador chega a mostrar "Cannot connect to server" mesmo com o
back-end vivo, só ocupado. Usando `await` em vez de chamada bloqueante,
o loop de eventos fica livre para atender outras coisas (incluindo o
próprio heartbeat da conexão) enquanto a resposta do Xano não chega.
"""

from __future__ import annotations

import asyncio
import datetime

import httpx

BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:LtU_pM2N"
_TIMEOUT = 15.0
_MAX_TENTATIVAS = 5
_ESPERA_BASE_SEGUNDOS = 1.5


def _segundos_de_espera(resposta: httpx.Response, tentativa: int) -> float:
    """Quanto esperar antes de repetir uma chamada que voltou 429.

    O cabeçalho `Retry-After` pode vir como número de segundos OU como data
    HTTP ("Wed, 21 Oct 2015 07:28:00 GMT"). Converter direto com `float()`
    quebrava nesse segundo caso — aqui qualquer valor não numérico cai na
    espera crescente padrão.
    """
    try:
        espera = float(resposta.headers.get("Retry-After", ""))
    except ValueError:
        espera = 0.0
    if espera <= 0:
        espera = _ESPERA_BASE_SEGUNDOS * (2**tentativa)
    return min(espera, 20)


async def _request(metodo: str, url: str, **kwargs) -> httpx.Response:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resposta = await client.request(metodo, url, **kwargs)
        # A espera só faz sentido ENTRE duas tentativas: esperar depois da
        # última só atrasava a resposta de erro que já ia ser devolvida.
        for tentativa in range(_MAX_TENTATIVAS - 1):
            if resposta.status_code != 429:
                return resposta
            await asyncio.sleep(_segundos_de_espera(resposta, tentativa))
            resposta = await client.request(metodo, url, **kwargs)
        return resposta


async def listar(tabela: str) -> list[dict]:
    resposta = await _request("GET", f"{BASE_URL}/{tabela}")
    resposta.raise_for_status()
    return resposta.json() or []


async def buscar(tabela: str, registro_id: int) -> dict | None:
    resposta = await _request("GET", f"{BASE_URL}/{tabela}/{registro_id}")
    if resposta.status_code == 404:
        return None
    resposta.raise_for_status()
    return resposta.json()


async def criar(tabela: str, dados: dict) -> dict:
    resposta = await _request("POST", f"{BASE_URL}/{tabela}", json=dados)
    resposta.raise_for_status()
    return resposta.json()


async def atualizar(tabela: str, registro_id: int, dados: dict) -> dict:
    resposta = await _request("PATCH", f"{BASE_URL}/{tabela}/{registro_id}", json=dados)
    resposta.raise_for_status()
    return resposta.json()


async def excluir(tabela: str, registro_id: int) -> None:
    resposta = await _request("DELETE", f"{BASE_URL}/{tabela}/{registro_id}")
    if resposta.status_code == 404:
        return
    resposta.raise_for_status()


async def enviar_foto(rota: str, conteudo: bytes, nome: str, mime: str) -> dict:
    """Envia um arquivo de imagem (multipart, campo `arquivo`) para um
    endpoint de upload do Xano e devolve os metadados gravados no
    armazenamento de arquivos (path, name, mime, size, url...).

    Esse objeto é o que vai no campo de imagem do registro — nunca o
    conteúdo do arquivo nem Base64.
    """
    resposta = await _request(
        "POST", f"{BASE_URL}/{rota}", files={"arquivo": (nome, conteudo, mime)}
    )
    resposta.raise_for_status()
    return resposta.json() or {}


def url_arquivo(metadados: object) -> str:
    """URL pública de um arquivo guardado no Xano a partir dos metadados.

    Usa `url` quando o Xano a devolve; senão monta host da instância + `path`.
    Metadados ausentes ou inválidos viram string vazia.
    """
    if not isinstance(metadados, dict):
        return ""
    url = texto(metadados.get("url"))
    if url:
        return url
    caminho = texto(metadados.get("path"))
    if not caminho:
        return ""
    host = BASE_URL.split("/api:")[0]
    return f"{host}/{caminho.lstrip('/')}"


def epoch_ms_para_datetime(valor: int | float | str | None) -> datetime.datetime:
    """Converte a data do Xano (epoch em milissegundos) para datetime.

    Aceita também string — um campo configurado como `timestamp` no Xano
    pode voltar como texto ISO ou como número dentro de aspas, e nesses
    casos a divisão por 1000 levantava TypeError e derrubava a tela.
    """
    if not valor:
        return datetime.datetime.now()
    if isinstance(valor, str):
        try:
            convertido = datetime.datetime.fromisoformat(valor.replace("Z", "+00:00"))
        except ValueError:
            pass
        else:
            # Sempre devolver datetime "ingênuo" (sem fuso): o resto do app
            # compara essas datas com datetime.now(), e misturar com/sem
            # fuso levanta TypeError.
            if convertido.tzinfo is not None:
                convertido = convertido.astimezone().replace(tzinfo=None)
            return convertido
    try:
        return datetime.datetime.fromtimestamp(float(valor) / 1000)
    except (TypeError, ValueError, OSError, OverflowError):
        return datetime.datetime.now()


def texto(valor: object) -> str:
    """Campo de texto vindo do Xano: nulo vira string vazia.

    Usar isto ao ordenar, filtrar ou exibir campos da API. Sem isso, um
    registro com o campo nulo derruba a tela inteira: comparar None com
    str levanta TypeError em `sorted()` e `None.lower()` levanta
    AttributeError na busca.
    """
    return "" if valor is None else str(valor)


def numero(valor: object) -> float:
    """Campo numérico vindo do Xano: nulo ou inválido vira 0.0."""
    try:
        return float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def inteiro(valor: object) -> int:
    """Campo inteiro vindo do Xano: nulo ou inválido vira 0."""
    return int(numero(valor))


def datetime_para_epoch_ms(valor: datetime.datetime | None = None) -> int:
    valor = valor or datetime.datetime.now()
    return int(valor.timestamp() * 1000)
