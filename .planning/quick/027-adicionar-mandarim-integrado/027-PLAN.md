---
phase: quick-027-adicionar-mandarim-integrado
plan: "027"
type: execute
wave: 1
runtime: opencode
assurance: self_checked
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/planner.md não existe; o plano foi produzido pelo contrato quick fornecido pelo usuário e autocheck do planner, sem role template nem checker independente."
depends_on: []
autonomous: false
requirements: []
files_modified:
  - pyproject.toml
  - uv.lock
  - src/multilang/domain/jobs.py
  - src/multilang/domain/exporting.py
  - src/multilang/settings.py
  - src/multilang/runtime.py
  - src/multilang/db/models.py
  - src/multilang/repositories/export_repository.py
  - src/multilang/services/provider_text_adapters.py
  - src/multilang/services/provider_pronunciation_adapters.py
  - src/multilang/services/local_text_adapter.py
  - src/multilang/services/tatoeba_sentence_source.py
  - src/multilang/services/language_identifier.py
  - src/multilang/services/lexical_grounding.py
  - src/multilang/services/part_of_speech.py
  - src/multilang/services/text_validation.py
  - src/multilang/services/audio_voice_registry.py
  - src/multilang/services/elevenlabs_speech_adapter.py
  - src/multilang/services/google_translate_speech_adapter.py
  - src/multilang/services/frequency_decks.py
  - src/multilang/services/mandarin_orthography.py
  - src/multilang/services/generate_audio_items.py
  - src/multilang/services/assemble_export_cards.py
  - src/multilang/services/card_template_loader.py
  - src/multilang/services/export_anki_package.py
  - src/multilang/templates/mandarin_card.md
  - scripts/build_frequency_assets.py
  - assets/frequency/zh/curated-v1.csv
  - assets/frequency/zh/rejections-v1.csv
  - alembic/versions/20260720_15_mandarin_export_fields.py
  - tests/domain/test_jobs.py
  - tests/domain/test_exporting.py
  - tests/test_settings.py
  - tests/test_migration_schema_parity.py
  - tests/repositories/test_export_repository.py
  - tests/services/test_mandarin_language_support.py
  - tests/services/test_mandarin_orthography.py
  - tests/services/test_text_validation.py
  - tests/services/test_frequency_decks.py
  - tests/services/test_generate_audio_items.py
  - tests/services/test_assemble_export_cards.py
  - tests/services/test_card_template_loader.py
  - tests/services/test_export_anki_package.py
  - tests/services/test_export_tabular_bundle.py
  - tests/integration/test_mandarin_modern_flow.py
  - .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md
  - .planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg
non_goals:
  - Não importar, abrir durante execução, copiar ou transformar cards, notas, mídia, CSS ou JavaScript de `Mandarin nivel 1.apkg`.
  - Não reproduzir o template Migaku, seus scripts de tons, screenshots ou flags.
  - Não adicionar Mandarim aos fluxos de Kindle highlights, kana, fonemas ou Latin MVP; o escopo é frequency e word-list do fluxo moderno.
  - Não alterar o contrato visual de `normal_card.md` nem os note types já existentes.
  - Não corrigir a falha Windows preexistente de `tests/services/test_japanese_furigana.py`.
hard_boundaries:
  - `Image` continua sendo a string vazia em todo snapshot e export Mandarim.
  - Os quatro valores derivados de ortografia chinesa são congelados no snapshot; nenhum export pode recalculá-los silenciosamente.
  - Testes não fazem chamadas reais a LLM, DeepL, Tatoeba, Azure, ElevenLabs ou Google TTS.
  - Não tocar/reverter os relatórios Danish removidos nem `jap-back.png`, `jap-front.png`, `jap1.png`, `jap2.png` e `japonese.md` não rastreados.
escalation_triggers:
  - Parar se a filtragem/normalização documentada de `wordfreq:zh` não produzir 3000 entradas Han simplificadas dentro do limite de varredura, em vez de relaxar o contrato de script.
  - Parar se o head Alembic deixar de ser `20260714_14` antes da criação da revisão, em vez de criar branches de migration concorrentes sem confirmação.
  - Parar se `pypinyin` 0.55.x ou `opencc-python-reimplemented` 0.1.7 não funcionar em Python 3.12, registrando o mismatch factual antes de trocar biblioteca.
  - Parar se suportar `zh` com locale de conteúdo/TTS `zh-CN` exigir mutar field order ou template de outro idioma; Mandarim deve permanecer um note type separado.
approval_gates:
  - Antes da Task 027-01, exigir aceite explícito do risco residual de escopo deste quick task (47 arquivos/artefatos, três subsistemas e três ondas) ou aprovação para convertê-lo em fase/múltiplos planos; `continue` genérico não conta como aceite do risco.
  - A afirmação de posicionamento/legibilidade real exige revisão humana em Anki Desktop e em um cliente móvel; testes estáticos não substituem essa aprovação.
  - Qualquer chamada paga/real de provider ou publicação de screenshots exige autorização explícita; a implementação e os testes permanecem offline/mocados.
anti_regression_targets:
  - Os idiomas existentes continuam aceitos com os mesmos códigos, field sets, note types, templates e políticas de áudio.
  - Word-list não Mandarim continua com seu contrato atual e somente sentence audio; apenas `zh` usa o field set Mandarim com word e sentence audio.
  - Japanese frequency continua usando furigana e seu template próprio; a falha Windows conhecida não é alterada nem usada como evidência.
  - Os fluxos frequency/word-list existentes e exports APKG/CSV/TSV continuam passando seus testes de integração.
known_unknowns:
  - O repositório não contém renderer Anki; a geometria e a legibilidade reais em Desktop/mobile só podem ser observadas por uma pessoa após importação.
  - Pinyin de nomes próprios ou leituras raras pode exigir curadoria de conteúdo; o contrato desta entrega é derivação determinística, phrase-aware, com tons e falha fechada para saída vazia/script inválido.
ui_proof_slots:
  - slot_id: mandarin-anki-static-contract
    claim: "O note type Mandarim mantém a linguagem visual Multilang e coloca Simplificado, pinyin, Tradicional, frase e áudios na hierarquia definida, com Translation oculta na frente."
    route_state: "build_multilang_model(source_type='frequency' e 'word-list', language=SupportedLanguage.ZH), front/back do template e modelo dentro do APKG"
    required_evidence_kinds: [code, test, runtime]
    minimum_observations: 6
    expected_artifact_types: ["assertions de template/field order", "inspeção SQLite do collection.anki2", "resolução do media map APKG", "inspeção de headers/sound tags CSV", "inspeção de headers/sound tags TSV", "APKG persistente com SHA-256"]
    validation_command: "uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/integration/test_mandarin_modern_flow.py -q"
    environment: "Python 3.12 + genanki + inspeção de APKG/SQLite; sem renderer Anki"
    viewport: "não aplicável à prova automatizada; o CSS declara max-width de 400px"
    manual_acceptance_required: false
    claim_limit: "Prova somente field order, referências de template, ordem estrutural, CSS Multilang presente, Translation front-hidden e estrutura APKG/CSV/TSV; não prova pixels ou legibilidade em Anki."
  - slot_id: mandarin-anki-desktop-mobile-render
    claim: "A posição e a legibilidade do pinyin e das linhas tradicionais são adequadas no Anki Desktop e em cliente móvel, na frente e no verso."
    route_state: "Importar `.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg`, gerado para `SupportedLanguage.ZH`, e observar a mesma nota na frente e no verso em Desktop e Google Pixel 7/AnkiDroid."
    required_evidence_kinds: [human]
    minimum_observations: 4
    expected_artifact_types: ["APKG persistente com SHA-256 registrado", "checklist manual Desktop front/back", "checklist manual Google Pixel 7/AnkiDroid front/back"]
    validation_command: "npx -y gsdd-cli ui-proof validate .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md"
    environment: "Anki Desktop atual em desktop 1280x800 e AnkiDroid em Google Pixel 7; indisponíveis no ambiente automatizado do repositório"
    viewport: "Desktop 1280x800 e Google Pixel 7/AnkiDroid 412x915 portrait"
    manual_acceptance_required: true
    claim_limit: "Permanece human_needed até observação humana; ausência de renderer não autoriza alegar posicionamento visual real."
