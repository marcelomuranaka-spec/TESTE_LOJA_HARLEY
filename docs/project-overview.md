# Visão geral do projeto — Harley Store

Documento de contexto: o que o sistema é hoje, como está construído e onde estão
suas fronteiras. Descreve o **estado observado no repositório** em 16/09/2026;
pontos ainda não decididos aparecem marcados como **(em aberto)**.

## 1. Produto

Sistema de gestão do dia a dia de uma loja/oficina de motos. Cobre quatro
operações que hoje acontecem no balcão e na oficina:

- **Cadastrar** clientes, motos dos clientes, produtos/peças, fornecedores e funcionários.
- **Vender** (balcão, peças, moto) registrando a transação e baixando estoque.
- **Atender na oficina** abrindo Ordens de Serviço com peças utilizadas.
- **Repor estoque** dando entrada de mercadoria de fornecedores.

Mais um painel com indicadores do dia/mês e um extrato recente de operações.

### Contexto de uso

- Usado no computador da loja e **instalado como PWA no iPhone**
  (`assets/manifest.json`, ícones Apple e meta tags de tela cheia em
  `harley_store/harley_store.py`).
- Não há service worker: o app é instalável, mas **não funciona offline**.
- Público: equipe da loja. Número de usuários simultâneos esperado: **(em aberto)**.

## 2. Arquitetura

```
+-------------------------------------------------------------+
|                    Navegador / PWA (iPhone)                 |
|            Frontend Next.js gerado pelo Reflex              |
+----------------------------+--------------------------------+
                             | WebSocket (eventos de State)
                             v
+-------------------------------------------------------------+
|                 Servidor Reflex (Python)                    |
|                                                             |
|   pages/*.py  (visual)  <--->  state/*_state.py (regras)    |
|                                        |                    |
|                   +--------------------+------------------+  |
|                   v                    v                  v  |
|            xano_client.py     xano_auth_client.py   xano_admin_client.py
+-------------------|--------------------|------------------|--+
                    | HTTPS (httpx async)
                    v                    v                  v
+-------------------------------------------------------------+
|                          Xano                               |
|  api:LtU_pM2N (CRUD)  api:lH_WsSPl (Auth)  api:KegVKtiw (Admin)
|                                                             |
|  tabelas: clientes, motos_clientes, funcionarios,           |
|  fornecedores, produtos, entrada_mercadoria,                |
|  itens_compra_estoque, transacoes, ordens_servico,          |
|  itens_ordem_servico, user, event_log                       |
+-------------------------------------------------------------+
```

### Camadas

| Camada | Onde | Responsabilidade |
|--------|------|------------------|
| Apresentação | `harley_store/pages/`, `harley_store/components/` | Desenhar a tela e disparar eventos. Sem regra de negócio. |
| Aplicação/Regras | `harley_store/state/` | Carregar dados, validar entrada, aplicar regra de estoque, orquestrar chamadas. |
| Acesso a dados | `harley_store/xano_client.py`, `xano_auth_client.py`, `xano_admin_client.py` | Falar HTTP com o Xano, normalizar tipos, retentar em 429. |
| Persistência e lógica remota | Workspace Xano (`xano/*.xs`) | Tabelas, autenticação, endpoints administrativos. |

### Rotas registradas

`/login`, `/` (painel), `/produtos`, `/clientes`, `/motos`, `/vendas`,
`/ordens-servico`, `/compras`, `/fornecedores`, `/funcionarios`, `/usuarios`.
Todas exceto `/login` chamam `AuthState.exigir_login` no `on_load`.

## 3. Autenticação e sessão

- Login e cadastro usam a tabela `user` do Xano (grupo Authentication), com
  email e senha. Não existe campo de "usuário/login" separado.
- A sessão é mantida em três cookies: `hs_usuario` (nome exibido),
  `hs_auth_token` (token do Xano) e `hs_auth_user_id_v3` (id prefixado com
  `user:` para o Reflex não reidratar como número).
- O token do Xano expira em **86400 s (24 h)**; o app não renova nem detecta
  expiração explicitamente.
