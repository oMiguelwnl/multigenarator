---
mode: quick
task: 037-compactar-espacamento-fields
plan: 037
type: execute
wave: 1
depends_on: []
autonomous: true
task_count: 2
requirements: []
files_modified:
  - tests/services/test_card_template_loader.py
  - src/multilang/templates/normal_card.md
  - german_frequency_template_dummy.apkg
  - .planning/quick/037-compactar-espacamento-fields/UI-PROOF.md
  - .planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md
files_verified:
  - path: tests/integration/test_v13_normal_template_export_contract.py
    mode: verification-only
    note: "Executar, mas não editar, para proteger o contrato do template/export normal."
hard_boundaries:
  - "Não editar artefatos das Quicks 035/036, outros templates, loader, export, ROADMAP.md, SPEC.md, STATE.md ou LOG.md."
  - "Não alterar markup, campos, margens de seções, Translation reveal, áudio, imagem, min-height, padding, width ou demais declarações visuais."
  - "Não criar branch, stage ou commit; german_frequency_template_dummy.apkg permanece gitignored."
closure_claim_limit: "Automação prova o fluxo block vencedor, regressões focadas e estrutura do APKG; a correção visual no Anki permanece human_needed até o usuário inspecionar o pacote com IDs 1995037001/1995037002."
must_haves:
  truths:
    - "Os fields do card normal voltam ao fluxo vertical compacto, sem distribuir a altura livre entre os filhos diretos."
    - "O painel continua alto, responsivo e centralizado externamente, com min-height, padding, width e visual existentes intactos."
    - "O bloco final de .customCard usa display: block e não declara flex-direction, justify-content nem align-items."
    - "Mandarin herda a mesma correção pela composição CSS normal existente, sem editar seu template."
    - "Um novo APKG alemão com sete cards e IDs 1995037001/1995037002 incorpora o CSS corrigido sem rede ou providers."
    - "O UAT anterior fica registrado como rejeitado por espaçamento excessivo e a reavaliação do novo APKG fica honestamente pendente."
  artifacts:
    - path: tests/services/test_card_template_loader.py
      provides: "Regressão test-first do fluxo block compacto em normal e Mandarin."
    - path: src/multilang/templates/normal_card.md
      provides: "Override CSS final corrigido sem mudanças de conteúdo ou aparência."
    - path: german_frequency_template_dummy.apkg
      provides: "Preview alemão offline com sete cards e identidades novas."
    - path: .planning/quick/037-compactar-espacamento-fields/UI-PROOF.md
      provides: "Bundle exclusivo e satisfeito do slot code/test/APKG."
    - path: .planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md
      provides: "Bundle exclusivo do slot humano, com UAT anterior falho e nova inspeção deferred/human_needed."
  key_links:
    - from: tests/services/test_card_template_loader.py
      to: src/multilang/templates/normal_card.md
      via: "assertions sobre o último bloco CSS de .customCard"
    - from: src/multilang/templates/normal_card.md
      to: "normal e Mandarin via load_card_template"
      via: "o loader existente antepõe o CSS normal ao CSS Mandarin"
    - from: src/multilang/templates/normal_card.md
      to: german_frequency_template_dummy.apkg
      via: "build_multilang_model para German frequency e clone com IDs de preview Quick 037"
