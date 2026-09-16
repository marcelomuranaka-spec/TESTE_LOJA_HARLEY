import reflex as rx

from ..state.auth_state import AuthState

PRETO = "#111111"
PRETO_CARTAO = "#1a1a1a"
LARANJA = "#F76511"
LARANJA_ESCURO = "#c94e0a"


def _aba_botao(rotulo: str, valor: str) -> rx.Component:
    ativo = AuthState.aba_atual == valor
    return rx.box(
        rx.text(rotulo, weight="bold", size="3"),
        on_click=AuthState.definir_aba(valor),
        padding="0.75rem 0",
        width="50%",
        text_align="center",
        cursor="pointer",
        color=rx.cond(ativo, "white", "#888888"),
        border_bottom=rx.cond(ativo, f"3px solid {LARANJA}", "3px solid transparent"),
        transition="all 0.15s",
    )


def _campo(rotulo: str, value: rx.Var, on_change, tipo: str = "text") -> rx.Component:
    return rx.vstack(
        rx.text(rotulo, size="2", weight="bold", color="white"),
        rx.input(
            value=value,
            on_change=on_change,
            type=tipo,
            width="100%",
            size="3",
            style={
                "backgroundColor": "#0d0d0d",
                "color": "#ffffff",
                "border": "1px solid #3a3a3a",
                "caretColor": LARANJA,
            },
            _focus={"border_color": LARANJA, "outline": "none"},
        ),
        spacing="1",
        width="100%",
        align="start",
    )


# Botões do diálogo: menores no celular para "Redefinir senha" e "Fechar"
# caberem lado a lado numa tela estreita sem o texto estourar.
_TAMANHO_BOTAO = rx.breakpoints(initial="2", md="3")


