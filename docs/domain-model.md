# Modelo de domínio — Harley Store

Entidades, relacionamentos, invariantes e lacunas do domínio. Reflete o esquema
real versionado em `xano/table/*.xs` e as regras efetivamente aplicadas em
`harley_store/state/`. Onde o modelo é insuficiente ou ambíguo, o ponto está
marcado como **lacuna** — não foi presumido nem resolvido aqui.

## 1. Mapa de relacionamentos

```
                       +---------------+
                       |  fornecedores |
                       +-------+-------+
                               | 1
                               | N
                    +----------v------------+
                    |  entrada_mercadoria   |  (cabecalho da compra)
                    +----------+------------+
                               | 1
                               | N
                    +----------v------------+        +-------------+
                    | itens_compra_estoque  |>------<|  produtos   |
                    +-----------------------+   N:1  +------+------+
                                                            ^ N:1
                                                            |
   +-----------+ 1     N +-----------------+      +---------+-----------+
   | clientes  +--------->  motos_clientes |      | itens_ordem_servico |
   +-----+-----+         +--------+--------+      +---------+-----------+
         | 0..1                   | 1                       | N
         |                        | N                       | 1
         |               +--------v--------+       +--------+---------+
         |               | ordens_servico  +------>| (cabecalho da OS)|
         |               +--------+--------+       +------------------+
         |                        | N
         |                        | 1
         |               +--------v--------+
         +-------------->|  funcionarios   |<---------+
         |               +-----------------+          | N:1
         | 0..1                                       |
         |               +-----------------+          |
         +-------------->|   transacoes    +----------+
                         +-----------------+
                          (venda: sem itens)

   +-----------+ 0..1  N +-----------------+      (em paralelo a motos_clientes;
   | clientes  +--------->      motos      |       cliente_id opcional; futuro
   +-----------+         +-----------------+       ordens_servico.moto_id -> motos.id)

   +---------+        +-------------+
   |  user   +------->|  event_log  |     (contas de acesso e auditoria,
   +---------+  1:N   +-------------+      separadas de `funcionarios`)
```

## 2. Entidades

### Cadastros base

| Entidade | Campos | Chaves/únicos | Observações |
|----------|--------|---------------|-------------|
| `clientes` | `nome_cliente`, `cpf_cnpj`, `telefone?`, `email?`, `endereco?` | `cpf_cnpj` único | Pessoa ou empresa; sem distinção de tipo. |
| `motos_clientes` | `id_cliente`, `modelo`, `placa`, `chassi`, `imagem?` | `placa` e `chassi` únicos | Toda moto pertence a um cliente (1:N). |
| `motos` | `marca`, `modelo`, `ano`, `cliente_id?`, `cor?`, `placa?`, `chassi?`, `quilometragem?=0`, `status?=Em estoque`, `em_estoque?=true`, `foto?` (image), `preco_compra?`, `preco_venda?`, `data_entrada?`, `data_saida?`, `observacoes?`, `created_at?=now`, `updated_at?` | btree em `cliente_id`; placa/chassi **sem** índice único (opcionais) | 1 registro = 1 motocicleta da loja (tela Motocicletas). `cliente_id` nulo = em estoque sem dono. Foto no armazenamento de arquivos do Xano. Convive com `motos_clientes` (ver L11). |
| `funcionarios` | `nome_funcionario`, `cargo`, `tipo`, `contato?` | — | `tipo` ∈ `VENDEDOR`, `MECANICO`, `GERENTE` (convenção em texto livre, sem enum no banco). |
| `fornecedores` | `nome_fornecedor`, `cnpj`, `contato?` | `cnpj` único | — |
| `produtos` | `nome_produto`, `descricao?`, `categoria`, `estoque_qtd?`, `preco_venda`, `imagem?` | — | `categoria` é texto livre. `estoque_qtd` é o **saldo**, não um histórico. |

### Operações