ui_proof_slots:
  - slot_id: compact-fields-code-test-apkg
    claim: "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between."
    route_state: "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo."
    required_evidence_kinds: [code, test]
    minimum_observations:
      - "O bloco final de .customCard usa display: block e não contém flex-direction, justify-content ou align-items."
      - "Min-height, padding, width, visual e centralização externa permanecem com os valores anteriores."
      - "Normal e as duas rotas Mandarin recebem o fluxo compacto pelo CSS normal compartilhado."
      - "Os dois arquivos pytest focados passam após o RED esperado."
      - "O APKG contém sete notes, CSS block compacto e somente os IDs 1995037001/1995037002."
    expected_artifact_types:
      - "css inspection report"
      - "focused pytest output"
      - "apkg structural report"
      - "ui-proof metadata"
    validation_command: "node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/037-compactar-espacamento-fields/UI-PROOF.md"
    environment: "Python 3.12+ e serviços locais para code/test/APKG; Anki nativo para aceitação humana; sem rede/providers."
    viewport: "Contrato CSS responsivo preservado; tamanho real do Anki usado pelo usuário na reavaliação, sem alegar pixels antes dela."
    manual_acceptance_required: false
    claim_limit: "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
  - slot_id: compact-fields-native-anki-recheck
    claim: "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between."
    route_state: "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo."
    required_evidence_kinds: [human]
    minimum_observations:
      - "No Anki, um card curto mantém o painel alto e centralizado, mas os fields aparecem compactos sem grandes vazios artificiais."
      - "No Anki, o verso revela Translation e preserva definição, imagem vazia e controles de áudio sem regressão visual."
      - "No Anki, o card de conteúdo longo permanece legível e cresce ou rola naturalmente sem clipping."
    expected_artifact_types:
      - "human anki observation"
    validation_command: "node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md"
    environment: "Python 3.12+ e serviços locais para code/test/APKG; Anki nativo para aceitação humana; sem rede/providers."
    viewport: "Contrato CSS responsivo preservado; tamanho real do Anki usado pelo usuário na reavaliação, sem alegar pixels antes dela."
    manual_acceptance_required: true
    claim_limit: "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."
---

# Quick Task 037 Plan: Compactar espaçamento entre fields

<objective>
Corrigir a regressão visual introduzida pela Quick 035: restaurar o fluxo de conteúdo compacto no override final do template normal, preservar integralmente o painel alto/responsivo e entregar um novo dummy APKG alemão para reavaliação no Anki.

Output: teste e template corrigidos, `german_frequency_template_dummy.apkg` substituído, bundle automático em `UI-PROOF.md`, sidecar humano em `NATIVE-ANKI-RECHECK.md` e `037-SUMMARY.md` criado separadamente pelo executor.
</objective>

## Context

- Discovery level 0: a causa está confirmada no código e a correção usa os helpers e serviços existentes, sem dependência externa nova.
- `.customCard` no override final hoje é flex column com `justify-content: space-between`; isso distribui toda a altura livre da `min-height` e impede o colapso natural de margens verticais.
- `.card` deve continuar flex/center e `.customCard` deve manter `min-height: min(760px, calc(100vh - 80px))`, padding responsivo, largura e aparência atuais.
- `load_card_template` compõe o CSS normal como prefixo do Mandarin; nenhuma edição de `mandarin_card.md` é necessária.
- O usuário já executou UAT real do APKG anterior e o rejeitou por espaçamento excessivo. O APKG Quick 037 exige nova inspeção humana no Anki.

## Locked Decisions

- **D-01 — Correção exata:** no override final, usar `.customCard { display: block; }` e remover desse mesmo bloco `flex-direction`, `justify-content` e `align-items`.
- **D-02 — Preservação visual:** manter min-height, padding, width, max-width, centralização externa, cores, tipografia, borda, sombra e demais declarações intactas.
- **D-03 — Limite funcional:** não alterar markup, fields, margens de seções, Translation reveal, áudio, imagem, loader, export ou templates Mandarin/Japanese/Latin; Mandarin herda pelo CSS normal.
- **D-04 — TDD e testes focados:** editar primeiro o teste, observar RED por `flex`/`space-between`, depois editar produção e executar somente os dois arquivos pytest autorizados.
- **D-05 — Novo APKG:** substituir o dummy alemão com os mesmos sete cards, IDs de preview `1995037001`/`1995037002`, template live corrigido, verificação estrutural local e nenhuma rede/provider.
- **D-06 — UAT honesto:** manter `UI-PROOF.md` exclusivo do slot automático e registrar em `NATIVE-ANKI-RECHECK.md` que o UAT anterior falhou por espaçamento e que o novo UAT no Anki está `human_needed`; não inventar observações nativas.
- **D-07 — Operação:** não editar Quicks 035/036 nem lifecycle docs, não criar script permanente e não executar branch/stage/commit.

