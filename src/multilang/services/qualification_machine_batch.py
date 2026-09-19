"""Export every frozen pipeline review item into deterministic machine batches."""

from pathlib import Path

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine import MachineActor, build_machine_request
from multilang.services.qualification_machine_runner import (
    _locked,
    _write_once,
    export_machine_request,
    json_bytes,
    persist_artifact,
    read_json,
)
from multilang.services.qualification_pipeline import _resume
from multilang.services.qualification_review import load_review_packet
from multilang.services.vocabulary_review import _plain_path


def export_pipeline_machine_requests(
    pipeline: Path,
    *,
    manifest_sha256: str,
    actor: MachineActor,
    output: Path,
    item_limit: int = 20,
    enrich_sources: bool = True,
) -> dict:
    """Exports frozen, hash-verified evidence; no acquisition, inference or calls.

    The upstream pipeline command revalidates original source files. This step
    revalidates its published inventory, keeping source acquisition and export
    separate. Shards preserve all items and reference their parent packet.
    """
    if type(item_limit) is not int or not 1 <= item_limit <= 100:
        raise ValueError("machine batch item limit must be between 1 and 100")
    if type(enrich_sources) is not bool:
        raise ValueError("enrich_sources must be a boolean")
    pipeline = _plain_path(pipeline)
    manifest = read_json(pipeline / "manifest.json", manifest_sha256)
    request = read_json(pipeline / "request.json", manifest["files"]["request.json"])
    evidence = read_json(
        pipeline / "source-evidence.json", manifest["files"]["source-evidence.json"]
    )
    if _resume(pipeline, request, evidence) != manifest:
        raise ValueError("pipeline artifact drift")
    actor = MachineActor.model_validate(actor.model_dump(mode="json"))
    config = {
        "pipeline_manifest_sha256": manifest_sha256,
        "actor": actor.model_dump(mode="json"),
        "item_limit": item_limit,
        "schema_version": 2,
        "enrich_sources": enrich_sources,
    }
    requests, total, packet_number = [], 0, 0
    with _locked(output) as root:
        if root.exists():
            if read_json(root / "batch.json") != config:
                raise ValueError("machine batch configuration drift")
        else:
            root.mkdir(mode=0o700)
            _write_once(root / "batch.json", config)
        for name, digest in sorted(manifest["files"].items()):
            if not name.startswith("pilot/review/") or not name.endswith("/packet.json"):
                continue
            packet = load_review_packet(pipeline / name, expected_sha256=digest)
            parent_hash = packet.packet_sha256
            enrichment_path = None
            packet_number += 1
            if enrich_sources:
                from multilang.services.qualification_machine_evidence import enrich_machine_packet

                enrichment = enrich_machine_packet(
                    packet, pipeline=pipeline, manifest_sha256=manifest_sha256
                )
                enrichment_path = f"evidence-{packet_number:06d}"
                persist_artifact(
                    root / enrichment_path,
                    kind="machine-evidence",
                    binding=canonical_sha256(enrichment.model_dump(mode="json")),
                    files={
                        "enrichment.json": json_bytes(enrichment),
                        "packet.json": json_bytes(enrichment.packet),
                    },
                )
                packet = enrichment.packet
            for offset in range(0, len(packet.items), item_limit):
                items = packet.items[offset : offset + item_limit]
                shard_id = canonical_sha256([packet.packet_sha256, offset, item_limit])
                shard = packet.model_copy(
                    update={"packet_id": "machine-shard:" + shard_id, "items": items}
                )
                shard_actor = actor.model_copy(
                    update={
                        "context_id": "context:" + canonical_sha256([actor.context_id, shard_id])
                    }
                )
                machine_request = build_machine_request(
                    shard, actor=shard_actor, run_id="proposal:" + shard_id
                )
                path = f"request-{len(requests) + 1:06d}"
                child = export_machine_request(machine_request, root / path)
                requests.append(
                    {
                        "path": path,
                        "parent_packet_sha256": parent_hash,
                        "enriched_packet_sha256": packet.packet_sha256 if enrich_sources else None,
                        "enrichment_path": enrichment_path,
                        "parent_packet_path": name,
                        "item_count": len(items),
                        "kind": items[0].kind,
                        "request_sha256": machine_request.request_sha256,
                        "request_file_sha256": child["files"]["request.json"],
                    }
                )
                total += len(items)
        if not requests:
            raise ValueError("pipeline contains no review packets")
        result = {
            "config_sha256": canonical_sha256(config),
            "language": request["language"],
            "request_count": len(requests),
            "item_count": total,
            "requests": requests,
            "enrich_sources": enrich_sources,
            "provider_calls_executed": 0,
            "production_eligible": False,
        }
        if (root / "index.json").exists():
            if read_json(root / "index.json") != result:
                raise ValueError("machine batch inventory drift")
        else:
            _write_once(root / "index.json", result)
        return result
