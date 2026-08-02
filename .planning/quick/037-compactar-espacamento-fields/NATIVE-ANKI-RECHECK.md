# Native Anki Recheck: Compact Fields

```json
{
  "proof_bundle_version": "1.0",
  "scope": {
    "work_item": "quick-037-compactar-espacamento-fields-native-recheck",
    "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
    "requirement_ids": [
      "quick-task-without-phase-requirement-id"
    ],
    "slot_ids": [
      "compact-fields-native-anki-recheck"
    ]
  },
  "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
  "environment": "Python 3.12+ e serviços locais para code/test/APKG; Anki nativo para aceitação humana; sem rede/providers.",
  "viewport": "Contrato CSS responsivo preservado; tamanho real do Anki usado pelo usuário na reavaliação, sem alegar pixels antes dela.",
  "evidence_inputs": {
    "kinds": [
      "human"
    ],
    "tools_used": [
      "manual"
    ],
    "evidence_state": "deferred; nenhuma reavaliação humana do APKG Quick 037 foi registrada"
  },
  "commands_or_manual_steps": [
    {
      "manual_step": "Importar german_frequency_template_dummy.apkg no Anki e inspecionar um card curto na frente, verificando painel alto/centralizado e fields compactos.",
      "result": "deferred"
    },
    {
      "manual_step": "No Anki, revelar o verso de um card e verificar Translation, definição, imagem vazia e controles de áudio.",
      "result": "deferred"
    },
    {
      "manual_step": "No Anki, inspecionar o card de conteúdo longo e verificar legibilidade, crescimento ou rolagem natural e ausência de clipping.",
      "result": "deferred"
    }
  ],
  "observations": [
    {
      "observation": "No Anki, um card curto mantém o painel alto e centralizado, mas os fields aparecem compactos sem grandes vazios artificiais.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "human",
      "artifact_refs": [
        ".planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md"
      ],
      "privacy": {
        "data_classification": "checklist humano pendente sem captura ou conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente até a reavaliação humana"
      },
      "result": "deferred",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    },
    {
      "observation": "No Anki, o verso revela Translation e preserva definição, imagem vazia e controles de áudio sem regressão visual.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "human",
      "artifact_refs": [
        ".planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md"
      ],
      "privacy": {
        "data_classification": "checklist humano pendente sem captura ou conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente até a reavaliação humana"
      },
      "result": "deferred",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    },
    {
      "observation": "No Anki, o card de conteúdo longo permanece legível e cresce ou rola naturalmente sem clipping.",
      "claim": "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between.",
      "route_state": "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo.",
      "evidence_kind": "human",
      "artifact_refs": [
        ".planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md"
      ],
      "privacy": {
        "data_classification": "checklist humano pendente sem captura ou conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente até a reavaliação humana"
      },
      "result": "deferred",
      "claim_limit": "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
    }
  ],
  "artifacts": [
    {
      "path": ".planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md",
      "type": "human anki observation",
      "visibility": "local_only",
      "retention": "reter localmente até a reavaliação humana",
      "sensitivity": "checklist pendente sem raw UI artifact",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "data_classification": "checklist humano pendente; nenhuma captura, observação nova ou conteúdo de usuário",
    "raw_artifacts_safe_to_publish": false,
    "retention": "reter localmente até a reavaliação humana; nenhuma publicação aprovada",
    "contains_personal_data": false,
    "contains_user_content": false,
    "contains_secrets": false,
    "contains_private_absolute_paths": false,
    "screenshots_included": false,
    "external_publication_approved": false
  },
  "result": {
    "claim_status": "deferred",
    "comparison_status_by_slot": {
      "compact-fields-native-anki-recheck": "deferred"
    },
    "native_acceptance_status": "human_needed",
    "summary": "A reavaliação do APKG Quick 037 no Anki permanece pendente."
  },
  "claim_limits": [
    "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
  ],
  "uat_history": {
    "previous_uat_status": "failed",
    "previous_uat_reason": "espaçamento excessivo entre fields no APKG anterior",
    "current_uat_status": "human_needed",
    "current_artifact": "german_frequency_template_dummy.apkg",
    "current_model_id": 1995037001,
    "current_deck_id": 1995037002
  }
}
```
