## Context

Veja `proposal.md` (Why) e `specs/motocicletas/spec.md` (requisitos). O que
molda a solução:

- **Frontend e "backend do frontend" são o mesmo processo Python** (Reflex).
  As chamadas ao Xano saem do servidor, via `harley_store/xano_client.py`, e
  não do navegador. Nenhuma URL ou credencial do Xano chega ao cliente.
- `xano_client` já tem CRUD genérico por nome de tabela
  (`listar/buscar/criar/atualizar/excluir`) sobre o grupo CRUD `api:LtU_pM2N`,
  com retentativa em HTTP 429. O PATCH exige o registro completo. As datas
  trafegam como epoch em ms.
- O upload atual (Produtos, Motos dos clientes) usa `rx.upload`, grava em
  `uploaded_files/` do servidor e manda só o nome do arquivo ao Xano. A foto
  some ao trocar de máquina (D9).
- Consulta de leitura feita em 2026-09-16: `GET /motos` e qualquer rota de
  upload respondem 404 no grupo CRUD, então nada disso existe no Xano. O grupo
  CRUD não está versionado em `xano/api/`.
- O plano Free não tem Metadata API. Tabela e endpoints são criados à mão no
  painel (D2, alternativa a: o usuário executa a receita versionada).
- `ordens_servico.id_moto_cliente` e `transacoes.id_moto_cliente` apontam para
  `motos_clientes`. Nenhuma tabela referencia `motos`.

## Goals / Non-Goals

**Goals:**
- Tela nova no padrão do projeto (par `state/motocicletas_state.py` +
  `pages/motocicletas.py`), sem tocar nas telas existentes.
- Foto guardada no armazenamento de arquivos do Xano, com prévia antes do
  envio.
- No máximo 2 GETs ao abrir a tela (motos + clientes) e nenhuma requisição ao
  mexer em filtros, por causa do limite de requisições do plano Free.

**Non-Goals:**
- Reaproveitar o `MotosState` existente: ele modela `motos_clientes` e
  continua servindo a tela `/motos`.
- Criar componente genérico de upload para outras telas. A extração fica para
  quando Produtos migrar a foto para o Xano.

## Decisions

### 1. Tabela `motos` nova, em paralelo a `motos_clientes`
Escolha do usuário. Alternativas avaliadas:
- **Evoluir `motos_clientes` (adicionar colunas):** mantém IDs e vínculos de
  OS e vendas sem migração. Descartada pelo usuário.
- **`motos` nova + migração e troca de `id_moto_cliente` por `moto_id`:**
  modelo final único, mas mexe em OS, vendas e dados reais na mesma Change.
  Maior e mais arriscada.
- **Paralela (escolhida):** Change pequena e sem risco para o que já funciona.
  Consequência aceita: por um tempo existem duas fontes de "moto". Uma moto de
  cliente cadastrada em Motocicletas ainda não aparece para abrir OS. A
  unificação é uma Change futura (ver Riscos).

Esquema (`xano/table/motos.xs`):

| Campo | Tipo Xano | Regra |
|---|---|---|
| `id` | int | PK auto |
| `created_at` | timestamp | `?=now` |
| `updated_at` | timestamp? | enviado pelo app a cada gravação |
| `cliente_id` | int? | → `clientes.id`; nulo = sem dono |
| `marca`, `modelo` | text (trim) | obrigatórios |
| `ano` | int | obrigatório |
| `cor`, `placa`, `chassi`, `observacoes` | text? (trim) | placa/chassi normalizados pelo app |
| `quilometragem` | int? | `?=0` |
| `status` | text? | `?="Em estoque"` (texto, como `ordens_servico.status`) |
| `em_estoque` | bool? | `?=true` |
| `foto` | image? | metadados do arquivo no armazenamento do Xano |
| `preco_compra`, `preco_venda` | decimal? | ≥ 0 validado no app |
| `data_entrada` | timestamp? | |
| `data_saida` | timestamp? | nulo enquanto na loja |

Índices: PK e btree em `cliente_id`, para a consulta "motos do cliente". Não
há índice **único** em placa e chassi, porque os dois são opcionais: com índice
único, dois registros com valor vazio colidiriam, a depender de como o Xano
grava texto vazio versus nulo. A unicidade fica no app (decisão 6). Nome em
snake_case e FK com sufixo `_id`, conforme `xano/knowledge/agents.md`. A
exceção a esse padrão está nas tabelas legadas (`id_cliente`).

