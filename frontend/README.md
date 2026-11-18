# Multilang — protótipo do estúdio

Interface local em português, React + TypeScript + Vite. O escopo desta entrega é
o painel administrativo: produções, configuração e resultado/revisão. Loja e
gerador público permanecem em planejamento.

A direção visual é grafite e azul. A hierarquia, a paleta e o comportamento
responsivo estão em [DESIGN.md](DESIGN.md).

## Executar

Com Node.js 22.20+ e npm, a partir de `frontend/`:

```powershell
npm ci
npm run dev
```

Abra `http://127.0.0.1:5174`. Use `npm test` para as verificações de estado e
`npm run build` para verificar os tipos e empacotar. `dist/` é temporário e ignorado.

Depois do build, `npm run preview:artifact` cria uma prévia HTML independente em
`output/previews/admin-prototype/index.html`. Ela pode ser aberta diretamente,
sem servidor. O código-fonte permanece em `frontend/`.

Em ambientes Windows com certificados corporativos, o Node instalado pode
precisar de `--use-system-ca` em `NODE_OPTIONS` para instalar dependências.
Mantenha a validação TLS habilitada.

## Explorar

### Provedores e conexões reais (Windows, uso pessoal local)

Abra `frontend/Abrir Estúdio.cmd` e acesse o link local mostrado na janela.
Mantenha essa janela aberta durante o uso. O iniciador usa o build em `frontend/dist`
e o ambiente isolado `.venv-studio-win` desta worktree. Não há instalação automática nem geração ao iniciar.
Se necessário, prepare o build com `npm --prefix frontend run build`; as dependências
do serviço são FastAPI, Uvicorn, HTTPX e Pydantic Settings, já declaradas no projeto.
Para preparar o ambiente em outra máquina Windows, use uma instalação oficial de Python
compatível com o projeto (3.12+): `python -m venv .venv-studio-win`, seguido de
`uv pip install --python .venv-studio-win/Scripts/python.exe fastapi uvicorn httpx pydantic-settings`.
Nesta máquina foi validado o Python oficial 3.13.7. As distribuições standalone do uv
presentes apresentaram falha nativa OpenSSL ao configurar `SSLKEYLOGFILE`; nenhuma
configuração de registro TLS ou validação de certificado foi removida para contornar isso.
Esse ambiente mínimo atende às conexões; executar o pipeline completo exige as
dependências do projeto em seu ambiente correspondente. O baseline do projeto permanece 3.12.

Na seção **Provedores e conexões**:

1. Escolha OpenAI por chave de API ou ChatGPT pelo Codex local.
2. Para ChatGPT, clique em **Entrar com ChatGPT**, abra o link oficial e conclua o
   login no navegador. Volte e use **Verificar login**.
3. Salve a conexão, consulte os modelos disponíveis e selecione um modelo de texto.
   `gpt-6-luna` é uma sugestão, não uma garantia de acesso pela sua conta.
4. Informe as chaves de DeepL e Azure Speech e a região do recurso Azure, se usados.
5. Salve e use **Verificar conexão**. Essas consultas leem modelos, consumo ou vozes;
   não sintetizam áudio nem geram cartões. Campo de chave vazio preserva a chave atual;
   **Remover chave** a apaga explicitamente do cofre local.

O servidor aceita apenas `127.0.0.1`, exige sessão local e a mesma origem nas alterações.
O código temporário do link é retirado da barra de endereço após a autenticação;
a sessão usa cookie HttpOnly/SameSite. Não compartilhe o link de acesso.
As chaves são criptografadas com DPAPI, vinculadas ao usuário Windows, em
`.multilang/studio/connections.dpapi`, ignorado pelo Git. Elas não ficam em
localStorage, nos arquivos do frontend nem nas respostas da API.

O login Codex requer o CLI oficial instalado. Foi conferido o handshake com a versão
0.167.0. Usa `CODEX_HOME` próprio em `.multilang/studio/codex` e o cofre do sistema
(`cli_auth_credentials_store=keyring`); não copia a sessão principal do Codex.
Chamadas de conteúdo usam sessões efêmeras, sandbox somente leitura e ferramentas
de execução, navegação e delegação desabilitadas. JSON e validações do projeto
continuam obrigatórios. Esse caminho é somente para uso pessoal local; uso comercial
ou hospedado exige API ou integração comercial oficial Sign in with ChatGPT.

**Integração com o pipeline:** comandos/worker que devem usar o cofre precisam iniciar
com `MULTILANG_STUDIO_CONNECTIONS_ENABLED=1` e com esta worktree como diretório atual.
O iniciador do estúdio já define essa opção para seu processo. Workers separados
precisam da mesma opção; releem o cofre antes de cada tarefa. Configuração em memória
de uma tarefa já iniciada não muda. Não são alterados os gates de geração, as evidências,
a autorização de chamadas nem a aprovação dos inventários. O transporte Codex reutiliza
os adaptadores e validadores de conteúdo; OpenAI usa LiteLLM, com parâmetros compatíveis
com GPT-6 e teto de saída por chamada. O teto não é um orçamento monetário.