def _dialogo_esqueci_senha() -> rx.Component:
    """Link "Esqueci minha senha" da aba Entrar + a janela de redefinição.

    É um diálogo (e não uma terceira aba ou outra página) justamente pra
    não mexer em nada do que já existe: as abas Entrar e Criar conta
    continuam exatamente como estavam.

    As cores vêm escritas na mão como no resto desta página porque o
    diálogo é renderizado num portal, fora da árvore do `rx.theme` escuro
    lá de baixo — sem isso ele apareceria claro no meio da tela preta.
    """
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.box(
                rx.text("Esqueci minha senha", size="2", color=LARANJA),
                width="100%",
                text_align="center",
                cursor="pointer",
                padding_top="0.25rem",
                _hover={"textDecoration": "underline"},
            ),
        ),
        rx.dialog.content(
            rx.vstack(
                rx.heading("Redefinir senha", size=rx.breakpoints(initial="4", md="5"), color="white"),
                rx.text(
                    "Informe o email da conta e escolha uma senha nova.",
                    size="2",
                    color="#999999",
                ),
                _campo("Email da conta", AuthState.rec_email, AuthState.set_rec_email, tipo="email"),
                _campo("Nova senha", AuthState.rec_senha, AuthState.set_rec_senha, tipo="password"),
                _campo(
                    "Confirmar nova senha",
                    AuthState.rec_confirmar_senha,
                    AuthState.set_rec_confirmar_senha,
                    tipo="password",
                ),
                rx.cond(
                    AuthState.rec_erro != "",
                    rx.text(AuthState.rec_erro, color="#ff6b6b", size="2"),
                ),
                rx.cond(
                    AuthState.rec_sucesso != "",
                    rx.text(AuthState.rec_sucesso, color="#51cf66", size="2", weight="bold"),
                ),
                rx.flex(
                    rx.dialog.close(
                        rx.button(
                            "Fechar",
                            variant="soft",
                            color_scheme="gray",
                            width="100%",
                            size=_TAMANHO_BOTAO,
                            type="button",
                        ),
                        style={"width": "100%"},
                    ),
                    rx.button(
                        "Redefinir senha",
                        on_click=AuthState.redefinir_senha,
                        width="100%",
                        size=_TAMANHO_BOTAO,
                        background=LARANJA,
                        color="white",
                        type="button",
                        _hover={"background": LARANJA_ESCURO},
                    ),
                    # Sempre lado a lado, inclusive no celular. Os dois têm
                    # width 100% e dividem a linha meio a meio; o que faz o
                    # texto caber em tela estreita é o `_TAMANHO_BOTAO`.
                    direction="row",
                    spacing="3",
                    width="100%",
                    padding_top="0.5rem",
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            background=PRETO_CARTAO,
            border=f"1px solid {LARANJA}",
            width="100%",
            # No celular ocupa a largura da tela menos uma folga lateral; a
            # partir de telas médias volta a ser uma caixa de 380px.
            max_width=["calc(100vw - 1.5rem)", "calc(100vw - 1.5rem)", "380px"],
            padding=["1.1rem", "1.1rem", "1.5rem"],
            # Com o teclado aberto sobra pouca altura: rola em vez de cortar.
            max_height="85vh",
            overflow_y="auto",
        ),
        open=AuthState.recuperacao_aberta,
        on_open_change=AuthState.alternar_recuperacao,
    )


def _formulario_entrar() -> rx.Component:
    return rx.vstack(
        _campo("Email", AuthState.login_email, AuthState.set_login_email, tipo="email"),
        _campo("Senha", AuthState.login_senha, AuthState.set_login_senha, tipo="password"),
        rx.cond(
            AuthState.login_erro != "",
            rx.text(AuthState.login_erro, color="#ff6b6b", size="2"),
        ),
        rx.button(
            "Entrar",
            on_click=AuthState.fazer_login,
            width="100%",
            size="3",
            background=LARANJA,
            color="white",
            _hover={"background": LARANJA_ESCURO},
        ),
        _dialogo_esqueci_senha(),
        spacing="3",
        width="100%",
    )


def _formulario_cadastrar() -> rx.Component:
    return rx.vstack(
        _campo("Nome completo", AuthState.cad_nome_completo, AuthState.set_cad_nome_completo),
        _campo("Email", AuthState.cad_email, AuthState.set_cad_email, tipo="email"),
        _campo("Senha", AuthState.cad_senha, AuthState.set_cad_senha, tipo="password"),
        _campo("Confirmar senha", AuthState.cad_confirmar_senha, AuthState.set_cad_confirmar_senha, tipo="password"),
        rx.cond(
            AuthState.cad_erro != "",
            rx.text(AuthState.cad_erro, color="#ff6b6b", size="2"),
        ),
        rx.button(
            "Criar conta",
            on_click=AuthState.cadastrar,
            width="100%",
            size="3",
            background=LARANJA,
            color="white",
            _hover={"background": LARANJA_ESCURO},
        ),
        spacing="3",
        width="100%",
    )


def login_page() -> rx.Component:
    return rx.theme(
        rx.box(
            rx.center(
                rx.vstack(
                    rx.hstack(
                        rx.icon("flame", size=36, color=LARANJA),
                        rx.heading("HARLEY STORE", size="7", color="white", letter_spacing="1px"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Sistema da loja e da oficina",
                        color="#999999",
                        size="2",
                        padding_bottom="1.5rem",
                    ),
                    rx.box(
                        rx.hstack(
                            _aba_botao("Entrar", "entrar"),
                            _aba_botao("Criar conta", "cadastrar"),
                            width="100%",
                            spacing="0",
                            border_bottom="1px solid #2a2a2a",
                            padding_bottom="1.25rem",
                            margin_bottom="1.25rem",
                        ),
                        rx.cond(
                            AuthState.aba_atual == "entrar",
                            _formulario_entrar(),
                            _formulario_cadastrar(),
                        ),
                        background=PRETO_CARTAO,
                        border=f"1px solid {LARANJA}",
                        border_radius="0.75rem",
                        padding="2rem",
                        width="380px",
                        box_shadow="0 0 40px rgba(247, 101, 17, 0.15)",
                    ),
                    spacing="1",
                    align="center",
                ),
                width="100%",
                height="100vh",
            ),
            width="100%",
            height="100vh",
            background=f"radial-gradient(circle at 50% 20%, #1f1f1f 0%, {PRETO} 60%)",
        ),
        appearance="dark",
        accent_color="orange",
        radius="medium",
        has_background=False,
    )
