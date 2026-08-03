---
mode: quick
phase: quick-039-preview-melhorado-anki
task: 039-preview-melhorado-anki
plan: 039
type: execute
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
autonomous: true
task_count: 2
requirements: []
files_modified:
  - normal_card_improved_preview.html
  - exports/anki_previews/normal-card-improved-test.apkg
  - exports/anki_previews/normal-card-improved-test.tsv
  - .planning/quick/039-preview-melhorado-anki/UI-PROOF.md
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/ está vazio; este plano aplica diretamente o contrato planner quick fornecido pelo usuário."
non_goals:
  - "Não modificar o template normal de produção, código da aplicação, testes existentes, previews anteriores, LOG.md, ROADMAP.md ou SPEC.md."
  - "Não incorporar a variante experimental à geração de produção antes da aprovação do usuário."
  - "Não gerar nem baixar áudio, imagem, fonte, biblioteca, script ou outro asset externo."
  - "Não alegar aparência observada no Anki nativo antes da importação humana do APKG."
hard_boundaries:
  - "O write set dentro do repositório contém somente os quatro caminhos em files_modified; o executor cria 039-SUMMARY.md depois das tarefas e o verifier cria 039-VERIFICATION.md separadamente. A única escrita externa transitória é o baseline JSON em %LOCALAPPDATA%/Temp/opencode/."
  - "src/, tests/, normal_card_anki_corrected_preview.html e todo o worktree concorrente são somente leitura."
  - "Não ler .env, não importar settings/providers do produto, não realizar chamadas de rede e não permitir sync/lock mutation do uv."
  - "Não fazer stage, commit, restore, reset, clean, delete ou reformatação fora do write set."
anti_regression_targets:
  - "HEAD, staged diff global, status global filtrado e digest de todos os arquivos tracked/untracked não ignorados fora dos outputs permitidos permanecem idênticos antes/depois/live."
  - "uv.lock, pyproject.toml e todos os paths fora do write set mantêm os mesmos bytes; arquivos tracked ausentes entram no digest com marcador MISSING."
  - "O note model, o deck e os três GUIDs experimentais são próprios, sem substituir Multilang::Card, deck ou note de produção."
  - "O shell permanece full-width e de altura natural; somente .cardContent limita a largura interna a 900px."
closure_claim_limit: "A inspeção automatizada prova o source do preview, a estrutura ZIP/SQLite do APKG, o TSV e a entrega local. A aparência no renderer nativo continua human_needed até o usuário importar e observar o pacote no Anki."
ui_proof_slots:
  - slot_id: improved-normal-card-preview-source
    claim: "O preview standalone contém exatamente dois estados front/back, declara shell full-width de altura natural, conteúdo interno de 900px, tipografia clamp, controles de áudio circulares de pelo menos 34px, hierarquia dark responsiva e nenhuma dependência ativa ou externa."
    route_state: "Abrir ou inspecionar normal_card_improved_preview.html localmente; data-window-state e data-card-state aparecem em ordem front/back, com Translation hidden/visible por classes."
    required_evidence_kinds: [code, test]
    minimum_observations: 8
    expected_artifact_types: ["HTML source", "Python stdlib validator output"]
    validation_command: >-
      uv run --offline --no-sync --frozen --no-env-file python -c "import re; from pathlib import Path; s=Path('normal_card_improved_preview.html').read_text(encoding='utf-8'); states=re.findall(r'data-card-state=\"(front|back)\"',s); css=re.search(r'/\* BEGIN IMPROVED ANKI CSS \*/(.*?)/\* END IMPROVED ANKI CSS \*/',s,re.S).group(1); rule=lambda selector: re.search(re.escape(selector)+r'\s*\{([^}]*)\}',css,re.S).group(1); assert states==['front','back']; assert 'box-sizing: border-box' in rule('*, *::before, *::after'); assert all(token in rule('.customCard') for token in ('width: 100%','max-width: none','min-height: 0','margin: 0','box-sizing: border-box')); assert 'max-width: 900px' in rule('.cardContent') and rule('.cardContent').count('clamp(')>=2; assert 'font-size: clamp(' in rule('.targetWord') and all('font-size: clamp(' in rule(selector) for selector in ('.definitionText','.exampleSentenceText','.sentenceTranslation')); assert 'gap: clamp(' in rule('.wordHero') and 'gap: clamp(' in rule('.cardSections'); assert all(token in rule('.examplePanel') for token in ('background:','border-left:','border-radius:','padding:')); assert all(token in rule('.replay-button') for token in ('min-width: 34px','min-height: 34px','border-radius: 50%','background: #233a57','border: 1px solid #6aa9f4','color: #f5f9ff')) and all(token in rule('.replay-button:focus-visible') for token in ('outline: 3px solid #93c5fd','outline-offset: 3px')) and 'fill: currentColor' in rule('.replay-button svg path'); mobile=css.split('@media (max-width: 420px)',1)[1]; assert all(token in mobile for token in ('.cardContent','.wordHero','.cardSections','.examplePanel','.exampleSentenceLine','align-items: flex-start')); assert '<script' not in s.lower() and not re.search(r'https?://|@import|url\s*\(',s,re.I); print('preview source slot PASS')"
    environment: "Source local offline executado com o Python do projeto via uv; sem browser, Anki, rede ou providers."
    viewport: "Contrato CSS amplo em duas janelas e breakpoint de comparação; o card possui breakpoint próprio em max-width 420px. Nenhum pixel renderizado é alegado."
    manual_acceptance_required: false
    claim_limit: "Prova declarações e estados no source, não gosto visual, pixels computados nem fidelidade do WebView do Anki."
  - slot_id: improved-normal-card-apkg-structure
    claim: "O APKG local é importável, contém exatamente três notes/cards alemães com GUIDs explícitos distintos, IDs/nome de modelo e deck exclusivos, nove fields na ordem exigida, um único template Card 1, templates/CSS válidos, nenhuma mídia e TSV LF exatamente correspondente."
    route_state: "Inspecionar exports/anki_previews/normal-card-improved-test.apkg como ZIP e sua collection.anki2/collection.anki21 como SQLite, sem importá-lo no Anki."
    required_evidence_kinds: [code, test, delivery]
    minimum_observations: 8
    expected_artifact_types: ["APKG", "TSV", "ZIP manifest inspection", "SQLite inspection output"]
    validation_command: >-
      uv run --offline --no-sync --frozen --no-env-file python -c "import json,sqlite3,tempfile,zipfile,genanki; from pathlib import Path; fields=['SortIndex','word','IPA','Definitions','Example Sentence','Translation','word_audio','sentence_audio','Image']; apkg=Path('exports/anki_previews/normal-card-improved-test.apkg'); archive=zipfile.ZipFile(apkg); assert archive.testzip() is None; names=archive.namelist(); collections=[name for name in names if name in {'collection.anki2','collection.anki21'}]; assert len(collections)==1; collection=collections[0]; temporary=tempfile.TemporaryDirectory(); db=Path(temporary.name)/collection; db.write_bytes(archive.read(collection)); connection=sqlite3.connect(db); notes=connection.execute('select guid,mid from notes').fetchall(); cards=connection.execute('select nid,did,ord from cards').fetchall(); models=json.loads(connection.execute('select models from col').fetchone()[0]); decks=json.loads(connection.execute('select decks from col').fetchone()[0]); expected={genanki.guid_for('Multilang::Card Improved Preview','1762801039',sort_index,word) for sort_index,word in (('1','Buch'),('2','Wasser'),('3','lernen'))}; model=models['1762801039']; assert len(notes)==3 and len({row[0] for row in notes})==3 and {row[0] for row in notes}==expected and {row[1] for row in notes}=={1762801039}; assert len(cards)==3 and len({row[0] for row in cards})==3 and {row[1] for row in cards}=={1762801040} and {row[2] for row in cards}=={0}; assert model['name']=='Multilang::Card Improved Preview' and [field['name'] for field in model['flds']]==fields and len(model['tmpls'])==1 and model['tmpls'][0]['name']=='Card 1' and decks['1762801040']['name']=='Multilang Improved Card Test'; assert json.loads(archive.read('media').decode('utf-8'))=={}; connection.close(); archive.close(); temporary.cleanup(); print('APKG structure slot PASS')"
    environment: "genanki já instalado no ambiente uv e inspeção offline com zipfile/sqlite3/csv da stdlib; nenhuma leitura de .env."
    viewport: "Não aplicável à inspeção estrutural; o CSS armazenado é validado por contrato."
    manual_acceptance_required: false
    claim_limit: "Prova integridade e importabilidade estrutural do pacote, não o resultado visual do renderer nativo."
  - slot_id: improved-normal-card-native-anki-appearance
    claim: "Após importar o APKG, o usuário observa no Anki o shell full-width de altura natural, o conteúdo centralizado, a hierarquia dark e a responsividade em frente e verso."
    route_state: "Importar exports/anki_previews/normal-card-improved-test.apkg no Anki, abrir Multilang Improved Card Test e revisar Buch, Wasser e lernen na frente e no verso."
    required_evidence_kinds: [delivery, human]
    minimum_observations: 4
    expected_artifact_types: ["APKG import result", "human Anki review notes"]
    validation_command: "Manual: importar o APKG no Anki Desktop, revisar frente/verso em largura ampla e com a janela reduzida até 420px ou menos, e informar aprovação ou problemas."
    environment: "Anki nativo do usuário, totalmente offline depois da importação."
    viewport: "Reviewer amplo e estreito (até 420px); a aprovação móvel real só pode ser acrescentada se o usuário também abrir o deck no cliente móvel."
    manual_acceptance_required: true
    claim_limit: "Permanece human_needed nesta execução; não converter a inspeção de source/APKG em aprovação visual nativa."
