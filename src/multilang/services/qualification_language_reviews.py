"""Replay language review results against their prepared packets, without granting authority."""

from collections import Counter
from html import escape
from pathlib import Path

from pydantic import Field

from multilang.domain.language_profiles import NativeContract
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine import (
    MachineQualificationResult,
    MachineReviewRequest,
)
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact, read_json
from multilang.services.qualification_pipeline import ArtifactReference


class LanguageReviewsInput(NativeContract):
    requests: tuple[ArtifactReference, ...] = Field(min_length=1, max_length=22)
    results: tuple[ArtifactReference, ...] = Field(default=(), max_length=22)


def build_language_reviews(configuration: LanguageReviewsInput) -> dict:
    """Accept changed executor identities only when the complete source packet is unchanged.

    The result contract replays both actors, exact citations and consensus. Missing
    languages remain visible; a rejection or abstention is never an accepted card.
    Input file hashes are retained so a report can be reproduced after restart.
    """
    configuration = LanguageReviewsInput.model_validate(configuration.model_dump(mode="json"))
    requests, results = {}, {}
    total_bytes = sum(
        reference.path.stat().st_size
        for reference in (*configuration.requests, *configuration.results)
    )
    if total_bytes > 128 * 1024**2:
        raise ValueError("aggregate language review input exceeds byte limit")
    for reference in configuration.requests:
        request = MachineReviewRequest.model_validate(read_json(reference.path, reference.sha256))
        language = request.packet.language.value
        if language == "la" or language in requests:
            raise ValueError("duplicate or unsupported language request")
        if request.phase != "proposal" or any(
            item.kind != "lexical" for item in request.packet.items
        ):
            raise ValueError("language review requires prepared lexical proposal packets")
        requests[language] = request
    for reference in configuration.results:
        result = MachineQualificationResult.model_validate(
            read_json(reference.path, reference.sha256)
        )
        language = result.packet.language.value
        if language not in requests or language in results:
            raise ValueError("duplicate or unrequested language result")
        if result.packet != requests[language].packet:
            raise ValueError("language result does not bind the complete prepared packet")
        results[language] = result
    rows, all_counts, reviewed = [], Counter(), 0
    for language, request in requests.items():
        result = results.get(language)
        outcomes = {item.item_id: item for item in result.decisions} if result else {}
        reviewed_ids = (
            {item.item_id for item in result.proposal.response.decisions}
            & {item.item_id for item in result.judgment.response.decisions}
            if result
            else set()
        )
        items = []
        for item in request.packet.items:
            outcome = outcomes.get(item.item_id)
            decision = (
                outcome.decision if outcome and outcome.status == "machine_agreement" else None
            )
            items.append(
                {
                    "item_id": item.item_id,
                    "item_sha256": item.item_sha256,
                    "lemma": decision.proposed_lemma if decision else item.lemma,
                    "pos": decision.proposed_pos if decision else item.pos,
                    "original_lemma": item.lemma,
                    "original_pos": item.pos,
                    "sense_id": decision.proposed_sense_id if decision else None,
                    "gloss": decision.proposed_gloss if decision else None,
                    "reviewed": item.item_id in reviewed_ids,
                    "status": outcome.status if outcome else "awaiting_review",
                    "reason_codes": list(outcome.reason_codes)
                    if outcome
                    else ["review_not_supplied"],
                }
            )
        counts = Counter(item["status"] for item in items)
        all_counts.update(counts)
        reviewed += len(reviewed_ids)
        rows.append(
            {
                "language": language,
                "request_sha256": request.request_sha256,
                "packet_sha256": request.packet.packet_sha256,
                "result_sha256": result.result_sha256 if result else None,
                "counts": dict(sorted(counts.items())),
                "items": items,
            }
        )
    return {
        "schema_version": "machine-language-reviews-1",
        "inputs": configuration.model_dump(mode="json"),
        "languages": rows,
        "prepared_items": sum(len(row["items"]) for row in rows),
        "reviewed_items": reviewed,
        "counts": dict(sorted(all_counts.items())),
        "origin": "machine",
        "qualified": False,
        "production_eligible": False,
        "redistribution_approved": False,
        "provider_calls_executed": 0,
        "scope": "Lexical review evidence only; pronunciation, frequency, content, audio and production qualification are separate.",
    }


def export_language_reviews(configuration: LanguageReviewsInput, output: Path) -> dict:
    report = build_language_reviews(configuration)
    body = [
        "<!doctype html><meta charset=utf-8><title>Revisão dos idiomas</title>",
        "<h1>Revisão lexical dos idiomas</h1>",
        "<p>Evidências de revisão por IA. Não representam decks completos ou aprovação de produção.</p>",
    ]
    for language in report["languages"]:
        body.append(
            "<h2>" + escape(language["language"]) + "</h2><table><thead><tr>"
            "<th>Palavra</th><th>Classe</th><th>Resultado</th><th>Motivo</th></tr></thead><tbody>"
        )
        for item in language["items"]:
            cells = (item["lemma"], item["pos"], item["status"], ", ".join(item["reason_codes"]))
            body.append(
                "<tr>" + "".join("<td>" + escape(cell) + "</td>" for cell in cells) + "</tr>"
            )
        body.append("</tbody></table>")
    return persist_artifact(
        output,
        kind="machine-language-reviews",
        binding=canonical_sha256(report),
        files={"report.json": json_bytes(report), "report.html": "\n".join(body).encode()},
    )
