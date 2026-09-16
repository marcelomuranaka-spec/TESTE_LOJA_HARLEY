// Recebe a foto de uma motocicleta (multipart/form-data, campo `arquivo`),
// grava no armazenamento de arquivos do Xano e devolve os metadados
// (path, name, size, mime, url...). O app envia esse objeto no campo `foto`
// de POST/PATCH motos. Não grava registro nenhum por si só.
// No painel: entrada do tipo "file resource" chamada `arquivo`.
query "motos/foto" verb=POST {
  api_group = "HARLEY"

  input {
    file arquivo
  }

  stack {
    storage.create_image {
      access = "public"
      value = $input.arquivo
      filename = ""
    } as $foto
  }

  response = $foto
  tags = ["harley-store"]
}
