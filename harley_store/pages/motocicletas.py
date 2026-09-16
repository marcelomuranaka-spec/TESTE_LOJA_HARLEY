import reflex as rx

from ..components.confirm_dialog import confirm_delete_button
from ..components.layout import page
from ..state.motocicletas_state import OPCOES_ESTOQUE, STATUS_MOTO, TODOS_STATUS, MotocicletasState
from .dashboard import BORDA_CARTAO, FUNDO_CARTAO, LARANJA_HARLEY, TEXTO_SUAVE

UPLOAD_ID = "upload_foto_motocicleta"


# ----------------------------------------------------------------------
# Cards de resumo
# ----------------------------------------------------------------------


def _cartao(titulo: str, valor: rx.Var, icone: str) -> rx.Component:
    # Mesmo visual dos cartões do Painel. No celular o ícone some: com dois
    # cartões por linha ao lado da trilha do menu, ele cortava "Em manutenção".
    return rx.card(
        rx.hstack(
            rx.box(
                rx.icon(icone, size=20, color=LARANJA_HARLEY),
                padding="0.6rem",
                border_radius="0.6rem",
                background="#2a1a13",
                display=rx.breakpoints(initial="none", sm="block"),
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


def _resumo() -> rx.Component:
    return rx.grid(
        _cartao("Total de motos", MotocicletasState.total_motos, "gauge"),
        _cartao("Em estoque", MotocicletasState.total_em_estoque, "warehouse"),
        _cartao("Reservadas", MotocicletasState.total_reservadas, "bookmark"),
        _cartao("Em manutenção", MotocicletasState.total_manutencao, "wrench"),
        _cartao("Vendidas", MotocicletasState.total_vendidas, "badge-check"),
        columns=rx.breakpoints(initial="2", sm="3", md="5"),
        spacing="3",
        width="100%",
    )


# ----------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------


def _filtros() -> rx.Component:
    return rx.grid(
        rx.input(
            rx.input.slot(rx.icon("search", size=16)),
            placeholder="Pesquisar moto...",
            value=MotocicletasState.busca,
            on_change=MotocicletasState.set_busca,
            width="100%",
        ),
        rx.select(
            MotocicletasState.opcoes_marca,
            value=MotocicletasState.filtro_marca,
            on_change=MotocicletasState.definir_filtro_marca,
            width="100%",
        ),
        rx.select(
            MotocicletasState.opcoes_modelo,
            value=MotocicletasState.filtro_modelo,
            on_change=MotocicletasState.set_filtro_modelo,
            width="100%",
        ),
        rx.select(
            MotocicletasState.opcoes_ano,
            value=MotocicletasState.filtro_ano,
            on_change=MotocicletasState.set_filtro_ano,
            width="100%",
        ),
        rx.select(
            [TODOS_STATUS, *STATUS_MOTO],
            value=MotocicletasState.filtro_status,
            on_change=MotocicletasState.set_filtro_status,
            width="100%",
        ),
        rx.select(
            OPCOES_ESTOQUE,
            value=MotocicletasState.filtro_estoque,
            on_change=MotocicletasState.set_filtro_estoque,
            width="100%",
        ),
        rx.select(
            MotocicletasState.opcoes_cliente_filtro,
            value=MotocicletasState.filtro_cliente,
            on_change=MotocicletasState.set_filtro_cliente,
            width="100%",
        ),
        rx.cond(
            MotocicletasState.ha_filtro_ativo,
            rx.button(
                rx.icon("x", size=14),
                "Limpar filtros",
                variant="soft",
                color_scheme="gray",
                on_click=MotocicletasState.limpar_filtros,
                width="100%",
            ),
        ),
        columns=rx.breakpoints(initial="1", sm="2", md="4"),
        spacing="3",
        width="100%",
    )


# ----------------------------------------------------------------------
# Tabela
# ----------------------------------------------------------------------


def _placeholder_foto(tamanho: str, icone: int) -> rx.Component:
    return rx.box(
        rx.icon("bike", size=icone, color=rx.color("gray", 8)),
        width=tamanho,
        height=tamanho,
        min_width=tamanho,
        border_radius="0.5rem",
        background=rx.color("gray", 3),
        border=f"1px solid {rx.color('gray', 5)}",
        display="flex",
        align_items="center",
        justify_content="center",
    )


def _miniatura(row: dict) -> rx.Component:
    return rx.cond(
        row["foto_url"] != "",
        rx.image(
            src=row["foto_url"],
            alt="Foto da motocicleta",
            width="56px",
            height="42px",
            min_width="56px",
            border_radius="0.5rem",
            object_fit="cover",
            cursor="zoom-in",
            on_click=MotocicletasState.ampliar_foto(row["foto_url"]),
        ),
        rx.box(_placeholder_foto("42px", 18), width="56px", display="flex", justify_content="center"),
    )


def _badge_status(status: rx.Var) -> rx.Component:
    return rx.badge(
        status,
        variant="soft",
        color_scheme=rx.match(
            status,
            ("Em estoque", "green"),
            ("Reservada", "amber"),
            ("Em manutenção", "blue"),
            ("Vendida", "orange"),
            "gray",
        ),
    )


def _linha(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(_miniatura(row)),
        rx.table.cell(row["marca"]),
        rx.table.cell(rx.text(row["modelo"], weight="medium")),
        rx.table.cell(row["ano"]),
        rx.table.cell(rx.cond(row["placa"] != "", row["placa"], "—")),
        rx.table.cell(row["cliente_nome"]),
        rx.table.cell(row["km"], white_space="nowrap"),
        rx.table.cell(_badge_status(row["status"])),
        rx.table.cell(
            rx.badge(row["estoque"], variant="outline", color_scheme=rx.cond(row["estoque"] == "Sim", "green", "gray"))
        ),
        rx.table.cell(row["preco"], white_space="nowrap"),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    size="1",
                    variant="soft",
                    on_click=MotocicletasState.abrir_edicao(row["id"]),
                ),
                confirm_delete_button(
                    MotocicletasState.excluir(row["id"]),
                    item_label="esta motocicleta",
                ),
                spacing="2",
            )
        ),
        align="center",
    )


