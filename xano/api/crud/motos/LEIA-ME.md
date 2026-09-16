# Motocicletas — configuração manual no Xano

Receita da Change `openspec/changes/cadastro-motocicletas`. O plano Free não
tem Metadata API, então tudo abaixo é feito no painel do Xano (ou empurrado
pela extensão Xano do VS Code, se ela estiver sincronizada com o workspace).
Os arquivos `.xs` desta pasta e `xano/table/motos.xs` são a referência exata.

Nada aqui altera tabelas existentes: `motos_clientes`, `ordens_servico` e
`transacoes` ficam como estão.

## 1. Criar a tabela `motos`

Database → **Add Table** → nome `motos`. Campos (conforme `xano/table/motos.xs`):

| Campo | Tipo | Obrigatório | Padrão |
|---|---|---|---|
| `id` | integer (automático) | — | — |
| `created_at` | timestamp | não | now |
| `updated_at` | timestamp | não | — |
| `cliente_id` | integer (ou *table reference* → `clientes`) | **não** (nullable) | — |
| `marca` | text (filtro trim) | sim | — |
| `modelo` | text (filtro trim) | sim | — |
| `ano` | integer | sim | — |
| `cor` | text | não | — |
| `placa` | text | não | — |
| `chassi` | text | não | — |
| `quilometragem` | integer | não | 0 |
| `status` | text | não | `Em estoque` |
| `em_estoque` | boolean | não | true |
| `foto` | **image** | não | — |
| `preco_compra` | decimal | não | — |
| `preco_venda` | decimal | não | — |
| `data_entrada` | timestamp | não | — |
| `data_saida` | timestamp | não | — |
| `observacoes` | text | não | — |

Índices: além da PK, um índice btree em `cliente_id`. **Não** crie índice
único em placa/chassi (são opcionais; a unicidade é validada no app).

## 2. Endpoints no grupo CRUD (o mesmo de `api:LtU_pM2N`)

1. Abra o grupo de API que responde em `.../api:LtU_pM2N` e **anote o nome
   dele** (se não for `CRUD`, ajuste `api_group` nos `.xs` desta pasta).
2. Na tabela `motos`, use **Add API endpoints → CRUD Database Operations**
   nesse grupo. Isso gera `GET motos`, `GET motos/{motos_id}`, `POST motos`,
   `PATCH motos/{motos_id}` e `DELETE motos/{motos_id}`.
3. **GET motos** — adicione entradas opcionais `cliente_id` (int), `status`
   (text), `em_estoque` (bool), `marca` (text), `modelo` (text), `ano` (int) e,
   no *Query All Records*, uma condição por entrada usando o operador que
   **ignora valor vazio** (`==?` / "ignore if empty"), como em `motos_GET.xs`.
4. **POST motos** e **PATCH motos/{motos_id}** — troque o tipo da entrada
   `foto` de *image* para **json** (o app manda o objeto de metadados), e
   deixe `cliente_id`, `data_saida` e `foto` aceitarem nulo.
5. Crie à mão **POST motos/foto**: entrada `arquivo` do tipo **file resource**;
   função **Create Image Metadata** (File Storage) com *value* =
   `input.arquivo` e acesso **public**; resposta = o resultado dessa função.
   (Ver `foto_POST.xs`.)
6. Não é preciso autenticação: o grupo CRUD inteiro ainda responde sem token
   (dívida registrada como C1 `proteger-api-de-dados`).

## 3. Conferência (rodar no terminal, Git Bash)

```bash
B=https://x8ki-letl-twmt.n7.xano.io/api:LtU_pM2N

# 2.1 — tabela e listagem
curl -s -w "\nHTTP %{http_code}\n" "$B/motos"                      # esperado: [] e HTTP 200

# 2.2 — upload de foto (use qualquer JPG/PNG local)
curl -s -F "arquivo=@teste.jpg" "$B/motos/foto" | tee /tmp/foto.json
#   esperado: JSON com "path" (e "url"). Abra a url no navegador.

# 2.3 — gravação com foto, cliente nulo, filtro e exclusão
curl -s -X POST "$B/motos" -H "Content-Type: application/json" \
  -d "{\"marca\":\"TESTE\",\"modelo\":\"TESTE\",\"ano\":2022,\"cliente_id\":null,\"em_estoque\":false,\"foto\":$(cat /tmp/foto.json)}"
curl -s "$B/motos/<id>"                    # foto preenchida, cliente_id null
curl -s "$B/motos?em_estoque=false"        # deve trazer o registro de teste
curl -s "$B/motos?cliente_id=1"            # não deve trazer o registro de teste
curl -s -X DELETE "$B/motos/<id>" -w "HTTP %{http_code}\n"
```

Se algum passo divergir (nome do grupo, tipo aceito em `foto`, forma da
resposta de imagem), anote e avise: os `.xs` e o design da Change são
atualizados para refletir o que o painel realmente aceitou.
