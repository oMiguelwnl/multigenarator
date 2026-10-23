# Contribuir com o Multilang

Consulte o [fluxo Gitflow com worktrees](docs/gitflow-worktrees.md).

- `main`: base estável escolhida a partir da Monarch local.
- `develop`: integração de melhorias concluídas.
- `feature/*`: trabalho isolado, um worktree por tarefa.
- `release/*`: estabilização; integrar em main e develop.
- `hotfix/*`: correção de produção; integrar em main e develop.

A feature `feature/roadmap-4-0-native-architecture` continua em execução e
permanece separada das branches permanentes. A Monarch legada é preservada.