must_haves:
  truths:
    - "O usuário encontra na raiz um preview offline com exatamente uma frente e um verso do card melhorado."
    - "O shell do card ocupa 100% da largura útil e termina no fluxo natural do conteúdo, enquanto .cardContent centraliza a leitura com max-width de 900px."
    - "Palavra e texto usam clamp(), o painel de exemplo e a tradução têm hierarquia clara, e os controles nativos possuem área circular mínima de 34px e contraste explícito."
    - "O layout possui gaps/paddings responsivos e um breakpoint max-width 420px sem introduzir min-height de viewport no shell."
    - "O usuário encontra no Explorer um APKG não vazio que importa como note type Multilang::Card Improved Preview e deck Multilang Improved Card Test, sem sobrescrever produção."
    - "O deck contém somente Buch, Wasser e lernen, com nove fields normais em ordem e áudio/imagem vazios."
    - "Cada note usa GUID explícito derivado de note type, model ID, SortIndex e word; os três GUIDs são distintos e exclusivos da variante."
    - "Frente oculta Translation; verso a revela com FrontSide e o script fixo permitido; IPA e Image permanecem condicionais."
    - "O TSV possui o mesmo header e as mesmas três linhas armazenadas nas notes do APKG."
    - "UI-PROOF registra source e estrutura APKG como pass, mas mantém a aparência no Anki como human_needed."
    - "HEAD, staged diff global, status filtrado, uv.lock, pyproject.toml e todo path tracked/untracked não ignorado fora dos outputs permitidos permanecem idênticos."
  artifacts:
    - path: normal_card_improved_preview.html
      provides: "Preview HTML5 standalone, front/back, responsivo, inerte e sem assets externos"
    - path: exports/anki_previews/normal-card-improved-test.apkg
      provides: "Pacote Anki experimental importável com modelo/deck isolados e três cards"
    - path: exports/anki_previews/normal-card-improved-test.tsv
      provides: "Companheiro textual UTF-8 tab-separated dos nove fields"
    - path: .planning/quick/039-preview-melhorado-anki/UI-PROOF.md
      provides: "Evidência source/APKG, metadados de privacidade, integridade do worktree e pendência humana nativa"
  key_links:
    - from: "normal_card_improved_preview.html entre os marcadores BEGIN/END IMPROVED ANKI CSS"
      to: "CSS do model 1762801039 dentro do APKG"
      via: "o gerador extrai literalmente o bloco marcado; a inspeção exige igualdade textual após strip"
    - from: "qfmt do model experimental"
      to: "os nove fields do model"
      via: "referências Mustache validadas contra o field set, incluindo condicionais IPA/Image e slots de áudio"
    - from: "afmt do model experimental"
      to: "#translation criado pelo qfmt"
      via: "FrontSide seguido somente por document.getElementById('translation').style.display = 'block'"
    - from: "três genanki.Note"
      to: "normal-card-improved-test.tsv"
      via: "as mesmas listas ordenadas de nove strings alimentam package e csv.writer"
    - from: "cada genanki.Note experimental"
      to: "notes.guid dentro do APKG"
      via: "guid=genanki.guid_for('Multilang::Card Improved Preview', str(model_id), SortIndex, word), com conjunto exato de três GUIDs distintos validado no SQLite"
    - from: "normal-card-improved-test.apkg"
      to: ".planning/quick/039-preview-melhorado-anki/UI-PROOF.md"
      via: "contagens ZIP/SQLite, IDs, templates, CSS, fields, mídia e correspondência TSV registradas por observação"
---

# Quick Task 039 Plan: Preview melhorado e APKG experimental

<objective>
Criar uma variante visual experimental do card normal, entregá-la como preview HTML standalone e como APKG offline importável, e registrar evidência estrutural suficiente para o usuário decidir depois de observar o pacote no Anki.

Purpose: permitir aprovação informada das melhorias de largura, legibilidade, hierarquia, controles e responsividade sem tocar no template ou nos testes de produção.

Output: `normal_card_improved_preview.html`, `exports/anki_previews/normal-card-improved-test.apkg`, `exports/anki_previews/normal-card-improved-test.tsv` e `.planning/quick/039-preview-melhorado-anki/UI-PROOF.md`.
</objective>

<context>
@AGENTS.md
@pyproject.toml
@normal_card_anki_corrected_preview.html
@src/multilang/templates/normal_card.md
@src/multilang/services/export_anki_package.py
@.planning/quick/037-preview-card-anki-corrigido/037-SUMMARY.md
@.planning/quick/036-criar-outro-deck-teste-alemao/036-SUMMARY.md

- `genanki>=0.13,<0.14` já está no ambiente uv. O padrão local confirmado é `genanki.Model(...)` → `genanki.Note(...)` → `genanki.Deck(...)` → `genanki.Package(...).write_to_file(...)`.
- Os IDs candidatos `1762801039`/`1762801040` devem ser verificados dinamicamente antes da geração em todo arquivo tracked/untracked não ignorado enumerado pelo Git, excluindo somente quick039 e os outputs desta quick task; arquivos binários ou não UTF-8 são ignorados de forma explícita e segura.
- O worktree já contém mudanças tracked/untracked concorrentes, inclusive no template e em testes. Não limpar, absorver, reverter ou formatar essas mudanças.
- Discovery nível 0: o trabalho reutiliza genanki e padrões de inspeção ZIP/SQLite já presentes no projeto, sem dependência ou API nova.

<interfaces>
```python
# Contrato local observado em src/multilang/services/export_anki_package.py
model = genanki.Model(model_id, name, fields=[{"name": ...}], templates=[{"name": ..., "qfmt": ..., "afmt": ...}], css=css)
note = genanki.Note(model=model, fields=[...])
deck = genanki.Deck(deck_id, deck_name)
deck.add_note(note)
package = genanki.Package(deck)
package.media_files = []
package.write_to_file(str(output_path))
```
</interfaces>
</context>

## Decisões bloqueadas

