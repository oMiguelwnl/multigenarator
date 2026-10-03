# Seleção de vocabulário: arquivo e banco

A seleção de todos os idiomas pode ser salva como uma fotografia versionada, sem
iniciar geração. O exportador inclui todos os idiomas presentes no plano, mesmo
quando ainda existem revisões pendentes. Latim permanece identificado como `la`.

A entrega de 03/10/2026 fica em
`output/reports/vocabulary-selection/20261003-01/`. O arquivo
`selecao-vocabulario-todos-idiomas.zip` é a cópia portátil para guardar. Consulte
`README.md`, `snapshot/languages.json` e o recibo `database-receipt.json` para os
totais capturados e a confirmação de gravação.

## Conteúdo

- `snapshot/inventory/<idioma>.jsonl`: todas as unidades, evidência lexical,
  decisão importada, formas, sentidos e origem.
- `snapshot/selected/<idioma>.jsonl`: unidades com decisão efetiva `include`.
- `snapshot/attachments/`: decisões derivadas, metadados e vínculos de anotação
  explicitamente incorporados.
- `snapshot/manifest.json`: identificador imutável, hashes, contagens e intervalo
  de captura.

Uma unidade incluída não aprova todos os sentidos do verbete. Na revisão original,
use `selected_candidate_ids` e `selected_forms`; em `resolved_content`, use somente
os candidatos/formas retidos e suas restrições. `uncertain`, `quarantined` e
`unreviewed` nunca são promovidos automaticamente. As contagens são de unidades
de revisão, não de cartões nem de cobertura lexical.

As sessões são lidas sob seus próprios locks e as decisões são verificadas contra
os pedidos e pacotes originais. A captura é sequencial, não um instante atômico de
todos os terminais. Novas importações após a captura exigem outra versão; elas não
alteram o arquivo salvo. Não se toma uma decisão nova com base em frequência ou
em heurísticas durante a exportação.

O parâmetro opcional `--nordic-version` incorpora a versão derivada de da/nb/sv,
incluindo correções, seis adições e metadados de identidades derivadas. O vínculo
com a revisão histórica precisa coincidir. Se outra sessão já tiver substituído
essa revisão, as duas versões são preservadas como conflito pendente.

## Comandos

A partir da raiz do projeto:

```bash
uv run python scripts/save_vocabulary_selection.py export \
  --plan output/reports/vocabulary-qualification/session-plan-20260926 \
  --plan-sha256 a8b0e2ab9bbe6593ede96946c1a3bbbc44151da17efdabd77e1e1e25e12edac8 \
  --work output/reports/vocabulary-qualification/session-work \
  --nordic-version output/reports/vocabulary-qualification/reservation-da-nb-sv-20260926/focused-repair-20261003/VERSION.json \
  --output output/reports/vocabulary-selection/NOVA-VERSAO/snapshot

uv run python scripts/save_vocabulary_selection.py bundle \
  --snapshot output/reports/vocabulary-selection/NOVA-VERSAO/snapshot \
  --archive output/reports/vocabulary-selection/NOVA-VERSAO/selecao-vocabulario-todos-idiomas.zip \
  --receipt output/reports/vocabulary-selection/NOVA-VERSAO/archive-receipt.json

uv run python scripts/save_vocabulary_selection.py persist \
  --snapshot output/reports/vocabulary-selection/NOVA-VERSAO/snapshot \
  --receipt output/reports/vocabulary-selection/NOVA-VERSAO/database-receipt.json

uv run python scripts/save_vocabulary_selection.py verify \
  --snapshot output/reports/vocabulary-selection/NOVA-VERSAO/snapshot \
  --receipt output/reports/vocabulary-selection/NOVA-VERSAO/database-check.json
```

Os comandos recusam sobrescrever a exportação ou um recibo. `persist` usa
`Settings.database_url` (`MULTILANG_DATABASE_URL`), grava numa transação e verifica
todos os payloads após a gravação. Reimportar a mesma fotografia é idempotente;
use um destino novo para o recibo. `verify` compara o banco com os arquivos.
Nenhum comando constrói clientes de geração, traduz ou sintetiza áudio.

Se a conexão estiver em `.env`, execute `persist` e `verify` sem definir
`MULTILANG_FORBID_PROVIDERS` ou `MULTILANG_FORBID_NETWORK`: essas variáveis fazem
`Settings` ignorar esse arquivo. Isso não habilita geração nestes comandos, que
apenas importam e verificam dados. Para manter essas variáveis no ambiente,
forneça `MULTILANG_DATABASE_URL` explicitamente por um mecanismo seguro.

## Banco de dados

As tabelas ficam no PostgreSQL configurado para o projeto:

- `vocabulary_selection_snapshots`: manifesto e contagem de cada versão.
- `vocabulary_selection_units`: registros completos, indexados por versão,
  idioma e decisão; cada payload tem SHA-256.

O schema de preparação possui histórico Alembic próprio em
`src/multilang/db/selection_migrations/`, registrado na tabela
`vocabulary_selection_schema_version`. A migração aditiva cria apenas essas
estruturas; não executa as migrações de ativação nativa nem altera tabelas de
cards, datasets de produção ou filas existentes. O script `persist` aplica essa
migração explicitamente. SQLite é usado apenas nos testes.

As inserções são parametrizadas e feitas em lotes. A versão só fica visível após
commit integral; um erro reverte toda a importação. Fotografias antigas são
preservadas. A geração continua bloqueada pelo estado `production_eligible=false`
e pela instrução do usuário, independentemente da existência dos registros.

Para consultar os totais de uma versão:

```sql
SELECT language, decision, count(*) AS units
FROM vocabulary_selection_units
WHERE snapshot_id = :snapshot_id
GROUP BY language, decision
ORDER BY language, decision;
```
