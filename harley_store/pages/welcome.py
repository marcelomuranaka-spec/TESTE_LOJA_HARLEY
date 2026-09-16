import reflex as rx


FUNDO = "#090909"
LARANJA = "#f76511"
LARANJA_CLARO = "#ff8a3d"
LOGO_SRC = "/harley-davidson-logo.png"


_ESTILOS = """
@keyframes welcome-fundo {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes welcome-logo {
  from { opacity: 0; transform: translateY(18px) scale(.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes welcome-conteudo {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes welcome-brilho {
  0%, 100% { opacity: .28; transform: translate(-50%, -50%) scale(.92); }
  50% { opacity: .46; transform: translate(-50%, -50%) scale(1.04); }
}
.welcome-fundo { animation: welcome-fundo 700ms ease-out both; }
.welcome-logo { animation: welcome-logo 900ms 120ms cubic-bezier(.2,.75,.25,1) both; }
.welcome-conteudo { animation: welcome-conteudo 650ms 500ms ease-out both; }
.welcome-entrada { animation: welcome-conteudo 650ms 700ms ease-out both; }
.welcome-brilho { animation: welcome-brilho 4s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .welcome-fundo, .welcome-logo, .welcome-conteudo, .welcome-entrada, .welcome-brilho {
    animation: none;
  }
}
"""


def welcome_page() -> rx.Component:
    return rx.box(
        rx.el.style(_ESTILOS),
        rx.box(class_name="welcome-brilho", position="absolute", top="42%", left="50%", width="min(72vw, 520px)", height="min(72vw, 520px)", border_radius="50%", background="radial-gradient(circle, rgba(247, 101, 17, .18) 0%, rgba(247, 101, 17, .05) 38%, transparent 70%)", filter="blur(20px)", pointer_events="none"),
        rx.vstack(
            rx.box(
                rx.image(
                    src=LOGO_SRC,
                    alt="Logotipo Harley-Davidson",
                    class_name="welcome-logo",
                    width="min(78vw, 460px)",
                    height="min(52vh, 360px)",
                    object_fit="contain",
                ),
                position="relative",
                z_index="1",
            ),
            rx.vstack(
                rx.text(
                    "SISTEMA DE GESTÃO",
                    color="#f4eee8",
                    font_size=rx.breakpoints(initial="1rem", md="1.2rem"),
                    font_weight="700",
                    letter_spacing=".18em",
                    text_align="center",
                ),
                rx.text(
                    "Oficina • Clientes • Funcionários • Serviços • Estoque",
                    color="#aaa39d",
                    font_size=rx.breakpoints(initial=".72rem", md=".85rem"),
                    text_align="center",
                    padding_x="1rem",
                ),
                class_name="welcome-conteudo",
                spacing="2",
                align="center",
            ),
            rx.button(
                "ENTRAR NO SISTEMA",
                on_click=rx.redirect("/login"),
                class_name="welcome-entrada",
                aria_label="Entrar no sistema",
                background="transparent",
                border=f"1px solid {LARANJA}",
                color="#fff7f0",
                padding_x=rx.breakpoints(initial="1.4rem", md="2rem"),
                padding_y=".85rem",
                margin_top="1.3rem",
                letter_spacing=".08em",
                font_weight="700",
                cursor="pointer",
                transition="all 250ms ease",
                _hover={
                    "background": LARANJA,
                    "border_color": LARANJA_CLARO,
                    "box_shadow": "0 0 24px rgba(247, 101, 17, .3)",
                    "transform": "scale(1.03)",
                },
                _focus_visible={"outline": f"2px solid {LARANJA_CLARO}", "outline_offset": "3px"},
            ),
            align="center",
            justify="center",
            spacing="0",
            width="100%",
            max_width="700px",
            padding_x="1rem",
            z_index="1",
        ),
        class_name="welcome-fundo",
        position="relative",
        overflow="hidden",
        width="100%",
        min_height="100vh",
        background="radial-gradient(circle at 50% 42%, #24211f 0%, #11100f 38%, #090909 76%)",
        background_image="linear-gradient(135deg, rgba(255,255,255,.035) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.035) 50%, rgba(255,255,255,.035) 75%, transparent 75%)",
        background_size="5px 5px",
        display="flex",
        align_items="center",
        justify_content="center",
    )