- **D-01 — Variante isolada:** criar somente artefatos experimentais; produção e testes permanecem byte a byte inalterados.
- **D-02 — Entrega exata:** usar os quatro caminhos declarados em `files_modified`; o APKG deve ficar em `exports/anki_previews/` para acesso direto pelo Explorer.
- **D-03 — Identidade exclusiva:** model ID `1762801039`, note type `Multilang::Card Improved Preview`; deck ID `1762801040`, deck `Multilang Improved Card Test`; cada note recebe `guid=genanki.guid_for('Multilang::Card Improved Preview', str(model_id), SortIndex, word)` e os três GUIDs devem ser distintos.
- **D-04 — Conteúdo offline:** exatamente três notes/cards, em ordem `Buch`, `Wasser`, `lernen`, com fields `SortIndex`, `word`, `IPA`, `Definitions`, `Example Sentence`, `Translation`, `word_audio`, `sentence_audio`, `Image`; os três últimos ficam vazios.
- **D-05 — Shell e wrapper:** `.card` em block; `#qa` com width 100% e min-width 0; `.customCard` com width 100%, max-width none, min-height 0 e margin 0; `.cardContent` centralizado com width 100% e max-width 900px. Nenhum shell recebe altura/min-height de viewport.
- **D-06 — Tipografia e áudio:** palavra e texto usam `clamp()`; `.replay-button` recebe min-width/min-height de 34px, formato circular, fundo/borda/ícone contrastantes e estados focus-visible.
- **D-07 — Hierarquia e responsividade:** hero da palavra, headings compactos, definição clara, exemplo em painel sutil, tradução secundária legível, paddings/gaps fluidos e `@media (max-width: 420px)`.
- **D-08 — Template seguro:** Translation existe no qfmt com `display:none`, IPA/Image são condicionais, campos de áudio permanecem referenciados, e afmt usa somente `{{FrontSide}}` mais o reveal fixo atual. Proibidos `innerHTML`, script derivado de field, URL/import e asset externo.
- **D-09 — Preview inerte:** exatamente dois estados simulados front/back, conteúdo espelhado salvo a visibilidade da Translation, sem `<script>`, rede ou referência externa. Botões no preview representam visualmente o controle nativo; no APKG eles não aparecem porque os fields de áudio estão vazios por D-04, embora o CSS nativo esteja incluído.
- **D-10 — Geração local:** toda execução Python via uv usa a sintaxe válida `uv run --offline --no-sync --frozen --no-env-file python ...`; não abrir `.env`, importar providers/settings, sincronizar ambiente, atualizar lock ou acessar rede.
- **D-11 — Evidência honesta:** source do preview e estrutura do APKG/TSV podem passar automaticamente; aparência nativa permanece `human_needed` até a importação do usuário.
- **D-12 — Lifecycle/Git:** executor cria `039-SUMMARY.md`, verifier cria `039-VERIFICATION.md`, orchestrator atualiza LOG; nenhuma operação de staging ou commit é permitida. Um baseline automatizado global preserva HEAD, hash do staged diff, status porcelain filtrado e digest de todos os paths tracked/untracked não ignorados, com marcadores para tracked missing e hashes explícitos de `uv.lock`/`pyproject.toml`.

<checks>
<plan_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: "Revisado após FAIL do plan checker: validation_commands agora são diretos; GUIDs são explícitos e inspecionados; todo uv é offline/no-sync/frozen/no-env-file; integridade global before/after/live cobre HEAD, staged diff, status e todos os paths Git; slots exigem 8/8/4 observações; CSS, template/Card ord/nids, TSV LF e busca dinâmica de IDs possuem assertions."
</plan_check>
</checks>

<tasks>

<task id="039-01" type="auto">
  <name>Criar o preview e gerar o APKG/TSV experimental</name>
  <files>
    - CREATE: normal_card_improved_preview.html
    - CREATE: exports/anki_previews/normal-card-improved-test.apkg
    - CREATE: exports/anki_previews/normal-card-improved-test.tsv
  </files>
  <preflight>
    <automated>uv run --offline --no-sync --frozen --no-env-file python -c "import base64,hashlib,json,os,stat,subprocess; from pathlib import Path
root=Path.cwd()
allowed={'normal_card_improved_preview.html','exports/anki_previews/normal-card-improved-test.apkg','exports/anki_previews/normal-card-improved-test.tsv','.planning/quick/039-preview-melhorado-anki/UI-PROOF.md','.planning/quick/039-preview-melhorado-anki/039-SUMMARY.md'}
def git_bytes(*args):
    return subprocess.run(['git',*args],check=True,capture_output=True).stdout
def filtered_status():
    raw=git_bytes('status','--porcelain=v1','-z','--untracked-files=all')
    kept=[]
    for record in raw.split(b'\0'):
        if not record:
            continue
        candidate=record[3:].decode('utf-8','surrogateescape').replace('\\\\','/') if len(record)>=4 and record[2:3]==b' ' else None
        if candidate not in allowed:
            kept.append(record)
    blob=b'\0'.join(kept)+(b'\0' if kept else b'')
    return base64.b64encode(blob).decode('ascii'),hashlib.sha256(blob).hexdigest(),len(kept)
def repository_digest():
    raw_paths=sorted(path for path in git_bytes('ls-files','-z','--cached','--others','--exclude-standard').split(b'\0') if path)
    digest=hashlib.sha256(); count=0
    for raw_path in raw_paths:
        relative=raw_path.decode('utf-8','surrogateescape').replace('\\\\','/')
        if relative in allowed:
            continue
        path=root/Path(relative)
        digest.update(b'PATH\0'+raw_path+b'\0')
        try:
            mode=os.lstat(path).st_mode
        except FileNotFoundError:
            digest.update(b'MISSING\0'); count+=1; continue
        if stat.S_ISREG(mode):
            marker,payload=b'FILE\0',path.read_bytes()
        elif stat.S_ISLNK(mode):
            marker,payload=b'SYMLINK\0',os.readlink(path).encode('utf-8','surrogateescape')
        else:
            marker,payload=b'OTHER\0',str(mode).encode('ascii')
        digest.update(marker+len(payload).to_bytes(8,'big')+payload+b'\0'); count+=1
    return digest.hexdigest(),count
def file_hash(relative):
    return hashlib.sha256((root/relative).read_bytes()).hexdigest()
def snapshot():
    status_b64,status_hash,status_count=filtered_status(); repository_hash,repository_count=repository_digest()
    return {'head':git_bytes('rev-parse','HEAD').decode('ascii').strip(),'staged_diff_sha256':hashlib.sha256(git_bytes('diff','--cached','--binary','--no-ext-diff','--no-textconv')).hexdigest(),'filtered_status_b64':status_b64,'filtered_status_sha256':status_hash,'filtered_status_entry_count':status_count,'repository_paths_sha256':repository_hash,'repository_paths_count':repository_count,'uv_lock_sha256':file_hash('uv.lock'),'pyproject_sha256':file_hash('pyproject.toml')}
existing=sorted(relative for relative in allowed if (root/relative).exists())
assert not existing,'allowed output already exists before execution: '+repr(existing)
temp_root=Path(os.environ['LOCALAPPDATA'])/'Temp'/'opencode'
assert temp_root.is_dir(),temp_root
baseline_path=temp_root/'quick-039-integrity-baseline.json'
baseline={'schema_version':1,'allowed_outputs':sorted(allowed),'before':snapshot()}
baseline_path.write_text(json.dumps(baseline,ensure_ascii=True,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
print('GLOBAL BASELINE CAPTURED:',baseline_path,baseline['before']['repository_paths_count'],'paths')"</automated>
    <automated>uv run --offline --no-sync --frozen --no-env-file python -c "import os,stat,subprocess; from pathlib import Path
excluded_prefix='.planning/quick/039-preview-melhorado-anki/'
excluded_outputs={'normal_card_improved_preview.html','exports/anki_previews/normal-card-improved-test.apkg','exports/anki_previews/normal-card-improved-test.tsv'}
identifiers=('1762801039','1762801040')
raw=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],check=True,capture_output=True).stdout
hits=[]; scanned=0
for item in raw.split(b'\0'):
    if not item:
        continue
    relative=item.decode('utf-8','surrogateescape').replace('\\\\','/')
    if relative.startswith(excluded_prefix) or relative in excluded_outputs:
        continue
    path=Path(relative)
    try:
        mode=os.lstat(path).st_mode
    except FileNotFoundError:
        continue
    if not stat.S_ISREG(mode):
        continue
    payload=path.read_bytes()
    if b'\0' in payload:
        continue
    try:
        text=payload.decode('utf-8')
    except UnicodeDecodeError:
        continue
    scanned+=1
    hits.extend((relative,identifier) for identifier in identifiers if identifier in text)
