---
mode: quick
task: 035-aumentar-altura-template-frequencia
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: []
files_modified:
  - tests/services/test_card_template_loader.py
  - src/multilang/templates/normal_card.md
  - .planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md
files_verified:
  - path: tests/integration/test_v13_normal_template_export_contract.py
    mode: verification-only
    note: "Executar sem editar para proteger o contrato APKG normal."
  - path: src/multilang/services/card_template_loader.py
    mode: verification-only
    note: "Preservar a seleção do template normal e a composição CSS do Mandarin."
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/planner.md não existe; o contrato quick fornecido pelo usuário foi aplicado diretamente."
non_goals:
  - "Não alterar mandarin_card.md, japanese_card.md, latin_mvp_card.md nem qualquer outra família de template."
  - "Não alterar campos, markup, Translation reveal, áudio, imagens, schema, loader, export ou model IDs."
  - "Não adicionar infraestrutura de browser nem editar ROADMAP.md, SPEC.md ou LOG.md."
  - "Não criar branch, stage ou commit."
closure_claim_limit: "A automação prova o contrato CSS efetivo e sua composição em normal/Mandarin; aparência e rolagem no WebView nativo do Anki Desktop/mobile permanecem human_needed até inspeção humana."
must_haves:
  truths:
    - "O painel de frequência normal fica centralizado, alto e responsivo, ocupando grande parte da viewport sem usar altura fixa rígida."
    - "Em uma viewport desktop de 1280x800, o contrato CSS destina 720px mínimos ao painel; em mobile portrait 390x667, destina 587px, sem a altura mínima causar rolagem por si só."
    - "O espaço vertical excedente é distribuído intencionalmente entre as seções, enquanto conteúdo longo pode aumentar a altura natural do painel."
    - "Mandarin frequency e word-list herdam o CSS normal atualizado pela composição existente do loader."
    - "Templates de japonês e latim e todos os contratos de campos, markup e export permanecem inalterados."
  artifacts:
    - path: tests/services/test_card_template_loader.py
      provides: "Regressão test-first para altura responsiva, centralização, distribuição vertical e herança Mandarin."
    - path: src/multilang/templates/normal_card.md
      provides: "Override CSS final canônico do painel normal alto e responsivo."
    - path: .planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md
      provides: "Evidência code/test com limites honestos para o WebView nativo do Anki."
  key_links:
    - from: src/multilang/templates/normal_card.md
      to: src/multilang/services/card_template_loader.py
      via: "parse da seção Styling e seleção para source_type=frequency"
    - from: src/multilang/templates/normal_card.md
      to: src/multilang/templates/mandarin_card.md
      via: "o loader concatena base_template.css antes do CSS Mandarin"
    - from: ".card com min-height: 100vh e centralização"
      to: ".customCard com min-height responsiva e layout em coluna"
      via: "calc/min baseados na viewport e flex distribution sem height rígida"
ui_proof_slots:
  - slot_id: frequency-panel-responsive-css-contract
    claim: "Normal frequency e Mandarin frequency/word-list recebem o painel alto, centralizado e responsivo: 720px mínimos em desktop 1280x800, 587px em mobile 390x667, distribuição vertical flex e crescimento natural para conteúdo longo."
    route_state: "Carregar os templates com load_card_template para frequency normal, frequency Mandarin e word-list Mandarin; inspecionar as declarações CSS finais e executar os testes focados."
    required_evidence_kinds: [code, test]
    minimum_observations: 7
    expected_artifact_types: ["diff do template/teste", "inspeção do CSS gerado", "saída pytest focada", "registros em UI-PROOF.md"]
    validation_command: "uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q"
    environment: "Python 3.12+, loader real do projeto; sem browser ou renderer nativo do Anki"
    viewport: "Desktop 1280x800 (min-height calculada 720px) e mobile portrait 390x667 (min-height calculada 587px); cálculo/contrato CSS, não pixels renderizados"
    manual_acceptance_required: false
    claim_limit: "Prova CSS efetivo, aritmética de viewport, ausência de height rígida, composição Mandarin e regressões de export; não prova aparência, fontes, clipping ou rolagem em WebViews nativos."
  - slot_id: frequency-panel-native-anki-acceptance
    claim: "O painel normal e o Mandarin aparecem altos, centralizados e bem espaçados no Anki Desktop e mobile, sem rolagem causada apenas pela altura mínima em tela curta e sem cortar conteúdo longo."
    route_state: "Importar decks representativos normal e Mandarin; observar frente e verso com conteúdo curto e longo no Anki Desktop e em um cliente Anki mobile portrait."
    required_evidence_kinds: [human]
    minimum_observations: 8
    expected_artifact_types: ["checklist manual normal/Mandarin, front/back, Desktop/mobile, incluindo conteúdo longo"]
    validation_command: "npx -y gsdd-cli ui-proof validate .planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"
    environment: "WebView nativo do Anki Desktop e de um cliente Anki mobile; agent-browser comum não é equivalente"
    viewport: "Anki Desktop 1280x800 e mobile portrait representativo 390x667, mais estado de tela baixa disponível no cliente"
    manual_acceptance_required: true
    claim_limit: "Permanece human_needed até as observações nativas serem registradas; pytest, inspeção de CSS e agent-browser comum não fecham esta alegação visual."
