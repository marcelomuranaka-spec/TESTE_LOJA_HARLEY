import reflex as rx

from ..components.layout import page
from ..state.motos_state import MotosState


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["modelo"]),
        rx.table.cell(row["placa"]),
        rx.table.cell(row["chassi"]),
        rx.table.cell(row["cliente_nome"]),
        rx.table.cell(
            rx.hstack(
                rx.button("Editar", size="1", variant="soft", on_click=MotosState.editar(row)),
                rx.button(
                    "Excluir",
                    size="1",
                    variant="soft",
                    color_scheme="red",
                    on_click=MotosState.excluir(row["id"]),
                ),
                spacing="2",
            )
        ),
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(rx.cond(MotosState.form_id, "Editar moto", "Nova moto"), size="4"),
            rx.cond(
                MotosState.clientes_opcoes.length() == 0,
                rx.callout(
                    "Cadastre um cliente primeiro, na página Clientes.",
                    icon="triangle_alert",
                    color_scheme="amber",
                ),
                rx.fragment(
                    rx.select(
                        MotosState.clientes_opcoes,
                        placeholder="Cliente dono da moto",
                        value=rx.cond(
                            MotosState.cliente_selecionado,
                            MotosState.cliente_selecionado,
                            MotosState.clientes_opcoes[0],
                        ),
                        on_change=MotosState.set_cliente_selecionado,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Modelo (ex.: Iron 883)",
                            value=MotosState.modelo,
                            on_change=MotosState.set_modelo,
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Placa",
                            value=MotosState.placa,
                            on_change=MotosState.set_placa,
                            width="160px",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Chassi",
                        value=MotosState.chassi,
                        on_change=MotosState.set_chassi,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button("Salvar", on_click=MotosState.salvar),
                        rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=MotosState.novo),
                        spacing="3",
                    ),
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def motos_page() -> rx.Component:
    return page(
        _formulario(),
        rx.input(
            placeholder="Buscar por modelo ou placa...",
            value=MotosState.busca,
            on_change=MotosState.definir_busca,
            max_width="320px",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Modelo"),
                    rx.table.column_header_cell("Placa"),
                    rx.table.column_header_cell("Chassi"),
                    rx.table.column_header_cell("Dono"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(MotosState.motos, _linha)),
            width="100%",
            variant="surface",
        ),
        title="Motos dos clientes",
        subtitle="Motos que passam pela oficina ou foram compradas na loja.",
    )
