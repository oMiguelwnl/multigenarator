"""Offline multilingual review preparation, with explicit artifact hashes."""

from pathlib import Path


def register_language_commands(cli):
    from multilang.services.qualification_machine_languages import (
        LanguageExpansionRequest,
        build_machine_language_expansion,
        export_machine_language_expansion,
    )
    from multilang.services.qualification_machine_runner import read_json
    from multilang.vocabulary_cli import _guard, _print

    @cli.command("prepare-languages")
    @_guard
    def prepare_languages(configuration: Path, configuration_sha256: str, output: Path):
        request = LanguageExpansionRequest.model_validate(
            read_json(configuration, configuration_sha256)
        )
        expansion = build_machine_language_expansion(request)
        _print(export_machine_language_expansion(expansion, output))

    @cli.command("review-languages")
    @_guard
    def review_languages(configuration: Path, configuration_sha256: str, output: Path):
        from multilang.services.qualification_language_reviews import (
            LanguageReviewsInput,
            export_language_reviews,
        )

        request = LanguageReviewsInput.model_validate(
            read_json(configuration, configuration_sha256)
        )
        _print(export_language_reviews(request, output))
