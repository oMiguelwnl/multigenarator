# Multilingual lexical, corpus and model source research

Research date: 2026-09-12. Scope: all 22 modern languages in the approved multilingual completion design. Classical Latin remains isolated. This is source selection and acquisition evidence, not a linguistic review, redistribution decision, or activation receipt.

Use **raw English-edition Wiktextract JSONL** as the shared downloadable lexical candidate input; **Croatian Wordnet plus Princeton WordNet 3.0** supplies Croatian-specific synset evidence. Use **release-pinned UD CoNLL-U** for observed contextual morphology and evaluation. The machine-readable companion is `src/multilang/resources/vocabulary_sources.json`; it records exact download URLs, licenses, restrictions, processor packages and dependencies for every language. Downloads can populate quarantine now. Corpus observations, dictionary senses and approved Core identities remain separate records.

## Audit of existing assets

I read all `assets/frequency/*/curated-v1.csv` files. The 21 modern-language files excluding Korean contain 3000 rows each (63,000 total), with `part_of_speech=unknown` in every row. Their columns are language, frequency_list_version, level, rank, source_rank, display_form, lemma, lemma_key, part_of_speech, definition_seed, source_provenance and curation_flags. They supply candidate ordering, not validated lemma/POS/sense identities. Latin has a separate 10-row file and is excluded from the modern inventory.

The separate `.multilang/phase32/bundles/multilang-korean-frequency-v1/` contains 3000 real NIKL-derived records, 1000 per level, and an immutable manifest. The inventory SHA-256 is `209a98c134bc9c65ecca459dc71cc9065ee8b1e24700071573b09deea028ab3a`; bundle digest is `d235d962f706ce95822b00ec4dc65d4fa55b96b4e28238720adf0df5cf86582a`. Source version is `2003-06-04.revised-2019-05-30`; source snapshot has 5965 rows. All 3000 lexical `sense_id` values equal `nikl:<source_rank>`. These are learner-list source references, not independently established semantic senses. Existing manifest strings say `approved-redistribution` and `repository-redistributable`; this audit reports those existing values without creating or extending approval. All entries carry `modernity_review_required`.

Korean POS counts: NNG 1612, VV 764, MAG 208, VA 196, NNB 75, MM 37, NNP 36, NP 22, VX 21, NR 19, IC 10. These are Kiwi/Sejong tags, not directly interchangeable with UD UPOS. Preserve the recorded Kiwi 0.23.2 / model 0.23.0 configuration and perform explicit tag mappings.

The existing runtime guide `docs/lexical-data.md` uses a generic local cache and generated card definitions. Earlier `docs/generation-process-improvement-plan.md` explicitly proposes Kaikki/Wiktionary as lexical grounding. Therefore a provenance-preserving offline ingestion adapter is compatible with recorded preferences; it must not silently replace generated card-definition behavior or revive a provider-specific runtime dependency.

## Shared lexical extraction

