# ADR 0001 — Evolução nativa no pacote existente

Data: 2026-09-12. Estado: implementada, ativação de produção condicionada à evidência.

## Contexto

`info1.md` e `info2.md` exigem independência operacional de GSDD e preservação
da arquitetura existente. O pacote já possui Python, Pydantic, SQLAlchemy,
Alembic, Typer, providers de texto/áudio e genanki.

## Decisão

Acrescentar contratos em `domain`, serviços em `services`, persistência em
`repositories`/`db` e composição em `native_runtime`. FastAPI é apenas um
adapter. A fila SQLAlchemy e a busca SQL reutilizam infraestrutura existente;
Redis/RQ e Meilisearch ficam adiados até medições indicarem necessidade.

Eventos e audit log são transacionais. Dados gerados e privados não são donos
da identidade lexical. Feature flags e capacidades desabilitadas permitem
evolução gradual. OpenTelemetry, MkDocs, CI e Dependabot cobrem capacidades
ausentes sem substituir o stack existente.

## Consequências

Workers operam com entrega pelo menos uma vez. Índices SQL e cache local têm
limites conhecidos; cargas maiores podem exigir adapters especializados.
Fixtures não habilitam idiomas nem aprovam redistribuição. A aplicação não
depende de planos executáveis em `.planning`.