`status` fica como texto, e não enum do Xano, pelo mesmo motivo do
`ordens_servico.status`: mudar os valores de um enum exige alteração manual no
esquema. O app restringe os valores.

### 2. Endpoints no grupo CRUD existente
- **Escolhida:** `GET/POST /motos`, `GET/PATCH/DELETE /motos/{motos_id}` e
  `POST /motos/foto` no grupo CRUD atual. O `xano_client` genérico funciona sem
  mudar a `BASE_URL`: `listar("motos")`, `criar("motos", ...)`. As rotas CRUD
  podem ser geradas pelo assistente "CRUD Database Operations" do Xano. Depois
  basta editar o GET de lista para aceitar os filtros e criar à mão o endpoint
  de foto.
- **Alternativa: grupo de API novo "Motos"** totalmente versionado. Isolaria
  melhor, mas cria outra base URL fixa no código ou uma variável de ambiente
  nova (D5 ainda aberta). Descartada por aumentar configuração sem ganho
  funcional.
- Os `.xs` dos novos endpoints ficam versionados em `xano/api/crud/motos/`,
  seguindo a mitigação "versionar o grupo CRUD ao tocá-lo". O nome real do
  `api_group` precisa ser conferido no painel na hora de aplicar.

`GET /motos` recebe como entradas opcionais `cliente_id`, `status`,
`em_estoque`, `marca`, `modelo` e `ano`. Cada filtro só se aplica quando
informado (`db.query` com `where` condicional). A tela chama sem filtros.

### 3. Foto: endpoint de upload dedicado + metadados no registro
Fluxo:
1. `rx.upload` → handler valida extensão (jpg/jpeg/png/webp) e tamanho (5 MB,
   o mesmo limite já usado no projeto).
2. O arquivo vai para um temporário local `uploaded_files/tmp_moto_<uuid>.<ext>`,
   usado **só para a prévia**.
3. Em "Salvar", se houver temporário: `POST /motos/foto` (multipart, campo
   `arquivo`). O endpoint executa `storage.create_image` (acesso público) e
   devolve os metadados (`path`, `name`, `type`, `size`, `mime`, `meta` e
   `url`, quando houver).
4. `POST` ou `PATCH /motos` recebe `foto` = esse objeto de metadados. O arquivo
   temporário é apagado.

Na leitura, a URL exibida é `foto.url`. Se esse campo não vier, usa-se o host
da instância + `foto.path`, com o host derivado da `BASE_URL`.

Alternativas:
- **Enviar o arquivo direto no `POST /motos` (multipart):** acopla upload e
  gravação. Uma falha de validação no Xano reenviaria o arquivo, e como o PATCH
  exige registro completo, cada edição sem troca de foto precisaria reenviar
  metadados em multipart. Descartada.
- **Subir ao Xano já na seleção:** a prévia viria do próprio Xano, mas cada
  cancelamento deixaria arquivo órfão ocupando cota, e o fluxo pedido é enviar
  só ao confirmar. Descartada.
- **Guardar os bytes no state do Reflex:** o state é serializado e trafega no
  websocket, e 5 MB por sessão é inviável. Descartada.
- **Base64 no banco:** proibido pelo requisito.
- **Manter o upload local:** não resolve D9. Descartada para Motocicletas.
  Produtos segue local, fora de escopo.

Edição: `foto_atual` guarda os metadados vindos do Xano, `foto_temp` guarda o
arquivo novo e `remover_foto` é um sinal. Ao salvar:
- com arquivo novo → sobe e usa os novos metadados;
- com remoção → `foto: null`;
- sem mudança → reenvia `foto_atual` inalterado (exigência do PATCH completo).

Todo erro no upload interrompe o salvamento antes de gravar o registro.

Credenciais: nenhum segredo novo. O endpoint de foto segue o grupo CRUD atual,
sem token, a mesma exposição já registrada para C1.

### 4. Filtros e resumo calculados em memória
Ao abrir a tela: `listar("motos")` + `listar("clientes")`, ambos em
`try/except`, que alimentam os estados de erro. Busca, filtros, opções dos
selects e cards são calculados em Python sobre a lista completa guardada no
state. As variáveis derivadas (`@rx.var`) recalculam sem nova requisição.
- **Alternativa: um GET com parâmetros a cada mudança de filtro.** Gera uma
  requisição por tecla ou seleção e esbarra no limite do plano Free. Os filtros
  da API existem para outros consumidores e para a futura ficha do cliente.
