"""
Página de Fornecedores — template mais simples de página CRUD do projeto.
Para criar uma página nova parecida, copie este arquivo.
"""

import reflex as rx

from ..components.layout import page
from ..state.fornecedores_state import FornecedoresState


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["nome_fornecedor"]),
        rx.table.cell(row["cnpj"]),
        rx.table.cell(row["contato"]),
        rx.table.cell(
            rx.hstack(
                rx.button("Editar", size="1", variant="soft", on_click=FornecedoresState.editar(row)),
                rx.button(
                    "Excluir",
                    size="1",
                    variant="soft",
                    color_scheme="red",
                    on_click=FornecedoresState.excluir(row["id"]),
                ),
                spacing="2",
            )
        ),
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(
                rx.cond(FornecedoresState.form_id, "Editar fornecedor", "Novo fornecedor"),
                size="4",
            ),
            rx.hstack(
                rx.input(
                    placeholder="Nome do fornecedor",
                    value=FornecedoresState.nome_fornecedor,
                    on_change=FornecedoresState.set_nome_fornecedor,
                    width="100%",
                ),
                rx.input(
                    placeholder="CNPJ",
                    value=FornecedoresState.cnpj,
                    on_change=FornecedoresState.set_cnpj,
                    width="220px",
                ),
                spacing="3",
                width="100%",
            ),
            rx.input(
                placeholder="Contato (telefone / e-mail)",
                value=FornecedoresState.contato,
                on_change=FornecedoresState.set_contato,
                width="100%",
            ),
            rx.hstack(
                rx.button("Salvar", on_click=FornecedoresState.salvar),
                rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=FornecedoresState.novo),
                spacing="3",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def fornecedores_page() -> rx.Component:
    return page(
        _formulario(),
        rx.input(
            placeholder="Buscar por nome...",
            value=FornecedoresState.busca,
            on_change=FornecedoresState.definir_busca,
            max_width="320px",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Fornecedor"),
                    rx.table.column_header_cell("CNPJ"),
                    rx.table.column_header_cell("Contato"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(FornecedoresState.fornecedores, _linha)),
            width="100%",
            variant="surface",
        ),
        title="Fornecedores",
        subtitle="Empresas que abastecem o estoque da loja.",
    )
