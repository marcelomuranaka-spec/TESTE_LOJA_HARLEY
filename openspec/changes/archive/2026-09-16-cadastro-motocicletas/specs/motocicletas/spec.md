## Purpose

Permitir que a loja cadastre e controle cada motocicleta como um bem
individual: identificação do veículo, foto guardada no backend, dono opcional,
situação de estoque, valores, consulta e exclusão protegida.

## ADDED Requirements

### Requirement: Motocicleta é um registro individual
O sistema SHALL armazenar cada motocicleta como um registro próprio, separado
de produtos e de "motos dos clientes". Cada registro guarda marca, modelo, ano,
cor, placa, chassi, quilometragem, status, indicador de estoque, foto, preço de
compra, preço de venda, data de entrada, data de saída, observações, data de
criação e data de atualização. O registro MUST referenciar o cliente apenas
pelo identificador (`cliente_id`), sem copiar nome, documento, telefone ou
email. `cliente_id` MAY ser nulo.

#### Scenario: Moto em estoque sem dono
- **WHEN** o usuário cadastra uma motocicleta escolhendo "Sem cliente"
- **THEN** o registro é salvo com `cliente_id` nulo e aparece na tabela com o cliente exibido como "Sem cliente"

#### Scenario: Moto vinculada a cliente
- **WHEN** o usuário cadastra uma motocicleta escolhendo um cliente existente
- **THEN** o registro é salvo com o `cliente_id` desse cliente, e a tabela mostra o nome atual do cliente, buscado pelo relacionamento

#### Scenario: Cadastros existentes não mudam
- **WHEN** a nova funcionalidade é publicada
- **THEN** a tela "Motos dos clientes", as ordens de serviço e as vendas continuam funcionando com os mesmos dados de antes

### Requirement: Página de Motocicletas
O sistema SHALL oferecer uma página "Motocicletas", acessível pelo menu
principal e só para usuários logados. A página tem o subtítulo "Gerencie as
motocicletas cadastradas, estoque e informações dos veículos." e o botão
"+ Cadastrar Moto". Ela MUST seguir a identidade visual atual do sistema (tema
escuro, cores e componentes existentes) e MUST funcionar em telas de celular
sem que elementos ultrapassem a largura da tela. Tabelas largas usam rolagem
horizontal.

#### Scenario: Acesso sem login
- **WHEN** um visitante não autenticado abre a página de Motocicletas
- **THEN** ele é redirecionado para a tela de login

#### Scenario: Uso no celular
- **WHEN** a página é aberta numa tela de ~390px de largura
- **THEN** cards e filtros empilham, a tabela rola na horizontal dentro da própria área, e o formulário cabe na tela com rolagem vertical

### Requirement: Estados de carregamento, vazio e erro
A página SHALL mostrar "Carregando motocicletas..." enquanto busca os dados.
Sem nenhum registro, mostra "Nenhuma motocicleta cadastrada." com o botão
"+ Cadastrar primeira moto". Se a busca falhar, mostra "Não foi possível
carregar as motocicletas.". Depois de cadastrar, editar ou excluir com sucesso,
MUST mostrar uma mensagem de sucesso.

#### Scenario: Falha ao carregar
- **WHEN** o backend não responde ou devolve erro ao listar motocicletas
- **THEN** a página mostra "Não foi possível carregar as motocicletas." em vez da tabela, sem quebrar a tela

#### Scenario: Lista vazia
- **WHEN** não existe nenhuma motocicleta cadastrada
- **THEN** a página mostra "Nenhuma motocicleta cadastrada." e o botão "+ Cadastrar primeira moto", que abre o formulário de cadastro

### Requirement: Cards de resumo com dados reais
A página SHALL mostrar cards com: total de motos, motos em estoque
(`em_estoque` verdadeiro), reservadas (status "Reservada"), em manutenção
(status "Em manutenção") e vendidas (status "Vendida" ou "Entregue"). Os
números MUST ser calculados sobre todos os registros vindos do backend,
independentemente dos filtros aplicados, e MUST ser atualizados após cadastro,
edição ou exclusão.

#### Scenario: Resumo após venda
- **WHEN** uma moto com status "Em estoque" é editada para "Vendida"
- **THEN** o card "Em estoque" diminui em 1 e o card "Vendidas" aumenta em 1, sem recarregar a página

### Requirement: Tabela de motocicletas
A página SHALL listar as motocicletas numa tabela com as colunas Foto, Marca,
Modelo, Ano, Placa, Cliente, KM, Status, Estoque, Preço e Ações (Editar e
Excluir). A miniatura MUST ter tamanho fixo, cantos arredondados e proporção
preservada com recorte. Sem foto, a célula mostra um marcador visual do mesmo
tamanho. Clicar na miniatura MUST abrir a foto ampliada numa janela sobreposta.

