"""Machine corrections remain replayable projections of exact source occurrences."""

import importlib

import pytest
from test_qualification_machine import accept
from test_qualification_machine_sources import reference

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import (
    ContextualAnalysis,
    ContextualToken,
    sentence_hash,
)
from multilang.services.qualification_observations import ObservationLimits, _observe


def api():
    return importlib.import_module("multilang.services.qualification_machine_observation_revision")


def digest(value):
    return canonical_sha256(value.model_dump(mode="json", exclude_computed_fields=True))


@pytest.fixture
def observation():
    sentences = ("apoio aberto", "boa compra", "boa parte")

    class Analyzer:
        def analyze(self, language, text):
            tokens, offset = [], 0
            base = dict(sentence_sha256=sentence_hash(text), model_fingerprint="e" * 64)
            for word in text.split():
                lemma, pos = {
                    "aberto": ("abrir", "VERB"),
                    "boa": ("bom", "ADJ"),
                }.get(word, (word, "NOUN"))
                tokens.append(
                    ContextualToken(
                        text=word,
                        lemma=lemma,
                        pos=pos,
                        start=offset,
                        end=offset + len(word),
                        features=(("VerbForm", "Part"),) if word == "aberto" else (),
                        **base,
                    )
                )
                offset += len(word) + 1
            return ContextualAnalysis(
                language=language, status="complete", reason="fixture", tokens=tuple(tokens), **base
            )

    return _observe(
        ((f"doc-{i}", f"s-{i}", None, None, text) for i, text in enumerate(sentences)),
        language=SupportedLanguage.PT,
        source_sha256="a" * 64,
        split="calibration",
        analyzer=Analyzer(),
        limits=ObservationLimits(),
        document_hashes={f"doc-{i}": sentence_hash(text) for i, text in enumerate(sentences)},
        source_scope="UD-train-grammar-only",
        sampling_description="synthetic test fixture",
    )


def plan(observation, **updates):
    values = dict(
        original_sha256=digest(observation),
        revision_id="round-1",
        occurrence_sha256s=tuple(
            digest(row) for row in observation.occurrences if row.text in {"aberto", "boa"}
        ),
        profile_sha256="b" * 64,
        rubric_sha256="c" * 64,
    )
    values.update(updates)
    return api().build_machine_observation_revision(observation, **values)


def qualification(plan, *, change=None, pending=()):
    from multilang.services.qualification_machine import reconcile_machine_reviews

    decisions = []
    for index, item in enumerate(plan.packet.items):
        base = dict(kind="case", item_id=item.item_id, item_sha256=item.item_sha256)
        if index in pending:
            decisions.append(
                dict(
                    **base,
                    decision="inconclusive",
                    reason="Evidence missing",
                    uncertainties=["gap"],
                )
            )
            continue
        token = item.proposal_tokens[0].model_dump(mode="json")
        token["sense_id"] = f"sense-{index}"
        decision = dict(
            **base,
            decision="corrected",
            reason="Fixture evidence review",
            tokens=[token],
            expected_match=True,
            citations=[
                dict(
                    source_index=0,
                    source_sha256=item.sources[0].source_sha256,
                    start=0,
                    end=len(item.text),
                    quote=item.text,
                )
            ],
        )
        if change:
            change(index, decision)
        decisions.append(decision)
    response = {"decisions": decisions}
    proposer = accept(plan.packet, response)
    judge = accept(plan.packet, response, name="judge", context="context-2", proposal=proposer)
    return reconcile_machine_reviews(plan.packet, proposer, judge)


def test_revision_corrects_analysis_without_mutating_original_model_tokens(observation):
    original = observation.model_dump(mode="json")
    request = plan(observation)

    def change(index, decision):
        if index == 0:
            decision["tokens"][0].update(lemma="aberto", pos="ADJ", features={})

    result = api().apply_machine_observation_revision(
        request, qualification(request, change=change)
    )
    assert observation.model_dump(mode="json") == original
    assert result.plan.original.model_dump(mode="json") == original
    assert result.occurrences[1].lemma == "aberto"
    assert result.occurrences[1].pos == "ADJ"
    assert result.occurrences[1].features == {}
    assert result.plan.original.analyses[0].analysis.tokens[1].lemma == "abrir"
    assert result.measurement.effective_token_count == 6
    assert result.origin == "machine" and result.production_eligible is False


def test_sense_split_preserves_two_physical_occurrences_without_double_counting(observation):
    request = plan(observation)
    result = api().apply_machine_observation_revision(request, qualification(request))
    groups = [row for row in result.measurement.measurements if row.text == "boa"]
    assert len(groups) == 2
    assert sum(row.observed_count for row in groups) == 2
    assert result.measurement.effective_token_count == 6


