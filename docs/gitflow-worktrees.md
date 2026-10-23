# Gitflow com worktrees

O Multilang adota Gitflow para organizar a integração e worktrees para manter
cada tarefa em seu próprio diretório. Os comandos usam Git nativo, sem depender
da extensão `git-flow`. A convenção de commits e o hook local estão descritos em
[CONTRIBUTING.md](../CONTRIBUTING.md). Proteções no servidor não são configuradas
por este fluxo.

## Branches e destinos

| Branch | Base | Destino | Uso |
|---|---|---|---|
| `main` | Base estável revisada | — | Versões estáveis, identificadas por tags `vX.Y.Z` |
| `develop` | `main` na inicialização | `release/*` | Integração do próximo lançamento |
| `feature/<slug>` | `develop` | `develop` | Funcionalidades e melhorias |
| `fix/<slug>` | `develop` | `develop` | Correções do desenvolvimento |
| `release/<version>` | `develop` | `main` e depois `develop` | Estabilização de versão, sem novas funcionalidades |
| `hotfix/<slug>` | `main` | `main` e depois `develop` | Correção urgente de versão publicada |

Use nomes curtos em minúsculas, com hífens. Uma tarefa corresponde a uma branch
e um worktree. Worktrees compartilham objetos, referências e configuração Git,
mas têm arquivos e índice próprios. Uma branch só pode estar ativa em um deles.

## Base e estado da organização

Organização local criada em 2026-10-23 por solicitação do usuário:

- `main` começa em `1b5e528fbbba42cc48e681081c57f4ffc4d5faa1`, o estado da
  **Monarch local escolhido pelo usuário**. Não foi usada `origin/Monarch`,
  que possui histórico divergente, nem a tag `v1.3` como base final.
- `develop` parte dessa mesma base e recebe a configuração do Gitflow.
- `Monarch` é preservada como branch legada, sem renomeação ou novos commits.
- `feature/roadmap-4-0-native-architecture` permanece uma feature em execução,
  no checkout principal. Não é a branch de integração e não foi incorporada
  em `main` ou `develop` nesta organização.
- Os merges feitos anteriormente nessa feature permanecem no histórico.
  A nova organização não desfaz nem modifica esse trabalho.
- Novas tarefas independentes partem de `develop`. Tarefas que dependam da
  feature em execução devem declarar essa dependência e usar uma branch própria,
  sem integrar prematuramente o Roadmap 4.

Worktrees de longa duração, relativos ao checkout principal:

| Branch | Diretório |
|---|---|
| `main` | `.worktrees/main` |
| `develop` | `.worktrees/develop` |
| `feature/roadmap-4-0-native-architecture` | checkout principal existente |

A feature Roadmap 4 só será integrada em `develop` quando estiver concluída,
revisada e testada, mediante solicitação de integração. Até lá, preserve seus
commits, arquivos pendentes e diretório. Não troque a branch do checkout principal.

Esta configuração é local. Publicação, mudança da branch padrão do GitHub e
proteções remotas ainda não foram realizadas. A escolha da base organiza o
histórico; não representa uma nova certificação da qualidade do produto.

## Iniciar uma tarefa

Execute a inspeção no checkout principal:

```bash
git status --short
git branch -a
git worktree list
```

Os exemplos seguintes pressupõem que a migração já criou `main` e `develop`.
Se houver remoto, atualize as referências com `git fetch --prune origin` e
sincronize a base no worktree que a possui, com `git merge --ff-only
origin/develop`. Se houver divergência, revise-a antes de continuar.

Crie o diretório a partir da raiz do checkout principal:

```bash
mkdir -p .worktrees
git worktree add -b feature/minha-tarefa .worktrees/feature-minha-tarefa develop
cd .worktrees/feature-minha-tarefa
uv sync --locked --extra dev
```

Para uma branch já existente, omita `-b`:

```bash
git worktree add .worktrees/feature-outra-tarefa feature/outra-tarefa
```

Não execute ambos os exemplos para a mesma branch. Se ela já estiver ativa,
use o diretório informado por `git worktree list`. Não use `-B` ou `--force`.
Crie novos worktrees a partir do checkout principal, evitando diretórios
aninhados dentro do worktree de uma tarefa.

## Trabalhar e verificar

