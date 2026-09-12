"""Wire task types to the same facade used by CLI and HTTP."""

from multilang.jobs.anki_jobs import export_anki_job
from multilang.jobs.audio_jobs import generate_audio_job
from multilang.jobs.import_jobs import import_dataset_job
from multilang.jobs.ranking_jobs import calculate_ranking_job


def build_handlers(settings, *, facade_factory=None):
    if facade_factory is None:
        from multilang.native_runtime import build_native_facade

        facade_factory = build_native_facade

    def bind(operation):
        def run(payload, actor, session):
            return operation(facade_factory(session, settings), payload, actor)

        return run

    return {
        "audio": bind(generate_audio_job),
        "ranking": bind(calculate_ranking_job),
        "import": bind(import_dataset_job),
        "anki": bind(export_anki_job),
        "content": bind(lambda facade, payload, actor: facade.generate_content(payload, actor)),
    }
