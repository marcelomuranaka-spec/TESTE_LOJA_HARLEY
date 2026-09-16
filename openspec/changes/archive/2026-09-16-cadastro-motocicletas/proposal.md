## Por que ?

Hoje a loja só registra "motos dos clientes" (`motos_clientes`): modelo, placa,
chassi e dono obrigatório. Não há como controlar as motocicletas que a
concessionária tem em estoque para vender. Faltam marca, ano, quilometragem,
preços, situação (reservada, em manutenção, vendida), datas de entrada e saída
e uma foto que fique salva de verdade. A foto atual só existe na máquina que
fez o upload (D9). Cada motocicleta é um bem individual, e tratá-la como
categoria de produto com um saldo ("estoque = 10") perderia placa, chassi e
histórico.

## Quais Mudanças

- Nova tabela `motos` no Xano: 1 registro = 1 motocicleta, com `cliente_id`
  opcional (moto em estoque ainda sem dono), status, `em_estoque`, preços,
  datas, observações e foto no armazenamento de arquivos do Xano.
- Novos endpoints no grupo CRUD do Xano: listar (com filtros opcionais, entre
  eles `cliente_id`), buscar, cadastrar, atualizar e excluir motocicletas, mais
  um endpoint de upload da foto.
- Nova tela **Motocicletas** (`/motocicletas`, item "Motocicletas" no menu):
  - cards de resumo calculados sobre os dados reais;
  - busca e filtros por marca, modelo, ano, status, estoque e cliente;
  - tabela com miniatura da foto e visualização ampliada;
  - formulário de cadastro/edição em diálogo, com seleção de cliente
    pesquisável ("Sem cliente" permitido), prévia, troca e remoção da foto;
  - validações de campos obrigatórios, placa, chassi, números não negativos e
    duplicidade de placa e chassi;
  - exclusão com confirmação;
  - estados de carregando, vazio, erro e sucesso.
- Função no cliente HTTP para enviar a foto ao Xano.
- **Sem alteração** em `motos_clientes` nem na tela `/motos` ("Motos dos
  clientes"). Ordens de serviço e vendas continuam apontando para
  `motos_clientes`. As duas tabelas convivem em paralelo por decisão do usuário.

**Depende de alteração manual no workspace Xano** (plano Free, sem Metadata
API): criar a tabela `motos` e publicar os endpoints seguindo a receita
versionada em `xano/` que esta Change entrega. A tela não funciona de ponta a
ponta enquanto isso não for feito.

## Não são objetivos

- Migrar os registros de `motos_clientes` para `motos`, ou unificar as duas
  tabelas.
- Ligar ordens de serviço e vendas a `motos` (`ordens_servico.moto_id`). A
  tabela nasce preparada para isso, mas o vínculo é uma Change futura.
- Filtro de categoria em Produtos e qualquer outra mudança em Produtos.
- Mover para o Xano as fotos de Produtos e de "Motos dos clientes".
- Exigir token de autenticação nas chamadas de dados (C1
  `proteger-api-de-dados`). Os novos endpoints seguem o grupo CRUD atual.
- Apagar do armazenamento do Xano o arquivo de uma foto substituída ou
  removida.
- Paginação no servidor.

## Capacidades

### Novas Capacidades
- `motocicletas`: cadastro individual de motocicletas da loja, com foto no
  Xano, vínculo opcional com cliente, controle de estoque por unidade
  (status + em_estoque), busca, filtros, resumo e exclusão protegida.

### Capacidades Modificadas
<!-- Nenhuma: não há specs publicadas em openspec/specs/ e nenhum comportamento existente muda. -->

## Impacto

- **Xano (manual):** tabela `motos`; endpoints `GET /motos`,
  `GET /motos/{motos_id}`, `POST /motos`, `PATCH /motos/{motos_id}`,
  `DELETE /motos/{motos_id}` e `POST /motos/foto` no grupo CRUD
  (`api:LtU_pM2N`); uso da cota de armazenamento de arquivos do plano.
- **Código novo:** `harley_store/state/motocicletas_state.py`,
  `harley_store/pages/motocicletas.py`, `xano/table/motos.xs`,
  `xano/api/crud/motos/*.xs`.
- **Código alterado:** `harley_store/harley_store.py` (rota),
  `harley_store/components/layout.py` (item de menu),
  `harley_store/xano_client.py` (upload de arquivo).
- **Documentação:** `docs/domain-model.md` (nova entidade e relacionamentos).
- **Dados:** testar grava na base real (D5). O impacto se limita à tabela
  nova, que começa vazia.
