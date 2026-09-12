# Roadmap 4 native implementation plan

**Goal:** implementar os mecanismos solicitados nos dois arquivos, integrados ao
Multilang, preservando dados e comportamento legado.

**Architecture:** contratos Pydantic imutáveis, serviços explícitos, repositórios
SQLAlchemy transacionais e adapters CLI/HTTP/worker. Feature flag e evidências
versionadas controlam a ativação. GSDD não é usado.

**Spec:** `info1.md`, `info2.md`, `docs/multilingual-lexical-adaptive-plan-v4.md`.

## Sequência e ownership

1. Domínio: `domain/language_profiles.py`, `domain/lexical_identity.py`,
   `domain/ranking.py`, `services/language_profiles.py`, `services/ranking.py`,
   `services/lexical_pipeline.py`. Perfis, identidade, formas, MWE, ranking e
   validação com testes de determinismo, ambiguidade e limites.
2. Áudio/conteúdo/Anki: contratos e serviços em arquivos próprios dentro de
   `domain`/`services`; assinatura completa, schemas fechados, edições canônicas,
   protótipos A/B, histórico read-only e fila adaptativa com pré-requisitos.
   Testar preservação de GUID, áudio contextual, escaping, isolamento e ZIP hostil.
3. Persistência e integração: `db/native_models.py`, migration Alembic linear,
   `repositories/native_repository.py`, eventos/audit, imports, busca/cache,
   plugins, validações e snapshot/preview/apply/rollback. Testar atomicidade,
   versões imutáveis, isolamento privado, drift, upgrade/downgrade e restore.
4. Interfaces/infraestrutura: `api.py`, `native_cli.py`, `jobs/`, configuração,
   segurança, observabilidade, CI e build. Interfaces consomem os mesmos
   contratos/repositórios, sem copiar regras de domínio. Testar flag, autenticação,
   papéis, limites, ownership, leases/retries, OpenAPI e CLI.
5. Integração final: exercer import -> rank -> persist -> enrich -> audio ->
   projection/export -> history -> adaptive; revisar os limites entre módulos.
   Executar suite existente, novos testes, lint, build e validação de migrations.
6. Documentação/entrega: README, arquitetura, domínio, banco/API/migração, ADRs e
   `ROADMAP_4_NATIVE_IMPLEMENTATION.md`, com matriz de cada requisito, comandos,
   evidências e bloqueios externos explícitos. Commits por domínio, somente
   arquivos da tarefa; sem incluir alterações anteriores do usuário.

Cada implementação começa por testes que expõem o comportamento faltante;
falhas são reproduzidas antes da correção. Integrações são verificadas antes dos
commits. Nenhum teste estrutural é tratado como aceite real dos clientes Anki.
