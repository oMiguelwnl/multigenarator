# Local UI proof

```json
{
  "proof_bundle_version": 1,
  "scope": {
    "work_item": "061-output-deck-design",
    "claim": "Local prototype rendering and interactions",
    "requirement_ids": [
      "direct-user-request-output-design"
    ],
    "slot_ids": [
      "output-layout",
      "output-interaction"
    ]
  },
  "route_state": "local preview: front, hints, back, variants and reset",
  "environment": {
    "browser": "151.0.7922.34",
    "runner": "existing Playwright; temporary Chromium",
    "fragment_sha256": "58abff5e3d27b35ab6bb2fbd2e140a302a8f4966871ee729a9c9610cbaf74577",
    "fallback_reason": "agent-browser and CUA browsers unavailable"
  },
  "viewport": [
    {
      "width": 360,
      "height": 800
    },
    {
      "width": 736,
      "height": 900
    }
  ],
  "evidence_inputs": {
    "kinds": [
      "code",
      "test",
      "runtime"
    ],
    "tools_used": [
      "playwright",
      "view_image"
    ]
  },
  "commands_or_manual_steps": [
    {
      "command": "node .multilang/verification/output-deck-design/check-preview.cjs",
      "result": "passed"
    },
    {
      "manual_step": "Inspect mobile light/dark front/back, desktop dark back and Korean/Japanese/Mandarin mobile screenshots",
      "result": "passed"
    }
  ],
  "observations": [
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "state": "front",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "front",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "state": "back; hint and manual grade",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "back; hint and manual grade",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "language": "de",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "language": "es",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "language": "fr",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "language": "ko",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "language": "ja",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "light",
        "language": "zh",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "state": "front",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "front",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "state": "back; hint and manual grade",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "back; hint and manual grade",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "language": "de",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "language": "es",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "language": "fr",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "language": "ko",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "language": "ja",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 360,
        "theme": "dark",
        "language": "zh",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "state": "front",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "front",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "state": "back; hint and manual grade",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "back; hint and manual grade",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "language": "de",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "language": "es",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "language": "fr",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "language": "ko",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "language": "ja",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "light",
        "language": "zh",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "state": "front",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "front",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "state": "back; hint and manual grade",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "back; hint and manual grade",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "language": "de",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "language": "es",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "language": "fr",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "language": "ko",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "language": "ja",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    },
    {
      "observation": {
        "width": 736,
        "theme": "dark",
        "language": "zh",
        "state": "example; all disclosures; reset",
        "result": "passed"
      },
      "claim": "Visible state and expected interaction; no horizontal overflow",
      "route_state": "example; all disclosures; reset",
      "evidence_kind": "runtime",
      "artifact_refs": [
        ".multilang/verification/output-deck-design/report.json"
      ],
      "privacy": {
        "data_classification": "synthetic_content",
        "raw_artifacts_safe_to_publish": false,
        "retention": "local_task_artifact"
      },
      "result": "passed",
      "claim_limit": "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
    }
  ],
  "artifacts": [
    {
      "path": ".multilang/verification/output-deck-design/back-360-dark.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/back-360-light.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/back-736-dark.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/back-736-light.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/front-360-dark.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/front-360-light.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/front-736-dark.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/front-736-light.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/ja-360-dark.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/ko-360-dark.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/zh-360-dark.png",
      "type": "screenshot",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    },
    {
      "path": ".multilang/verification/output-deck-design/report.json",
      "type": "report",
      "visibility": "local_only",
      "retention": "local_task_artifact",
      "sensitivity": "synthetic_content",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "data_classification": "synthetic_content",
    "raw_artifacts_safe_to_publish": false,
    "retention": "local_task_artifact"
  },
  "result": {
    "claim_status": "passed",
    "comparison_status_by_slot": {
      "output-layout": "satisfied",
      "output-interaction": "satisfied"
    }
  },
  "claim_limits": [
    "HTML prototype only; no Anki client acceptance, real audio, grading, scheduling or linguistic production approval."
  ]
}
```