---

# Quick Task 035 Plan: Aumentar altura do template de frequência

## Objective

Corrigir somente o override CSS final de `normal_card.md` para que o painel dos decks de frequência normal — e do Mandarin que herda esse CSS — seja alto, responsivo, centralizado e verticalmente bem distribuído, sem impor altura rígida nem regressar contratos Anki/export.

## Context

- Discovery level 0: a mudança segue o padrão existente de template Markdown, loader e asserts CSS com `_last_css_value`; não há dependência ou integração externa nova.
- O override canônico final atualmente vence a cascata com `.customCard { display: block; min-height: 0; ... }`, fazendo o painel encolher até o conteúdo apesar de `.card` já usar flex, centralização e `min-height: 100vh`.
- `card_template_loader.py` usa `normal_card.md` para frequência normal e antepõe todo o CSS normal ao CSS de `mandarin_card.md` em frequency/word-list Mandarin.
- A suíte ampla tem drift documentado. Os gates autoritativos desta mudança são o teste de loader completo e o contrato de export v1.3 indicado como verification-only.

## Locked Decisions

- **D-01 — Escopo:** Alterar apenas o template normal de frequência e permitir que Mandarin herde seu CSS pela composição já existente. Preservar integralmente os templates separados de japonês e latim.
- **D-02 — Abordagem visual:** Usar painel alto e responsivo, centralizado, ocupando boa parte da altura disponível, com espaço interno melhor distribuído, sem altura fixa rígida e sem forçar rolagem em telas pequenas.
- **D-03 — TDD:** Primeiro atualizar/adicionar o teste focado, executar e observar RED causado pelas novas expectativas; somente depois editar produção e obter GREEN.
- **D-04 — Limite de mudança:** Preferir o override CSS canônico final. Não alterar campos, markup, reveal de Translation, áudio, imagens, schema, loader, export ou outras famílias.

## Tasks

<task id="035-01" type="auto" tdd="true">
  <name>Fixar em RED o contrato responsivo normal e Mandarin</name>
  <files>
    - tests/services/test_card_template_loader.py
  </files>
  <behavior>
    - O CSS efetivo final de `.card` mantém `display: flex`, `justify-content: center`, `align-items: center`, `padding: 40px 16px` e `min-height: 100vh`; os 40px superior + 40px inferior são os 80px descontados em `calc(100vh - 80px)`.
    - A regra universal efetiva mantém `box-sizing: border-box`, garantindo que padding e borda participem da geometria responsiva sem ampliar o painel além da viewport.
    - O CSS efetivo final de `.customCard` usa `display: flex`, coluna, `justify-content: space-between`, `align-items: stretch` e `min-height: min(760px, calc(100vh - 80px))` por D-02.
    - O painel não declara `height` rígida; a min-height resulta em 720px para viewport 1280x800, 587px para 390x667 e teto de 760px em telas altas, enquanto conteúdo longo pode aumentar o box.
    - O padding efetivo do painel é `clamp(24px, 4vh, 40px) 24px`, e nenhum `.cardBack` posterior o anula.
    - Frequency normal, frequency Mandarin e word-list Mandarin expõem o mesmo contrato base; as duas rotas Mandarin continuam idênticas e com CSS iniciado pelo CSS normal completo.
    - Referências de campos, Translation reveal, áudio, imagem e ordem pedagógica existentes continuam cobertos sem alteração por D-04.
  </behavior>
  <action>
    Por D-03, editar somente `tests/services/test_card_template_loader.py`. Antes de qualquer edição de produção, atualizar obrigatoriamente em `test_project_normal_template_preserves_contract_and_uses_gemini_dark_layout` a expectativa já existente de `.customCard` `padding: 28px 24px` para `padding: clamp(24px, 4vh, 40px) 24px`; essa expectativa alterada deve falhar no RED junto das demais novas expectativas. Adicionar também um teste nomeado `test_normal_and_mandarin_panels_use_responsive_viewport_height`. Reutilizar `_last_css_block` e `_last_css_value` para verificar as declarações vencedoras, não simples ocorrências antigas.

    No novo teste, exigir para `.card` os valores finais `display: flex`, `justify-content: center`, `align-items: center`, `padding: 40px 16px` e `min-height: 100vh`, e ligar explicitamente os dois paddings verticais de 40px aos 80px de `calc(100vh - 80px)`. Provar a regra universal efetiva sem criar parser: usar o `re` já importado para coletar, em ordem, blocos do seletor isolado `*`, exigir pelo menos um bloco e aplicar `_last_css_value` ao último bloco coletado para obter `box-sizing: border-box`. Carregar frequency normal, frequency Mandarin e word-list Mandarin; exigir exatamente a expressão de min-height, o flex column/space-between/stretch, o padding responsivo e a ausência de uma propriedade `height:` rígida no bloco final. Verificar pela posição dos blocos que nenhum override `.cardBack` posterior substitui o padding canônico. Manter e reforçar a asserção de que Mandarin começa com todo `base.css` e que as duas rotas Mandarin coincidem.

    Não editar produção nem criar/escrever `UI-PROOF.md` nesta task. Executar o teste nominal abaixo e também `test_project_normal_template_preserves_contract_and_uses_gemini_dark_layout`; confirmar que o RED inclui a expectativa obrigatoriamente atualizada de padding e que as demais falhas decorrem de o CSS atual ainda retornar `display: block`/`min-height: 0`, não de erro de sintaxe, import ou fixture. Capturar e preservar a saída e o motivo do RED nas notas de execução; registrá-los em `UI-PROOF.md` somente na Task 035-02. Se qualquer expectativa nova passar imediatamente sem provar o comportamento ausente, corrigi-la antes de continuar.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py::test_project_normal_template_preserves_contract_and_uses_gemini_dark_layout tests/services/test_card_template_loader.py::test_normal_and_mandarin_panels_use_responsive_viewport_height -q</automated>
    Resultado obrigatório nesta task: RED que inclua a troca esperada de `28px 24px` para `clamp(24px, 4vh, 40px) 24px` e seja atribuível às novas expectativas geométricas/layout, com nenhum arquivo de produção ou UI-PROOF modificado.
  </verify>
  <done>O teste Gemini existente e o novo teste focado cobrem D-01/D-02 sobre normal e ambas as rotas Mandarin; a expectativa de padding, a geometria externa e box-sizing foram atualizadas antes de produção, o RED foi preservado em notas de execução, e UI-PROOF ainda não foi escrito.</done>
