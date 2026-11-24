# Estúdio local do Multilang

O Estúdio usa React + TypeScript + Vite. Loja e Gerador pessoal são sites separados,
cada um com entrada, navegação e folha de estilo próprias. Ambos abrem diretamente
no navegador, sem build ou servidor:

- [Loja](apps/web/index.html): demonstração de cartão do Estúdio, catálogo em
  preparação e ajuda sobre baralhos prontos.
- [Gerador pessoal](apps/generator/index.html): instruções de formato para listas
  próprias e destaques do Kindle, sem upload ou geração nesta prévia.

Compra, conta e bibliotecas estão planejadas. A conta compartilhada é uma integração
futura; os sites não dependem um do outro para abrir. Hospedagem e domínios ficam
para uma etapa posterior.

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
do serviço e do executor estão declaradas no projeto. Para preparar uma nova
instalação Windows, na raiz da worktree e com Python 3.12+ compatível, execute:

```powershell
python -m venv .venv-studio-win
uv pip install --python .venv-studio-win/Scripts/python.exe -e .
```

A produção usa esse mesmo Python e o banco configurado para esta worktree.

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
Use **Substituir** para trocar uma chave principal. Em **Chaves adicionais**, use
**Editar** para mudar o nome ou a chave; deixe o campo da chave vazio para manter
o valor salvo. As alterações persistem após fechar e reabrir o Estúdio nesta worktree.

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

## Produções e revisão

Abra **Nova produção**, escolha o idioma, o idioma de apoio e uma modalidade
disponível no catálogo do servidor. Em frequência, selecione o nível. Listas
personalizadas aceitam TXT UTF-8. Destaques Kindle aceitam TXT, HTML e HTM,
até 5 MB por arquivo. A prévia usa os leitores do backend e informa quantos
itens foram reconhecidos. Para destaques em coreano, exibe somente contagens.

**Salvar rascunho** guarda a configuração e o anexo no IndexedDB deste navegador.
**Gerar produção** inicia a execução local e pode consumir os provedores
configurados. O Estúdio registra o andamento em `.multilang/studio/productions`.
Abra a produção para acompanhar as etapas ou corrigir um trabalho elegível.

Em uma produção concluída, abra **Resultado e revisão** para buscar notas, ouvir
áudios disponíveis e alterar campos editáveis. A revisão mantém uma cópia em
`.multilang/studio/reviews`. O download inclui as edições salvas e preserva o
pacote original na pasta de decks configurada para a worktree.

A prévia de template do formulário usa exemplos de apresentação. O catálogo de
templates está em `apps/admin/src/anki-template-manifest.json`. Atualize-o após
alterar modelos Anki com `uv run --project . python scripts/generate_anki_template_manifest.py`.

## Estrutura

`apps/admin/src/` contém a interface administrativa. `apps/web/` contém a vitrine
pública. A extração de componentes para `packages/` fica para quando houver
consumidores compartilhados.

Decisões e dependências: `docs/product-interface.md`, na raiz do repositório.