high_leverage_surfaces:
  - src/multilang/domain/exporting.py
  - src/multilang/db/models.py
  - src/multilang/services/assemble_export_cards.py
  - src/multilang/services/export_anki_package.py
  - src/multilang/runtime.py
second_pass_required: true
closure_claim_limit: "Concluir integração e regressões somente após os comandos automatizados passarem; limitar a conclusão visual a contrato estático até aprovação humana Anki Desktop/mobile."
scope_sanity:
  status: acceptance_required
  estimated_files_and_artifacts: 47
  residual_risk: "O escopo cruza contratos/providers/assets, persistência/migration e três exporters; excede o orçamento normal de contexto de um quick task, mas não pode ser reduzido sem violar D-01..D-06."
  execution_policy: "Uma onda por contexto de execução, com entry/exit gate obrigatório; não iniciar 027-01 sem aceite explícito do risco ou aprovação de split."
parallelism_budget:
  max_concurrent_plans: 1
  safe_parallelism: []
leverage:
  lost: "O plano toca vários registries e a migration porque `zh` atravessa o pipeline inteiro com locale `zh-CN`; não mascara esse custo com recomputação ou campos genéricos."
  kept: "CLI moderno, separação service/repository, assets congelados, normal_card como linguagem visual, genanki e adapters de áudio existentes."
  gained: "Ortografia Mandarim determinística e snapshots exportáveis/auditáveis em todos os formatos sem dependência do deck de referência."
must_haves:
  truths:
    - "Usuário pode selecionar `zh` em generation requests frequency e word-list e obter conteúdo Simplificado (`zh-CN`) validado e word/sentence audio."
    - "O asset frequency `zh` contém exatamente 3000 entradas, 1000 por nível, provenientes de wordfreq:zh e normalizadas para Han Simplificado."
    - "Cada card Mandarim exportável contém pinyin com marcas de tom e Tradicional para a palavra e para a frase, persistidos no snapshot."
    - "APKG, CSV e TSV usam o mesmo field order Mandarim estável, incluem ambos os áudios e mantêm Image vazio."
    - "O template usa a base visual de normal_card: palavra Simplificada no topo, pinyin logo abaixo, Tradicional auxiliar, frase Simplificada com áudio, sentence pinyin/Tradicional abaixo e Translation somente no verso."
    - "Nenhum conteúdo, mídia, CSS ou JavaScript do APKG de referência é incorporado."
    - "Os fluxos e exports não Mandarim continuam com seus contratos atuais."
  artifacts:
    - path: src/multilang/services/mandarin_orthography.py
      provides: "Validação Simplificado/Han, pinyin phrase-aware com tons e conversão s2t determinística."
    - path: assets/frequency/zh/curated-v1.csv
      provides: "Lista congelada de 3 níveis x 1000 entradas `zh`, com formas canônicas Simplificadas."
    - path: alembic/versions/20260720_15_mandarin_export_fields.py
      provides: "Persistência dos quatro valores Mandarim sem quebrar snapshots legados."
    - path: src/multilang/templates/mandarin_card.md
      provides: "Template Anki Mandarim derivado somente do normal_card do projeto."
    - path: tests/integration/test_mandarin_modern_flow.py
      provides: "Prova offline de frequency/word-list, texto, áudio, snapshots e APKG/CSV/TSV."
    - path: .planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg
      provides: "Artefato persistente exato usado na gate visual Desktop/AnkiDroid."
    - path: .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md
      provides: "Hash, ambiente, viewports, limites de claim e estado human_needed sem observações fabricadas."
  key_links:
    - from: scripts/build_frequency_assets.py
      to: assets/frequency/zh/curated-v1.csv
      via: "código canônico `zh` compartilhado com wordfreq e normalização Simplificado/Han"
    - from: src/multilang/services/assemble_export_cards.py
      to: src/multilang/services/mandarin_orthography.py
      via: "derivação única antes de persistir o ExportCardRow"
    - from: src/multilang/repositories/export_repository.py
      to: src/multilang/db/models.py
      via: "round-trip dos quatro campos Mandarim"
    - from: src/multilang/services/generate_audio_items.py
      to: src/multilang/domain/exporting.py
      via: "resolução de field set por language + source para exigir dois áudios em word-list `zh`"
    - from: src/multilang/services/export_anki_package.py
      to: src/multilang/templates/mandarin_card.md
      via: "note model Multilang::Mandarin Card para frequency e word-list"
    - from: src/multilang/runtime.py
      to: src/multilang/services/export_anki_package.py
      via: "snapshots persistidos e routing de note type/mídia para APKG/CSV/TSV"
    - from: tests/integration/test_mandarin_modern_flow.py
      to: .planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg
      via: "helper offline write_mandarin_proof_artifact com dois áudios resolvíveis"
    - from: .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md
      to: .planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg
      via: "path, byte size e SHA-256 do mesmo arquivo importado na gate humana"
---

# Quick Task 027: Adicionar Mandarim ao fluxo moderno

## Objective

Adicionar Mandarim Simplificado como idioma completo dos fluxos modernos frequency e word-list, usando `SupportedLanguage.ZH = "zh"` como código canônico público/interno e `zh-CN` somente como locale/variante de conteúdo e TTS, com geração/validação de texto, áudio, pinyin tonal e Tradicional para palavra e frase, snapshots persistidos e export APKG/CSV/TSV em um note type próprio que conserva a linguagem visual Multilang.

O arquivo `Mandarin nivel 1.apkg` é somente inspiração conceitual já resumida no contexto do usuário. A execução não o lê nem o usa como fonte; os únicos conceitos reaproveitados são campos pedagógicos abstratos (Simplificado, pinyin tonal, Tradicional e áudio separado), implementados sobre contratos e template do próprio projeto.

## Reduced Assurance

