"""
Cliente HTTP para o backend Xano (workspace HARLEY, instância Free).

Os states em `state/` usavam `rx.session()` (SQLModel/SQLite local). Este
módulo troca a fonte de dados pelas APIs REST publicadas no Xano, mantendo
a mesma forma de uso: funções simples que recebem/retornam `dict`.

Detalhes importantes do Xano que este cliente já resolve para quem chama:

- O endpoint PATCH gerado pelo assistente "CRUD Database Operations" do
  Xano exige TODOS os campos obrigatórios da tabela (não é um PATCH
  parcial de verdade) — por isso `update()` espera o registro completo,
  não só os campos alterados.
- Campos de data/hora voltam do Xano como epoch em milissegundos (int),
  não como string ISO. `epoch_ms_para_datetime` / `datetime_para_epoch_ms`
  fazem a conversão nos dois sentidos.
- O plano Free do Xano tem limite de requisições por minuto. Como
  algumas telas (ex.: Painel, Compras, Vendas, Ordens de Serviço) fazem
  várias chamadas em sequência para montar os menus/relatórios, é fácil
  esbarrar nesse limite (erro 429) mesmo em uso normal. `_request` faz
  retentativas automáticas com espera crescente antes de desistir.
"""

from __future__ import annotations

import datetime
import time

import httpx

BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:LtU_pM2N"
_TIMEOUT = 15.0
_MAX_TENTATIVAS = 5
_ESPERA_BASE_SEGUNDOS = 1.5


def _request(metodo: str, url: str, **kwargs) -> httpx.Response:
    for tentativa in range(_MAX_TENTATIVAS):
        resposta = httpx.request(metodo, url, timeout=_TIMEOUT, **kwargs)
        if resposta.status_code != 429:
            return resposta
        espera = float(resposta.headers.get("Retry-After", 0)) or _ESPERA_BASE_SEGUNDOS * (2**tentativa)
        time.sleep(min(espera, 20))
    return resposta


def listar(tabela: str) -> list[dict]:
    resposta = _request("GET", f"{BASE_URL}/{tabela}")
    resposta.raise_for_status()
    return resposta.json() or []


def buscar(tabela: str, registro_id: int) -> dict | None:
    resposta = _request("GET", f"{BASE_URL}/{tabela}/{registro_id}")
    if resposta.status_code == 404:
        return None
    resposta.raise_for_status()
    return resposta.json()


def criar(tabela: str, dados: dict) -> dict:
    resposta = _request("POST", f"{BASE_URL}/{tabela}", json=dados)
    resposta.raise_for_status()
    return resposta.json()


def atualizar(tabela: str, registro_id: int, dados: dict) -> dict:
    resposta = _request("PATCH", f"{BASE_URL}/{tabela}/{registro_id}", json=dados)
    resposta.raise_for_status()
    return resposta.json()


def excluir(tabela: str, registro_id: int) -> None:
    resposta = _request("DELETE", f"{BASE_URL}/{tabela}/{registro_id}")
    if resposta.status_code == 404:
        return
    resposta.raise_for_status()


def epoch_ms_para_datetime(valor: int | float | None) -> datetime.datetime:
    if not valor:
        return datetime.datetime.now()
    return datetime.datetime.fromtimestamp(valor / 1000)


def datetime_para_epoch_ms(valor: datetime.datetime | None = None) -> int:
    valor = valor or datetime.datetime.now()
    return int(valor.timestamp() * 1000)
