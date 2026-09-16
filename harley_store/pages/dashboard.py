import reflex as rx

from ..components.layout import page
from ..state.dashboard_state import DashboardState

LARANJA_HARLEY = "#f76511"
LARANJA_SUAVE = "#ff9a5c"
FUNDO_CARTAO = "#1b1b1b"
BORDA_CARTAO = "#3b291f"
TEXTO_SUAVE = "#b8b4af"


def _cartao(titulo: str, valor: rx.Var, icone: str, cor: str = "gray") -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.box(
                rx.icon(icone, size=20, color=rx.cond(cor == "alerta", LARANJA_SUAVE, LARANJA_HARLEY)),
                padding="0.6rem",
                border_radius="0.6rem",
                background=rx.cond(cor == "alerta", "#3b2115", "#2a1a13"),
            ),
            rx.vstack(
                rx.text(titulo, size="2", color=TEXTO_SUAVE),
                rx.heading(valor, size="6", color="#ffffff"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        width="100%",
        background=FUNDO_CARTAO,
        border=f"1px solid {BORDA_CARTAO}",
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
            _cartao("Produtos cadastrados", DashboardState.total_produtos, "package"),
            _cartao("Estoque baixo (≤ 5 un.)", DashboardState.produtos_estoque_baixo, "triangle_alert", "alerta"),
            _cartao("Clientes cadastrados", DashboardState.total_clientes, "users"),
            _cartao("Ordens de serviço em aberto", DashboardState.os_em_aberto, "wrench", "alerta"),
            columns=rx.breakpoints(initial="2", sm="4"),
            spacing="4",
            width="100%",
        ),
        rx.grid(
            _cartao("Faturamento de hoje", rx.text("R$ ", DashboardState.faturamento_hoje), "wallet"),
            _cartao("Faturamento do mês", rx.text("R$ ", DashboardState.faturamento_mes), "line-chart"),
            columns=rx.breakpoints(initial="1", xs="2"),
            spacing="4",
            width="100%",
        ),
        rx.heading("Atividade recente", size="4", color="#ffffff"),
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
            background=FUNDO_CARTAO,
        ),
        title="Painel",
        subtitle="Visão geral da loja e da oficina.",
    )
