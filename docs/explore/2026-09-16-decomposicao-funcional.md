# Sessão de Explore — Decomposição funcional do Harley Store

**Data:** 16/09/2026
**Objetivo:** decompor o sistema em capacidades implementáveis de forma
incremental e definir uma ordem de implementação. **Não** é uma proposta de
implementação e **não** cria nenhuma Change.

**Base de análise:** código em `harley_store/`, backend versionado em `xano/`,
`rxconfig.py`, `requirements.txt`, `README.md`, `xano_import/`, `assets/` e o
histórico do Git. Os documentos [project-overview.md](../project-overview.md) e
[domain-model.md](../domain-model.md) foram escritos nesta mesma sessão a partir
dessa leitura — antes dela não existia documentação de projeto, de domínio nem
estrutura OpenSpec no repositório.

---

## 1. Visão geral da decomposição

O sistema já tem **todas as telas de CRUD funcionando** — a decomposição não é
sobre "o que ainda falta construir do zero", e sim sobre **quais capacidades
existem parcialmente, quais estão apoiadas em fundações frágeis e em que ordem
consolidá-las**.

Três observações organizam tudo o que vem a seguir:

1. **A largura já existe; falta profundidade.** Onze telas cobrem os dez
   cadastros e operações do banco original. O que não existe é a espessura
   vertical de cada uma: autorização, rastreabilidade, integridade e relatório.
2. **A fundação está mais frágil que o andar de cima.** Os dados no Xano
   respondem **sem token**; o login protege a navegação, não a API. Qualquer
   Change de funcionalidade construída antes disso será construída sobre um
   alicerce que vai precisar ser trocado.
3. **Há duas heranças convivendo.** O caminho SQL Server → SQLite/SQLModel →
   Xano deixou `models.py`, `alembic/` e `rxconfig.db_url` ainda no lugar, sem
   uso real. Enquanto o projeto tiver duas "fontes de verdade" aparentes, toda
   Change que toque dados vai precisar decidir isso de novo.

```
        O QUE O SISTEMA TEM HOJE (por profundidade)
   =================================================================
                     |  tela  |  regra  |  dado  |  API  | autoriz.|
   Cadastros base    |   OK   |  parcial|   OK   |aberta |  nenhuma|
   Estoque           |   --   |  parcial| saldo  |aberta |  nenhuma|
   Compras           |   OK   |  parcial|   OK   |aberta |  nenhuma|
   Vendas            |   OK   |  parcial| SEM ITEM|aberta|  nenhuma|
   Ordens de servico |   OK   |  parcial| sem M.O|aberta|  nenhuma|
   Painel/relatorios |   OK   |  cliente|derivado|aberta |  nenhuma|
   Identidade/acesso |   OK   |  parcial|   OK   | com   |  nenhuma|
                                                   token
```

---

## 2. Mapa de capacidades

Nomes em `kebab-case` são a sugestão de nome de capacidade para
`openspec/specs/<capability>/spec.md`. `[E]` = existe e funciona; `[P]` = existe
parcialmente; `[ ]` = não existe.

