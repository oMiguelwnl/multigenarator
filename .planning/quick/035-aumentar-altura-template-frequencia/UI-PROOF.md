# UI Proof: Automated Responsive Frequency Panel Contract

This bundle is intentionally scoped only to the automated code/test slot. Native Anki acceptance is recorded separately in `NATIVE-ANKI-ACCEPTANCE.md` and remains `human_needed`.

```json
{
  "proof_bundle_version": "1.0",
  "scope": {
    "work_item": "quick-035-aumentar-altura-template-frequencia",
    "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
    "requirement_ids": [
      "quick-task-without-phase-requirement-id"
    ],
    "slot_ids": [
      "frequency-panel-responsive-css-contract"
    ]
  },
  "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
  "environment": "Python 3.12+, loader real do projeto; sem browser ou renderer nativo do Anki",
  "viewport": "Desktop 1280x800 (min-height calculada 720px) e mobile portrait 390x667 (min-height calculada 587px); cálculo/contrato CSS, não pixels renderizados",
  "evidence_inputs": {
    "kinds": [
      "code",
      "test"
    ],
    "tools_used": [
      "pytest",
      "git-diff",
      "python-css-inspection"
    ],
    "files_observed": [
      "src/multilang/templates/normal_card.md",
      "src/multilang/templates/mandarin_card.md",
      "src/multilang/services/card_template_loader.py",
      "tests/services/test_card_template_loader.py",
      "tests/integration/test_v13_normal_template_export_contract.py"
    ]
  },
  "commands_or_manual_steps": [
    {
      "command": "uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q",
      "result": "passed",
      "observed_exit_code": 0,
      "output": "30 passed in 2.38s"
    }
  ],
  "observations": [
    {
      "observation": "O CSS efetivo final de .card mantém display flex, justify-content center, align-items center, padding 40px 16px e min-height 100vh.",
      "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
      "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
      "evidence_kind": "code",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "declarações CSS de repositório sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
    },
    {
      "observation": "O teste focado confirma box-sizing border-box na última regra universal e vincula os dois paddings verticais de 40px aos 80px de calc(100vh - 80px).",
      "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
      "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
      "evidence_kind": "test",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "assertions de teste e aritmética sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
    },
    {
      "observation": "O bloco vencedor de .customCard usa display flex, flex-direction column, justify-content space-between, align-items stretch, min-height min(760px, calc(100vh - 80px)) e padding clamp(24px, 4vh, 40px) 24px, sem override .cardBack posterior.",
      "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
      "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
      "evidence_kind": "code",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "declarações CSS de repositório sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
    },
    {
      "observation": "A aritmética testada produz min(760, 800 - 80) = 720px no desktop, min(760, 667 - 80) = 587px no mobile e teto de 760px em viewports altas.",
      "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
      "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
      "evidence_kind": "test",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "aritmética determinística de teste sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
    },
    {
      "observation": "O bloco final não declara height ou max-height rígida nem adiciona overflow-y forçado, portanto a min-height permite crescimento natural para conteúdo longo.",
      "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
      "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
      "evidence_kind": "code",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "inspeção CSS de repositório sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
    },
    {
      "observation": "Frequency Mandarin e word-list Mandarin permanecem iguais e começam com o CSS normal completo, herdando o mesmo contrato responsivo sem edição de mandarin_card.md.",
      "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
      "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
      "evidence_kind": "test",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "assertions de composição de template sem conteúdo de usuário",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
    },
    {
      "observation": "A suíte focada do loader e o contrato de export v1.3 passam 30 testes, preservando referências de campo, reveal de Translation, áudio, imagem, composição Mandarin e contrato APKG normal.",
      "claim": "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo.",
      "route_state": "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados.",
      "evidence_kind": "test",
      "artifact_refs": [
        ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
      ],
      "privacy": {
        "data_classification": "resultado agregado de pytest e assertions de repositório",
        "raw_artifacts_safe_to_publish": false,
        "retention": "reter localmente com os registros da quick task"
      },
      "result": "passed",
      "claim_limit": "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
    }
  ],
  "artifacts": [
    {
      "path": ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md",
      "type": "diff do template/teste",
      "visibility": "local_only",
      "retention": "reter localmente com os registros da quick task",
      "sensitivity": "registro textual de diff sem conteúdo de usuário",
      "safe_to_publish": false
    },
    {
      "path": ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md",
      "type": "inspeção do CSS gerado",
      "visibility": "local_only",
      "retention": "reter localmente com os registros da quick task",
      "sensitivity": "registro textual de CSS sem conteúdo de usuário",
      "safe_to_publish": false
    },
    {
      "path": ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md",
      "type": "saída pytest focada",
      "visibility": "local_only",
      "retention": "reter localmente com os registros da quick task",
      "sensitivity": "saída agregada de teste sem conteúdo de usuário",
      "safe_to_publish": false
    },
    {
      "path": ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md",
      "type": "registros em UI-PROOF.md",
      "visibility": "local_only",
      "retention": "reter localmente com os registros da quick task",
      "sensitivity": "metadados de proof sem dados pessoais ou secrets",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "data_classification": "código do repositório, assertions e saída agregada de testes; sem conteúdo de usuário",
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
      "frequency-panel-responsive-css-contract": "satisfied"
    },
    "summary": "O slot code/test automatizado está satisfeito; nenhuma alegação de rendering nativo faz parte deste bundle."
  },
  "claim_limits": [
    "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
  ],
  "evidence_details": {
    "diff do template/teste": "O diff contém somente a regressão CSS focada e o override final aprovado no template normal; famílias separadas e loader não têm diff.",
    "inspeção do CSS gerado": "O loader produz .card flex/center com 100vh e .customCard flex-column/space-between/stretch com min(760px, calc(100vh - 80px)); Mandarin frequency e word-list têm o CSS normal como prefixo completo.",
    "saída pytest focada": "30 passed in 2.38s",
    "registros em UI-PROOF.md": "Sete observações passed fornecem evidência code e test com claim, route_state e claim_limit literais do slot planejado."
  },
  "tooling_mismatch_waiver": {
    "minimum_observations": "O plano confirmado usa o valor numérico 7, enquanto validateUiProofSlots nesta versão exige uma lista. O plano permanece inalterado; este bundle registra sete observações passed e aceita somente o erro global missing_minimum_observations como incompatibilidade de schema.",
    "expected_artifact_type_case": "Os tipos dos artifacts preservam literalmente os quatro valores planejados. Como compareUiProofSlots converte os tipos observados para lowercase sem converter os esperados, a execução de compatibilidade aplica case-fold somente à cópia em memória dos tipos planejados antes de chamar o comparador; nenhum artifact ou plano é reescrito."
  }
}
```

## Native acceptance boundary

O checklist humano não integra este bundle automatizado. Consulte `NATIVE-ANKI-ACCEPTANCE.md`; o estado nativo continua `human_needed`.
