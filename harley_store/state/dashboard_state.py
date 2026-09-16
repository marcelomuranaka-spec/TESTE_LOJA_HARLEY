"""
State do Painel (dashboard).

A lista `atividades_recentes` reproduz em Python a ideia da view SQL
original `vw_resumo_operacoes` (que juntava Transacoes + Entrada de
Mercadoria num só extrato) — um bom exemplo de como combinar duas
tabelas num só relatório dentro de um State, caso você queira montar
outros relatórios parecidos no futuro.

Dados vêm do backend Xano.
"""

import datetime

import reflex as rx

from .. import xano_client as xano

LIMITE_ESTOQUE_BAIXO = 5


class DashboardState(rx.State):
    total_produtos: int = 0
    produtos_estoque_baixo: int = 0
    total_clientes: int = 0
    os_em_aberto: int = 0
    faturamento_hoje: str = "0.00"
    faturamento_mes: str = "0.00"
    atividades_recentes: list[dict] = []

    @rx.event
    async def carregar(self):
        hoje = datetime.date.today()
        inicio_hoje = datetime.datetime.combine(hoje, datetime.time.min)
        inicio_mes = datetime.datetime.combine(hoje.replace(day=1), datetime.time.min)

        produtos = await xano.listar("produtos")
        self.total_produtos = len(produtos)
        self.produtos_estoque_baixo = sum(
            1 for p in produtos if xano.inteiro(p.get("estoque_qtd")) <= LIMITE_ESTOQUE_BAIXO
        )

        # A lista de clientes era buscada duas vezes na mesma tela (uma para
        # o contador, outra para o extrato). Como o plano Free do Xano limita
        # requisições por minuto, aqui ela é lida uma vez só e reaproveitada.
        lista_clientes = await xano.listar("clientes")
        self.total_clientes = len(lista_clientes)

        ordens = await xano.listar("ordens_servico")
        self.os_em_aberto = sum(1 for o in ordens if o.get("status") in ("ABERTA", "EM_ANDAMENTO"))

        transacoes = await xano.listar("transacoes")
        transacoes_com_data = [
            (t, xano.epoch_ms_para_datetime(t.get("data_transacao"))) for t in transacoes
        ]
        total_hoje = sum(xano.numero(t.get("valor_total")) for t, d in transacoes_com_data if d >= inicio_hoje)
        total_mes = sum(xano.numero(t.get("valor_total")) for t, d in transacoes_com_data if d >= inicio_mes)
        self.faturamento_hoje = f"{total_hoje:.2f}"
        self.faturamento_mes = f"{total_mes:.2f}"

        funcionarios = {f["id"]: xano.texto(f.get("nome_funcionario")) for f in await xano.listar("funcionarios")}
        clientes = {c["id"]: xano.texto(c.get("nome_cliente")) for c in lista_clientes}
        fornecedores = {f["id"]: xano.texto(f.get("nome_fornecedor")) for f in await xano.listar("fornecedores")}
        entradas = await xano.listar("entrada_mercadoria")

        atividades = [
            {
                "origem": "Venda",
                "tipo": xano.texto(t.get("tipo_transacao")),
                "quem": clientes.get(t.get("id_cliente")) or funcionarios.get(t.get("id_funcionario")) or "—",
                "data": d,
                "valor": xano.numero(t.get("valor_total")),
            }
            for t, d in transacoes_com_data
        ] + [
            {
                "origem": "Compra",
                "tipo": "ENTRADA ESTOQUE",
                "quem": fornecedores.get(e.get("id_fornecedor")) or "—",
                "data": xano.epoch_ms_para_datetime(e.get("data_entrada")),
                "valor": xano.numero(e.get("valor_total")),
            }
            for e in entradas
        ]
        atividades.sort(key=lambda a: a["data"], reverse=True)

        self.atividades_recentes = [
            {
                "origem": a["origem"],
                "tipo": a["tipo"],
                "quem": a["quem"],
                "data": a["data"].strftime("%d/%m/%Y %H:%M"),
                "valor": f"{a['valor']:.2f}",
            }
            for a in atividades[:12]
        ]