```
HARLEY STORE
|
+-- A. PLATAFORMA E FUNDACAO
|   +-- [P] acesso-a-dados .............. cliente HTTP Xano, retry 429, conversao de tipos
|   +-- [ ] sessao-autenticada-na-api ... propagar token; tratar 401/expiracao
|   +-- [ ] ambientes ................... separar dados de desenvolvimento dos da loja
|   +-- [ ] verificacao-automatizada .... testes, lint, smoke de compilacao
|   +-- [P] fonte-unica-do-dominio ...... enums/regras num lugar so; aposentar SQLModel legado
|
+-- B. IDENTIDADE E ACESSO
|   +-- [E] autenticacao ................ login/cadastro via Xano, cookies de sessao
|   +-- [P] recuperacao-de-senha ........ duas implementacoes concorrentes (ver secao 6, D3)
|   +-- [E] gestao-de-usuarios .......... listar, trocar email, excluir conta
|   +-- [ ] autorizacao-por-papel ....... `role` existe no banco, `enforce_role` existe no Xano, nada usa
|   +-- [P] auditoria-de-eventos ........ `event_log` gravado pelo Xano, nunca lido pelo app
|
+-- C. CADASTROS BASE
|   +-- [E] cadastro-clientes
|   +-- [E] cadastro-motos ............... vinculo cliente -> moto, placa/chassi unicos
|   +-- [E] cadastro-funcionarios ........ tipos VENDEDOR/MECANICO/GERENTE
|   +-- [E] cadastro-fornecedores
|   +-- [E] catalogo-produtos ............ nome, categoria, preco, foto
|   +-- [ ] integridade-referencial ...... impedir excluir registro em uso
|
+-- D. ESTOQUE
|   +-- [P] saldo-de-estoque ............. campo `estoque_qtd`, alterado por 3 fluxos
|   +-- [ ] movimentacao-de-estoque ...... historico de entradas/saidas; estorno; ajuste manual
|   +-- [P] alerta-estoque-baixo ......... limite fixo 5, duplicado em 2 arquivos
|
+-- E. COMPRAS (ENTRADA)
|   +-- [E] entrada-de-mercadoria ........ cabecalho + itens, soma estoque
|   +-- [ ] estorno-de-entrada ........... excluir compra nao devolve estoque
|
+-- F. VENDAS
|   +-- [E] registro-de-venda ............ tipo, vendedor, cliente/moto opcionais, valor
|   +-- [ ] itens-de-venda ............... LACUNA CENTRAL: nao se sabe o que foi vendido
|   +-- [ ] pagamento .................... forma/condicao de pagamento nao existem
|
+-- G. OFICINA
|   +-- [E] ordem-de-servico ............. abertura, mecanico, status
|   +-- [E] itens-de-os ................. pecas usadas, baixa estoque
|   +-- [ ] mao-de-obra .................. servico prestado nao e precificado
|   +-- [ ] faturamento-de-os ............ concluir OS nao gera transacao
|
+-- H. RELATORIOS
|   +-- [P] painel-operacional ........... calculado no cliente, baixando tabelas inteiras
|   +-- [ ] relatorios-consolidados ...... endpoints Xano existem, mas vazios
|
+-- I. EXPERIENCIA
    +-- [E] pwa-instalavel ............... manifest + icones + meta tags iOS
    +-- [P] ui-responsiva ................ padrao ja estabelecido em components/layout.py
    +-- [P] upload-de-imagens ............ arquivo fica local, so o nome vai ao Xano
    +-- [ ] uso-offline ................. sem service worker
```

---

## 3. Dependências entre capacidades

### 3.1 Grafo de dependências

```
                    +---------------------------+
                    | A. sessao-autenticada-na- |
                    |    api  (token + 401)     |
                    +-------------+-------------+
                                  |
              +-------------------+-------------------+
              v                                       v
   +---------------------+                 +-----------------------+
   | B. autorizacao-por- |                 | A. ambientes (dados   |
   |    papel            |                 |    de dev separados)  |
   +----------+----------+                 +-----------+-----------+
              |                                        |
              v                                        v
   +---------------------+                 +-----------------------+
   | B. gestao-de-       |                 | A. verificacao-       |
   |    usuarios (restrita)                |    automatizada       |
   +---------------------+                 +-----------+-----------+
                                                       |
   +---------------------------+                       |
   | A. fonte-unica-do-dominio |<----------------------+
   +------------+--------------+
                |
                v
   +---------------------------+      +--------------------------+
   | D. movimentacao-de-estoque|<-----+ F. itens-de-venda        |
   +------------+--------------+      +-----------+--------------+
                |                                 |
                +---------------+-----------------+
                                v
                    +-------------------------+
                    | E/G. estorno e          |
                    |      faturamento de OS  |
                    +-----------+-------------+
                                |
                                v
                    +-------------------------+
                    | H. relatorios reais     |
                    |    (margem, ABC, caixa) |
                    +-------------------------+
```

### 3.2 Dependências por natureza