def _tabela() -> rx.Component:
    colunas = ["Foto", "Marca", "Modelo", "Ano", "Placa", "Cliente", "KM", "Status", "Estoque", "Preço", "Ações"]
    return rx.vstack(
        # Rolagem horizontal só dentro desta área, para a tela não vazar no celular
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(*[rx.table.column_header_cell(c, white_space="nowrap") for c in colunas])
                ),
                rx.table.body(rx.foreach(MotocicletasState.motos_filtradas, _linha)),
                width="100%",
                variant="surface",
            ),
            width="100%",
            overflow_x="auto",
        ),
        rx.cond(
            MotocicletasState.motos_filtradas.length() == 0,
            rx.text("Nenhuma motocicleta encontrada com esses filtros.", color=TEXTO_SUAVE, size="2"),
        ),
        width="100%",
        spacing="3",
    )


# ----------------------------------------------------------------------
# Estados da tela
# ----------------------------------------------------------------------


def _carregando() -> rx.Component:
    return rx.hstack(
        rx.spinner(size="3"),
        rx.text("Carregando motocicletas...", color=TEXTO_SUAVE),
        spacing="3",
        align="center",
        padding_y="2rem",
    )


def _erro() -> rx.Component:
    return rx.callout(
        "Não foi possível carregar as motocicletas.",
        icon="triangle_alert",
        color_scheme="red",
        width="100%",
    )


def _vazio() -> rx.Component:
    return rx.card(
        rx.vstack(
            _placeholder_foto("64px", 30),
            rx.text("Nenhuma motocicleta cadastrada.", size="3", color="#ffffff"),
            rx.button(
                rx.icon("plus", size=16),
                "Cadastrar primeira moto",
                on_click=MotocicletasState.abrir_cadastro,
            ),
            spacing="3",
            align="center",
            padding_y="1.5rem",
        ),
        width="100%",
        background=FUNDO_CARTAO,
        border=f"1px solid {BORDA_CARTAO}",
    )


# ----------------------------------------------------------------------
# Formulário (diálogo)
# ----------------------------------------------------------------------


def _secao(titulo: str, *campos: rx.Component, colunas: str = "2") -> rx.Component:
    cabecalho = (
        [rx.text(titulo, size="1", weight="bold", color=TEXTO_SUAVE, text_transform="uppercase", letter_spacing="0.06em")]
        if titulo
        else []
    )
    return rx.vstack(
        *cabecalho,
        rx.grid(
            *campos,
            columns=rx.breakpoints(initial="1", sm=colunas),
            spacing="3",
            width="100%",
        ),
        rx.divider(),
        spacing="3",
        width="100%",
    )


def _campo(rotulo: str, controle: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="2", weight="medium"),
        controle,
        spacing="1",
        width="100%",
    )


