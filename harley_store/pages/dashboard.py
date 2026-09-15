import reflex as rx

from ..components.layout import page
from ..state.dashboard_state import DashboardState


def _cartao(titulo: str, valor: rx.Var, icone: str, cor: str = "gray") -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.box(
                rx.icon(icone, size=20, color=rx.color(cor, 9)),
                padding="0.6rem",
                border_radius="0.6rem",
                background=rx.color(cor, 3),
            ),
            rx.vstack(
                rx.text(titulo, size="2", color=rx.color("gray", 10)),
                rx.heading(valor, size="6"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        width="100%",
    )


def _linha_atividade(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["data"]),
        rx.table.cell(rx.badge(row["origem"], variant="soft")),
        rx.table.cell(row["tipo"]),
        rx.table.cell(row["quem"]),
        rx.table.cell(rx.text("R$ ", row["valor"])),
    )


def dashboard_page() -> rx.Component:
    return page(
        rx.grid(
            _cartao("Produtos cadastrados", DashboardState.total_produtos, "package", "blue"),
            _cartao("Estoque baixo (≤ 5 un.)", DashboardState.produtos_estoque_baixo, "triangle_alert", "red"),
            _cartao("Clientes cadastrados", DashboardState.total_clientes, "users", "violet"),
            _cartao("Ordens de serviço em aberto", DashboardState.os_em_aberto, "wrench", "amber"),
            columns=rx.breakpoints(initial="2", sm="4"),
            spacing="4",
            width="100%",
        ),
        rx.grid(
            _cartao("Faturamento de hoje", rx.text("R$ ", DashboardState.faturamento_hoje), "wallet", "green"),
            _cartao("Faturamento do mês", rx.text("R$ ", DashboardState.faturamento_mes), "line-chart", "green"),
            columns=rx.breakpoints(initial="1", xs="2"),
            spacing="4",
            width="100%",
        ),
        rx.heading("Atividade recente", size="4"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Data"),
                    rx.table.column_header_cell("Origem"),
                    rx.table.column_header_cell("Tipo"),
                    rx.table.column_header_cell("Quem"),
                    rx.table.column_header_cell("Valor"),
                )
            ),
            rx.table.body(rx.foreach(DashboardState.atividades_recentes, _linha_atividade)),
            width="100%",
            variant="surface",
        ),
        title="Painel",
        subtitle="Visão geral da loja e da oficina.",
    )
