---
mode: quick
phase: quick-037-preview-card-anki-corrigido
task: 037-preview-card-anki-corrigido
plan: 037
type: execute
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
autonomous: true
task_count: 1
requirements: []
files_modified:
  - normal_card_anki_corrected_preview.html
  - .planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/ está vazio; este plano aplica diretamente o contrato quick fornecido pelo usuário."
non_goals:
  - "Não modificar produção, testes, o artefato de debug, pt1.png, pt2.png, previews anteriores ou qualquer arquivo concorrente."
  - "Não executar nem alegar fidelidade em Anki nativo, comparação de pixels, aparência computada ou reprodução de áudio."
  - "Não adicionar scripts, rede, bibliotecas, fontes, imagens ou outros assets externos."
hard_boundaries:
  - "A execução pode escrever somente o novo preview raiz e o UI-PROOF desta quick task; o executor cria 037-SUMMARY.md separadamente após concluir a tarefa."
  - "src/multilang/templates/normal_card.md é fonte de inspeção somente e deve permanecer byte a byte inalterado."
  - "Não editar LOG.md, ROADMAP.md ou SPEC.md; não fazer stage, commit, restore, clean, delete ou reformatação fora do write set."
anti_regression_targets:
  - "A largura fluida e os paddings efetivos do template atual são espelhados sem reintroduzir max-width de 460px ou min-height de viewport no card."
  - "O card termina pelo fluxo natural do conteúdo, enquanto a viewport simulada mantém área visível com o background separado da página."
  - "Frente e verso têm conteúdo idêntico; somente o estado de visibilidade da tradução difere."
