"""
Cliente HTTP para o grupo "Admin" do Xano — endpoints dedicados pra tela de
"Usuários do sistema" (listar/editar email/excluir contas na tabela `user`) e
para a redefinição de senha da tela de login.

Grupo separado do "Authentication" (login/cadastro) porque é um grupo de API
diferente no Xano, com sua própria base URL. A lógica de retentativa em erro
429 é reaproveitada de `xano_client._request`.

COMO CRIAR O ENDPOINT DE REDEFINIR SENHA NO XANO
-------------------------------------------------
A função `redefinir_senha()` aqui embaixo chama `POST /user/reset-password`,
que precisa ser criado uma única vez no workspace (o Xano não traz isso
pronto). Enquanto ele não existir, a tela de login mostra um aviso explicando
o que falta — nada quebra.

No Xano: API > grupo "Admin" (api:KegVKtiw) > Add API Endpoint > from scratch

    Verbo/caminho : POST  /user/reset-password
    Inputs        : email     (text)
                    password  (password)

    Function Stack:
      1. Query All Records — tabela `user`
           where: email = input.email
           output as: usuarios
      2. Precondition — usuarios|count > 0
           Error type: notfound   Message: "Email não cadastrado."
      3. Edit Record — tabela `user`
           field_value: usuarios.0.id
           password = input.password  (aplique o filtro `bcrypt` no valor!)
      4. Response: {"ok": true}

O filtro `bcrypt` do passo 3 é obrigatório: sem ele a senha vai pro banco em
texto puro e o `auth/login` nunca mais confere. Depois de publicar (Publish),
a tela de "Esqueci minha senha" passa a funcionar sozinha.

Atenção, é bom você saber: como não há envio de email no projeto, esse
endpoint redefine a senha só com o email da conta — quem souber o email de um
usuário consegue trocar a senha dele. Isso acompanha o modelo atual do
backend, em que os endpoints deste grupo Admin também respondem sem token.
"""

from __future__ import annotations

from . import xano_client
from .xano_auth_client import XanoAuthError

BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:KegVKtiw"

# Mensagem que o Xano devolve quando o caminho não existe no workspace — é o
# que distingue "endpoint ainda não criado" de "endpoint recusou os dados".
_MENSAGEM_ROTA_INEXISTENTE = "unable to locate request"


class XanoEndpointAusente(Exception):
    """O endpoint ainda não foi criado no workspace do Xano (ver topo do arquivo)."""


async def listar_usuarios() -> list[dict]:
    resposta = await xano_client._request("GET", f"{BASE_URL}/user/list")
    resposta.raise_for_status()
    return resposta.json() or []


async def atualizar_email(usuario_id: int, novo_email: str) -> dict:
    resposta = await xano_client._request(
        "POST", f"{BASE_URL}/user/update-email", json={"id": usuario_id, "email": novo_email}
    )
    resposta.raise_for_status()
    return resposta.json()


async def excluir_usuario(usuario_id: int) -> None:
    resposta = await xano_client._request("POST", f"{BASE_URL}/user/delete", json={"id": usuario_id})
    resposta.raise_for_status()


async def redefinir_senha(email: str, nova_senha: str) -> dict:
    """Grava uma senha nova para a conta com esse email.

    Levanta `XanoEndpointAusente` se o endpoint ainda não foi criado no Xano
    (ver a receita no topo do arquivo) e `XanoAuthError` com a mensagem do
    próprio Xano nos demais erros — por exemplo, email não cadastrado.
    """
    resposta = await xano_client._request(
        "POST", f"{BASE_URL}/user/reset-password", json={"email": email, "password": nova_senha}
    )

    if resposta.status_code == 404 and _MENSAGEM_ROTA_INEXISTENTE in resposta.text.lower():
        raise XanoEndpointAusente(
            "O endpoint POST /user/reset-password ainda não existe no Xano."
        )

    if resposta.status_code >= 400:
        try:
            mensagem = resposta.json().get("message", "")
        except ValueError:
            mensagem = ""
        raise XanoAuthError(mensagem or f"Erro {resposta.status_code} ao redefinir a senha.")

    try:
        return resposta.json()
    except ValueError:
        return {}