**Limites atuais:** a tela de conexões é real, mas produções, progresso e resultados do
frontend continuam demonstrativos. Esta entrega não conecta o botão de simulação à
fila real. Geração, tradução, áudio e exportação reais permanecem para uma etapa
explicitamente autorizada. Estimativa de custo não é apresentada sem dados de uso e
preços validados. A prévia HTML independente permite ver a tela, mas desabilita os
campos de credenciais por não possuir backend.

Referências: [Codex App Server](https://learn.chatgpt.com/docs/app-server),
[GPT-6](https://developers.openai.com/api/docs/guides/latest-model),
[Windows DPAPI](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata).

1. Abra a produção demonstrativa ou clique em Nova produção.
2. Mantenha Inglês + Frequência + apoio em Português e clique em Simular produção.
3. Confira as etapas ilustrativas e o resultado com seis registros.
4. Busque uma palavra, filtre pendências, veja frente/verso no template Anki e edite o conteúdo.
5. Alterar uma frase invalida o áudio ilustrativo e exige nova revisão.

Outras configurações podem ser salvas como rascunhos nesta sessão. Os seletores
representam o planejamento; não afirmam suporte qualificado para cada combinação.
Editar e salvar um rascunho atualiza a mesma produção; Nova produção começa outro
rascunho. As situações dos cartões aparecem por escrito na lista de revisão.
O idioma de apoio é salvo por rascunho: Português (`pt`), Inglês (`en`) ou
Espanhol (`es`). Coreano aceita apenas Português; selecionar Coreano ajusta o
apoio para Português e avisa sobre a mudança. A escolha aparece no resumo e na
lista de produções. O aplicativo continua em português.

A simulação só usa a combinação dos fixtures: Inglês + Frequência + apoio em
Português. Outras combinações válidas podem ser salvas, sem simulação. O resultado
mostra o idioma dos seus próprios dados, independentemente do rascunho aberto.
Todos os dados são em memória: recarregar descarta rascunhos e edições. As rotas
de demonstração usam `#producoes`, `#nova` e `#resultado`.

## Anexar arquivos

Em Nova produção, escolha uma das modalidades abaixo. A seção Conteúdo e
apresentação mostra o seletor de arquivo:

- Lista personalizada: `.txt` em UTF-8; prefira uma palavra ou expressão por linha.
- Destaques de leitura: exportação do Kindle `.txt`, `.html` ou `.htm`. No TXT,
  os destaques são separados por `==========`. Escolha entre extrair palavras de
  trechos ou usar cada destaque como palavra/expressão. Coreano aceita apenas o
  modo de trechos de leitura.

O limite local é de 5 MB por arquivo. O protótipo verifica extensão, tamanho e
leitura UTF-8; não reproduz os parsers lexicais ou certifica a estrutura Kindle.
Arquivos vazios, binários ou com codificação inválida apresentam erro próximo ao
seletor. Se uma substituição falhar, o anexo anterior é mantido.

É possível conferir até 2.000 caracteres de TXT, substituir e remover o anexo.
HTML é mantido como arquivo, sem renderizar seu conteúdo ou carregar recursos
externos. O arquivo original fica no rascunho em memória, inclusive ao reabri-lo;
nada é enviado ao servidor. Mudar a modalidade remove o anexo anterior com aviso.
Recarregar a página descarta os anexos. Rascunhos incompletos podem ser salvos.

O nome do arquivo aparece no resumo e na lista de produções. Anexar um arquivo
não habilita geração, simulação ou exportação dessas modalidades.

## Integração e limites

Não há chamadas à API, provedores, banco, geração real, áudio real, exportação ou
publicação comercial. A prévia de frente e verso usa o HTML e CSS dos modelos
Anki reais construídos pelos exportadores existentes. Os valores exibidos são
fixtures visuais, não inventários nem cartões aprovados; combinações sem
exportador/template disponível são marcadas como indisponíveis, sem substituição
por um mockup.

O catálogo usado pela interface fica em
`apps/admin/src/anki-template-manifest.json`. Depois de alterar qualquer modelo
Anki, regenere-o na raiz do repositório com
`uv run --project . python scripts/generate_anki_template_manifest.py`.
`tests/services/test_anki_template_preview.py` verifica que o catálogo não deriva
dos templates atuais.

O contrato de idioma de apoio acompanha o commit `bdb0548` da arquitetura.
O commit não foi incorporado por merge/cherry-pick: a adaptação é somente do
protótipo. A futura integração deverá enviar `support_language` explicitamente e
preservar o valor persistido ao retomar um job. Retomada de jobs ainda não existe
nesta interface.

## Estrutura

`apps/admin/src/` contém a interface administrativa. A separação futura proposta
é `apps/web/` para loja/gerador/biblioteca e `packages/` para componentes
compartilhados; essas pastas serão criadas quando houver consumidores reais.

Decisões e dependências: `docs/product-interface.md`, na raiz do repositório.
