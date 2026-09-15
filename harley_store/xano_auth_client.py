"""
Cliente HTTP para o grupo "Authentication" do Xano (login e cadastro na
tabela `user`).

É um módulo separado de `xano_client.py` porque o grupo Authentication tem
uma base URL própria (canonical diferente do grupo de CRUD genérico usado
pelas outras tabelas do sistema). A lógica de retentativa em erro 429 é
reaproveitada de `xano_client._request` em vez de duplicada aqui.
"""

from __future__ import annotations

from . import xano_client

BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:lH_WsSPl"


class XanoAuthError(Exception):
    """Erro retornado pelo Xano (mensagem já pronta pra decidir o que mostrar)."""


async def _post(caminho: str, dados: dict) -> dict:
    resposta = await xano_client._request("POST", f"{BASE_URL}/{caminho}", json=dados)
    if resposta.status_code >= 400:
        try:
            mensagem = resposta.json().get("message", "")
        except ValueError:
            mensagem = ""
        raise XanoAuthError(mensagem or f"Erro {resposta.status_code} ao chamar {caminho}")
    return resposta.json()


async def login(email: str, senha: str) -> dict:
    """Retorna {"authToken", "user_id", "name"}. Levanta XanoAuthError em credenciais inválidas."""
    return await _post("auth/login", {"email": email, "password": senha})


async def signup(nome: str, email: str, senha: str) -> dict:
    """Retorna {"authToken", "user_id"}. Levanta XanoAuthError se o email já existe."""
    return await _post("auth/signup", {"name": nome, "email": email, "password": senha})
