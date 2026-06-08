"""Final scanner-readable v2.0 Classical Latin milestone evidence."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from types import ModuleType

from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.latin_export import export_latin_mvp_bundle
V20_REQUIREMENTS = (
    "MODE-01", "MODE-02", "MODE-03",
    "FREQ-01", "FREQ-02", "FREQ-03", "SRC-01", "SRC-02", "SENT-01", "SENT-02",
    "GRAM-01", "GRAM-02", "GRAM-03", "GRAM-04",
    "REV-01", "REV-02", "REV-03",
    "PT-01", "PT-02", "PT-03",
    "AUD-01", "AUD-02", "AUD-03", "AUD-04",
    "EXP-01", "EXP-02", "EXP-03",
    "EVID-01", "EVID-02", "EVID-03",
)
REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_ROOT = REPO_ROOT / "tests" / "integration"


def _load_evidence_module(file_name: str) -> ModuleType:
    module_path = INTEGRATION_ROOT / file_name
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PHASE_22_REQUIREMENTS = _load_evidence_module("test_v20_latin_mode_isolation_evidence.py").PHASE_22_REQUIREMENTS
PHASE_23_REQUIREMENTS = _load_evidence_module("test_v20_latin_source_pack_evidence.py").PHASE_23_REQUIREMENTS
PHASE_24_REQUIREMENTS = tuple(_load_evidence_module("test_v20_latin_grammar_evidence.py").PHASE_24_REQUIREMENTS)
PHASE_25_REQUIREMENTS = _load_evidence_module("test_v20_latin_review_gate_evidence.py").PHASE_25_REQUIREMENTS
PHASE_26_REQUIREMENTS = _load_evidence_module("test_v20_latin_portuguese_translation_asset.py").PHASE_26_REQUIREMENTS
PHASE_27_REQUIREMENTS = _load_evidence_module("test_v20_latin_audio_evidence.py").PHASE_27_REQUIREMENTS
PHASE_28_EXPORT_REQUIREMENTS = _load_evidence_module("test_v20_latin_export_evidence.py").PHASE_28_EXPORT_REQUIREMENTS


def test_v20_requirement_set_is_exactly_30_ids() -> None:
    assert len(V20_REQUIREMENTS) == 30
    assert len(set(V20_REQUIREMENTS)) == 30
    assert V20_REQUIREMENTS[0] == "MODE-01"
    assert V20_REQUIREMENTS[-1] == "EVID-03"


def test_all_v20_requirements_have_executable_or_review_artifact_coverage() -> None:
    covered = set(PHASE_22_REQUIREMENTS)
    covered.update(PHASE_23_REQUIREMENTS)
    covered.update(PHASE_24_REQUIREMENTS)
    covered.update(PHASE_25_REQUIREMENTS)
    covered.update(PHASE_26_REQUIREMENTS)
    covered.update(PHASE_27_REQUIREMENTS)
    covered.update(PHASE_28_EXPORT_REQUIREMENTS)
    covered.update({"EVID-01", "EVID-02", "EVID-03"})

    assert covered == set(V20_REQUIREMENTS)


def test_final_milestone_privacy_and_source_safeguards(tmp_path: Path) -> None:
    json_paths = [
        REPO_ROOT / "data/latin_mvp/latin-mvp-50-v1.json",
        REPO_ROOT / "data/latin_mvp/latin-mvp-50-v1-curation.json",
        REPO_ROOT / "data/latin_mvp/latin-mvp-50-v1-pt.json",
        REPO_ROOT / "data/latin_mvp/latin-mvp-50-v1-audio.json",
    ]
    export_latin_mvp_bundle(export_format=ExportArtifactFormat.CSV, output_dir=tmp_path, repo_root=REPO_ROOT)
    export_latin_mvp_bundle(export_format=ExportArtifactFormat.TSV, output_dir=tmp_path, repo_root=REPO_ROOT)
    rendered = "\n".join(path.read_text(encoding="utf-8") for path in json_paths)
    rendered += "\n" + (tmp_path / "latin-mvp-50.csv").read_text(encoding="utf-8")
    rendered += "\n" + (tmp_path / "latin-mvp-50.tsv").read_text(encoding="utf-8")
    json.loads(json_paths[0].read_text(encoding="utf-8"))

    forbidden = ["C:\\", "/Users/", "/home/", "../", "..\\", "AZURE_", "OPENAI_", "api_key", "provider_response", "raw_response", "unapproved_source"]
    for token in forbidden:
        assert token not in rendered
    assert "license_gate\": \"blocked" not in rendered
    assert "review_status\": \"rejected" not in rendered
    assert "playback_review_status\": \"rejected" not in rendered