<tasks>

<task id="037-01" type="auto" tdd="true">
  <name>Fixar em RED o contrato de fluxo block compacto</name>
  <files>
    - tests/services/test_card_template_loader.py
  </files>
  <behavior>
    - O último bloco CSS aplicável a `.customCard` retorna `display: block` para frequency normal, frequency Mandarin e word-list Mandarin.
    - Esse bloco final não contém declarações `flex-direction`, `justify-content` ou `align-items`.
    - `min-height: min(760px, calc(100vh - 80px))` e `padding: clamp(24px, 4vh, 40px) 24px` permanecem iguais.
    - `.card` continua com `display: flex`, `justify-content: center` e `align-items: center` para preservar a centralização externa.
  </behavior>
  <action>
    Por D-01/D-03/D-04, editar somente `test_normal_and_mandarin_panels_use_responsive_viewport_height` em `tests/services/test_card_template_loader.py`. No loop que já carrega normal e as duas rotas Mandarin, trocar a expectativa do bloco final de `.customCard` de `display == "flex"` para `display == "block"`. Substituir as três expectativas de valores flex por assertions de ausência no próprio `custom_card_block`, usando `re.search(r"(?:^|[;\s])PROPERTY\s*:", custom_card_block) is None` para cada propriedade `flex-direction`, `justify-content` e `align-items`.

    Preservar todas as assertions existentes de `.card`, box-sizing, min-height, padding, ausência de `height` rígida, cálculos responsivos, composição Mandarin e ausência de override `.cardBack` posterior. Não alterar helpers ou outros testes.

    Executar o teste nominal antes de qualquer edição de produção. O resultado obrigatório é RED por o CSS live ainda devolver `display: flex` (e, ao prosseguir pelas assertions, ainda conter `flex-direction`, `justify-content` e `align-items`), não por erro de sintaxe, import ou fixture. Guardar comando, saída e causa nas notas da execução para registrar em `UI-PROOF.md` apenas na Task 037-02. Não editar produção, APKG ou proof nesta task.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py::test_normal_and_mandarin_panels_use_responsive_viewport_height -q</automated>
    Resultado exigido nesta task: RED atribuível ao fluxo flex atual; se passar imediatamente ou falhar por infraestrutura, corrigir o teste antes de continuar.
  </verify>
  <done>O teste real do loader especifica D-01/D-02/D-03 para normal e Mandarin, e o RED correto foi observado antes de qualquer mudança em `normal_card.md`.</done>
</task>

<task id="037-02" type="auto" tdd="true">
  <name>Aplicar o fluxo compacto, chegar a GREEN e substituir o APKG</name>
  <files>
    - src/multilang/templates/normal_card.md
    - german_frequency_template_dummy.apkg
    - .planning/quick/037-compactar-espacamento-fields/UI-PROOF.md
    - .planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md
  </files>
  <files_verified>
    - tests/integration/test_v13_normal_template_export_contract.py (executar sem editar)
    - src/multilang/templates/mandarin_card.md (não editar)
    - src/multilang/templates/japanese_card.md (não editar)
    - src/multilang/templates/latin_mvp_card.md (não editar)
    - src/multilang/services/card_template_loader.py (não editar)
  </files_verified>
  <action>
    Após o RED, implementar somente D-01 no bloco final `.customCard, .nightMode .customCard` de `src/multilang/templates/normal_card.md`: trocar `display: flex;` por `display: block;` e remover as linhas `flex-direction: column;`, `justify-content: space-between;` e `align-items: stretch;`. Não reformatar nem alterar qualquer outra declaração. Em particular, preservar literalmente min-height, padding, margin, max-width, width, overflow, wrapping, cores, borda, raio, sombra, família/tamanho/peso de fonte e toda a regra `.card` externa (D-02). Não tocar markup, seções, Translation, mídia ou outros templates (D-03).

    Executar o teste nominal até GREEN e depois, em uma única invocação, somente os dois arquivos pytest autorizados por D-04:

    `uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q`

    Com GREEN confirmado, substituir `german_frequency_template_dummy.apkg` pelo comando abaixo. Ele reutiliza os sete conteúdos fixos da Quick 036 sem editar seus artefatos, carrega o modelo German frequency live já corrigido, clona-o para IDs novos e não chama rede/providers (D-05/D-07):