</task>

<task id="035-02" type="auto" tdd="true">
  <name>Implementar o painel responsivo e registrar prova proporcional</name>
  <files>
    - src/multilang/templates/normal_card.md
    - .planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md
  </files>
  <files_verified>
    - tests/integration/test_v13_normal_template_export_contract.py (executar sem editar)
    - src/multilang/templates/mandarin_card.md (não editar)
    - src/multilang/templates/japanese_card.md (não editar)
    - src/multilang/templates/latin_mvp_card.md (não editar)
    - src/multilang/services/card_template_loader.py (não editar)
  </files_verified>
  <action>
    Após o RED, modificar somente o override CSS canônico no fim de `normal_card.md` por D-01/D-04. Em `.customCard, .nightMode .customCard`, substituir o encolhimento atual por `display: flex`, `flex-direction: column`, `justify-content: space-between`, `align-items: stretch`, `min-height: min(760px, calc(100vh - 80px))` e `padding: clamp(24px, 4vh, 40px) 24px`. Remover o override final redundante `.cardBack { padding: 28px 24px; }` para que o padding responsivo realmente vença a cascata. Manter `width: 100%`, `max-width: 460px`, wrapping, cores, borda, raio, sombra e todo o restante do CSS/markup intactos.

    A expressão baseada na viewport deve produzir 720px no desktop 1280x800 e 587px no mobile 390x667, com teto de 760px; não adicionar `height`, `max-height`, overflow vertical forçado ou media query que imponha um mínimo maior que a altura disponível. `min-height` deve permitir que conteúdo longo expanda o painel e use a rolagem natural da página apenas quando o conteúdo realmente exceder a viewport. Não editar `mandarin_card.md`: a herança deve ocorrer exclusivamente pelo loader existente. Não tocar japonês, latim, loader, markup, campos, Translation, áudio, imagem, schema ou export (D-01/D-04).

    Executar o teste nominal até GREEN e depois os dois arquivos de regressão completos. Criar `UI-PROOF.md` com JSON cercado e os top-level fields `proof_bundle_version`, `scope`, `route_state`, `environment`, `viewport`, `evidence_inputs`, `commands_or_manual_steps`, `observations`, `artifacts`, `privacy`, `result` e `claim_limits`. Recuperar das notas de execução da Task 035-01 a saída RED preservada e registrá-la somente agora. Registrar pelo menos sete observações code/test do primeiro slot: RED esperado incluindo a expectativa alterada de padding; geometria final de `.card` (`40px 16px`, `100vh` e centralização); regra universal efetiva `box-sizing: border-box`; vínculo dos 80px externos com o `calc`; declarações finais normal; cálculo desktop; cálculo mobile; ausência de height rígida/crescimento natural; composição das duas rotas Mandarin; contratos loader/export verdes. Cada artifact deve conter `visibility`, `retention`, `sensitivity` e `safe_to_publish`; tratar outputs, relatórios ou capturas brutas como local-only/unsafe por padrão.

    Não criar browser tooling nem inventar observações renderizadas. Registrar que `agent-browser` comum não equivale aos WebViews nativos do Anki. Manter o resultado visual nativo como `human_needed` e listar os oito passos pendentes do segundo slot (normal/Mandarin, front/back, Desktop/mobile, incluindo tela baixa e conteúdo longo) até revisão humana real.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py::test_normal_and_mandarin_panels_use_responsive_viewport_height -q</automated>
    <automated>uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q</automated>
    <automated>git diff --exit-code -- "src/multilang/templates/mandarin_card.md" "src/multilang/templates/japanese_card.md" "src/multilang/templates/latin_mvp_card.md" "src/multilang/services/card_template_loader.py" "tests/integration/test_v13_normal_template_export_contract.py"</automated>
    <automated>npx -y gsdd-cli ui-proof validate .planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md</automated>
    <automated>git diff --check -- "src/multilang/templates/normal_card.md" "tests/services/test_card_template_loader.py" ".planning/quick/035-aumentar-altura-template-frequencia/UI-PROOF.md"</automated>
  </verify>
  <done>O override final entrega D-01/D-02, os testes chegam a GREEN preservando normal/Mandarin/export e famílias isoladas, e UI-PROOF separa prova automatizada da aceitação nativa human_needed.</done>