def _campo_foto() -> rx.Component:
    previa = rx.cond(
        MotocicletasState.foto_temp != "",
        rx.image(
            src=rx.get_upload_url(MotocicletasState.foto_temp),
            alt="Prévia da foto da motocicleta",
            width="100%",
            height="100%",
            object_fit="cover",
        ),
        rx.cond(
            MotocicletasState.foto_atual_url != "",
            rx.image(
                src=MotocicletasState.foto_atual_url,
                alt="Foto atual da motocicleta",
                width="100%",
                height="100%",
                object_fit="cover",
            ),
            rx.vstack(
                rx.icon("image-plus", size=28, color=rx.color("gray", 8)),
                rx.text("Adicionar foto da motocicleta", size="2", color=TEXTO_SUAVE),
                align="center",
                justify="center",
                spacing="2",
                height="100%",
            ),
        ),
    )
    tem_foto = (MotocicletasState.foto_temp != "") | (MotocicletasState.foto_atual_url != "")
    return rx.vstack(
        rx.text("Foto da motocicleta", size="2", weight="medium"),
        rx.box(
            previa,
            width="100%",
            max_width="360px",
            aspect_ratio="4 / 3",
            border_radius="0.6rem",
            overflow="hidden",
            background=rx.color("gray", 3),
            border=f"1px solid {rx.color('gray', 5)}",
        ),
        rx.flex(
            rx.upload(
                rx.hstack(
                    rx.icon("upload", size=16),
                    rx.text(rx.cond(tem_foto, "Trocar foto", "Selecionar foto")),
                    spacing="2",
                    align="center",
                ),
                id=UPLOAD_ID,
                accept={
                    "image/jpeg": [".jpg", ".jpeg"],
                    "image/png": [".png"],
                    "image/webp": [".webp"],
                },
                max_files=1,
                multiple=False,
                on_drop=MotocicletasState.handle_upload_foto(rx.upload_files(upload_id=UPLOAD_ID)),
                border=f"1px dashed {rx.color('gray', 7)}",
                border_radius="0.5rem",
                padding="0.5rem 0.9rem",
                cursor="pointer",
            ),
            rx.cond(
                tem_foto,
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Remover foto",
                    variant="soft",
                    color_scheme="red",
                    on_click=MotocicletasState.remover_foto,
                ),
            ),
            spacing="3",
            wrap="wrap",
            align="center",
        ),
        rx.text("JPG, JPEG, PNG ou WEBP, até 5 MB.", size="1", color=TEXTO_SUAVE),
        rx.cond(
            MotocicletasState.erro_foto != "",
            rx.text(MotocicletasState.erro_foto, color="red", size="2"),
        ),
        spacing="2",
        width="100%",
    )