| Entidade | Campos | Relacionamentos | Observações |
|----------|--------|-----------------|-------------|
| `entrada_mercadoria` | `id_fornecedor`, `data_entrada?=now`, `valor_total?` | → `fornecedores` | Cabeçalho da compra. |
| `itens_compra_estoque` | `id_entrada`, `id_produto`, `quantidade`, `valor_unitario` | → `entrada_mercadoria`, `produtos` | Item da compra; soma no estoque. |
| `transacoes` | `tipo_transacao`, `id_funcionario`, `id_cliente?`, `id_moto_cliente?`, `data_transacao?=now`, `valor_total?` | → `funcionarios`, `clientes`, `motos_clientes` | Registro de venda. `tipo_transacao` ∈ `MOTO`, `PECAS`, `BALCAO`, `COMPRA`, `ORDEM_SERVICO`. **Não tem itens.** |
| `ordens_servico` | `id_moto_cliente`, `id_funcionario`, `data_abertura?=now`, `status?=ABERTA` | → `motos_clientes`, `funcionarios` | `status` ∈ `ABERTA`, `EM_ANDAMENTO`, `CONCLUIDA`, `CANCELADA`. |
| `itens_ordem_servico` | `id_os`, `id_produto`, `quantidade`, `valor_total_item` | → `ordens_servico`, `produtos` | Peça usada na OS; baixa estoque. Guarda **valor total do item**, não unitário. |

### Identidade e auditoria

| Entidade | Campos | Observações |
|----------|--------|-------------|
| `user` | `name`, `email` (único), `password` (mín. 8, ≥1 letra, ≥1 dígito), `role` (`admin`\|`member`), `password_reset{token, expiration, used}`, `created_at` | Conta de acesso ao sistema. Tabela com `auth = true`. |
| `event_log` | `user_id?`, `action?`, `metadata?` (json), `created_at` | Preenchido pelos endpoints do Xano (`login`, `signup`, `reset_password`...). Não é lido por nenhuma tela do app. |

## 3. Invariantes e regras de negócio

Regras **aplicadas hoje**, e onde vivem:

| # | Regra | Onde é aplicada | Fragilidade |
|---|-------|-----------------|-------------|
| R1 | Venda não pode consumir mais que o estoque disponível | `vendas_state.salvar` | Verificação e baixa não são atômicas (leitura + PATCH separados). |
| R2 | Peça lançada em OS baixa o estoque, nunca abaixo de zero | `os_state.abrir_os` (`max(0, ...)`) | Silenciosamente zera em vez de recusar. |
| R3 | Item de compra soma no estoque do produto | `compras_state.finalizar_compra` | Sem transação: falha no meio deixa estado parcial. |
| R4 | Placa e chassi não se repetem | `motos_state.salvar` + índice único no Xano | Verificação no app baixa a tabela inteira. |
| R5 | Estoque e preço não podem ser negativos | `produtos_state.salvar` | Só no app; sem CHECK no banco. |
| R6 | Estoque baixo = saldo ≤ 5 | `produtos_state`, `dashboard_state` | Constante duplicada em dois arquivos; não é configurável. |
| R7 | Senha com 8+ caracteres, com letra e número | `auth_state` + filtro do Xano | — |
| R8 | Não é possível excluir o único usuário do sistema | `usuarios_state.excluir` | Conta o total via API a cada exclusão. |
| R10 | Placa e chassi de `motos` não se repetem; placa no formato AAA9999/AAA9A99, chassi com 17 caracteres sem I/O/Q, ambos normalizados em maiúsculas | `motocicletas_state.salvar` | Só no app (lista recém-buscada a cada gravação); duas gravações simultâneas passam. |
| R11 | Status da moto determina o estoque: `Vendida`/`Entregue` → `em_estoque = false` e `data_saida` preenchida; `Em estoque` → `em_estoque = true` e sem `data_saida`; `Reservada`/`Em manutenção` → escolha do usuário | `motocicletas_state.salvar` | Só no app; um PATCH direto na API pode gravar combinação incoerente. |
| R12 | Moto com registro vinculado não pode ser excluída | `motocicletas_state.excluir` (`REFERENCIAS_MOTO`) | Lista vazia hoje: nenhuma tabela referencia `motos`. |
| R9 | Só funcionário com `tipo = MECANICO` pode ser mecânico da OS | `os_state.carregar` (filtra o select) | Só filtra a lista; OS antiga com outro tipo continua válida. |

Regras **ausentes** que o domínio pressupõe:

- Excluir venda, compra ou OS **não estorna** o estoque (documentado em comentário).
- Não há bloqueio para excluir cadastro referenciado (cliente com motos, produto
  com itens de compra/OS). O Xano tem os campos como `int`, sem integridade
  referencial forçada.
- OS concluída não gera transação financeira automaticamente: o tipo
  `ORDEM_SERVICO` existe em `transacoes`, mas o vínculo OS → transação **não é
  persistido** em lugar nenhum.

## 4. Lacunas conhecidas do modelo

