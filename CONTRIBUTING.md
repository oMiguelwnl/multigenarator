# Contribuir com o Multilang

Consulte o [fluxo Gitflow com worktrees](docs/gitflow-worktrees.md).

- `main`: base estável escolhida a partir da Monarch local.
- `develop`: integração de melhorias concluídas.
- `feature/*`: trabalho isolado, um worktree por tarefa.
- `release/*`: estabilização; integrar em main e develop.
- `hotfix/*`: correção de produção; integrar em main e develop.

A feature `feature/roadmap-4-0-native-architecture` continua em execução e
permanece separada das branches permanentes. A Monarch legada é preservada.

## Mensagens de commit

Todos os novos commits, em todas as branches, seguem
[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
O histórico anterior fica preservado; não reescreva commits antigos para adequá-los.

Formato: `tipo(escopo opcional)!: descrição`. Escopo e `!` são opcionais.
O projeto usa tipos e escopos em minúsculas; a descrição pode ser em português
ou inglês. Use uma descrição concreta e separe o corpo do título por linha vazia.

| Tipo | Uso |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de erro |
| `docs` | Documentação |
| `style` | Formatação do código, sem mudança de comportamento |
| `refactor` | Reorganização sem adicionar funcionalidade ou corrigir erro |
| `perf` | Melhoria de desempenho |
| `test` | Testes |
| `build` | Dependências e empacotamento |
| `ci` | Integração contínua |
| `chore` | Manutenção e integração de branches |
| `revert` | Reversão de mudança |

Exemplos:

```text
feat(vocabulary): adiciona validação de identidade lexical
fix(audio): impede reutilização de áudio incompatível
docs(gitflow): documenta worktrees
chore(merge): integra feature/minha-tarefa
revert: desfaz alteração no cache
feat(api)!: remove o endpoint legado
```

Uma quebra de compatibilidade exige `!` no título ou rodapé
`BREAKING CHANGE: descrição da quebra`. O hook verifica o formato do título
 e a separação do corpo; a revisão verifica o tipo correto e a descrição das
quebras. Não há geração automática de versões ou changelog nesta configuração.

Merges também seguem o padrão, sem a mensagem automática `Merge branch ...`:

```bash
git merge --no-ff feature/minha-tarefa -m "chore(merge): integra feature/minha-tarefa"
```

Use esse formato também no título de PRs, especialmente quando houver squash.
Para reversões, use `git revert --no-commit <commit>` e depois um commit com
`revert: ...`. Não use `--no-verify` para contornar o padrão. Commits temporários
`fixup!`/`squash!` não são aceitos pelo hook; use commits convencionais.

## Validação local em todos os worktrees

O hook `.githooks/commit-msg` usa apenas Python 3 e rejeita mensagens inválidas.
A instalação é por clone. Neste repositório, o caminho absoluto aponta para
`.worktrees/develop/.githooks`, de modo que também cobre branches antigas que
não possuem os arquivos do hook, sem editar seus arquivos ou commits.

Para instalar em outro clone, execute no checkout permanente de `develop`:

```bash
git config --show-origin --get core.hooksPath
# Se já houver hooks próprios, integre-os antes de substituir a configuração.
git config --local core.hooksPath "$(pwd)/.githooks"
python3 -m unittest discover -s tests/tooling -v
```

Mantenha esse checkout disponível. Se mover o clone ou o worktree, atualize o
caminho absoluto. Configuração específica de worktree pode sobrepor a configuração
local; confira `git config --show-origin --get core.hooksPath` em caso de dúvida.
Hooks locais não são transferidos automaticamente pelo clone, não validam
commits antigos recebidos por fetch e não controlam commits feitos pela interface
do GitHub. Checks e proteções no servidor ainda não foram configurados.
