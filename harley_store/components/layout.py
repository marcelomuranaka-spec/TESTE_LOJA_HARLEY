"""
Layout comum a todas as páginas: menu lateral + moldura da página.

Para adicionar um link novo no menu, basta acrescentar uma linha em
MENU_ITEMS — nada mais precisa mudar aqui.
"""

import reflex as rx

from ..state.auth_state import AuthState

LARANJA_HARLEY = "#f76511"
FUNDO_CARVAO = "#101010"
FUNDO_GRAFITE = "#181818"
TEXTO_SUAVE = "#b8b4af"

MENU_ITEMS = [
    ("/painel", "layout-dashboard", "Painel"),
    ("/produtos", "package", "Produtos"),
    ("/clientes", "users", "Clientes"),
    ("/motos", "bike", "Motos dos clientes"),
    ("/vendas", "shopping-cart", "Vendas / Balcão"),
    ("/ordens-servico", "wrench", "Ordens de serviço"),
    ("/compras", "truck", "Compras (entrada)"),
    ("/fornecedores", "factory", "Fornecedores"),
    ("/funcionarios", "id-card", "Funcionários"),
    ("/usuarios", "shield-user", "Usuários do sistema"),
]


def _menu_link(href: str, icon: str, label: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(label, size="3", display=["none", "none", "block"]),
            spacing="3",
            align="center",
            justify=rx.breakpoints(initial="center", md="start"),
            width="100%",
            padding="0.55rem 0.75rem",
            border_radius="0.5rem",
            color="#e7e2dc",
            _hover={"background": "#2a1a13", "color": LARANJA_HARLEY},
        ),
        href=href,
        underline="none",
        color_scheme="orange",
        high_contrast=True,
        width="100%",
        title=label,
    )


def sidebar() -> rx.Component:
    """Menu lateral. Em telas estreitas (celular) encolhe para uma trilha só
    de ícones, já que o app agora também roda instalado como PWA no iPhone."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("flame", size=22, color=LARANJA_HARLEY),
                rx.heading("Harley Store", size="5", color="#ffffff", display=["none", "none", "block"]),
                align="center",
                spacing="2",
                padding_bottom="1rem",
            ),
            *[_menu_link(href, icon, label) for href, icon, label in MENU_ITEMS],
            rx.spacer(),
            rx.divider(),
            rx.hstack(
                rx.icon("circle-user-round", size=18, color=TEXTO_SUAVE),
                rx.text(
                    AuthState.usuario_logado,
                    size="2",
                    color=TEXTO_SUAVE,
                    display=["none", "none", "block"],
                ),
                align="center",
                spacing="2",
                width="100%",
                padding="0.4rem 0.75rem",
            ),
            rx.button(
                rx.icon("log-out", size=16),
                rx.text("Sair", display=["none", "none", "block"]),
                on_click=AuthState.sair,
                variant="soft",
                color_scheme="orange",
                width="100%",
            ),
            align="start",
            width="100%",
            spacing="1",
            height="100%",
        ),
        width=["64px", "64px", "230px"],
        min_width=["64px", "64px", "230px"],
        height="100vh",
        position="sticky",
        top="0",
        padding=["0.5rem", "0.5rem", "1rem"],
        border_right="1px solid #33231b",
        background=FUNDO_CARVAO,
        flex_shrink="0",
    )


def page(*children: rx.Component, title: str, subtitle: str = "") -> rx.Component:
    """Moldura padrão usada em todas as páginas: sidebar + cabeçalho + conteúdo."""
    header_children = [rx.heading(title, size="6", color="#ffffff")]
    if subtitle:
        header_children.append(rx.text(subtitle, color=TEXTO_SUAVE, size="3"))

    return rx.hstack(
        sidebar(),
        rx.box(
            rx.vstack(
                rx.vstack(*header_children, align="start", spacing="1", padding_bottom="1.25rem"),
                *children,
                align="start",
                width="100%",
                spacing="4",
            ),
            padding=["1rem", "1rem", "2rem"],
            width="100%",
            max_width="1100px",
            min_height="100vh",
            background=FUNDO_CARVAO,
            overflow_x="auto",
        ),
        align="start",
        width="100%",
        spacing="0",
        background=FUNDO_CARVAO,
    )