- `.planning/templates/roles/planner.md` foi procurado primeiro e não existe.
- Este artefato registra `reduced_assurance: true` e usa autocheck no mesmo runtime; nenhum checker independente foi alegado.
- A consulta Context7 confirmou os IDs de `pypinyin` e `opencc-python`; a página de docs do pypinyin respondeu com verificação anti-bot, então API/versão foram conferidas também no README oficial e PyPI (`pypinyin` 0.55.0; `opencc-python-reimplemented` 0.1.7).
- A consulta Context7 de 2026-07-20 à referência oficial ElevenLabs confirmou `language_code` ISO 639-1 opcional, explicitamente incompatível com modelos `multilingual_v2`; exemplos atuais usam `eleven_flash_v2_5`, e o changelog declara suporte em Flash/Turbo/v3. O plano usa allowlist e omissão fail-closed para modelos desconhecidos.

## Locked Decisions

- **D-01:** Mandarim Simplificado é a forma principal e Tradicional é complementar; o código canônico público/interno é `zh`, enquanto `zh-CN` identifica somente locale/variante Simplificada onde o provider exige locale.
- **D-02:** palavra e frase exportam pinyin com marcas de tom e respectivas formas tradicionais.
- **D-03:** preservar layout/CSS/comportamento-base de `normal_card.md`; usar o posicionamento pedagógico descrito no pedido, sem template Migaku.
- **D-04:** `Image` permanece vazio.
- **D-05:** o APKG de referência não é fonte de importação/cópia de cards, notas, mídia, CSS ou JavaScript.
- **D-06:** frequency e word-list devem atravessar texto, word/sentence audio e APKG/CSV/TSV com testes offline e regressões não Mandarim.

## Context

- `AGENTS.md`
- `.planning/config.json`
- `src/multilang/domain/jobs.py`
- `src/multilang/domain/exporting.py`
- `src/multilang/repositories/export_repository.py`
- `src/multilang/services/assemble_export_cards.py`
- `src/multilang/services/generate_audio_items.py`
- `src/multilang/services/export_anki_package.py`
- `src/multilang/services/export_tabular_bundle.py`
- `src/multilang/services/card_template_loader.py`
- `src/multilang/templates/normal_card.md`
- `scripts/build_frequency_assets.py`

## Must-Haves

1. `zh` é aceito pelos contratos e por ambos os modos modernos como único código canônico; `zh-CN` aparece somente em locale/voz/provider e nunca em enum, request, asset path ou coluna `language`.
2. Texto primário e candidatos frequency são Simplificado/Han; saída Latina, kana-dominante/Japonesa, Tradicional como primária ou sem target substring falha antes do export.
3. Pinyin é phrase-aware (`Style.TONE`, sem heterônimos múltiplos), usa marcas de tom e preserva pontuação sem espaços artificiais; OpenCC `s2t` produz Tradicional.
4. Os quatro campos derivados sobrevivem a commit/expire/reload do banco e são consumidos sem recomputação após o snapshot.
5. Frequency e word-list `zh` usam exatamente: `SortIndex`, `word`, `Pinyin`, `Traditional`, `Definitions`, `Example Sentence`, `Sentence Pinyin`, `Traditional Sentence`, `Translation`, `word_audio`, `sentence_audio`, `Image`.
6. O note type é `Multilang::Mandarin Card`, com model id estável `1762800901`, e os três formatos preservam field order/UTF-8/áudios/Image vazio.
7. A prova automatizada fica limitada ao contrato estático; renderização real Desktop/mobile fica explicitamente `human_needed`.

## Anti-Goals

- Não criar comando paralelo de deck Mandarim nem um importador do APKG de referência.
- Não alterar `normal_card.md`; criar `mandarin_card.md` a partir da estrutura interna existente.
- Não habilitar highlights Mandarim, scripts de cor por tom, screenshots ou campos Migaku.
- Não remediar arquivos Japanese/Danish fora deste write set.

## Hard Boundaries

- Persistência é obrigatória: não guardar os valores somente em propriedades transitórias, JSON implícito ou cálculo no export.
- As colunas novas podem ser nullable para rows legadas, mas um `ExportCardRow` `zh` frequency/word-list deve exigir os quatro valores não vazios.
- Routing deve considerar **language + source_type**; alterar globalmente o profile word-list quebraria idiomas existentes.
- Conteúdo inserido no template passa pelo escaping já usado pelo assembler; nenhum provider pode fornecer HTML/JS executável para os campos ortográficos.

## Dependencies / Order

| Task | Needs | Creates | Order rationale |
|---|---|---|---|
| 027-01 / Wave 1 | Aceite explícito do risco de escopo + baseline dos testes existentes | `zh` registrado, dependências, serviço ortográfico, validação e assets 3000 | Fundação consumida pelos snapshots/export; exit gate exige geração real seguida de `--check` e focused tests verdes |
| 027-02 / Wave 2 | Exit gate 027-01 + head Alembic único `20260714_14` | Field contract, migration, round-trip e assembly/audio row-aware | Congela dados antes de conectá-los a formatos; exit gate exige head único `20260720_15`, upgrade SQLite e round-trip verde |
| 027-03 / Wave 3 | Exit gate 027-02 + snapshot reload comprovado | Template/model/routing APKG/CSV/TSV, APKG de prova persistente, E2E e UI proof | Export consome somente contratos persistidos completos; exit gate exige APKG/hash, regressões e UI proof validator |

Execução é estritamente sequencial, uma wave por contexto de execução. `runtime.py` é compartilhado pelas Tasks 027-01 e 027-03 e os contratos da Task 027-02 são consumidos pela Task 027-03; não executar tarefas em paralelo nem avançar quando um exit gate falhar.

## Scope Sanity / Required Acceptance

- O write set revisado contém 47 arquivos/artefatos e atravessa três subsistemas acoplados. Isso excede deliberadamente o orçamento normal de um quick task e continua sendo um blocker de `scope_sanity`, não um plano falsamente classificado como pequeno.
- D-01..D-06 e o limite solicitado de três tasks impedem reduzir funcionalidade ou decompor silenciosamente. A mitigação é uma task/wave por contexto, gates fail-closed e segunda passada sobre superfícies de alto impacto.
- **Gate bloqueante:** antes de executar 027-01, obter do usuário uma resposta explícita equivalente a `aceito o risco residual de escopo do quick 027`; caso contrário, converter o trabalho em fase/múltiplos planos. Um “continue” genérico autoriza esta revisão, não aceita o risco de execução.

## Evidence Contract

- **Code:** registries, serviço ortográfico, migration/model/repository, field routing e template existem e estão ligados ao runtime.
- **Test:** testes unitários e E2E offline cobrem todos os itens enumerados no pedido.
- **Runtime:** builder gera e depois valida o asset `zh` real; integração CLI usa fake TTS e providers locais/mocados para gerar exports, incluindo o APKG persistente de prova com SHA-256 registrado.
- **Human:** somente posicionamento/legibilidade no Anki Desktop 1280x800 e Google Pixel 7/AnkiDroid 412x915 portrait; `observations` permanece `[]`, sem screenshots ou alegação visual, até ação humana posterior.
- **Delivery:** não há alegação de release/publicação neste quick task.

## Common Pitfalls