```bash
PYTHONPATH=src uv run python -c 'exec("""from pathlib import Path

import genanki

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import (
    DECK_ID as PRODUCTION_DECK_ID,
    MODEL_ID as PRODUCTION_MODEL_ID,
    build_multilang_model,
    build_multilang_note,
)

output = Path("german_frequency_template_dummy.apkg")
preview_model_id = 1_995_037_001
preview_deck_id = 1_995_037_002
assert preview_model_id != PRODUCTION_MODEL_ID
assert preview_deck_id != PRODUCTION_DECK_ID

live_model = build_multilang_model(source_type="frequency", language=SupportedLanguage.DE)
preview_model = genanki.Model(
    preview_model_id,
    "Multilang::German Frequency Dummy Preview Q037",
    fields=[dict(field) for field in live_model.fields],
    templates=[dict(template) for template in live_model.templates],
    css=live_model.css,
)
deck = genanki.Deck(preview_deck_id, "Multilang::German Frequency Template Dummy Preview Q037")

cards = [
    ("der Alltag", "/deːɐ̯ ˈʔaltaːk/", "everyday life; the ordinary activities and routines of a normal day", "Im Alltag fahre ich meistens mit dem Fahrrad zur Arbeit.", "In everyday life, I usually ride my bicycle to work."),
    ("zuverlässig", "/ˈt͡suːfɛɐ̯ˌlɛsɪç/", "reliable; able to be trusted to work well or behave consistently", "Unsere Nachbarin ist sehr zuverlässig und hilft immer pünktlich.", "Our neighbor is very reliable and always helps on time."),
    ("trotzdem", "/ˈtʁɔt͡sdeːm/", "nevertheless; despite the situation just mentioned", "Es regnete stark, trotzdem gingen wir im Park spazieren.", "It was raining heavily; nevertheless, we went for a walk in the park."),
    ("die Herausforderung", "/diː hɛʁˈaʊ̯sˌfɔʁdəʁʊŋ/", "a demanding task or situation that requires sustained effort, careful thought, and the willingness to adapt before a satisfactory result can be reached", "Obwohl die Herausforderung zunächst größer wirkte als erwartet, teilte das Team sie in klare Schritte auf und fand schließlich eine ruhige, zuverlässige Lösung.", "Although the challenge initially seemed larger than expected, the team divided it into clear steps and eventually found a calm, reliable solution."),
    ("sich entscheiden", "/zɪç ʔɛntˈʃaɪ̯dn̩/", "to decide; to make a choice after considering alternatives", "Nach einem langen Gespräch entschied sie sich für den früheren Zug.", "After a long conversation, she decided on the earlier train."),
    ("gemütlich", "/ɡəˈmyːtlɪç/", "cozy, comfortable, and pleasantly relaxed", "Das kleine Café ist am Abend besonders gemütlich.", "The small café is especially cozy in the evening."),
    ("wahrscheinlich", "/vaːɐ̯ˈʃaɪ̯nlɪç/", "probably; in a way that is likely to happen or be true", "Der Brief kommt wahrscheinlich schon morgen an.", "The letter will probably arrive tomorrow."),
]

for rank, (word, ipa, definition, sentence, translation) in enumerate(cards, start=1):
    row = ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.DE,
            source_type="frequency",
            job_id="quick-037-german-dummy-preview",
            item_key=f"dummy-level-1-rank-{rank:04d}",
            lemma_key=f"de-dummy-{rank:04d}",
            sort_index=rank,
        ),
        word=word,
        front_of_card=word,
        ipa=ipa,
        definitions=definition,
        example_sentence=sentence,
        translation=translation,
        word_audio="",
        sentence_audio="",
        image="",
    )
    deck.add_note(build_multilang_note(row, model=preview_model))

output.unlink(missing_ok=True)
package = genanki.Package(deck)
package.media_files = []
package.write_to_file(str(output))
assert output.is_file() and output.stat().st_size > 0
print(f"created {output} with {len(cards)} notes and IDs {preview_model_id}/{preview_deck_id}")
""")'
```

    Criar dois bundles separados para que evidência humana pendente não contamine o fechamento automatizado. Ambos devem usar um único JSON cercado e os campos exigidos pelo helper local: `proof_bundle_version`, `scope`, `route_state`, `environment`, `viewport`, `evidence_inputs`, `commands_or_manual_steps`, `observations`, `artifacts`, `privacy`, `result` e `claim_limits`. Cada artifact deve declarar `visibility`, `retention`, `sensitivity` e `safe_to_publish`; nenhum screenshot é exigido.

    Em `UI-PROOF.md`, declarar **somente** `compact-fields-code-test-apkg` em `scope.slot_ids`. Copiar literalmente do slot planejado seu `claim`, `route_state`, `environment`, `viewport` e `claim_limit`. Usar somente `code` e `test` em `evidence_inputs.kinds`; todos os commands e todas as observations deste bundle devem ter `result: passed`. Copiar como texto integral as cinco strings de `minimum_observations` do slot code/test, distribuindo-as entre evidências `code` e `test`, e registrar RED correto, GREEN, suíte focada e inspeção APKG. Definir `result.claim_status: passed` e `result.comparison_status_by_slot.compact-fields-code-test-apkg: satisfied`. Não incluir slot, passo, observação, status ou claim humano/deferred neste arquivo.

    Em `NATIVE-ANKI-RECHECK.md`, declarar **somente** `compact-fields-native-anki-recheck` em `scope.slot_ids`, novamente com `claim`, `route_state`, `environment`, `viewport` e `claim_limit` literais. Usar somente `human` em `evidence_inputs.kinds` e `manual` em `tools_used`. Registrar como `commands_or_manual_steps` as três inspeções planejadas no Anki e como `observations` as três strings integrais de `minimum_observations` do slot humano; enquanto não houver reavaliação real, todos esses passos e observações têm `result: deferred`. Definir `result.claim_status: deferred`, `result.comparison_status_by_slot.compact-fields-native-anki-recheck: deferred` e o metadado `native_acceptance_status: human_needed`.

    Por D-06, colocar no sidecar nativo `uat_history` com `previous_uat_status: failed`, motivo `espaçamento excessivo entre fields no APKG anterior`, `current_uat_status: human_needed` e `current_artifact: german_frequency_template_dummy.apkg` com IDs `1995037001/1995037002`. Isso registra o feedback humano já recebido sem adicionar uma observação `passed` para o novo APKG.

    Depois de validar os dois bundles separadamente, executar a comparação determinística definida em `<verify>`. Ela cria somente em `/tmp` a representação JSON literal dos dois slots planejados, chama o helper local real contra ambos os bundles e exige: slot automático `satisfied` sem issues; slot nativo `partial` somente pelos códigos de falta de aceite humano decorrentes dos estados `deferred`; nenhum erro de parsing/metadata, drift de observação mínima, artifact type ou claim literal.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py::test_normal_and_mandarin_panels_use_responsive_viewport_height -q</automated>
    <automated>uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q</automated>
    <automated>PYTHONPATH=src uv run python -c 'exec("""from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile
