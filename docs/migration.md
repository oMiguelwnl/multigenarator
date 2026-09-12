# Migração, backup e recuperação

A revisão `20260912_20` acrescenta o schema nativo à revisão legada
`20260828_19`. O processo usa o banco existente, preserva suas tabelas e não
reescreve GUIDs de decks já exportados. A implementação foi exercitada em
bancos temporários; nenhuma instalação de produção foi migrada.

## Pré-condições

O caminho de produção exige snapshot validado, ensaio em clone, prévia
vinculada aos hashes atuais, confirmação explícita e decisão ANKI-01 assinada.
A decisão precisa comparar A e B em Desktop atual, Desktop anterior,
AnkiDroid e AnkiMobile, com artefatos reais verificáveis. Sem evidência, a
aplicação é recusada. O flag nativo não substitui essas condições.

Configuração e assets podem entrar no snapshot por um manifest explícito de
arquivos. Inclua somente o necessário: backups podem conter dados privados e
segredos de configuração. Arquivos e manifest são escritos com acesso restrito;
paths relativos, hashes, limites, links simbólicos e drift são verificados.
Banco e mídia precisam estar em estado consistente no momento do snapshot.

## Fluxo de operação

Estes comandos são instruções para o operador, não foram executados contra uma
base de produção. Configure a URL do banco via ambiente/secret manager. Não
passe senhas pela linha de comando. Consulte `native --help` e a ajuda de cada
subcomando para as opções locais de backup, restore e adoção do legado.

```bash
uv run multilang native backup .multilang/backups/before-native
uv run multilang native rehearse-migration \
  .multilang/backups/before-native/manifest.json .multilang/rehearsal.sqlite3
uv run multilang native preview-migration \
  .multilang/backups/before-native/manifest.json \
  --topology topology-reviewed.json --rehearsal rehearsal.json
```

Grave o JSON emitido pelo ensaio em `rehearsal.json` e o da prévia em
`preview.json`. A confirmação é um SHA-256 da prévia; revise o destino,
snapshot, checksum da migration, modelo Anki e resultado do ensaio antes de
usar esse valor:

```bash
uv run multilang native apply-migration preview.json \
  .multilang/backups/before-native/manifest.json \
  topology-reviewed.json rehearsal.json --confirm HASH_DA_PREVIA
```

Qualquer alteração relevante exige outra prévia/confirmação. Reexecução da
mesma aplicação concluída consulta o journal e revalida integridade; não
reexecuta DDL nem duplica auditoria. Mudança não autorizada de schema, índices
ou dados invalida o processo. Não use `alembic upgrade head` como atalho.

## SQLite legado sem Alembic

Algumas instalações antigas criavam tabelas por SQLAlchemy `create_all`.
`MigrationService.adoption_preview()` compara o schema inteiro com o baseline
legado esperado. `adopt_legacy_schema()` aceita somente esse caso, com snapshot
e confirmação de hash, e adiciona o stamp 19 sem modificar linhas existentes.
Schema divergente precisa ser reconciliado explicitamente. Depois do stamp,
crie outro snapshot: o fingerprint mudou.

## Clone, restore e rollback

SQLite usa a API de backup do SQLite e valida integridade e fingerprint lógico.
PostgreSQL usa `pg_dump`/`pg_restore`, com credenciais fora do argv. O ensaio
PostgreSQL recebe uma engine de destino vazia e isolada por
`MigrationService.rehearse(..., clone_engine=...)`; não deve restaurar sobre a
origem. Os programas `pg_dump`/`pg_restore` precisam estar instalados.

`BackupService.restore_to()` recusa origem/destino iguais e destino populado;
verifica também os assets selecionados. O ensaio aplica a revisão nativa,
confere preservação do legado, volta à revisão 19 e compara com o snapshot.

`MigrationService.rollback_preview()` e `rollback()` exigem o journal concluído,
o backup original, integridade atual e confirmação vinculada ao estado. Se
existirem novos dados após a migração, o rollback destrutivo é recusado. Nesse
caso, reconciliar/exportar os dados novos é necessário; não há descarte
silencioso. Rollback de uma edição de dataset é diferente: move seu head para
uma versão imutável anterior sem apagar as versões intermediárias.

## Aliases e histórico

`LegacyIdentityAdapter` recebe candidatos e evidência explícita de mapeamento
um a um. Identidade inconclusiva, merge, split, duplicidade e conflito ficam
pendentes. Seu preview não altera o legado. A aplicação confirmada preserva o
GUID original e registra o vínculo sem inventar mapeamento de cards.

Importar histórico requer provas separadas de note GUID, modelo, ordinal do
template e card semântico. `NativeLearningService` lê o APKG com limites e
somente leitura, guarda fatos mínimos por usuário e permite revogação/reset.
Não importa scheduling para o Core nem grava no APKG de origem.

## Retomada segura

Mantenha `MULTILANG_ROADMAP_4_ENABLED=false` enquanto faltar qualquer prova.
Cadastre perfis com capabilities/policies e receipts válidos; importe e revise
datasets; gere conteúdo/áudio com limites de custo; aprove versões e congele a
edição completa antes de exportar produção. Não reclassifique listas legadas
wordfreq nem fixtures sintéticas como identidades linguisticamente aprovadas.