- Consequência: não escala para milhares de motos. Paginação no servidor é
  Change futura, e o volume de uma concessionária pequena não exige isso agora.

### 5. Formulário em `rx.dialog`
As telas atuais usam um card inline no topo. Aqui o formulário tem 5 seções e
15 campos, e o requisito pede um botão que abre o cadastro. Por isso ele vai
num `rx.dialog` com largura `min(95vw, 760px)`, `max_height="90vh"` e rolagem
interna. As seções usam `rx.grid` com `columns=rx.breakpoints(initial="1", md="2")`.
- **Alternativa: card inline como nas outras telas.** Mais consistente, mas
  empurra a tabela para baixo da dobra no celular. Descartada.

Cliente pesquisável: o Reflex 0.7 não tem combobox nativo. A solução é um
`rx.input` de pesquisa que filtra as opções de um `rx.select` logo abaixo,
sempre com "Sem cliente" como primeira opção. Cada opção usa o formato
`"<id> - <nome>"`, o padrão de `MotosState`.
- **Alternativa: embrulhar um combobox React.** Adiciona dependência npm e
  manutenção. Descartada.
- **Alternativa: `<datalist>`.** O Safari do iOS tem suporte inconsistente
  para ele, e o app roda como PWA no iPhone. Descartada.

Foto ampliada: um `rx.dialog` único na página, controlado por
`foto_ampliada_url`, em vez de um diálogo por linha.

### 6. Regras de negócio no state
Validação, normalização, duplicidade e a regra status ↔ `em_estoque` ficam em
`motocicletas_state.salvar`, como nas demais telas.
- **Normalização:** placa e chassi em maiúsculas, sem espaço e sem hífen; vazio
  vira `null`.
- **Formatos:**
  - placa: `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`, que cobre o formato antigo e o
    Mercosul;
  - chassi: `^[A-HJ-NPR-Z0-9]{17}$`;
  - ano: 1900 a ano atual + 1;
  - preço: aceita `12.500,50`, `12500,50` e `12500.50`.
- **Duplicidade:** um `listar("motos")` feito no momento de salvar, e não a
  lista em memória, que pode estar velha. A própria moto (mesmo `id`) é
  ignorada.
- **Estoque:** a regra da spec é aplicada antes de montar o payload. No
  formulário, o switch "Em estoque" fica desabilitado quando o status o
  determina.
- **Alternativa: preconditions nos endpoints do Xano.** Mais robusto contra
  concorrência, mas duplica regras em XanoScript sem teste e sem versionamento
  confiável do grupo CRUD. Fica como reforço futuro. O cenário de uso é
  majoritariamente um usuário por vez (D12, suposição a).

### 7. Exclusão protegida
O state mantém `REFERENCIAS_MOTO: list[tuple[str, str]]` (tabela, campo). A
lista está vazia nesta Change, porque nenhuma tabela tem `moto_id`. Antes do
`DELETE`, cada referência é consultada, e havendo vínculo a exclusão é negada
com a mensagem da spec. O próprio `DELETE` fica em `try/except`: qualquer
resposta de erro do Xano vira mensagem amigável e o registro é mantido.
- **Alternativa: precondition no `DELETE /motos/{id}` do Xano.** É o lugar
  certo a longo prazo, mas hoje não há tabela para consultar. A Change que
  criar `ordens_servico.moto_id` deve adicionar a referência aqui **e** a
  precondition no endpoint.

O arquivo da foto não é apagado do armazenamento ao excluir ou substituir.
Isso está registrado como non-goal.

### 8. Rota, menu e visual
- Rota `/motocicletas`, com `on_load=[AuthState.exigir_login, MotocicletasState.carregar]`.
- Item de menu "Motocicletas" logo após "Clientes", com ícone `gauge`, para não
  repetir o `bike` de "Motos dos clientes" na trilha só de ícones do celular.
- Nenhuma cor nova: `rx.card`, `rx.badge` e botões com o tema (`accent_color="orange"`),
  mais as constantes de `layout.py` (`LARANJA_HARLEY`, `TEXTO_SUAVE`) e
  `rx.color("gray", n)`, como Produtos e Motos já fazem. Cores dos badges de
  status: esquemas do Radix já disponíveis (green, amber, blue, gray, orange).