| Natureza | Dependência observada | Consequência para o sequenciamento |
|----------|----------------------|-----------------------------------|
| **Modelo de dados** | `itens-de-venda` exige tabela nova no Xano; `movimentacao-de-estoque` muda a semântica de `estoque_qtd` (saldo → derivado) | Mudanças estruturais: decidir **antes** de construir relatórios que dependam delas |
| **Modelo de dados** | `id_cliente = 0` em `transacoes` (em vez de `null`) | Qualquer relatório por cliente precisa tratar isso; corrigir junto com `itens-de-venda` evita migrar duas vezes |
| **Autenticação** | Todo endpoint CRUD do Xano responde sem token | É pré-requisito de qualquer autorização; nada de B funciona antes |
| **Autorização** | `autorizacao-por-papel` exige token chegando ao Xano e papéis definidos pelo negócio | Depende de A **e** de uma decisão do usuário (D4) |
| **Regra de negócio** | Estorno de estoque depende de saber o que foi movimentado | `itens-de-venda` e/ou `movimentacao-de-estoque` vêm antes do estorno |
| **Regra de negócio** | `faturamento-de-os` exige vínculo OS → transação (não existe) | Precisa de campo novo; decidir junto com `mao-de-obra` |
| **API** | O grupo CRUD (`api:LtU_pM2N`) não está versionado em `xano/api/` | Mudanças de API hoje não deixam rastro no Git — endereçar antes de multiplicar endpoints |
| **API** | `relatorios/resumo_GET` e `relatorio/resumo_operacoes` são esqueletos vazios | Relatório no servidor é trabalho novo, não ajuste |
| **Frontend** | O par `state/` + `pages/` e o padrão responsivo já existem | Novas telas são incrementais e baratas — o custo está nas camadas de baixo |
| **Integração externa** | Plano Free do Xano: limite por minuto, sem Metadata API | Migração de esquema é manual; relatórios que baixam tabelas inteiras não escalam |
| **Integração externa** | SMTP configurado em `.env`, sem código que o use | Fluxo de email é capacidade nova, não conexão de fio solto |

---

## 4. Ordem de implementação sugerida

Princípio aplicado: **o banco não evolui sozinho**. Cada onda entrega uma fatia
vertical (dado → regra → API → tela) e só mexe no esquema quando uma
funcionalidade concreta precisa daquele campo.

```
   ONDA 0 - FUNDACAO           ONDA 1 - NUCLEO         ONDA 2 - CICLO
   (destrava tudo)             (fecha lacunas)          COMPLETO
   +---------------------+     +-------------------+   +-------------------+
   | sessao-autenticada  |     | itens-de-venda    |   | mao-de-obra +     |
   | fonte-unica-dominio |---->| movimentacao-de-  |-->| faturamento-de-os |
   | verificacao-minima  |     | estoque + estorno |   | relatorios no     |
   | ambientes (decisao) |     | integridade-ref.  |   | servidor          |
   +---------------------+     +-------------------+   +-------------------+
            |                                                   |
            v                                                   v
   +---------------------+                             +-------------------+
   | autorizacao-por-    |                             | ONDA 3 - EXTENSOES|
   | papel               |                             | pagamento, fotos  |
   +---------------------+                             | no Xano, offline, |
                                                        | backup/exportacao|
                                                        +-------------------+
```

**Por que nesta ordem**

- **Onda 0 antes de tudo** porque muda o contrato de todas as chamadas de dados.
  Feita depois, obriga a revisitar cada capacidade construída no meio-tempo.
- **`fonte-unica-do-dominio` é barata e destrava leitura**: enquanto `models.py`
  parecer um banco ativo, toda Change gasta tempo decidindo onde mexer.
- **`verificacao-minima` cedo** porque o pedido é que cada Change seja
  *verificável*; hoje a única verificação possível é abrir a tela e olhar.
- **Onda 1 corrige o modelo onde ele falha**, sem "terminar o banco": cada tabela
  ou campo novo entra acompanhado da tela e da regra que o usa.
- **Onda 2 fecha o ciclo financeiro** (OS que vira faturamento) e só então os
  relatórios têm dados confiáveis para agregar no servidor.
- **Onda 3 é opcional** e depende de decisões de negócio ainda não tomadas.

---

## 5. Primeiras Changes candidatas

Cinco candidatas, em ordem de prioridade sugerida. Cada uma é vertical, de
escopo pequeno e com critério de verificação explícito. **Nenhuma foi criada** —
a escolha da primeira é do usuário.