- Propagar `zh-CN` como enum/request/path cria duas identidades para o mesmo idioma; manter `zh` canônico e limitar `zh-CN` a locale/voz/provider.
- Reaproveitar `IPA` ou campos Japanese perde o contrato de pinyin/Tradicional e pode não persistir; usar quatro campos Mandarim próprios.
- Resolver fields somente por source_type faz word-list `zh` omitir word audio/Translation; usar helper language-aware em assembly, geração de áudio, runtime e packaging.
- Truncar locale com `split("-")[0]` faz Google TTS enviar `tl=zh`; Mandarim deve enviar exatamente `tl=zh-CN`.
- Enviar `language_code` com `eleven_multilingual_v2` viola o contrato ElevenLabs; omiti-lo nesse modelo e serializar `zh` somente para modelos explicitamente compatíveis.
- Tratar sentence chinesa como tokens separados por espaço faz Tatoeba rejeitar conteúdo válido; usar contagem Han e substring normalizada para `zh`.
- Aceitar qualquer CJK permite frases Japanese com kanji+kana; contar Han/kana/Latin e exigir Simplificado canônico.
- `lazy_pinyin` pode devolver pontuação como tokens; renderizar espaços somente entre sílabas pinyin, não antes de pontuação.
- Um teste do objeto em memória não prova snapshot; expirar a sessão e recarregar antes de assertar.
- Não usar a falha Japanese preexistente como sinal de sucesso/falha Mandarim.

## Stop-And-Challenge

- Acionar os `escalation_triggers` do frontmatter sem reduzir contagem, script, campos, persistência, áudio ou formatos.
- Se o model id proposto já estiver em uso no repositório durante execução, parar e escolher outro id estável após busca comprovada; não reutilizar identidade de note type existente.
- Se o E2E word-list gerar apenas sentence audio, corrigir todos os consumidores do helper language-aware; não enfraquecer o teste.

## Approval Gates

- Toda implementação e verificação automatizada ocorre antes da revisão humana.
- Após os testes, manter o APKG `artifacts/mandarin-proof.apkg` e seu SHA-256 no proof bundle e solicitar que o usuário observe frente/verso no Anki Desktop 1280x800 e Google Pixel 7/AnkiDroid 412x915 portrait. Sem essa observação, `mandarin-anki-desktop-mobile-render` permanece `human_needed`, `observations: []` e sem screenshots fabricados.

<checks>
<plan_check>
checker: self
checker_runtime: opencode
status: issues_found
blocking: true
notes: "Revisão/autocheck endereçou identidade `zh` versus locale `zh-CN`, geração real de assets, topology/upgrade Alembic, contratos de ElevenLabs/Google/Tatoeba, semântica de mídia e APKG/UI proof persistentes. Permanece somente o blocker honesto de scope_sanity (47 arquivos/artefatos); execução exige aceite explícito ou split. Assurance reduzida porque o role template e checker independente não estão disponíveis."
</plan_check>
</checks>

## Tasks

