"""Deterministic corpus ranking with explicit allocation and MWE accounting."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from multilang.domain.lexical_identity import canonical_sha256
from multilang.domain.ranking import (
    CorpusContribution,
    CorpusManifest,
    CorpusObservation,
    QuarantinedOccurrence,
    RankingEntry,
    RankingPolicy,
    RankingResult,
)


class RankingEngine:
    def __init__(
        self, *, max_observations: int = 1_000_000, max_corpora: int = 128
    ) -> None:
        if max_observations < 1 or max_corpora < 1:
            raise ValueError("ranking limits must be positive")
        self.max_observations = max_observations
        self.max_corpora = max_corpora

    def calculate(
        self,
        *,
        corpora: Iterable[CorpusManifest],
        observations: Iterable[CorpusObservation],
        policy: RankingPolicy,
    ) -> RankingResult:
        corpus_rows = tuple(
            sorted(
                self._bounded(corpora, self.max_corpora, "corpus"),
                key=lambda item: item.corpus_id,
            )
        )
        rows = tuple(
            sorted(
                self._bounded(observations, self.max_observations, "observation"),
                key=lambda item: (item.corpus_id, item.document_id, item.occurrence_id),
            )
        )
        if not corpus_rows or len({item.corpus_id for item in corpus_rows}) != len(
            corpus_rows
        ):
            raise ValueError("ranking requires unique corpus manifests")
        if len({item.language for item in corpus_rows}) != 1:
            raise ValueError("rank each language independently")
        if any(item.held_out for item in corpus_rows):
            raise ValueError("held-out corpora cannot contribute to canonical ranking")
        if sum((item.weight for item in corpus_rows), Decimal(0)) != Decimal(1):
            raise ValueError("corpus weights must sum exactly to 1")
        by_corpus = {item.corpus_id: item for item in corpus_rows}
        occurrence_keys = [(item.corpus_id, item.occurrence_id) for item in rows]
        if len(occurrence_keys) != len(set(occurrence_keys)):
            raise ValueError("duplicate corpus occurrence ID")
        documents: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            if row.corpus_id not in by_corpus:
                raise ValueError("observation references an unknown corpus")
            if row.counting_channel not in policy.allowed_counting_channels:
                raise ValueError("observation uses an unapproved counting channel")
            documents[row.corpus_id].add(row.document_id)
        if any(
            len(ids) > by_corpus[corpus_id].document_count
            for corpus_id, ids in documents.items()
        ):
            raise ValueError("observed document count exceeds corpus denominator")

        accepted, suppressed, quarantine = self._deduplicate_spans(rows)
        counts: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        identity_docs: dict[tuple[str, str], set[str]] = defaultdict(set)
        identity_occurrences: dict[tuple[str, str], list[str]] = defaultdict(list)
        confidence_counts: dict[str, Decimal] = defaultdict(Decimal)
        channel_counts: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        with localcontext() as context:
            context.prec = policy.intermediate_precision
            context.rounding = ROUND_HALF_EVEN
            for row in accepted:
                reason = (
                    "unresolved_allocation"
                    if not row.allocations
                    else (
                        "allocation_confidence_below_threshold"
                        if any(
                            item.confidence < policy.confidence_threshold
                            for item in row.allocations
                        )
                        else None
                    )
                )
                if reason:
                    quarantine.append(
                        QuarantinedOccurrence(
                            corpus_id=row.corpus_id,
                            occurrence_id=row.occurrence_id,
                            reason=reason,
                        )
                    )
                    continue
                channel_counts[(row.corpus_id, row.counting_channel)] += (
                    row.occurrence_count
                )
                for allocation in sorted(
                    row.allocations, key=lambda item: item.lexical_identity_id
                ):
                    key = (row.corpus_id, allocation.lexical_identity_id)
                    allocated = row.occurrence_count * allocation.share
                    counts[key] += allocated
                    confidence_counts[allocation.lexical_identity_id] += (
                        allocated * allocation.confidence
                    )
                    identity_docs[key].add(row.document_id)
                    identity_occurrences[key].append(row.occurrence_id)
            if any(
                count > by_corpus[corpus_id].token_count
                for (corpus_id, _), count in channel_counts.items()
            ):
                raise ValueError(
                    "allocated occurrence count exceeds corpus token denominator"
                )

            entries = []
            for identity_id in sorted({identity_id for _, identity_id in counts}):
                contributions = []
                score = Decimal(0)
                total = Decimal(0)
                for corpus in corpus_rows:
                    key = (corpus.corpus_id, identity_id)
                    count = counts.get(key, Decimal(0))
                    if not count:
                        continue
                    ppm = Decimal(1_000_000) * count / Decimal(corpus.token_count)
                    dispersion = Decimal(len(identity_docs[key])) / Decimal(
                        corpus.document_count
                    )
                    score += corpus.weight * (Decimal(1) + ppm).ln() * dispersion
                    total += count
                    contributions.append(
                        CorpusContribution(
                            corpus_id=corpus.corpus_id,
                            allocated_count=count,
                            document_frequency=len(identity_docs[key]),
                            frequency_ppm=ppm,
                            dispersion=dispersion,
                            occurrence_ids=tuple(sorted(identity_occurrences[key])),
                        )
                    )
                dimensions = {
                    "frequency": total / (Decimal(1) + total),
                    "confidence": confidence_counts[identity_id] / total,
                    "coverage": Decimal(len(contributions)) / Decimal(len(corpus_rows)),
                    "validation": Decimal(1),
                }
                quality = sum(
                    (
                        policy.quality_weights[name] * dimensions[name]
                        for name in sorted(dimensions)
                    ),
                    Decimal(0),
                )
                entries.append(
                    RankingEntry(
                        lexical_identity_id=identity_id,
                        rank=1,
                        score=score.quantize(Decimal(1).scaleb(-policy.rank_precision)),
                        aggregate_allocated_frequency=total,
                        quality_score=quality,
                        contributions=tuple(contributions),
                    )
                )
            entries.sort(
                key=lambda item: (
                    -item.score,
                    -item.aggregate_allocated_frequency,
                    item.lexical_identity_id,
                )
            )
            ranked = tuple(
                item.model_copy(update={"rank": rank})
                for rank, item in enumerate(entries, 1)
            )

        # Canonicalize allocation ordering too: equivalent declared order must not change a manifest.
        canonical_observations = []
        for row in rows:
            payload = row.model_dump(mode="json")
            payload["allocations"] = sorted(
                payload["allocations"], key=lambda item: item["lexical_identity_id"]
            )
            canonical_observations.append(payload)
        return RankingResult(
            language=corpus_rows[0].language,
            policy=policy,
            corpora=corpus_rows,
            observations_sha256=canonical_sha256(canonical_observations),
            entries=ranked,
            quarantine=tuple(
                sorted(
                    quarantine, key=lambda item: (item.corpus_id, item.occurrence_id)
                )
            ),
            suppressed_occurrence_ids=tuple(sorted(suppressed)),
        )

    @staticmethod
    def _bounded(values: Iterable, limit: int, name: str) -> list:
        result = []
        for item in values:
            if len(result) >= limit:
                raise ValueError(f"ranking {name} limit exceeded")
            result.append(item)
        return result

    @staticmethod
    def _deduplicate_spans(
        rows: tuple[CorpusObservation, ...],
    ) -> tuple[list[CorpusObservation], list[str], list[QuarantinedOccurrence]]:
        groups: dict[tuple[str, str, str], list[CorpusObservation]] = defaultdict(list)
        for row in rows:
            groups[(row.corpus_id, row.document_id, row.counting_channel)].append(row)
        accepted = []
        suppressed = []
        quarantine = []
        for key in sorted(groups):
            occupied: set[int] = set()
            spans: dict[tuple[int, int], list[CorpusObservation]] = defaultdict(list)
            for row in groups[key]:
                spans[(row.token_start, row.token_end)].append(row)
            for (start, end), candidates in sorted(
                spans.items(),
                key=lambda item: (
                    -(item[0][1] - item[0][0]),
                    item[0][0],
                ),
            ):
                tokens = range(start, end)
                if any(token in occupied for token in tokens):
                    suppressed.extend(
                        f"{row.corpus_id}:{row.occurrence_id}" for row in candidates
                    )
                    continue
                occupied.update(tokens)
                signatures = {
                    (
                        row.surface,
                        row.occurrence_count,
                        row.is_mwe,
                        tuple(
                            sorted(
                                (a.lexical_identity_id, a.share, a.confidence)
                                for a in row.allocations
                            )
                        ),
                    )
                    for row in candidates
                }
                if len(signatures) > 1:
                    quarantine.extend(
                        QuarantinedOccurrence(
                            corpus_id=row.corpus_id,
                            occurrence_id=row.occurrence_id,
                            reason="ambiguous_span",
                        )
                        for row in candidates
                    )
                    continue
                ordered = sorted(candidates, key=lambda item: item.occurrence_id)
                accepted.append(ordered[0])
                suppressed.extend(
                    f"{row.corpus_id}:{row.occurrence_id}" for row in ordered[1:]
                )
        return accepted, suppressed, quarantine
