"""Every prepared item is exported exactly once, with stable resumable shards."""

import hashlib
import json

import pytest
from test_qualification_machine_runner import request_fixture
from test_qualification_pipeline import request as pipeline_request


def test_batch_preserves_every_item_and_resumes(tmp_path):
    from multilang.services.qualification_machine_batch import export_pipeline_machine_requests
    from multilang.services.qualification_pipeline import run_qualification_pipeline

    pipeline = tmp_path / "pipeline"
    run_qualification_pipeline(pipeline_request(tmp_path), pipeline)
    digest = hashlib.sha256((pipeline / "manifest.json").read_bytes()).hexdigest()
    actor = request_fixture().actor
    output = tmp_path / "batch"
    first = export_pipeline_machine_requests(
        pipeline, manifest_sha256=digest, actor=actor, output=output, item_limit=1
    )
    assert first["item_count"] > 0
    assert first["request_count"] == first["item_count"]
    assert first["enrich_sources"] is True
    assert (output / "evidence-000001" / "enrichment.json").is_file()
    assert (
        export_pipeline_machine_requests(
            pipeline, manifest_sha256=digest, actor=actor, output=output, item_limit=1
        )
        == first
    )
    item_ids = []
    for entry in first["requests"]:
        data = json.loads((output / entry["path"] / "request.json").read_text())
        item_ids.extend(item["item_id"] for item in data["packet"]["items"])
    assert len(item_ids) == len(set(item_ids)) == first["item_count"]
    with pytest.raises(ValueError, match="drift"):
        export_pipeline_machine_requests(
            pipeline, manifest_sha256=digest, actor=actor, output=output, item_limit=2
        )
    path = output / first["requests"][0]["path"] / "request.json"
    path.write_text("{}")
    with pytest.raises(ValueError):
        export_pipeline_machine_requests(
            pipeline, manifest_sha256=digest, actor=actor, output=output, item_limit=1
        )


def test_batch_rejects_changed_pipeline_and_invalid_limits(tmp_path):
    from multilang.services.qualification_machine_batch import export_pipeline_machine_requests
    from multilang.services.qualification_pipeline import run_qualification_pipeline

    pipeline = tmp_path / "pipeline"
    manifest = run_qualification_pipeline(pipeline_request(tmp_path), pipeline)
    digest = hashlib.sha256((pipeline / "manifest.json").read_bytes()).hexdigest()
    actor = request_fixture().actor
    with pytest.raises(ValueError):
        export_pipeline_machine_requests(
            pipeline, manifest_sha256=digest, actor=actor, output=tmp_path / "bad", item_limit=0
        )
    name = next(name for name in manifest["files"] if name.endswith("packet.json"))
    (pipeline / name).write_text("{}")
    with pytest.raises(ValueError):
        export_pipeline_machine_requests(
            pipeline, manifest_sha256=digest, actor=actor, output=tmp_path / "bad"
        )