#### Scenario: Moto sem foto
- **WHEN** uma motocicleta não possui foto
- **THEN** a célula Foto mostra o marcador no mesmo tamanho da miniatura, e o alinhamento da linha não muda

#### Scenario: Ampliar foto
- **WHEN** o usuário clica na miniatura de uma moto com foto
- **THEN** a foto é exibida em tamanho maior numa janela que pode ser fechada

### Requirement: Busca e filtros
A página SHALL oferecer busca textual (marca, modelo, placa, chassi, cor e nome
do cliente) e filtros por marca, modelo, ano, status, estoque (Todos, Em
estoque, Fora do estoque) e cliente. As opções de marca, modelo e ano MUST vir
dos registros existentes. Filtros e busca MUST ser combináveis. Filtrar por
cliente MUST mostrar todas as motocicletas daquele cliente.

#### Scenario: Filtros combinados
- **WHEN** o usuário escolhe a marca "Harley-Davidson" e o estoque "Em estoque"
- **THEN** a tabela mostra apenas motos dessa marca com `em_estoque` verdadeiro

#### Scenario: Motos de um cliente
- **WHEN** o usuário filtra pelo cliente "João da Silva"
- **THEN** a tabela mostra todas as motocicletas com o `cliente_id` desse cliente

### Requirement: Consulta de motocicletas por API com filtros
O backend SHALL expor a listagem de motocicletas com filtros opcionais por
`cliente_id`, `status`, `em_estoque`, `marca`, `modelo` e `ano`, além da busca
de uma motocicleta por id, cadastro, atualização e exclusão.

#### Scenario: Listar motos de um cliente pela API
- **WHEN** a listagem é chamada com `cliente_id` igual a 3
- **THEN** a resposta contém apenas motocicletas com `cliente_id` 3

#### Scenario: Listar sem filtros
- **WHEN** a listagem é chamada sem parâmetros
- **THEN** a resposta contém todas as motocicletas

