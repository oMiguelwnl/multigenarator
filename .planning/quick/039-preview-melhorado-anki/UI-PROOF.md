# Quick Task 039 UI Proof

```json
{
  "proof_bundle_version": "1.0",
  "scope": "Preview HTML offline e pacote Anki experimental isolado para Buch, Wasser e lernen; nenhuma alteração de produção, teste, provider ou mídia.",
  "route_state": {
    "improved-normal-card-preview-source": "Abrir ou inspecionar normal_card_improved_preview.html localmente; as janelas e os cards aparecem em ordem front/back.",
    "improved-normal-card-apkg-structure": "Inspecionar exports/anki_previews/normal-card-improved-test.apkg como ZIP e sua collection.anki2 como SQLite, sem extractall.",
    "improved-normal-card-native-anki-appearance": "Importar o APKG no Anki Desktop e revisar Buch, Wasser e lernen na frente e no verso."
  },
  "environment": {
    "runtime": "opencode",
    "os": "Windows",
    "python": "Projeto via uv offline/no-sync/frozen/no-env-file",
    "network_used": false,
    "env_file_read": false,
    "providers_loaded": false,
    "extractall_used": false,
    "browser_or_anki_renderer_used": false,
    "notes": "A inspeção estrutural completa fechou explicitamente a conexão SQLite antes do cleanup do TemporaryDirectory, necessário no Windows."
  },
  "viewport": {
    "source_contract": "Duas janelas comparativas; conteúdo interno limitado a 900px; breakpoint próprio em max-width 420px.",
    "native_pending": "Revisor Anki amplo e estreito, reduzido até 420px ou menos.",
    "rendering_claim": "Nenhum pixel computado ou comportamento do WebView nativo foi observado nesta execução."
  },
  "evidence_inputs": {
    "tools_used": [
      "uv run --offline --no-sync --frozen --no-env-file python",
      "Python stdlib: pathlib, re, csv, zipfile, sqlite3, tempfile, hashlib, json",
      "genanki 0.13 family",
      "Git somente leitura para HEAD, staged diff, status e enumeração de paths"
    ],
    "artifacts_inspected": [
      "normal_card_improved_preview.html",
      "exports/anki_previews/normal-card-improved-test.apkg",
      "exports/anki_previews/normal-card-improved-test.tsv"
    ],
    "validator_outputs": [
      "PREVIEW-SOURCE PASS: selector-bound full-width, hierarchy, clamp, audio focus/contrast and mobile declarations",
      "DELIVERY PASS: APKG non-empty; TSV UTF-8/no-BOM/newline-empty/LF-only with exact rows",
      "preview source slot PASS",
      "APKG structure slot PASS",
      "APKG-STRUCTURE PASS: dynamic IDs, exact GUIDs, 3 distinct nids/ord0, one Card 1, selector CSS, LF TSV and zero media"
    ],
    "artifact_sha256": {
      "normal_card_improved_preview.html": "b45e89603c1aba172d0edd730f1b51bf6327efd741db173902893fab31548c4d",
      "exports/anki_previews/normal-card-improved-test.apkg": "6aae7f3ac61ef9ac79e0ff45856f1a24be00e95982a6da2c6c75ce2c206d7fbf",
      "exports/anki_previews/normal-card-improved-test.tsv": "a52fc303b03900f44531db3e5a9ace543f91cf34c2cbdc5daa1219432d07bc18"
    },
    "artifact_sizes_bytes": {
      "normal_card_improved_preview.html": 12836,
      "exports/anki_previews/normal-card-improved-test.apkg": 61658,
      "exports/anki_previews/normal-card-improved-test.tsv": 479
    },
    "sqlite_note_guids": [
      "HtYJ}S^5Rf",
      "JPd<d]p+7?",
      "Ll0a&a<R0n"
    ]
  },
  "commands_or_manual_steps": [
    {
      "slot_id": "improved-normal-card-preview-source",
      "kind": "automated",
      "command_or_step": "uv run --offline --no-sync --frozen --no-env-file python -c \"<Task 039-01 preview source validator from 039-PLAN.md>\"",
      "observed_output": "PREVIEW-SOURCE PASS: selector-bound full-width, hierarchy, clamp, audio focus/contrast and mobile declarations",
      "result": "pass"
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "kind": "automated",
      "command_or_step": "uv run --offline --no-sync --frozen --no-env-file python -c \"<preview source slot validation_command from 039-PLAN.md>\"",
      "observed_output": "preview source slot PASS",
      "result": "pass"
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "kind": "automated",
      "command_or_step": "uv run --offline --no-sync --frozen --no-env-file python -c \"<Task 039-02 ZIP/SQLite/TSV validator from 039-PLAN.md, with explicit SQLite close for Windows cleanup>\"",
      "observed_output": "APKG-STRUCTURE PASS: dynamic IDs, exact GUIDs, 3 distinct nids/ord0, one Card 1, selector CSS, LF TSV and zero media",
      "result": "pass"
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "kind": "automated",
      "command_or_step": "uv run --offline --no-sync --frozen --no-env-file python -c \"<APKG structure slot validation_command from 039-PLAN.md>\"",
      "observed_output": "APKG structure slot PASS",
      "result": "pass"
    },
    {
      "slot_id": "improved-normal-card-native-anki-appearance",
      "kind": "manual",
      "command_or_step": "Abrir exports/anki_previews/ no Explorer; importar normal-card-improved-test.apkg no Anki Desktop; abrir Multilang Improved Card Test; revisar Buch, Wasser e lernen na frente e no verso em largura ampla e com a janela reduzida até 420px ou menos; responder com aprovação ou problemas observados.",
      "observed_output": null,
      "result": "human_needed"
    }
  ],
  "observations": [
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "O preview contém exatamente um estado front e um back, nessa ordem, sem dependência ativa.",
      "route_state": "normal_card_improved_preview.html; data-window-state e data-card-state front/back.",
      "observation": "O parser encontrou exatamente duas janelas e dois article bodies em ordem front/back; não encontrou script, link, URL, src, href, Mustache ou elemento de mídia/embed.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; amostra alemã fixa; sem secrets, rede ou providers",
      "result": "pass",
      "claim_limit": "Prova source HTML, não pixels ou execução em WebView."
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "O shell é full-width e de altura natural.",
      "route_state": "Bloco BEGIN/END IMPROVED ANKI CSS, regras .card, #qa e .customCard.",
      "observation": ".card declara display block, width 100%, min-width/min-height 0 e margin 0; #qa declara width 100%/min-width 0; .customCard declara width 100%, max-width none, min-height 0, margin 0 e border-box, sem height.",
      "evidence_kind": "code",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; CSS estático sem dados privados",
      "result": "pass",
      "claim_limit": "Não mede largura computada no host Anki."
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "O conteúdo interno centraliza leitura até 900px com padding fluido.",
      "route_state": "Regra .cardContent no CSS compartilhado.",
      "observation": ".cardContent declara width 100%, max-width 900px, margin 0 auto e padding com dois clamp().",
      "evidence_kind": "test",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; CSS estático",
      "result": "pass",
      "claim_limit": "Prova declarações, não layout computado."
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "Palavra, definição, exemplo e tradução usam tipografia fluida própria.",
      "route_state": "Regras .targetWord, .definitionText, .exampleSentenceText e .sentenceTranslation.",
      "observation": "Cada um dos quatro seletores contém font-size: clamp(...); definição e tradução também possuem line-height explícito.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; CSS estático",
      "result": "pass",
      "claim_limit": "Não avalia rasterização ou fontes instaladas."
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "Hero, seções e breakpoint móvel têm espaçamento responsivo localizado.",
      "route_state": ".wordHero, .cardSections e @media (max-width: 420px).",
      "observation": ".wordHero e .cardSections usam gap com clamp; dentro do bloco 420px existem novos padding/gaps e .exampleSentenceLine usa align-items flex-start.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; CSS estático",
      "result": "pass",
      "claim_limit": "O breakpoint foi inspecionado no source, não renderizado."
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "Definição, heading, painel de exemplo e tradução possuem hierarquia dark distinguível.",
      "route_state": ".sectionHeading, .definitionText, .examplePanel e .sentenceTranslation.",
      "observation": "Heading possui família sans-serif, letter-spacing e uppercase; painel possui background, borda esquerda, radius e padding; tradução possui cor secundária, borda e line-height.",
      "evidence_kind": "code",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; CSS estático",
      "result": "pass",
      "claim_limit": "Contraste declarado não equivale a julgamento visual humano."
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "O controle visual de áudio é circular, contrastante e possui foco visível.",
      "route_state": ".replay-button, :focus-visible e svg path.",
      "observation": "O CSS declara mínimos 34x34px, radius 50%, fundo #233a57, borda #6aa9f4, texto #f5f9ff, outline 3px e fill currentColor; o preview contém quatro botões inertes.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; nenhum áudio ou playback",
      "result": "pass",
      "claim_limit": "Prova contrato visual do botão, não playback nativo."
    },
    {
      "slot_id": "improved-normal-card-preview-source",
      "claim": "Frente e verso simulados diferem somente pela visibilidade da tradução.",
      "route_state": "Bodies dos dois article.customCard, Translation hidden/visible.",
      "observation": "A normalização is-hidden/is-visible, hidden/visible e aria-hidden true/false tornou os dois bodies textualmente idênticos; /buːx/ aparece duas vezes e Image não é renderizada.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_improved_preview.html",
      "privacy": "local_only; amostra fixa",
      "result": "pass",
      "claim_limit": "Não prova comportamento do reveal no Anki."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "O APKG é um ZIP íntegro com exatamente uma collection permitida.",
      "route_state": "normal-card-improved-test.apkg aberto por ZipFile.read.",
      "observation": "ZipFile.testzip retornou None; existe exatamente collection.anki2 ou collection.anki21 e o inspector não usou extractall.",
      "evidence_kind": "test",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; archive gerado localmente",
      "result": "pass",
      "claim_limit": "Integridade ZIP não prova aparência nativa."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "A coleção contém exatamente três notes e três cards distintos em ord 0.",
      "route_state": "Tabelas notes e cards da collection SQLite temporária.",
      "observation": "Foram lidas três notes, três cards, três notes.id/cards.nid distintos e todos os cards usam ord 0 com nid correspondente a uma note.",
      "evidence_kind": "test",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; somente metadados estruturais",
      "result": "pass",
      "claim_limit": "Não executa o scheduler ou reviewer do Anki."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "Model e deck experimentais são isolados de produção.",
      "route_state": "models/decks JSON da tabela col.",
      "observation": "Todas as notes usam mid 1762801039 e nome Multilang::Card Improved Preview; todos os cards usam did 1762801040 e deck Multilang Improved Card Test; o scan dinâmico não encontrou esses IDs fora de quick039/outputs.",
      "evidence_kind": "code",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; IDs públicos experimentais",
      "result": "pass",
      "claim_limit": "Prova identidade armazenada, não uma importação real na coleção do usuário."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "Cada note possui GUID explícito, esperado e distinto.",
      "route_state": "notes.guid versus genanki.guid_for(note type, model ID, SortIndex, word).",
      "observation": "O conjunto SQLite tem três GUIDs distintos e corresponde exatamente aos valores recalculados para Buch, Wasser e lernen: HtYJ}S^5Rf, JPd<d]p+7? e Ll0a&a<R0n.",
      "evidence_kind": "test",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; GUIDs experimentais sem dados pessoais",
      "result": "pass",
      "claim_limit": "Não observa conflitos em uma coleção Anki externa."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "O model possui nove fields normais em ordem e um único Card 1.",
      "route_state": "model.flds e model.tmpls no SQLite.",
      "observation": "A ordem é SortIndex, word, IPA, Definitions, Example Sentence, Translation, word_audio, sentence_audio, Image; existe um único template Card 1 com ord 0.",
      "evidence_kind": "code",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; contrato de fields",
      "result": "pass",
      "claim_limit": "Não prova edição manual do note type no Anki."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "qfmt e afmt referenciam somente fields permitidos e usam reveal fixo.",
      "route_state": "Card 1 qfmt/afmt armazenados no model.",
      "observation": "qfmt não contém script, inclui IPA/Image condicionais, slots de áudio e Translation display:none; afmt é FrontSide seguido somente do getElementById fixo; não há innerHTML, URL/import, sound tag ou field desconhecido.",
      "evidence_kind": "test",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; templates estáticos",
      "result": "pass",
      "claim_limit": "Valida texto do template, não sua execução nativa."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "O CSS do model é textualmente igual ao bloco compartilhado do preview.",
      "route_state": "model.css versus comentários BEGIN/END do preview.",
      "observation": "A igualdade após strip passou e as assertions de shell, wrapper 900px, clamp, gaps, painel, botão e bloco 420px passaram novamente sobre model.css.",
      "evidence_kind": "test",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; CSS estático",
      "result": "pass",
      "claim_limit": "Igualdade textual não garante fidelidade visual do WebView."
    },
    {
      "slot_id": "improved-normal-card-apkg-structure",
      "claim": "APKG e TSV entregam exatamente as mesmas três linhas e nenhuma mídia.",
      "route_state": "notes.flds, TSV LF e manifesto media.",
      "observation": "TSV e notes coincidem para Buch, Wasser e lernen; cada row possui nove fields e os três finais vazios; TSV tem UTF-8 sem BOM, quatro LF e zero CR; media é {} e não há membro numérico.",
      "evidence_kind": "delivery",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.tsv",
      "privacy": "local_only; conteúdo didático fixo, sem mídia",
      "result": "pass",
      "claim_limit": "Entrega local estrutural; importação permanece pendente."
    },
    {
      "slot_id": "improved-normal-card-native-anki-appearance",
      "claim": "O APKG local está disponível para importação humana.",
      "route_state": "Explorer em exports/anki_previews/ e importação no Anki Desktop.",
      "observation": "O arquivo existe com 61658 bytes e SHA-256 6aae7f3ac61ef9ac79e0ff45856f1a24be00e95982a6da2c6c75ce2c206d7fbf, mas nenhuma importação foi observada.",
      "evidence_kind": "delivery",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; não publicar sem aprovação",
      "result": "human_needed",
      "claim_limit": "Disponibilidade local não prova que o Anki do usuário importou o pacote."
    },
    {
      "slot_id": "improved-normal-card-native-anki-appearance",
      "claim": "Frente e verso apresentam hierarquia dark e tradução revelada corretamente no Anki.",
      "route_state": "Reviewer do deck Multilang Improved Card Test, frente e verso dos três cards.",
      "observation": "Nenhum reviewer Anki nativo foi aberto nesta execução; o usuário precisa observar a frente e o verso.",
      "evidence_kind": "human",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "revisão local do usuário; não publicar captura sem consentimento",
      "result": "human_needed",
      "claim_limit": "Source e SQLite não substituem julgamento visual nativo."
    },
    {
      "slot_id": "improved-normal-card-native-anki-appearance",
      "claim": "Shell e conteúdo respondem corretamente em reviewer amplo e estreito.",
      "route_state": "Janela Anki ampla e reduzida até 420px ou menos.",
      "observation": "As regras responsivas estão no CSS, porém largura computada, overflow e altura natural no WebView não foram observados.",
      "evidence_kind": "human",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "revisão local do usuário",
      "result": "human_needed",
      "claim_limit": "Requer inspeção humana nas duas larguras."
    },
    {
      "slot_id": "improved-normal-card-native-anki-appearance",
      "claim": "Os três cards são legíveis e não exibem controles ou mídia vazios no pacote.",
      "route_state": "Buch, Wasser e lernen no reviewer Anki.",
      "observation": "Áudio e Image estão vazios por contrato, então o APKG não deve renderizar controle/mídia; o contrato dos botões foi provado apenas no preview/CSS e a legibilidade final ainda precisa de observação humana.",
      "evidence_kind": "delivery",
      "artifact_path": "exports/anki_previews/normal-card-improved-test.apkg",
      "privacy": "local_only; conteúdo fixo sem mídia",
      "result": "human_needed",
      "claim_limit": "Não há alegação de playback ou aparência observada."
    }
  ],
  "artifacts": [
    {
      "path": "normal_card_improved_preview.html",
      "visibility": "local_only",
      "retention": "Manter até aprovação ou descarte explícito da variante experimental.",
      "sensitivity": "low; amostra alemã fixa e CSS sem dados privados",
      "safe_to_publish": false
    },
    {
      "path": "exports/anki_previews/normal-card-improved-test.apkg",
      "visibility": "local_only",
      "retention": "Manter até revisão humana no Anki e decisão sobre a variante.",
      "sensitivity": "low; três cards fixos, sem áudio, imagem, secrets ou provider metadata",
      "safe_to_publish": false
    },
    {
      "path": "exports/anki_previews/normal-card-improved-test.tsv",
      "visibility": "local_only",
      "retention": "Manter junto ao APKG como companion textual.",
      "sensitivity": "low; conteúdo didático fixo",
      "safe_to_publish": false
    },
    {
      "path": ".planning/quick/039-preview-melhorado-anki/UI-PROOF.md",
      "visibility": "local_only",
      "retention": "Manter para o verifier e a decisão humana subsequente.",
      "sensitivity": "low; hashes e estado estrutural local sem secrets",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "classification": "local_only",
    "safe_to_publish": false,
    "network_contacted": false,
    "secrets_or_env_read": false,
    "external_assets": false,
    "provider_data": false,
    "reason": "O bundle contém paths e hashes de integridade do worktree; publicação exige revisão humana explícita."
  },
  "result": {
    "overall": "human_needed",
    "by_slot": {
      "improved-normal-card-preview-source": "pass",
      "improved-normal-card-apkg-structure": "pass",
      "improved-normal-card-native-anki-appearance": "human_needed"
    }
  },
  "claim_limits": {
    "automated": "Os validadores provam source do preview, conteúdo TSV e estrutura ZIP/SQLite do APKG.",
    "human_needed": "A aparência, legibilidade e responsividade no renderer nativo do Anki continuam human_needed até importação e observação do usuário.",
    "audio_and_image": "Como word_audio, sentence_audio e Image estão vazios, o APKG não demonstra playback nem mídia; os botões são provados no preview e no CSS.",
    "publication": "Nenhum artefato é considerado seguro para publicação sem aprovação explícita."
  },
  "source_integrity": {
    "policy": "user_authorized_explicit_rebaseline_after_concurrent_drift",
    "allowed_outputs": [
      ".planning/quick/039-preview-melhorado-anki/039-SUMMARY.md",
      ".planning/quick/039-preview-melhorado-anki/UI-PROOF.md",
      "exports/anki_previews/normal-card-improved-test.apkg",
      "exports/anki_previews/normal-card-improved-test.tsv",
      "normal_card_improved_preview.html"
    ],
    "original_baseline": {
      "preserved_at": "%LOCALAPPDATA%/Temp/opencode/quick-039-integrity-baseline-original.json",
      "head": "0664390fec7aa1d210438b3f7baa599f84cbbe01",
      "staged_diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "filtered_status_sha256": "8125ea1117b3292ba98a214af716a337b0daf562b1618677935862be05b05e36",
      "filtered_status_entry_count": 39,
      "repository_paths_sha256": "e8f50246056479475a36a129ae41f1cdd11ef3f0770e7c19f19a46315ba822b3",
      "repository_paths_count": 861,
      "uv_lock_sha256": "6e73a05c6b14abfe1d542d72005a4bb4d14f9ea0c8790f7d00c3eab572b5ae5f",
      "pyproject_sha256": "ad086568939eefc0573a374bcc29330bab2425756d06d71dd442474c93904f68"
    },
    "rebaseline": {
      "authorized": true,
      "authorized_at": "2026-07-29T16:44:24Z",
      "reason": "O usuário autorizou rebaseline explícito após drift concorrente fora de escopo; nenhum path concorrente foi alterado, revertido ou absorvido.",
      "original_to_rebaseline_different_keys": [
        "filtered_status_b64",
        "filtered_status_entry_count",
        "filtered_status_sha256",
        "repository_paths_count",
        "repository_paths_sha256"
      ],
      "drift_events": [
        {
          "path": "docs/multilingual-lexical-adaptive-plan-v4.md",
          "change": "Bytes mudaram entre o baseline original e o primeiro preproof; o status já era modified.",
          "disposition": "external_out_of_scope_preserved"
        },
        {
          "path": ".planning/quick/039-fechar-gaps-geracao-v4/039-SUMMARY.md",
          "change": "Arquivo concorrente foi criado entre baselines.",
          "disposition": "external_out_of_scope_preserved"
        },
        {
          "path": ".planning/quick/039-fechar-gaps-geracao-v4/039-VERIFICATION.md",
          "change": "Arquivo concorrente foi criado entre baselines.",
          "disposition": "external_out_of_scope_preserved"
        },
        {
          "path": ".planning/quick/LOG.md",
          "change": "Bytes mudaram entre baselines; o arquivo permaneceu fora do write set desta execução.",
          "disposition": "external_out_of_scope_preserved"
        }
      ]
    },
    "before": {
      "filtered_status_b64": "IE0gLnBsYW5uaW5nL3F1aWNrL0xPRy5tZAAgRCBkYW5pc2gtdGVzdC1kZWNrL2dlbmVyYXRpb24tcmVwb3J0Lmpzb24AIEQgZGFuaXNoLXRlc3QtZGVjay9nZW5lcmF0aW9uLXJlcG9ydC5tZAAgTSBkb2NzL211bHRpbGluZ3VhbC1sZXhpY2FsLWFkYXB0aXZlLXBsYW4tdjQubWQAIE0gc3JjL211bHRpbGFuZy90ZW1wbGF0ZXMvbm9ybWFsX2NhcmQubWQAIE0gdGVzdHMvc2VydmljZXMvdGVzdF9jYXJkX3RlbXBsYXRlX2xvYWRlci5weQAgTSB0ZXN0cy9zZXJ2aWNlcy90ZXN0X2V4cG9ydF9hbmtpX3BhY2thZ2UucHkAPz8gLnBsYW5uaW5nL2RlYnVnL25vcm1hbC1jYXJkLXRvby1zbWFsbC1pbi1hbmtpLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzMtZm9ybWFzLW5vLWRlY2stZGUtZnJlcXVlbmNpYS8wMzMtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDMzLWZvcm1hcy1uby1kZWNrLWRlLWZyZXF1ZW5jaWEvMDMzLVNVTU1BUlkubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzMy1mb3JtYXMtbm8tZGVjay1kZS1mcmVxdWVuY2lhLzAzMy1WRVJJRklDQVRJT04ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNS1jcmlhci1kZWNrLXRlc3RlLWFsZW1hby8wMzUtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM1LWNyaWFyLWRlY2stdGVzdGUtYWxlbWFvLzAzNS1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzUtY3JpYXItZGVjay10ZXN0ZS1hbGVtYW8vMDM1LVZFUklGSUNBVElPTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM2LWNyaWFyLW91dHJvLWRlY2stdGVzdGUtYWxlbWFvLzAzNi1QTEFOLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzYtY3JpYXItb3V0cm8tZGVjay10ZXN0ZS1hbGVtYW8vMDM2LVNVTU1BUlkubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNi1jcmlhci1vdXRyby1kZWNrLXRlc3RlLWFsZW1hby8wMzYtVkVSSUZJQ0FUSU9OLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1QTEFOLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1WRVJJRklDQVRJT04ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNy1wcmV2aWV3LWNhcmQtYW5raS1jb3JyaWdpZG8vVUktUFJPT0YubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzOC1jcmlhci10ZXJjZWlyby1kZWNrLXRlc3RlLWFsZW1hby8wMzgtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM4LWNyaWFyLXRlcmNlaXJvLWRlY2stdGVzdGUtYWxlbWFvLzAzOC1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzgtY3JpYXItdGVyY2Vpcm8tZGVjay10ZXN0ZS1hbGVtYW8vMDM4LVZFUklGSUNBVElPTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM5LWZlY2hhci1nYXBzLWdlcmFjYW8tdjQvMDM5LVBMQU4ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzOS1mZWNoYXItZ2Fwcy1nZXJhY2FvLXY0LzAzOS1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzktZmVjaGFyLWdhcHMtZ2VyYWNhby12NC8wMzktVkVSSUZJQ0FUSU9OLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzktcHJldmlldy1tZWxob3JhZG8tYW5raS8wMzktUExBTi5tZAA/PyBmcmVxX2NhcmRfaGVyb19kYXJrLmh0bWwAPz8gZ2VtaW5pLWNvZGUtMTc4NTE3ODA2MzU1OC5odG1sAD8/IGphcC1iYWNrLnBuZwA/PyBqYXAtZnJvbnQucG5nAD8/IGphcDEucG5nAD8/IGphcDIucG5nAD8/IGphcG9uZXNlLm1kAD8/IG5vcm1hbF9jYXJkX2Fua2lfY29ycmVjdGVkX3ByZXZpZXcuaHRtbAA/PyBub3JtYWxfY2FyZF9pbmxpbmVfbGlnaHRkYXJrLmh0bWwAPz8gcGhvbmVtZV9jYXJkX3Jlc3R5bGUuaHRtbAA/PyBwdDEucG5nAD8/IHB0Mi5wbmcAPz8gdW5pZmllZF90ZW1wbGF0ZXNfcHJldmlldy5odG1sAA==",
      "filtered_status_entry_count": 41,
      "filtered_status_sha256": "553c4f09e4b4c809e5ae47202ca62caca00080a658c99422bcadd3b3f0569858",
      "head": "0664390fec7aa1d210438b3f7baa599f84cbbe01",
      "pyproject_sha256": "ad086568939eefc0573a374bcc29330bab2425756d06d71dd442474c93904f68",
      "repository_paths_count": 863,
      "repository_paths_sha256": "9ff49dd653397d6d32022e513c3b4f9b5548819ecbf783eee5840031017ac0be",
      "staged_diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "uv_lock_sha256": "6e73a05c6b14abfe1d542d72005a4bb4d14f9ea0c8790f7d00c3eab572b5ae5f"
    },
    "after": {
      "filtered_status_b64": "IE0gLnBsYW5uaW5nL3F1aWNrL0xPRy5tZAAgRCBkYW5pc2gtdGVzdC1kZWNrL2dlbmVyYXRpb24tcmVwb3J0Lmpzb24AIEQgZGFuaXNoLXRlc3QtZGVjay9nZW5lcmF0aW9uLXJlcG9ydC5tZAAgTSBkb2NzL211bHRpbGluZ3VhbC1sZXhpY2FsLWFkYXB0aXZlLXBsYW4tdjQubWQAIE0gc3JjL211bHRpbGFuZy90ZW1wbGF0ZXMvbm9ybWFsX2NhcmQubWQAIE0gdGVzdHMvc2VydmljZXMvdGVzdF9jYXJkX3RlbXBsYXRlX2xvYWRlci5weQAgTSB0ZXN0cy9zZXJ2aWNlcy90ZXN0X2V4cG9ydF9hbmtpX3BhY2thZ2UucHkAPz8gLnBsYW5uaW5nL2RlYnVnL25vcm1hbC1jYXJkLXRvby1zbWFsbC1pbi1hbmtpLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzMtZm9ybWFzLW5vLWRlY2stZGUtZnJlcXVlbmNpYS8wMzMtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDMzLWZvcm1hcy1uby1kZWNrLWRlLWZyZXF1ZW5jaWEvMDMzLVNVTU1BUlkubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzMy1mb3JtYXMtbm8tZGVjay1kZS1mcmVxdWVuY2lhLzAzMy1WRVJJRklDQVRJT04ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNS1jcmlhci1kZWNrLXRlc3RlLWFsZW1hby8wMzUtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM1LWNyaWFyLWRlY2stdGVzdGUtYWxlbWFvLzAzNS1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzUtY3JpYXItZGVjay10ZXN0ZS1hbGVtYW8vMDM1LVZFUklGSUNBVElPTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM2LWNyaWFyLW91dHJvLWRlY2stdGVzdGUtYWxlbWFvLzAzNi1QTEFOLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzYtY3JpYXItb3V0cm8tZGVjay10ZXN0ZS1hbGVtYW8vMDM2LVNVTU1BUlkubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNi1jcmlhci1vdXRyby1kZWNrLXRlc3RlLWFsZW1hby8wMzYtVkVSSUZJQ0FUSU9OLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1QTEFOLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1WRVJJRklDQVRJT04ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNy1wcmV2aWV3LWNhcmQtYW5raS1jb3JyaWdpZG8vVUktUFJPT0YubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzOC1jcmlhci10ZXJjZWlyby1kZWNrLXRlc3RlLWFsZW1hby8wMzgtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM4LWNyaWFyLXRlcmNlaXJvLWRlY2stdGVzdGUtYWxlbWFvLzAzOC1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzgtY3JpYXItdGVyY2Vpcm8tZGVjay10ZXN0ZS1hbGVtYW8vMDM4LVZFUklGSUNBVElPTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM5LWZlY2hhci1nYXBzLWdlcmFjYW8tdjQvMDM5LVBMQU4ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzOS1mZWNoYXItZ2Fwcy1nZXJhY2FvLXY0LzAzOS1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzktZmVjaGFyLWdhcHMtZ2VyYWNhby12NC8wMzktVkVSSUZJQ0FUSU9OLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzktcHJldmlldy1tZWxob3JhZG8tYW5raS8wMzktUExBTi5tZAA/PyBmcmVxX2NhcmRfaGVyb19kYXJrLmh0bWwAPz8gZ2VtaW5pLWNvZGUtMTc4NTE3ODA2MzU1OC5odG1sAD8/IGphcC1iYWNrLnBuZwA/PyBqYXAtZnJvbnQucG5nAD8/IGphcDEucG5nAD8/IGphcDIucG5nAD8/IGphcG9uZXNlLm1kAD8/IG5vcm1hbF9jYXJkX2Fua2lfY29ycmVjdGVkX3ByZXZpZXcuaHRtbAA/PyBub3JtYWxfY2FyZF9pbmxpbmVfbGlnaHRkYXJrLmh0bWwAPz8gcGhvbmVtZV9jYXJkX3Jlc3R5bGUuaHRtbAA/PyBwdDEucG5nAD8/IHB0Mi5wbmcAPz8gdW5pZmllZF90ZW1wbGF0ZXNfcHJldmlldy5odG1sAA==",
      "filtered_status_entry_count": 41,
      "filtered_status_sha256": "553c4f09e4b4c809e5ae47202ca62caca00080a658c99422bcadd3b3f0569858",
      "head": "0664390fec7aa1d210438b3f7baa599f84cbbe01",
      "pyproject_sha256": "ad086568939eefc0573a374bcc29330bab2425756d06d71dd442474c93904f68",
      "repository_paths_count": 863,
      "repository_paths_sha256": "9ff49dd653397d6d32022e513c3b4f9b5548819ecbf783eee5840031017ac0be",
      "staged_diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "uv_lock_sha256": "6e73a05c6b14abfe1d542d72005a4bb4d14f9ea0c8790f7d00c3eab572b5ae5f"
    },
    "live": {
      "filtered_status_b64": "IE0gLnBsYW5uaW5nL3F1aWNrL0xPRy5tZAAgRCBkYW5pc2gtdGVzdC1kZWNrL2dlbmVyYXRpb24tcmVwb3J0Lmpzb24AIEQgZGFuaXNoLXRlc3QtZGVjay9nZW5lcmF0aW9uLXJlcG9ydC5tZAAgTSBkb2NzL211bHRpbGluZ3VhbC1sZXhpY2FsLWFkYXB0aXZlLXBsYW4tdjQubWQAIE0gc3JjL211bHRpbGFuZy90ZW1wbGF0ZXMvbm9ybWFsX2NhcmQubWQAIE0gdGVzdHMvc2VydmljZXMvdGVzdF9jYXJkX3RlbXBsYXRlX2xvYWRlci5weQAgTSB0ZXN0cy9zZXJ2aWNlcy90ZXN0X2V4cG9ydF9hbmtpX3BhY2thZ2UucHkAPz8gLnBsYW5uaW5nL2RlYnVnL25vcm1hbC1jYXJkLXRvby1zbWFsbC1pbi1hbmtpLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzMtZm9ybWFzLW5vLWRlY2stZGUtZnJlcXVlbmNpYS8wMzMtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDMzLWZvcm1hcy1uby1kZWNrLWRlLWZyZXF1ZW5jaWEvMDMzLVNVTU1BUlkubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzMy1mb3JtYXMtbm8tZGVjay1kZS1mcmVxdWVuY2lhLzAzMy1WRVJJRklDQVRJT04ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNS1jcmlhci1kZWNrLXRlc3RlLWFsZW1hby8wMzUtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM1LWNyaWFyLWRlY2stdGVzdGUtYWxlbWFvLzAzNS1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzUtY3JpYXItZGVjay10ZXN0ZS1hbGVtYW8vMDM1LVZFUklGSUNBVElPTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM2LWNyaWFyLW91dHJvLWRlY2stdGVzdGUtYWxlbWFvLzAzNi1QTEFOLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzYtY3JpYXItb3V0cm8tZGVjay10ZXN0ZS1hbGVtYW8vMDM2LVNVTU1BUlkubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNi1jcmlhci1vdXRyby1kZWNrLXRlc3RlLWFsZW1hby8wMzYtVkVSSUZJQ0FUSU9OLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1QTEFOLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzctcHJldmlldy1jYXJkLWFua2ktY29ycmlnaWRvLzAzNy1WRVJJRklDQVRJT04ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzNy1wcmV2aWV3LWNhcmQtYW5raS1jb3JyaWdpZG8vVUktUFJPT0YubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzOC1jcmlhci10ZXJjZWlyby1kZWNrLXRlc3RlLWFsZW1hby8wMzgtUExBTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM4LWNyaWFyLXRlcmNlaXJvLWRlY2stdGVzdGUtYWxlbWFvLzAzOC1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzgtY3JpYXItdGVyY2Vpcm8tZGVjay10ZXN0ZS1hbGVtYW8vMDM4LVZFUklGSUNBVElPTi5tZAA/PyAucGxhbm5pbmcvcXVpY2svMDM5LWZlY2hhci1nYXBzLWdlcmFjYW8tdjQvMDM5LVBMQU4ubWQAPz8gLnBsYW5uaW5nL3F1aWNrLzAzOS1mZWNoYXItZ2Fwcy1nZXJhY2FvLXY0LzAzOS1TVU1NQVJZLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzktZmVjaGFyLWdhcHMtZ2VyYWNhby12NC8wMzktVkVSSUZJQ0FUSU9OLm1kAD8/IC5wbGFubmluZy9xdWljay8wMzktcHJldmlldy1tZWxob3JhZG8tYW5raS8wMzktUExBTi5tZAA/PyBmcmVxX2NhcmRfaGVyb19kYXJrLmh0bWwAPz8gZ2VtaW5pLWNvZGUtMTc4NTE3ODA2MzU1OC5odG1sAD8/IGphcC1iYWNrLnBuZwA/PyBqYXAtZnJvbnQucG5nAD8/IGphcDEucG5nAD8/IGphcDIucG5nAD8/IGphcG9uZXNlLm1kAD8/IG5vcm1hbF9jYXJkX2Fua2lfY29ycmVjdGVkX3ByZXZpZXcuaHRtbAA/PyBub3JtYWxfY2FyZF9pbmxpbmVfbGlnaHRkYXJrLmh0bWwAPz8gcGhvbmVtZV9jYXJkX3Jlc3R5bGUuaHRtbAA/PyBwdDEucG5nAD8/IHB0Mi5wbmcAPz8gdW5pZmllZF90ZW1wbGF0ZXNfcHJldmlldy5odG1sAA==",
      "filtered_status_entry_count": 41,
      "filtered_status_sha256": "553c4f09e4b4c809e5ae47202ca62caca00080a658c99422bcadd3b3f0569858",
      "head": "0664390fec7aa1d210438b3f7baa599f84cbbe01",
      "pyproject_sha256": "ad086568939eefc0573a374bcc29330bab2425756d06d71dd442474c93904f68",
      "repository_paths_count": 863,
      "repository_paths_sha256": "9ff49dd653397d6d32022e513c3b4f9b5548819ecbf783eee5840031017ac0be",
      "staged_diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "uv_lock_sha256": "6e73a05c6b14abfe1d542d72005a4bb4d14f9ea0c8790f7d00c3eab572b5ae5f"
    }
  }
}
```