assert not hits,'experimental ID collision outside quick039/outputs: '+repr(hits)
print('ID COLLISION SCAN PASS:',scanned,'UTF-8 text files')"</automated>
  </preflight>
  <action>
    Execute os dois comandos de `<preflight>` antes de qualquer write. O primeiro falha se algum output permitido já existir e persiste fora do worktree um baseline scanner-readable com: HEAD; SHA-256 dos bytes de `git diff --cached --binary --no-ext-diff --no-textconv` para o repositório inteiro; estado exato de `git status --porcelain=v1 -z --untracked-files=all` após filtrar somente os cinco paths permitidos (quatro artefatos + `039-SUMMARY.md`), armazenado como base64 + SHA-256 + count; e digest/count de todos os paths retornados por `git ls-files -z --cached --others --exclude-standard`, incorporando caminho, tipo, bytes e marcador `MISSING` para tracked ausente, excluindo somente esses cinco outputs. O baseline também guarda hashes explícitos de `uv.lock` e `pyproject.toml`. O segundo comando deve provar dinamicamente que os IDs experimentais não aparecem em texto UTF-8 tracked/untracked não ignorado fora de quick039/outputs. Só então crie `exports/anki_previews/` sem tocar nos outros exports.

    Crie `normal_card_improved_preview.html` como HTML5 standalone com CSS inline. Coloque o CSS que será armazenado no APKG entre comentários literais `/* BEGIN IMPROVED ANKI CSS */` e `/* END IMPROVED ANKI CSS */`; mantenha CSS exclusivo da moldura de preview fora desses marcadores. Dentro do bloco compartilhado, implemente D-05 a D-07 literalmente: `*, *::before, *::after { box-sizing: border-box; }`; paleta dark coerente com page `#121212` e shell próximo de `#1E1E1E`, texto principal de alto contraste, muted legível, accent azul e borda/painel distinguíveis; `.card { display: block; width: 100%; min-width: 0; min-height: 0; margin: 0; }`; `#qa { width: 100%; min-width: 0; }`; `.customCard { display: block; box-sizing: border-box; width: 100%; max-width: none; min-height: 0; margin: 0; }`; e `.cardContent { box-sizing: border-box; width: 100%; max-width: 900px; margin: 0 auto; padding: clamp(...) clamp(...); }`. O padding fica no conteúdo interno, não reduz a largura do shell. Não declarar `height`, `100vh`, `100dvh`, `100svh`, `100lvh` ou `calc(...vh...)` no shell.

    Vincule cada melhoria a seletores verificáveis, sem depender de contagem global de tokens: `.targetWord` deve ter `font-size: clamp(...)`; `.definitionText`, `.exampleSentenceText` e `.sentenceTranslation` devem possuir seus próprios `font-size: clamp(...)`; `.cardContent` deve usar `padding: clamp(...) clamp(...)`; `.wordHero` e `.cardSections` devem usar `gap: clamp(...)`. Faça `.wordHero` centralizado e distinto, `.sectionHeading` compacta em sans-serif com letter-spacing/text-transform, `.definitionText` com line-height explícito, `.examplePanel` com background, border-left, border-radius e padding, e `.sentenceTranslation` com cor secundária legível e line-height. Estilize `.replay-button` com `min-width: 34px`, `min-height: 34px`, `border-radius: 50%`, `background: #233a57`, `border: 1px solid #6aa9f4` e `color: #f5f9ff`; `.replay-button svg path` usa `fill: currentColor`; `.replay-button:focus-visible` declara `outline: 3px solid #93c5fd` e `outline-offset: 3px`. Dentro — não apenas ao lado — de `@media (max-width: 420px)`, declare novos valores de padding em `.cardContent`, gap em `.wordHero`/`.cardSections`, padding em `.examplePanel` e `align-items: flex-start` em `.exampleSentenceLine`, sem altura de viewport.

    O preview deve conter exatamente duas `<section class="anki-window" data-window-state="...">` e exatamente dois `<article class="customCard cardBack" data-card-state="...">`, em ordem `front`, `back`. Cada janela simula o host `.card` e um wrapper `.previewQa` equivalente a `#qa`, sem duplicar IDs. Use conteúdo `Buch`, `/buːx/`, `noun: book; a written or printed work bound as pages`, `Das Buch liegt auf dem Tisch.` e `O livro está sobre a mesa.`. Mostre um controle visual fixo `.replay-button previewAudioButton` para palavra e frase em cada estado, sem playback. Os dois article bodies devem ser idênticos depois de normalizar apenas `is-hidden/is-visible`, `hidden/visible` e `aria-hidden=true/false`; não renderize Image. Não inclua template Mustache, script, link, mídia, `src`/`href`, import/url CSS, HTTP(S) ou asset externo no preview.

    Em seguida, execute um gerador descartável fora do worktree, ou diretamente com `uv run --offline --no-sync --frozen --no-env-file python -c`, importando apenas stdlib + `genanki`. Extraia literalmente o CSS entre os dois marcadores do preview e use-o como `model.css`. Crie o model/deck de D-03 com exatamente um template chamado `Card 1`. O qfmt deve conter `.customCard > .cardContent`, hero com `{{word}}`, `{{#IPA}}...{{IPA}}...{{/IPA}}`, `{{word_audio}}`, Definition, `{{#Image}}...{{Image}}...{{/Image}}`, painel com `{{Example Sentence}}`, `{{sentence_audio}}` e `<div id="translation" ... style="display:none;">{{Translation}}</div>`. O afmt deve ser exatamente `{{FrontSide}}`, uma linha em branco, e o script fixo `document.getElementById("translation").style.display = "block";`; não usar `innerHTML` nem interpolar field dentro do script.

    Alimente APKG e TSV com as mesmas listas de nove strings, nesta ordem exata: (1) `1`, `Buch`, `/buːx/`, `noun: book; a written or printed work bound as pages`, `Das Buch liegt auf dem Tisch.`, `O livro está sobre a mesa.`, ``, ``, ``; (2) `2`, `Wasser`, `/ˈvasɐ/`, `noun: water; the clear liquid people drink`, `Ich trinke ein Glas Wasser.`, `Eu bebo um copo de água.`, ``, ``, ``; (3) `3`, `lernen`, `/ˈlɛʁnən/`, `verb: to learn; to gain knowledge or a skill`, `Wir lernen jeden Tag Deutsch.`, `Nós estudamos alemão todos os dias.`, ``, ``, ``. Para cada row, construa `genanki.Note(..., guid=genanki.guid_for('Multilang::Card Improved Preview', str(model_id), row[0], row[1]))`; não reutilize GUID automático/baseado somente em SortIndex. Escreva o TSV em UTF-8, sem BOM, abrindo o arquivo com `newline=''` e usando `csv.writer(delimiter='\t', lineterminator='\n')`, header exato e três linhas; os bytes finais devem conter somente LF, nenhum CR. Defina `package.media_files = []`. Remova qualquer script descartável/arquivo parcial; preserve somente os três outputs declarados.
  </action>
  <verify>
    <automated>uv run --offline --no-sync --frozen --no-env-file python -c "import re; from pathlib import Path
s=Path('normal_card_improved_preview.html').read_text(encoding='utf-8')
def rule(source,selector):
    match=re.search(re.escape(selector)+r'\s*\{([^}]*)\}',source,re.S)
    assert match,'missing selector '+selector
    return match.group(1)
def at_rule(source,marker):
    start=source.index(marker); opening=source.index('{',start); depth=0
    for index in range(opening,len(source)):
        depth+=source[index]=='{'; depth-=source[index]=='}'
        if depth==0:
            return source[opening+1:index]
    raise AssertionError('unclosed '+marker)