import json
import re
import sqlite3

from multilang.services.export_anki_package import DECK_ID, MODEL_ID

path = Path("german_frequency_template_dummy.apkg")
preview_model_id = 1_995_037_001
preview_deck_id = 1_995_037_002
assert path.is_file() and path.stat().st_size > 0 and is_zipfile(path)

with ZipFile(path) as archive, TemporaryDirectory() as temp_dir:
    assert "collection.anki2" in archive.namelist()
    database = Path(temp_dir) / "collection.anki2"
    database.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(database) as connection:
        note_count = connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        card_count = connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        model_ids = {row[0] for row in connection.execute("SELECT DISTINCT mid FROM notes")}
        deck_ids = {row[0] for row in connection.execute("SELECT DISTINCT did FROM cards")}
        fields = [row[0].split("\\x1f") for row in connection.execute("SELECT flds FROM notes")]
        models_raw, decks_raw = connection.execute("SELECT models, decks FROM col").fetchone()

model = json.loads(models_raw)[str(preview_model_id)]
deck = json.loads(decks_raw)[str(preview_deck_id)]
css = model["css"]
blocks = [declarations for selectors, declarations in re.findall(r"([^{}]+)\\{([^{}]*)\\}", re.sub(r"/\\*.*?\\*/", "", css, flags=re.DOTALL)) if ".customCard" in {item.strip() for item in selectors.split(",")}]
assert blocks
final_block = blocks[-1]
values = lambda name: re.findall(rf"(?:^|[;\\s]){re.escape(name)}:\\s*([^;]+);", final_block)