def test_explicit_exclusion_keeps_original_denominator_and_records_reason(observation):
    request = plan(observation)

    def change(index, decision):
        if index == 0:
            decision.update(tokens=[], expected_match=False)

    result = api().apply_machine_observation_revision(
        request, qualification(request, change=change)
    )
    assert len(result.occurrences) == 5
    assert result.measurement.effective_token_count == 6
    assert len(result.excluded_occurrence_sha256s) == 1
    assert result.changes[0].action == "excluded_from_projection"
    assert result.changes[0].reason == "Fixture evidence review"


def test_pending_decision_does_not_silently_modify_or_approve_occurrence(observation):
    request = plan(observation)
    result = api().apply_machine_observation_revision(request, qualification(request, pending=(0,)))
    assert result.occurrences[1] == observation.occurrences[1]
    assert result.blockers[request.packet.items[0].item_id] == "blocked_uncertainty"


@pytest.mark.parametrize("selection", [("f" * 64,), ("duplicate",)])
def test_selection_rejects_foreign_or_duplicate_occurrences(observation, selection):
    if selection == ("duplicate",):
        selection = (digest(observation.occurrences[1]),) * 2
    with pytest.raises(ValueError, match="selection|duplicate|unknown"):
        plan(observation, occurrence_sha256s=selection)


def test_changed_original_denominator_or_hash_is_rejected(observation):
    with pytest.raises(ValueError, match="checksum"):
        plan(observation, original_sha256="0" * 64)
    with pytest.raises(ValueError):
        changed = observation.model_copy(
            update={"context": observation.context.model_copy(update={"token_count": 5})}
        )
        plan(changed)


def test_correction_cannot_replace_another_token_or_duplicate_the_occurrence(observation):
    request = plan(observation)

    def change(index, decision):
        if index == 0:
            decision["tokens"] = [
                dict(start=0, end=5, text="apoio", lemma="apoio", pos="NOUN", sense_id="support")
            ]

    with pytest.raises(ValueError, match="span|occurrence"):
        api().apply_machine_observation_revision(request, qualification(request, change=change))


def test_changed_supplement_is_rejected_when_applying_revision(observation, tmp_path):
    supplemental = reference(tmp_path)
    request = plan(
        observation, supplemental_sources={digest(observation.occurrences[1]): (supplemental,)}
    )
    result = qualification(request)
    supplemental.path.write_text("Modified source")
    with pytest.raises(ValueError, match="checksum"):
        api().apply_machine_observation_revision(request, result)


def test_projection_and_qualification_tampering_fail_on_replay(observation):
    request = plan(observation)
    result = api().apply_machine_observation_revision(request, qualification(request))
    payload = result.model_dump(mode="json", exclude_computed_fields=True)
    payload["occurrences"][1]["lemma"] = "invented"
    with pytest.raises(ValueError, match="projection|replay"):
        api().MachineObservationRevision.model_validate(payload)


def test_duplicate_physical_occurrence_is_not_counted_twice(observation):
    rows = observation.occurrences
    with pytest.raises(ValueError, match="occurrence|context|count|inventory"):
        plan(observation.model_copy(update={"occurrences": (*rows, rows[0])}))


def test_revision_from_another_plan_cannot_be_applied(observation):
    first = plan(observation)
    second = plan(observation, revision_id="round-2")
    with pytest.raises(ValueError, match="packet mismatch"):
        api().apply_machine_observation_revision(first, qualification(second))


def test_case_cannot_expand_one_occurrence_into_two_tokens(observation):
    request = plan(observation)

    def change(index, decision):
        if index == 0:
            decision["tokens"].insert(
                0, dict(start=0, end=5, text="apoio", lemma="apoio", pos="NOUN", sense_id="support")
            )

    with pytest.raises(ValueError, match="one occurrence"):
        api().apply_machine_observation_revision(request, qualification(request, change=change))


def test_unresolved_sense_is_preserved_as_an_explicit_blocker(observation):
    request = plan(observation)

    def change(index, decision):
        if index == 0:
            decision["tokens"][0]["sense_id"] = None

    result = api().apply_machine_observation_revision(
        request, qualification(request, change=change)
    )
    assert result.blockers[request.packet.items[0].item_id] == "sense_unresolved"


def test_stored_revision_replays_without_claiming_files_were_rechecked(observation, tmp_path):
    supplemental = reference(tmp_path)
    request = plan(
        observation, supplemental_sources={digest(observation.occurrences[1]): (supplemental,)}
    )
    result = api().apply_machine_observation_revision(request, qualification(request))
    payload = result.model_dump(mode="json", exclude_computed_fields=True)
    supplemental.path.unlink()
    assert api().MachineObservationRevision.model_validate(payload) == result
    with pytest.raises(OSError):
        api().apply_machine_observation_revision(request, qualification(request))
