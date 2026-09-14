"""
Layout comum a todas as páginas: menu lateral + moldura da página.

Para adicionar um link novo no menu, basta acrescentar uma linha em
MENU_ITEMS — nada mais precisa mudar aqui.
"""

import reflex as rx

from ..state.auth_state import AuthState

MENU_ITEMS = [
    ("/", "layout-dashboard", "Painel"),
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
            rx.text(label, size="3"),
            spacing="3",
            align="center",
            width="100%",
            padding="0.55rem 0.75rem",
            border_radius="0.5rem",
            _hover={"background": rx.color("gray", 4)},
        ),
        href=href,
        underline="none",
        color_scheme="gray",
        high_contrast=True,
        width="100%",
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("flame", size=22, color=rx.color("orange", 9)),
                rx.heading("Harley Store", size="5"),
                align="center",
                spacing="2",
                padding_bottom="1rem",
            ),
            *[_menu_link(href, icon, label) for href, icon, label in MENU_ITEMS],
            rx.spacer(),
            rx.divider(),
            rx.hstack(
                rx.icon("circle-user-round", size=18, color=rx.color("gray", 10)),
                rx.text(AuthState.usuario_logado, size="2", color=rx.color("gray", 11)),
                align="center",
                spacing="2",
                width="100%",
                padding="0.4rem 0.75rem",
            ),
            rx.button(
                rx.icon("repeat", size=16),
                "Trocar de usuário",
                on_click=AuthState.sair,
                variant="soft",
                color_scheme="gray",
                width="100%",
            ),
            rx.button(
                rx.icon("log-out", size=16),
                "Sair",
                on_click=AuthState.sair,
                variant="soft",
                color_scheme="red",
                width="100%",
            ),
            align="start",
            width="100%",
            spacing="1",
            height="100%",
        ),
        width="230px",
        min_width="230px",
        height="100vh",
        position="sticky",
        top="0",
        padding="1rem",
        border_right=f"1px solid {rx.color('gray', 5)}",
        background=rx.color("gray", 1),
    )


def page(*children: rx.Component, title: str, subtitle: str = "") -> rx.Component:
    """Moldura padrão usada em todas as páginas: sidebar + cabeçalho + conteúdo."""
    header_children = [rx.heading(title, size="6")]
    if subtitle:
        header_children.append(rx.text(subtitle, color=rx.color("gray", 10), size="3"))

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
            padding="2rem",
            width="100%",
            max_width="1100px",
        ),
        align="start",
        width="100%",
        spacing="0",
    )