- Tabela dentro de `rx.box(overflow_x="auto", width="100%")`. Cards de resumo
  em `rx.grid` com `columns=rx.breakpoints(initial="2", sm="3", md="5")`.
- Mensagens de sucesso e erro via `rx.toast`, disponível no Reflex 0.7.

### Decisões em aberto de `docs/explore/2026-09-16-decomposicao-funcional.md`
- **Pressupõe:**
  - D2(a): o usuário cria tabela e endpoints à mão.
  - D12(a): uso majoritariamente de um usuário por vez.
- **Resolve parcialmente:** D9(a), com fotos no Xano **só** para Motocicletas.
- **Convive com:**
  - D5(c): testes gravam na base real, limitados à tabela nova.
  - C1: API sem token.
- **Não toca:** D1, D3, D4, D6, D7, D8, D10 e D11.

## Risks / Trade-offs

- [Duas fontes de "moto" confundem o usuário: a mesma moto pode ser cadastrada
  nas duas telas] → Rótulos distintos no menu ("Motocicletas" x "Motos dos
  clientes"). Registrar em `docs/domain-model.md` como lacuna, com a unificação
  como Change futura.
- [O `image` input do Xano pode não aceitar o objeto de metadados como JSON] →
  O endpoint versionado declara `foto` como `json?` na entrada e grava no campo
  `image`. A tarefa de verificação confere isso no painel antes de ligar a tela.
- [Resposta de imagem sem `url`] → Fallback host + `path` (decisão 3).
- [Duplicidade verificada só no app: duas gravações simultâneas passam] →
  Aceito sob D12(a). Precondition no Xano como reforço futuro.
- [Arquivos temporários de prévia acumulam em `uploaded_files/` se a sessão cair
  antes de salvar ou cancelar] → `carregar` apaga `tmp_moto_*` com mais de 24 h.
- [Cota de armazenamento do plano Free] → Limite de 5 MB por foto. Fotos
  substituídas ficam órfãs no Xano (non-goal), a revisar se a cota apertar.
- [Testes gravam na base real (D5)] → Registros de teste marcados em
  `observacoes` como "TESTE" e excluídos ao final da verificação.

## Migration Plan

1. **Xano (manual):**
   - criar a tabela `motos` conforme `xano/table/motos.xs`;
   - gerar o CRUD da tabela no grupo CRUD;
   - ajustar o GET de lista com os filtros;
   - criar `POST /motos/foto`;
   - conferir tudo com `curl` (tarefas de verificação).
2. **Código:** state, página, rota, menu e função de upload.
3. **Verificação ponta a ponta** com registros de teste.
4. **Rollback:** remover rota e item de menu. A tabela e os endpoints no Xano
   podem ficar, pois não afetam as demais telas. Nenhum dado existente é
   alterado em nenhum passo.

## Conferência no Xano (2026-09-16)

Resultado da configuração manual (tarefas 2.1–2.4), com registro de teste
criado, alterado e excluído:

- Grupo de API: **`HARLEY`** (`api:LtU_pM2N`). Os `.xs` foram atualizados.
- `foto` como `json` na entrada de POST/PATCH aceita o objeto de metadados. A
  resposta de `POST motos/foto` traz `url` pública (redireciona 303 para a
  imagem). `foto: null` no PATCH remove a foto.
- **Nulos viram valor padrão:** `cliente_id`, `preco_*` e `data_saida`
  enviados como `null` são gravados como `0`, e textos opcionais como `""`
  (mesmo comportamento da lacuna L3). O app já trata `cliente_id = 0` como
  "Sem cliente" e `data_saida = 0` como vazia. Preço `0` passou a ser tratado
  como "não informado" (`preco_informado`). O filtro `GET /motos?cliente_id=`
  não serve para listar "motos sem cliente".
- `POST /motos` ignora `updated_at` (grava 0); o PATCH grava. Consequência:
  moto recém-cadastrada fica com `updated_at = 0` até a primeira edição. Para
  corrigir, basta adicionar a entrada `updated_at` no POST do painel. Não
  bloqueia a Change.
- `GET /motos/{id}` de id inexistente devolve `null` com HTTP 200 (não 404);
  `DELETE` devolve a mensagem "Registro excluído com sucesso.".
- Os uploads de teste deixaram 2 imagens órfãs no armazenamento (non-goal:
  arquivos não são apagados).

## Open Questions

- Nenhuma: o nome do grupo foi confirmado na conferência acima.