closure_claim_limit: "A evidência pode provar apenas a estrutura e o CSS declarados no arquivo standalone, sua contenção offline e os estados front/back; não prova Anki nativo, pixels, fontes instaladas, áudio ou aparência renderizada."
ui_proof_slots:
  - slot_id: normal-card-anki-corrected-source-proof
    claim: "O HTML standalone declara exatamente duas janelas simuladas, uma frente e um verso, com cards fluidos que seguem a altura do conteúdo, fundo de viewport separado e visível abaixo deles, tradução oculta/visível por estado, layout responsivo e nenhuma dependência ativa ou externa."
    route_state: "Inspecionar normal_card_anki_corrected_preview.html localmente: data-window-state e data-card-state em ordem front/back; nenhuma rota da aplicação ou execução em Anki nativo participa da evidência."
    required_evidence_kinds: [code, test]
    minimum_observations: 10
    expected_artifact_types: ["inspeção de fonte HTML/CSS", "saída do validador Python stdlib", "observação de integridade da fonte de produção"]
    validation_command: >-
      python -c "import re; from pathlib import Path; s=Path('normal_card_anki_corrected_preview.html').read_text(encoding='utf-8'); lt=chr(60); windows=re.findall(lt+r'section class=\"anki-window\" data-window-state=\"(front|back)\"',s,re.I); cards=re.findall(lt+r'article class=\"customCard cardBack\" data-card-state=\"(front|back)\"[^>]*>(.*?)'+lt+r'/article>',s,re.I|re.S); assert windows==['front','back'] and len(re.findall(r'class=\"anki-window\"',s,re.I))==2; assert len(cards)==2 and [state for state,_ in cards]==['front','back'] and len(re.findall(lt+r'article\b',s,re.I))==2; front,back=(body for _,body in cards); assert front.replace('is-hidden','is-visible').replace('\"hidden\"','\"visible\"').replace('aria-hidden=\"true\"','aria-hidden=\"false\"')==back; assert 'class=\"sentenceTranslation is-hidden\"' in front and 'data-translation-state=\"hidden\"' in front and 'aria-hidden=\"true\"' in front; assert 'class=\"sentenceTranslation is-visible\"' in back and 'data-translation-state=\"visible\"' in back and 'aria-hidden=\"false\"' in back; assert re.search(r'\.is-hidden\s*\{[^}]*display\s*:\s*none',s,re.I|re.S) and re.search(r'\.is-visible\s*\{[^}]*display\s*:\s*block',s,re.I|re.S); card_rules=re.findall(r'\.customCard\s*\{([^}]*)\}',s,re.I|re.S); assert card_rules; base=card_rules[0]; assert re.search(r'width\s*:\s*100%\s*;',base,re.I) and re.search(r'max-width\s*:\s*none\s*;',base,re.I) and re.search(r'min-height\s*:\s*0\s*;',base,re.I) and re.search(r'background\s*:\s*var\(--color-card-background\)',base,re.I); assert sum(bool(re.search(r'min-height\s*:',rule,re.I)) for rule in card_rules)==1 and not re.search(r'calc\s*\(\s*100vh',s,re.I); viewport=re.search(r'\.anki-viewport\s*\{([^}]*)\}',s,re.I|re.S).group(1); assert re.search(r'background\s*:\s*var\(--color-page-background\)',viewport,re.I) and re.search(r'min-height\s*:\s*620px\s*;',viewport,re.I) and re.search(r'padding\s*:\s*12px\s*;',viewport,re.I); body_css=re.search(r'body\s*\{([^}]*)\}',s,re.I|re.S).group(1); assert re.search(r'min-height\s*:\s*100vh\s*;',body_css,re.I); content=('Buch','/buːx/','noun: book','Das Buch liegt auf dem Tisch.','O livro está sobre a mesa.'); assert all(all(token in body for token in content) for body in (front,back)) and s.count('▶')==4; required=('--color-page-background: #121212','--color-card-background: #1E1E1E','--color-text-primary: #EAEAEA','--color-text-muted: #A0A0A0','--color-divider: #333333','Georgia, Cambria, \"Times New Roman\", Times, serif','padding: 28px 24px','border: 1px solid var(--color-divider)','border-radius: 8px','box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5)','font-size: 38px','font-weight: 600','grid-template-columns: repeat(2, minmax(0, 1fr))','@media (max-width: 980px)','grid-template-columns: 1fr','@media (max-width: 420px)','padding: 8px','padding: 22px 18px'); assert all(token in s for token in required),[token for token in required if token not in s]; forbidden=(lt+r'script\b',lt+r'link\b',lt+r'(?:img|audio|video|iframe|object|embed)\b',r'\b(?:src|href)\s*=',r'@import\b',r'url\s*\(',r'https?://',r'\{\{'); assert not any(re.search(pattern,s,re.I) for pattern in forbidden),[pattern for pattern in forbidden if re.search(pattern,s,re.I)]; print('corrected preview contract OK: 2 windows/cards, content-height fluid cards, separate viewport background, front/back translation, responsive and offline')"
    environment: "Inspeção offline com Python stdlib; sem servidor, rede, automação de browser ou cliente Anki nativo."
    viewport: "Contrato de fonte: duas colunas acima de 980px, uma coluna em 980px ou menos; cada .anki-viewport declara min-height de 620px e padding 12px/8px para expor o background abaixo do card. Nenhuma viewport renderizada é alegada."
    manual_acceptance_required: false
    claim_limit: "Prova somente HTML/CSS declarado e resultados do validador; não prova pixels, gosto visual, fontes instaladas, áudio ou fidelidade do WebView do Anki Desktop/mobile."
