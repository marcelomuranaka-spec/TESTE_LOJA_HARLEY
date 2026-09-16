// Cadastra uma motocicleta. `foto` recebe o objeto de metadados devolvido por
// POST motos/foto (não o arquivo, nem Base64). Validações de formato e
// duplicidade de placa/chassi são feitas no app (design, decisão 6).
query motos verb=POST {
  api_group = "HARLEY"

  input {
    int cliente_id?
    text marca filters=trim
    text modelo filters=trim
    int ano
    text cor? filters=trim
    text placa? filters=trim
    text chassi? filters=trim
    int quilometragem?
    text status? filters=trim
    bool em_estoque?
    json foto?
    decimal preco_compra?
    decimal preco_venda?
    timestamp data_entrada?
    timestamp data_saida?
    text observacoes?
    timestamp updated_at?
  }

  stack {
    db.add motos {
      data = {
        created_at   : "now"
        updated_at   : $input.updated_at
        cliente_id   : $input.cliente_id
        marca        : $input.marca
        modelo       : $input.modelo
        ano          : $input.ano
        cor          : $input.cor
        placa        : $input.placa
        chassi       : $input.chassi
        quilometragem: $input.quilometragem
        status       : $input.status
        em_estoque   : $input.em_estoque
        foto         : $input.foto
        preco_compra : $input.preco_compra
        preco_venda  : $input.preco_venda
        data_entrada : $input.data_entrada
        data_saida   : $input.data_saida
        observacoes  : $input.observacoes
      }
    } as $moto
  }

  response = $moto
  tags = ["harley-store"]
}
