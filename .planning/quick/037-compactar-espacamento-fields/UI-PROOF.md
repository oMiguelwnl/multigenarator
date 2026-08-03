# UI Proof: Compact Fields Code, Test, and APKG Contract

```json
{
  "proof_bundle_version": "1.0",
  "scope": {
    "work_item": "quick-037-compactar-espacamento-fields",
    "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
    "requirement_ids": [
      "quick-task-without-phase-requirement-id"
    ],
    "slot_ids": [
      "compact-fields-code-test-apkg"
    ]
  },
  "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
  "environment": "Python 3.12+ e serviços locais para code/test/APKG; Anki nativo para aceitação humana; sem rede/providers.",
  "viewport": "Contrato CSS responsivo preservado; tamanho real do Anki usado pelo usuário na reavaliação, sem alegar pixels antes dela.",
  "evidence_inputs": {
    "kinds": [
      "code",
      "test"
    ],
    "tools_used": [
      "pytest",
      "python-css-inspection",
      "python-apkg-sqlite-inspection",
      "gsdd-ui-proof-validate"
    ],
    "files_observed": [
      "tests/services/test_card_template_loader.py",
      "tests/integration/test_v13_normal_template_export_contract.py",
      "src/multilang/templates/normal_card.md",
      "german_frequency_template_dummy.apkg"
    ]
  },
  "commands_or_manual_steps": [
    {
      "command": "uv run pytest tests/services/test_card_template_loader.py::test_normal_and_mandarin_panels_use_responsive_viewport_height -q",
      "result": "passed",
      "observed_exit_code": 1,
      "output": "Expected TDD RED observed: display resolved to flex instead of block."
    },
    {
      "command": "uv run pytest tests/services/test_card_template_loader.py::test_normal_and_mandarin_panels_use_responsive_viewport_height -q",
      "result": "passed",
      "observed_exit_code": 0,
      "output": "1 passed in 1.63s"
    },
    {
      "command": "uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q",
      "result": "passed",
      "observed_exit_code": 0,
      "output": "30 passed in 2.79s"
    },
    {
      "command": "PYTHONPATH=src uv run python -c '<037-PLAN.md APKG structural verifier>'",
      "result": "passed",
      "observed_exit_code": 0,
      "output": "APKG OK: 7 notes/cards, compact final block, preserved geometry, IDs 1995037001/1995037002; size_bytes=69850"
    }
  ],
  "observations": [
    {
      "observation": "O bloco final de .customCard usa display: block e não contém flex-direction, justify-content ou align-items.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "code",
      "artifact_refs": [
        "src/multilang/templates/normal_card.md"
      ],
      "privacy": {
        "data_classification": "CSS de repositório sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    },
    {
      "observation": "Min-height, padding, width, visual e centralização externa permanecem com os valores anteriores.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "code",
      "artifact_refs": [
        "src/multilang/templates/normal_card.md"
      ],
      "privacy": {
        "data_classification": "CSS de repositório sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    },
    {
      "observation": "Normal e as duas rotas Mandarin recebem o fluxo compacto pelo CSS normal compartilhado.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "test",
      "artifact_refs": [
        "tests/services/test_card_template_loader.py"
      ],
      "privacy": {
        "data_classification": "assertions de teste sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    },
    {
      "observation": "Os dois arquivos pytest focados passam após o RED esperado.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "test",
      "artifact_refs": [
        ".planning/quick/037-compactar-espacamento-fields/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "saída agregada de testes sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    },
    {
      "observation": "O APKG contém sete notes, CSS block compacto e somente os IDs 1995037001/1995037002.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "code",
      "artifact_refs": [
        "german_frequency_template_dummy.apkg"
      ],
      "privacy": {
        "data_classification": "APKG fictício local sem mídia ou conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente para a reavaliação desta quick task"
      },
      "result": "passed",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    }
  ],
  "artifacts": [
    {
      "path": "src/multilang/templates/normal_card.md",
      "type": "css inspection report",
      "visibility": "local_only",
      "retention": "reter localmente com os registros da quick task",
      "sensitivity": "CSS de repositório sem conteúdo de usuário",
      "safe_to_publish": false
    },
    {
      "path": ".planning/quick/037-compactar-espacamento-fields/UI-PROOF.md",
      "type": "focused pytest output",
      "visibility": "local_only",
      "retention": "reter localmente com os registros da quick task",
      "sensitivity": "resultado agregado de testes sem conteúdo de usuário",
      "safe_to_publish": false
    },
    {
      "path": "german_frequency_template_dummy.apkg",
      "type": "apkg structural report",
      "visibility": "local_only",
      "retention": "reter localmente para a reavaliação desta quick task",
      "sensitivity": "dados fictícios locais sem mídia ou conteúdo de usuário",
      "safe_to_publish": false
    },
    {
      "path": ".planning/quick/037-compactar-espacamento-fields/UI-PROOF.md",
      "type": "ui-proof metadata",
      "visibility": "local_only",
      "retention": "reter localmente com os registros da quick task",
      "sensitivity": "metadados locais sem dados pessoais ou secrets",
      "safe_to_publish": false
    },
    {
      "path": "tests/services/test_card_template_loader.py",
      "type": "test contract",
      "visibility": "local_only",
      "retention": "reter localmente com o repositório",
      "sensitivity": "assertions de teste sem conteúdo de usuário",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "data_classification": "código, assertions, saída agregada de teste e APKG fictício; sem conteúdo de usuário",
    "raw_artifacts_safe_to_publish": false,
    "retention": "reter localmente com os registros da quick task; nenhuma publicação aprovada",
    "contains_personal_data": false,
    "contains_user_content": false,
    "contains_secrets": false,
    "contains_private_absolute_paths": false,
    "screenshots_included": false,
    "external_publication_approved": false
  },
  "result": {
    "claim_status": "passed",
    "comparison_status_by_slot": {
      "compact-fields-code-test-apkg": "satisfied"
    },
    "summary": "O slot automático de code/test/APKG está satisfeito por inspeção local e regressões focadas."
  },
  "claim_limits": [
    "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
  ]
}
```
