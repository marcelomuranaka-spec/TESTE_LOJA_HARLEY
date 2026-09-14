"""
State de Fornecedores — este arquivo é o template mais simples de CRUD
do projeto. Para criar um cadastro novo parecido (uma tabela sem
relacionamento com outras), copie este arquivo e ajuste os campos.

Os dados vêm do backend Xano (workspace HARLEY) via `xano_client`, não
mais do SQLite local — ver `xano_client.py` para detalhes da API.
"""

from typing import Optional

import reflex as rx

from .. import xano_client as xano

TABELA = "fornecedores"


class FornecedoresState(rx.State):
    fornecedores: list[dict] = []
    busca: str = ""

    # campos do formulário (sempre como string; convertidos ao salvar)
    form_id: Optional[int] = None
    nome_fornecedor: str = ""
    cnpj: str = ""
    contato: str = ""

    @rx.event
    def carregar(self):
        registros = xano.listar(TABELA)
        if self.busca.strip():
            termo = self.busca.strip().lower()
            registros = [r for r in registros if termo in r["nome_fornecedor"].lower()]
        registros = sorted(registros, key=lambda r: r["nome_fornecedor"])
        self.fornecedores = [
            {
                "id": str(r["id"]),
                "nome_fornecedor": r["nome_fornecedor"],
                "cnpj": r["cnpj"],
                "contato": r.get("contato") or "—",
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
        self.nome_fornecedor = ""
        self.cnpj = ""
        self.contato = ""

    @rx.event
    def editar(self, row: dict):
        self.form_id = int(row["id"])
        self.nome_fornecedor = row["nome_fornecedor"]
        self.cnpj = row["cnpj"]
        self.contato = "" if row["contato"] == "—" else row["contato"]

    @rx.event
    def salvar(self):
        nome = self.nome_fornecedor.strip()
        cnpj = self.cnpj.strip()
        if not nome or not cnpj:
            return rx.window_alert("Preencha nome e CNPJ do fornecedor.")

        duplicado = any(
            r["cnpj"] == cnpj and str(r["id"]) != str(self.form_id)
            for r in xano.listar(TABELA)
        )
        if duplicado:
            return rx.window_alert("Já existe um fornecedor com esse CNPJ.")

        dados = {"nome_fornecedor": nome, "cnpj": cnpj, "contato": self.contato.strip() or None}
        if self.form_id is None:
            xano.criar(TABELA, dados)
        else:
            xano.atualizar(TABELA, self.form_id, dados)

        self.novo()
        self.carregar()

    @rx.event
    def excluir(self, fornecedor_id: str):
        xano.excluir(TABELA, int(fornecedor_id))
        self.carregar()