### Requirement: Formulário de cadastro e edição
O sistema SHALL oferecer um formulário, aberto por "+ Cadastrar Moto" ou por
"Editar", com as seções Informações da motocicleta (foto, marca, modelo, ano,
cor, placa, chassi, quilometragem), Estoque (status, em estoque), Valores
(preço de compra, preço de venda), Cliente e Informações adicionais (data de
entrada, observações), e os botões "Cancelar" e "Cadastrar Moto" ("Salvar
alterações" na edição). O cliente MUST ser escolhido numa lista pesquisável
carregada do backend, com a opção "Sem cliente". Na edição, o formulário MUST
vir preenchido com todos os valores atuais, incluindo a foto.

#### Scenario: Pesquisar cliente
- **WHEN** o usuário digita "silva" no campo de pesquisa de cliente
- **THEN** a lista de clientes mostra apenas os nomes que contêm "silva" e continua oferecendo "Sem cliente"

#### Scenario: Editar mantém dados
- **WHEN** o usuário abre "Editar" numa moto e salva sem alterar nada
- **THEN** todos os campos, incluindo a foto, permanecem iguais no backend, e a data de atualização muda

#### Scenario: Cancelar
- **WHEN** o usuário preenche o formulário e clica em "Cancelar"
- **THEN** o formulário fecha e nada é gravado

### Requirement: Validações do cadastro
O sistema SHALL recusar o salvamento, com mensagem explicativa, quando:
- marca, modelo ou ano estiverem vazios;
- o ano não for um número inteiro entre 1900 e o ano atual + 1;
- a quilometragem não for um número inteiro maior ou igual a zero;
- um preço não for um valor monetário maior ou igual a zero;
- uma placa informada não estiver no formato brasileiro antigo (AAA9999) nem
  no Mercosul (AAA9A99);
- um chassi informado não tiver 17 caracteres alfanuméricos sem as letras I, O
  e Q.

Placa e chassi MUST ser gravados em maiúsculas e sem espaços ou hífens. O
sistema MUST recusar placa ou chassi já usados por outra motocicleta, com as
mensagens "Já existe uma motocicleta cadastrada com esta placa." e "Já existe
uma motocicleta cadastrada com este chassi.". Placa e chassi são opcionais.

#### Scenario: Campos obrigatórios
- **WHEN** o usuário tenta cadastrar sem informar o modelo
- **THEN** nada é gravado e o formulário indica que marca, modelo e ano são obrigatórios

#### Scenario: Placa duplicada
- **WHEN** o usuário cadastra uma moto com a placa "abc-1d23" e já existe outra moto com a placa "ABC1D23"
- **THEN** nada é gravado e aparece "Já existe uma motocicleta cadastrada com esta placa."

#### Scenario: Editar a própria placa
- **WHEN** o usuário edita uma moto e mantém a placa dela
- **THEN** a validação de duplicidade não considera a própria moto e o salvamento prossegue

#### Scenario: Valor negativo
- **WHEN** o usuário informa preço de venda "-100"
- **THEN** nada é gravado e aparece mensagem de valor inválido

### Requirement: Controle de estoque por unidade
Cada motocicleta SHALL ter um status entre "Em estoque", "Reservada", "Em
manutenção", "Vendida" e "Entregue", e um indicador booleano `em_estoque`. Um
cadastro novo começa com status "Em estoque", `em_estoque` verdadeiro,
quilometragem 0 e data de entrada igual à data atual. Ao salvar:
- status "Vendida" ou "Entregue" MUST gravar `em_estoque` falso e preencher a
  data de saída com o momento atual, se estiver vazia;
- status "Em estoque" MUST gravar `em_estoque` verdadeiro e limpar a data de
  saída;
- "Reservada" e "Em manutenção" MUST respeitar o valor de `em_estoque`
  escolhido no formulário.

#### Scenario: Marcar como vendida
- **WHEN** uma moto em estoque é salva com status "Vendida"
- **THEN** o registro fica com `em_estoque` falso e com data de saída preenchida

#### Scenario: Reserva mantém na loja
- **WHEN** uma moto é salva com status "Reservada" e "Em estoque" marcado
- **THEN** o registro fica com status "Reservada" e `em_estoque` verdadeiro

### Requirement: Foto da motocicleta no armazenamento do backend
O sistema SHALL permitir anexar uma foto por motocicleta nos formatos JPG,
JPEG, PNG ou WEBP, com até 5 MB. Arquivos de outro formato ou maiores MUST ser
recusados com mensagem, sem alterar a foto atual. Depois da seleção, o
formulário MUST mostrar a prévia e o botão "Remover foto". Sem foto, mostra
"Adicionar foto da motocicleta". O arquivo MUST ser enviado ao armazenamento
de arquivos do backend só quando o usuário confirmar o salvamento, e o
registro guarda a referência retornada pelo backend, nunca o conteúdo em
Base64. Se o envio da foto falhar, a motocicleta MUST NOT ser gravada e o
usuário vê uma mensagem de erro.

#### Scenario: Prévia antes de salvar
- **WHEN** o usuário seleciona um arquivo PNG de 2 MB
- **THEN** a prévia aparece no formulário e nada é enviado ao backend até ele clicar em salvar

#### Scenario: Arquivo incompatível
- **WHEN** o usuário seleciona um arquivo PDF ou uma imagem de 8 MB
- **THEN** aparece uma mensagem de arquivo inválido e a prévia continua como estava

#### Scenario: Foto persistida
- **WHEN** o usuário cadastra a moto com foto e recarrega a página em outro computador
- **THEN** a miniatura da foto aparece na tabela, servida pelo backend

#### Scenario: Editar sem trocar foto
- **WHEN** o usuário edita uma moto com foto e salva sem mexer na foto
- **THEN** nenhum arquivo é enviado e o registro mantém a mesma referência de foto

#### Scenario: Substituir foto
- **WHEN** o usuário edita uma moto, seleciona outra imagem e salva
- **THEN** a nova imagem é enviada ao backend e o registro passa a referenciá-la

#### Scenario: Remover foto
- **WHEN** o usuário edita uma moto, clica em "Remover foto" e salva
- **THEN** o registro fica sem foto e a tabela mostra o marcador

### Requirement: Exclusão com confirmação e proteção de vínculos
O sistema SHALL pedir confirmação antes de excluir, com a mensagem "Tem certeza
que deseja excluir esta motocicleta?" e os botões "Cancelar" e "Excluir".
Antes de excluir, MUST verificar se algum registro de outra tabela referencia
a motocicleta. Se houver vínculo, ou se o backend recusar a exclusão, MUST
manter o registro e mostrar "Esta motocicleta possui registros vinculados e
não pode ser excluída." ou uma mensagem de erro amigável.

#### Scenario: Cancelar exclusão
- **WHEN** o usuário clica em "Excluir" e depois em "Cancelar"
- **THEN** a motocicleta continua cadastrada

#### Scenario: Exclusão confirmada
- **WHEN** o usuário confirma a exclusão de uma moto sem vínculos
- **THEN** o registro é removido do backend, some da tabela, os cards são atualizados e aparece mensagem de sucesso

#### Scenario: Moto com vínculos
- **WHEN** o usuário confirma a exclusão de uma moto referenciada por outro registro
- **THEN** o registro é mantido e aparece "Esta motocicleta possui registros vinculados e não pode ser excluída."