### C1. `proteger-api-de-dados` — *fundacional, urgente*

| | |
|---|---|
| **Problema** | Os dados da loja (clientes, CPF/CNPJ, vendas, estoque) respondem a qualquer requisição sem token. O login protege só a navegação. |
| **Escopo** | Exigir autenticação nos endpoints do grupo CRUD do Xano; enviar `Authorization: Bearer <token>` em `xano_client`; tratar `401` como sessão expirada (limpar cookies, redirecionar para `/login` com aviso). |
| **Fatia vertical** | Xano (endpoints) → cliente HTTP → `AuthState` → tela de login. |
| **Verificação** | Requisição sem token ao endpoint de dados retorna 401; app logado continua funcionando em todas as telas; token expirado leva ao login em vez de tela vazia. |
| **Fora de escopo** | Papéis e permissões (fica em C4). |
| **Risco/alternativa** | Exige alterar o workspace Xano manualmente (plano Free, sem Metadata API). Se isso não for possível agora, uma versão reduzida — só tratar 401 e expiração no app — deixa a exposição de dados aberta e **não** resolve o problema; é paliativo, não a Change. |

### C2. `definir-fonte-unica-do-dominio` — *fundacional, barata*

| | |
|---|---|
| **Problema** | `models.py`, `alembic/` e `rxconfig.db_url` sugerem um banco local ativo que não existe mais; enums de domínio moram no arquivo legado. |
| **Escopo** | Extrair `TIPOS_FUNCIONARIO`, `TIPOS_TRANSACAO`, `STATUS_OS` e o limite de estoque baixo para um módulo de domínio; decidir o destino do SQLModel/Alembic/SQLite (remover ou congelar com nota explícita); alinhar `rxconfig.py`. |
| **Fatia vertical** | Não toca dados — é consolidação de código e documentação. |
| **Verificação** | App sobe e todas as telas carregam; nenhuma referência a `models.py` fora do módulo de domínio; `docs/domain-model.md` atualizado. |
| **Alternativa** | Manter SQLite como modo offline futuro. Consequência: o modelo passa a ter dois destinos de escrita e toda Change de dados precisa considerar sincronização — é um projeto próprio, não um detalhe. |

### C3. `verificacao-minima` — *fundacional, habilita "verificável"*

| | |
|---|---|
| **Problema** | Sem testes, lint ou CI, "verificar" uma Change é abrir a tela e olhar. |
| **Escopo** | `pytest` + testes das funções puras já existentes (conversão de epoch, `texto`/`numero`/`inteiro`, validação de email e senha, cálculo de totais de compra/OS) e um smoke de compilação do app. |
| **Fatia vertical** | Infraestrutura de qualidade; não altera comportamento. |
| **Verificação** | Suite roda em um comando e passa; uma quebra proposital é detectada. |
| **Observação** | Pode ser feita em paralelo com C1/C2 — não compete por arquivos. |

### C4. `autorizacao-por-papel` — *depende de C1 e da decisão D4*

| | |
|---|---|
| **Problema** | Qualquer usuário logado acessa a tela "Usuários do sistema" e pode excluir contas. `role` e `enforce_role` existem e não são usados. |
| **Escopo** | Definir a matriz papel × tela; aplicar no `on_load` das páginas sensíveis e no menu; aplicar `enforce_role` nos endpoints administrativos do Xano. |
| **Fatia vertical** | Xano → `AuthState` → layout/menu → páginas. |
| **Verificação** | Usuário `member` não acessa `/usuarios` nem por URL direta; `admin` acessa; endpoint administrativo recusa token `member`. |
| **Bloqueio** | Precisa da resposta de D4 (quais papéis o negócio tem). |

### C5. `itens-de-venda` — *primeira Change de funcionalidade*