<task id="027-01" type="auto" tdd="true">
  <name>Registrar zh e criar geração, ortografia, validação e frequência determinísticas</name>
  <files>
    - MODIFY: pyproject.toml
    - MODIFY: uv.lock
    - MODIFY: src/multilang/domain/jobs.py
    - MODIFY: src/multilang/settings.py
    - MODIFY: src/multilang/runtime.py
    - MODIFY: src/multilang/services/provider_text_adapters.py
    - MODIFY: src/multilang/services/provider_pronunciation_adapters.py
    - MODIFY: src/multilang/services/local_text_adapter.py
    - MODIFY: src/multilang/services/tatoeba_sentence_source.py
    - MODIFY: src/multilang/services/language_identifier.py
    - MODIFY: src/multilang/services/lexical_grounding.py
    - MODIFY: src/multilang/services/part_of_speech.py
    - MODIFY: src/multilang/services/text_validation.py
    - MODIFY: src/multilang/services/audio_voice_registry.py
    - MODIFY: src/multilang/services/elevenlabs_speech_adapter.py
    - MODIFY: src/multilang/services/google_translate_speech_adapter.py
    - MODIFY: src/multilang/services/frequency_decks.py
    - CREATE: src/multilang/services/mandarin_orthography.py
    - MODIFY: scripts/build_frequency_assets.py
    - CREATE: assets/frequency/zh/curated-v1.csv
    - CREATE: assets/frequency/zh/rejections-v1.csv
    - MODIFY: tests/domain/test_jobs.py
    - MODIFY: tests/test_settings.py
    - CREATE: tests/services/test_mandarin_language_support.py
    - CREATE: tests/services/test_mandarin_orthography.py
    - MODIFY: tests/services/test_text_validation.py
    - MODIFY: tests/services/test_frequency_decks.py
  </files>
  <entry_checkpoint>
    - Gate humano bloqueante: confirmar que o usuário aceitou explicitamente o risco residual de escopo descrito em `Scope Sanity / Required Acceptance`; sem esse texto, não modificar arquivos.
    - Run `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_tatoeba_sentence_source.py tests/services/test_text_validation.py tests/services/test_frequency_decks.py -q` e registrar qualquer baseline que não seja causado por esta wave.
  </entry_checkpoint>
  <behavior>
    - RED first: requests/defaults accept only canonical `zh`; enum/path rows never use `zh-CN`.
    - RED first: phrase-aware pinyin and s2t conversion produce the specified word/sentence values and reject invalid scripts.
    - RED first: ElevenLabs omits `language_code` for `eleven_multilingual_v2`/unknown models and allowlisted Flash/Turbo/v3 models serialize `zh`; Google serializes `tl=zh-CN`, and Tatoeba serializes `from=cmn` with Han-aware matching.
    - RED first: a scan limited to 25000 either produces exactly 3000 Simplified/Han rows in 3x1000 or fails closed.
  </behavior>
  <action>
    - Adicionar `pypinyin>=0.55,<0.56` e `opencc-python-reimplemented>=0.1.7,<0.2` via uv e atualizar `uv.lock`. Usar as APIs documentadas `lazy_pinyin(..., style=Style.TONE, heteronym=False, v_to_u=True, neutral_tone_with_five=False, tone_sandhi=False)` e `OpenCC("s2t").convert(...)`; não gerar pinyin com LLM (D-02).
    - Adicionar `SupportedLanguage.ZH = "zh"`, o Literal/default correspondente e display name `Mandarin Chinese`. `GenerationRequest`, settings, persistence identity, paths e tags usam somente `zh`; `zh-CN` não é alias público nem segundo valor de enum. Cobrir frequency, word-list e a lista exata de defaults (D-01, D-06).
    - Criar `mandarin_orthography.py` com `MandarinOrthographyError`, um value object contendo `word_pinyin`, `word_traditional`, `sentence_pinyin`, `sentence_traditional`, e funções/serviço para: normalizar NFKC; contar Han/kana/Latin; exigir texto não vazio com Han predominante e sem kana/Latin dominante; confirmar Simplificado canônico com OpenCC `t2s`; converter para Tradicional com `s2t`; e produzir pinyin tonal phrase-aware. Formatar pontuação junto ao token anterior e falhar se qualquer derivado ficar vazio. Testar `中国 -> zhōng guó / 中國` e `我去银行。 -> wǒ qù yín háng。 / 我去銀行。`, incluindo uma leitura polifônica dependente da frase, saída inválida, Tradicional primário, Japanese e Latin (D-01, D-02).
    - Registrar os mapas do código canônico `zh`: nomes de provider e prompt de pronúncia; DeepL target `ZH-HANS`; templates locais em Simplificado; function-word POS chinês; Azure preferred `zh-CN-XiaoxiaoNeural` e same-locale alternate `zh-CN-YunxiNeural`. Incrementar `VOICE_REGISTRY_VERSION`. O prompt de sentence deve exigir explicitamente Simplified Chinese e proibir Tradicional/pinyin na sentence principal; pinyin é derivado localmente (D-01, D-06).
    - No ElevenLabs, manter `VoiceSelection.language=SupportedLanguage.ZH` e `locale="zh-CN"`, mas tratar o payload conforme capacidade do modelo: para o default e qualquer id da família `eleven_multilingual_v2`, omitir completamente `language_code`; usar uma allowlist explícita para `eleven_flash_v2_5`, `eleven_turbo_v2_5` e `eleven_v3`, que recebem `language_code: "zh"`; modelos desconhecidos também omitem fail-closed. Testar o JSON serializado para default, um allowlisted e um unknown, sem request real (D-01, D-06).
    - No Google Translate TTS, selecionar `voice_id/locale="zh-CN"` para Mandarim e impedir `_language_code()` de truncar esse locale; inspecionar a query mockada e exigir exatamente `tl=zh-CN`. Os demais idiomas preservam seus códigos atuais (D-01, D-06).
    - No Tatoeba, mapear `zh -> cmn` na API e tornar filtro/matching/scoring aware do target language: para `zh`, usar substring NFKC/casefold e contagem de Han para mínimo/comprimento em vez de tokenização por espaços. Testar query `from=cmn`, sentence chinesa sem espaços aceita quando contém o target e rejeitada quando não contém, sem rede (D-01, D-06).
    - Para word-list `zh`, fazer `LexicalGroundingService` usar `policy_for_language(zh)` para definitions/translation target em inglês, em vez de traduzir a sentence chinesa para chinês; manter o comportamento word-list dos demais idiomas. Cobrir com fake lookup/provider, sem rede (D-06).
    - Estender `TextValidationService` para tratar `zh` como idioma sem espaços: target por substring normalizada, comprimento por contagem de Han e gate de script antes do detector de corpus. Exigir Han, Simplificado canônico e ratio Han suficiente; rejeitar texto Latin, kana-dominante/Japanese, Tradicional primário e sentence sem target. Não reutilizar a aceitação Japanese, pois CJK sozinho não distingue os idiomas (D-01).
    - Usar `zh` diretamente em `wordfreq` e em `assets/frequency/zh`; não criar alias `zh-CN`. Normalizar cada token para Simplificado antes de dedupe, rejeitar tokens sem Han ou de script dominante incorreto com reason code válido, preservar `source_rank` e marcar a normalização em `curation_flags`. Expor `--scan-limit` no CLI e passá-lo a `build_assets`. O curated deve ter ranks 1..3000, níveis 1/2/3 com 1000 rows, `language=zh`, `source_provenance=wordfreq:zh` e nenhuma row fora do contrato de script (D-01, D-06).
    - Concentrar os novos testes scanner-readable de registries/prompts/adapters em `test_mandarin_language_support.py`, inspecionando payloads/URLs e usando mocks; reexecutar também as suites existentes dos adapters/Tatoeba para anti-regressão. Não acessar nem citar conteúdo do APKG de referência (D-05).
  </action>
  <verify>
    - Run `uv lock --check`
    - Run `uv run python -c "from pypinyin import Style, lazy_pinyin; from opencc import OpenCC; assert lazy_pinyin('银行', style=Style.TONE) == ['yín', 'háng']; assert OpenCC('s2t').convert('中国') == '中國'"`
    - Run `uv run python scripts/build_frequency_assets.py --assets-dir assets/frequency --version v1 --language zh --scan-limit 25000`
    - Run `uv run python scripts/build_frequency_assets.py --assets-dir assets/frequency --version v1 --language zh --check`
    - Run `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_mandarin_language_support.py tests/services/test_mandarin_orthography.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_tatoeba_sentence_source.py -q`
    - Run `uv run pytest tests/services/test_text_validation.py tests/services/test_frequency_decks.py -q`
  </verify>
  <exit_checkpoint>
    - Não avançar para 027-02 se o comando de geração não tiver escrito ambos os assets reais antes do `--check`, se não houver exatamente 3000 rows/3x1000, ou se qualquer teste focado falhar.
    - Registrar no summary da wave que `zh` é a identidade única e listar separadamente os usos legítimos de locale `zh-CN` (Azure, ElevenLabs VoiceSelection e Google `tl`).
  </exit_checkpoint>
  <done>
    `zh` é selecionável nos dois source types; providers/TTS/local fallback resolvem a identidade `zh` e os locales corretos; payloads ElevenLabs/Google e matching Tatoeba cumprem seus contratos; pinyin/Tradicional são determinísticos e fail-closed; os assets reais em `assets/frequency/zh` contêm exatamente 3000 entradas em 3x1000.
  </done>
</task>

