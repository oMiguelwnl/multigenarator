# Quick Task 036: Criar Outro Deck Teste Alemao

## Objective

Criar um segundo deck Anki de teste em alemao, separado do deck anterior, sem alterar codigo de produto.

## Context

- O deck anterior foi gerado em `.multilang/exports/german-test/`.
- Este deck deve usar um novo caminho para evitar sobrescrita: `.multilang/exports/german-test-2/`.
- O artefato deve ser offline, com audio e imagem vazios, sem depender de `.env` ou providers externos.

## Tasks

### Task 1: Gerar o segundo deck local

<files>

- `.multilang/exports/german-test-2/german-test-2.apkg`
- `.multilang/exports/german-test-2/german-test-2.tsv`

</files>

<action>

Rodar um pequeno script Python via `uv run python -c` usando `genanki` para criar um deck `Multilang German Test 2` com 3 notas em alemao, campos compativeis com o contrato normal de frequencia e audio/imagem vazios.

</action>

<verify>

- `test -s .multilang/exports/german-test-2/german-test-2.apkg`
- `test -s .multilang/exports/german-test-2/german-test-2.tsv`

</verify>

### Task 2: Inspecionar o pacote gerado

<files>

- `.multilang/exports/german-test-2/german-test-2.apkg`

</files>

<action>

Abrir o `.apkg` como zip/SQLite e confirmar que ha 3 notas, modelo `Multilang::Card`, campos esperados e deck `Multilang German Test 2`.

</action>

<verify>

- `uv run python -c "<inspect generated apkg>"`

</verify>

### Task 3: Registrar resumo e verificacao

<files>

- `.planning/quick/036-criar-outro-deck-teste-alemao/036-SUMMARY.md`
- `.planning/quick/036-criar-outro-deck-teste-alemao/036-VERIFICATION.md`
- `.planning/quick/LOG.md`

</files>

<action>

Persistir o resumo, a verificacao objetiva e adicionar uma linha ao log de quick tasks.

</action>

<verify>

- `test -f .planning/quick/036-criar-outro-deck-teste-alemao/036-SUMMARY.md`
- `test -f .planning/quick/036-criar-outro-deck-teste-alemao/036-VERIFICATION.md`

</verify>

## No UI Proof Rationale

Esta tarefa gera um artefato Anki local, sem interface web/renderizacao de UI do produto.
