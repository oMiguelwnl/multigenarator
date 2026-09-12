# Roadmap 4: análise antes da implementação

Data: 2026-09-12. Branch: `feature/roadmap-4-0-native-architecture`.

## Escopo e baseline

As solicitações de `info1.md` e `info2.md` autorizam a implementação nativa do
Roadmap 4. O contrato detalhado está em
`docs/multilingual-lexical-adaptive-plan-v4.md`. GSDD não participa da execução
nem do runtime. Os arquivos `.planning` e as alterações preexistentes permanecem
preservados. A autorização de implementação não constitui evidência de licença,
qualidade linguística, autorização de gastos ou aceite dos clientes Anki.

O baseline Git é `c13d603`. Há alterações anteriores, inclusive um arquivo
staged em `.planning/phases/33-grammar-and-personal-sources`; os commits desta
implementação devem incluir somente os arquivos desta tarefa.

## Arquitetura atual e impacto

| Estrutura atual | Limitação | Requisito v4 | Evolução natural |
|---|---|---|---|
| `domain/jobs.py`, `domain/source_profiles.py` | Idiomas enumerados, políticas dispersas | LanguageProfile e capabilities | Reutilizar os 22 códigos modernos e `la`; contratos de capacidade versionados |
| `domain/lexicon.py`, `services/lexical_lookup.py`, `repositories/lexical_repository.py` | Identidades geralmente associadas ao job; ambiguidade lexical genérica | Identidade lemma/POS/sense estável | Domínio semântico próprio no mesmo pacote, resolução explícita e aliases do legado |
| `domain/korean.py`, `services/korean_morphology.py` | Modelo forte, específico de coreano | Morfologia multilíngue fail-closed | Preservar Kiwi/NFC e IDs; adapters qualificados, sem fallback por sufixo |
| `services/frequency_decks.py`, `assets/frequency` | Ranking congelado legado, sem observações suficientes para RANK-01 | Ranking auditável por corpus | Motor determinístico com alocações, pesos, dispersão, MWE e manifests |
| `db/models.py`, `repositories/*`, `alembic/versions` | Persistência orientada a jobs, commits por operação | Core/Generated/User, eventos, versões e auditoria | Tabelas adicionais na mesma base, transações e outbox; migração Alembic explícita |
| `services/generate_job.py`, `repositories/job_repository.py` | Execução síncrona, sem lease de worker | Fila durável/retry/status | Fila SQLAlchemy no mesmo banco; handlers dos serviços existentes |
| `services/text_generation.py`, `provider_text_adapters.py` | Conteúdo mutável, sem edição canônica | IA somente enriquece | Contrato fechado e repositório separado de conteúdo versionado |
| `services/audio_synthesis.py`, `repositories/audio_repository.py` | Cache genérico não cobre todo contexto de pronúncia | AudioVersion e assinatura completa | Adapter nativo com provider/model/voz/política/contexto/texto e verificação de bytes |
| `services/export_anki_package.py`, `domain/exporting.py` | GUID inclui job/ordem; variantes de exporter já existem | GUID semântico, formas obrigatórias, subdecks | Projeção e protótipos semânticos, aliases provados, preservar exporter legado |
| `settings.py`, `runtime.py`, `cli.py` | CLI Typer sem API HTTP | API v1/v2, feature flag, segurança | FastAPI como adapter; CLI continua disponível; flag desligada por padrão |
| `services/rate_limit.py`, `provider_retry.py`, `security/redaction.py` | Proteção de provider, sem autenticação HTTP | Papéis, limites e secrets | Reutilizar redaction/retry; autenticação por credencial configurada e RBAC |
| Testes pytest, Hatch, uv | Sem CI/documentação integrada | Lint/build/migrations/deploy/docs | GitHub Actions, Dependabot e MkDocs; testes locais e PostgreSQL em CI |

## Decisões

Continuar com Python 3.12, Pydantic v2, SQLAlchemy, Alembic, Typer e genanki.
A fila persistida no banco e a busca indexada SQL atendem aos requisitos iniciais;
Redis/RQ e Meilisearch não serão dependências redundantes. Interfaces permitem
adapters futuros. FastAPI, OpenTelemetry e MkDocs cobrem capacidades ausentes.

Os contratos entram em `domain`, as operações em `services`, a persistência em
`repositories`/`db`, e as interfaces em CLI/API. Nenhum serviço lê um plano
executável para decidir regras de negócio. Eventos e audit log são gravados na
mesma transação dos fatos que descrevem. Históricos privados não alteram Core.

## Migração e riscos

Migrações nativas são aditivas e não alteram GUIDs/usuários/históricos legados.
O startup legado não deve aplicar silenciosamente a migração nativa. Aplicação
exige prévia, snapshot validado e confirmação vinculada a hashes; mudanças no
baseline invalidam a prévia. Desenvolvimento e ensaios usam bancos descartáveis.

O plano exige uma decisão ANKI-01 com provas de dois modelos em Desktop atual,
Desktop anterior, AnkiDroid e AnkiMobile. Prototipar não significa comprovar
scheduling/burying nesses clientes. Esse requisito é um bloqueio de ativação,
assim como fontes/licenças e avaliação independente dos 22 idiomas. As listas
legadas não serão reclassificadas como 66 mil identidades semanticamente revistas.
Chamadas pagas, redistribuição e migração de uma instalação viva necessitam de
evidência concreta; sua falta será reportada, nunca convertida em sucesso.

## Validação

Registrar baseline pytest antes de implementar; testar contratos e negativos,
transações/concorrência, migração/restore, importação segura, API/RBAC, Anki
round-trip estrutural, determinismo e carga de 3000/66000 identidades sintéticas.
Fixtures sintéticas são evidência de software, não aprovação linguística.
