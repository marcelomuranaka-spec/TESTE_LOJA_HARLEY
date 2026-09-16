// Atualiza uma motocicleta. Como os demais PATCH do grupo CRUD, espera o
// registro completo (menos id e created_at): o app reenvia todos os campos,
// inclusive `foto` inalterada quando a foto não mudou.
query "motos/{motos_id}" verb=PATCH {
  api_group = "HARLEY"

  input {
    int motos_id? filters=min:1
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
    db.get motos {
      field_name = "id"
      field_value = $input.motos_id
    } as $existente

    precondition ($existente != null) {
      error_type = "notfound"
      error = "Motocicleta não encontrada."
    }

    db.edit motos {
      field_name = "id"
      field_value = $input.motos_id
      data = {
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
