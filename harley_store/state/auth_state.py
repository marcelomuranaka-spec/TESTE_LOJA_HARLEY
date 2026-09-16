"""
State de autenticação (login / cadastro de usuário).

Login e cadastro usam a tabela `user` do Xano (grupo "Authentication" —
ver `xano_auth_client.py`), não um banco local. Quem está logado é
lembrado através de três cookies (`rx.Cookie`): `usuario_logado` (nome
pra exibir), `auth_token` (token do Xano) e `auth_user_id` (id numérico
do Xano) — por isso todo `on_load` de página protegida chama primeiro
`AuthState.exigir_login`, que redireciona para `/login` se não houver
token.

A redefinição de senha ("Esqueci minha senha", na aba Entrar) fica nos
campos/eventos com prefixo `rec_` mais abaixo. Ela não envia email nem
código: pede o email da conta e a senha nova, e grava direto pelo
endpoint `user/reset-password` do grupo Admin do Xano (a receita pra
criar esse endpoint está no topo de `xano_admin_client.py`).
"""

from __future__ import annotations

import re

import reflex as rx

from .. import xano_admin_client, xano_auth_client
from ..xano_admin_client import XanoEndpointAusente
from ..xano_auth_client import XanoAuthError

_SENHA_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")
_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _senha_valida(senha: str) -> bool:
    """Mesma regra de senha exigida pelo Xano: 8+ caracteres, com letra e número."""
    return bool(_SENHA_REGEX.match(senha))


def _email_valido(email: str) -> bool:
    """Conferência de formato (não de existência) — usada também em UsuariosState."""
    return bool(_EMAIL_REGEX.match(email))


_MENSAGEM_SENHA_INVALIDA = "A senha precisa ter pelo menos 8 caracteres, com letras e números."
_MENSAGEM_RESPOSTA_INESPERADA = "Resposta inesperada do servidor. Tente novamente em instantes."
_MENSAGEM_SEM_ENDPOINT = (
    "A redefinição de senha ainda não foi ligada no Xano. "
    "Crie o endpoint POST /user/reset-password no grupo Admin "
    "(passo a passo no topo do arquivo xano_admin_client.py)."
)


