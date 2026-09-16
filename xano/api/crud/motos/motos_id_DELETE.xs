// Exclui uma motocicleta. Hoje nenhuma tabela referencia `motos`; quando
// `ordens_servico.moto_id` existir, adicionar aqui um db.has + precondition
// que recuse a exclusão de moto com OS vinculada (design, decisão 7).
// O arquivo da foto não é removido do armazenamento.
query "motos/{motos_id}" verb=DELETE {
  api_group = "HARLEY"

  input {
    int motos_id? filters=min:1
  }

  stack {
    db.del motos {
      field_name = "id"
      field_value = $input.motos_id
    }
  }

  response = null
  tags = ["harley-store"]
}
