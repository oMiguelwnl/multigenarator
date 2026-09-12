# Banco de dados

A aplicação mantém SQLAlchemy 2 e Alembic. PostgreSQL é o destino de produção;
SQLite continua útil em desenvolvimento e ensaios. Não existe segundo banco
operacional para a arquitetura nativa.

A revisão linear `20260912_20`, filha de `20260828_19`, acrescenta 18 tabelas:

| Grupo | Tabelas |
|---|---|
| Perfis e identidades | `language_profiles`, `lexical_identities`, `lexical_identity_revisions` |
| Morfologia | `surface_forms`, `surface_form_revisions` |
| Datasets | `dataset_versions`, `dataset_memberships`, `dataset_form_memberships`, `dataset_heads` |
| Conteúdo e mídia | `content_versions`, `audio_versions`, `deck_editions` |
| Privacidade | `user_state` |
| Operação | `audit_log`, `domain_events`, `legacy_identity_aliases`, `migration_journal`, `native_tasks` |

Os nomes DDL e colunas são validados pela suite de paridade.
A revisão congela operações `create_table/create_index`;
não chama `metadata.create_all` em produção.

Identidade e forma mantêm uma projeção atual e um histórico imutável.
Memberships fixam os hashes das revisões. Edições fixam as versões geradas e
seus hashes. Atualizar uma fonte não altera os dados de uma edição anterior.
Mover o head de um dataset é uma operação separada e auditada; o rollback de
edição move o head para uma versão existente.

Writes do repositório fazem flush. A transação do chamador reúne mudança,
auditoria e outbox. Alterações de revisão/head usam compare-and-swap; a fila
usa lease/fencing. Cada request/worker tem sua própria sessão. Não compartilhe
Session entre threads.

Eventos contêm apenas identificadores e hashes. Payloads de jobs e estado do
usuário podem ser privados: o banco e seus backups precisam de acesso restrito.
A API projeta apenas status e metadados permitidos, sem expor esses payloads.

O startup legado continua no schema 19. A revisão 20 não deve ser executada com
um `alembic upgrade head` não autorizado. Siga [migração](migration.md).