must_haves:
  truths:
    - "O usuário pode abrir um único HTML standalone na raiz e comparar frente e verso do card normal corrigido em duas janelas simuladas."
    - "Em largura desktop as janelas ficam lado a lado; em tela estreita ficam empilhadas sem overflow horizontal."
    - "Cada viewport simulada mostra background de página abaixo do card porque a viewport é alta e o card termina após o conteúdo."
    - "Cada card usa width: 100%, max-width: none e min-height: 0, com padding externo 12px no desktop e 8px no mobile."
    - "Ambos mostram Buch, IPA, definição, exemplo e indicadores Unicode separados; a tradução fica oculta na frente e visível no verso."
    - "O preview espelha a paleta, tipografia, espaçamento, borda, raio, sombra e hierarquia Gemini efetivos do template atual."
    - "O preview não contém scripts, rede, fontes, imagens, bibliotecas ou assets externos."
    - "Produção e todos os arquivos fora do write set permanecem inalterados e nenhum estado Git é modificado."
  artifacts:
    - path: normal_card_anki_corrected_preview.html
      provides: "Preview offline responsivo com duas janelas Anki simuladas e cards front/back de altura corrigida"
    - path: .planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md
      provides: "Evidência source-only, comando/resultado, observações, privacidade, integridade e limites da claim"
  key_links:
    - from: "normal_card_anki_corrected_preview.html .anki-viewport"
      to: "normal_card_anki_corrected_preview.html .customCard"
      via: "viewport com background #121212, min-height 620px e padding externo contém card #1E1E1E com largura fluida e altura natural"
    - from: "article[data-card-state=front]"
      to: "article[data-card-state=back]"
      via: "markup e dados espelhados; somente classes/atributos de visibilidade da tradução diferem"
    - from: normal_card_anki_corrected_preview.html
      to: .planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md
      via: "validador Python exato, observações source-only e SHA-256 antes/depois de normal_card.md"
---

# Quick Task 037 Plan: Preview do card Anki corrigido

<objective>
Criar um preview HTML standalone que mostre como o card normal corrigido é estruturado para frente e verso, destacando que a borda/fundo do card terminam após o conteúdo e que o restante da janela usa somente o background da página.

Purpose: permitir comparação direta do resultado esperado após a correção do excesso de espaço inferior observado em `pt1.png`/`pt2.png`, sem tocar na implementação de produção já corrigida.

Output: `normal_card_anki_corrected_preview.html`, evidenciado de forma source-only em `.planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md`.
</objective>

<context>
- Fonte visual e dimensional bloqueada: `src/multilang/templates/normal_card.md`, incluindo as declarações finais efetivas `body/.card min-height: 100vh`, padding externo `12px`/`8px`, `.customCard { width: 100%; max-width: none; min-height: 0; }` e padding interno `28px 24px`/`22px 18px`.
- Referência de resultado: `pt1.png` mostra a borda terminando após o conteúdo; `pt2.png` fornece os dados alemães e evidencia o espaço inferior incorreto dentro da borda.
- `src/multilang/templates/normal_card.md` está modificado e não commitado. Toda a árvore suja é concorrente e deve ser preservada.
- Discovery nível 0: composição HTML/CSS offline a partir de padrões existentes, sem dependência ou API nova.
</context>

## Decisões bloqueadas

- **D-01 — Produção somente leitura:** não editar `src/multilang/templates/normal_card.md`, testes, debug, `pt1.png`, `pt2.png`, previews anteriores ou qualquer arquivo concorrente.
- **D-02 — Dimensões corrigidas:** card com `width: 100%`, `max-width: none`, `min-height: 0`; viewport/página separada mantém altura e padding externo desktop/mobile.
- **D-03 — Duas janelas:** exatamente uma janela front e uma back, lado a lado no desktop, empilhadas em largura estreita e com altura suficiente para declarar fundo visível abaixo do card.
- **D-04 — Conteúdo alemão:** ambos os cards usam `Buch`, `/buːx/`, `noun: book`, `Das Buch liegt auf dem Tisch.`, `O livro está sobre a mesa.` e indicadores Unicode `▶` para palavra e frase; tradução escondida somente visualmente na frente e mostrada no verso.
- **D-05 — Estilo Gemini atual:** espelhar as declarações finais efetivas do template, sem retornar ao limite antigo de 460px.
- **D-06 — Standalone inerte:** HTML e CSS inline, sem script, rede, fontes externas, bibliotecas, imagens, SVGs ou outros assets.
- **D-07 — Claim source-only:** validar estrutura e CSS por inspeção/Python; não alegar Anki nativo, pixels, renderização observada ou áudio funcional.
- **D-08 — Lifecycle/Git:** não editar LOG/ROADMAP/SPEC e não fazer commit ou staging.