windows=re.findall(r'data-window-state=\"(front|back)\"',s)
cards=re.findall(r'<article class=\"customCard cardBack\" data-card-state=\"(front|back)\"[^>]*>(.*?)</article>',s,re.S)
assert windows==['front','back'] and len(cards)==2 and [state for state,_ in cards]==['front','back']
front,back=[body for _,body in cards]
assert front.replace('is-hidden','is-visible').replace('\"hidden\"','\"visible\"').replace('aria-hidden=\"true\"','aria-hidden=\"false\"')==back
assert s.count('class=\"replay-button previewAudioButton\"')==4 and s.count('/buːx/')==2 and 'class=\"image\"' not in s
css=re.search(r'/\* BEGIN IMPROVED ANKI CSS \*/(.*?)/\* END IMPROVED ANKI CSS \*/',s,re.S).group(1)
universal=rule(css,'*, *::before, *::after'); card=rule(css,'.card'); qa=rule(css,'#qa'); shell=rule(css,'.customCard'); content=rule(css,'.cardContent')
assert 'box-sizing: border-box' in universal and 'box-sizing: border-box' in shell and 'box-sizing: border-box' in content
assert all(token in card for token in ('display: block','width: 100%','min-width: 0','min-height: 0','margin: 0'))
assert all(token in qa for token in ('width: 100%','min-width: 0'))
assert all(token in shell for token in ('display: block','width: 100%','max-width: none','min-height: 0','margin: 0')) and not re.search(r'(?m)^\s*height\s*:',shell)
assert all(token in content for token in ('width: 100%','max-width: 900px','margin: 0 auto','padding:')) and content.count('clamp(')>=2
assert 'font-size: clamp(' in rule(css,'.targetWord')
assert all('font-size: clamp(' in rule(css,selector) for selector in ('.definitionText','.exampleSentenceText','.sentenceTranslation'))
assert 'gap: clamp(' in rule(css,'.wordHero') and 'gap: clamp(' in rule(css,'.cardSections')
heading=rule(css,'.sectionHeading'); definition=rule(css,'.definitionText'); panel=rule(css,'.examplePanel'); translation=rule(css,'.sentenceTranslation')
assert all(token in heading for token in ('font-family:','letter-spacing:','text-transform:')) and 'line-height:' in definition
assert all(token in panel for token in ('background:','border-left:','border-radius:','padding:')) and all(token in translation for token in ('color:','line-height:'))
audio=rule(css,'.replay-button'); focus=rule(css,'.replay-button:focus-visible'); icon=rule(css,'.replay-button svg path')
assert all(token in audio for token in ('min-width: 34px','min-height: 34px','border-radius: 50%','background: #233a57','border: 1px solid #6aa9f4','color: #f5f9ff'))
assert all(token in focus for token in ('outline: 3px solid #93c5fd','outline-offset: 3px')) and 'fill: currentColor' in icon
mobile=at_rule(css,'@media (max-width: 420px)')
assert 'padding:' in rule(mobile,'.cardContent') and 'gap:' in rule(mobile,'.wordHero') and 'gap:' in rule(mobile,'.cardSections') and 'padding:' in rule(mobile,'.examplePanel') and 'align-items: flex-start' in rule(mobile,'.exampleSentenceLine')
assert not re.search(r'100(?:vh|dvh|svh|lvh)',css,re.I)
forbidden=(r'<script\b',r'<link\b',r'<(?:img|audio|video|iframe|object|embed)\b',r'\b(?:src|href)\s*=',r'@import\b',r'url\s*\(',r'https?://',r'\{\{')
assert not any(re.search(pattern,s,re.I) for pattern in forbidden)
print('PREVIEW-SOURCE PASS: selector-bound full-width, hierarchy, clamp, audio focus/contrast and mobile declarations')"</automated>
    <automated>uv run --offline --no-sync --frozen --no-env-file python -c "import csv; from pathlib import Path; apkg=Path('exports/anki_previews/normal-card-improved-test.apkg'); tsv=Path('exports/anki_previews/normal-card-improved-test.tsv'); fields=['SortIndex','word','IPA','Definitions','Example Sentence','Translation','word_audio','sentence_audio','Image']; assert apkg.is_file() and apkg.stat().st_size>0; raw=tsv.read_bytes(); assert raw and not raw.startswith(b'\xef\xbb\xbf') and b'\r' not in raw and raw.endswith(b'\n') and raw.count(b'\n')==4; rows=list(csv.reader(tsv.open(encoding='utf-8',newline=''),delimiter='\t')); assert len(rows)==4 and rows[0]==fields and [row[1] for row in rows[1:]]==['Buch','Wasser','lernen']; assert all(len(row)==9 and row[6:]==['','',''] for row in rows[1:]); print('DELIVERY PASS: APKG non-empty; TSV UTF-8/no-BOM/newline-empty/LF-only with exact rows')"</automated>
  </verify>
  <done>O baseline global e o scan dinâmico de IDs passam antes de qualquer write; o preview possui os dois estados e contratos selector-bound de D-05 a D-09; APKG/TSV usam as identidades, três GUIDs explícitos e linhas de D-03/D-04, não contêm mídia e foram gerados somente com uv offline/no-sync/frozen/no-env-file.</done>
</task>

<task id="039-02" type="auto">
  <name>Inspecionar ZIP/SQLite/TSV e registrar UI proof</name>
  <files>
    - CREATE: .planning/quick/039-preview-melhorado-anki/UI-PROOF.md
  </files>
  <preproof>
    <automated>uv run --offline --no-sync --frozen --no-env-file python -c "import base64,hashlib,json,os,stat,subprocess; from pathlib import Path
root=Path.cwd(); allowed={'normal_card_improved_preview.html','exports/anki_previews/normal-card-improved-test.apkg','exports/anki_previews/normal-card-improved-test.tsv','.planning/quick/039-preview-melhorado-anki/UI-PROOF.md','.planning/quick/039-preview-melhorado-anki/039-SUMMARY.md'}
def git_bytes(*args): return subprocess.run(['git',*args],check=True,capture_output=True).stdout
def filtered_status():
    raw=git_bytes('status','--porcelain=v1','-z','--untracked-files=all'); kept=[]
    for record in raw.split(b'\0'):
        if not record: continue
        candidate=record[3:].decode('utf-8','surrogateescape').replace('\\\\','/') if len(record)>=4 and record[2:3]==b' ' else None
        if candidate not in allowed: kept.append(record)
    blob=b'\0'.join(kept)+(b'\0' if kept else b''); return base64.b64encode(blob).decode('ascii'),hashlib.sha256(blob).hexdigest(),len(kept)
def repository_digest():
    raw_paths=sorted(path for path in git_bytes('ls-files','-z','--cached','--others','--exclude-standard').split(b'\0') if path); digest=hashlib.sha256(); count=0
    for raw_path in raw_paths:
        relative=raw_path.decode('utf-8','surrogateescape').replace('\\\\','/')
        if relative in allowed: continue
        path=root/Path(relative); digest.update(b'PATH\0'+raw_path+b'\0')
        try: mode=os.lstat(path).st_mode
        except FileNotFoundError: digest.update(b'MISSING\0'); count+=1; continue
        if stat.S_ISREG(mode): marker,payload=b'FILE\0',path.read_bytes()
        elif stat.S_ISLNK(mode): marker,payload=b'SYMLINK\0',os.readlink(path).encode('utf-8','surrogateescape')
        else: marker,payload=b'OTHER\0',str(mode).encode('ascii')
        digest.update(marker+len(payload).to_bytes(8,'big')+payload+b'\0'); count+=1
    return digest.hexdigest(),count
def file_hash(relative): return hashlib.sha256((root/relative).read_bytes()).hexdigest()
def snapshot():
    status_b64,status_hash,status_count=filtered_status(); repository_hash,repository_count=repository_digest()
    return {'head':git_bytes('rev-parse','HEAD').decode('ascii').strip(),'staged_diff_sha256':hashlib.sha256(git_bytes('diff','--cached','--binary','--no-ext-diff','--no-textconv')).hexdigest(),'filtered_status_b64':status_b64,'filtered_status_sha256':status_hash,'filtered_status_entry_count':status_count,'repository_paths_sha256':repository_hash,'repository_paths_count':repository_count,'uv_lock_sha256':file_hash('uv.lock'),'pyproject_sha256':file_hash('pyproject.toml')}
