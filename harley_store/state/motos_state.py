"""
State de Motos dos Clientes.

Este arquivo mostra o padrão a seguir sempre que uma tabela nova
referenciar outra (chave estrangeira): além da lista principal, o state
também carrega uma lista de opções (`clientes_opcoes`) para alimentar o
`rx.select` do formulário, e faz um JOIN simples (em Python) para mostrar
o nome do cliente na tabela em vez do id_cliente cru. Dados vêm do
backend Xano.
"""

from typing import Optional

import reflex as rx

from .. import xano_client as xano

TABELA = "motos_clientes"
TABELA_CLIENTES = "clientes"


class MotosState(rx.State):
    motos: list[dict] = []
    busca: str = ""

    clientes_opcoes: list[str] = []  # ex.: ["3 - João Pereira", ...]

    form_id: Optional[int] = None
    cliente_selecionado: str = ""
    modelo: str = ""
    placa: str = ""
    chassi: str = ""

    @rx.event
    def carregar(self):
        clientes = sorted(xano.listar(TABELA_CLIENTES), key=lambda c: c["nome_cliente"])
        self.clientes_opcoes = [f"{c['id']} - {c['nome_cliente']}" for c in clientes]
        nomes_por_id = {c["id"]: c["nome_cliente"] for c in clientes}

        registros = xano.listar(TABELA)
        if self.busca.strip():
            termo = self.busca.strip().lower()
            registros = [
                r for r in registros
                if termo in r["modelo"].lower() or termo in r["placa"].lower()
            ]
        registros = sorted(registros, key=lambda r: r["modelo"])

        self.motos = [
            {
                "id": str(r["id"]),
                "modelo": r["modelo"],
                "placa": r["placa"],
                "chassi": r["chassi"],
                "id_cliente": str(r["id_cliente"]),
                "cliente_nome": nomes_por_id.get(r["id_cliente"], "(cliente removido)"),
            }
            for r in registros
        ]

    @rx.event
    def definir_busca(self, valor: str):
        self.busca = valor
        self.carregar()

    @rx.event
    def novo(self):
        self.form_id = None
        self.cliente_selecionado = ""
        self.modelo = ""
        self.placa = ""
        self.chassi = ""

    @rx.event
    def editar(self, row: dict):
        self.form_id = int(row["id"])
        self.cliente_selecionado = f"{row['id_cliente']} - {row['cliente_nome']}"
        self.modelo = row["modelo"]
        self.placa = row["placa"]
        self.chassi = row["chassi"]

    @rx.event
    def salvar(self):
        modelo = self.modelo.strip()
        placa = self.placa.strip().upper()
        chassi = self.chassi.strip().upper()
        if not modelo or not placa or not chassi:
            return rx.window_alert("Preencha modelo, placa e chassi.")

        cliente_selecionado = self.cliente_selecionado
        if not cliente_selecionado:
            clientes_existentes = sorted(xano.listar(TABELA_CLIENTES), key=lambda c: c["nome_cliente"])
            if not clientes_existentes:
                return rx.window_alert("Cadastre um cliente antes de cadastrar a moto dele.")
            primeiro_cliente = clientes_existentes[0]
            cliente_selecionado = f"{primeiro_cliente['id']} - {primeiro_cliente['nome_cliente']}"

        id_cliente = int(cliente_selecionado.split(" - ")[0])

        duplicado = any(
            (r["placa"] == placa or r["chassi"] == chassi) and str(r["id"]) != str(self.form_id)
            for r in xano.listar(TABELA)
        )
        if duplicado:
            return rx.window_alert("Já existe uma moto cadastrada com essa placa ou chassi.")

        dados = {"id_cliente": id_cliente, "modelo": modelo, "placa": placa, "chassi": chassi}
        if self.form_id is None:
            xano.criar(TABELA, dados)
        else:
            xano.atualizar(TABELA, self.form_id, dados)

        self.novo()
        self.carregar()

    @rx.event
    def excluir(self, moto_id: str):
        xano.excluir(TABELA, int(moto_id))
        self.carregar()