<checks>
<plan_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: "Uma tarefa atômica cobre os dois artefatos, possui comandos executáveis, implementa D-01 a D-08 e limita honestamente a evidência. Assurance independente não está disponível porque .planning/templates/roles/ está vazio."
</plan_check>
</checks>

<tasks>

<task id="037-01" type="auto">
  <name>Criar o preview corrigido e registrar prova source-only</name>
  <files>
    - CREATE: normal_card_anki_corrected_preview.html
    - MODIFY: .planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md
  </files>
  <action>
    Antes de escrever, registre `git status --short` e o SHA-256 dos bytes atuais de `src/multilang/templates/normal_card.md`; preserve-os como baseline protegido de D-01/D-08. Leia somente as declarações finais efetivas da fonte e não execute formatadores, testes de produto ou comandos que escrevam caches. Crie `normal_card_anki_corrected_preview.html` na raiz como HTML5 autocontido com um único `<style>` inline.

    Implemente exatamente duas seções, nesta ordem e com estas aberturas determinísticas: `<section class="anki-window" data-window-state="front">` e `<section class="anki-window" data-window-state="back">`. Cada janela deve ter chrome/label conciso fora da viewport e exatamente um `<div class="anki-viewport">`; a viewport declara `display: block`, `min-height: 620px`, `padding: 12px` e `background: var(--color-page-background)`, oferecendo área de fundo abaixo do conteúdo por D-02/D-03. Use uma `.preview-grid` de `repeat(2, minmax(0, 1fr))` e, em `@media (max-width: 980px)`, mude para `1fr`. Em `@media (max-width: 420px)`, reduza somente o padding da viewport para `8px` e o padding interno do card para `22px 18px`.

    Dentro das viewports, crie exatamente dois artigos, nesta ordem: `<article class="customCard cardBack" data-card-state="front">` e a variante `back`. A regra base única de `.customCard` deve declarar literalmente `display: block`, `width: 100%`, `max-width: none`, `min-height: 0`, `padding: 28px 24px` e `background: var(--color-card-background)`; não declarar altura, flex-grow, `calc(100vh...)` ou qualquer override mobile de min-height. O body mantém `min-height: 100vh`. Isso implementa D-02 sem confundir a altura da viewport simulada com a altura natural do card.

    Espelhe D-05 com as variáveis `#121212`, `#1E1E1E`, `#EAEAEA`, `#A0A0A0` e `#333333`, Georgia/Cambria/serif no conteúdo, sans-serif em IPA/labels, borda `1px`, raio `8px`, sombra `0 4px 20px rgba(0, 0, 0, 0.5)`, palavra `38px/600`, divisores, headings compactos, definição `16px/1.6` e exemplo/tradução `16px/1.5`. Não use o `max-width: 460px` do preview anterior; limite apenas o container de comparação, nunca cada card.

    Duplique o mesmo corpo semântico e os dados exatos de D-04 nos dois artigos, com um `▶` acessível para áudio da palavra e outro para áudio da frase em cada card. O único delta entre os corpos deve ser a tradução: frente usa `class="sentenceTranslation is-hidden"`, `data-translation-state="hidden"`, `aria-hidden="true"`; verso usa `is-visible`, `visible`, `false`. Defina `.is-hidden { display: none; }` e `.is-visible { display: block; }`, sem JavaScript. Cumpra D-06 sem elementos `script`, `link`, `img`, `audio`, `video`, `iframe`, `object` ou `embed`, sem `src`/`href`, `@import`, `url(...)`, HTTP(S), templates Anki ou qualquer asset externo.

    Execute o comando exato de `ui_proof_slots`. Atualize o `UI-PROOF.md` já criado pelo planner com JSON cercado válido e todos os campos de topo existentes. Substitua o estado `pending` por evidência observada: no mínimo dez observações vinculadas ao slot, cada uma com `slot_id`, `claim`, `route_state`, `observation`, `evidence_kind`, `artifact_path`, `privacy`, `result` e `claim_limit`; registre o comando e sua saída; inclua metadados `visibility`, `retention`, `sensitivity`, `safe_to_publish` para cada artefato; e registre SHA-256 antes/depois/live de `normal_card.md`. Marque `result: pass` somente se os validadores passarem e os três hashes forem iguais. Preserve D-07 em `claim_limits`: source-only, sem Anki nativo e sem pixels. Compare o status final com o baseline para confirmar que não surgiu mudança fora dos dois arquivos permitidos; não crie `037-SUMMARY.md` dentro desta tarefa, pois o executor o cria como artefato de lifecycle após concluí-la.
  </action>
  <verify>
    <automated>python -c "import re; from pathlib import Path; s=Path('normal_card_anki_corrected_preview.html').read_text(encoding='utf-8'); lt=chr(60); windows=re.findall(lt+r'section class=\"anki-window\" data-window-state=\"(front|back)\"',s,re.I); cards=re.findall(lt+r'article class=\"customCard cardBack\" data-card-state=\"(front|back)\"[^>]*>(.*?)'+lt+r'/article>',s,re.I|re.S); assert windows==['front','back'] and len(re.findall(r'class=\"anki-window\"',s,re.I))==2; assert len(cards)==2 and [state for state,_ in cards]==['front','back'] and len(re.findall(lt+r'article\b',s,re.I))==2; front,back=(body for _,body in cards); assert front.replace('is-hidden','is-visible').replace('\"hidden\"','\"visible\"').replace('aria-hidden=\"true\"','aria-hidden=\"false\"')==back; assert 'class=\"sentenceTranslation is-hidden\"' in front and 'data-translation-state=\"hidden\"' in front and 'aria-hidden=\"true\"' in front; assert 'class=\"sentenceTranslation is-visible\"' in back and 'data-translation-state=\"visible\"' in back and 'aria-hidden=\"false\"' in back; assert re.search(r'\.is-hidden\s*\{[^}]*display\s*:\s*none',s,re.I|re.S) and re.search(r'\.is-visible\s*\{[^}]*display\s*:\s*block',s,re.I|re.S); card_rules=re.findall(r'\.customCard\s*\{([^}]*)\}',s,re.I|re.S); assert card_rules; base=card_rules[0]; assert re.search(r'width\s*:\s*100%\s*;',base,re.I) and re.search(r'max-width\s*:\s*none\s*;',base,re.I) and re.search(r'min-height\s*:\s*0\s*;',base,re.I) and re.search(r'background\s*:\s*var\(--color-card-background\)',base,re.I); assert sum(bool(re.search(r'min-height\s*:',rule,re.I)) for rule in card_rules)==1 and not re.search(r'calc\s*\(\s*100vh',s,re.I); viewport=re.search(r'\.anki-viewport\s*\{([^}]*)\}',s,re.I|re.S).group(1); assert re.search(r'background\s*:\s*var\(--color-page-background\)',viewport,re.I) and re.search(r'min-height\s*:\s*620px\s*;',viewport,re.I) and re.search(r'padding\s*:\s*12px\s*;',viewport,re.I); body_css=re.search(r'body\s*\{([^}]*)\}',s,re.I|re.S).group(1); assert re.search(r'min-height\s*:\s*100vh\s*;',body_css,re.I); content=('Buch','/buːx/','noun: book','Das Buch liegt auf dem Tisch.','O livro está sobre a mesa.'); assert all(all(token in body for token in content) for body in (front,back)) and s.count('▶')==4; required=('--color-page-background: #121212','--color-card-background: #1E1E1E','--color-text-primary: #EAEAEA','--color-text-muted: #A0A0A0','--color-divider: #333333','Georgia, Cambria, \"Times New Roman\", Times, serif','padding: 28px 24px','border: 1px solid var(--color-divider)','border-radius: 8px','box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5)','font-size: 38px','font-weight: 600','grid-template-columns: repeat(2, minmax(0, 1fr))','@media (max-width: 980px)','grid-template-columns: 1fr','@media (max-width: 420px)','padding: 8px','padding: 22px 18px'); assert all(token in s for token in required),[token for token in required if token not in s]; forbidden=(lt+r'script\b',lt+r'link\b',lt+r'(?:img|audio|video|iframe|object|embed)\b',r'\b(?:src|href)\s*=',r'@import\b',r'url\s*\(',r'https?://',r'\{\{'); assert not any(re.search(pattern,s,re.I) for pattern in forbidden),[pattern for pattern in forbidden if re.search(pattern,s,re.I)]; print('corrected preview contract OK: 2 windows/cards, content-height fluid cards, separate viewport background, front/back translation, responsive and offline')"</automated>
    <automated>python -c "import hashlib,json,re; from pathlib import Path; text=Path('.planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md').read_text(encoding='utf-8'); match=re.search(r'```json\s*(.*?)\s*```',text,re.S); assert match; data=json.loads(match.group(1)); required={'proof_bundle_version','scope','route_state','environment','viewport','evidence_inputs','commands_or_manual_steps','observations','artifacts','privacy','result','claim_limits','source_integrity'}; assert required.issubset(data),sorted(required-data.keys()); assert data['scope']['slot_id']=='normal-card-anki-corrected-source-proof' and data['result']=='pass'; observations=data['observations']; observation_fields={'slot_id','claim','route_state','observation','evidence_kind','artifact_path','privacy','result','claim_limit'}; assert len(observations)>=10 and all(observation_fields.issubset(item) and item['result']=='pass' for item in observations); artifact_fields={'visibility','retention','sensitivity','safe_to_publish'}; assert len(data['artifacts'])>=2 and all(artifact_fields.issubset(item) for item in data['artifacts']); live=hashlib.sha256(Path('src/multilang/templates/normal_card.md').read_bytes()).hexdigest(); integrity=data['source_integrity']; assert integrity['before_sha256']==integrity['after_sha256']==integrity['live_final_sha256']==live; limits=json.dumps(data['claim_limits'],ensure_ascii=False).lower(); assert 'source-only' in limits and 'anki nativo' in limits and 'pixel' in limits; print('UI proof OK: complete, source integrity preserved, claim source-only')"</automated>
    <automated>git diff --check -- "normal_card_anki_corrected_preview.html" ".planning/quick/037-preview-card-anki-corrigido/037-PLAN.md" ".planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md"</automated>
    <automated>git diff --cached --exit-code -- "normal_card_anki_corrected_preview.html" ".planning/quick/037-preview-card-anki-corrigido" "src/multilang/templates/normal_card.md" "tests" ".planning/debug/normal-card-too-small-in-anki.md" "pt1.png" "pt2.png" "normal_card_gemini_preview.html" ".planning/quick/LOG.md" ".planning/ROADMAP.md" ".planning/SPEC.md"</automated>
  </verify>
  <done>`normal_card_anki_corrected_preview.html` contém exatamente duas janelas/cards front/back, declara largura fluida e altura natural do card com viewport separada, usa os dados alemães e estados de tradução exigidos, responde em duas/uma coluna, permanece totalmente offline e passa os validadores; `UI-PROOF.md` registra prova source-only e integridade; nenhum arquivo protegido ou estado Git é alterado.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Arquivo local → renderer HTML | O preview aberto localmente deve permanecer inerte e não carregar nem executar conteúdo externo. |