The [official raw download index](https://kaikki.org/dictionary/rawdata.html) links [raw English-edition JSONL gzip](https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz), currently advertised as 2.7 GB compressed / 23.1 GB uncompressed, from the 2026-09-02 dump extracted 2026-09-09. These are mutable download URLs: record the retrieval date, actual bytes, SHA-256, extractor version and upstream dump date. Download once and stream language partitions; do not download the combined archive 22 times. Bound compressed bytes, decompressed bytes, record length and output count separately.

Kaikki marks **postprocessed per-language and per-word downloads deprecated**. They remain useful for a bounded parser smoke test; new production acquisition should use the raw English-edition export. Other Wiktionary editions have different schemas and gloss languages, so a generic English-edition parser must not assume it can read them.

[Wiktextract's source documentation](https://github.com/tatuylonen/wiktextract) defines JSONL records with `word`, `lang_code`, `pos`, `senses`, optional `forms`, sounds and etymology information. Treat each sense as evidence under its source entry. Preserve a native sense identifier if present; otherwise use an immutable snapshot digest plus record locator and sense position as an **evidence reference**, then maintain separately reviewed stable semantic identities across revisions. A changing gloss hash or sense ordinal is not an eternal cross-version sense identity. `form_of`, `alt_of`, inflection tags and headword senses must remain distinguishable. Never turn dictionary file order into usage frequency.

The text's [Wikimedia licensing terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use#7._Licensing_of_Content) require appropriate attribution, license notice, and treatment of modifications and share-alike obligations. Retain Wiktionary entry/history attribution and credit the extraction source. Extractor MIT licensing does not replace dictionary text licensing. The [Wiktionary copyright page](https://en.wiktionary.org/wiki/Wiktionary:Copyrights) also documents external material with separate rights; copied quotations and linked audio need their own provenance. Research acquisition is not a project redistribution decision.

The [Kaikki language inventory](https://kaikki.org/dictionary/) lists all direct target languages except Croatian, which appears as Serbo-Croatian. Norwegian Bokmål is distinct from Nynorsk. Greek is distinct from Ancient Greek. Chinese and Mandarin have separate language entries. Preserve language distinctions rather than accepting a neighboring language code because the spelling matches.

## Per-language implementation choices

All rows use the shared lexical source above except the Croatian-specific supplement described below. The UD license is the release metadata, not a blanket declaration about third-party underlying text. Model names are explicit Stanza 1.10.0 packages; use the corresponding tokenize model and MWT package where listed in the JSON catalog. License and test links below were checked against official release files.

| Product language | Lexical scope | Annotated corpus / license | Stanza POS + lemma package |
| --- | --- | --- | --- |
| pt — Portuguese | Exact pt | [UD Portuguese-Bosque](https://raw.githubusercontent.com/UniversalDependencies/UD_Portuguese-Bosque/r2.16/README.md) / CC BY-SA 4.0 | `bosque_nocharlm` |
| es — Spanish | Exact es | [UD Spanish-AnCora](https://raw.githubusercontent.com/UniversalDependencies/UD_Spanish-AnCora/r2.16/README.md) / CC BY 4.0 | `combined_nocharlm` |
| en — English | Exact en | [UD English-EWT](https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/r2.16/README.md) / CC BY-SA 4.0 | `combined_nocharlm` |
| fr — French | Exact fr | [UD French-GSD](https://raw.githubusercontent.com/UniversalDependencies/UD_French-GSD/r2.16/README.md) / CC BY-SA 4.0 | `combined_nocharlm` |
| de — German | Exact de | [UD German-GSD](https://raw.githubusercontent.com/UniversalDependencies/UD_German-GSD/r2.16/README.md) / CC BY-SA 4.0 | `combined_nocharlm` |
| it — Italian | Exact it | [UD Italian-ISDT](https://raw.githubusercontent.com/UniversalDependencies/UD_Italian-ISDT/r2.16/README.md) / CC BY-NC-SA 3.0 | `combined_nocharlm` |
| pl — Polish | Exact pl | [UD Polish-PDB](https://raw.githubusercontent.com/UniversalDependencies/UD_Polish-PDB/r2.16/README.md) / CC BY-NC-SA 4.0 | `pdb_nocharlm` |
| tr — Turkish | Exact tr | [UD Turkish-IMST](https://raw.githubusercontent.com/UniversalDependencies/UD_Turkish-IMST/r2.16/README.md) / CC BY-NC-SA 4.0 | `imst_nocharlm` |
| ro — Romanian | Exact ro | [UD Romanian-RRT](https://raw.githubusercontent.com/UniversalDependencies/UD_Romanian-RRT/r2.16/README.md) / CC BY-SA 4.0 | `rrt_nocharlm` |
| ru — Russian | Exact ru | [UD Russian-SynTagRus](https://raw.githubusercontent.com/UniversalDependencies/UD_Russian-SynTagRus/r2.16/README.md) / CC BY-NC-SA 4.0 | `syntagrus_nocharlm` |
| nl — Dutch | Exact nl | [UD Dutch-Alpino](https://raw.githubusercontent.com/UniversalDependencies/UD_Dutch-Alpino/r2.16/README.txt) / CC BY-SA 4.0 | `alpino_nocharlm` |
| ko — Korean | Exact ko | [UD Korean-GSD](https://raw.githubusercontent.com/UniversalDependencies/UD_Korean-GSD/r2.16/README.md) / CC BY-SA 4.0 | Kiwi (runtime); Stanza GSD alternative |
| da — Danish | Exact da | [UD Danish-DDT](https://raw.githubusercontent.com/UniversalDependencies/UD_Danish-DDT/r2.16/README.md) / CC BY-SA 4.0 | `ddt_nocharlm` |
| nb — Norwegian Bokmål | Exact nb | [UD Norwegian-Bokmaal](https://raw.githubusercontent.com/UniversalDependencies/UD_Norwegian-Bokmaal/r2.16/README.md) / CC BY-SA 4.0 | `bokmaal_nocharlm` |
| sv — Swedish | Exact sv | [UD Swedish-Talbanken](https://raw.githubusercontent.com/UniversalDependencies/UD_Swedish-Talbanken/r2.16/README.md) / CC BY-SA 4.0 | `talbanken_nocharlm` |
| fi — Finnish | Exact fi | [UD Finnish-TDT](https://raw.githubusercontent.com/UniversalDependencies/UD_Finnish-TDT/r2.16/README.txt) / CC BY-SA 4.0 | `tdt_nocharlm` |
| hu — Hungarian | Exact hu | [UD Hungarian-Szeged](https://raw.githubusercontent.com/UniversalDependencies/UD_Hungarian-Szeged/r2.16/README.md) / CC BY-NC-SA 3.0 | `szeged_nocharlm` |
| cs — Czech | Exact cs | [UD Czech-PDT](https://raw.githubusercontent.com/UniversalDependencies/UD_Czech-PDT/r2.16/README.md) / CC BY-NC-SA 4.0 | `pdt_nocharlm` |
| hr — Croatian | Croatian OMW; sh only with Croatian evidence | [UD Croatian-SET](https://raw.githubusercontent.com/UniversalDependencies/UD_Croatian-SET/r2.16/README.md) / CC BY-SA 4.0 | `set_nocharlm` |
| el — Greek | Exact el | [UD Greek-GDT](https://raw.githubusercontent.com/UniversalDependencies/UD_Greek-GDT/r2.16/README.md) / CC BY-NC-SA 3.0 | `gdt_nocharlm` |
| ja — Japanese | Exact ja | [UD Japanese-GSD](https://raw.githubusercontent.com/UniversalDependencies/UD_Japanese-GSD/r2.16/README.md) / CC BY-SA 4.0 | Fugashi/UniDic (runtime); Stanza GSD alternative |
| zh — Chinese | Chinese zh; require Mandarin scope | [UD Chinese-GSDSimp](https://raw.githubusercontent.com/UniversalDependencies/UD_Chinese-GSDSimp/r2.16/README.md) / CC BY-SA 4.0 | `gsdsimp_nocharlm` |


The 22 UD directories were queried at `r2.16`, and all test-file URLs were verified by a bounded HTTP read. The exact train and test URLs are in the catalog. Train directories were listed rather than guessed: Russian SynTagRus has `train-a`, `train-b`, `train-c`; Czech's PDT repository redirects to PDTC and uses `cs_pdtc` with 12 training shards. Norwegian corpus filenames use `no_bokmaal` while both product and Stanza use `nb`. Dutch/Finnish README files are `.txt`.

### Croatian

Download [OMW Croatian TSV](https://raw.githubusercontent.com/omwn/omw-data/master/wns/hrv/wn-data-hrv.tab). The [source metadata](https://github.com/omwn/omw-data/blob/master/index.toml) and [license file](https://raw.githubusercontent.com/omwn/omw-data/master/wns/hrv/LICENSE) identify Croatian and CC BY 3.0. The downloaded 1,498,438 bytes have SHA-256 `640879334f5a801a39aff42e274db58c96c5621f53ec5c7e9c2beb1cd77c9f7c`: 47,890 lemma links, 23,115 synsets and 29,001 distinct lemmas. Every data row is `synset<TAB>hrv:lemma<TAB>lemma`; there are no gloss rows. This inventory includes automatic expansion and needs review. Credit its named Croatian contributors and OMW.

Join exact synset offsets/POS to [Princeton WordNet 3.0](https://wordnetcode.princeton.edu/3.0/WordNet-3.0.tar.gz), whose gzip endpoint returned HTTP 200. Retain the [Princeton license and copyright](https://wordnet.princeton.edu/license-and-commercial-use) with all copies. Read `dict/data.noun`, `data.verb`, `data.adj`, `data.adv`, retain the synset identifier and text after the gloss separator; do not join against another WordNet release's offsets. Native gloss evidence is English. Open-class WordNet coverage cannot supply every frequent function word. For the latter, shared Serbo-Croatian Wiktionary senses require an explicit Croatian lexical attestation/review; `sh` is never automatically mapped to `hr`.

### Japanese

Prefer [JMdict Japanese-English XML gzip](https://www.edrdg.org/pub/Nihongo/JMdict_e.gz) as an additional sense source. Its endpoint returned HTTP 200 with gzip bytes. The [official directory](https://www.edrdg.org/pub/Nihongo/00INDEX.html) also offers new-generation files; these require a separate schema adapter, so use the explicit legacy filename for the first importer. The [DTD documentation](https://www.edrdg.org/jmdict/jmdict_dtd_h.html) describes entry IDs, written/read forms, sense restrictions and POS inheritance. Retain `ent_seq`, sense position and snapshot, `keb`/`reb`, `stagk`/`stagr`, inherited `pos`, usage labels and English glosses. Priority markers support dictionary priority, not observed corpus frequency. Parse with bounded XML handling; resolve only the bundled known entity vocabulary, never remote external entities.

[EDRDG's license](https://www.edrdg.org/edrdg/licence.html) specifies CC BY-SA 4.0 for the Japanese/English components, documentation/source attribution and update conditions; translations into other languages have separate copyright holders. Use `JMdict_e` to avoid silently importing those components. Do not copy the optional example-sentence archive under assumed dictionary-wide rights.

Use [Fugashi](https://github.com/polm/fugashi) with [UniDic](https://github.com/polm/unidic-py) for native morphology. Fugashi is MIT; bundled MeCab uses BSD; the packaged modern UniDic uses BSD with its own notice. Full UniDic is about 770 MB installed; `unidic-lite` is an older smoke option, not an equivalent production model. Preserve surface, lemma, orthographic base, reading, conjugation and dictionary fingerprint separately. Dictionary lemma IDs are morphology identifiers, not JMdict semantic sense IDs.

### Mandarin Chinese

[CC-CEDICT's official download page](https://www.mdbg.net/chinese/dictionary?page=cc-cedict) offers UTF-8 gzip text with traditional/simplified forms, Pinyin and gloss segments under CC BY-SA 4.0. The exact published bulk endpoint is included in the catalog; dictionary-page automated scraping is prohibited. CC-CEDICT is a pronunciation/gloss supplement: it has no uniform structured POS or durable sense IDs. Preserve traditional and simplified spellings plus pronunciation; do not collapse homographs from spelling alone. Use Wiktextract sense/POS evidence plus explicit Mandarin scope for identity admission.

Stanza's `zh` alias resolves to `zh-hans`, with `gsdsimp` tokenizer/POS/lemma. The acquired and evaluated corpus is the separately pinned Chinese-GSDSimp r2.16 treebank, matching simplified script. Its SHA-256 is `573f59b799b499a920d2d5bdc0e3c1dbd7bcacf86bdece4334ecbd03e21b6150`. No gold text was silently converted. A tokenizer/POS tagger alone does not establish word senses.

### Korean

Use the existing Kiwi runtime for morphology, with its [LGPL-2.1-or-later library notice](https://github.com/bab2min/kiwipiepy/blob/main/LICENSE.txt) and separately recorded model artifact provenance. Stanza GSD provides an alternative contextual annotation comparison, not a drop-in Sejong/UPOS mapping.

Kaikki supplies downloadable Korean lexical candidates now. NIKL's [Korean Basic Dictionary API](https://krdict.korean.go.kr/kor/openApi/openApiInfo) is a more direct supplement when a registered key is available. Endpoints are `/api/search` and `/api/view`; response evidence includes `target_code`, homograph `sup_no`, POS and `sense_order` with definitions. Do not substitute the existing learner-list `nikl:<rank>` for these dictionary identifiers. API authentication and dictionary copyright terms are source-specific; no key or bulk API corpus was acquired in this task.

## Corpus use and evaluation

[CoNLL-U](https://universaldependencies.org/format.html) represents sentences with ten tab-separated fields, comment metadata, multiword-token ranges and empty-node IDs. Preserve FORM separately from LEMMA, UPOS, XPOS and FEATS. Multiword ranges are not extra lexical token observations; empty nodes are not literal input spans. Keep sentence IDs and source-document references. Test files provide real annotated evaluation inputs, but UD itself mixes manual annotation and automatic conversion—never describe all annotation layers as independently human-reviewed.

Count tokens by lemma/POS only where the corpus annotations justify the join. Without explicit sense annotation, keep the observation sense unresolved. UD counts are observed frequencies **within that sample**, not a balanced everyday-language ranking. Keep genre, document counts, token denominator and sample bounds. Hold out test sentences from rank estimation and generation training used in the same evaluation.

Seven selected corpora have NonCommercial terms: Italian ISDT, Polish PDB, Turkish IMST, Russian SynTagRus, Hungarian Szeged, Czech PDTC, Greek GDT. These are identified candidates, not automatic inputs for commercial redistribution. Other corpora still require their individual notices. [English EWT](https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/r2.16/README.md) and GSD README files distinguish annotation rights from underlying third-party text. Keep raw corpora local with explicit use disposition, and do not export corpus sentences merely because an annotation file declares CC BY-SA.

## Model acquisition

The [Stanza resource manifest 1.10.0](https://raw.githubusercontent.com/stanfordnlp/stanza-resources/main/resources_1.10.0.json) was downloaded and checked: all 22 profiles have tokenizer, POS and lemmatizer packages. All 22 individual Hugging Face model cards at tag `v1.10.0` declare Apache-2.0; their URLs are in the catalog. This is a pinned reproducible inventory, not a claim that 1.10.0 is the latest runtime. Exact package/model compatibility must be tested against the project's locked version.

Use explicit `*_nocharlm` POS/lemma packages to avoid unnecessary transformer/character-model downloads during bounded preparation, and fetch their declared pretrain dependencies. Where provided, include MWT. The [Stanza FAQ](https://stanfordnlp.github.io/stanza/faq.html) explains why MWT expansion is required before POS/lemma in those pipelines and how to disable automatic downloading during offline runtime. Resolve official URLs from the pinned manifest and preserve actual hashes. Model metadata MD5 is upstream integrity metadata; add SHA-256 in the acquired manifest. The catalog lists model dependencies instead of implying a lone `.pt` file is sufficient.

## Bounded acquisition evidence and remaining qualification

A real [English `hello` JSONL sample](https://kaikki.org/dictionary/English/meaning/h/he/hello.jsonl) was downloaded: 187,332 bytes, SHA-256 `28c6cae3df7a7044ec6fe1c84f0cf4401440d2362eafcf7468b86ddba5871d91`, three POS records and seven senses. None has a native `id`; this verifies the need for snapshot-local evidence locators. It is deprecated postprocessed data, suitable for ingestion smoke evidence only. The Croatian TSV above was also fully downloaded. Downloads were kept under `/tmp` during research; the catalog preserves their facts, and the execution task can copy/acquire them into its immutable quarantine.

No 2.7 GB raw dictionary dump, full UD training corpus or additional model weights were acquired by this research task. The exact train/test paths and source formats are now concrete, so implementation can proceed without another discovery pass. Full lexical coverage must be measured after parsing: accepted lemma/POS/sense identities, unresolved entries, non-headword forms, prohibited/obsolete registers and important-form candidates. Neither dictionary availability nor 3000 old rows proves a complete qualified Core. Independent linguistic review, sense-to-context adjudication, source-specific distribution decisions and real model evaluation remain separate evidence requirements; no approval was fabricated here.