baseline_path=Path(os.environ['LOCALAPPDATA'])/'Temp'/'opencode'/'quick-039-integrity-baseline.json'; baseline=json.loads(baseline_path.read_text(encoding='utf-8')); assert baseline['allowed_outputs']==sorted(allowed); after=snapshot(); assert after==baseline['before']; baseline['after']=after; baseline_path.write_text(json.dumps(baseline,ensure_ascii=True,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n'); print('GLOBAL AFTER CAPTURE PASS:',after['repository_paths_count'],'paths')"</automated>
  </preproof>
  <action>
    Execute `<preproof>` imediatamente após os três outputs de Task 039-01 e antes de criar UI-PROOF; ele deve capturar `after`, exigir igualdade com `before` e persistir ambos no baseline externo. Então inspecione somente o APKG recém-gerado. Use `zipfile.ZipFile.read` para ler `media` e o único membro `collection.anki2` ou `collection.anki21`; grave apenas esse membro em `tempfile.TemporaryDirectory` e abra-o com `sqlite3`. Não use `extractall`. Confirme exatamente: ZIP íntegro; manifesto `media` igual a `{}` e nenhum membro numérico; três rows em `notes`; três rows em `cards`; três `cards.nid` distintos; `cards.ord == 0` em todos; `notes.mid == 1762801039`; `cards.did == 1762801040`; model/deck JSON com IDs e nomes de D-03; exatamente um template, chamado `Card 1`; field list de D-04 na ordem; conteúdo das notes igual ao TSV; e áudio/imagem vazios. Recalcule os três GUIDs com `genanki.guid_for('Multilang::Card Improved Preview', str(model_id), SortIndex, word)` e exija conjunto exatamente igual a `notes.guid` e `count(distinct guid) == 3`.

    Valide qfmt/afmt/CSS, não somente sua presença. Todas as referências Mustache devem pertencer aos nove fields ou ao built-in `FrontSide`; qfmt não contém script, contém condicionais IPA/Image, slots de áudio, Translation oculta e as classes de hierarquia; afmt é exatamente o reveal fixo de D-08; nenhum template usa `innerHTML`, URL/import, sound tag ou referência de field desconhecida. O CSS armazenado deve ser textualmente igual ao bloco marcado do preview depois de `strip`. Reaplique as assertions vinculadas aos seletores: border-box em universal/shell/wrapper; full-width/natural-height; `.cardContent` 900px e padding clamp; clamp em palavra/três textos; gap clamp em hero/seções; heading/definition/example/translation; áudio com dimensões/cores/focus/SVG; e declarações específicas dentro do bloco 420px. Repita o scan dinâmico dos IDs em todos os arquivos tracked/untracked não ignorados fora de quick039/outputs, ignorando de modo seguro binários e `UnicodeDecodeError`; não use somente uma lista de IDs conhecidos.

    Crie `UI-PROOF.md` com um único fenced JSON válido e os campos de topo `proof_bundle_version`, `scope`, `route_state`, `environment`, `viewport`, `evidence_inputs`, `commands_or_manual_steps`, `observations`, `artifacts`, `privacy`, `result`, `claim_limits` e `source_integrity`. Registre no mínimo 20 observações, cada uma com `slot_id`, `claim`, `route_state`, `observation`, `evidence_kind`, `artifact_path`, `privacy`, `result` e `claim_limit`: pelo menos 8 observações `pass` no slot source com kinds cobrindo `code` e `test`; pelo menos 8 `pass` no slot APKG com kinds cobrindo `code`, `test` e `delivery`; e pelo menos 4 `human_needed` no slot native com kinds cobrindo `delivery` e `human`. Não aceite outro slot/result/kind. Inclua saídas reais dos validadores; não invente browser/Anki evidence. `result.overall` deve ser `human_needed` e `result.by_slot` deve listar exatamente os três estados.

    Em `artifacts`, registre preview, APKG, TSV e UI-PROOF com `visibility`, `retention`, `sensitivity` e `safe_to_publish`; mantenha-os `local_only`/não publicáveis sem aprovação. Leia o baseline externo criado no preflight e recalcule o mesmo snapshot global depois dos outputs. Em `source_integrity`, registre `allowed_outputs` e objetos `before`, `after`, `live`, cada qual contendo HEAD, staged-diff SHA-256 global, filtered-status base64/SHA-256/count, repository-paths SHA-256/count, `uv_lock_sha256` e `pyproject_sha256`. `before` deve ser o baseline; `after` deve ser a captura pós-write; o parser deve recomputar `live`. Exija igualdade estrutural `before == after == live`; nenhum pathspec parcial substitui essa prova global. Os cinco únicos paths filtráveis são os quatro outputs da quick task e `039-SUMMARY.md`; o baseline falha se algum já existia. Registre o passo humano exato para abrir `exports/anki_previews/` no Explorer, importar o APKG, revisar os três cards front/back em largura ampla e estreita e responder com aprovação/problemas. Explique que, por D-04, áudio/imagem vazios não renderizam controles/mídia no APKG; o contrato dos botões é provado no preview/CSS, não como playback.
  </action>
  <verify>
    <automated>uv run --offline --no-sync --frozen --no-env-file python -c "import csv,json,os,re,sqlite3,stat,subprocess,tempfile,zipfile,genanki; from pathlib import Path
apkg=Path('exports/anki_previews/normal-card-improved-test.apkg'); tsv=Path('exports/anki_previews/normal-card-improved-test.tsv'); preview=Path('normal_card_improved_preview.html').read_text(encoding='utf-8')
fields=['SortIndex','word','IPA','Definitions','Example Sentence','Translation','word_audio','sentence_audio','Image']; model_id,deck_id=1762801039,1762801040; note_type='Multilang::Card Improved Preview'
def rule(source,selector):
    match=re.search(re.escape(selector)+r'\s*\{([^}]*)\}',source,re.S); assert match,'missing selector '+selector; return match.group(1)
def at_rule(source,marker):
    start=source.index(marker); opening=source.index('{',start); depth=0
    for index in range(opening,len(source)):
        depth+=source[index]=='{'; depth-=source[index]=='}'
        if depth==0: return source[opening+1:index]
    raise AssertionError('unclosed '+marker)
excluded_prefix='.planning/quick/039-preview-melhorado-anki/'; excluded_outputs={'normal_card_improved_preview.html','exports/anki_previews/normal-card-improved-test.apkg','exports/anki_previews/normal-card-improved-test.tsv'}; identifiers=(str(model_id),str(deck_id))
raw_paths=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],check=True,capture_output=True).stdout; hits=[]
for item in raw_paths.split(b'\0'):
    if not item: continue
    relative=item.decode('utf-8','surrogateescape').replace('\\\\','/')
    if relative.startswith(excluded_prefix) or relative in excluded_outputs: continue
    path=Path(relative)
    try: mode=os.lstat(path).st_mode
    except FileNotFoundError: continue
    if not stat.S_ISREG(mode): continue
    payload=path.read_bytes()
    if b'\0' in payload: continue
    try: text=payload.decode('utf-8')
    except UnicodeDecodeError: continue
    hits.extend((relative,identifier) for identifier in identifiers if identifier in text)
assert not hits,'experimental ID collision outside quick039/outputs: '+repr(hits)
with zipfile.ZipFile(apkg) as archive:
    assert archive.testzip() is None
    names=archive.namelist(); collections=[name for name in names if name in {'collection.anki2','collection.anki21'}]
    assert len(collections)==1 and 'media' in names and json.loads(archive.read('media').decode('utf-8'))=={} and not any(name.isdigit() for name in names)
    with tempfile.TemporaryDirectory() as directory:
        collection_path=Path(directory)/collections[0]; collection_path.write_bytes(archive.read(collections[0]))
        with sqlite3.connect(collection_path) as connection:
            notes=connection.execute('select id,guid,flds,mid from notes').fetchall(); cards=connection.execute('select nid,did,ord from cards').fetchall()
            distinct_guid_count=connection.execute('select count(distinct guid) from notes').fetchone()[0]
            models=json.loads(connection.execute('select models from col').fetchone()[0]); decks=json.loads(connection.execute('select decks from col').fetchone()[0])
assert len(notes)==3 and len(cards)==3 and len({row[0] for row in notes})==3 and len({row[0] for row in cards})==3 and {row[0] for row in cards}=={row[0] for row in notes}
assert {row[3] for row in notes}=={model_id} and {row[1] for row in cards}=={deck_id} and {row[2] for row in cards}=={0}
note_rows=sorted((row[2].split('\x1f') for row in notes),key=lambda row:int(row[0])); actual_guids={row[1] for row in notes}; expected_guids={genanki.guid_for(note_type,str(model_id),row[0],row[1]) for row in note_rows}
assert distinct_guid_count==3 and len(actual_guids)==3 and actual_guids==expected_guids
model=models[str(model_id)]; deck=decks[str(deck_id)]
assert model['name']==note_type and deck['name']=='Multilang Improved Card Test' and [field['name'] for field in model['flds']]==fields
assert len(model['tmpls'])==1 and model['tmpls'][0]['name']=='Card 1' and model['tmpls'][0]['ord']==0
assert [row[0] for row in note_rows]==['1','2','3'] and [row[1] for row in note_rows]==['Buch','Wasser','lernen'] and all(len(row)==9 and row[6:]==['','',''] for row in note_rows)
raw_tsv=tsv.read_bytes(); assert raw_tsv and not raw_tsv.startswith(b'\xef\xbb\xbf') and b'\r' not in raw_tsv and raw_tsv.endswith(b'\n') and raw_tsv.count(b'\n')==4
with tsv.open(encoding='utf-8',newline='') as handle: tsv_rows=list(csv.reader(handle,delimiter='\t'))
assert tsv_rows==[fields,*note_rows]
template=model['tmpls'][0]; qfmt,afmt,css=template['qfmt'],template['afmt'],model['css']; tokens=re.findall(r'\{\{([^{}]+)\}\}',qfmt+afmt); refs={token.strip().lstrip('#/^').split(':')[-1] for token in tokens}
assert refs<=set(fields)|{'FrontSide'} and all(token in qfmt for token in ('{{word}}','{{#IPA}}','{{IPA}}','{{/IPA}}','{{word_audio}}','{{Definitions}}','{{#Image}}','{{Image}}','{{/Image}}','{{Example Sentence}}','{{sentence_audio}}','{{Translation}}','cardContent','wordHero','sectionHeading','definitionText','examplePanel','sentenceTranslation'))
dq=chr(34); assert '<script' not in qfmt.lower() and 'id='+dq+'translation'+dq in qfmt and 'style='+dq+'display:none;'+dq in qfmt
expected_afmt='{{FrontSide}}\n\n<script>\n  document.getElementById('+dq+'translation'+dq+').style.display = '+dq+'block'+dq+';\n</script>'; assert afmt.strip()==expected_afmt
combined=(qfmt+afmt+css).lower(); assert 'innerhtml' not in combined and '[sound:' not in combined and not any(token in combined for token in ('http://','https://','@import','url('))
source_css=re.search(r'/\* BEGIN IMPROVED ANKI CSS \*/(.*?)/\* END IMPROVED ANKI CSS \*/',preview,re.S).group(1).strip(); assert css.strip()==source_css
universal=rule(css,'*, *::before, *::after'); card=rule(css,'.card'); qa=rule(css,'#qa'); shell=rule(css,'.customCard'); content=rule(css,'.cardContent')
assert 'box-sizing: border-box' in universal and 'box-sizing: border-box' in shell and 'box-sizing: border-box' in content
assert all(token in card for token in ('display: block','width: 100%','min-width: 0','min-height: 0','margin: 0')) and all(token in qa for token in ('width: 100%','min-width: 0')) and all(token in shell for token in ('display: block','width: 100%','max-width: none','min-height: 0','margin: 0'))
assert all(token in content for token in ('width: 100%','max-width: 900px','margin: 0 auto','padding:')) and content.count('clamp(')>=2
assert 'font-size: clamp(' in rule(css,'.targetWord') and all('font-size: clamp(' in rule(css,selector) for selector in ('.definitionText','.exampleSentenceText','.sentenceTranslation')) and 'gap: clamp(' in rule(css,'.wordHero') and 'gap: clamp(' in rule(css,'.cardSections')
heading=rule(css,'.sectionHeading'); definition=rule(css,'.definitionText'); panel=rule(css,'.examplePanel'); translation=rule(css,'.sentenceTranslation'); audio=rule(css,'.replay-button'); focus=rule(css,'.replay-button:focus-visible'); icon=rule(css,'.replay-button svg path')
assert all(token in heading for token in ('font-family:','letter-spacing:','text-transform:')) and 'line-height:' in definition and all(token in panel for token in ('background:','border-left:','border-radius:','padding:')) and all(token in translation for token in ('color:','line-height:'))
assert all(token in audio for token in ('min-width: 34px','min-height: 34px','border-radius: 50%','background: #233a57','border: 1px solid #6aa9f4','color: #f5f9ff')) and all(token in focus for token in ('outline: 3px solid #93c5fd','outline-offset: 3px')) and 'fill: currentColor' in icon
mobile=at_rule(css,'@media (max-width: 420px)'); assert 'padding:' in rule(mobile,'.cardContent') and 'gap:' in rule(mobile,'.wordHero') and 'gap:' in rule(mobile,'.cardSections') and 'padding:' in rule(mobile,'.examplePanel') and 'align-items: flex-start' in rule(mobile,'.exampleSentenceLine') and not re.search(r'100(?:vh|dvh|svh|lvh)',css,re.I)
print('APKG-STRUCTURE PASS: dynamic IDs, exact GUIDs, 3 distinct nids/ord0, one Card 1, selector CSS, LF TSV and zero media')"</automated>
    <automated>uv run --offline --no-sync --frozen --no-env-file python -c "import base64,hashlib,json,os,re,stat,subprocess; from pathlib import Path