| Nova evidência → worktree concorrente | A criação do preview não pode sobrescrever a correção de produção nem mudanças preexistentes. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q037-01 | Tampering / Information disclosure | `normal_card_anki_corrected_preview.html` | mitigate | O validador rejeita scripts, elementos de mídia/embed, `src`/`href`, imports/URLs CSS, HTTP(S) e placeholders Anki; somente dados representativos fixos são permitidos. |
| T-Q037-02 | Tampering / Repudiation | `src/multilang/templates/normal_card.md` e worktree sujo | mitigate | Write set de dois arquivos, SHA-256 antes/depois/live da fonte, status antes/depois e proibição explícita de operações Git mutáveis ou cleanup. |
</threat_model>

## Source Coverage Audit

| SOURCE | ID | Feature/Requirement | Plan | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Mostrar frente/verso do card normal após corrigir o espaço inferior | 037 | COVERED | Task 037-01 cria o preview raiz comparativo |
| REQ | — | Quick mode não possui requirement IDs de ROADMAP | 037 | COVERED | `requirements: []`; nenhum requisito de fase é apropriado |
| RESEARCH | — | Diagnóstico confirmado: manter largura/padding e usar `.customCard min-height: 0` com página alta | 037 | COVERED | D-02 e validação literal do CSS |
| CONTEXT | D-01 | Produção, testes, debug, imagens, previews e concorrentes intocados | 037 | COVERED | Write set, hash, status e proibições |
| CONTEXT | D-02 | width 100%, max-width none, min-height 0; viewport/padding separados | 037 | COVERED | Estrutura e validador Python |
| CONTEXT | D-03 | Duas janelas lado a lado/empilhadas com fundo abaixo do card | 037 | COVERED | Grid, media query e min-height 620px da viewport |
| CONTEXT | D-04 | Dados alemães, áudio Unicode e tradução front/back | 037 | COVERED | Corpos espelhados e estados verificáveis |
| CONTEXT | D-05 | Estilo Gemini e dimensões atuais | 037 | COVERED | Tokens CSS literais e nenhum 460px no card |
| CONTEXT | D-06 | Sem script, rede, fontes ou assets externos | 037 | COVERED | Scan negativo automatizado |
| CONTEXT | D-07 | Claim source-only | 037 | COVERED | Slot e UI-PROOF limitam a alegação |
| CONTEXT | D-08 | Sem LOG/ROADMAP/SPEC/commit/staging | 037 | COVERED | Hard boundaries e checks Git |