assert note_count == card_count == 7
assert model_ids == {preview_model_id} and MODEL_ID not in model_ids
assert deck_ids == {preview_deck_id} and DECK_ID not in deck_ids
assert "Q037" in model["name"] and "Q037" in deck["name"]
assert values("display")[-1].strip() == "block"
assert all(not values(name) for name in ("flex-direction", "justify-content", "align-items"))
assert values("min-height")[-1].strip() == "min(760px, calc(100vh - 80px))"
assert values("padding")[-1].strip() == "clamp(24px, 4vh, 40px) 24px"
assert values("width")[-1].strip() == "100%"
assert values("max-width")[-1].strip() == "460px"
assert all(len(parts) == 9 for parts in fields)
assert all(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] for parts in fields)
assert all(parts[6] == parts[7] == parts[8] == "" for parts in fields)
print("APKG OK: 7 notes/cards, compact final block, preserved geometry, IDs 1995037001/1995037002")
""")'</automated>
    <automated>git check-ignore -q "german_frequency_template_dummy.apkg"</automated>
    <automated>node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/037-compactar-espacamento-fields/UI-PROOF.md</automated>
    <automated>node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md</automated>
    <automated>uv run python -c 'exec("""from pathlib import Path
import json
import subprocess

claim = "O APKG alemão Quick 037 preserva o painel alto/centralizado e apresenta os fields em fluxo compacto sem os vazios artificiais do flex space-between."
route = "Gerar o APKG Quick 037 com o template normal corrigido; inspecionar CSS, testes e estrutura e importar o mesmo arquivo no Anki para frente, verso e card longo."
environment = "Python 3.12+ e serviços locais para code/test/APKG; Anki nativo para aceitação humana; sem rede/providers."
viewport = "Contrato CSS responsivo preservado; tamanho real do Anki usado pelo usuário na reavaliação, sem alegar pixels antes dela."
claim_limit = "Automação prova CSS, regressões e estrutura do APKG; aceitação da aparência compacta no Anki permanece human_needed até observação humana do APKG com IDs 1995037001/1995037002."

