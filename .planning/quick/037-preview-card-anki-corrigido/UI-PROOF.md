# UI Proof: Preview do card Anki corrigido

```json
{
  "proof_bundle_version": "1.0",
  "scope": {
    "work_item": "quick-037-preview-card-anki-corrigido",
    "requirement_ids": [],
    "slot_ids": [
      "normal-card-anki-corrected-source-proof"
    ],
    "slot_id": "normal-card-anki-corrected-source-proof",
    "claim": "O HTML standalone declara exatamente duas janelas simuladas, uma frente e um verso, com cards fluidos que seguem a altura do conteúdo, fundo de viewport separado e visível abaixo deles, tradução oculta/visível por estado, layout responsivo e nenhuma dependência ativa ou externa.",
    "evidence_kinds": [
      "code",
      "test"
    ],
    "status": "complete_source_only"
  },
  "route_state": "Inspecionar normal_card_anki_corrected_preview.html localmente em data-window-state/data-card-state front e back; nenhuma rota da aplicação ou execução em Anki nativo participa desta evidência.",
  "environment": {
    "kind": "offline_source_inspection",
    "tools_used": [
      "Python standard library",
      "Git read-only inspection"
    ],
    "network_used": false,
    "agent_browser_available": false,
    "agent_browser_used": false,
    "browser_automation_used": false,
    "native_browser_used": false,
    "native_anki_used": false,
    "visual_rendering_observed": false,
    "status": "completed_without_rendering"
  },
  "viewport": {
    "wide_source_contract": "Acima de 980px, .preview-grid declara duas colunas de largura fluida.",
    "narrow_source_contract": "Em 980px ou menos, .preview-grid declara uma coluna.",
    "simulated_anki_viewport_contract": ".anki-viewport declara min-height de 620px e padding 12px/8px para separar, no CSS fonte, o fundo da página do card de altura natural.",
    "rendered_viewport_claimed": false
  },
  "evidence_inputs": {
    "kinds": [
      "code",
      "test"
    ],
    "inspected_files": [
      "normal_card_anki_corrected_preview.html",
      "src/multilang/templates/normal_card.md",
      ".planning/quick/037-preview-card-anki-corrigido/037-PLAN.md"
    ],
    "tools_used": [
      "python-stdlib",
      "git-read-only"
    ],
    "status": "complete"
  },
  "commands_or_manual_steps": [
    {
      "command": "PYTHONIOENCODING=utf-8 python -c \"import re,shlex,subprocess; from pathlib import Path; text=Path('.planning/quick/037-preview-card-anki-corrigido/037-PLAN.md').read_text(encoding='utf-8'); command=re.findall(r'<automated>(.*?)</automated>',text,re.S)[0]; result=subprocess.run(shlex.split(command,posix=True)); raise SystemExit(result.returncode)\"",
      "purpose": "Executar sem reescrita e sem shell expansion o primeiro comando automated do plano, que é o validation_command exato do slot.",
      "output": "corrected preview contract OK: 2 windows/cards, content-height fluid cards, separate viewport background, front/back translation, responsive and offline",
      "result": "pass",
      "claim_limit": "Validação de texto-fonte HTML/CSS; nenhuma renderização foi aberta ou observada."
    },
    {
      "command": "python -c \"import re; from pathlib import Path; s=Path('normal_card_anki_corrected_preview.html').read_text(encoding='utf-8'); rule=re.search(r'\\.customCard\\s*\\{([^}]*)\\}',s,re.I|re.S); assert rule and re.search(r'box-sizing\\s*:\\s*border-box\\s*;',rule.group(1),re.I); print('must-have box sizing OK: .customCard declares border-box')\"",
      "purpose": "Resolver e validar explicitamente o aviso must_have de box sizing sem ampliar o escopo.",
      "output": "must-have box sizing OK: .customCard declares border-box",
      "result": "pass",
      "claim_limit": "Confirma somente a declaração CSS source-only em .customCard."
    },
    {
      "command": "PYTHONIOENCODING=utf-8 python -c \"import re,shlex,subprocess; from pathlib import Path; text=Path('.planning/quick/037-preview-card-anki-corrigido/037-PLAN.md').read_text(encoding='utf-8'); command=re.findall(r'<automated>(.*?)</automated>',text,re.S)[1]; result=subprocess.run(shlex.split(command,posix=True)); raise SystemExit(result.returncode)\"",
      "purpose": "Executar sem reescrita e sem shell expansion o validador local do bundle definido no plano.",
      "output": "UI proof OK: complete, source integrity preserved, claim source-only",
      "result": "pass",
      "claim_limit": "Passe do validador Python local do plano; não é um passe do validador GSDD nem uma prova visual."
    },
    {
      "command": "git diff --check -- \"normal_card_anki_corrected_preview.html\" \".planning/quick/037-preview-card-anki-corrigido/037-PLAN.md\" \".planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md\"",
      "purpose": "Executar o check de whitespace solicitado pelo plano.",
      "output": "sem saída; exit code 0",
      "result": "pass",
      "claim_limit": "O comando Git é somente leitura e não faz staging."
    },
    {
      "command": "git diff --cached --exit-code -- \"normal_card_anki_corrected_preview.html\" \".planning/quick/037-preview-card-anki-corrigido\" \"src/multilang/templates/normal_card.md\" \"tests\" \".planning/debug/normal-card-too-small-in-anki.md\" \"pt1.png\" \"pt2.png\" \"normal_card_gemini_preview.html\" \".planning/quick/LOG.md\" \".planning/ROADMAP.md\" \".planning/SPEC.md\"",
      "purpose": "Confirmar que nenhum caminho protegido ou desta quick task entrou no staging.",
      "output": "sem saída; exit code 0",
      "result": "pass",
      "claim_limit": "Confirma somente ausência de delta staged nos caminhos enumerados."
    },
    {
      "command": "python -c \"import hashlib; from pathlib import Path; p=Path('src/multilang/templates/normal_card.md'); print(hashlib.sha256(p.read_bytes()).hexdigest())\"",
      "purpose": "Calcular SHA-256 dos bytes de normal_card.md antes, depois e no estado live final.",
      "runs": 3,
      "output": "e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97 em todas as execuções",
      "result": "pass",
      "claim_limit": "Integridade byte a byte do arquivo protegido; não valida comportamento de produção."
    },
    {
      "command": "git status --short",
      "purpose": "Comparar o status final com o baseline capturado antes da escrita.",
      "runs": 2,
      "output": "As entradas concorrentes/protegidas mantiveram o mesmo status; surgiu somente normal_card_anki_corrected_preview.html na raiz, enquanto o diretório quick 037 já aparecia como untracked no baseline.",
      "result": "pass",
      "claim_limit": "Comparação de status Git e write set; não atribui nem altera mudanças concorrentes."
    },
    {
      "command": "command -v gsdd; command -v agent-browser",
      "purpose": "Verificar a disponibilidade dos validadores/runners de closure sem instalá-los.",
      "output": "gsdd CLI indisponível; agent-browser indisponível",
      "result": "not_used",
      "claim_limit": "Nenhum passe GSDD ou browser é alegado."
    }
  ],
  "observations": [
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Estrutura determinística das janelas",
      "route_state": "Fonte local, estados front/back em ordem",
      "observation": "O parser encontrou exatamente duas .anki-window, abertas em ordem front e back.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "Conteúdo representativo fixo, sem dados pessoais.",
      "result": "pass",
      "claim_limit": "Contagem e ordem no source HTML; sem inspeção visual."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Estrutura determinística dos cards",
      "route_state": "Fonte local, articles front/back em ordem",
      "observation": "O parser encontrou exatamente dois articles customCard cardBack, um por viewport, em ordem front e back.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "Conteúdo representativo fixo, sem dados pessoais.",
      "result": "pass",
      "claim_limit": "Estrutura declarada; não prova layout computado."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Corpos front/back espelhados",
      "route_state": "Comparação textual dos dois article bodies",
      "observation": "Depois de normalizar apenas is-hidden/is-visible, hidden/visible e aria-hidden true/false, os corpos são idênticos.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "Nenhum dado privado processado.",
      "result": "pass",
      "claim_limit": "Equivalência textual source-only."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Tradução por estado sem JavaScript",
      "route_state": "Front hidden e back visible",
      "observation": "A frente declara sentenceTranslation is-hidden/hidden/true, o verso is-visible/visible/false, e o CSS mapeia as classes para display none/block.",
      "evidence_kind": "code",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "Texto de exemplo fixo e não sensível.",
      "result": "pass",
      "claim_limit": "Declarações de estado e CSS; nenhuma interação/renderização observada."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Card fluido com altura natural",
      "route_state": "Regra base .customCard",
      "observation": ".customCard declara display block, width 100%, max-width none e min-height 0, sem height, flex-grow ou calc(100vh).",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "CSS local sem conteúdo sensível.",
      "result": "pass",
      "claim_limit": "Propriedades declaradas no CSS source-only."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Box model explícito",
      "route_state": "Regra base .customCard",
      "observation": ".customCard declara box-sizing: border-box, resolvendo o aviso must_have do checker.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "CSS local sem conteúdo sensível.",
      "result": "pass",
      "claim_limit": "Validação literal da declaração; sem medição de pixels."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Background de viewport separado",
      "route_state": "Regra base .anki-viewport",
      "observation": ".anki-viewport declara display block, min-height 620px, padding 12px e background da página, separado do background do card.",
      "evidence_kind": "code",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "CSS local sem conteúdo sensível.",
      "result": "pass",
      "claim_limit": "Contrato CSS fonte; não se alega que a área foi visualmente renderizada."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Responsividade declarada",
      "route_state": "Media queries 980px e 420px",
      "observation": "A grade declara duas colunas fluidas e muda para uma em 980px; em 420px somente os paddings da viewport e do card mudam para 8px e 22px 18px.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "CSS local sem conteúdo sensível.",
      "result": "pass",
      "claim_limit": "Breakpoints declarados; nenhuma viewport real foi aberta."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Conteúdo alemão exigido",
      "route_state": "Ambos os article bodies",
      "observation": "Buch, /buːx/, noun: book, a frase alemã e a tradução portuguesa aparecem nos dois corpos; há exatamente quatro indicadores Unicode ▶.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "Frases representativas fixas, sem dados pessoais.",
      "result": "pass",
      "claim_limit": "Presença textual e semântica; não prova reprodução de áudio."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Estilo Gemini espelhado",
      "route_state": "Tokens e regras CSS inline",
      "observation": "O validador confirmou paleta, Georgia/Cambria/serif, sans-serif em labels/IPA, borda, raio, sombra, palavra 38px/600, definição 16px/1.6 e exemplo/tradução 16px/1.5.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "CSS local sem conteúdo sensível.",
      "result": "pass",
      "claim_limit": "Conformidade de source; não prova fonte instalada, pixels ou gosto visual."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Standalone inerte e offline",
      "route_state": "Scan negativo do HTML completo",
      "observation": "O scan não encontrou script, link, mídia/embed, src/href, @import, url(...), HTTP(S) ou placeholders Anki.",
      "evidence_kind": "test",
      "artifact_path": "normal_card_anki_corrected_preview.html",
      "privacy": "Nenhuma rede, segredo ou asset externo envolvido.",
      "result": "pass",
      "claim_limit": "Scan textual dos padrões proibidos."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Integridade da fonte protegida",
      "route_state": "SHA-256 antes/depois/live de normal_card.md",
      "observation": "Os três hashes SHA-256 são e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97.",
      "evidence_kind": "test",
      "artifact_path": "src/multilang/templates/normal_card.md",
      "privacy": "Somente hash criptográfico do arquivo local.",
      "result": "pass",
      "claim_limit": "Prova preservação byte a byte durante a quick task, não correção funcional do template."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Limite de closure preservado",
      "route_state": "Ambiente source-only sem browser",
      "observation": "agent-browser e browser nativo não foram usados; Anki nativo também não foi usado e nenhuma renderização visual foi observada.",
      "evidence_kind": "code",
      "artifact_path": ".planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md",
      "privacy": "Nenhum screenshot, trace ou dado de sessão foi produzido.",
      "result": "pass",
      "claim_limit": "O pass vale exclusivamente para estrutura e CSS source-only."
    },
    {
      "slot_id": "normal-card-anki-corrected-source-proof",
      "claim": "Write set e estado Git preservados",
      "route_state": "Comparação git status baseline/final",
      "observation": "Os caminhos concorrentes e protegidos mantiveram o status inicial, nenhum delta staged surgiu e apenas o novo preview foi acrescentado como caminho raiz desta tarefa.",
      "evidence_kind": "test",
      "artifact_path": ".planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md",
      "privacy": "Somente nomes de caminhos relativos do repositório; nenhuma publicação aprovada.",
      "result": "pass",
      "claim_limit": "Preservação durante esta execução; mudanças preexistentes continuam pertencendo ao trabalho concorrente."
    }
  ],
  "artifacts": [
    {
      "path": "normal_card_anki_corrected_preview.html",
      "type": "standalone HTML source",
      "visibility": "local_only",
      "retention": "project_worktree",
      "sensitivity": "none_fixed_representative_content",
      "safe_to_publish": false,
      "status": "validated_source_only"
    },
    {
      "path": ".planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md",
      "type": "source-only proof bundle",
      "visibility": "local_only",
      "retention": "quick_task_record",
      "sensitivity": "none_source_metadata_only",
      "safe_to_publish": false,
      "status": "validated_by_local_plan_checker"
    },
    {
      "path": "src/multilang/templates/normal_card.md",
      "type": "protected production source inspected by SHA-256",
      "visibility": "local_only",
      "retention": "project_source",
      "sensitivity": "none_source_hash_recorded",
      "safe_to_publish": false,
      "status": "byte_integrity_preserved"
    }
  ],
  "privacy": {
    "data_classification": "non_sensitive_fixed_example_and_source_metadata",
    "raw_artifacts_safe_to_publish": false,
    "retention": "local project worktree and quick-task record",
    "contains_personal_data": false,
    "contains_secrets": false,
    "contains_private_paths": false,
    "contains_screenshots_or_traces": false,
    "publication_approved": false
  },
  "result": "pass",
  "claim_limits": [
    "Claim source-only: o bundle prova somente a estrutura HTML/CSS declarada, os resultados dos validadores locais e a integridade da fonte protegida.",
    "Não prova Anki nativo, pixels, aparência computada, fontes instaladas, gosto visual, áudio ou fidelidade de WebView Desktop/mobile.",
    "A responsividade e a área de background abaixo do card são alegadas somente como contratos CSS declarados, sem viewport renderizada.",
    "agent-browser e browser nativo não foram usados; nenhuma renderização visual foi observada.",
    "O comando standalone gsdd ui-proof validate não está disponível neste runtime; nenhum passe GSDD é alegado."
  ],
  "source_integrity": {
    "path": "src/multilang/templates/normal_card.md",
    "algorithm": "sha256",
    "before_sha256": "e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97",
    "after_sha256": "e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97",
    "live_final_sha256": "e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97"
  },
  "closure_validation": {
    "local_plan_validators": "pass",
    "gsdd_cli_available": false,
    "gsdd_pass_claimed": false,
    "agent_browser_available": false,
    "agent_browser_used": false,
    "native_browser_used": false,
    "native_anki_used": false,
    "visual_rendering_observed": false,
    "project_local_helper_probe": "O helper node .planning/bin/gsdd.mjs foi sondado antes da execução e rejeitou o bundle pending, além de exigir result.comparison_status_by_slot; o contrato local aprovado exige result como string pass. Por isso ele não foi usado como evidência de closure e nenhum passe GSDD foi inventado.",
    "validator_invocation_note": "Uma primeira tentativa de encaminhar o segundo comando por bash falhou porque os backticks do code fence sofreram command substitution. A execução registrada usa shlex e subprocess sem shell, preserva o código do plano como argumento literal e passou."
  }
}
```
