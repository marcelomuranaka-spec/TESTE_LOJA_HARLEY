import reflex as rx

from ..components.layout import page
from ..state.produtos_state import ProdutosState


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["nome_produto"]),
        rx.table.cell(row["categoria"]),
        rx.table.cell(
            rx.cond(
                row["estoque_baixo"],
                rx.badge(row["estoque_qtd"], color_scheme="red", variant="soft"),
                rx.text(row["estoque_qtd"]),
            )
        ),
        rx.table.cell(rx.text("R$ ", row["preco_venda"])),
        rx.table.cell(
            rx.hstack(
                rx.button("Editar", size="1", variant="soft", on_click=ProdutosState.editar(row)),
                rx.button(
                    "Excluir",
                    size="1",
                    variant="soft",
                    color_scheme="red",
                    on_click=ProdutosState.excluir(row["id"]),
                ),
                spacing="2",
            )
        ),
    )


def _formulario() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(rx.cond(ProdutosState.form_id, "Editar produto", "Novo produto"), size="4"),
            rx.hstack(
                rx.input(
                    placeholder="Nome do produto",
                    value=ProdutosState.nome_produto,
                    on_change=ProdutosState.set_nome_produto,
                    width="100%",
                ),
                rx.input(
                    placeholder="Categoria (ex.: Peças, Acessórios, Vestuário)",
                    value=ProdutosState.categoria,
                    on_change=ProdutosState.set_categoria,
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            rx.input(
                placeholder="Descrição (opcional)",
                value=ProdutosState.descricao,
                on_change=ProdutosState.set_descricao,
                width="100%",
            ),
            rx.hstack(
                rx.input(
                    placeholder="Estoque",
                    type="number",
                    value=ProdutosState.estoque_qtd,
                    on_change=ProdutosState.set_estoque_qtd,
                    width="150px",
                ),
                rx.input(
                    placeholder="Preço de venda",
                    type="number",
                    value=ProdutosState.preco_venda,
                    on_change=ProdutosState.set_preco_venda,
                    width="180px",
                ),
                spacing="3",
            ),
            rx.hstack(
                rx.button("Salvar", on_click=ProdutosState.salvar),
                rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=ProdutosState.novo),
                spacing="3",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def produtos_page() -> rx.Component:
    return page(
        _formulario(),
        rx.hstack(
            rx.input(
                placeholder="Buscar por nome...",
                value=ProdutosState.busca,
                on_change=ProdutosState.definir_busca,
                max_width="320px",
            ),
            rx.hstack(
                rx.switch(
                    checked=ProdutosState.somente_estoque_baixo,
                    on_change=ProdutosState.alternar_filtro_estoque_baixo,
                ),
                rx.text("Só estoque baixo"),
                spacing="2",
                align="center",
            ),
            spacing="5",
            align="center",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Produto"),
                    rx.table.column_header_cell("Categoria"),
                    rx.table.column_header_cell("Estoque"),
                    rx.table.column_header_cell("Preço"),
                    rx.table.column_header_cell("Ações"),
                )
            ),
            rx.table.body(rx.foreach(ProdutosState.produtos, _linha)),
            width="100%",
            variant="surface",
        ),
        title="Produtos",
        subtitle="Catálogo e estoque de peças, acessórios e itens vendidos na loja.",
    )
