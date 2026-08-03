# Quick Task 038: Criar Terceiro Deck Teste Alemao

## Objective

Criar um terceiro deck Anki de teste em alemao, separado dos decks anteriores, sem alterar codigo de produto.

## Context

- Decks anteriores foram gerados em `.multilang/exports/german-test/` e `.multilang/exports/german-test-2/`.
- Este deck deve usar `.multilang/exports/german-test-3/` para evitar sobrescrita.
- O artefato deve ser offline, com audio e imagem vazios, sem depender de `.env` ou providers externos.

## Tasks

### Task 1: Gerar o terceiro deck local

<files>

- `.multilang/exports/german-test-3/german-test-3.apkg`
- `.multilang/exports/german-test-3/german-test-3.tsv`

</files>

<action>

Rodar um pequeno script Python via `uv run python -c` usando `genanki` para criar um deck `Multilang German Test 3` com 3 notas em alemao, campos compativeis com o contrato normal de frequencia e audio/imagem vazios.

</action>

<verify>

- `test -s .multilang/exports/german-test-3/german-test-3.apkg`
- `test -s .multilang/exports/german-test-3/german-test-3.tsv`

</verify>

### Task 2: Inspecionar o pacote gerado

<files>

- `.multilang/exports/german-test-3/german-test-3.apkg`

</files>

<action>

Abrir o `.apkg` como zip/SQLite e confirmar que ha 3 notas, modelo `Multilang::Card`, campos esperados e deck `Multilang German Test 3`.

</action>

<verify>

- `uv run python -c "<inspect generated apkg>"`

</verify>

### Task 3: Registrar resumo e verificacao

<files>

- `.planning/quick/038-criar-terceiro-deck-teste-alemao/038-SUMMARY.md`
- `.planning/quick/038-criar-terceiro-deck-teste-alemao/038-VERIFICATION.md`
- `.planning/quick/LOG.md`

</files>

<action>

Persistir o resumo, a verificacao objetiva e adicionar uma linha ao log de quick tasks.

</action>

<verify>

- `test -f .planning/quick/038-criar-terceiro-deck-teste-alemao/038-SUMMARY.md`
- `test -f .planning/quick/038-criar-terceiro-deck-teste-alemao/038-VERIFICATION.md`

</verify>

## No UI Proof Rationale

Esta tarefa gera um artefato Anki local, sem interface web/renderizacao de UI do produto.