<task id="027-02" type="auto" tdd="true">
  <name>Definir e persistir o snapshot Mandarim com assembly e áudio language-aware</name>
  <files>
    - MODIFY: src/multilang/domain/exporting.py
    - MODIFY: src/multilang/db/models.py
    - CREATE: alembic/versions/20260720_15_mandarin_export_fields.py
    - MODIFY: src/multilang/repositories/export_repository.py
    - MODIFY: src/multilang/services/generate_audio_items.py
    - MODIFY: src/multilang/services/assemble_export_cards.py
    - MODIFY: tests/domain/test_exporting.py
    - MODIFY: tests/test_migration_schema_parity.py
    - MODIFY: tests/repositories/test_export_repository.py
    - MODIFY: tests/services/test_generate_audio_items.py
    - MODIFY: tests/services/test_assemble_export_cards.py
  </files>
  <entry_checkpoint>
    - Run `uv run python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; heads=ScriptDirectory.from_config(Config('alembic.ini')).get_heads(); assert heads == ['20260714_14'], heads"` antes de criar a migration; qualquer outro resultado aciona stop-and-challenge.
    - Run `uv run python scripts/build_frequency_assets.py --assets-dir assets/frequency --version v1 --language zh --check` e os testes focados da Wave 1; não avançar com foundation vermelha.
  </entry_checkpoint>
  <behavior>
    - RED first: `(zh, frequency)` and `(zh, word-list)` resolve the exact Mandarin field tuple, while mixed-language/source batches fail.
    - RED first: missing orthography values or nonblank Image reject Mandarin rows; non-Mandarin legacy rows retain prior contracts.
    - RED first: all four derived values survive commit/expire/reload and no repository/export path recomputes them.
    - RED first: word-list `zh` requires/materializes word and sentence audio while other word-list languages retain sentence-only behavior.
  </behavior>
  <action>
    - Definir `MANDARIN_EXPORT_CARD_FIELD_NAMES` exatamente como `("SortIndex", "word", "Pinyin", "Traditional", "Definitions", "Example Sentence", "Sentence Pinyin", "Traditional Sentence", "Translation", "word_audio", "sentence_audio", "Image")`. Adicionar ao `ExportCardRow` quatro propriedades explícitas `mandarin_word_pinyin`, `mandarin_word_traditional`, `mandarin_sentence_pinyin`, `mandarin_sentence_traditional`, com os aliases acima. Para rows `zh` frequency/word-list exigir os quatro valores e `Translation` não vazios e exigir `Image == ""`; não reaproveitar `word_reading`/`sentence_furigana` Japanese (D-02, D-04).
    - Criar um único helper de resolução por `(language, source_type)`: Mandarim para `zh` em `frequency` e `word-list`; Japanese somente em `ja + frequency`; Latin mantém sua regra; demais usam o profile existente. Fazer `ExportCardRow.ordered_field_mapping()` e `export_field_names_for_rows()` usarem esse helper e rejeitarem lotes mixed-language **ou** mixed-source, em vez de escolher silenciosamente um schema.
    - Criar a revisão Alembic `20260720_15` com `down_revision = "20260714_14"` e quatro colunas `Text`, nullable para compatibilidade com rows legadas. Espelhar as colunas em `CardExportModel`, `_card_payload` e `_to_card_domain`. Adicionar parity test de nomes e teste de repository que grava, `session.expire_all()`, recarrega e compara os quatro valores; isso é a prova contra o bug de fields derivados não persistidos (D-02).
    - No assembler, resolver fields por language+source antes de decidir IPA, Translation e áudio. Para `zh`, exigir word e sentence audio, não exigir IPA, chamar o serviço ortográfico uma vez sobre display word e accepted sentence não escapados, escapar os quatro resultados e persistir o row. Converter qualquer `MandarinOrthographyError` em `AssembleExportCardsError` com contexto do item; não recalcular em repository/export (D-01, D-02, D-04).
    - Em `GenerateAudioItemsService`, usar o mesmo helper language-aware. Assim word-list `zh` materializa dois assets, enquanto word-list não Mandarim continua materializando apenas sentence audio. Testar ambos os lados no mesmo arquivo de regressão (D-06).
    - Adicionar testes do mapping exato, falta de qualquer derivado, Image não vazio, assembly frequency e word-list, dois áudios, snapshot persistido e isolamento Japanese/non-Mandarin. Todos os fakes permanecem offline.
  </action>
  <verify>
    - Run `uv run python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; heads=ScriptDirectory.from_config(Config('alembic.ini')).get_heads(); assert heads == ['20260720_15'], heads"`
    - Run `uv run python -c "import os,tempfile; from pathlib import Path; from alembic import command; from alembic.config import Config; os.environ.pop('MULTILANG_DATABASE_URL', None); d=tempfile.TemporaryDirectory(); url='sqlite:///' + (Path(d.name)/'mandarin.db').as_posix(); c=Config('alembic.ini'); c.set_main_option('sqlalchemy.url', url); command.upgrade(c, 'head')"`
    - Run `uv run pytest tests/domain/test_exporting.py tests/services/test_mandarin_orthography.py tests/services/test_assemble_export_cards.py tests/services/test_generate_audio_items.py -q`
    - Run `uv run pytest tests/repositories/test_export_repository.py tests/test_migration_schema_parity.py -q`
  </verify>
  <exit_checkpoint>
    - Não avançar para 027-03 até `ScriptDirectory.get_heads()` retornar somente `20260720_15`, o upgrade de uma SQLite descartável chegar ao head, schema parity passar e o repository provar commit/expire/reload dos quatro campos.
    - Registrar a lista de chamadores migrados para o helper `(language, source_type)`; qualquer consumidor row-aware ainda usando somente source type permanece blocker.
  </exit_checkpoint>
  <done>
    O row Mandarim tem field contract exato, recebe quatro derivados e dois áudios nos dois source types, persiste todos os valores por migration/ORM/repository e os recupera sem recomputação; rows legadas e idiomas existentes mantêm seus contratos.
  </done>
</task>

