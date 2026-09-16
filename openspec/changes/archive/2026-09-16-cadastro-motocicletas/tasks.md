## 1. Receita do backend (versionada no repositório)

- [x] 1.1 Criar `xano/table/motos.xs` com o esquema e os índices da decisão 1 do design (comentário de propósito no topo, `cliente_id?` com btree) e verificar que todos os campos da spec "Motocicleta é um registro individual" estão presentes
- [x] 1.2 Criar `xano/api/crud/motos/motos_GET.xs` (lista com filtros opcionais `cliente_id`, `status`, `em_estoque`, `marca`, `modelo`, `ano`), `motos_id_GET.xs`, `motos_POST.xs`, `motos_id_PATCH.xs` e `motos_id_DELETE.xs`, e verificar que `POST`/`PATCH` declaram `foto` como `json?` e gravam no campo `image`
- [x] 1.3 Criar `xano/api/crud/motos/foto_POST.xs` (entrada `file arquivo`, `storage.create_image` com acesso público, resposta = metadados) e verificar que nenhum `.xs` contém segredo ou token
- [x] 1.4 Escrever `xano/api/crud/motos/LEIA-ME.md` com o passo a passo manual no painel do Xano (criar tabela, gerar CRUD, editar o GET de lista, criar o endpoint de foto, conferir o nome do `api_group`) e os comandos `curl` de conferência da tarefa 2

## 2. Configuração manual no Xano (executada pelo usuário) e conferência

- [x] 2.1 Usuário cria a tabela `motos` e os endpoints seguindo o LEIA-ME; verificar com `curl GET .../api:LtU_pM2N/motos` → HTTP 200 e `[]`
- [x] 2.2 Conferir o upload: `curl -F arquivo=@teste.jpg .../motos/foto` devolve metadados com `path` (e `url`, se houver), e a URL montada abre a imagem no navegador
- [x] 2.3 Conferir a gravação: `POST /motos` com `foto` = metadados do 2.2 e `cliente_id` nulo → `GET /motos/{id}` devolve a foto e `cliente_id: null`; depois `GET /motos?cliente_id=<id>` filtra e `DELETE /motos/{id}` remove o registro de teste
- [x] 2.4 Atualizar os `.xs` da tarefa 1 se algo no painel diferir (nome do `api_group`, tipo aceito em `foto`) e registrar a diferença no design

## 3. Cliente HTTP

- [x] 3.1 Adicionar em `harley_store/xano_client.py` a função async `enviar_foto(rota, conteudo, nome, mime)` (multipart via `_request`) e `url_arquivo(metadados)` (usa `url` ou host da `BASE_URL` + `path`); verificar chamando-as num script rápido contra o endpoint do 2.2

## 4. State `motocicletas_state.py`

- [x] 4.1 Criar `harley_store/state/motocicletas_state.py` com constantes (`STATUS_MOTO`, formatos aceitos, 5 MB, `REFERENCIAS_MOTO = []`) e `carregar` async (motos + clientes em `try/except`, normalização com `xano.texto/numero/inteiro/epoch_ms_para_datetime`, flags `carregando`/`erro_carregamento`, limpeza de `tmp_moto_*` com mais de 24 h); verificar que a tela compila e mostra os estados de carregando e erro (derrubando a rede)
- [x] 4.2 Implementar os vars derivados: lista filtrada (busca + marca, modelo, ano, status, estoque, cliente), opções dos selects, cards de resumo sobre a lista completa e opções de cliente filtradas pela pesquisa com "Sem cliente"; verificar os cenários "Filtros combinados", "Motos de um cliente" e "Pesquisar cliente"
- [x] 4.3 Implementar `abrir_cadastro`, `abrir_edicao` (preenche tudo, incluindo `foto_atual`) e `cancelar` (fecha e apaga temporário); verificar o cenário "Cancelar"
- [x] 4.4 Implementar `handle_upload_foto` (valida extensão e tamanho, grava temporário `tmp_moto_*`, mantém a foto anterior em caso de erro) e `remover_foto`; verificar os cenários "Prévia antes de salvar" e "Arquivo incompatível"
- [x] 4.5 Implementar `salvar`: validações e normalização (decisão 6), duplicidade com `listar` fresco ignorando a própria moto, regra status ↔ `em_estoque`/`data_saida`, upload da foto só se houver temporário, payload completo com `updated_at`, `criar`/`atualizar`, toast de sucesso e recarga; verificar os cenários de "Validações do cadastro" e "Controle de estoque por unidade"
- [x] 4.6 Implementar `excluir` (checa `REFERENCIAS_MOTO`, trata erro do `DELETE` com mensagem amigável, toast de sucesso e recarga) e `ampliar_foto`/`fechar_foto`; verificar os cenários de "Exclusão com confirmação e proteção de vínculos"

## 5. Página, rota e menu

- [x] 5.1 Criar `harley_store/pages/motocicletas.py` com cabeçalho (título, subtítulo, botão "+ Cadastrar Moto"), cards de resumo, barra de busca e filtros, tabela em `rx.box(overflow_x="auto")` com miniatura, badge de status, estoque, preço formatado e ações, e os estados de carregando/vazio/erro; verificar visualmente que só as cores do tema e das constantes de `layout.py` são usadas
- [x] 5.2 Implementar o diálogo de formulário (5 seções em `rx.grid` responsivo, campo de foto com prévia/"Adicionar foto da motocicleta"/"Remover foto", pesquisa + select de cliente, switch "Em estoque" desabilitado quando o status determina, botões "Cancelar" e "Cadastrar Moto"/"Salvar alterações") e o diálogo de foto ampliada; exclusão via `confirm_delete_button` com o texto da spec
- [x] 5.3 Registrar a rota `/motocicletas` em `harley_store/harley_store.py` (`AuthState.exigir_login` primeiro) e o item "Motocicletas" (ícone `gauge`) após "Clientes" em `components/layout.py`; verificar que `/motos`, OS e vendas continuam abrindo e funcionando como antes

## 6. Documentação

- [x] 6.1 Atualizar `docs/domain-model.md`: entidade `motos`, relacionamento `clientes 1:N motos`, regras (placa/chassi únicos no app, status ↔ em_estoque), lacuna "duas fontes de moto (`motos` x `motos_clientes`)" e o vínculo futuro `ordens_servico.moto_id`; verificar que o diagrama e a tabela de entidades citam `motos`

## 7. Verificação ponta a ponta

- [x] 7.1 Rodar `reflex run` e verificar que compila sem erro nem aviso novo no terminal e sem erro no console do navegador
- [x] 7.2 Com registros de teste (observação "TESTE"): abrir a página, listar, pesquisar, filtrar por marca, modelo, ano, status e estoque, cadastrar com cliente e foto (conferir registro e foto via `curl GET /motos/{id}`), editar trocando a foto (conferir a nova referência), editar sem trocar a foto (referência igual), marcar como "Vendida" (cards e `data_saida`), tentar placa e chassi duplicados, excluir, e recarregar a página confirmando persistência
- [x] 7.3 Verificar responsividade em ~390px (DevTools e, se possível, no iPhone como PWA): nada ultrapassa a tela, a tabela rola dentro da área, o diálogo cabe com rolagem e os botões são clicáveis
- [x] 7.4 Excluir os registros de teste e rodar `openspec validate cadastro-motocicletas`
