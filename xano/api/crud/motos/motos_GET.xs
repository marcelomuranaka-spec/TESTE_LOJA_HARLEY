// Lista motocicletas. Todos os filtros são opcionais: o operador `==?`
// ignora a condição quando a entrada não é informada. A tela Motocicletas
// chama sem filtros e filtra em memória (limite de requisições do plano Free);
// os filtros servem para outros consumidores, ex.: "motos do cliente".
query motos verb=GET {
  api_group = "HARLEY"

  input {
    int cliente_id?
    text status? filters=trim
    bool em_estoque?
    text marca? filters=trim
    text modelo? filters=trim
    int ano?
  }

  stack {
    db.query motos {
      where = $db.motos.cliente_id ==? $input.cliente_id && $db.motos.status ==? $input.status && $db.motos.em_estoque ==? $input.em_estoque && $db.motos.marca ==? $input.marca && $db.motos.modelo ==? $input.modelo && $db.motos.ano ==? $input.ano
      sort = {motos.marca: "asc", motos.modelo: "asc"}
      return = {type: "list"}
    } as $motos
  }

  response = $motos
  tags = ["harley-store"]
}