<task id="027-03" type="auto" tdd="true">
  <name>Conectar template Multilang e export APKG/CSV/TSV com prova E2E</name>
  <files>
    - CREATE: src/multilang/templates/mandarin_card.md
    - MODIFY: src/multilang/services/card_template_loader.py
    - MODIFY: src/multilang/services/export_anki_package.py
    - MODIFY: src/multilang/runtime.py
    - MODIFY: tests/services/test_card_template_loader.py
    - MODIFY: tests/services/test_export_anki_package.py
    - MODIFY: tests/services/test_export_tabular_bundle.py
    - CREATE: tests/integration/test_mandarin_modern_flow.py
    - CREATE: .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md
    - CREATE: .planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg
  </files>
  <entry_checkpoint>
    - Run `uv run python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; heads=ScriptDirectory.from_config(Config('alembic.ini')).get_heads(); assert heads == ['20260720_15'], heads"` e `uv run pytest tests/repositories/test_export_repository.py tests/test_migration_schema_parity.py tests/services/test_assemble_export_cards.py tests/services/test_generate_audio_items.py -q`.
    - Não iniciar template/export se os quatro valores ainda não sobreviverem a reload ou se word-list `zh` não produzir ambos os sound fields.
  </entry_checkpoint>
  <behavior>
    - RED first: both Mandarin source types select model `1762800901`, exact fields/template order, hidden-front Translation and blank Image.
    - RED first: APKG media map resolves both sound tags to archived payloads; CSV/TSV serialize the same tags without claiming packaged media.
    - RED first: frequency and word-list E2E reload frozen orthography, export all formats and do not invoke orthography again.
    - RED first: persistent proof APKG/hash validate while render evidence remains `human_needed` with `observations: []`.
  </behavior>
  <action>
    - Criar `mandarin_card.md` somente a partir de `normal_card.md` (D-03, D-05). Preservar integralmente o CSS Multilang existente como base e acrescentar apenas selectors para `.traditional`, `.sentencePinyin` e `.traditionalSentence`, com aparência auxiliar discreta e night mode. Não modificar `normal_card.md`; não incluir código, classes, mídia ou nomes Migaku/reference.
    - Na frente: `word` Simplificado permanece `targetWord`; `Pinyin` aparece imediatamente abaixo usando o espaço/estilo fonético; `Traditional` vem na linha auxiliar discreta; word audio permanece à direita. Manter Definitions/Image/divisores. Na linha de exemplo, mostrar `Example Sentence` Simplificado e sentence audio juntos; dentro do bloco textual colocar `Sentence Pinyin` e `Traditional Sentence` logo abaixo. Manter `Translation` no DOM com `display:none` e revelar somente no verso pelo mesmo script curto de `normal_card.md`. Não adicionar JavaScript de tons (D-02, D-03, D-04, D-05).
    - Registrar o template no loader para `zh` frequency e word-list e validar referências contra o tuple Mandarim. Testar ordem dos marcadores no HTML, CSS base contido no CSS Mandarim, estilos auxiliares, Translation oculta/revelada, ausência de helpers tone/Migaku e condicional Image.
    - Em `export_anki_package.py`, adicionar `MANDARIN_MODEL_ID = 1762800901` e `MANDARIN_NOTE_TYPE_NAME = "Multilang::Mandarin Card"`; usar field tuple/template/model em ambos os source types. Tornar a coleta de mídia language-aware para incluir word e sentence audio no word-list Mandarim. Em `runtime.py`, finalizar display/default deck, note type tabular, media index e quality-gate counts pelo mesmo helper; não duplicar decisões divergentes (D-06).
    - Provar APKG abrindo o zip e `collection.anki2`: model id/name, fields na ordem exata, qfmt/afmt/CSS, valores pinyin/Tradicional, tags e Image vazio. Ler o JSON `media` do APKG e provar que cada `[sound:<basename>]` de word/sentence resolve para uma entrada arquivada cujo payload existe; APKG é o único dos três formatos que empacota os bytes de mídia.
    - Provar CSV e TSV em UTF-8 com os cinco headers Anki, tuple exato e rows na mesma ordem para frequency e word-list. Ambos devem serializar `word_audio` e `sentence_audio` como `[sound:<basename>]` e o E2E deve provar que esses basenames resolvem para arquivos existentes no `media_index`; não alegar que CSV/TSV copiam ou empacotam mídia (eles não recebem `media_index`).
    - Criar `test_mandarin_modern_flow.py` com dois slices CLI/repository offline: (1) frequency `zh` com 1 card por nível, fake wordfreq/lexicon/text e fake Azure, quality gate partial explícito e os três exports; (2) word-list `zh` com índice lexical de fixture, texto Simplificado, quatro assets para dois cards e os três exports. Verificar accepted text, identity `zh`, voice/locale `zh-CN`, snapshots com quatro derivados, reload antes do segundo formato, nenhuma nova chamada ao serviço ortográfico após snapshot, semântica distinta de mídia APKG versus CSV/TSV e Image vazio. Reexecutar os E2E frequency/word-list existentes como regressão (D-01, D-02, D-04, D-06).
    - No mesmo módulo de integração, expor `write_mandarin_proof_artifact(output_path: Path)`, reutilizando somente fixtures/fakes offline do slice frequency para escrever `.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg`. O helper deve falhar se o APKG não contiver exatamente um note `zh`, os dois áudios e `Image == ""`; não usar o APKG de referência (D-04, D-05).
    - Criar `UI-PROOF.md` com JSON cercado contendo os top-level fields exigidos pelo workflow: `proof_bundle_version`, `scope`, `route_state`, `environment`, `viewport`, `evidence_inputs`, `commands_or_manual_steps`, `observations`, `artifacts`, `privacy`, `result`, `claim_limits`. Registrar path, byte size e SHA-256 do `mandarin-proof.apkg`; declarar Desktop `1280x800` e Google Pixel 7/AnkiDroid `412x915` portrait. Manter `observations: []`, `artifacts` sem screenshots e `result: human_needed` até observação humana real; não instalar/scaffoldar browser tooling nem transformar contrato estático em alegação de render (D-03, D-05).
  </action>
  <verify>
    - Run `uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/integration/test_mandarin_modern_flow.py -q`
    - Run `uv run pytest tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py -q`
    - Run `uv run python -c "from pathlib import Path; import runpy; ns=runpy.run_path('tests/integration/test_mandarin_modern_flow.py'); ns['write_mandarin_proof_artifact'](Path('.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg'))"`
    - Run `uv run python -c "import hashlib; from pathlib import Path; p=Path('.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg'); proof=Path('.planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md').read_text(encoding='utf-8'); digest=hashlib.sha256(p.read_bytes()).hexdigest(); assert p.is_file() and p.stat().st_size > 0 and digest in proof"`
    - Run `npx -y gsdd-cli ui-proof validate .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md`
  </verify>
  <exit_checkpoint>
    - Não concluir automação até focused/E2E/regression tests passarem, o APKG persistente existir e seu SHA-256 coincidir com `UI-PROOF.md`.
    - Encerrar com o slot estático validado e o slot de render explicitamente `human_needed`, `observations: []`, sem screenshots; posicionamento e legibilidade continuam dependentes da gate humana posterior.
  </exit_checkpoint>
  <done>
    Frequency e word-list `zh` exportam snapshots persistidos para APKG/CSV/TSV com note type/template/fields exatos, ambos os sound tags e Image vazio; APKG empacota mídia, CSV/TSV apenas referenciam basenames resolvíveis; o proof bundle registra APKG/hash e mantém a renderização Desktop/mobile honestamente `human_needed`.
  </done>
</task>

<threat_model>

## Trust Boundaries

| Boundary | Description |
|---|---|
| wordfreq/word-list/provider -> text validation | Texto externo ou gerado cruza para o domínio learner-facing `zh` com conteúdo Simplificado. |
| accepted text -> orthography/snapshot | Pinyin/Tradicional derivados tornam-se dados congelados e auditáveis. |
| snapshot -> Anki template/tabular export | Conteúdo persistido entra em HTML de card, APKG e arquivos importáveis. |
| audio storage -> APKG media | Caminhos e sound tags precisam corresponder por basename e existir. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-027-01 | Tampering | `text_validation.py`, `mandarin_orthography.py` | mitigate | Validar Simplificado/Han, target substring, ratios Han/kana/Latin e derivados não vazios antes do snapshot. |
| T-027-02 | Information Disclosure | APKG de referência / template | mitigate | Não ler/importar/copiar o APKG; template deriva somente de `normal_card.md`; scan/test proíbe identificadores Migaku/reference. |
| T-027-03 | Tampering | snapshot DB -> export | mitigate | Quatro colunas explícitas, migration parity, repository expire/reload e teste de ausência de recomputação. |
| T-027-04 | Elevation of Privilege | texto -> Anki HTML/JS | mitigate | Escapar word/sentence/derivados no assembler e permitir somente o script fixo de reveal já pertencente ao template Multilang. |
| T-027-05 | Spoofing | routing de note type | mitigate | Resolver schema/model por language+source e rejeitar lotes mixed-language/source. |
| T-027-06 | Denial of Service | pypinyin/OpenCC sobre texto | accept | Inputs já passam limites de sentence e cards; conversão local linear e sem I/O externo. |
| T-027-07 | Repudiation | evidência visual | mitigate | UI-PROOF separa prova estática de observação humana, inclui comandos, artifacts e metadados de privacidade. |

</threat_model>