| Lacuna | Consequência prática | Alternativas |
|--------|----------------------|--------------|
| **L1. Venda sem itens** | Não se sabe o que foi vendido em cada venda; sem base para devolução, margem, curva ABC ou estorno de estoque. | (a) criar `itens_transacao` espelhando `itens_ordem_servico`; (b) manter só o total e aceitar que vendas não são rastreáveis por produto. |
| **L2. Estoque como saldo, sem histórico** | Nenhuma forma de auditar por que o saldo mudou; correções manuais são invisíveis; concorrência causa perda de atualização. | (a) tabela de movimentações (`movimentos_estoque`) com o saldo derivado; (b) manter saldo e adicionar só log de ajustes. |
| **L3. Ausência de nulos em `transacoes`** | "Sem cliente" é `0`, um id inexistente; consultas e joins precisam de casos especiais. | Tornar os campos opcionais no Xano e migrar `0` → `null`. |
| **L4. OS sem valor de mão de obra** | Só peças são precificadas; serviço prestado não entra no total nem no faturamento. | Campo de mão de obra na OS, ou item de OS sem produto vinculado. |
| **L5. OS não fecha ciclo financeiro** | Concluir OS não registra faturamento; o painel só conta `transacoes`. | Gerar transação ao concluir, com FK `id_os` em `transacoes`. |
| **L6. `funcionarios` e `user` desconectados** | Quem operou a venda (funcionário) e quem estava logado (usuário) são pessoas registradas separadamente; a tela de vendas pede o vendedor num select em vez de usar a sessão. | (a) FK `id_funcionario` em `user`; (b) manter separados e documentar que são cadastros distintos. |
| **L7. `role` não usado** | Não há autorização real; todos veem tudo, inclusive gestão de contas. | Mapear papéis do negócio (gerente/vendedor/mecânico) para `role` ou criar tabela de permissões. |
| **L8. Categoria e tipo como texto livre** | Erros de digitação criam categorias e tipos fantasmas; filtros e relatórios ficam inconsistentes. | Enum no Xano ou tabela de domínio. |
| **L9. Imagem como nome de arquivo local** | Foto não acompanha o dado; some em outra instalação. Resolvido só para `motos` (armazenamento do Xano); produtos e `motos_clientes` seguem locais. | Armazenamento de arquivos do Xano, ou URL externa. |
| **L10. Sem forma de pagamento / condição** | Não se sabe como a venda foi paga; sem fluxo de caixa ou contas a receber. | Campo na transação, ou entidade própria de pagamento. |
| **L11. Duas fontes de "moto" (`motos` x `motos_clientes`)** | A mesma moto pode ser cadastrada nas duas telas; moto cadastrada em Motocicletas não aparece para abrir OS nem em vendas. Escolha deliberada da Change `cadastro-motocicletas`. | (a) migrar `motos_clientes` para `motos` e trocar `id_moto_cliente` por `moto_id` em `ordens_servico`/`transacoes` (com precondition de exclusão no `DELETE /motos`); (b) manter as duas e documentar papéis distintos. |

## 5. Divergências entre as três representações

| Ponto | Xano (`xano/table`) | SQLModel (`models.py`) | Efeito |
|-------|---------------------|------------------------|--------|
| Fonte de verdade | **Sim** (produção) | Não (legado) | `models.py` só é lido pelas constantes de tipo/status. |
| `id_cliente` em `transacoes` | `int?` no esquema, mas usado como `0` pelo app | `Optional[int]`, FK real | Semântica de "sem cliente" diverge. |
| Integridade referencial | Campos `int` (Table Reference é passo manual descrito em `xano_import/LEIA-ME.md`) | `foreign_key=` declarado | Exclusões órfãs são possíveis no Xano. |
| Enums | Texto livre com comentário | Constantes Python | Nenhum dos dois é validado no banco. |
| Grupo de API CRUD (`api:LtU_pM2N`) | **Não versionado** em `xano/api/` | — | Mudanças nesses endpoints não têm rastro no Git. |
| `relatorios/resumo_GET`, `relatorio/resumo_operacoes`, `utils/template_processo` | Esqueletos vazios (`stack {}`, `response = null`) | Cálculo equivalente feito em Python no `dashboard_state` | Relatório existe só no cliente, baixando tabelas inteiras. |

## 6. Vocabulário

- **Transação**: registro de venda (balcão, peças ou moto). Não confundir com
  transação de banco de dados.
- **Entrada de mercadoria / Compra**: reposição de estoque vinda de fornecedor.
- **OS**: ordem de serviço da oficina, sempre ligada a uma moto e a um mecânico.
- **Funcionário**: cadastro operacional (quem vende, quem conserta).
- **Usuário**: conta de acesso ao sistema (email + senha) na tabela `user`.
