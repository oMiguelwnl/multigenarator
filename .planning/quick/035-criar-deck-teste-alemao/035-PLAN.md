# Quick Task 035: Criar Deck Teste Alemao

## Objective

Criar um deck Anki de teste em alemao e deixar um artefato `.apkg` local acessivel para importacao manual, sem alterar codigo de produto.

## Context

- O projeto e CLI-first em Python, com exportacao Anki via `genanki`.
- A geracao moderna completa pode depender de providers externos para audio; `.env` nao deve ser lido nem exposto.
- O diretorio `.multilang/` e arquivos `.apkg` sao gitignored e apropriados para artefatos locais gerados.
- Ha mudancas preexistentes no worktree; esta tarefa nao deve reverte-las nem depender delas.

## Tasks

### Task 1: Gerar o deck de teste local

<files>

- `.multilang/exports/german-test/german-test.apkg`
- `.multilang/exports/german-test/german-test.tsv`

</files>

<action>

Rodar um pequeno script Python via `uv run python -c` usando `genanki` para criar um deck `Multilang German Test` com 3 notas em alemao, campos compativeis com o contrato normal de frequencia (`SortIndex`, `word`, `IPA`, `Definitions`, `Example Sentence`, `Translation`, `word_audio`, `sentence_audio`, `Image`) e audio/imagem vazios para manter o artefato offline.

</action>

<verify>

- `test -f .multilang/exports/german-test/german-test.apkg`
- `test -f .multilang/exports/german-test/german-test.tsv`

</verify>

### Task 2: Inspecionar o pacote gerado

<files>

- `.multilang/exports/german-test/german-test.apkg`

</files>

<action>

Abrir o `.apkg` como zip/SQLite e confirmar que ha 3 notas no pacote, que o modelo contem os campos esperados e que o deck foi gravado com nome de teste alemao.

</action>

<verify>

- `uv run python -c "<inspect generated apkg>"`

</verify>

### Task 3: Registrar resumo e verificacao

<files>

- `.planning/quick/035-criar-deck-teste-alemao/035-SUMMARY.md`
- `.planning/quick/035-criar-deck-teste-alemao/035-VERIFICATION.md`
- `.planning/quick/LOG.md`

</files>

<action>

Persistir o resumo da tarefa, a verificacao objetiva do deck criado e adicionar uma linha ao log de quick tasks.

</action>

<verify>

- `test -f .planning/quick/035-criar-deck-teste-alemao/035-SUMMARY.md`
- `test -f .planning/quick/035-criar-deck-teste-alemao/035-VERIFICATION.md`

</verify>

## No UI Proof Rationale

Esta tarefa gera um artefato Anki local, sem interface web/renderizacao de UI do produto.