proof_path=Path('.planning/quick/039-preview-melhorado-anki/UI-PROOF.md'); match=re.search(r'```json\s*(.*?)\s*```',proof_path.read_text(encoding='utf-8'),re.S); assert match; data=json.loads(match.group(1))
required={'proof_bundle_version','scope','route_state','environment','viewport','evidence_inputs','commands_or_manual_steps','observations','artifacts','privacy','result','claim_limits','source_integrity'}; assert required<=set(data)
expected_results={'improved-normal-card-preview-source':'pass','improved-normal-card-apkg-structure':'pass','improved-normal-card-native-anki-appearance':'human_needed'}; assert data['result']=={'overall':'human_needed','by_slot':expected_results}
observation_fields={'slot_id','claim','route_state','observation','evidence_kind','artifact_path','privacy','result','claim_limit'}; observations=data['observations']; assert len(observations)>=20 and all(observation_fields<=set(item) for item in observations)
source=[item for item in observations if item['slot_id']=='improved-normal-card-preview-source']; apkg=[item for item in observations if item['slot_id']=='improved-normal-card-apkg-structure']; native=[item for item in observations if item['slot_id']=='improved-normal-card-native-anki-appearance']
assert len(source)>=8 and all(item['result']=='pass' and item['evidence_kind'] in {'code','test'} for item in source) and {'code','test'}<={item['evidence_kind'] for item in source}
assert len(apkg)>=8 and all(item['result']=='pass' and item['evidence_kind'] in {'code','test','delivery'} for item in apkg) and {'code','test','delivery'}<={item['evidence_kind'] for item in apkg}
assert len(native)>=4 and all(item['result']=='human_needed' and item['evidence_kind'] in {'delivery','human'} for item in native) and {'delivery','human'}<={item['evidence_kind'] for item in native}
assert len(source)+len(apkg)+len(native)==len(observations)
artifact_fields={'path','visibility','retention','sensitivity','safe_to_publish'}; assert len(data['artifacts'])>=4 and all(artifact_fields<=set(item) and item['safe_to_publish'] is False for item in data['artifacts'])
assert any(step.get('result')=='human_needed' and step.get('slot_id')=='improved-normal-card-native-anki-appearance' for step in data['commands_or_manual_steps'])
root=Path.cwd(); allowed={'normal_card_improved_preview.html','exports/anki_previews/normal-card-improved-test.apkg','exports/anki_previews/normal-card-improved-test.tsv','.planning/quick/039-preview-melhorado-anki/UI-PROOF.md','.planning/quick/039-preview-melhorado-anki/039-SUMMARY.md'}
def git_bytes(*args):
    return subprocess.run(['git',*args],check=True,capture_output=True).stdout
def filtered_status():
    raw=git_bytes('status','--porcelain=v1','-z','--untracked-files=all'); kept=[]
    for record in raw.split(b'\0'):
        if not record: continue
        candidate=record[3:].decode('utf-8','surrogateescape').replace('\\\\','/') if len(record)>=4 and record[2:3]==b' ' else None
        if candidate not in allowed: kept.append(record)
    blob=b'\0'.join(kept)+(b'\0' if kept else b'')
    return base64.b64encode(blob).decode('ascii'),hashlib.sha256(blob).hexdigest(),len(kept)
def repository_digest():
    raw_paths=sorted(path for path in git_bytes('ls-files','-z','--cached','--others','--exclude-standard').split(b'\0') if path); digest=hashlib.sha256(); count=0
    for raw_path in raw_paths:
        relative=raw_path.decode('utf-8','surrogateescape').replace('\\\\','/')
        if relative in allowed: continue
        path=root/Path(relative); digest.update(b'PATH\0'+raw_path+b'\0')
        try: mode=os.lstat(path).st_mode
        except FileNotFoundError: digest.update(b'MISSING\0'); count+=1; continue
        if stat.S_ISREG(mode): marker,payload=b'FILE\0',path.read_bytes()
        elif stat.S_ISLNK(mode): marker,payload=b'SYMLINK\0',os.readlink(path).encode('utf-8','surrogateescape')
        else: marker,payload=b'OTHER\0',str(mode).encode('ascii')
        digest.update(marker+len(payload).to_bytes(8,'big')+payload+b'\0'); count+=1
    return digest.hexdigest(),count
def file_hash(relative): return hashlib.sha256((root/relative).read_bytes()).hexdigest()
def snapshot():
    status_b64,status_hash,status_count=filtered_status(); repository_hash,repository_count=repository_digest()
    return {'head':git_bytes('rev-parse','HEAD').decode('ascii').strip(),'staged_diff_sha256':hashlib.sha256(git_bytes('diff','--cached','--binary','--no-ext-diff','--no-textconv')).hexdigest(),'filtered_status_b64':status_b64,'filtered_status_sha256':status_hash,'filtered_status_entry_count':status_count,'repository_paths_sha256':repository_hash,'repository_paths_count':repository_count,'uv_lock_sha256':file_hash('uv.lock'),'pyproject_sha256':file_hash('pyproject.toml')}
