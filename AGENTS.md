# AGENTS.md — Harley Store

Instruções para agentes de IA (e para qualquer pessoa nova) que forem trabalhar
neste repositório. Leia este arquivo antes de propor ou aplicar qualquer mudança.

Documentos complementares:

- [docs/project-overview.md](docs/project-overview.md) — o que é o sistema, arquitetura e estado atual.
- [docs/domain-model.md](docs/domain-model.md) — entidades, relacionamentos e invariantes do domínio.
- [docs/explore/2026-09-16-decomposicao-funcional.md](docs/explore/2026-09-16-decomposicao-funcional.md) — decomposição funcional e ordem de implementação sugerida.
- [xano/knowledge/agents.md](xano/knowledge/agents.md) — convenções do workspace XanoScript (backend).

## 1. O que é o projeto

Aplicativo web de gestão para uma loja/oficina de motos (concessionária +
oficina). Escrito em **Reflex 0.7.14** (Python puro, sem HTML/JS escrito à mão),
com os dados em um **backend Xano** (REST). É usado no balcão da loja e também
instalado como **PWA no iPhone**.

## 2. Stack e execução

| Item | Valor |
|------|-------|
| Linguagem | Python 3.11 / 3.12 / 3.13 (**nunca 3.14** — Reflex 0.7 não suporta) |
| Framework | Reflex 0.7.14 |
| Backend de dados | Xano (3 grupos de API REST, ver abaixo) |
| HTTP client | `httpx` (assíncrono) |
| Banco local | SQLite + SQLModel + Alembic — **legado, não usado pelas telas** (ver seção 6) |

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
reflex run          # http://localhost:3000
```

## 3. Estrutura do código

```
harley_store/
├── rxconfig.py                 # configuração do app Reflex
├── AGENTS.md                   # este arquivo
├── docs/                       # documentação de produto/domínio
├── openspec/                   # workflow spec-driven (config, specs, changes)
├── xano/                       # backend XanoScript versionado (.xs)
├── xano_import/                # CSVs da carga inicial + instruções
├── assets/                     # manifest PWA e ícones
└── harley_store/
    ├── harley_store.py         # rotas (app.add_page)
    ├── models.py               # SQLModel legado + constantes de domínio
    ├── xano_client.py          # CRUD genérico no Xano + helpers de conversão
    ├── xano_auth_client.py     # grupo Authentication (login/signup)
    ├── xano_admin_client.py    # grupo Admin (usuários, reset de senha)
    ├── components/             # layout e componentes compartilhados
    ├── state/                  # um arquivo por tela: dados + regras de negócio
    └── pages/                  # um arquivo por tela: só o visual
```

**Regra estrutural:** toda tela é sempre o par `state/<algo>_state.py` +
`pages/<algo>.py`. O `state` carrega dados e aplica regras; a `page` só desenha e
chama eventos do state. Ao adicionar uma tela nova: crie o par, registre a rota
em `harley_store/harley_store.py` (com `AuthState.exigir_login` como **primeiro**
item de `on_load`) e o link em `components/layout.py` (`MENU_ITEMS`).

## 4. Convenções obrigatórias

1. **Português do Brasil** em nomes de variáveis, funções, comentários,
   docstrings, mensagens de UI e documentação. O código existente é todo em
   pt-BR; mantenha.
2. **Nada de chamada de rede bloqueante.** Todo event handler que fala com o
   Xano é `async` e usa `await`. Uma chamada síncrona trava o loop de eventos do
   Reflex inteiro e o navegador chega a mostrar "Cannot connect to server".
3. **Sempre normalize dados vindos do Xano** com `xano.texto()`, `xano.numero()`,
   `xano.inteiro()` e `xano.epoch_ms_para_datetime()`. Campos nulos derrubam a
   tela em `sorted()`, `.lower()` e formatação numérica.
4. **`PATCH` do Xano não é parcial**: `xano.atualizar()` exige o registro
   completo. Busque o registro, altere o campo e reenvie tudo menos o `id`.
5. **Toda interface nova nasce responsiva.** O app roda como PWA no iPhone;
   telas pequenas são uso normal, não caso extremo. Use largura relativa, botões
   que empilham, altura máxima com rolagem em diálogos. Em Reflex 0.7, props
   tipadas como `Responsive` (`size` de `rx.heading`, `direction` de `rx.flex`)
   exigem `rx.breakpoints(initial=..., md=...)` — listas quebram a compilação.
6. **Exclusão sempre com confirmação**, usando `components/confirm_dialog.py`.
7. **Plano Free do Xano tem limite de requisições por minuto.** Evite chamadas
   redundantes (carregar a mesma lista duas vezes na mesma tela) e não faça
   requisição em `on_blur` quando nada mudou. `xano_client._request` já faz
   retentativa com espera crescente em HTTP 429.

## 5. Limites de autonomia (peça antes de agir)

- **Escopo de autenticação é decisão do usuário.** O fluxo de recuperação de
  senha já foi removido a pedido e depois reintroduzido a pedido. Não remova nem
  reintroduza esse tipo de funcionalidade por iniciativa própria — confirme antes.
- **Não derrube funcionalidade existente** ao adicionar algo novo. As abas
  "Entrar" e "Criar conta" da tela de login, em especial, devem ser preservadas
  como estão.
- **Não altere o esquema de dados do Xano** (tabelas em `xano/table/*.xs`) sem
  uma Change aprovada: o workspace é a fonte de verdade em produção e o plano
  Free não expõe a Metadata API, então mudanças de esquema são manuais.
- **Não commite dados reais da loja** (`*.db`, `uploaded_files/`, `.env`).

## 6. Dívidas e armadilhas conhecidas

- `models.py`, `alembic/` e `harley_store.db` são **legado**: nenhum state usa
  mais `rx.session()`. O arquivo só é importado pelas constantes
  `TIPOS_FUNCIONARIO`, `TIPOS_TRANSACAO` e `STATUS_OS`. Não trate o SQLite como
  fonte de dados.
- O **token de autenticação não é enviado** nas chamadas de dados: o grupo CRUD
  do Xano responde sem token. O login protege a navegação, não a API.
- O grupo de API CRUD genérico (`api:LtU_pM2N`) **não está versionado** em
  `xano/api/` — só Authentication, Admin, Event Logs e Relatorios estão.
- `relatorios/resumo_GET.xs`, `function/relatorio/resumo_operacoes.xs` e
  `function/utils/template_processo.xs` são **esqueletos vazios**.
- Vendas (`transacoes`) não têm tabela de itens; o produto escolhido só serve
  para calcular valor e baixar estoque.
- Exclusão de venda, compra ou OS **não estorna estoque**.
- Não há testes automatizados, lint nem CI no repositório.

## 7. Workflow de mudanças (OpenSpec)

Este repositório usa OpenSpec (`openspec/`, CLI `openspec` 1.12). O ciclo é
**Propose → Review → Apply → Verify → Archive**:

```bash
openspec list                      # changes ativas
openspec new change "<nome>"       # nunca crie a pasta da change à mão
openspec status --change "<nome>" --json
openspec validate
openspec archive "<nome>"
```

Artefatos de uma change (schema `spec-driven`): `proposal.md`, `design.md`,
`specs/<capability>/spec.md`, `tasks.md`. Por configuração
(`openspec/config.yaml`), os artefatos são escritos em **pt-BR**, mantendo em
inglês apenas os cabeçalhos estruturais do OpenSpec e as palavras-chave
SHALL/MUST.

Cada Change deve ter **escopo pequeno, vertical e verificável**: uma capacidade
de ponta a ponta (dado → regra → API → tela), não uma camada isolada.