| | |
|---|---|
| **Problema** | Não se sabe o que foi vendido em cada venda: o produto escolhido só calcula valor e baixa estoque. Sem isso não há devolução, margem, curva ABC nem estorno. |
| **Escopo** | Tabela `itens_transacao` no Xano; venda com um ou mais itens; total calculado a partir dos itens; histórico mostrando os itens; estorno de estoque ao excluir a venda. |
| **Fatia vertical** | Xano (tabela + endpoints) → `vendas_state` → `pages/vendas.py`. |
| **Verificação** | Venda com 2 itens grava 2 linhas, baixa o estoque dos dois e soma o total corretamente; excluir a venda devolve o estoque. |
| **Alternativa de sequência** | Fazer `movimentacao-de-estoque` primeiro: o estorno passaria a valer também para compras e OS, mas é uma mudança estrutural maior (saldo deixa de ser campo e passa a ser derivado) e atrasa o ganho visível no balcão. Fazer `itens-de-venda` primeiro entrega valor antes e deixa o estorno parcial (só vendas) por um tempo. |

**Se for para escolher uma só:** C1, por ser a única cujo adiamento cria retrabalho
em tudo que vier depois — e por ser a única que hoje expõe dados reais de clientes.

---

## 6. Decisões e dúvidas a resolver antes da primeira Change

Numeradas para referência. As marcadas **(bloqueante)** impedem começar a Change
correspondente.

| # | Questão | Por que importa | Alternativas e consequências |
|---|---------|-----------------|------------------------------|
| **D1** | O Xano é a fonte de verdade definitiva? **(bloqueante para C2)** | Define se `models.py`/Alembic/SQLite saem do repositório ou viram outra coisa | (a) Xano único: simplifica tudo, cria dependência de internet na loja; (b) SQLite como modo offline: exige projeto de sincronização |
| **D2** | Podemos alterar o workspace Xano (criar tabela, exigir auth, publicar endpoint)? Quem executa, já que o plano Free não tem Metadata API? **(bloqueante para C1 e C5)** | Toda Change com dado novo depende de trabalho manual no painel do Xano | (a) usuário executa seguindo receita na Change; (b) plano pago com Metadata API: mudanças versionáveis e automatizáveis, com custo |
| **D3** | Qual fluxo de recuperação de senha permanece? **(bloqueante se C1 mexer em auth)** | Hoje `POST /user/reset-password` troca a senha **só com o email**: quem souber o email de alguém troca a senha dessa pessoa. O backend já tem `reset/request-code` + `reset/confirm-code` prontos e o `.env` tem SMTP | (a) migrar para código por email (fecha a brecha, exige envio de email pelo app); (b) manter o atual (risco permanece); (c) restringir reset a administradores. **Decisão do usuário — o escopo de autenticação já mudou de direção antes e não deve ser alterado por iniciativa própria** |
| **D4** | Quais papéis o negócio tem e o que cada um acessa? **(bloqueante para C4)** | `role` só tem `admin`/`member`, enquanto o negócio fala em gerente, vendedor e mecânico | (a) mapear os três para `admin`/`member`: barato, granularidade grossa; (b) ampliar o enum: mais fiel, mexe no esquema e no `enforce_role` |
| **D5** | Existe ambiente de desenvolvimento separado dos dados da loja? | Hoje `BASE_URL` é fixa no código: testar uma Change mexe nos dados reais | (a) workspace/branch separado no Xano; (b) base URL por variável de ambiente; (c) aceitar o risco e testar em horário sem movimento |
| **D6** | Venda precisa de múltiplos itens e forma de pagamento? | Define o tamanho de C5 e se `pagamento` entra na mesma Change | (a) só itens agora; (b) itens + pagamento juntos: uma migração só, Change maior |
| **D7** | OS precisa precificar mão de obra e gerar faturamento ao concluir? | Hoje OS concluída não entra no faturamento do painel | (a) campo de mão de obra na OS; (b) item de OS sem produto; (c) manter só peças |
| **D8** | Funcionário e usuário devem ser unificados? | A venda pede o vendedor num select em vez de usar quem está logado | (a) vincular `user` → `funcionario`: elimina o select e melhora a auditoria; (b) manter separados |
| **D9** | Fotos devem ir para o armazenamento do Xano? | Hoje a imagem só existe na máquina que fez o upload | (a) migrar para o Xano (consome cota do plano); (b) manter local e documentar a limitação |
| **D10** | Uso offline é requisito real? | O PWA é instalável mas não funciona sem internet; se a loja tem internet instável, isso muda a arquitetura inteira | (a) não é requisito: nada muda; (b) é requisito: fila local e sincronização — projeto grande, afeta D1 |
| **D11** | Qual a estratégia de backup dos dados no Xano? | O backup antigo era copiar o arquivo SQLite; hoje não há equivalente documentado | (a) exportação periódica via app; (b) recurso do próprio Xano; (c) assumir o risco |
| **D12** | Quantas pessoas usam ao mesmo tempo? | Define se a leitura-e-escrita de saldo de estoque precisa de proteção contra concorrência | (a) uso praticamente single-user: risco baixo; (b) balcão + oficina simultâneos: `movimentacao-de-estoque` sobe de prioridade |

