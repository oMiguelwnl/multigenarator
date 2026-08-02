# Native Anki Acceptance: Responsive Frequency Panel

No native Anki observation or screenshot has been captured. This sidecar preserves the planned checklist without contaminating the automated code/test slot.

```json
{
  "proof_bundle_version": "1.0",
  "scope": {
    "work_item": "quick-035-aumentar-altura-template-frequencia-native-acceptance",
    "claim": "O painel normal e o Mandarin aparecem altos, centralizados e bem espaçados no Anki Desktop e mobile, sem rolagem causada apenas pela altura mínima em tela curta e sem cortar conteúdo longo.",
    "requirement_ids": [
      "quick-task-without-phase-requirement-id"
    ],
    "slot_ids": [
      "frequency-panel-native-anki-acceptance"
    ]
  },
  "route_state": "Importar decks representativos normal e Mandarin; observar frente e verso com conteúdo curto e longo no Anki Desktop e em um cliente Anki mobile portrait.",
  "environment": "WebView nativo do Anki Desktop e de um cliente Anki mobile; agent-browser comum não é equivalente",
  "viewport": "Anki Desktop 1280x800 e mobile portrait representativo 390x667, mais estado de tela baixa disponível no cliente",
  "evidence_inputs": {
    "kinds": [
      "human"
    ],
    "tools_used": [
      "manual"
    ],
    "evidence_state": "pending; no native observation exists"
  },
  "commands_or_manual_steps": [
    {
      "manual_step": "Anki Desktop 1280x800: observar normal frequency frente com conteúdo curto, verificando altura, centralização e espaçamento.",
      "result": "deferred"
    },
    {
      "manual_step": "Anki Desktop 1280x800: observar normal frequency verso com conteúdo longo, reveal e crescimento sem clipping.",
      "result": "deferred"
    },
    {
      "manual_step": "Anki Desktop 1280x800: observar Mandarin frequency frente com conteúdo curto e CSS herdado.",
      "result": "deferred"
    },
    {
      "manual_step": "Anki Desktop 1280x800: observar Mandarin word-list verso com conteúdo longo, reveal e crescimento sem clipping.",
      "result": "deferred"
    },
    {
      "manual_step": "Cliente Anki mobile 390x667/tela baixa: observar normal frequency frente curta e confirmar que a min-height sozinha não cria rolagem.",
      "result": "deferred"
    },
    {
      "manual_step": "Cliente Anki mobile 390x667: observar normal frequency verso longo e confirmar rolagem natural sem corte.",
      "result": "deferred"
    },
    {
      "manual_step": "Cliente Anki mobile 390x667/tela baixa: observar Mandarin frequency frente curta para altura, centralização e espaçamento.",
      "result": "deferred"
    },
    {
      "manual_step": "Cliente Anki mobile 390x667: observar Mandarin word-list verso longo para rolagem natural, reveal e ausência de clipping.",
      "result": "deferred"
    }
  ],
  "observations": [
    {
      "observation": "As oito observações nativas planejadas ainda não foram executadas; não existe evidência humana passada, screenshot ou avaliação de scrolling/clipping.",
      "claim": "O painel normal e o Mandarin aparecem altos, centralizados e bem espaçados no Anki Desktop e mobile, sem rolagem causada apenas pela altura mínima em tela curta e sem cortar conteúdo longo.",
      "route_state": "Importar decks representativos normal e Mandarin; observar frente e verso com conteúdo curto e longo no Anki Desktop e em um cliente Anki mobile portrait.",
      "evidence_kind": "human",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/NATIVE-ANKI-ACCEPTANCE.md"
      ],
      "privacy": {
        "data_classification": "checklist pendente sem captura ou conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente até revisão humana"
      },
      "result": "deferred",
      "native_acceptance_status": "human_needed",
      "claim_limit": "Permanece human_needed até as observações nativas serem registradas; pytest, inspeção de CSS e agent-browser comum não fecham esta alegação visual."
    }
  ],
  "artifacts": [
    {
      "path": ".planning/quick/035-aumentar-altura-template-frequencia/NATIVE-ANKI-ACCEPTANCE.md",
      "type": "checklist manual normal/Mandarin, front/back, Desktop/mobile, incluindo conteúdo longo",
      "visibility": "local_only",
      "retention": "reter localmente até revisão humana",
      "sensitivity": "checklist pendente sem raw UI artifact",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "data_classification": "checklist humano pendente; nenhuma captura, observação ou conteúdo de usuário",
    "raw_artifacts_safe_to_publish": false,
    "retention": "reter localmente até revisão humana; nenhuma publicação aprovada",
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
      "frequency-panel-native-anki-acceptance": "deferred"
    },
    "native_acceptance_status": "human_needed",
    "summary": "Aceitação visual/scrolling em WebViews nativos ainda não observada."
  },
  "claim_limits": [
    "Permanece human_needed até as observações nativas serem registradas; pytest, inspeção de CSS e agent-browser comum não fecham esta alegação visual."
  ],
  "tooling_mismatch_waiver": {
    "minimum_observations": "O plano confirmado usa o valor numérico 8, enquanto validateUiProofSlots nesta versão exige uma lista. O plano permanece inalterado e os oito passos pendentes estão preservados neste sidecar."
  }
}
```
