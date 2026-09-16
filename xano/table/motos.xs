// Motocicletas da concessionária — 1 registro = 1 motocicleta individual.
// Controla estoque por unidade (status + em_estoque), valores, datas e foto
// guardada no armazenamento de arquivos do Xano. Convive em paralelo com
// `motos_clientes` (usada por ordens_servico e transacoes); a unificação é
// uma Change futura (ver openspec/changes/cadastro-motocicletas/design.md).
table motos {
  auth = false

  schema {
    int id
    timestamp created_at?=now

    // Preenchido pelo app a cada gravação
    timestamp updated_at?

    // Relacionamento com Clientes (nulo = moto em estoque sem proprietário)
    int cliente_id?

    text marca filters=trim
    text modelo filters=trim
    int ano
    text cor? filters=trim

    // Placa e chassi: maiúsculas, sem espaço/hífen; unicidade validada no app
    text placa? filters=trim
    text chassi? filters=trim

    int quilometragem?=0

    // Status: Em estoque, Reservada, Em manutenção, Vendida, Entregue
    text status?="Em estoque"

    bool em_estoque?=true

    // Metadados do arquivo no armazenamento do Xano (path, url, mime, ...)
    image foto?

    decimal preco_compra?
    decimal preco_venda?
    timestamp data_entrada?

    // Nulo enquanto a moto estiver na loja
    timestamp data_saida?

    text observacoes?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "cliente_id"}]}
  ]
}