baseline_path=Path(os.environ['LOCALAPPDATA'])/'Temp'/'opencode'/'quick-039-integrity-baseline.json'; baseline=json.loads(baseline_path.read_text(encoding='utf-8')); live=snapshot(); integrity=data['source_integrity']
assert baseline['schema_version']==1 and baseline['allowed_outputs']==sorted(allowed) and baseline['before']==baseline['after']
assert integrity['allowed_outputs']==sorted(allowed) and integrity['before']==baseline['before'] and integrity['after']==baseline['after'] and integrity['live']==live and live==baseline['after']
limits=json.dumps(data['claim_limits'],ensure_ascii=False).lower(); assert 'human_needed' in limits and 'anki' in limits
print('UI-PROOF PASS: 8 source + 8 APKG + 4 native minimums; global HEAD/stage/status/repository/lock state preserved; native remains human_needed')"</automated>
    <automated>git diff --check -- "normal_card_improved_preview.html" "exports/anki_previews/normal-card-improved-test.tsv" ".planning/quick/039-preview-melhorado-anki/039-PLAN.md" ".planning/quick/039-preview-melhorado-anki/UI-PROOF.md" && for file in "normal_card_improved_preview.html" "exports/anki_previews/normal-card-improved-test.tsv" ".planning/quick/039-preview-melhorado-anki/039-PLAN.md" ".planning/quick/039-preview-melhorado-anki/UI-PROOF.md"; do test -z "$(git -c core.autocrlf=false diff --no-index --check -- /dev/null "$file" 2>&1)" || exit 1; done</automated>
  </verify>
  <done>A inspeção ZIP/SQLite/TSV passa todos os contratos de D-03 a D-11, incluindo GUIDs/card ord/nids/template/LF e scan dinâmico de IDs; UI-PROOF cumpre mínimos 8/8/4 e mantém aparência nativa human_needed; o snapshot global prova before == after == live para HEAD, staged diff, status, todos os paths Git, uv.lock e pyproject.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Preview/APKG → renderer HTML do browser/Anki | Markup e CSS locais entram em um renderer; somente o reveal fixo do verso pode executar no APKG. |
| APKG experimental → coleção Anki do usuário | IDs de model/deck determinam se a importação cria uma variante isolada ou sobrescreve tipos existentes. |
| ZIP gerado → inspector SQLite | O inspector lê um archive local e deve evitar extração arbitrária de caminhos. |
| Gerador local → ambiente/configuração | A geração deve usar apenas dados fixos e genanki, sem tocar em secrets/providers/rede. |
| Quick task → worktree concorrente | Novos artefatos não podem alterar source, testes ou mudanças preexistentes. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q039-01 | Tampering / Elevation of privilege | qfmt/afmt e fields | mitigate | Fields são strings fixas; qfmt não contém script; afmt aceita somente o reveal literal; inspeção rejeita innerHTML, referência desconhecida, URL/import e sound tag. |
| T-Q039-02 | Spoofing / Tampering | IDs e GUIDs do model/deck/notes | mitigate | Fixar IDs 1762801039/1762801040, fazer scan dinâmico do repositório, gerar GUID por note type/model/sort/word e validar conjunto exato/distinto no SQLite. |
| T-Q039-03 | Information disclosure / Tampering | geração uv/genanki e lockfiles | mitigate | Toda invocação usa `uv run --offline --no-sync --frozen --no-env-file`; não lê `.env`, não importa providers e hashes globais confirmam `uv.lock`/`pyproject.toml` inalterados. |
| T-Q039-04 | Path traversal | inspeção APKG | mitigate | Ler membros por nome com `ZipFile.read`, aceitar somente collection.anki2/collection.anki21, usar TemporaryDirectory e proibir `extractall`. |
| T-Q039-05 | Repudiation / Tampering | worktree concorrente | mitigate | Baseline e parser independentes comparam before/after/live de HEAD, staged diff global, status porcelain filtrado e digest de todo path tracked/untracked não ignorado, incluindo MISSING; somente cinco outputs exatos são filtrados. |
</threat_model>

## Source Coverage Audit

| SOURCE | ID | Feature/Requirement | Plan | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Preview visual melhorado e APKG importável para teste no Anki | 039 | COVERED | Tasks 039-01 e 039-02 entregam e inspecionam ambos |
| REQ | — | Quick mode não possui requirement IDs de ROADMAP | 039 | COVERED | `requirements: []`; lifecycle de fase permanece read-only |
| RESEARCH | — | genanki local e inspeção ZIP/SQLite já são padrões do projeto | 039 | COVERED | Context/interfaces e verificadores reutilizam o stack existente |
| CONTEXT | D-01 | Variante isolada sem produção/testes | 039 | COVERED | Write set e snapshot global de todos os paths Git |
| CONTEXT | D-02 | Quatro caminhos de entrega exatos | 039 | COVERED | Frontmatter e files por tarefa |
| CONTEXT | D-03 | Model/deck/GUIDs exclusivos e nomes exatos | 039 | COVERED | Scan dinâmico, `guid_for` e SQLite validator |
| CONTEXT | D-04 | Três cards, nove fields, áudio/imagem vazios | 039 | COVERED | Linhas exatas + APKG/TSV comparison |
| CONTEXT | D-05 | Shell full-width/natural e wrapper 900px | 039 | COVERED | CSS compartilhado + dois validadores |
| CONTEXT | D-06 | clamp e botão nativo circular 34px | 039 | COVERED | Assertions vinculadas a seletores, cores, SVG e focus-visible |
| CONTEXT | D-07 | Hierarquia dark e mobile 420px | 039 | COVERED | Regras de heading/panel/translation e declarations dentro do media block |
| CONTEXT | D-08 | Translation/IPA/Image/audio e reveal seguro | 039 | COVERED | qfmt/afmt token/script validation |
| CONTEXT | D-09 | Preview exatamente front/back, sem scripts/rede/assets | 039 | COVERED | Parser de estados, corpos espelhados e scan negativo |
| CONTEXT | D-10 | `uv run --offline --no-sync --frozen --no-env-file python` + genanki local | 039 | COVERED | Todas as invocações usam os quatro gates |
| CONTEXT | D-11 | ZIP/SQLite/TSV/UI proof e Anki human_needed | 039 | COVERED | Task 039-02 exige 8/8/4 observações e 20 total |
| CONTEXT | D-12 | Lifecycle sem LOG/stage/commit | 039 | COVERED | Baseline global, parser live e final guard após SUMMARY |

Excluído sem gap: alteração do template/testes de produção, provider/media real, publicação, aprovação automática de aparência nativa e atualização de LOG/ROADMAP/SPEC.

<verification>
Execute todos os comandos a partir da raiz. O preflight global deve ocorrer antes do primeiro write. Os validadores de Task 039-01 cobrem source/entrega; o inspector de Task 039-02 é a autoridade estrutural do APKG/TSV/GUIDs/IDs/CSS; o parser do UI-PROOF exige mínimos por slot e recomputa a integridade global live. Uma falha deve interromper a conclusão, sem ajustar produção para fazê-la passar.
</verification>

<success_criteria>
- O preview raiz contém exatamente dois estados espelhados e passa o validador source obrigatório.
- Shell, wrapper 900px, clamp, botão 34px, hierarquia, paleta e breakpoint 420px aparecem tanto no bloco CSS do preview quanto no model APKG.
- APKG e TSV existem nos caminhos exatos e são não vazios.
- ZIP/SQLite contém exatamente 3 notes/cards, três nids/GUIDs distintos e esperados, ord 0, model/deck exclusivos, nove fields em ordem, um único template `Card 1` e zero mídia.
- APKG e TSV contêm exatamente Buch, Wasser e lernen com os valores definidos e três fields finais vazios; TSV foi aberto com `newline=''` e possui somente LF.
- qfmt/afmt preservam front/back, condicionais e reveal fixo sem innerHTML ou referência inválida.
- UI-PROOF registra no mínimo 8 source pass, 8 APKG pass e 4 native human_needed (20 total), com evidence kinds corretos, passos humanos e metadados de privacidade.
- Scan dinâmico não encontra os IDs fora de quick039/outputs; checks textuais passam.
- HEAD, staged diff global, status filtrado, digest de todos os paths Git, uv.lock e pyproject permanecem estruturalmente iguais before/after/live; nenhum stage/commit é criado.
</success_criteria>

<output>
Após executar as duas tarefas, criar `.planning/quick/039-preview-melhorado-anki/039-SUMMARY.md` — este é o único quinto path permitido e só pode surgir neste estágio executor. Rode `test -z "$(git -c core.autocrlf=false diff --no-index --check -- /dev/null ".planning/quick/039-preview-melhorado-anki/039-SUMMARY.md" 2>&1)"` e depois rerun o comando automatizado do parser `UI-PROOF` de Task 039-02; como o snapshot filtra somente os cinco paths declarados, ele deve continuar provando `before == after == live`. Preserve o JSON baseline fora do worktree em `%LOCALAPPDATA%/Temp/opencode/quick-039-integrity-baseline.json` até o verifier terminar, para que a recomputação independente continue executável; ele pode ser removido somente após `039-VERIFICATION.md`. Não criar `039-VERIFICATION.md` no executor; o verifier fará isso depois. Não editar `.planning/quick/LOG.md`, `.planning/ROADMAP.md` ou `.planning/SPEC.md`; o orchestrator cuida do LOG. Não fazer staging ou commit.
</output>
