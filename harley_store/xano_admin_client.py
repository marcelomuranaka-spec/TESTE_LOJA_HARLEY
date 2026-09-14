"""
Cliente HTTP para o grupo "Admin" do Xano — endpoints dedicados pra tela de
"Usuários do sistema" (listar/editar email/excluir contas na tabela `user`).

Grupo separado do "Authentication" (login/cadastro/reset) porque é um grupo
de API diferente no Xano, com sua própria base URL. A lógica de retentativa
em erro 429 é reaproveitada de `xano_client._request`.
"""

from __future__ import annotations

from . import xano_client

BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:KegVKtiw"


def listar_usuarios() -> list[dict]:
    resposta = xano_client._request("GET", f"{BASE_URL}/user/list")
    resposta.raise_for_status()
    return resposta.json() or []


def atualizar_email(usuario_id: int, novo_email: str) -> dict:
    resposta = xano_client._request(
        "POST", f"{BASE_URL}/user/update-email", json={"id": usuario_id, "email": novo_email}
    )
    resposta.raise_for_status()
    return resposta.json()


def excluir_usuario(usuario_id: int) -> None:
    resposta = xano_client._request("POST", f"{BASE_URL}/user/delete", json={"id": usuario_id})
    resposta.raise_for_status()