def _formulario() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(rx.cond(MotocicletasState.form_id, "Editar motocicleta", "Cadastrar motocicleta")),
            rx.vstack(
                rx.text("Informações da motocicleta", size="1", weight="bold", color=TEXTO_SUAVE,
                        text_transform="uppercase", letter_spacing="0.06em"),
                _campo_foto(),
                _secao(
                    "",
                    _campo("Marca *", rx.input(placeholder="Harley-Davidson", value=MotocicletasState.marca,
                                               on_change=MotocicletasState.set_marca)),
                    _campo("Modelo *", rx.input(placeholder="Iron 883", value=MotocicletasState.modelo,
                                                on_change=MotocicletasState.set_modelo)),
                    _campo("Ano *", rx.input(placeholder="2022", type="number", min="1900",
                                             value=MotocicletasState.ano, on_change=MotocicletasState.set_ano)),
                    _campo("Cor", rx.input(placeholder="Preta", value=MotocicletasState.cor,
                                           on_change=MotocicletasState.set_cor)),
                    _campo("Placa", rx.input(placeholder="ABC1D23", value=MotocicletasState.placa,
                                             on_change=MotocicletasState.set_placa)),
                    _campo("Chassi", rx.input(placeholder="17 caracteres", value=MotocicletasState.chassi,
                                              on_change=MotocicletasState.set_chassi)),
                    _campo("Quilometragem", rx.input(placeholder="0", type="number", min="0",
                                                     value=MotocicletasState.quilometragem,
                                                     on_change=MotocicletasState.set_quilometragem)),
                ),
                _secao(
                    "Estoque",
                    _campo("Status", rx.select(STATUS_MOTO, value=MotocicletasState.status,
                                               on_change=MotocicletasState.definir_status, width="100%")),
                    _campo(
                        "Em estoque",
                        rx.hstack(
                            rx.switch(
                                checked=MotocicletasState.em_estoque,
                                on_change=MotocicletasState.set_em_estoque,
                                disabled=MotocicletasState.status_define_estoque,
                            ),
                            rx.text(rx.cond(MotocicletasState.em_estoque, "Sim", "Não"), size="2"),
                            spacing="2",
                            align="center",
                            min_height="32px",
                        ),
                    ),
                ),
                _secao(
                    "Valores",
                    _campo("Preço de compra (R$)", rx.input(placeholder="0,00", input_mode="decimal",
                                                            value=MotocicletasState.preco_compra,
                                                            on_change=MotocicletasState.set_preco_compra)),
                    _campo("Preço de venda (R$)", rx.input(placeholder="0,00", input_mode="decimal",
                                                           value=MotocicletasState.preco_venda,
                                                           on_change=MotocicletasState.set_preco_venda)),
                ),
                _secao(
                    "Cliente",
                    _campo("Pesquisar cliente", rx.input(
                        rx.input.slot(rx.icon("search", size=16)),
                        placeholder="Digite o nome...",
                        value=MotocicletasState.pesquisa_cliente,
                        on_change=MotocicletasState.set_pesquisa_cliente,
                    )),
                    _campo("Cliente", rx.select(MotocicletasState.opcoes_cliente_form,
                                                value=MotocicletasState.cliente_selecionado,
                                                on_change=MotocicletasState.set_cliente_selecionado,
                                                width="100%")),
                ),
                _secao(
                    "Informações adicionais",
                    _campo("Data de entrada", rx.input(type="date", value=MotocicletasState.data_entrada,
                                                       on_change=MotocicletasState.set_data_entrada)),
                    _campo("Observações", rx.text_area(value=MotocicletasState.observacoes,
                                                       on_change=MotocicletasState.set_observacoes,
                                                       placeholder="Detalhes, acessórios, histórico...")),
                ),
                rx.cond(
                    MotocicletasState.erro_form != "",
                    rx.callout(MotocicletasState.erro_form, icon="triangle_alert", color_scheme="red", width="100%"),
                ),
                rx.flex(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=MotocicletasState.cancelar,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    rx.button(
                        rx.icon("check", size=16),
                        rx.cond(MotocicletasState.form_id, "Salvar alterações", "Cadastrar Moto"),
                        on_click=MotocicletasState.salvar,
                        loading=MotocicletasState.salvando,
                        width=rx.breakpoints(initial="100%", sm="auto"),
                    ),
                    direction=rx.breakpoints(initial="column-reverse", sm="row"),
                    justify="end",
                    spacing="3",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="95vw",
            max_width="760px",
            max_height="90vh",
            overflow_y="auto",
        ),
        open=MotocicletasState.dialogo_aberto,
        on_open_change=MotocicletasState.alternar_dialogo,
    )


def _foto_ampliada() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Foto da motocicleta", size="3"),
            # Durante a animação de fechamento a URL já está vazia; <img src="">
            # faria o navegador buscar a página de novo.
            rx.cond(
                MotocicletasState.foto_ampliada_url != "",
                rx.image(
                    src=MotocicletasState.foto_ampliada_url,
                    alt="Foto ampliada da motocicleta",
                    width="100%",
                    max_height="75vh",
                    object_fit="contain",
                    border_radius="0.6rem",
                ),
            ),
            rx.flex(
                rx.dialog.close(rx.button("Fechar", variant="soft", color_scheme="gray")),
                justify="end",
                padding_top="0.75rem",
            ),
            width="95vw",
            max_width="900px",
        ),
        open=MotocicletasState.foto_ampliada_url != "",
        on_open_change=MotocicletasState.alternar_foto_ampliada,
    )


# ----------------------------------------------------------------------
# Página
# ----------------------------------------------------------------------


def motocicletas_page() -> rx.Component:
    return page(
        rx.flex(
            rx.button(
                rx.icon("plus", size=16),
                "Cadastrar Moto",
                on_click=MotocicletasState.abrir_cadastro,
                size="3",
                width=rx.breakpoints(initial="100%", sm="auto"),
            ),
            justify="end",
            width="100%",
            margin_top="-0.75rem",
        ),
        rx.cond(
            MotocicletasState.carregando,
            _carregando(),
            rx.cond(
                MotocicletasState.erro_carregamento,
                _erro(),
                rx.cond(
                    MotocicletasState.total_motos == 0,
                    _vazio(),
                    rx.vstack(_resumo(), _filtros(), _tabela(), spacing="4", width="100%"),
                ),
            ),
        ),
        _formulario(),
        _foto_ampliada(),
        title="Motocicletas",
        subtitle="Gerencie as motocicletas cadastradas, estoque e informações dos veículos.",
    )