slots = [
    {
        "slot_id": "compact-fields-code-test-apkg",
        "claim": claim,
        "route_state": route,
        "required_evidence_kinds": ["code", "test"],
        "minimum_observations": [
            "O bloco final de .customCard usa display: block e não contém flex-direction, justify-content ou align-items.",
            "Min-height, padding, width, visual e centralização externa permanecem com os valores anteriores.",
            "Normal e as duas rotas Mandarin recebem o fluxo compacto pelo CSS normal compartilhado.",
            "Os dois arquivos pytest focados passam após o RED esperado.",
            "O APKG contém sete notes, CSS block compacto e somente os IDs 1995037001/1995037002.",
        ],
        "expected_artifact_types": [
            "css inspection report",
            "focused pytest output",
            "apkg structural report",
            "ui-proof metadata",
        ],
        "validation_command": "node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/037-compactar-espacamento-fields/UI-PROOF.md",
        "environment": environment,
        "viewport": viewport,
        "manual_acceptance_required": False,
        "claim_limit": claim_limit,
    },
    {
        "slot_id": "compact-fields-native-anki-recheck",
        "claim": claim,
        "route_state": route,
        "required_evidence_kinds": ["human"],
        "minimum_observations": [
            "No Anki, um card curto mantém o painel alto e centralizado, mas os fields aparecem compactos sem grandes vazios artificiais.",
            "No Anki, o verso revela Translation e preserva definição, imagem vazia e controles de áudio sem regressão visual.",
            "No Anki, o card de conteúdo longo permanece legível e cresce ou rola naturalmente sem clipping.",
        ],
        "expected_artifact_types": ["human anki observation"],
        "validation_command": "node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md",
        "environment": environment,
        "viewport": viewport,
        "manual_acceptance_required": True,
        "claim_limit": claim_limit,
    },
]

