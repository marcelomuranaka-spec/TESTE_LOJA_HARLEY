import reflex as rx

from ..components.layout import page
from ..models import TIPOS_FUNCIONARIO
from ..state.funcionarios_state import FuncionariosState


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["nome_funcionario"]),
        rx.table.cell(row["cargo"]),
        rx.table.cell(rx.badge(row["tipo"], variant="soft")),
        rx.table.cell(row["contato"]),
        rx.table.cell(
            rx.hstack(
                rx.button("Editar", size="1", variant="soft", on_click=FuncionariosState.editar(row)),
                rx.button(
                    "Excluir",
                    size="1",
                    variant="soft",
                    color_scheme="red",
                    on_click=FuncionariosState.excluir(row["id"]),
                ),
                spacing="2",
            )
        ),
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(rx.cond(FuncionariosState.form_id, "Editar funcionário", "Novo funcionário"), size="4"),
            rx.hstack(
                rx.input(
                    placeholder="Nome do funcionário",
                    value=FuncionariosState.nome_funcionario,
                    on_change=FuncionariosState.set_nome_funcionario,
                    width="100%",
                ),
                rx.input(
                    placeholder="Cargo (ex.: Vendedor balcão, Mecânico-chefe)",
                    value=FuncionariosState.cargo,
                    on_change=FuncionariosState.set_cargo,
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            rx.hstack(
                rx.select(
                    TIPOS_FUNCIONARIO,
                    value=FuncionariosState.tipo,
                    on_change=FuncionariosState.set_tipo,
                    width="200px",
                ),
                rx.input(
                    placeholder="Contato (telefone / e-mail)",
                    value=FuncionariosState.contato,
                    on_change=FuncionariosState.set_contato,
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            rx.hstack(
                rx.button("Salvar", on_click=FuncionariosState.salvar),
                rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=FuncionariosState.novo),
                spacing="3",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def funcionarios_page() -> rx.Component:
    return page(
        _formulario(),
        rx.input(
            placeholder="Buscar por nome...",
            value=FuncionariosState.busca,
            on_change=FuncionariosState.definir_busca,
            max_width="320px",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Funcionário"),
                    rx.table.column_header_cell("Cargo"),
                    rx.table.column_header_cell("Tipo"),
                    rx.table.column_header_cell("Contato"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(FuncionariosState.funcionarios, _linha)),
            width="100%",
            variant="surface",
        ),
        title="Funcionários",
        subtitle="Vendedores, mecânicos e gerência.",
    )