- **O token não é enviado nas chamadas de dados.** `xano_client` não define
  cabeçalho `Authorization`, e os endpoints do grupo CRUD respondem sem token.
  O login hoje protege a navegação da interface, não os dados.
- A tabela `user` tem o campo `role` (`admin` | `member`) e o workspace tem a
  função `enforce_role`, mas **nada no app usa papéis**: qualquer usuário logado
  acessa qualquer tela, inclusive "Usuários do sistema".

### Recuperação de senha

Há **duas implementações concorrentes** no repositório (decisão pendente):

1. **A que o app usa hoje**: diálogo "Esqueci minha senha" na aba Entrar chama
   `POST /user/reset-password` do grupo Admin, que troca a senha **só com o
   email**, sem comprovar posse da caixa postal. Esse endpoint precisa ser criado
   manualmente no Xano (receita no topo de `xano_admin_client.py`); enquanto não
   existir, a tela mostra um aviso explicativo e nada quebra.
2. **A que o backend já tem versionada**: `reset/request-code` +
   `reset/confirm-code` (código de uso único, expira em 60 min, marcado como
   usado), além de `reset/request-reset-link` (magic link com email do Xano) e
   `reset/magic-link-login`. O `.env` do projeto tem credenciais SMTP, sugerindo
   intenção de enviar email próprio — mas **nenhum código Python envia email**.

## 4. Dados

A fonte de verdade em produção é o **Xano**. O mesmo modelo aparece, porém, em
três lugares do repositório, e eles podem divergir:

| Representação | Arquivo | Papel |
|---------------|---------|-------|
| XanoScript | `xano/table/*.xs` | Espelho versionado do esquema real |
| SQLModel | `harley_store/models.py` | **Legado**; hoje só fornece constantes de domínio |
| CSV | `xano_import/*.csv` | Carga inicial, traduzida do SQL Server original |

O projeto nasceu de um script SQL Server (`HARLEY_DAVIDSON_STORE.sql`), passou
por SQLite local (SQLModel + Alembic, migrações em `alembic/versions/`) e migrou
para o Xano. Os resíduos dessa trajetória ainda estão no repositório:
`rxconfig.py` aponta para `sqlite:///harley_store.db`, mas **nenhum state usa
`rx.session()`**.

Detalhes que afetam quem escreve código:

- Datas voltam do Xano como **epoch em milissegundos** (às vezes string).
- Em `transacoes`, `id_cliente` e `id_moto_cliente` são inteiros não-opcionais
  por causa da importação por CSV: "sem cliente" é representado como **`0`**,
  não `null`.
- `PATCH` no Xano exige o registro completo.

## 5. Imagens

Fotos de produtos e motos são enviadas pela tela, salvas **localmente** em
`uploaded_files/` com nome gerado (`produto_<uuid>.<ext>`), e só o nome do
arquivo vai para o campo `imagem` no Xano. Limites: 5 MB, extensões PNG/JPG/
JPEG/WEBP/GIF. Consequência: a imagem só existe na máquina que fez o upload —
outra instalação vê o nome sem o arquivo.

## 6. Qualidade e operação

- **Sem testes automatizados, sem lint, sem CI** no repositório.
- Verificação hoje é manual: rodar `reflex run` e conferir a tela.
- Não há configuração de deploy; a operação é rodar o servidor local na loja.
- Backup do período SQLite era copiar `harley_store.db`. Com os dados no Xano,
  a estratégia de backup é **(em aberto)**.
- Plano Free do Xano: limite de requisições por minuto (HTTP 429). Telas que
  montam menus e relatórios fazem várias chamadas em sequência; `xano_client`
  retenta até 5 vezes com espera crescente.

## 7. Estado do repositório

Há trabalho não commitado no momento desta análise (15 arquivos modificados,
principalmente `auth_state.py`, `pages/login.py`, `xano_admin_client.py` e os
states convertidos para chamadas assíncronas). Os três últimos commits cobrem:
estrutura inicial do projeto, suporte a PWA e uma revisão geral que corrigiu
chamadas bloqueantes, adicionou upload de fotos e confirmação de exclusão.
