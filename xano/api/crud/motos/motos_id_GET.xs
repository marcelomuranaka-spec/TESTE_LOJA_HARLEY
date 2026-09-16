// Busca uma motocicleta pelo id.
query "motos/{motos_id}" verb=GET {
  api_group = "HARLEY"

  input {
    int motos_id? filters=min:1
  }

  stack {
    db.get motos {
      field_name = "id"
      field_value = $input.motos_id
    } as $moto

    precondition ($moto != null) {
      error_type = "notfound"
      error = "Motocicleta não encontrada."
    }
  }

  response = $moto
  tags = ["harley-store"]
}