</task>

## Threat Model

### Trust Boundaries

| Boundary | Description |
|---|---|
| Conteúdo lexical/HTML de campos → renderer Anki | Texto, definição, imagem e áudio existentes podem ter comprimento e dimensões variáveis dentro do painel. |

### STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q035-01 | Denial of service | `.customCard` com conteúdo longo | mitigate | Usar min-height responsiva sem height/max-height rígida; preservar wrapping e crescimento natural para não cortar conteúdo nem provocar overflow pelo novo mínimo. |
| T-Q035-02 | Tampering / Elevation | Interpolação dos campos no template | accept | O contrato de renderização já existe e não muda; não adicionar referências, markup, scripts, `innerHTML` ou assets externos, e executar as regressões de contrato. |

## Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Painel de frequência maior, centralizado e responsivo | Tasks 035-01 e 035-02 |
| REQ | Quick mode não possui requirement IDs de fase | N/A |
| RESEARCH | Override final atual, composição do loader, helpers e suítes focadas fornecidos/confirmados no código | Tasks 035-01 e 035-02 |
| CONTEXT | D-01 (normal + herança Mandarin; japonês/latim separados) | Tests normal/Mandarin e limite explícito de arquivos em ambas as tasks |
| CONTEXT | D-02 (altura responsiva, centralização, distribuição e mobile sem scroll imposto) | Contrato CSS test-first e implementação exata nas duas tasks |
| CONTEXT | D-03 (RED antes de produção) | Task 035-01 → Task 035-02 |
| CONTEXT | D-04 (override final e contratos intocados) | Action/verify de ambas as tasks |

Exclusões sem gap: mudanças em outras famílias, loader, schema/export/markup, suíte ampla com drift, infraestrutura de browser e alegação de aparência nativa sem observação humana.

## Success Criteria

- Exatamente duas tasks executam RED → GREEN e cada uma contém comandos automatizados reproduzíveis.
- O write scope fica restrito a `tests/services/test_card_template_loader.py`, `src/multilang/templates/normal_card.md` e `UI-PROOF.md`; o executor cria `035-SUMMARY.md` separadamente.
- O painel normal usa min-height responsiva, flex column e distribuição vertical; não usa height rígida e cresce para conteúdo longo.
- Desktop 1280x800 e mobile 390x667 estão explicitamente cobertos no contrato code/test; aparência nativa continua honestamente `human_needed`.
- Frequency e word-list Mandarin continuam compondo todo o CSS normal; japonês, latim e demais contratos permanecem inalterados.
- ROADMAP.md, SPEC.md e LOG.md não são tocados; nenhuma branch ou commit é criado.

## Output

Após executar as duas tasks, criar `.planning/quick/035-aumentar-altura-template-frequencia/035-SUMMARY.md` separadamente do write scope deste plano.

## Quick Plan Self-Check

- Task count: 2 (dentro do limite 1-3).
- Cada task possui `<action>` e `<verify>` com comandos executáveis.
- Escopo mínimo: um teste focado, um template compartilhado e um bundle proporcional de UI proof.