class AuthState(rx.State):
    # Guarda o nome do usuário logado (só pra exibição); "" significa deslogado.
    usuario_logado: str = rx.Cookie("", name="hs_usuario")
    auth_token: str = rx.Cookie("", name="hs_auth_token")
    # O prefixo impede que o Reflex reidrate o id como um número.
    auth_user_id: str = rx.Cookie("", name="hs_auth_user_id_v3")

    # Campos do formulário de login
    login_email: str = ""
    login_senha: str = ""
    login_erro: str = ""

    # Campos do formulário de cadastro
    cad_nome_completo: str = ""
    cad_email: str = ""
    cad_senha: str = ""
    cad_confirmar_senha: str = ""
    cad_erro: str = ""

    # Campos do "Esqueci minha senha" (diálogo aberto pela aba Entrar).
    recuperacao_aberta: bool = False
    rec_email: str = ""
    rec_senha: str = ""
    rec_confirmar_senha: str = ""
    rec_erro: str = ""
    rec_sucesso: str = ""

    aba_atual: str = "entrar"  # "entrar" | "cadastrar"

    @rx.var
    def esta_logado(self) -> bool:
        return bool(self.auth_token)

    @rx.event
    def exigir_login(self):
        """Chamar no on_load de toda página protegida."""
        if not self.auth_token:
            return rx.redirect("/login")

    @rx.event
    def redirecionar_se_ja_logado(self):
        """Chamar no on_load da página de login — se já estiver logado, pula para o painel."""
        if self.auth_token:
            return rx.redirect("/painel")

    @rx.event
    def definir_aba(self, aba: str):
        self.aba_atual = aba
        self.login_erro = ""
        self.cad_erro = ""

    @rx.event
    async def fazer_login(self):
        email = self.login_email.strip()
        senha = self.login_senha
        if not email or not senha:
            self.login_erro = "Preencha email e senha."
            return

        try:
            resultado = await xano_auth_client.login(email, senha)
        except XanoAuthError:
            self.login_erro = "Email ou senha incorretos."
            return
        except Exception:
            self.login_erro = "Não foi possível conectar. Tente novamente em instantes."
            return

        # O token é obrigatório: sem ele o app acharia que ninguém está
        # logado e `exigir_login` devolveria o usuário para cá em loop.
        # Antes isso levantava KeyError e derrubava o event handler.
        token = resultado.get("authToken")
        if not token:
            self.login_erro = _MENSAGEM_RESPOSTA_INESPERADA
            return

        self.login_erro = ""
        self.login_senha = ""
        self.auth_token = token
        self.auth_user_id = f"user:{resultado.get('user_id', '')}"
        self.usuario_logado = resultado.get("name") or email
        return rx.redirect("/painel")

    @rx.event
    async def cadastrar(self):
        nome_completo = self.cad_nome_completo.strip()
        email = self.cad_email.strip()
        senha = self.cad_senha
        confirmar = self.cad_confirmar_senha

        if not nome_completo or not email or not senha:
            self.cad_erro = "Preencha todos os campos."
            return
        if not _senha_valida(senha):
            self.cad_erro = _MENSAGEM_SENHA_INVALIDA
            return
        if senha != confirmar:
            self.cad_erro = "As senhas não coincidem."
            return

        try:
            resultado = await xano_auth_client.signup(nome_completo, email, senha)
        except XanoAuthError as erro:
            if "already exists" in str(erro).lower():
                self.cad_erro = "Esse email já está cadastrado."
            else:
                self.cad_erro = "Não foi possível criar a conta. Verifique os dados e tente novamente."
            return
        except Exception:
            self.cad_erro = "Não foi possível conectar. Tente novamente em instantes."
            return

        token = resultado.get("authToken")
        if not token:
            self.cad_erro = _MENSAGEM_RESPOSTA_INESPERADA
            return

        self.cad_erro = ""
        self.cad_nome_completo = ""
        self.cad_email = ""
        self.cad_senha = ""
        self.cad_confirmar_senha = ""
        self.auth_token = token
        self.auth_user_id = f"user:{resultado.get('user_id', '')}"
        self.usuario_logado = nome_completo
        return rx.redirect("/painel")

    @rx.event
    def alternar_recuperacao(self, aberta: bool):
        """Abre/fecha o diálogo de redefinição de senha, sempre do zero.

        Ao abrir, já aproveita o email digitado no login (se houver) pra
        poupar digitação; ao fechar, limpa tudo para a próxima vez.
        """
        self.recuperacao_aberta = aberta
        self.rec_email = self.login_email.strip() if aberta else ""
        self.rec_senha = ""
        self.rec_confirmar_senha = ""
        self.rec_erro = ""
        self.rec_sucesso = ""

    @rx.event
    async def redefinir_senha(self):
        email = self.rec_email.strip()
        senha = self.rec_senha

        if not email or not senha:
            self.rec_erro = "Preencha o email e a nova senha."
            return
        if not _email_valido(email):
            self.rec_erro = "Email inválido."
            return
        if not _senha_valida(senha):
            self.rec_erro = _MENSAGEM_SENHA_INVALIDA
            return
        if senha != self.rec_confirmar_senha:
            self.rec_erro = "As senhas não coincidem."
            return

        try:
            await xano_admin_client.redefinir_senha(email, senha)
        except XanoEndpointAusente:
            self.rec_erro = _MENSAGEM_SEM_ENDPOINT
            return
        except XanoAuthError as erro:
            # O Xano manda a mensagem pronta (ex.: "Email não cadastrado.").
            self.rec_erro = str(erro) or "Não foi possível redefinir a senha."
            return
        except Exception:
            self.rec_erro = "Não foi possível conectar. Tente novamente em instantes."
            return

        # Deu certo: deixa o login pronto pra usar a senha nova.
        self.rec_erro = ""
        self.rec_senha = ""
        self.rec_confirmar_senha = ""
        self.rec_sucesso = "Senha redefinida! Feche esta janela e entre com a senha nova."
        self.login_email = email
        self.login_senha = ""
        self.login_erro = ""

    @rx.event
    def sair(self):
        self.auth_token = ""
        self.auth_user_id = ""
        self.usuario_logado = ""
        # Não deixar a senha digitada em memória nem o erro antigo na tela
        # de login depois de sair.
        self.login_senha = ""
        self.login_erro = ""
        self.cad_erro = ""
        self.aba_atual = "entrar"
        self.recuperacao_aberta = False
        self.rec_email = ""
        self.rec_senha = ""
        self.rec_confirmar_senha = ""
        self.rec_erro = ""
        self.rec_sucesso = ""
        return rx.redirect("/login")