---

## 7. Riscos identificados

| Risco | Gravidade | Evidência | Mitigação sugerida |
|-------|-----------|-----------|--------------------|
| Dados pessoais e financeiros acessíveis sem autenticação | **Alta** | `xano_client` não envia `Authorization`; tabelas com `auth = false` | C1 |
| Redefinição de senha exige apenas o email | **Alta** | `xano_admin_client.redefinir_senha`, documentado no próprio arquivo | D3 |
| Desenvolvimento e produção compartilham a mesma base | **Alta** | `BASE_URL` fixa nos três clientes | D5 |
| Operações multi-etapas sem atomicidade | Média | Compra/OS gravam cabeçalho, itens e estoque em chamadas separadas | Regra no servidor (função Xano) ou compensação explícita |
| Estoque diverge da realidade | Média | Exclusões não estornam; `max(0, ...)` mascara erro | `movimentacao-de-estoque` |
| Limite de requisições do plano Free | Média | Retry de 429 no cliente; telas que baixam tabelas inteiras | Relatórios no servidor; paginação |
| Divergência entre `xano/*.xs` e o workspace real | Média | Grupo CRUD não versionado; três arquivos `.xs` vazios | Versionar o grupo CRUD ao tocá-lo |
| Ausência de verificação automatizada | Média | Sem testes/lint/CI | C3 |
| Perda de fotos entre instalações | Baixa | Upload local, só o nome no Xano | D9 |
| Exclusão de registro referenciado | Baixa | Sem integridade referencial forçada | `integridade-referencial` |

---

## 8. O modelo de domínio sustenta esta decomposição?

**Sustenta as ondas 0 e parte da 1; não sustenta a onda 2 sem mudanças.**

| Onda | Suficiente? | O que falta |
|------|-------------|-------------|
| 0 — Fundação | **Sim** | Nada no modelo; são mudanças de contrato de API, código e processo |
| 1 — Núcleo | **Não** | `itens_transacao` não existe (L1); estoque não tem histórico (L2); `id_cliente = 0` em vez de `null` (L3) |
| 2 — Ciclo completo | **Não** | OS não tem mão de obra (L4) nem vínculo com transação (L5); sem forma de pagamento (L10) |
| 3 — Extensões | **Parcialmente** | Depende de D9/D10/D11 |

As lacunas estão catalogadas em [domain-model.md](../domain-model.md#4-lacunas-conhecidas-do-modelo)
(L1 a L10) com alternativas. Duas delas são **estruturais** e merecem decisão
antecipada, porque mudam a semântica de dados já gravados:

1. **L2 — estoque: saldo ou histórico?** Trocar `estoque_qtd` de campo para valor
   derivado de movimentações afeta produtos, vendas, compras, OS e painel ao
   mesmo tempo. É a mudança de maior alcance identificada nesta sessão.
2. **L1/L3 — vendas: itens e nulos.** Criar `itens_transacao` e migrar
   `id_cliente = 0` para `null` é oportuno fazer numa migração só, já que ambos
   tocam `transacoes`.

Nenhuma das duas precisa ser feita "para terminar o banco": as duas devem entrar
acompanhadas da funcionalidade que as justifica (C5 e o estorno de estoque).

---

## 9. Próximo passo

Escolher a primeira Change (recomendação: **C1 `proteger-api-de-dados`**) e
responder às decisões bloqueantes correspondentes — D2 e D5 para C1, D1 para C2,
D4 para C4, D2/D6 para C5. Com isso definido, o ciclo
**Propose → Review → Apply → Verify → Archive** começa com
`openspec new change "<nome>"`.