Excluído sem gap: alteração da produção/testes/debug, renderização em Anki nativo, comparação de pixels, prova de áudio e qualquer atualização de LOG/ROADMAP/SPEC.

<verification>
Executar todos os comandos da tarefa a partir da raiz do repositório. O primeiro Python é a autoridade para o contrato do preview; o segundo valida o bundle e a preservação byte a byte de `normal_card.md`. A conclusão permanece estritamente source-only.
</verification>

<success_criteria>
- Exatamente duas janelas simuladas e dois cards em ordem front/back existem no único HTML raiz novo.
- Os cards declaram `width: 100%`, `max-width: none`, `min-height: 0`; nenhuma altura de viewport é aplicada ao card.
- As viewports declaram fundo de página separado, altura suficiente e padding externo 12px/8px; os cards mantêm padding 28px 24px/22px 18px.
- Layout fonte declara duas colunas no desktop e uma coluna em telas estreitas.
- Dados `Buch` e quatro indicadores `▶` aparecem nos corpos espelhados; tradução fica hidden na frente e visible no verso sem JavaScript.
- Paleta, tipografia e métricas Gemini exigidas são encontradas literalmente.
- Não existem scripts, rede, fontes, mídia, embeds, templates ou referências externas.
- `UI-PROOF.md` possui JSON válido, dez ou mais observações completas, metadados de privacidade, resultado pass, hash preservado e limites source-only.
- Produção, testes, debug, imagens, previews anteriores, concorrentes, LOG, ROADMAP, SPEC e staging permanecem intocados; nenhum commit é criado.
</success_criteria>

<output>
Após executar e verificar a tarefa, criar `.planning/quick/037-preview-card-anki-corrigido/037-SUMMARY.md`; não atualizar LOG/ROADMAP/SPEC e não fazer commit ou staging.
</output>