## Multi-Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Mandarim integrado ao fluxo moderno completo | Tasks 027-01..03 e E2E frequency/word-list |
| REQ | Requirement IDs | N/A — quick task sem ROADMAP/SPEC requirement IDs, conforme instrução |
| CONTEXT D-01 | Código canônico `zh`, conteúdo/locale Simplificado `zh-CN` e Tradicional complementar | 027-01 separa identity/provider locale e valida/deriva; 027-02 persiste; 027-03 renderiza/exporta |
| CONTEXT D-02 | Pinyin tonal e Tradicional para palavra/frase | 027-01 serviço/teste; 027-02 fields/migration; 027-03 formatos/template |
| CONTEXT D-03 | Layout normal_card e posicionamento pedagógico | 027-03 template e UI slots |
| CONTEXT D-04 | Image vazio | model validator, assembly, APKG/CSV/TSV tests |
| CONTEXT D-05 | APKG apenas inspiração, sem cópia | Anti-goals, hard boundary, 027-03 e T-027-02 |
| CONTEXT D-06 | frequency/word-list, texto, áudio, APKG/CSV/TSV, testes | 027-01 runtime/assets; 027-02 dois áudios/snapshot; 027-03 E2E/exports |
| RESEARCH | pypinyin + OpenCC determinísticos e ranges compatíveis | 027-01 dependências/API/testes |
| RESEARCH | Azure locale `zh-CN`; ElevenLabs `zh` somente em modelo compatível; Google `tl=zh-CN` | 027-01 registries, payload/URL mocks e testes |
| RESEARCH | Tatoeba `zh -> cmn` e matching por substring/contagem Han | 027-01 provider e testes sem espaços |
| RESEARCH | Script/substring/CJK validation e prompt Simplificado | 027-01 validator/provider tests |
| RESEARCH | Persistência explícita, sem repetir bug Japanese | 027-02 migration/ORM/repository parity |
| RESEARCH | Template/model/field routing separado | 027-03 loader/APKG/runtime/tabular tests |

**Audit result:** todos os itens de GOAL, CONTEXT e RESEARCH estão cobertos; não há requirement IDs ou itens deferred. Highlights, Migaku/import do APKG e correção Japanese Windows são exclusões explícitas, não gaps.

## Final Verification

Executar na ordem, sem chamadas reais de provider:

1. `uv lock --check`
2. `uv run python scripts/build_frequency_assets.py --assets-dir assets/frequency --version v1 --language zh --scan-limit 25000`
3. `uv run python scripts/build_frequency_assets.py --assets-dir assets/frequency --version v1 --language zh --check`
4. `uv run python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; heads=ScriptDirectory.from_config(Config('alembic.ini')).get_heads(); assert heads == ['20260720_15'], heads"`
5. `uv run python -c "import os,tempfile; from pathlib import Path; from alembic import command; from alembic.config import Config; os.environ.pop('MULTILANG_DATABASE_URL', None); d=tempfile.TemporaryDirectory(); url='sqlite:///' + (Path(d.name)/'mandarin.db').as_posix(); c=Config('alembic.ini'); c.set_main_option('sqlalchemy.url', url); command.upgrade(c, 'head')"`
6. `uv run pytest tests/services/test_mandarin_language_support.py tests/services/test_mandarin_orthography.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_tatoeba_sentence_source.py tests/integration/test_mandarin_modern_flow.py -q`
7. `uv run pytest tests/domain/test_exporting.py tests/repositories/test_export_repository.py tests/test_migration_schema_parity.py tests/services/test_text_validation.py tests/services/test_frequency_decks.py tests/services/test_generate_audio_items.py tests/services/test_assemble_export_cards.py tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py -q`
8. `uv run pytest tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py -q`
9. `uv run pytest tests --ignore=tests/services/test_japanese_furigana.py -q`
10. `uv run python -c "from pathlib import Path; import runpy; ns=runpy.run_path('tests/integration/test_mandarin_modern_flow.py'); ns['write_mandarin_proof_artifact'](Path('.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg'))"`
11. `uv run python -c "import hashlib; from pathlib import Path; p=Path('.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg'); proof=Path('.planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md').read_text(encoding='utf-8'); digest=hashlib.sha256(p.read_bytes()).hexdigest(); assert p.is_file() and p.stat().st_size > 0 and digest in proof"`
12. `uv run python -c "from pathlib import Path; roots=[Path('src'), Path('scripts')]; banned=('Mandarim Metodo Poliglota','Migaku','Piyin','Additional images','Is Vocabulary Card','Is Audio Card'); text='\n'.join(p.read_text(encoding='utf-8', errors='ignore') for root in roots for p in root.rglob('*') if p.suffix in {'.py','.md'}); assert not any(term in text for term in banned)"`
13. `npx -y gsdd-cli ui-proof validate .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md`
14. `git diff --check`

`tests/services/test_japanese_furigana.py` é excluído somente do comando agregado porque sua falha Windows por path Fugashi sem quoting precede este trabalho. Não alterar esse teste e não citá-lo como evidência Mandarim; todos os testes Mandarim e regressões direcionadas devem passar por seus próprios comandos.

## Manual UI Acceptance Gate

Depois da automação:

1. Confirmar que o SHA-256 registrado aponta exatamente para `.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg` e importar esse arquivo no Anki Desktop em viewport `1280x800`.
2. Observar frente e verso: Simplificado no topo; pinyin imediatamente abaixo; Tradicional discreto; sentence Simplificada e áudio na mesma região; sentence pinyin/Tradicional abaixo; Translation somente após virar.
3. Importar a mesma hash do APKG em AnkiDroid num Google Pixel 7 `412x915` portrait e repetir frente/verso, confirmando ausência de overflow/colisão e legibilidade.
4. Responder `approved` ou descrever desvios. Até existir essa resposta, manter `observations: []`, `result: human_needed` e nenhum screenshot no `UI-PROOF.md`; não inventar observações nem usar screenshot como substituto da revisão.

Até essa gate, não alegar fidelidade visual real — somente contrato estático/APKG.

## Success Criteria

- `GenerationRequest` e defaults aceitam `zh` para frequency e word-list; `zh-CN` permanece somente locale/provider.
- Assets `assets/frequency/zh` validam 3000 rows em 3x1000 e Simplificado/Han após geração real com scan limit 25000.
- Palavra/frase produzem pinyin tonal e Tradicional determinísticos, sem saída vazia ou script incorreto.
- Migration, ORM e repository preservam os quatro campos após reload.
- Word-list `zh` gera dois áudios; word-list não Mandarim conserva seu comportamento.
- APKG/CSV/TSV têm note type, model id, fields, valores, ambos os sound tags e Image vazio exatos; somente APKG empacota mídia, enquanto CSV/TSV apontam para basenames resolvíveis.
- Template conserva CSS/layout Multilang e Translation hidden-until-back, sem conteúdo Migaku/reference.
- Testes Mandarim e regressões direcionadas passam; suite agregada passa com apenas o arquivo baseline explicitamente excluído.
- UI proof estático valida e registra APKG/SHA-256; renderização Desktop 1280x800 e Pixel 7/AnkiDroid 412x915 permanece `human_needed` com `observations: []` até revisão.

## High-Leverage Review

Uma segunda passada é obrigatória sobre migration/schema parity, todos os chamadores do helper de field routing, persistência/reload, media collection e template loader. Verificar especificamente que nenhuma chamada remanescente a `export_field_names_for_source_type()` decide fields/áudio para um row que já possui language.

## Leverage Review

- **Lost:** write set amplo e execução sequencial por atravessar registries, persistence e export.
- **Kept:** arquitetura do fluxo moderno, CLI, providers, normal visual language, snapshots e exporters existentes.
- **Gained:** `zh` completo e auditável, locale `zh-CN` usado somente onde correto, com dados pedagógicos determinísticos e um único contrato consistente entre APKG/CSV/TSV.

## Output

Após execução, criar `.planning/quick/027-adicionar-mandarim-integrado/027-SUMMARY.md`; o workflow de UI também mantém `.planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md`.
