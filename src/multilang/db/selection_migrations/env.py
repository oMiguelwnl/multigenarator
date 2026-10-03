"""Explicit additive migrations for vocabulary selection storage only."""

from alembic import context
from multilang.db.vocabulary_selection_models import SelectionBase

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Selection migrations require an explicit application connection")
context.configure(
    connection=connection,
    target_metadata=SelectionBase.metadata,
    version_table="vocabulary_selection_schema_version",
)
with context.begin_transaction():
    context.run_migrations()