- Leia o `AGENTS.md` do checkout e mantenha commits restritos à tarefa.
- Use uma `.venv` própria; não compartilhe a pasta de outro checkout.
- Configure o ambiente explicitamente a partir de `.env.example`, sem copiar
  segredos automaticamente. Use banco de testes dedicado; worktrees não isolam
  serviços externos nem variáveis de ambiente herdadas.
- Mantenha caches em `.multilang/` e entregas em `output/` do próprio worktree.
  Revise caminhos absolutos configurados para evitar gravações compartilhadas.
- Se executar servidores simultâneos, use portas distintas. Não execute workers
  contra a mesma fila de produção como efeito da criação de um worktree.
- Execute os testes relevantes à mudança e os checks aplicáveis do README.
  A preparação de vocabulário continua sem autorizar geração de cards ou áudio.

Exemplo de teste offline, substituindo o caminho pelo teste pertinente:

```bash
env -u MULTILANG_DATABASE_URL MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 \
  uv run --no-sync pytest tests/services/test_frequency_decks.py -q
git diff --check
git diff
git add caminho/do/arquivo
git commit -m "feat: descreve a mudança"
```

Antes de integrar, atualize a branch da tarefa com a base revisada, resolva
conflitos e repita os checks afetados. Prefira merge da base em branches já
compartilhadas; não reescreva o histórico de outros colaboradores.

## Integração e versões

Use Conventional Commits em todos os novos commits, incluindo merges
(`chore(merge): ...`), e nos títulos de PRs. Abra PRs com o destino da tabela. Descreva o problema resolvido e a validação
executada. Prefira merge commits para preservar a relação entre branches.
Se a integração for local, execute no worktree limpo da branch de destino:

```bash
# No worktree de develop, após revisão e checks:
git merge --no-ff feature/minha-tarefa -m "chore(merge): integra feature/minha-tarefa"
```

Não troque a branch de outro worktree para executar esse comando. Caso precise
de um checkout de integração, crie-o na raiz principal com
`git worktree add .worktrees/develop develop`, apenas se `develop` ainda não
estiver ativa em outro diretório.

Para preparar uma versão, crie `release/1.2.0` a partir de `develop`, usando
`git worktree add -b release/1.2.0 .worktrees/release-1.2.0 develop`. Ajuste a
versão conforme o projeto, estabilize e valide. Integre a release em `main`
com merge commit e marque **o commit resultante em `main`** com
`git tag -a v1.2.0 -m "Release 1.2.0"`. Depois integre a mesma release em
`develop`, preservando as correções de estabilização.

Para uma urgência em produção, crie `hotfix/<slug>` a partir de `main` em um
worktree próprio. Valide, integre em `main`, crie uma nova tag de correção e
integre o hotfix também em `develop`. Se houver uma release aberta, incorpore
nela a correção antes de finalizá-la. Não mova tags já publicadas.

Publicar branches/tags e fazer deploy são ações distintas da integração local.
Não faça push automático de todas as branches ou tags do repositório.

## Encerrar um worktree

Depois da integração, inspecione o diretório da tarefa:

```bash
git -C .worktrees/feature-minha-tarefa status --short
git -C .worktrees/feature-minha-tarefa status --short --ignored
git merge-base --is-ancestor feature/minha-tarefa develop
```

O último comando deve retornar código zero para confirmar a integração por
ancestralidade. Preserve entregas, arquivos não rastreados e dados ignorados
úteis antes da remoção: um worktree pode ter status limpo e conter relatórios,
áudio ou bancos ignorados. A remoção pode apagar esses arquivos.

Somente depois dessa verificação, a partir do checkout principal:

```bash
git worktree remove .worktrees/feature-minha-tarefa
git -C .worktrees/develop branch -d feature/minha-tarefa
```

O segundo comando pressupõe o worktree de `develop` criado acima; use o caminho
real indicado por `git worktree list`. Para releases e hotfixes, confirme a
ancestralidade tanto em `main` quanto em `develop` antes de remover a branch.
Se `branch -d` recusar, investigue; não substitua por `-D` automaticamente.

Use `git worktree prune --dry-run` para inspecionar registros de diretórios que
já não existem. Execute `git worktree prune` apenas depois de confirmar que
não são diretórios temporariamente indisponíveis. Não remova worktrees de
outras tarefas ou colaboradores como parte da limpeza da sua tarefa.
