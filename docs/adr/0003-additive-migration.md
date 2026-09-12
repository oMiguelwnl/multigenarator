# ADR 0003 — Migração aditiva, explícita e verificável

Data: 2026-09-12. Estado: implementada para ensaio e aplicação controlada.

## Decisão

Preservar as revisões Alembic existentes e acrescentar uma revisão linear com
DDL congelado. Não aplicar a revisão nativa no startup legado. Snapshot,
verificação, clone, prévia e confirmação por hash precedem qualquer aplicação.
Uma decisão Anki assinada é obrigatória na aplicação controlada.

Backups podem incluir configuração e assets explicitamente selecionados, com
paths relativos, limites e hashes. Restore escreve em destino isolado. O
rollback de schema recusa descartar dados escritos depois da migração; nesse
caso é necessário reconciliar dados e criar outra estratégia de restauração.

## Consequências

Instalações SQLite antigas criadas com `create_all` precisam provar paridade
exata antes de receber o stamp legado. Não há migração automática de aliases
ambíguos. Uma instalação de produção não foi alterada nesta implementação.