planned_path = Path("/tmp/quick-037-ui-proof-slots.json")
planned_path.write_text(json.dumps({"ui_proof_slots": slots}, ensure_ascii=False, indent=2), encoding="utf-8")
completed = subprocess.run(
    [
        "node",
        ".planning/bin/gsdd.mjs",
        "ui-proof",
        "compare",
        str(planned_path),
        ".planning/quick/037-compactar-espacamento-fields/UI-PROOF.md",
        ".planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md",
    ],
    capture_output=True,
    text=True,
    check=False,
)
assert completed.returncode == 1, (completed.returncode, completed.stdout, completed.stderr)
comparison = json.loads(completed.stdout)
assert comparison["status"] == "partial"
assert comparison["errors"] == []
by_slot = {entry["slot_id"]: entry for entry in comparison["slots"]}
automatic = by_slot["compact-fields-code-test-apkg"]
native = by_slot["compact-fields-native-anki-recheck"]
assert automatic["status"] == "satisfied" and automatic["issues"] == []
assert native["status"] == "partial"
native_issue_codes = {issue["code"] for issue in native["issues"]}
expected_human_only_codes = {
    "unsatisfied_observed_claim_status",
    "unsatisfied_observed_comparison_status",
    "missing_supporting_observation_evidence_kind",
    "unsatisfied_proof_step",
    "missing_manual_acceptance_observation",
    "unsatisfied_observation_result",
}
assert native_issue_codes == expected_human_only_codes, native["issues"]
print("UI proof compare OK: automatic satisfied/no issues; native partial only for deferred human acceptance")
""")'</automated>
    <automated>git diff --check -- "tests/services/test_card_template_loader.py" "src/multilang/templates/normal_card.md" ".planning/quick/037-compactar-espacamento-fields/UI-PROOF.md" ".planning/quick/037-compactar-espacamento-fields/NATIVE-ANKI-RECHECK.md" ".planning/quick/037-compactar-espacamento-fields/037-PLAN.md"</automated>
  </verify>
  <done>D-01 a D-07 estão entregues: CSS block compacto, geometria/visual preservados, normal/Mandarin e export verdes, APKG de sete cards com IDs novos validado offline, slot code/test satisfeito sem issues e sidecar nativo deferred/human_needed somente por falta da nova inspeção humana no Anki.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| CSS/template live → renderer Anki | Conteúdo de fields com comprimentos variáveis é renderizado dentro do painel responsivo. |
| Modelo/dados locais → APKG importado | Template e sete registros fixos são empacotados sob novas identidades de preview. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q037-01 | Denial of service | Fluxo do `.customCard` | mitigate | Restaurar block sem height/max-height rígida e preservar wrapping/min-height para conteúdo longo crescer ou rolar naturalmente. |
| T-Q037-02 | Tampering | IDs do modelo/deck APKG | mitigate | Usar IDs fixos novos 1995037001/1995037002 e inspecionar SQLite/JSON contra IDs de produção. |
| T-Q037-03 | Information disclosure / SSRF | Geração do dummy | mitigate | Usar apenas dados fictícios fixos e serviços locais, sem mídia, conteúdo de usuário, rede ou providers. |
| T-Q037-04 | Tampering / Elevation | Markup e interpolação Anki | accept | O boundary existente não muda; o patch de produção é somente CSS e os contratos de template/export focados devem permanecer verdes. |
</threat_model>

## Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Compactar o espaçamento excessivo observado no dummy alemão sem perder o painel alto/responsivo | Tasks 037-01 e 037-02 |
| REQ | Quick mode não possui requirement IDs de ROADMAP | N/A (`requirements: []`) |
| RESEARCH | Root cause confirmada: flex column + space-between e margens sem colapso no painel com min-height | Teste RED e correção CSS exata nas duas tasks |
| CONTEXT | D-01/D-02: display block, remoção das três declarações e preservação visual | Teste efetivo + patch mínimo na Task 037-02 |
| CONTEXT | D-03: sem markup/outros templates; Mandarin herda normalmente | Assertions normal/Mandarin e limites de arquivo |
| CONTEXT | D-04: RED → GREEN e somente dois arquivos pytest | Ordem das tasks e comandos nominais/focados |
| CONTEXT | D-05: APKG substituído, sete cards, IDs novos, offline e verificação mínima | Gerador e inspeção SQLite/APKG da Task 037-02 |
| CONTEXT | D-06: UAT anterior falhou; novo UAT human_needed | Bundle automático isolado e `uat_history`/deferred no sidecar nativo |
| CONTEXT | D-07: sem artefatos 035/036, lifecycle docs ou ações Git | Hard boundaries, actions e success criteria |

Exclusões sem gap: mudanças de markup/campos/margens/Translation/mídia/loader/export, outros templates, rede/providers, suíte ampla, screenshots obrigatórios, edição de Quicks 035/036 e qualquer branch/stage/commit.

## Success Criteria

- Exatamente duas tasks executam TDD RED → GREEN e cada uma possui comando automatizado executável.
- O último bloco de `.customCard` usa `display: block` e não contém `flex-direction`, `justify-content` ou `align-items`; nenhum outro valor visual muda.
- Apenas `tests/services/test_card_template_loader.py` e `tests/integration/test_v13_normal_template_export_contract.py` são executados como testes.
- Normal e Mandarin passam o contrato compartilhado, e o teste de integração permanece verification-only.
- `german_frequency_template_dummy.apkg` contém sete cards, campos/media esperados, CSS corrigido e somente IDs 1995037001/1995037002.
- `UI-PROOF.md` declara somente o slot code/test, contém apenas passos/observações `passed` e fecha como `passed`/`satisfied` sem issues.
- `NATIVE-ANKI-RECHECK.md` declara somente o slot humano, preserva o UAT anterior `failed` e mantém passos/observações e novo aceite como `deferred`/`human_needed`.
- Ambos os bundles passam `node .planning/bin/gsdd.mjs ui-proof validate`; a comparação determinística retorna auto `satisfied` sem issues e nativo `partial` somente pelos estados humanos deferred.
- O executor cria `.planning/quick/037-compactar-espacamento-fields/037-SUMMARY.md`; nenhum artefato 035/036, ROADMAP/SPEC/STATE/LOG ou ação Git é alterado.

## Output

Após concluir as duas tasks, criar `.planning/quick/037-compactar-espacamento-fields/037-SUMMARY.md` com RED/GREEN, testes focados, inspeção APKG, IDs, validações/comparação dos dois bundles e status final `human_needed`, sem stage/commit.

## Quick Plan Self-Check

- Task count: 2, dentro do limite quick solicitado.
- Ambas as tasks têm `<action>`, `<verify>` e comandos reproduzíveis.
- Cada decisão D-01 a D-07 aparece em action/verify/done e nenhuma ideia fora do escopo foi incluída.
- `minimum_observations` usa listas textuais nos dois slots; não usa contagens numéricas.
- Write scope: dois arquivos rastreados, um APKG gitignored, dois bundles de proof e o summary executor-owned.
