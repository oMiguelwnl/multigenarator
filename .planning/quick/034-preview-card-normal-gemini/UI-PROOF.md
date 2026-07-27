# UI Proof: Normal Card Gemini Preview

```json
{
  "proof_bundle_version": "1.0",
  "scope": {
    "slot_id": "normal-gemini-preview-source-proof",
    "claim": "The standalone root preview declares representative normal-card front and back states side by side at wide widths, a one-column narrow-width fallback, mirrored Gemini styling, front-only Translation hiding, and no script or external dependency.",
    "evidence_kinds": [
      "code",
      "test"
    ]
  },
  "route_state": "Inspect normal_card_gemini_preview.html as a local standalone document containing data-state=front followed by data-state=back; no application route or native Anki runtime is involved.",
  "environment": {
    "kind": "offline_source_inspection",
    "tools": [
      "Python standard library",
      "Git read-only integrity commands"
    ],
    "network_used": false,
    "browser_automation_used": false,
    "native_anki_used": false
  },
  "viewport": {
    "wide_source_contract": "Above 980px, .preview-grid declares repeat(2, minmax(0, 460px)).",
    "narrow_source_contract": "At or below 980px, the media query declares grid-template-columns: 1fr.",
    "rendered_viewport_claimed": false
  },
  "evidence_inputs": [
    {
      "path": "normal_card_gemini_preview.html",
      "kind": "code",
      "purpose": "Standalone preview source"
    },
    {
      "path": "src/multilang/templates/normal_card.md",
      "kind": "code",
      "purpose": "Read-only source of effective Gemini declarations and integrity target"
    },
    {
      "path": ".planning/quick/034-preview-card-normal-gemini/034-PLAN.md",
      "kind": "code",
      "purpose": "Preview contract and authoritative local validator"
    }
  ],
  "commands_or_manual_steps": [
    {
      "kind": "test",
      "command": "python -c \"import re; from pathlib import Path; s=Path('normal_card_gemini_preview.html').read_text(encoding='utf-8'); lt=chr(60); articles=re.findall(lt+r'article class=\\\"preview-card\\\" data-state=\\\"(front|back)\\\"[^>]*>(.*?)'+lt+r'/article>',s,re.I|re.S); assert len(re.findall(lt+r'article\\b',s,re.I))==2 and len(articles)==2; assert [state for state,_ in articles]==['front','back']; front,back=(body for _,body in articles); assert 'class=\\\"translation is-hidden\\\"' in front and 'data-translation-state=\\\"hidden\\\"' in front; assert 'class=\\\"translation is-visible\\\"' in back and 'data-translation-state=\\\"visible\\\"' in back; assert front.replace('is-hidden','is-visible').replace('\\\"hidden\\\"','\\\"visible\\\"').replace('aria-hidden=\\\"true\\\"','aria-hidden=\\\"false\\\"')==back; assert re.search(r'\\.is-hidden\\s*\\{[^}]*display\\s*:\\s*none',s,re.I|re.S) and re.search(r'\\.is-visible\\s*\\{[^}]*display\\s*:\\s*block',s,re.I|re.S); required=('#121212','#1E1E1E','#EAEAEA','#A0A0A0','#333333','Georgia, Cambria, \\\"Times New Roman\\\", Times, serif','max-width: 460px','padding: 28px 24px','border-radius: 8px','box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5)','font-size: 38px','grid-template-columns: repeat(2, minmax(0, 460px))','@media (max-width: 980px)','grid-template-columns: 1fr'); assert all(token in s for token in required),[token for token in required if token not in s]; forbidden=(lt+r'script\\b',lt+r'link\\b',r'\\b(?:src|href)\\s*=',r'@import\\b',r'url\\s*\\(',r'https?://'); assert not any(re.search(p,s,re.I) for p in forbidden),[p for p in forbidden if re.search(p,s,re.I)]; print('preview contract OK: exactly 2 mirrored cards, front hidden, back visible, responsive, offline, script-free')\"",
      "exit_code": 0,
      "output": "preview contract OK: exactly 2 mirrored cards, front hidden, back visible, responsive, offline, script-free"
    },
    {
      "kind": "code",
      "command": "sha256sum src/multilang/templates/normal_card.md",
      "exit_code": 0,
      "output": "a994cd4eaccd70fbab8650c89a82c4234c7109d5a6119464674f8b322f1f5040"
    }
  ],
  "observations": [
    {
      "id": "OBS-01",
      "evidence_kind": "test",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "The validator found exactly two preview-card article elements in deterministic front-then-back order."
    },
    {
      "id": "OBS-02",
      "evidence_kind": "test",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "The validator proved the two article bodies are byte-identical after replacing only the three Translation visibility tokens."
    },
    {
      "id": "OBS-03",
      "evidence_kind": "code",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "The front Translation uses class translation is-hidden, data-translation-state hidden, and aria-hidden true; .is-hidden declares display none."
    },
    {
      "id": "OBS-04",
      "evidence_kind": "code",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "The back Translation uses class translation is-visible, data-translation-state visible, and aria-hidden false; .is-visible declares display block."
    },
    {
      "id": "OBS-05",
      "evidence_kind": "code",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "Both mirrored bodies contain saudade, /sawˈdadʒi/, two definitions, the Portuguese example, the English Translation, and separate Unicode word and sentence audio indicators with accessible labels."
    },
    {
      "id": "OBS-06",
      "evidence_kind": "test",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "Literal source checks found page #121212, card #1E1E1E, primary #EAEAEA, muted #A0A0A0, divider #333333, the Georgia/Cambria serif stack, 460px card maximum, 28px 24px padding, 8px radius, the specified shadow, and a 38px target word."
    },
    {
      "id": "OBS-07",
      "evidence_kind": "code",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "The wide source contract uses a centered grid with grid-template-columns repeat(2, minmax(0, 460px))."
    },
    {
      "id": "OBS-08",
      "evidence_kind": "code",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "The @media max-width 980px override switches the grid to one fraction column while width, max-width, min-width, overflow, and border-box declarations contain narrow layouts."
    },
    {
      "id": "OBS-09",
      "evidence_kind": "test",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "The forbidden-source scan found no script or link elements, src or href attributes, CSS imports or URL functions, or HTTP(S) references."
    },
    {
      "id": "OBS-10",
      "evidence_kind": "code",
      "artifact": "normal_card_gemini_preview.html",
      "observation": "No image block is present, matching the normal card's empty-Image case, and the audio indicators are non-interactive spans rather than playback controls."
    },
    {
      "id": "OBS-11",
      "evidence_kind": "test",
      "artifact": "src/multilang/templates/normal_card.md",
      "observation": "The protected production template SHA-256 was a994cd4eaccd70fbab8650c89a82c4234c7109d5a6119464674f8b322f1f5040 before and after preview creation and equals the recorded live hash."
    }
  ],
  "artifacts": [
    {
      "path": "normal_card_gemini_preview.html",
      "type": "HTML source inspection",
      "visibility": "repository_worktree",
      "retention": "project_lifecycle",
      "sensitivity": "none_fixed_representative_content",
      "safe_to_publish": true
    },
    {
      "path": ".planning/quick/034-preview-card-normal-gemini/UI-PROOF.md",
      "type": "Source proof bundle",
      "visibility": "repository_worktree",
      "retention": "project_lifecycle",
      "sensitivity": "none_command_and_source_metadata_only",
      "safe_to_publish": true
    }
  ],
  "privacy": {
    "contains_personal_data": false,
    "contains_secrets": false,
    "contains_private_paths": false,
    "content_policy": "Only fixed representative vocabulary-card content, repository-relative paths, source observations, and a production-template digest are recorded."
  },
  "result": "pass",
  "claim_limits": [
    "This proof is source-only: it does not establish computed pixels, installed-font rendering, visual taste, accessibility acceptance, audio playback, browser-engine fidelity, or native Anki Desktop/mobile WebView behavior.",
    "Responsive behavior is established only as declared CSS structure; no rendered viewport or pixel comparison was attempted.",
    "Worktree-integrity claims are limited to the equal before/after/live SHA-256 of src/multilang/templates/normal_card.md, the relevant staged-diff command, and the named command outputs. The pre-existing concurrently dirty worktree was not globally fingerprinted, frozen, or claimed complete."
  ],
  "source_integrity": {
    "path": "src/multilang/templates/normal_card.md",
    "algorithm": "sha256",
    "normal_card_before_sha256": "a994cd4eaccd70fbab8650c89a82c4234c7109d5a6119464674f8b322f1f5040",
    "normal_card_after_sha256": "a994cd4eaccd70fbab8650c89a82c4234c7109d5a6119464674f8b322f1f5040",
    "live_final_sha256": "a994cd4eaccd70fbab8650c89a82c4234c7109d5a6119464674f8b322f1f5040"
  },
  "warnings": [
    "Non-blocking plan-check warning: evidence is source-only and intentionally does not attempt pixel rendering or native Anki proof.",
    "Non-blocking plan-check warning: statements about the concurrent dirty worktree are bounded to the template hash and explicit commands; no complete-worktree preservation claim is inferred."
  ]
}
```
