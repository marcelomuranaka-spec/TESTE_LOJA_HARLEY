"""
State de Usuários do sistema (contas de login na tabela `user` do Xano) —
diferente de Funcionários (que é cadastro de RH). Aqui é possível criar
novas contas de acesso, corrigir o email e excluir contas existentes.
"""

from __future__ import annotations

import reflex as rx

from .. import xano_admin_client
from ..xano_client import texto
from ..xano_auth_client import XanoAuthError, signup
from .auth_state import (
    AuthState,
    _MENSAGEM_SENHA_INVALIDA,
    _email_valido,
    _senha_valida,
)


class UsuariosState(rx.State):
    usuarios: list[dict] = []

    novo_nome_completo: str = ""
    novo_email: str = ""
    nova_senha: str = ""
    nova_confirmar_senha: str = ""
    erro: str = ""
    # Erro das ações feitas direto na lista (alterar email / excluir).
    erro_lista: str = ""

    @rx.event
    async def carregar(self):
        try:
            registros = await xano_admin_client.listar_usuarios()
        except Exception:
            self.erro_lista = "Não foi possível carregar os usuários. Tente novamente."
            return
        # `texto()` protege contra nome/email nulos no Xano: ordenar ou
        # exibir None no lugar de string derrubava a tela inteira.
        self.usuarios = [
            {
                "id": str(r["id"]),
                "nome": texto(r.get("name")),
                "email": texto(r.get("email")),
            }
            for r in sorted(registros, key=lambda r: texto(r.get("name")).lower())
        ]

    @rx.event
    def limpar_formulario(self):
        self.novo_nome_completo = ""
        self.novo_email = ""
        self.nova_senha = ""
        self.nova_confirmar_senha = ""
        self.erro = ""

    @rx.event
    async def salvar(self):
        nome_completo = self.novo_nome_completo.strip()
        email = self.novo_email.strip()
        senha = self.nova_senha
        if not nome_completo or not email or not senha:
            self.erro = "Preencha todos os campos."
            return
        if not _email_valido(email):
            self.erro = "Email inválido."
            return
        if not _senha_valida(senha):
            self.erro = _MENSAGEM_SENHA_INVALIDA
            return
        if senha != self.nova_confirmar_senha:
            self.erro = "As senhas não coincidem."
            return

        try:
            await signup(nome_completo, email, senha)
        except XanoAuthError as erro:
            if "already exists" in str(erro).lower():
                self.erro = "Esse email já está cadastrado."
            else:
                self.erro = "Não foi possível criar a conta. Verifique os dados e tente novamente."
            return
        except Exception:
            self.erro = "Não foi possível conectar. Tente novamente em instantes."
            return

        self.limpar_formulario()
        await self.carregar()

    @rx.event
    async def atualizar_email(self, usuario_id: str, novo_email: str):
        """Chamado quando o campo de email da lista perde o foco (on_blur)."""
        novo_email = novo_email.strip()
        atual = next((u["email"] for u in self.usuarios if u["id"] == usuario_id), "")
        # Só sair do campo, sem ter mudado nada, não pode gastar uma
        # requisição (o plano Free do Xano tem limite por minuto).
        if novo_email == atual:
            self.erro_lista = ""
            return
        if not _email_valido(novo_email):
            self.erro_lista = "Email inválido — a alteração não foi salva."
            await self.carregar()
            return

        try:
            await xano_admin_client.atualizar_email(int(usuario_id), novo_email)
        except Exception:
            self.erro_lista = "Não foi possível alterar o email (verifique se já está em uso)."
            await self.carregar()
            return

        self.erro_lista = ""
        await self.carregar()

    @rx.event
    async def excluir(self, usuario_id: str):
        try:
            total = len(await xano_admin_client.listar_usuarios())
        except Exception:
            self.erro_lista = "Não foi possível excluir agora. Tente novamente."
            return
        if total <= 1:
            return rx.window_alert("Não é possível excluir o único usuário do sistema.")

        try:
            await xano_admin_client.excluir_usuario(int(usuario_id))
        except Exception:
            self.erro_lista = "Não foi possível excluir a conta. Tente novamente."
            return

        self.erro_lista = ""
        auth = await self.get_state(AuthState)
        if auth.auth_user_id == f"user:{usuario_id}":
            # Excluiu a própria conta: derruba a sessão e volta pro login.
            auth.auth_token = ""
            auth.auth_user_id = ""
            auth.usuario_logado = ""
            self.usuarios = []
            return rx.redirect("/login")

        await self.carregar()
