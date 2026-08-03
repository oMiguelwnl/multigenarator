# Plano mestre lexical e adaptativo multilíngue v4

> **ESTADO PRESERVADO — PROPOSTA v4, NÃO ATIVA.** O milestone ativo continua sendo o v3.0 de coreano, com as Fases 30–34 e sua política de conteúdo em português. Este documento não inicia a v4, não inicia a Fase 35 e não altera `.planning/SPEC.md`, `.planning/ROADMAP.md` nem `.planning/STATE.md`. Nenhuma fase v4 pode começar ou entrar no planejamento ativo antes da aprovação integral de G0 e de uma ação posterior, separada e explicitamente aprovada de promoção.

Este documento é o contrato mestre normativo preservado para uma futura evolução v4 do Multilang. Ele fixa resultados já aprovados e mantém escolhas externas ainda não comprovadas como gates bloqueantes. Fonte, licença, provider, privacidade, orçamento e limiares de qualidade somente serão aprovados por evidência nas etapas indicadas; sua menção aqui não constitui seleção, autorização de chamada, licença de redistribuição nem aprovação de release.

## 1. Estado, resultado, escopo e não objetivos

### Resultado para o usuário

A v4 deverá permitir que o usuário estude vocabulário de 22 idiomas modernos por identidades lexicais estáveis, formas importantes e conteúdo linguisticamente adequado, com áudio da forma exibida, fontes pessoais protegidas, histórico Anki importado somente para leitura e uma fila adaptativa explicável. A exportação continuará orientada ao Anki e usará subdecks reais. O Latim clássico continuará em um caminho isolado, sem ser forçado pelas suposições dos idiomas modernos.

### Fronteira com o milestone ativo

- A v3.0 de coreano é o único milestone ativo; suas Fases 30–34 continuam inalteradas.
- A política v3.0 de definições, glossas e traduções coreanas em português continua válida para todo conteúdo v3.0.
- A transição das explicações coreanas para inglês é uma migração de conteúdo da v4, com regeneração e revisão; não é uma simples troca de rótulo e não retroage sobre a v3.0.
- G0 é um gate futuro de prontidão e promoção. Ele não está satisfeito pela existência deste arquivo.
- A promoção exige evidência de G0 e uma decisão humana separada que autorize alterações futuras no planejamento ativo. Até lá, este documento é somente leitura para fins de orientação.
- Toda implementação, dado persistido, asset, exportação e comportamento atuais permanecem inalterados até a execução explicitamente aprovada da fase responsável.

### Escopo normativo

A proposta cobre:

1. o contrato de capacidade por idioma `LanguageProfile`;
2. a identidade lexical versionada por idioma, lema normalizado, POS e sentido;
3. um núcleo moderno congelado de exatamente 3000 identidades em três níveis, com exatamente 3000 cards headword padrão e uma contagem variável, intencionalmente maior, de cards de frequência quando houver formas importantes ou papéis opcionais habilitados;
4. formas de superfície, formas importantes obrigatórias quando justificadas/aprovadas, herança do destino da identidade-pai, definições específicas da forma e áudio do texto exato;
5. MWE, resolução de sentido, roteamento de fonte e papéis de card como conceitos distintos;
6. listas personalizadas e highlights sob gates por perfil e controles de privacidade;
7. integração somente de leitura de histórico APKG;
8. priorização adaptativa explicável sem alteração da ordem canônica nem do histórico importado;
9. exportação para subdecks Anki reais sob uma topologia de nota/card ainda não selecionada, sem um destino top-level separado para formas importantes;
10. ranking agregado reproduzível, políticas versionadas de formas/display/pronúncia, isolamento de entradas e saídas de IA, conteúdo Core canônico por edição e avaliação multilíngue estratificada;
11. migração in-place do Multilang com prévia, backup, confirmação, recuperação e auditoria;
12. G0 e todas as Fases 35–51, com dependências e gates de saída.

### Evolução in-place, não produto paralelo

A v4 é uma evolução in-place do Multilang. Ela deve preservar identidades válidas, dados do usuário, histórico de estudo mapeável, contratos de exportação compatíveis e assets aprovados. Não será criado um segundo produto, banco ou fluxo paralelo para contornar a migração. Isolamentos linguísticos necessários, especialmente o Latim clássico, são limites dentro do mesmo produto e não justificam duplicar a aplicação.

### Não objetivos

- Não promover a v4 durante a persistência deste documento.
- Não alterar numeração, estado, requisitos ou política das Fases 30–34.
- Não implementar modelos, schemas, migrations, registries, providers, filas, integração Anki, CLI, API, UI, testes, decks ou assets neste trabalho de documentação.
- Não escolher uma fonte lexical, licença de redistribuição, provider, orçamento ou limiar de qualidade sem a evidência exigida pelo gate correspondente.
- Não incorporar o Latim clássico ao pipeline moderno nem migrá-lo por suposições modernas.
- Não transformar formas, cards, exemplos, áudios ou grafias duplicadas em novas vagas do núcleo lexical.
- Não tratar `Core 3x1000` como teto de 3000 cards, tornar uma `Important Form` justificada de Core opt-in, desviá-la para expansão nem criar um subdeck top-level de formas.
- Não selecionar antecipadamente uma topologia Anki: a Fase 35 deve comparar os dois modelos candidatos em clientes reais e assinar a decisão antes de qualquer persistência v4.
- Não regenerar conteúdo Core compartilhado a partir do histórico individual nem promover output de LLM a fato lexical, morfológico, semântico, de rank ou de pronúncia.
- Não escrever em APKG, Anki, AnkiConnect ou coleção do usuário.
- Não substituir o scheduler do Anki; a fila adaptativa ordena preparação/estudo no Multilang e permanece separada do histórico original.

## 2. Matriz de idiomas e política de explicações

| Família | Código | Idioma | Idioma das explicações | Transição no v4 | Estado da capacidade |
|---|---|---|---|---|---|
| Moderno | pt | Português | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | es | Espanhol | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | en | Inglês | Português | Exceção preservada | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | fr | Francês | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | de | Alemão | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | it | Italiano | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | pl | Polonês | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | tr | Turco | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | ro | Romeno | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | ru | Russo | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | nl | Neerlandês | Inglês | Nova política moderna | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | ko | Coreano | Inglês | Regenerar conteúdo v3 em português e revisar | Planejado; v3 permanece em português até migração aprovada |
| Moderno | da | Dinamarquês | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | nb | Norueguês Bokmål | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | sv | Sueco | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | fi | Finlandês | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | hu | Húngaro | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | cs | Tcheco | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | hr | Croata | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | el | Grego moderno | Inglês | Nova capacidade | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | ja | Japonês | Inglês | Alinhar capacidade existente à política v4 | Planejado; bloqueado até `LanguageProfile` aprovado |
| Moderno | zh | Mandarim | Inglês | Alinhar capacidade existente à política v4 | Planejado; bloqueado até `LanguageProfile` aprovado |
| Latim isolado | la | Latim | Português | Permanecer no caminho clássico isolado | Isolado; fora do núcleo e da migração moderna |

Rótulos normativos pesquisáveis:

- **Política dos idiomas modernos: explicações em inglês**
- **Exceção do idioma-alvo inglês: explicações em português**
- **Migração coreana no v4: português -> inglês**
- **Isolamento do Latim: explicações em português**

O idioma das explicações controla definições, explicações gramaticais e de formas, traduções de exemplos, mensagens de revisão e critérios linguísticos apresentados ao usuário. Ele não altera o idioma-alvo do lema, da forma exibida nem da frase de exemplo. Metadados internos podem manter identificadores técnicos canônicos, mas não podem vazar um idioma de explicação diferente para o conteúdo de estudo.

### 2.1 Requisitos linguísticos individuais

Esta matriz é obrigatória por código. Um adapter genérico só pode ser usado quando os casos dourados do idioma provarem seu comportamento; sem essa prova, a capacidade permanece desabilitada. Locales de provider são candidatos sujeitos aos gates de fonte, voz, custo e qualidade, e nunca substituem o código canônico.

| Código | Variante e locale | Normalização e escrita | Tokenização/segmentação | Lema, POS e sentido | Morfologia e formas | MWE e palavras funcionais | Matching do alvo | Pronúncia e áudio | Casos dourados obrigatórios |
|---|---|---|---|---|---|---|---|---|---|
| pt | Português versionado por variante; `pt-BR`/`pt-PT` somente quando declarados; locale de provider qualificado | Unicode NFC; diacríticos preservados | Contrações, hífen e clíticos sem split ingênuo | Lema, POS, regência e sentidos homógrafos separados | Gênero, número, pessoa, tempo, modo e formas irregulares | Contrações e locuções mantidas; artigos/preposições roteados por papel | Forma flexionada deve resolver ao lema/sentido no contexto | Variante e forma falada exatas; sem misturar pronúncias regionais | `ser/estar`, `por/pôr`, clíticos, subjuntivo, contrações e MWE |
| es | Espanhol com variante declarada; locale de provider não é identidade | NFC; `ñ` e acentos preservados | Enclíticos, contrações e pontuação invertida | Lema/POS/sentido distingue homógrafos e usos regionais | Pessoa, número, tempo, modo, gênero e irregularidade | `al`/`del`, perífrases e locuções têm rota explícita | Enclítico e flexão exigem análise; substring não basta | Variante, seseo/yeísmo e forma exata registrados quando relevantes | `ser/estar`, pretéritos, subjuntivo, enclíticos, `si/sí` e locuções |
| en | Inglês-alvo; explicações em português; locale/variante declarados | NFC; caixa preservada como evidência, não identidade automática | Contrações, possessivos, hífens e phrasal verbs | Lema/POS/sentido separa homógrafos; `be` é a identidade lexical | Número, pessoa, tempo, aspecto, modo e irregularidade | Phrasal verbs são MWE; auxiliares e function words recebem rota própria | Formas irregulares exigem análise contextual | Variante e forma exata; redução não substitui o texto exibido | `be/is/was/were`, substantivo/verbo homógrafo, phrasal verb, contração e irrealis |
| fr | Francês com variante declarada; locale de provider qualificado | NFC; acentos, cedilha, apóstrofo e hífen preservados | Elisão, clíticos, compostos e liaison gráfica tratados | Lema/POS/sentido e gênero lexical persistidos | Gênero, número, pessoa, tempo, modo e particípio | Locuções e clíticos não inflam o Core | Matching considera elisão/flexão sem aceitar substring | Liaison/elision e forma exata orientam áudio revisado | `être/avoir`, elisão, homógrafo, particípio, subjuntivo e locução |
| de | Alemão padrão com variante declarada; locale de provider qualificado | NFC; **capitalização de substantivos alemães é preservada**; `ä/ö/ü/ß` não são descartados | Compostos e verbos separáveis exigem segmentação linguística | Lema/POS/sentido preserva caixa lexical e composição | Caso, gênero, número, pessoa, tempo, modo, grau e ablaut | Compostos/MWE e partículas separáveis têm identidade/rota explícita | Partes separadas do verbo só casam com análise comprovada | Forma exata, vogais/umlauts e variante qualificada | substantivo capitalizado, composto, verbo separável, caso, ablaut e `das/dass` |
| it | Italiano com variante declarada; locale de provider qualificado | NFC; acentos e apóstrofos preservados | Elisão, artigos articulados e clíticos segmentados | Lema/POS/sentido e gênero lexical separados | Gênero, número, pessoa, tempo, modo e participialidade | Locuções e preposições articuladas são roteadas sem criar ranks falsos | Clíticos/flexões exigem contexto morfológico | Geminação e forma exata entram na revisão de voz | `essere/avere`, elisão, clítico, subjuntivo, particípio e locução |
| pl | Polonês padrão; locale de provider qualificado | NFC; `ą/ć/ę/ł/ń/ó/ś/ź/ż` preservados | Tokenização sensível a clíticos e locuções | Lema/POS/sentido separa aspecto e homógrafos | Caso, gênero, número, pessoa, aspecto, animacidade e flexão irregular | Preposições regem caso; locuções/MWE mantêm rota | Forma declinada/conjugada exige features compatíveis | Consoantes, acento e forma exata passam por revisão | paradigmas de caso, aspecto, animacidade, numeral, homógrafo e MWE |
| tr | Turco padrão; locale de provider qualificado | NFC; regras locale-aware para `i/İ/ı/I` | Cadeias de sufixos são analisadas, não cortadas | Lema/POS/sentido separa derivação de flexão | Harmonia, caso, posse, pessoa, tempo, aspecto, modo e evidencialidade | Pós-posições, auxiliares e MWE recebem rota explícita | Assinatura morfológica completa; sufixo textual não prova identidade | Harmonia e forma aglutinada exata orientam síntese | `i/İ/ı/I`, cadeia de casos/posse, negação, evidencial, derivação e MWE |
| ro | Romeno padrão; locale de provider qualificado | NFC; **diacríticos com vírgula `ș/ț`**, nunca normalização silenciosa para cedilha `ş/ţ` | Artigo enclítico e clíticos segmentados | Lema/POS/sentido e gênero persistidos | Caso, gênero, número, definitude, pessoa, tempo e modo | Locuções, clíticos e palavras funcionais têm rota | Forma com artigo enclítico deve mapear por análise | Diacrítico/forma exata e variante orientam áudio | `ș/ț` versus `ş/ţ`, artigo enclítico, caso, subjuntivo e clítico |
| ru | Russo padrão; locale de provider qualificado | NFC cirílico; **`е/ё` não são colapsados silenciosamente**; acento lexical é metadado versionado | Hífen, clíticos e MWE segmentados com script validado | Lema/POS/sentido separa homógrafos e pares aspectuais | Caso, gênero, número, animacidade, pessoa, tempo, aspecto e reflexividade | Preposições regem caso; partículas e MWE têm rota | Matching considera `е/ё`, stress, aspecto e features; falha fechado | **stress e aspecto** acompanham a forma; áudio exato não usa lema divergente | `е/ё`, posição de acento, pares aspectuais, caso/animacidade, reflexivo e homógrafo |
| nl | Neerlandês padrão; locale de provider qualificado | NFC; caixa e diacríticos preservados | Compostos, partículas e verbos separáveis | Lema/POS/sentido distingue composição e homógrafos | Número, grau, pessoa, tempo, particípio e diminutivo | Compostos/MWE e partículas separáveis têm rota | Partes deslocadas exigem análise sintática/morfológica | Variante e forma exata; vogais compostas revisadas | composto, verbo separável, diminutivo, particípio, gênero comum/neutro e MWE |
| ko | Coreano padrão de Seul; código `ko`, locale de provider `ko-KR` | **NFC Hangul obrigatório**; NFD equivalente no input; compatibility/halfwidth não entram como canônico | **Kiwi** versionado segmenta eojeol em morfemas | Lema/POS/sentido preserva predicados simples/compostos | Partículas, endings, tempo, aspecto, modo, honorífico, fala e irregularidade | Morfemas funcionais vão para Grammar; MWE preserva composição | **matching por assinatura de morfemas**, nunca espaço/substring/sufixo | Pronúncia normativa/superficial e áudio exato; jamo/regra exige revisão | NFC/NFD, `먹다/먹었어요`, partículas, irregular, `공부하다`, homógrafo e MWE |
| da | Dinamarquês padrão; locale de provider qualificado | NFC; `æ/ø/å` preservados | Compostos e partículas segmentados | Lema/POS/sentido e definitude lexical | Número, definitude, grau, pessoa, tempo e particípio | Compostos, verbos frasais e palavras funcionais roteados | Forma definida/flexionada exige análise | **stød** e redução são evidência de áudio, não inferência ortográfica | stød contrastivo, composto, definitude sufixal, verbo forte e MWE |
| nb | **Identidade canônica Bokmål `nb`, nunca `no` genérico**; locale qualificado | NFC; `æ/ø/å` preservados | Compostos e partículas segmentados | Lema/POS/sentido específico de Bokmål | Gênero, número, definitude, grau, pessoa e tempo | Compostos/MWE e function words roteados | Variação permitida é versionada; não mistura Nynorsk | Pitch accent e variante de voz requerem evidência | `nb` versus `no/nn`, definitude, gênero variável, composto e pitch accent |
| sv | Sueco padrão; locale de provider qualificado | NFC; `å/ä/ö` preservados | Compostos e partículas segmentados | Lema/POS/sentido e acento lexical | Gênero, número, definitude, grau, pessoa e tempo | Compostos/MWE e verbos com partícula mantêm rota | Flexão/partícula exige análise | Pitch accent e forma exata passam por qualificação | pitch accent, definitude dupla, composto, partícula e verbo forte |
| fi | Finlandês padrão; locale de provider qualificado | NFC; `ä/ö` e quantidade preservadas | Cadeias de morfemas e compostos analisados | Lema/POS/sentido separa derivação e flexão | Casos, posse, pessoa, tempo, modo, **gradação consonantal** e harmonia | Clíticos, pós-posições e MWE têm rota | Stem alternante exige análise completa | Quantidade, harmonia e forma aglutinada exata | gradação, harmonia, casos locativos, posse, clítico e derivação |
| hu | Húngaro padrão; locale de provider qualificado | NFC; vogais longas/duplas preservadas | Cadeias de sufixos e compostos analisados | Lema/POS/sentido separa derivação e flexão | Harmonia, casos, posse, pessoa, tempo, modo e conjugação definida/indefinida | Preverbos, pós-posições e MWE são roteados | Preverbo deslocado e sufixos exigem análise | Comprimento vocálico e forma exata são obrigatórios | harmonia, caso, posse, conjugação definida, preverbo deslocado e MWE |
| cs | Tcheco padrão; locale de provider qualificado | NFC; diacríticos preservados | Clíticos de segunda posição e MWE segmentados | Lema/POS/sentido separa aspecto/homógrafos | Caso, gênero, número, animacidade, pessoa, aspecto e reflexividade | Preposições, clíticos e MWE têm rota | Ordem de clítico não substitui análise | Comprimento/acento e forma exata revisados | caso/animacidade, aspecto, reflexivo, clítico, numeral e homógrafo |
| hr | **Identidade específica croata `hr`, nunca fallback final `sh`**; variante croata declarada | NFC latino; diacríticos e reflexo ijekaviano preservados | Clíticos e MWE segmentados segundo croata | Lema/POS/sentido não é fundido em identidade servo-croata genérica | Caso, gênero, número, animacidade, pessoa, aspecto e reflexividade | Clíticos, preposições e MWE têm rota croata | Flexão e clíticos exigem analyzer/perfil croata | Acento/quantidade e forma croata exata exigem evidência | `hr` versus `sh`, ijekaviano, caso, aspecto, clíticos e homógrafo |
| el | Grego moderno; locale de provider qualificado | NFC; monotônico, tonos/dialytika e sigma final preservados | Clíticos e MWE segmentados em script grego | Lema/POS/sentido separa homógrafos e variantes de stem | Caso, gênero, número, pessoa, tempo, aspecto, modo e voz | Clíticos, partículas e MWE têm rota | Acento, sigma e flexão entram na assinatura | Stress e forma grega exata são obrigatórios | tonos, sigma `σ/ς`, aspecto, voz, clítico, caso e homógrafo |
| ja | Japonês padrão; código `ja`, locale qualificado como `ja-JP` quando aprovado | NFC; Kanji, Hiragana e Katakana preservados; normalização não destrói variante | Segmentação por **UniDic**/adapter versionado, não por espaço | **lema, POS e leitura UniDic** integram a evidência de identidade/sentido | Forma flexionada, politeness, tempo/aspecto, voz e leitura | Partículas/auxiliares vão a Grammar; MWE e compostos preservados | Lema/POS/leitura e contexto resolvem alvo; substring de Kanji falha | Leitura, pitch quando disponível e texto exato controlam áudio | lema/orthBase/reading UniDic, homógrafo heterófono, conjugação, partícula e MWE |
| zh | Mandarim padrão; código `zh`; perfil de script/locale explícito | NFC; **Simplificado/Tradicional** preservados e ligados por mapping versionado, nunca colapso cego | **segmentação lexical chinesa** versionada, sem whitespace | Lema lexical, POS, sentido e leitura; caracteres iguais podem ter sentidos distintos | Aspecto, classificadores, reduplicação e variantes de script | Chengyu/MWE, classificadores e partículas funcionais têm rota | Segmento, sentido e contexto resolvem alvo | **polifonia** exige leitura contextual; Pinyin é evidência, não identidade | fronteira de palavra, Simplificado/Tradicional, polifonia, classificador, aspecto e chengyu |
| la | **Latim clássico isolado**; `la`; explicações em português; nenhuma locale moderna presumida | NFC; política de macrons/`u-v`/`i-j` versionada e não destrutiva | Enclíticos e locuções latinas segmentados no caminho isolado | Lema/POS/sentido e principal parts seguem fonte clássica aprovada | Caso, gênero, número, pessoa, tempo, modo, voz, grau e formas principais | Enclíticos, preposições e MWE permanecem no domínio latino | Forma flexionada casa por morfologia clássica e citação | Pronúncia clássica/provider exigem gate próprio; áudio exato | declinações, conjugações, deponentes, irregulares, enclítico e locução clássica |

Os casos dourados acima são conjuntos mínimos de fenômenos, não aprovações de analyzer. A Fase 38 transforma cada linha em fixtures positivas e negativas, com no mínimo 120 casos por idioma e 200 para idiomas CJK ou aglutinativos, sem reduzir a revisão exigida por risco.

## 3. Modelo de domínio normativo e invariantes

### 3.1 `LanguageProfile` como contrato de capacidade

Cada idioma tem exatamente um `LanguageProfile` versionado. O perfil é a autoridade fail-closed que conecta identidade, linguística, fontes, conteúdo, áudio, privacidade e capacidades. A existência de um código no registry não implica que todas as capacidades estejam habilitadas.

Campos e responsabilidades mínimas:

| Grupo | Contrato obrigatório |
|---|---|
| Identidade | código canônico, nomes públicos, família moderna ou Latim isolado e versão do perfil |
| Locales | locales por provider para conteúdo, tradução e áudio; um locale nunca cria outra identidade de idioma |
| Escrita | scripts aceitos, variantes, política de texto misto e normalização, incluindo NFC onde exigido |
| Segmentação | tokenizer, segmentador, regras de MWE e versões fixadas |
| Morfologia | adapter, versão, tagset, mapeamento POS, regras de lema e política de indisponibilidade |
| Sentido | fontes autorizadas, versionamento de sense IDs, homógrafos e critérios de desambiguação |
| Matching | assinatura do alvo, correspondência de forma exata, limiar de confiança e quarentena de ambiguidade |
| Explicação | idioma de explicações, traduções e revisão segundo a matriz normativa |
| Fontes | registry lexical, frequência, exemplos, tradução e áudio, com licença, atribuição e checksums |
| Áudio | locale, política de voz, providers permitidos, fallback, revisão e limites de custo |
| Qualidade | regras de morphology, sentido, naturalidade, target matching, tradução, áudio e exportação |
| Privacidade | classe dos dados, minimização, retenção, autorização de provider, exclusão e exportação |
| Topologia Anki | estado da decisão, versão selecionada quando houver, matriz de clientes suportados, identidade de nota/card, aliases, update, scheduling e política de pré-requisitos/burying ou alternativa honesta |
| Ranking | manifests de corpus, pesos, alocação lema/POS/sentido, dispersão, regra de MWE, fórmula, precisões, thresholds, analyzers e versão `RANK-01` |
| Formas importantes | `ImportantFormPolicy` por idioma, evidência, pesos, thresholds, deduplicação, ordenação, forecast integral e versão `FORM-04` |
| Display de forma | schema/prompt/resposta do card de forma, cues de análise/sentido, política de render e versão `DISPLAY-01` |
| Identidade de pronúncia | política e versão da `pronunciation_signature`, contexto fonológico/morfológico, provider/modelo e integridade de asset conforme `AUDIO-02` |
| Segurança de IA | trust classes, delimitação tipada, limites de bytes/caracteres/tokens/registros, contexto autorizado, schema de output, escaping/allowlist, budgets e auditoria `AISEC-01` |
| Conteúdo Core | `deck_edition_id`, bundle canônico assinado, versões/diffs/review, namespace privado de Custom/Highlight e limite adaptativo `CONTENT-01` |
| Avaliação | datasets de referência por idioma/estrato, métricas, rubricas, thresholds derivados de evidência, tolerância de drift, reviewers e bloqueios `EVAL-01` |
| Capacidades | flags explícitas para Core, expansão, listas personalizadas, highlights, mapeamento de histórico APKG e comportamento adaptativo, além dos oito grupos anteriores |

Cada capacidade e cada grupo de política acima possui estado `disabled`, `evidence_pending` ou `enabled` e referencia a evidência que autoriza o estado. Campo, versão, evidência ou capability ausente falha fechado; uma operação solicitada para capacidade não habilitada deve ser recusada com motivo acionável e nunca cair silenciosamente em heurística genérica. O perfil do Latim declara explicitamente seu isolamento e não herda flags modernas por padrão.

Para coreano, o perfil mantém `ko` como código canônico, `ko-KR` somente como locale de provider, normalização NFC e matching morfológico fail-closed. Para qualquer idioma, normalização destrutiva, tokenização por espaço ou remoção ingênua de sufixo não substituem um adapter exigido pelo perfil.

### 3.2 Identidade lexical estável e versionada

A chave conceitual normativa é **`language + normalized lemma + POS + sense`**. Uma função versionada e determinística produz um `lexical_identity_id` estável a partir dessa tupla e da versão do namespace. O ID não é uma grafia, uma linha de fonte, um card, um rank nem um hash de conteúdo mutável.

Invariantes:

- Homógrafos com POS diferentes são identidades distintas.
- Sentidos pedagogicamente distintos do mesmo lema e POS mantêm `sense` e IDs distintos.
- Mudanças de rótulo ou conteúdo não trocam o ID; uma correção que realmente muda a identidade cria mapeamento versionado, nunca sobrescrita silenciosa.
- Aliases, grafias históricas, variantes ortográficas e identificadores de fonte apontam para a identidade com proveniência.
- MWE é uma identidade lexical de primeira classe quando a unidade tem sentido/uso próprio; não é quebrada ou fundida somente por espaços.
- A análise inconclusiva gera quarentena. Ambiguidade nunca escolhe automaticamente o primeiro lema ou sentido.
- Referências persistidas registram versão do perfil, normalizador, analisador, fonte e regra de identidade para permitir rerun e migração.

### 3.3 Inventários modernos

#### `Core 3x1000`

Cada um dos 22 idiomas modernos possui exatamente 3000 identidades lexicais únicas aprovadas e ordenadas e, por `CARD-01`, exatamente 3000 cards headword de reconhecimento padrão. `Core 3x1000` fixa identidades e ranks; nunca é teto para a quantidade de cards de frequência:

- Nível 1: 1000 identidades, ranks 1–1000;
- Nível 2: 1000 identidades, ranks 1001–2000;
- Nível 3: 1000 identidades, ranks 2001–3000.

O rank pertence à versão congelada da identidade lexical no núcleo. Não pertence a um card nem a uma forma. Uma identidade pode produzir mais de um card pedagógico sem aumentar a contagem de identidades, mas cada card produzido aumenta a contagem de cards e o workload correspondente. Identidade sem sentido resolvido, duplicata de identidade, forma flexionada redundante, exemplo, áudio ou card não pode preencher uma vaga. Nenhum cap, amostragem, configuração de edição ou decisão de expansão pode descartar uma `Important Form` de Core justificada/aprovada para manter a exportação em 3000 cards.

#### `Optional expansion 0-3000`

A expansão opcional contém somente identidades lexicais adicionais além do Core: de zero a 3000 identidades aprovadas por idioma, sempre depois do núcleo e em namespace, versão, proveniência e destino próprios. A quantidade é opt-in e configurável dentro desse intervalo; não há padding. Habilitar, desabilitar ou regenerar a expansão não renumera, substitui nem altera o pertencimento das 3000 identidades do núcleo. `Important Forms` nunca são `Optional Expansion`, não consomem vagas de expansão e não podem ser usadas para esconder, adiar ou rotear formas obrigatórias de Core.

Uma forma herda o inventário e o destino de sua identidade-pai. Assim, uma forma de identidade de expansão fica colocada com o pai em Expansion, sem se tornar nem consumir uma identidade de expansão; o mesmo princípio vale para pais de Custom, Highlight, Grammar/foundation ou qualquer outro inventário aprovado. O opt-in de Expansion governa as identidades adicionais e, quando uma identidade de expansão está habilitada, suas formas justificadas/aprovadas não formam uma segunda classe de opt-in.

O Latim clássico não recebe automaticamente `Core 3x1000` nem `Optional expansion 0-3000`; sua escala e evolução continuam governadas pelo caminho isolado e por aprovações próprias.

### 3.4 Formas, definições e áudio

`SurfaceForms` liga uma identidade às realizações observadas ou geradas, com texto normalizado e exibido, features morfológicas, proveniência, confiança, adapter e versão. Uma forma submetida pelo usuário permanece preservada mesmo quando mapeada a um lema.

`Important Forms` é o subconjunto pedagogicamente justificado de `SurfaceForms`. Uma forma somente pode entrar nesse conjunto por pelo menos um destes motivos registrados: irregularidade, frequência própria comprovada, imprevisibilidade a partir do lema, ambiguidade, pronúncia inesperada, valor de pré-requisito ou dificuldade inferida a partir do lema e da evidência de aprendizagem. Conveniência de geração, mera existência no paradigma e desejo de aumentar o deck não são critérios válidos. Uma forma importante nunca vira nova identidade somente para ganhar um card.

Toda `Important Form` justificada/aprovada de uma identidade de Core produz um card adicional obrigatório: ela não é opt-in por aumentar a carga, não pode ser truncada e fica no mesmo nível, mesmo subdeck real e mesmo deck ID do lema, elegível somente depois dele por `DEPEND-01`. `Important Form` é papel de card descendente, não inventário de fonte; portanto nunca substitui o destino herdado do pai. Não existe subdeck top-level de `Important Forms`.

`Definitions` possui dois escopos relacionados e distintos:

1. definição da identidade e do sentido;
2. definição específica da forma exibida, ligada ao `surface_form_id`, que explica os atributos aplicáveis sem substituir o sentido lexical.

O bundle canônico de features admite, quando aplicável ao idioma e à forma, os identificadores técnicos `tense`, `mood`, `person`, `number`, `case`, `gender`, `aspect` e `register`. Campos não aplicáveis são explicitamente ausentes, não inventados. A definição específica da forma deve explicar somente análise comprovada pelo adapter e pela evidência; análise ambígua fica em quarentena.

`Exact-form audio` exige que o texto sintetizado ou resolvido seja exatamente a forma exibida no card, após a normalização declarada. Se o card mostra uma forma diferente do lema, áudio do lema não pode substituí-la. O asset registra texto exibido, texto falado, hash, idioma, locale, voz, provider, versão, SSML quando houver, licença, custo, status de revisão e hash do arquivo. Áudio da frase usa o texto exato do exemplo aprovado sob o mesmo princípio.

`SurfaceForms`, `Important Forms`, seus `Definitions`, cards de forma e assets de `Exact-form audio` ficam fora da quota de 3000 identidades, mas todos os cards exportados ficam dentro das contagens de cards e workload. O mesmo vale para exemplos, traduções, cards adicionais, mídia e grafias duplicadas: não ocupam identidade, embora qualquer card adicional conte como card.

### 3.5 Contratos normativos de card, forma, sentido, carga e GUID

As fórmulas normativas pesquisáveis para o inventário de frequência de Core são:

```text
core_identity_count = 3000
frequency_card_count = 3000 + N_important_form_cards + O_enabled_optional_role_cards
N_important_form_cards > 0 => frequency_card_count > 3000
frequency_level_card_count = 1000 + N_level_important_form_cards + O_level_enabled_optional_role_cards
```

Definições e reconciliação obrigatórias:

- `core_identity_count` conta as 3000 identidades de Core, exatamente 1000 em cada nível real; não conta cards nem formas.
- O termo fixo `3000` em `frequency_card_count` conta os 3000 cards headword de reconhecimento padrão, um para cada identidade de Core.
- `N_important_form_cards` conta **todos** os cards de `Important Forms` justificados/aprovados e exportados para identidades de Core, inclusive cards distintos da mesma grafia quando possuem análises distintas. Essas formas são adicionais e obrigatórias; não fazem parte de `O`.
- `O_enabled_optional_role_cards` conta somente cards de papéis opcionais, como reverse, listening ou cloze, explicitamente habilitados para o inventário de frequência. `O_enabled_optional_role_cards = 0` por padrão e permanece zero sem essa configuração explícita.
- Para cada Nível 1, 2 ou 3, `N_level_important_form_cards` e `O_level_enabled_optional_role_cards` contam somente descendentes das 1000 identidades daquele nível. A soma dos três `frequency_level_card_count` deve ser igual a `frequency_card_count`; as somas dos três componentes `N_level` e `O_level` devem ser iguais a `N_important_form_cards` e `O_enabled_optional_role_cards`, respectivamente.
- Os destinos reais são `{language}::Frequency::Level 1`, `{language}::Frequency::Level 2` e `{language}::Frequency::Level 3`. O rank da identidade-pai escolhe exatamente um deles antes da avaliação do papel; todo card de forma de Core preserva esse mesmo deck ID.

Contagens de Expansion, Custom, Highlight, Grammar/foundation e outros inventários não entram em `frequency_card_count`: são reportadas separadamente por identidade, headword padrão, forma e papel opcional. Uma forma sempre entra no total de cards/workload do inventário herdado do pai sem consumir uma vaga de identidade nesse inventário.

| ID | Contrato obrigatório |
|---|---|
| `CARD-01` | Cada identidade lexical aprovada produz, por padrão, exatamente um card headword de reconhecimento. O Core tem, portanto, 3000 identidades e 3000 cards headword padrão, sem impor teto ao total de frequência. Cards reversos, de listening e cloze são opcionais, têm papéis próprios e ficam **desabilitados por padrão**; habilitá-los exige configuração explícita, evidência de qualidade e relatório de carga. |
| `FORM-01` | Toda `SurfaceForm` referencia uma identidade-pai, análise morfológica versionada, texto exato, proveniência e confiança. Formas e seus cards ficam fora das 3000 vagas do Core e de qualquer quota de inventário, mas cada card entra na contagem e no workload do destino herdado do pai. |
| `FORM-02` | Uma `Important Form` só é selecionada por irregularidade, frequência, imprevisibilidade, ambiguidade, pronúncia inesperada, valor de pré-requisito ou dificuldade inferida do lema; a razão e a evidência são obrigatórias e alimentam a decisão reproduzível de `FORM-04`. |
| `FORM-03` | O card de forma referencia `surface_form_id` e `morphological_analysis_id`, mostra a forma analisada conforme `DISPLAY-01`, recebe `Definitions` e áudio dessa forma exata e não duplica a identidade lexical. Se o pai é Core, toda forma justificada/aprovada é card adicional obrigatório no mesmo subdeck real/deck ID do lema; para qualquer outro pai, o card preserva o destino do inventário de origem. |
| `SENSE-01` | Identidade e conteúdo são sense-aware; homógrafo, POS ou sentido inconclusivo fica em quarentena, sem escolher a primeira acepção nem compartilhar GUID indevidamente. |
| `MWE-01` | MWE com unidade lexical própria mantém identidade, segmentação, variantes, sentido e rota próprios; não é quebrada por espaço nem inflada por cada token. |
| `ROUTE-01` | A decisão determinística resolve `source type -> parent identity/sense -> parent inventory destination -> Core rank/real level when applicable -> content route -> card role -> inherited real subdeck/deck ID -> prerequisite sequence`. O papel `Important Form` nunca sobrepõe o destino do pai; rota não suportada ou ambígua falha fechado. |
| `DEF-01` | `Definitions` são concisas e meaning-first: começam pelo significado relevante e acrescentam gramática contextual da identidade ou da forma, sem despejo de paradigma nem metadado morfológico como falsa definição. |
| `AUDIO-01` | O áudio de palavra usa a forma exatamente exibida e o áudio de sentença usa a sentença exatamente aprovada; hashes, locale, voz, provider, custo, licença e revisão são vinculados ao texto e à identidade completa de pronúncia de `AUDIO-02`. |
| `LOAD-01` | Cada idioma publica, para Core: `core_identity_count`, 3000 cards headword padrão, `N_important_form_cards`, cada papel opcional habilitado, `frequency_card_count` computado e reconciliação dos mesmos componentes nos Níveis 1/2/3. Expansion reporta separadamente identidades, headwords, formas, papéis opcionais e total; Custom, Highlight e demais fontes também não são fundidos ao total de Core. |
| `DEPEND-01` | Card de forma só fica elegível depois do card do lema ou do pré-requisito explicitamente aprovado. Para Core, lema e formas compartilham o deck ID do nível real e o lema precede cada forma. Burying nativo só pode ser prometido se `ANKI-01` selecionar e comprovar cards da mesma nota; se selecionar notas separadas, a política deve nomear e testar uma alternativa honesta de pré-requisito e não exposição concorrente, sem chamá-las de siblings. |
| `GUID-01` | A identidade futura deriva de inputs semânticos versionados: identidade lexical + papel do card + análise da forma quando aplicável, reconciliada com a distinção entre note GUID e card identity/template ordinal decidida em `ANKI-01`. Rank, job, texto de definição, sentença, provider, ordem de geração e timestamp não podem alterar a identidade semântica; o baseline atual divergente exige alias/migração provados. |
| `ANKI-01` | A topologia permanece não selecionada até a Fase 35 comparar, em clientes reais suportados, **Modelo A — uma nota lexical por família com cards de headword/formas** e **Modelo B — notas separadas ligadas por metadados semânticos de família**. A decisão assinada deve provar identidade de nota/card, import/reimport/update/alias, scheduling, pré-requisitos, burying nativo ou alternativa honesta, formas dinâmicas, colisões e round-trip; nenhuma persistência v4 pode precedê-la. |
| `RANK-01` | O rank lexical é uma agregação determinística e versionada de corpora checksummed, pesos, observações de formas, alocações com confiança, dispersão e regras de MWE. Entradas/versões iguais reproduzem ranks e hash do manifest; drift cria nova versão, diff integral e reaprovação. |
| `FORM-04` | Cada idioma possui `ImportantFormPolicy` versionada com score, thresholds de atestação/análise, deduplicação, exceção de mesma grafia com análises distintas, ordem de pré-requisitos, forecast integral e evidência de aprovação. Forma aprovada é obrigatória e jamais sofre truncamento posterior por top-N, custo, edição ou teto de cards. |
| `DISPLAY-01` | Cada card de forma possui identidade estruturada, prompt não ambíguo e resposta que expõe lema-pai, papel, análise, sentido/contexto e áudio exato. Grafias iguais com análises distintas mantêm IDs, cards e cues distintos; a grafia isolada não basta como frente. |
| `AUDIO-02` | Reuso de áudio exige igualdade da tupla versionada `pronunciation_signature` completa e integridade do artefato. A assinatura inclui contexto linguístico, locale, voz, SSML/prosódia, políticas e provider/modelo; hash apenas do texto é proibido para heterófonos ou polifonia. |
| `AISEC-01` | Custom, Highlight, corpus e toda saída de LLM são dados não confiáveis. Controles e conteúdo ficam separados; limites precedem providers; contexto é mínimo e autorizado; outputs usam schemas fechados, grounding, escaping/allowlist e rejeição de conteúdo ativo; budgets e auditoria hash-only são obrigatórios, e LLM nunca é autoridade lexical. |
| `CONTENT-01` | Cada `deck_edition_id` assina um bundle Core canônico e versionado de definições, exemplos, traduções, assinaturas/áudio, render policy e review. Histórico individual só altera queue/module/order/eligibility; correções criam nova edição/diff/review, e namespaces privados nunca sobrescrevem Core compartilhado. |
| `EVAL-01` | Cada idioma possui datasets de referência checksummed por dimensão e estrato de risco, métricas/rubricas definidas, thresholds derivados de evidência, tolerância de drift e bloqueio de regressão. Validators determinísticos e revisão especialista independente decidem; LLM judge é somente sinal secundário. |

#### Decisão bloqueante de topologia Anki — `ANKI-01`

A Fase 35 deve construir e comparar, sem selecionar antecipadamente nenhum deles:

- **Modelo A — uma nota lexical por família com cards de headword/formas**;
- **Modelo B — notas separadas ligadas por metadados semânticos de família**.

Os dois protótipos usam o mesmo fixture semântico e medem, com resultado positivo e negativo, a distinção entre note GUID e generated card identity/template ordinal; import, reimport, update e aliases; preservação de scheduling; ordem lema-antes-da-forma; sibling burying nativo ou a alternativa exata e honestamente nomeada; adição/remoção dinâmica de formas; colisão/duplicação; e round-trip. Cada dimensão é executada e reportada separadamente no Anki Desktop atual, Anki Desktop na versão anterior suportada, AnkiDroid atual e AnkiMobile atual. Metadata de família, tag ou deck ID não cria parentesco nativo: **notas separadas não são siblings no Anki padrão**. Se o Modelo B for escolhido, a decisão deve nomear, implementar e testar o mecanismo alternativo de pré-requisito e não exposição concorrente sem usar a palavra sibling para descrevê-lo.

O baseline de migração atual é factual e limitado: `export_anki_package()` cria uma única instância de `genanki.Deck`; para cada `ExportCardRow`, chama uma vez `deck.add_note(build_multilang_note(...))`, produzindo um `genanki.Note` por linha. `build_multilang_model()` declara exatamente um template chamado `Card 1`, portanto cada nota atual gera um card sob esse modelo. `ExportCardIdentity.stable_guid_input()` inclui idioma, source type, `job_id`, `item_key`, `lemma_key` e `sort_index`, e `build_export_note_guid()` faz hash dessa entrada. Os strings de campo atualmente podem ser interpretados como HTML pelos templates Anki. Essa forma de transporte/renderização é somente baseline de segurança e migração: **o comportamento atual não satisfaz automaticamente a v4**.

A decisão da Fase 35 deve publicar a matriz comparativa, fixtures e artefatos por cliente, limitações, aliases necessários, mecanismo de prerequisite/burying ou alternativa, e assinatura dos responsáveis. Antes dessa assinatura, a Fase 36 não pode persistir candidate A, candidate B, card ordinals, aliases ou qualquer schema que torne uma escolha irreversível. Depois da seleção, `GUID-01`, `DISPLAY-01` e a migração passam a referenciar explicitamente o modelo e a versão assinados.

#### Agregação determinística de frequência — `RANK-01`

Cada versão de ranking registra, por corpus, ID, checksum, variante/domínio/período, contagem de tokens e contagem de documentos; pesos de corpus não negativos cuja soma exata é 1; e versões de normalizador, segmentador, analyzer, tagset, política de MWE, política de alocação, thresholds e precisões. O analyzer produz candidates de forma de superfície e possíveis identidades lema/POS/sentido. Cada ocorrência aceita recebe `allocation_share(o,i)` com confiança registrada; as shares das identidades aceitas para aquela ocorrência somam exatamente 1. Ocorrência abaixo do threshold de confiança fica em quarentena e não é atribuída ao primeiro sentido, não entra no denominador de shares aceitas e não contribui para nenhuma identidade.

A política de MWE aplica longest-span determinístico e somente permite overlaps explicitamente aprovados em canais distintos. Uma ocorrência de token não pode ser contada duas vezes no mesmo counting channel como MWE e como componente, nem por duas segmentações concorrentes. `document_frequency(c,i)` conta documentos com alocação aceita para `i` sob essa mesma versão. A fórmula normativa é:

```text
allocated_count(c,i) = sum_o occurrence_count(c,o) * allocation_share(o,i)
frequency_ppm(c,i) = 1_000_000 * allocated_count(c,i) / corpus_token_count(c)
dispersion(c,i) = document_frequency(c,i) / corpus_document_count(c)
rank_score(i) = round(sum_c corpus_weight(c) * ln(1 + frequency_ppm(c,i)) * dispersion(c,i), rank_precision)
```

`ln` é o logaritmo natural. `occurrence_count`, critérios de ocorrência aceita, alocação fracionária, corpus weights, denominadores, política de documentos, thresholds, `rank_precision` e a precisão intermediária são parâmetros versionados; nenhum arredondamento implícito é permitido. `aggregate_allocated_frequency(i) = sum_c allocated_count(c,i)` é calculado antes do tie-break. A ordenação final é exatamente `rank_score DESC`, aggregate allocated frequency `DESC`, depois `lexical_identity_id ASC`.

O manifest liga cada rank às observações e alocações que o produziram. Entradas, políticas e versões iguais devem reproduzir ranks, scores, quarentenas e manifest hash. Drift de corpus, peso, analyzer, alocação, threshold, MWE, fórmula ou precisão cria nova versão de ranking, diff integral identity-by-identity e reaprovação; nunca atualiza ranks silenciosamente dentro de uma edição assinada.

#### Aprovação e workload de formas — `FORM-04`

Cada idioma mantém uma `ImportantFormPolicy` com schema versionado que nomeia: evidence kinds; `evidence_weight(k)`; normalização de `evidence_value(k)`; `minimum_score`; `attestation_threshold`; `analysis_confidence_threshold`; dedup key; exceção same-spelling/different-analysis; `prerequisite_depth`; política de ordenação; forecast de workload; `policy_id`, versão e hash; fontes/checksums; e evidência/review de aprovação. Os pesos são não negativos e somam exatamente 1; cada evidence value é normalizado na escala declarada. O score é:

```text
important_form_score = round(sum_k evidence_weight(k) * evidence_value(k), score_precision)
```

`score_precision`, escala, tratamento de evidência ausente e thresholds são versionados. Depois da deduplicação determinística, a aprovação é exatamente:

```text
score >= minimum_score AND attestation >= attestation_threshold AND analysis_confidence >= analysis_confidence_threshold
```

A dedup key inclui a identidade-pai, surface normalizada e análise morfológica canônica. Grafias iguais podem escapar da deduplicação somente quando `morphological_analysis_id`, sentido/contexto ou pronúncia relevantes são distintos e comprovados; conveniência não cria exceção. As formas aprovadas são ordenadas por `prerequisite_depth ASC`, `important_form_score DESC`, normalized surface `ASC`, depois `morphological_analysis_id ASC`.

Antes da aprovação, o forecast publica a quantidade integral de cards obrigatórios, word audio, sentence audio quando aplicável, bytes/storage, chamadas, custo, review e rebuild por idioma, nível e edição. A aprovação desse workload torna toda forma Core aprovada obrigatória. Nenhum truncamento, top-N, cost cap, edition cap, sample, política adaptativa ou limite de 3000 cards pode removê-la ou enviá-la a Expansion; um cap interrompe o job antes de publicação parcial. Alterar elegibilidade exige nova versão de policy, diff e review, nunca truncamento silencioso na exportação.

#### Identidade e apresentação do card de forma — `DISPLAY-01`

O registro estruturado de cada card de forma contém, no mínimo: `form_card_id`; `parent_lexical_identity_id`; lema-pai exibido; `card_role`; `surface_form_id`; texto exato da superfície exibida; `morphological_analysis_id`; features normalizadas da análise; `sense_id`; cue de contexto/sentido; versão da definição e do conteúdo; referência à `pronunciation_signature`; `deck_edition_id`; deck ID real herdado; referência de pré-requisito; e versão da rendering policy. Esses campos participam do manifest, dos aliases e dos fixtures da topologia selecionada sem transformar a forma em identidade lexical.

A frente mostra contexto suficiente para perguntar o que a forma exata significa ou realiza **neste uso**. Uma grafia ambígua isolada é proibida. A resposta expõe o lema-pai, o papel do card, a análise morfológica, o sentido/cue relevante e áudio da forma exata. Análises distintas da mesma grafia conservam `form_card_id`, `morphological_analysis_id`, card, prompt e cue distintos, inclusive `were` indicativo versus `were` irrealis. A renderização falha fechado se contexto, análise, sentido, versão, áudio ou vínculo com o pai estiver ausente ou inconclusivo.

#### Identidade completa de pronúncia — `AUDIO-02`

A chave de cache se chama `pronunciation_signature` (pronunciation signature) e é uma tupla canônica/versionada que inclui: idioma e versão do `LanguageProfile`; texto exato exibido; texto normalizado declarado; leitura contextual ou fonemas; análise morfológica e sentido quando influenciam pronúncia; locale; voz; SSML/prosódia; versão da pronunciation policy; provider; e versão do provider/modelo. O manifest guarda a serialização canônica/hash da assinatura, hash e tamanho do artefato, codec e status de revisão.

Reuso exige igualdade de **todos** os componentes da assinatura e integridade do artefato. Campo ausente, policy drift, leitura incerta, hash/bytes divergentes ou provider/model version diferente bloqueiam o hit e exigem nova resolução/review segundo o gate de custo. Um `text-only hash` é explicitamente proibido para heterófonos, heterônimos, leituras contextuais e polifonia; texto igual nunca basta para autorizar reuso nesses casos.

#### Fronteira de confiança de IA e campos Anki — `AISEC-01`

Custom, Highlight, corpora e qualquer material externo entram como dados não confiáveis. Instruções embutidas, inclusive “ignore previous instructions...”, são conteúdo citado e nunca controles. Instruções de sistema/policy ficam separadas de conteúdo delimitado e tipado; nenhum payload pode escolher provider, ferramenta, schema, autorização, budget ou policy. Antes de qualquer chamada, limites versionados de bytes, caracteres, tokens e registros são medidos e aplicados por item/lote; somente o contexto mínimo autorizado é enviado, sem secrets, paths privados, raw private context desnecessário ou conteúdo de outro usuário/namespace.

Toda saída de LLM é não confiável e deve validar contra schema tipado fechado, enums/limites e evidência lexical/source autorizada. O pipeline rejeita campos extras, referências inexistentes, instruções de provider/tool e qualquer tentativa de elevar a saída a fato. Cada campo Anki é escaped/encoded para seu contexto de saída; se markup pedagógico for indispensável, usa uma strict allowlist documentada de tags e atributos. São rejeitados scripts, event handlers, URL executável como `javascript:`, active markup, embeds/forms, comandos de provider/tool e diretivas Anki não aprovadas. Escapar texto e validar a estrutura precedem persistência, preview e exportação; o comportamento HTML atual é baseline de risco, não exceção.

Rate, concurrency, input/output token, budget e retry limits são obrigatórios, com timeout, idempotência e interrupção fail-closed antes de ultrapassar o cap. Auditoria guarda somente hashes, IDs, versões, contagens, decisões e metadata sanitizada; prompt, resposta, secrets e texto privado bruto não entram no log compartilhado. Output de LLM nunca é autoridade para identidade lexical, morfologia, sentido, rank ou fatos de pronúncia: esses campos exigem adapter/fonte/evidência e review definidos pelo perfil.

#### Bundle canônico de conteúdo Core — `CONTENT-01`

Cada `deck_edition_id` referencia um bundle Core imutável, versionado, checksummed e assinado contendo definições, exemplos, traduções, `pronunciation_signature` e assets de áudio, render policy, fontes/grounding e evidência de review. **O conteúdo Core é canônico e versionado por edição assinada.** Ranks, content GUIDs, hashes e assets desse bundle são facts compartilhados da edição, não projeções pessoais.

**É proibido ao histórico do aprendiz regenerar ou mutar conteúdo Core compartilhado.** Uma correção material cria nova edição ou content version, diff machine-readable, review, decisão de alias/migração quando necessária e evidência de release; nunca sobrescreve a edição assinada nem troca semantic GUID por usuário. **A adaptação altera somente queue/module/order/eligibility.** Ela não altera definição, exemplo, tradução, áudio, render policy, rank, content GUID ou asset assinado.

Custom e Highlight permanecem caminhos privados em namespaces isolados de conteúdo/versão, com consentimento, retenção e acesso próprios. Sinais pessoais podem orientar conteúdo privado nesses caminhos, mas nunca sobrescrevem, contaminam ou regeneram o bundle Core compartilhado.

#### Avaliação reproduzível por idioma — `EVAL-01`

Cada idioma possui datasets de referência com ID, versão e hash, separados por source e estratos de risco. A cobertura inclui correção/concisão de definição, análise de forma, naturalidade, target/sense match, tradução, i+1 strict/adaptive/contextual, pronúncia/áudio e segurança de HTML/campos Anki. Cada métrica declara explicitamente numerator, denominator, casos elegíveis/excluídos, sample e strata, threshold derivado de evidência, drift tolerance, responsável e comportamento bloqueante; nenhum threshold numérico é inventado antes da baseline aprovada em G0/Fase 35.

As fórmulas comuns são:

```text
dimension_pass_rate = passed_cases / eligible_cases
critical_failure_rate = critical_failures / eligible_cases
regression_delta = current_dimension_pass_rate - signed_baseline_dimension_pass_rate
```

Dimensões subjetivas usam rubrica ancorada: `0=wrong/unsafe`, `1=major error`, `2=material correction required`, `3=correct with minor issue`, `4=release quality`. Checks estruturais, de segurança e fail-closed permanecem determinísticos e bloqueantes a 100% onde o contrato já exige 100%; uma média subjetiva não compensa falha crítica.

A aprovação combina validators determinísticos com review humano/especialista independente e estratificado. Um LLM judge pode ser sinal secundário calibrado, mas nunca sole approver nem substituto de especialista. Drift de dataset, analyzer, prompt, provider, modelo, policy ou render/schema reroda as suites afetadas; resultado abaixo do threshold ou além da regression tolerance bloqueia promoção/release e registra diff, sem waiver genérico de adapter.

#### Cenários de aceitação positivos e negativos

| Família de cenário | Caso positivo obrigatório | Caso negativo fail-closed obrigatório |
|---|---|---|
| Topologia/siblings | Cards produzidos pela mesma nota no Modelo A podem demonstrar native sibling burying por cliente; o manifest distingue note GUID de generated card identity/template ordinal. | No Modelo B, metadata de família não cria sibling: **notas separadas não são siblings no Anki padrão**. O teste deve usar a alternativa honestamente nomeada ou bloquear a decisão, nunca atribuir burying nativo inexistente. |
| `be/is/was/were` | Evidência aceita de `be`, `is`, `was` e `were` agrega reproduzivelmente ao rank correto de lema/POS/sentido; formas aprovadas permanecem obrigatórias no nível real de `be`; `were` indicativo e irrealis recebem prompts, análises, IDs e cards distintos sem consumir identidades Core. | Alocação automática ao primeiro sentido, prompt apenas “were”, GUID/análise compartilhado, truncamento por 3000 cards ou reroute para Expansion reprova o lote. |
| Polifonia CJK | Mandarim `行` com `xíng` e `háng`, e leituras contextuais do japonês `生`, geram pronunciation signatures e assets distintos quando leitura/contexto diferem. | Texto igual, hash apenas de `行`/`生` ou cache hit sem leitura/contexto completo nunca autoriza reuso; incerteza fica em quarentena. |
| Input privado/prompt injection | Texto benigno de Custom/Highlight permanece privado, delimitado e tipado, com contexto mínimo autorizado e audit hash-only. | “ignore previous instructions...” é somente dado citado; não muda controles, provider, ferramenta, schema, budget ou destino e não causa disclosure de raw private context. |
| HTML/campos Anki | Texto simples do aprendiz é encoded para o contexto e markup aprovado passa somente pela allowlist estrita. | `<script>`, event handler, URL `javascript:` ou qualquer executable markup/output é rejeitado antes de persistência/exportação, nunca renderizado. |
| GUID/migração | O mesmo item semântico em novo job ou rank conserva a identidade futura do modelo selecionado; alias 1:1 provado preserva o mapping elegível. | O drift atual causado por `job_id`/`sort_index` é detectado; sem alias/migração 1:1 comprovado, não é chamado de estável, não transfere scheduling e bloqueia apply. |

O comportamento padrão é, portanto, um card headword de reconhecimento por identidade lexical, além de toda `Important Form` justificada/aprovada que seja obrigatória para a identidade. Reverse, listening e cloze não aparecem por inferência nem por expansão de template; permanecem desabilitados até uma decisão explícita por edição/perfil. Quando habilitados, não alteram a contagem de identidades do Core, usam papéis e GUIDs distintos, respeitam `DEPEND-01`, incrementam `O_enabled_optional_role_cards` e aparecem no relatório `LOAD-01`.

O sequencing de formas é dirigido por pré-requisitos: primeiro o lema/identidade, depois cada forma importante elegível no destino já herdado. Sob a topologia selecionada e comprovada por `ANKI-01`, cards da mesma nota podem usar sibling burying nativo; notas separadas usam somente a alternativa de não exposição concorrente explicitamente nomeada/testada. O export fornece os IDs e metadados exigidos pelo mecanismo escolhido sem escrever no scheduler importado do Anki.

#### Exemplo normativo: `be`, `is`, `was` e `were`

- `be` é a identidade lexical Core do verbo e recebe o card headword de reconhecimento padrão. As observações aceitas de `be/is/was/were` são alocadas por lema/POS/sentido conforme `RANK-01`; seu rank congelado resolve `L_be` para exatamente um nível real e `D_be` para o deck ID correspondente; por exemplo, se `L_be = 1`, `D_be = en::Frequency::Level 1`.
- Toda análise de `is`, `was` ou `were` que satisfaz `FORM-02`/`FORM-04` e é aprovada gera um card obrigatório adicional em `D_be`, nunca em Expansion nem em destino próprio. `is` registra presente indicativo, terceira pessoa singular; “She is ready.” sustenta uma definição meaning-first com gramática contextual, prompt não ambíguo `DISPLAY-01` e áudio exatamente de `is`.
- `was` registra passado indicativo singular; “He was tired.” ancora sentido, pessoa/número aplicáveis e áudio exatamente de `was`, ainda em `D_be`.
- `were` requer análise contextual. “They were ready.” registra passado indicativo plural, enquanto “If I were ready, I would go.” registra irrealis. A grafia igual produz cues e, quando aprovadas, cards ligados a análises distintas; `DEF-01`, `FORM-03`, `DISPLAY-01`, `AUDIO-01`, `AUDIO-02` e `GUID-01` impedem prompt, áudio ou identidade incorretos. Se ambas as análises forem aprovadas, ambas contam separadamente em `N_important_form_cards` e em `N_level_important_form_cards` de `L_be`.
- O card de `be` precede todos os cards de forma; `is`, `was` e cada análise de `were` só ficam elegíveis depois dele, compartilham exatamente `D_be` e entram no total variável de cards/workload do mesmo nível do inglês sem consumir slots de identidade. Se `ANKI-01` selecionar cards da mesma nota, o cliente comprovado usa sibling burying nativo; se selecionar notas separadas, usa a alternativa nomeada/testada de não exposição concorrente e nunca as chama de siblings.

### 3.6 MWE, sentidos, fontes, rotas e papéis de card

Os seguintes conceitos são persistidos separadamente:

- **MWE:** identidade lexical multiword com segmentação, composição, variantes e sentido próprios;
- **resolução de sentido:** evidência que conecta ocorrência, POS e contexto a uma identidade;
- **tipo de fonte/inventário do pai:** núcleo, expansão, lista personalizada, highlight, histórico APKG ou fundação linguística; somente identidades pertencem ao inventário, e seus cards descendentes herdam esse pertencimento para roteamento;
- **rota de conteúdo:** conjunto aprovado de adapters e providers para enriquecer o item;
- **papel de card:** finalidade pedagógica e contrato de campos do card;
- **destino de subdeck:** caminho Anki real da identidade-pai, derivado antes de o papel do card ser aplicado e preservado pelos cards descendentes.

Papéis mínimos: headword, `Important Form`, MWE e os papéis opcionais explicitamente habilitados; Core, Expansion, Custom, Highlight e fundação são inventários/destinos, não papéis capazes de recategorizar descendentes. A decisão determinística segue `source type -> parent identity/sense -> parent inventory destination -> Core rank/real level when applicable -> content route -> card role -> inherited real subdeck/deck ID -> prerequisite sequence`. Assim, um `Important Form` de Core usa o mesmo subdeck real do lema; um de Expansion, Custom, Highlight, Grammar/foundation ou outra fonte aprovada permanece com o pai. Grammar continua destino próprio somente para identidade ou papel já atribuído à fundação/gramática, nunca como sink de forma de Core. Uma rota sem suporte ou com sentido ambíguo não cai em um card genérico: fica bloqueada ou em quarentena com diagnóstico.

### 3.7 Dados pessoais e histórico Anki

Listas personalizadas e highlights só são habilitados quando o `LanguageProfile` comprova normalização, morfologia, matching, conteúdo, áudio e `AISEC-01` para aquela capacidade. Os dados preservam forma e ordem submetidas, proveniência privada e consentimento em namespaces isolados. Podem mapear uma identidade compartilhada ou criar identidade privada, mas nunca mudam rank, pertencimento, GUID ou bundle `CONTENT-01` do núcleo compartilhado.

A integração **`read-only APKG history`** lê pacotes suportados e histórico de revisão para produzir um mapeamento com proveniência, confiança e quarentena. Ela não escreve no arquivo importado, na coleção, no Anki ou no AnkiConnect. O mapeamento é derivado e revogável; incerteza não vira certeza por conveniência.

A **`adaptive queue`** consome rank, pré-requisitos, prontidão de conteúdo, sinais pessoais autorizados e histórico mapeado. Ela é determinística para a mesma versão e entrada, explica cada componente do score, permite reset e override e separa prioridade de estudo de identidade/rank/exportação. Ela nunca altera rank canônico, histórico importado, intervalos do Anki, `deck_edition_id`, conteúdo/GUID compartilhado ou assets assinados. Em Core, seu efeito permitido é exclusivamente queue/module/order/eligibility; conteúdo privado de Custom/Highlight segue seu namespace próprio.

## 4. Fluxo de capacidade ponta a ponta

| Etapa | Entrada e transformação | Evidência persistida | Falha e recuperação |
|---|---|---|---|
| 1. Aprovação de fonte | Registro de fonte lexical, corpus/frequência, exemplo, tradução, áudio ou dataset de avaliação | licença, finalidade, atribuição, direitos de aquisição/derivação/redistribuição, versão e checksum | uso e redistribuição bloqueados; revogação identifica derivados, ranks, conteúdo e suites para rebuild |
| 2. Ingestão versionada | Bytes congelados entram por adapter declarado e observações de formas/corpora são contadas por canal | hash de entrada, versão do adapter/analyzer, token/document counts, contagens, rejeições e rerun ID | lote atômico falha ou retoma; entrada/analyzer alterado exige nova versão e diff |
| 3. Perfil linguístico | `LanguageProfile` aplica script, normalização, segmentação, morfologia e capabilities de topologia/rank/forms/display/pronúncia/IA/conteúdo/eval | perfil, normalizador, analyzer, policies, estados/evidências e versões | capability ausente/pendente, indisponibilidade ou ambiguidade vai para quarentena; nenhuma heurística silenciosa |
| 4. Identidade e alocação | candidates de forma resolvem lema, POS, sentido e MWE; ocorrências aceitas recebem shares determinísticas | evidência/confiança de resolução, shares, quarentena, aliases, proveniência e analyzer/policy versions | abaixo do threshold não escolhe primeiro sentido; overlap/double count de MWE bloqueia o ranking |
| 5. Inventário e rank | `RANK-01` agrega frequência alocada, pesos e dispersão; identidade aprovada recebe Core ou expansão e rank versionado | corpus manifests, fórmula/parâmetros, scores, tie-break, membership, nível/destino real, ranking version/hash e curadoria | drift exige nova versão/diff/reaprovação; card/forma nunca recebe rank ou membership próprio |
| 6. Formas | ocorrências viram `SurfaceForms`; `ImportantFormPolicy` calcula/deduplica/ordena aprovações, que herdam inventário, nível e deck ID do pai | score/evidência/thresholds, policy hash, forecast integral, forma exata, análise, `DISPLAY-01` e prerequisite | análise/threshold duvidoso não aprova; cap nunca omite forma Core já aprovada nem publica workload parcial |
| 7. Enriquecimento | definição, exemplo e tradução seguem sentido/forma, `AISEC-01` e o namespace canônico ou privado | grounding, conteúdo tipado/escaped, prompt/policy hash, `deck_edition_id`, versions, validações e review | instrução embutida não muda controles; output não grounded/seguro é rejeitado; histórico não regenera Core |
| 8. Áudio | forma/contexto exibidos e frase aprovada geram assets separados por `pronunciation_signature` | assinatura completa, texto/hash/bytes exatos, leitura, análise/sentido, voz, locale, SSML, provider/model, custo/licença/review | somente assinatura integral + artefato íntegro reutilizam cache; text-only hash, divergência ou incerteza bloqueiam |
| 9. Roteamento | fonte, identidade/sentido, inventário e rank/nível do pai fixam o destino antes de conteúdo e papel; a forma preserva o mesmo deck ID | decisão reproduzível, destino herdado e razão por regra | rota não suportada ou ambígua fica em quarentena; papel não desvia Core para Expansion/Grammar/destino de formas |
| 10. Exportação | somente a topologia selecionada por `ANKI-01` compõe notas/cards, subdecks reais e mídia; `DISPLAY-01` preserva identidade semântica e lema antes das formas | model/version, note GUID, generated card identity/template ordinal, aliases, schema/campos escaped, deck ID, sequência, fórmulas e round-trip por cliente | sem decisão/prova, persistência/export v4 bloqueia; colisão, update/scheduling ou total divergente impede publicação parcial |
| 11. Histórico | parser seguro executa mapeamento somente de leitura | schema detectado, limites, IDs candidatos, confiança e proveniência | arquivo suspeito ou mapping incerto é rejeitado/quarentenado sem escrita |
| 12. Adaptação | sinais autorizados alimentam score versionado e alteram somente queue/module/order/eligibility | componentes do score, policy, snapshot, explicação e prova de hashes Core/content/GUID/rank inalterados | reset restaura baseline; ausência de sinal usa cold-start canônico; tentativa de regenerar/mutar Core falha fechado |
| 13. Avaliação | datasets `EVAL-01` por idioma/estrato combinam validators determinísticos e review independente | hashes/versions, numerators/denominators, samples/strata, scores, thresholds, drift e decisões | falha crítica, resultado abaixo do threshold, drift excessivo ou sole LLM judge bloqueia freeze/export/release |
| 14. Migração | `in-place Multilang migration` parte do baseline atual um-row/one-note/`Card 1`/single deck e GUID com `job_id`/`sort_index`, aplicando o plano semântico confirmado em lotes | prévia, backup, decisão `ANKI-01`, aliases, confirmação, contagens, scheduling, signatures, conteúdo/avaliação, checkpoints e hashes | mapping não provado não transfere scheduling; divergência de fórmula, destino, conteúdo, segurança ou cliente aciona rollback/restore |

Todos os limites usam IDs estáveis e registros de proveniência/versionamento. Reruns com as mesmas entradas e versões devem produzir os mesmos resultados ou uma divergência bloqueante explícita. Quarentena mantém payload mínimo necessário, razão, candidato, regra/versão e ação possível. Recuperação nunca apaga silenciosamente a entrada original nem converte falha em aprovação.

## 5. G0 e especificações das fases

### G0: Pré-requisitos de promoção e baseline congelada

**Resultado:** Existe evidência suficiente para decidir, separadamente, se a proposta v4 pode entrar no planejamento ativo sem sobrepor a v3.0, perder dados atuais ou assumir fontes, privacidade, custos e qualidade ainda não aprovados.

**Depende de:** Conclusão, verificação e arquivamento formais da v3.0; nenhuma dependência v4 pode substituir esse requisito.

**Entregáveis:**

- inventário atual e datado de schemas, dados persistidos, IDs estáveis, migrations, exports/APKG, note types, subdecks, assets, testes, providers, registries e riscos da árvore de trabalho;
- baseline source-shaped de `ANKI-01`/`GUID-01`: uma instância de `genanki.Deck`, um `genanki.Note` por `ExportCardRow`, um template `Card 1` e um card por nota no modelo atual, além do GUID input com idioma/source type/`job_id`/`item_key`/`lemma_key`/`sort_index` e do risco de strings de campo interpretadas como HTML; **o comportamento atual não satisfaz automaticamente a v4**;
- snapshots checksummed e recuperáveis de banco, configurações, manifests, assets e mapeamentos existentes;
- ensaio documentado de restore em ambiente isolado, com RPO/RTO ou limites equivalentes aprovados;
- reconciliação do baseline com toda evolução ocorrida após a escrita deste documento;
- escopo v4, matriz dos 22 idiomas modernos e perfil isolado do Latim aprovados;
- estudo de viabilidade e evidência de fonte/licença/atribuição/redistribuição por idioma, sem commit de asset não aprovado;
- regras aprovadas de processamento, minimização, consentimento, retenção, exclusão e provider para dados pessoais/APKG;
- estimativas dry-run, budgets e hard caps por provider, item, lote e execução;
- pré-requisitos de `EVAL-01`: datasets/fixtures de baseline por idioma e estrato com ID/versão/hash, direitos aprovados, numerators/denominators/samples e evidência da qual serão derivados thresholds e drift tolerances para morfologia, sentido, matching, texto, tradução, i+1, áudio, HTML/Anki, exportação e migração;
- baseline de contagens que separa, por idioma, 3000 identidades Core, 3000 cards headword padrão, cards obrigatórios de formas, papéis opcionais explicitamente habilitados e identidades/cards de Expansion separados;
- pacote de evidência e registro explícito da decisão de promover ou rejeitar/deferir a v4.

**Critérios de saída:**

1. A v3.0 consta como concluída, verificada e arquivada nas fontes canônicas, sem fase aberta.
2. O inventário cobre 100% das superfícies listadas, registra riscos/diffs sem alterá-los e documenta literalmente o source baseline de `ANKI-01`/`GUID-01` sem chamá-lo de compliance v4 nem de decisão de topologia.
3. Um snapshot completo é restaurado e reconciliado por hashes e contagens em ambiente isolado.
4. Cada idioma possui decisão de viabilidade de fonte/licença e regras de privacidade, ainda que o resultado seja bloqueado.
5. Budgets/hard caps e os datasets/thresholds/drift de `EVAL-01` têm responsáveis, direitos, evidência, fixtures baseline e comportamento fail-closed, usando workload variável em vez de presumir 3000 cards por idioma.
6. Uma aprovação separada, registrada e explícita autoriza a futura alteração de SPEC/ROADMAP; sem ela, nenhuma Fase 35 começa.

### Fase 35: Contratos

**Resultado:** Glossário, contagens, variantes, políticas linguísticas, papéis de card, semântica de edição e todos os contratos normativos estão fechados antes de qualquer asset ou schema v4.

**Depende de:** G0 aprovado e promoção separada registrada.

**Entregáveis:**

- glossário normativo para identidade, sentido, `SurfaceForms`, `Important Forms`, MWE, Core, expansão, edição, módulo, tag, subdeck, deck ID, sequência e workload;
- regras exatas de 3000 identidades Core e 3000 cards headword padrão, três bandas de 1000 identidades, total variável de cards pelas fórmulas de §3.5 e expansão adicional opt-in de zero a 3000 identidades, com variantes e Latim isolado;
- política de explicações, exceção de inglês-alvo e transição coreana português-v3 para inglês-v4;
- papéis de card, reconhecimento padrão, opcionais reverse/listening/cloze desabilitados, formas fora da quota de identidades mas dentro da carga, herança obrigatória do destino do pai, módulos de 50–200 e tags suplementares;
- dois protótipos reais bloqueantes de `ANKI-01`, sem preselection: **Modelo A — uma nota lexical por família com cards de headword/formas** e **Modelo B — notas separadas ligadas por metadados semânticos de família**, usando `{language}::Frequency::Level 1`, `{language}::Frequency::Level 2` e `{language}::Frequency::Level 3`, sem subdeck top-level de formas;
- matriz comparativa por modelo e por Anki Desktop atual/anterior suportado, AnkiDroid atual e AnkiMobile atual, cobrindo note GUID versus generated card identity/template ordinal, import/reimport/update/alias, scheduling, lema-antes-da-forma, sibling burying nativo ou alternativa honesta, add/remove dinâmico, collision/duplication e round-trip; **notas separadas não são siblings no Anki padrão**;
- decisão assinada de topologia e versão, limitações e evidência; nenhum schema/persistence da Fase 36 codifica candidato antes dessa seleção;
- manifests e policies completos para agregação `RANK-01`, `ImportantFormPolicy`/`FORM-04`, display `DISPLAY-01`, pronunciation signature `AUDIO-02`, trust/output `AISEC-01`, bundle de edição `CONTENT-01` e avaliação `EVAL-01`, com fórmulas, thresholds derivados de evidência, datasets, ordering, workload, segurança e drift;
- especificações aprovadas dos 20 contratos: `CARD-01`, `FORM-01`, `FORM-02`, `FORM-03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01`, `GUID-01`, `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`.

**Critérios de saída:**

1. Um manifest sem conflito, campo indefinido ou decisão implícita fecha todos os 20 IDs: `CARD-01`, `FORM-01`, `FORM-02`, `FORM-03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01`, `GUID-01`, `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`.
2. Casos de contagem reconciliam `core_identity_count`, os 3000 headwords, `N`, cada componente de `O`, `frequency_card_count` e os três totais por nível; provam que identidade, não card/forma, ocupa a quota e que `N > 0` torna o total maior que 3000.
3. Matriz dos 22 idiomas e Latim fecha variantes, explicações e requisitos individuais sem escolher fonte/provider pendente.
4. Os dois protótipos `ANKI-01` publicam resultado por dimensão e por cada cliente suportado, e uma decisão assinada escolhe exatamente um modelo sem falsificar sibling semantics; fixture, dimensão, cliente ou alias unresolved reprova o gate.
5. Privacidade, licença, custo e qualidade possuem donos/evidência exigida; datasets/thresholds `EVAL-01`, policies, hashes, workloads e cenários positivos/negativos estão assinados ou permanecem explicitamente bloqueados.
6. Qualquer contrato, prototype, client result, decision ou evidência unresolved bloqueia a Fase 36 e todo downstream afetado; a documentação atual não equivale à execução ou aprovação desses artefatos.

### Fase 36: Persistência

**Resultado:** A persistência v4 existe de forma versionada e inativa somente para a topologia selecionada e assinada por `ANKI-01`, protegida por backups imutáveis restaurados antes de qualquer mutation e sem alterar o runtime atual.

**Depende de:** Fase 35.

**Entregáveis:**

- inventário de schemas/dados e backups imutáveis, checksummed e restore-tested antes da primeira migration;
- artefato de decisão `ANKI-01` validado como pré-condição técnica; nenhuma migration cria coluna/tabela/candidate mapping antes da assinatura e somente o modelo escolhido pode orientar o schema;
- contratos persistentes para `LanguageProfile`, identidade/sentido lexical, membership/rank/nível/destino da identidade-pai, `SurfaceForm`, `MorphologicalAnalysis`, `CardTarget`, note GUID, generated card identity/template ordinal, collection/version/entry, deck edition e aliases semânticos do modelo `ANKI-01`; uma forma referencia esses dados do pai e nunca recebe membership Core/Expansion próprio;
- mapeamento explícito do baseline atual one-row/one-`genanki.Note`/one-`Card 1`/single-deck e GUID com `job_id`/`sort_index` para posterior migração, sem chamá-lo de topologia v4;
- extensão de candidate/snapshot metadata, proveniência, versões de analyzer/policy e fingerprints;
- migrations forward/backward, modelos ORM e constraints equivalentes;
- feature/cutover flags que mantêm todas as estruturas novas inativas até a Fase 51.

**Critérios de saída:**

1. Restore de backup reconcilia hashes, contagens e referências antes e depois dos ensaios de migration.
2. Alembic/schema e ORM têm paridade comprovada para campos, constraints, índices e relações.
3. O schema `ANKI-01` persiste somente a candidate selecionada, distingue note GUID de generated card identity/template ordinal e prova round-trip/constraints/aliases sem campos órfãos do modelo rejeitado; fingerprints idênticos são determinísticos.
4. Estruturas inativas não alteram geração, exportação, dados pessoais nem comportamento v3 existente.
5. Rollback, segurança de dados, custo de armazenamento e qualidade de compatibilidade passam seus gates.

### Fase 37: Fontes e cobertura

**Resultado:** Cada idioma moderno possui fontes, corpora e pools candidatos de identidades auditáveis, maiores que 3000, com ranking `RANK-01` reproduzível, cobertura mensurada e redistribuição bloqueada até aprovação.

**Depende de:** Fase 35.

**Entregáveis:**

- registry por fonte/idioma para aquisição, licença, derivação, redistribuição, atribuição, versão e revogação;
- manifests `RANK-01` de corpora balanceados e held-out, com IDs/checksums, token/document counts, domínio, período, variante, qualidade, privacidade e corpus weights concretos não negativos somando 1;
- candidate pools maiores que 3000 **identidades** por idioma e reservas separadas; cards, `SurfaceForms` e form packs não contam como candidatos nem vagas;
- outputs `RANK-01` de candidates de superfície e alocação lema/POS/sentido com shares/confiança, quarentena abaixo do threshold, dedup longest-span/overlap de MWE, allocated counts, frequency ppm, dispersão, fórmula/rounding, aggregate frequency, tie-break e analyzer/policy versions;
- ranks e manifest hashes reproduzíveis, com diff integral/reaprovação obrigatórios para drift de input, analyzer, policy, threshold, fórmula ou precisão;
- relatórios separados para cobertura de identidades das bandas 1k/2k/3k e da Expansion opt-in, sem usar contagem de cards para preencher cobertura;
- `wordfreq` restrito a bootstrap, nunca fonte final nem autorização de CSV redistribuído.

**Critérios de saída:**

1. Todo idioma tem pool >3000 identidades e held-out independente, ou permanece explicitamente bloqueado; esse `>3000` não é contagem nem teto de cards.
2. `RANK-01` reproduz alocações, quarentenas, scores, ordem `rank_score DESC`/frequência alocada `DESC`/`lexical_identity_id ASC` e manifest hash com inputs/versões iguais; shares aceitas somam 1 e nenhum token é double-counted no mesmo canal MWE.
3. Cada byte/derivado aponta para versão, checksum, licença, atribuição e decisão de redistribuição.
4. Direito incerto impede commit/publicação; corpus privado não entra em asset compartilhado.
5. Aquisição/processamento têm orçamento/caps e os scores passam revisão de qualidade/viés.

### Fase 38: Morfologia e curadoria

**Resultado:** Profiles e analyzers fixados resolvem identidade, forma, sentido, MWE, target matching, display e pronúncia contextual com `FORM-04`, `DISPLAY-01` e `AUDIO-02`, precisão aceita de 100% e falha fechada mensurável.

**Depende de:** Fase 35.

**Entregáveis:**

- seleção, qualificação e pin de analyzer/tokenizer por `LanguageProfile`;
- normalização, lema/POS/sentido, MWE, features de forma e roteamento determinísticos, persistindo o inventário/nível/destino do pai antes de aplicar o papel de card;
- `ImportantFormPolicy` `FORM-04` por idioma com evidências/pesos, score/precisão, thresholds de score/attestation/analysis, dedup e exceções, ordering por prerequisite/score/surface/analysis, policy hash, approval evidence e forecast integral antes da aprovação;
- fixtures `DISPLAY-01` para schema, prompt/cue/resposta, análises same-spelling distintas e IDs estáveis, exigindo toda forma Core aprovada no mesmo deck ID do lema, depois dele, e formas de Expansion/Custom/Highlight/Grammar/foundation no destino herdado sem membership próprio;
- evidência `AUDIO-02` de leitura/fonemas contextuais, dependência de morfologia/sentido e política/versionamento completo de `pronunciation_signature`, incluindo heterófonos/polifonia positivos e negativos;
- reservas revisadas e congeladas para substituições posteriores;
- remoção de live fallback heurístico de qualquer caminho candidato v4;
- no mínimo 120 casos dourados por idioma e 200 para cada idioma CJK ou aglutinativo, com positivos/negativos;
- revisão humana estratificada e 100% dos casos de alto risco, ambiguidade, OOV e mudança de analyzer.

**Critérios de saída:**

1. Entre análises aceitas, a precisão é 100%; falso aceite reprova o profile/lote.
2. Pelo menos 98% dos casos inequivocamente resolvíveis são resolvidos; o restante é explicado/quarentenado.
3. Ambiguidade tem 100% de fail-closed e target matching positivo/negativo passa 100% dos goldens aprovados.
4. `FORM-04`, `DISPLAY-01` e `AUDIO-02` reproduzem aprovação/ordem/workload, identidade/prompt/cue e pronunciation signature/asset; same-spelling/different-analysis permanece distinto e text-only cache falha fechado.
5. Termos de analyzer/modelo, custo de execução, payload mínimo de review e thresholds têm aprovação; nenhum live fallback mascara falha.

### Fase 39: Piloto representativo

**Resultado:** Um piloto offline de oito idiomas prova os contratos ponta a ponta antes do rollout por famílias e produz estimates confiáveis de runtime, custo e invalidação.

**Depende de:** Fases 36, 37 e 38.

**Entregáveis:**

- execução offline dos 20 contratos `CARD-01`, `FORM-01`, `FORM-02`, `FORM-03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01`, `GUID-01`, `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, cada um com ao menos um caso positivo e um negativo aplicável;
- exatamente 100 identidades candidatas offline para cada `pt`, `en`, `de`, `pl`, `tr`, `ja`, `zh` e `ko` (800 no total), sem confundir o tamanho da amostra de identidades com quantidade de cards;
- evidência de identidade/sentido, formas, MWE/rota, 100 cards headword padrão por idioma-piloto e toda `Important Form` Core aprovada como card adicional obrigatório no nível/deck ID herdado;
- casos ingleses de `be`, `is`, `was` e `were`, incluindo indicativo versus irrealis contextual;
- `Definitions` meaning-first e contratos de áudio da forma/sentença exatas sem chamada paga;
- reports `LOAD-01` que separam identidades, headwords, `N`, cada `O`, total computado e reconciliação por nível; Expansion é reportada à parte por identidade/headword/forma/papel opcional;
- fixtures das seis famílias obrigatórias: same-note native burying versus separate-note alternative; `be/is/was/were`; `行`/`xíng`/`háng` e `生`; input privado benigno versus “ignore previous instructions...” citado; texto encoded versus `<script>`/event handler/`javascript:` markup; e identidade futura estável versus drift atual de `job_id`/`sort_index` com alias/migração 1:1;
- estimates de runtime, memória, storage, workload variável, chamadas/custo e regras de promotion/invalidation.

**Critérios de saída:**

1. Cada idioma produz 100 decisões de identidade reproduzíveis, com aceites, rejeições e quarentena reconciliados; os cards resultantes podem exceder 100 quando `N > 0`.
2. Todos os 20 contratos normativos — `CARD-01`, `FORM-01`, `FORM-02`, `FORM-03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01`, `GUID-01`, `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` — têm pelo menos uma prova positiva e uma negativa aplicável no piloto.
3. `is/was/were` mantêm contexto, análise, GUID e áudio pretendido distintos quando semanticamente necessário, contam cada análise aprovada em `N`, compartilham o nível/deck ID de `be` e seguem depois dele.
4. Budget padrão de provider pago é zero; tentativa de chamada bloqueia e rollout não avança com threshold falho.
5. Privacidade, licença, estimates de custo e métricas de qualidade geram decisão explícita de promover ou invalidar cada componente.
6. As seis famílias de cenário produzem resultado fail-closed esperado; nenhum adapter genérico, metadata de família ou julgamento exclusivo de LLM pode dispensar uma falha de idioma, cliente, segurança ou migração.

### Fase 40: Rollout românico

**Resultado:** `pt`, `es`, `fr`, `it` e `ro` possuem planos linguísticos completos e amostras verticais aprováveis sob os contratos comuns.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada idioma: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato em 3000 identidades/3000 headwords, reserva, todas as `Important Forms` Core aprovadas, Expansion opt-in somente de identidades e coverage report;
- para cada idioma românico, manifests/datasets e casos positivos/negativos de `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, com thresholds e drift próprios em vez de waiver por adapter comum;
- regras românicas para gênero, clíticos, contrações, conjugação, modo e, em romeno, `ș/ț` com vírgula;
- amostra diagnóstica vertical de 90 cards por idioma (450 no total), incluindo reconhecimento padrão e formas justificadas no destino herdado; esse tamanho não limita a exportação completa nem autoriza truncar formas;
- plano de voz/áudio da forma exata, sequência lema->formas e report `LOAD-01` com identidades/headwords/`N`/cada `O`/total e reconciliação por subdeck real, mantendo Expansion separada;
- manifests reproduzíveis sem freeze global nem provider pago implícito.

**Critérios de saída:**

1. Os cinco idiomas completam todos os itens do plano, sem lacuna escondida por adapter genérico.
2. Cada amostra de 90 passa identidade/sentido, target matching, definição, forma, rota herdada, mesmo deck ID do pai e exportability estática.
3. `Important Forms` têm somente razões `FORM-02`, ficam fora da contagem de identidades, entram obrigatoriamente depois do lema no mesmo nível de Core e aumentam o workload reportado.
4. Fonte/licença e variantes/locales são aprovadas ou bloqueiam somente o idioma afetado, sem redistribuição antecipada.
5. Custos/vozes são estimates; qualidade e human review aprovam a promoção para freeze.
6. `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` passam separadamente para `pt`, `es`, `fr`, `it` e `ro`; qualquer dataset, segurança, conteúdo canônico ou review independente falho bloqueia somente o profile afetado, sem LLM-only approval.

### Fase 41: Rollout germânico

**Resultado:** `en`, `de`, `nl`, `da`, `nb` e `sv` possuem planos completos e amostras verticais que preservam suas diferenças estruturais e fonológicas.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos seis idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato em identidades/headwords, reserva, todas as `Important Forms` Core aprovadas no nível do pai, Expansion opt-in de identidades, coverage report, amostra, voz/áudio e revisão humana;
- para cada idioma germânico, manifests/datasets e casos positivos/negativos de `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, incluindo capitalização, compostos, formas contextuais e pronúncia por variante;
- capitalização alemã, compostos e verbos separáveis; definitude; pitch accent/stød; identidade Bokmål `nb`;
- inglês-alvo com explicações em português e formas contextuais de `be`;
- amostra diagnóstica vertical de 90 cards por idioma (540 no total), sem transformar a amostra em cap para o inventário completo;
- planos de áudio/voz, sequência lema->formas, herança de destino e reports `LOAD-01` total/per-level com Expansion separada por idioma/variante.

**Critérios de saída:**

1. Os seis idiomas atendem ao checklist completo e a identidade `nb` nunca cai em `no`.
2. Capitalização, compostos, separáveis e definitude passam goldens positivos/negativos.
3. Pitch/stød são qualificados por evidência e nunca inventados por ortografia ou voz não revisada.
4. As 540 amostras respeitam a quota de identidades Core, GUIDs semânticos, formas Core obrigatórias no mesmo deck ID após o lema e explicações portuguesas para `en`; sua carga projetada usa as fórmulas e pode exceder 3000 cards por idioma.
5. Gates de privacidade, licença, custo e qualidade aprovam ou bloqueiam granularmente cada profile.
6. `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` passam separadamente para `en`, `de`, `nl`, `da`, `nb` e `sv`; nenhuma falha linguística/segurança é dispensada por adapter genérico ou julgamento exclusivo de LLM.

### Fase 42: Rollout eslavo e grego moderno

**Resultado:** `pl`, `ru`, `cs`, `hr` e `el` possuem planos completos e amostras verticais com caso, aspecto, escrita e identidade específicos.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos cinco idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato em identidades/headwords, reserva, todas as `Important Forms` Core aprovadas no nível do pai, Expansion opt-in de identidades, coverage report, amostra, voz/áudio e revisão humana;
- para cada idioma eslavo/grego, manifests/datasets e casos positivos/negativos de `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, estratificados por caso, aspecto, script, stress, homografia e risco de análise;
- caso, aspecto, animacidade, reflexivos, stress/script e clíticos por profile;
- política russa `е/ё`, stress e pares aspectuais; identidade croata `hr` sem fallback `sh`; normalização grega;
- amostra diagnóstica vertical de 90 cards por idioma (450 no total), sem truncar a projeção do inventário completo;
- planos de áudio/voz, sequência lema->formas e reports `LOAD-01` total/per-level e por fonte, com workload variável e revisão de risco morfológico.

**Critérios de saída:**

1. Os cinco idiomas completam o checklist sem fundir sentidos, aspectos ou identidades nacionais.
2. Goldens cobrem caso/aspecto/animacidade/reflexivos e matching positivo/negativo.
3. `е/ё`, acento russo, `hr` e diacríticos/sigma gregos sobrevivem a round-trip e fingerprints.
4. As 450 amostras mantêm formas fora da contagem de identidades, mas dentro da carga, com `Definitions` contextuais, áudio exato, destino herdado e formas Core depois do lema no mesmo deck ID.
5. Fonte/licença, privacidade, custo e quality review têm decisão por idioma antes do freeze.
6. `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` passam separadamente para `pl`, `ru`, `cs`, `hr` e `el`; adapter genérico ou LLM judge isolado não pode suprimir blocker de idioma.

### Fase 43: Rollout aglutinativo

**Resultado:** `tr`, `fi` e `hu` possuem planos completos e amostras verticais que analisam cadeias morfológicas sem heurística de sufixo.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos três idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato em identidades/headwords, reserva, todas as `Important Forms` Core aprovadas no nível do pai, Expansion opt-in de identidades, coverage report, amostra, voz/áudio e revisão humana;
- para cada idioma aglutinativo, manifests/datasets e casos positivos/negativos de `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, incluindo cadeias longas, derivação/flexão, harmonia, pronúncia e limites de consumo;
- cadeias de sufixos, harmonia, casos, derivação versus flexão, gradação, posse e sistemas de conjugação;
- regras locale-aware turcas, gradação finlandesa e conjugação definida/indefinida húngara;
- amostra diagnóstica vertical de 90 cards por idioma (270 no total), sem cap de cards no inventário completo;
- planos de áudio/voz, sequência lema->formas, herança de destino e reports `LOAD-01` total/per-level e por fonte, com revisão de análises longas/ambíguas.

**Critérios de saída:**

1. Os três idiomas atingem o mínimo de 200 goldens e o checklist completo.
2. Derivação não é fundida com flexão e cadeias não são resolvidas por suffix stripping.
3. Formas importantes justificadas mantêm análise, destino do pai, mesmo deck ID de Core, dependência depois do lema e carga reportada; burying nativo só é exigido se a topologia selecionada usar a mesma nota, caso contrário a alternativa nomeada/testada evita exposição concorrente sem chamar notas separadas de siblings; não viram Expansion.
4. As 270 amostras passam identidade/sentido/MWE/rota/target matching com falha fechada.
5. Privacidade, licença, custo computacional e qualidade permitem ou bloqueiam cada profile.
6. `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` passam separadamente para `tr`, `fi` e `hu`; nenhuma heurística comum ou decisão exclusiva de LLM pode liberar um profile falho.

### Fase 44: Rollout do Leste Asiático

**Resultado:** `ja`, `zh` e `ko` possuem planos completos e amostras verticais com segmentação, leitura, morfemas e scripts específicos.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos três idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato em identidades/headwords, reserva, todas as `Important Forms` Core aprovadas no nível do pai, Expansion opt-in de identidades, coverage report, amostra, voz/áudio/leitura e revisão humana;
- para `ja`, `zh` e `ko`, manifests/datasets e casos positivos/negativos de `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, incluindo leitura/polifonia, segmentação, morfemas, scripts e limites de contexto privado;
- japonês com lema/POS/leitura UniDic; Mandarim com segmentação, Simplificado/Tradicional e polifonia; coreano com NFC/Kiwi/assinaturas de morfema;
- roteamento de partículas, auxiliares, classifiers, endings e demais itens gramaticais;
- política revisada de regeneração coreana português-v3 para inglês-v4, sem relabel;
- amostra diagnóstica vertical de 90 cards por idioma (270 no total), sem cap do inventário completo, mais planos de áudio/leitura, sequência lema->formas e reports `LOAD-01` total/per-level e por fonte.

**Critérios de saída:**

1. Os três idiomas atingem o mínimo de 200 goldens e o checklist completo.
2. UniDic, fronteiras chinesas/polifonia e Kiwi/NFC passam casos positivos/negativos sem fallback por espaço.
3. Variantes de script/leitura preservam identidade/proveniência; formas preservam o destino do pai, e Grammar recebe somente identidades/papéis de fundação já roteados a ela, nunca formas de Core por conveniência.
4. A política coreana define regeneração e review; conteúdo v3 em português permanece intacto até migração confirmada.
5. As 270 amostras e planos de provider satisfazem gates de privacidade, licença, custo e qualidade.
6. `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` passam separadamente para `ja`, `zh` e `ko`; UniDic/Kiwi/segmentador ou LLM judge de outro idioma não dispensa falha local.

### Fase 45: Freeze multilíngue

**Resultado:** O Core moderno fica congelado em exatamente 66.000 identidades aprovadas e 66.000 cards headword padrão, enquanto form packs obrigatórios elevam intencionalmente a contagem variável de cards e Expansion permanece um inventário opt-in separado, sem drift de hash.

**Depende de:** Fases 40, 41, 42, 43 e 44.

**Entregáveis:**

- 3000 identidades e 3000 cards headword padrão por cada um dos 22 idiomas, em bandas disjuntas de 1000 identidades/headwords por nível;
- validação global contra POS desconhecido, identidade duplicada, sentido ambíguo e contaminação por idioma/script;
- licenças, atribuições, source manifests, analyzer/profile versions, ranks e hashes congelados;
- policies/evidências assinadas e imutáveis por idioma para `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, incluindo datasets de referência, thresholds/drift, pronunciation signatures, render/trust policies, bundle Core canônico por `deck_edition_id` e diffs de conteúdo;
- reservas e form packs versionados como datasets ligados à identidade-pai, nunca como subdecks; toda forma Core aprovada congela análise, razão, nível/deck ID herdado e ordem depois do lema, fora da quota de identidades e dentro do workload;
- Expansion configurável e opt-in de 0–3000 identidades por idioma, com proveniência própria, headwords/formas/papéis opcionais reportados separadamente e diff de Core;
- manifest `LOAD-01` por idioma com Core identity count, 3000 headwords, `N`, cada `O`, total computado e reconciliação para Level 1/2/3; nenhum freeze, edição ou sample pode capar o total em 3000 cards;
- segunda revisão humana obrigatória, independente da primeira passagem.

**Critérios de saída:**

1. A soma é exatamente 66.000 identidades e 66.000 headwords padrão; cada idioma valida 3000 identidades/headwords e três bandas de 1000 IDs únicos, separadamente do total de cards.
2. Unknown POS, duplicata, ambiguidade não resolvida ou foreign contamination têm contagem zero entre aceitos.
3. Toda identidade possui licença/manifest/curadoria aprovados; direito pendente bloqueia o idioma/release.
4. Form packs não alteram a contagem de identidades, mas todas as formas Core aprovadas elevam e reconciliam a contagem de cards/workload total e por nível; expansões 0/intermediária/3000 não mudam nenhum Core hash e não absorvem formas Core.
5. Segunda revisão, métricas de qualidade, custo de rebuild e privacidade/proveniência passam antes do freeze assinado.
6. `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` têm policy/hash/dataset/review assinados por todos os 22 idiomas; rank não reproduzível, workload incompleto, signature insegura, conteúdo não canônico ou regressão além do threshold invalida o freeze.

### Fase 46: Edições e exportação

**Resultado:** Edições versionadas implementam somente a topologia selecionada por `ANKI-01` e exportam notes/cards com identidade semântica estável e subdecks reais, permitindo updates 1:1 sem conflar níveis, papéis ou dados pessoais.

**Depende de:** Fase 45.

**Entregáveis:**

- implementação exclusiva do modelo/version `ANKI-01` assinado, distinguindo note GUID, generated card identity/template ordinal, aliases e scheduling; nenhum branch de candidate rejeitada permanece como fallback;
- identidade semântica de forma conforme `FORM-04`/`DISPLAY-01`: parent ID, role, surface/analysis/sense/context IDs, display cue, prerequisite e dynamic add/remove sem trocar rank, real deck ID ou consumir identidade;
- GUID por identidade + card role + form analysis conforme `GUID-01`, com alias apenas quando provado;
- topology real com `{language}::Frequency::Level 1`, `{language}::Frequency::Level 2` e `{language}::Frequency::Level 3`, além dos destinos aprovados Grammar, Expansion, Custom e Highlight; não existe destino top-level separado para `Important Forms`, que preservam exatamente o deck ID do pai;
- module tags suplementares, módulos de 50–200, mixed editions e manifests de composição;
- APKG e manifests CSV/TSV com identidade/fonte do pai, card role, form analysis, deck ID herdado, sequência, mídia resolvível, `Image` vazio e model/deck IDs isolados;
- 3000 cards headword de Core por idioma, toda forma Core aprovada como card adicional obrigatório e opcionais reverse/listening/cloze ainda desabilitados salvo edição explícita;
- reports de export que reconciliam Core identities/headwords/`N`/cada `O`/total por Level 1/2/3 e reportam Expansion identities/headwords/forms/opcionais/total separadamente;
- migração estrutural do baseline one-row/one-`genanki.Note`/one-`Card 1`/single-deck para o modelo selecionado, com aliases para GUIDs atuais que incluem `job_id`/`sort_index` somente quando o mapping 1:1 for provado;
- testes `ANKI-01`/`FORM-04`/`DISPLAY-01` de mesmo deck ID lema-forma, ordem/prerequisite, add/remove dinâmico, ausência de reroute, import/reimport/update/alias, scheduling, collision/duplication, burying nativo quando mesma nota ou alternativa honesta quando notas separadas, e round-trip em todos os clientes suportados.

**Critérios de saída:**

1. `ANKI-01` prova em cada cliente a topologia selecionada, note/card identity, update/alias, scheduling e burying nativo ou alternativa honesta; a inspeção também prova Level 1/2/3 e nenhum forms subdeck.
2. Mesma semântica mantém GUID; mudança de texto/rank/provider não o troca; role/análise diferente gera GUID distinto.
3. Update 1:1 preserva nota e scheduling em fixtures suportadas sem duplicação.
4. `FORM-04`/`DISPLAY-01` preservam IDs de parent/form/analysis/sense/context, prompt não ambíguo, dynamic forms, blank `Image`, fórmulas e sequência; toda forma Core compartilha o deck ID do lema e dados pessoais permanecem isolados.
5. Licenças/atribuições, tamanho/custo e qualidade de APKG/CSV/TSV bloqueiam artefato incompleto.
6. `ANKI-01`, `FORM-04` e `DISPLAY-01` passam migration fixture a partir do exporter atual, import/reimport/update e round-trip nos quatro clientes; qualquer duplicação, alias incerto ou perda de scheduling bloqueia a edição.

### Fase 47: Histórico Anki somente de leitura

**Resultado:** Um importador APKG local e sandboxed deriva estado mínimo de aprendizagem de conteúdo Multilang sem abrir nem escrever coleções vivas.

**Depende de:** Fase 46.

**Entregáveis:**

- importador local de scheduling APKG com limites de path, members, tamanho, razão de compressão, tempo, CPU/memória e SQLite;
- cópia read-only e proibição técnica de AnkiConnect, coleção viva e qualquer write no pacote;
- mapping apenas de identidade/review Multilang sob o modelo `ANKI-01` selecionado, distinguindo note GUID, generated card identity/template ordinal e legacy mapping incerto; `DISPLAY-01` preserva quando comprovados `card_role`, parent/form/analysis/sense/context IDs, inventário/destino e relação lema-forma, com confiança, proveniência, quarentena e schema drift;
- learner states minimizados; raw package e conteúdo extraído apagados conforme retenção;
- cold start, corrupção, archive bomb, traversal e formato não suportado;
- segunda revisão independente de privacidade e segurança.

**Critérios de saída:**

1. Hashes antes/depois comprovam zero escrita e nenhuma chamada de coleção/AnkiConnect existe.
2. Somente records mapeáveis sob `ANKI-01` alimentam learner state; `DISPLAY-01` diferencia note/card/role/form analysis, forma mapeada não recebe membership novo nem muda de destino, e qualquer legacy mapping ambíguo fica em quarentena sem transferir scheduling.
3. Raw package/content é removido no prazo aprovado e exclusão é verificável.
4. Cold start é funcional; corrupção/ataque falha dentro dos limites sem vazamento/exaustão.
5. Privacy/security second review, termos de pacote/schema, custo de processamento e qualidade do mapping passam.

### Fase 48: Ranking adaptativo

**Resultado:** A prioridade adaptativa é explicável e determinística, separada do rank editorial e do bundle canônico `CONTENT-01`, e organiza módulos/formas sem alterar histórico importado nem conteúdo Core compartilhado.

**Depende de:** Fases 45 e 47.

**Entregáveis:**

- diagnostics, marcação de itens conhecidos, metas e history signals minimizados;
- rank editorial imutável e adaptive priority versionada separados;
- enforcement `CONTENT-01` por `deck_edition_id`: learner signals alteram exclusivamente queue/module/order/eligibility e não regeneram/mutam definição, exemplo, tradução, pronunciation signature/áudio, content version, GUID, rank, render policy ou asset Core assinado;
- namespaces privados de Custom/Highlight continuam adaptáveis e isolados, com conteúdo/versionamento próprios que nunca sobrescrevem o bundle Core;
- modos `core_first`, `balanced` e `reading_first`, com explicação por componente;
- prerequisite eligibility, Expansion opt-in somente para identidades adicionais e proveniência pessoal para Custom/Highlight; cards de forma herdam o inventário já habilitado do pai;
- módulos determinísticos de 50–200 itens;
- `Important Forms` de Core no mesmo nível/deck ID do lema, depois dele, com burying nativo somente se cards da mesma nota forem o modelo `ANKI-01` selecionado ou alternativa nomeada/testada para notas separadas, além de workload variável conforme `DEPEND-01`/`LOAD-01`; nenhuma policy pode deferi-las para preservar 3000 cards;
- relatórios de fila que mantêm Core identities/headwords/`N`/cada `O`/total por nível e Expansion identities/headwords/forms/opcionais separados;
- cold start, reset, override, audit e invalidação de policy.

**Critérios de saída:**

1. Snapshot/policy iguais produzem mesma fila, módulos e explicação.
2. `CONTENT-01` prova por hashes/diffs que nenhum modo muda Core rank, GUID, membership, deck ID, content version, definição, exemplo, tradução, áudio ou asset assinado; Expansion exige opt-in de identidade.
3. Forma não fica elegível antes do lema, forma Core permanece no mesmo nível real e a topologia selecionada prova burying nativo ou a alternativa honesta de não exposição concorrente; notas separadas nunca são chamadas de siblings.
4. Reset/cold start removem adaptação sem apagar conteúdo/histórico; override é reversível/auditável e correção material de Core exige nova edição `CONTENT-01`, diff e review, nunca mutation learner-specific.
5. Sinais pessoais respeitam consentimento; custo computacional, efeitos e qualidade passam benchmarks/review.

### Fase 49: `Definitions`, sentenças, i+1 e áudio exato

**Resultado:** Conteúdo final Core combina identidade, sentido, forma e morfologia de modo canônico por edição, learner-independent sob `CONTENT-01`; conceitos conhecidos pessoais condicionam somente conteúdo privado de Custom/Highlight, enquanto `DISPLAY-01`, `AUDIO-02`, `AISEC-01` e `EVAL-01` protegem renderização, áudio, confiança e release.

**Depende de:** Fases 45 e 48.

**Entregáveis:**

- geração/curadoria Core edition-wide condicionada por identidade, sentido, forma, analysis e inventário/destino herdado, materializando uma única versão compartilhada `CONTENT-01`; known concepts pessoais só podem condicionar conteúdo privado de Custom/Highlight em namespace isolado;
- `Definitions` concisas com gramática contextual, inclusive distinção entre indicativo e irrealis em `were`;
- sentenças naturais com target matching sense-aware e policy strict/adaptive/contextual i+1;
- casos contextualizados `be/is/was/were` e formas equivalentes por idioma, mantendo cada análise aprovada no deck ID do lema, depois dele, com GUID/conteúdo/áudio próprios e contagem individual em `N`;
- render `DISPLAY-01` com parent/form/analysis/sense/context IDs, prompt/cue inequívoco, answer schema e escaping/allowlist versionados;
- `Exact-form audio` e áudio da sentença exata sob `AUDIO-02`, com pronunciation signature completa, artifact integrity, cache, hashes, locale/voz/SSML/provider/model e review;
- geração grounded `AISEC-01`: isolamento/redaction de Custom/Highlight/corpus, instruções embutidas como dados, limits antes de provider, contexto mínimo, output LLM tipado/escaped e rejeição de script/handler/URL/markup ativo;
- materialização do bundle `CONTENT-01` assinado com definições, exemplos, traduções, signatures/assets, render policy e review, mais diff machine-readable para correções;
- suites/review `EVAL-01` por idioma e estrato para definição, forma, naturalidade, target/sense, tradução, i+1, pronúncia/áudio e HTML/Anki safety;
- materialização obrigatória de toda forma Core aprovada sem cap de 3000 cards, preservando os destinos de Expansion/Custom/Highlight/Grammar/foundation dos respectivos pais;
- rate limits, retries, budgets/hard caps, idempotência e drift invalidation calculados sobre a carga real de cards.

**Critérios de saída:**

1. Toda saída `DISPLAY-01`/`CONTENT-01` aprovada casa identidade, sentido, análise, alvo, edição e namespace; ambiguidade, target ausente ou tentativa de personalizar Core falha fechado.
2. `DISPLAY-01` prova que `is`, `was` e os dois usos de `were` têm prompt/contexto/gramática/análise/GUID corretos, contam separadamente quando aprovados e compartilham o nível/deck ID de `be` depois do headword.
3. i+1 nunca sacrifica naturalidade; strict exige exatamente o desconhecido permitido e os demais modos declaram incidental concepts.
4. `AUDIO-02` casa a pronunciation signature completa com forma/contexto/sentença e artefato íntegro; text-only cache é rejeitado e drift invalida conteúdo/asset dependente.
5. `AISEC-01` bloqueia injection/disclosure/HTML ativo, `CONTENT-01` mantém Core canônico e `EVAL-01` combina validators com review independente; LLM judge nunca aprova sozinho.
6. `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` passam seus datasets/thresholds/drift e evidência de release; qualquer falha estrutural/segurança é bloqueante a 100%.

### Fase 50: Ensaio de migração

**Resultado:** A migração `ANKI-01` do exporter atual para o modelo semântico selecionado é integralmente ensaiada em clone restaurado, com aliases, dinâmica `FORM-04`/`DISPLAY-01`, prévia assinada e rollback provado, sem mutation viva.

**Depende de:** Fases 46, 47, 48 e 49.

**Entregáveis:**

- inventário factual do source baseline: uma instância de `genanki.Deck`, um `genanki.Note` por row, um template `Card 1`, um card por nota e GUID input contendo `job_id`/`sort_index`, além de tokens, ranks, IDs/GUIDs, roles/analyses, parent destination, schemas, assets, mídia e scheduling mappings antigos;
- classificação `1:1`, `merge`, `split`, `drop` ou `unresolved` por mapping, com confiança e perdas;
- prévia assinada vinculada aos hashes de source, target e backup, incluindo por idioma: Core identities, 3000 headwords, `N`, cada `O`, total computado, reconciliação Level 1/2/3 e, separadamente, Expansion identities/headwords/forms/opcionais/total, além de espaço, custo e mudanças de idioma;
- diff `ANKI-01` entre source baseline e topologia selecionada, distinguindo note GUID/card identity/template ordinal e cobrindo new job/rank drift, aliases 1:1, splits/merges, update/duplication, scheduling e cliente;
- diff `FORM-04`/`DISPLAY-01` que prova parent/form/analysis/sense/context identity, deck ID herdado, lema antes das formas, add/remove dinâmico e ausência de reroute para Expansion, Grammar ou forms subdeck;
- ensaio **somente** em clone restaurado e isolado;
- reuse de GUID antigo apenas em mapping 1:1 provado;
- proibição de transferir ou apagar scheduling em mapping ambíguo;
- fixtures separados para Anki Desktop atual/anterior suportado, AnkiDroid atual e AnkiMobile atual, com preservação isolada/non-transfer ambígua de scheduler, interruption/resume, journal, rollback, idempotência e unresolved blocking.

**Critérios de saída:**

1. Banco/config/assets vivos e Anki permanecem byte a byte intocados; toda mutation ocorre no clone.
2. `ANKI-01` reconcilia source/current GUIDs, note/card identity, aliases, job/rank drift, scheduling e clientes; `FORM-04`/`DISPLAY-01` reconciliam formas dinâmicas, prompts/analyses, totals, destinos e sequência; divergência invalida a assinatura.
3. Somente alias 1:1 provado reutiliza GUID/scheduling; merge/split/drop/unresolved não transfere/apaga review, e add/remove de forma ambíguo preserva o estado anterior.
4. Interrupção retoma pelo journal, rollback restaura hashes e segunda execução é no-op idempotente.
5. Regeneração coreana, exceção inglesa, Latim isolado, privacidade, licenças, custos e thresholds são auditados; unresolved bloqueia a Fase 51.
6. `ANKI-01`, `FORM-04` e `DISPLAY-01` passam apply/rollback e round-trip em cada fixture de cliente; collision, duplication, semantic alias incerto ou scheduling loss bloqueia o rehearsal.

### Fase 51: Preflight, aplicação confirmada e release

**Resultado:** A instalação viva só migra após preflight completo e confirmação hash-bound; aplicação transacional, postflight, rollback e rollout gradual produzem release auditável.

**Depende de:** Fase 50.

**Entregáveis:**

- preflight estrutural/vertical `ANKI-01` da topologia selecionada, clientes, privacidade, licença, custo, espaço, backup e qualidade antes de qualquer apply, incluindo fórmulas, note/card identities, aliases, scheduling e topology herdada;
- verificação de hashes/assinaturas do bundle canônico `CONTENT-01`, output seguro `AISEC-01`, pronunciation signatures/artefatos `AUDIO-02` e datasets/thresholds/regression drift `EVAL-01` por idioma;
- prévia da Fase 50 revalidada contra source/target/backup atuais;
- confirmação explícita do usuário vinculada aos hashes e ao resumo de mappings/perdas/custo;
- transação de banco e staging de assets com switch atômico, journal e checkpoints;
- postflight, rollback automático/manual e reconciliação de IDs/GUIDs/mídia/scheduling, Core identities/headwords/`N`/cada `O`/total por nível e contagens separadas de Expansion;
- validação `ANKI-01` separada no Anki Desktop atual/anterior, AnkiDroid atual e AnkiMobile atual, incluindo import/reimport/update/round-trip, aliases, dynamic forms, scheduling e burying nativo ou alternativa honesta;
- pilots seguidos por famílias linguísticas, monitorando retention, leeches, time/item e abandonment;
- auditoria final do milestone, limitações e decisão separada de release/promoção.

**Critérios de saída:**

1. A sequência **prévia -> backup -> confirmação explícita** é tecnicamente obrigatória e a confirmação expira com qualquer hash/drift.
2. Nenhum apply começa antes de todos os checks; DB/assets mudam atomicamente ou rollback restaura o estado anterior.
3. Mappings 1:1 `ANKI-01` preservam IDs/GUIDs/scheduling, parent inventory/deck ID, form role/análise e sequência; ambiguidades permanecem bloqueadas sem perda silenciosa.
4. Todos os quatro clientes-alvo passam separadamente sob `ANKI-01`; um resultado não substitui outro, e topology/client failure bloqueia release.
5. `CONTENT-01` preserva hashes canônicos, `AISEC-01` bloqueia output inseguro/disclosure, `AUDIO-02` reconcilia signatures completas e `EVAL-01` fica dentro de threshold/drift por idioma; qualquer falha bloqueia release.
6. Postflight, rollback drill, monitoramento e auditoria não têm bloqueante aberto antes do release.
7. `ANKI-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` possuem evidência de preflight/postflight e monitoring/revocation; nenhuma aprovação genérica ou LLM-only substitui o resultado requerido.

## 6. Contratos de gates transversais

### Gate de privacidade

**Evidência de entrada:** `AISEC-01` fornece trust map de Custom/Highlight/corpus, separação controle-conteúdo, limites versionados, contexto mínimo autorizado, no-secrets e schema/output policy; `CONTENT-01` fornece fronteira e hashes entre bundle Core canônico e namespaces privados, além de consentimento, finalidade, retenção/exclusão, acessos e threat model.

**Condições bloqueantes:** `AISEC-01` bloqueia consentimento/finalidade ausente, embedded instruction tratada como controle, limite/context minimization ausente, secret/raw private context em provider/audit ou output ativo não validado; `CONTENT-01` bloqueia mistura/overwrite entre Custom/Highlight e Core, regeneração Core por histórico, exclusão não verificável e APKG fora do sandbox read-only.

**Evidência de saída:** testes `AISEC-01` positivos/negativos provam delimitação tipada, minimização/redaction, injection inerte, output escaped/allowlisted e audit hash-only; testes `CONTENT-01` provam isolamento de storage/version namespace, Core hashes imutáveis sob adaptação e export/delete separados para Custom, Highlight e APKG, com aprovação do gate owner.

**Auditoria e retenção:** registrar para `AISEC-01`/`CONTENT-01` somente hashes, IDs, versions, counts, decisions e metadata sanitizada, mais consentimento/finalidade, acessos, subprocessadores, edição/namespace e evidência de exclusão; nunca prompt, resposta, secret ou texto privado bruto. Retenção/backup são mínimos, configuráveis e expurgáveis.

**Rollback/revogação:** revogação `AISEC-01` suspende provider/policy/capability, invalida prompts/caches e bloqueia novos jobs; revogação `CONTENT-01` remove sinal e derivados privados, preserva o bundle Core assinado e exige nova edição para correção compartilhada. Restore nunca reativa consentimento/namespace expirado nem muta Core por usuário.

### Gate de licença

**Evidência de entrada:** manifests e direitos de corpora/derivados `RANK-01`, evidências/form packs `FORM-04`, provider/voz/SSML/assets `AUDIO-02`, fontes/bundle de edição `CONTENT-01` e datasets/rubricas `EVAL-01`, todos com owner, versão/checksum, aquisição, finalidade, derivação/redistribuição, atribuição e revogação.

**Condições bloqueantes:** direito, atribuição, versão ou cadeia fonte->derivado indefinida bloqueia `RANK-01`, `FORM-04`, `AUDIO-02`, `CONTENT-01` ou `EVAL-01`; corpus privado não vira rank asset compartilhado, forma/dataset sem direito não congela, provider/áudio sem termos não sintetiza e bundle/reference dataset não é commitado/empacotado/publicado enquanto pendente.

**Evidência de saída:** decisões assinadas por fonte/version/finalidade/distribuição autorizam separadamente corpora/ranks `RANK-01`, evidence/form datasets `FORM-04`, signatures/assets `AUDIO-02`, Core editions `CONTENT-01` e reference suites `EVAL-01`; manifests ligam cada derivado/checksum/atribuição ao release permitido e testes preservam a cadeia no export.

**Auditoria e retenção:** manter termos/referência durável, reviewer/data/escopo, atribuições e cadeia source->`RANK-01`/`FORM-04`/`AUDIO-02`/`CONTENT-01`/`EVAL-01`->release durante a vida dos derivados e prazo legal, incluindo policy/provider/dataset versions sem armazenar conteúdo privado além do autorizado.

**Rollback/revogação:** revogar uma source/version bloqueia builds e localiza ranks `RANK-01`, forms `FORM-04`, audio `AUDIO-02`, editions `CONTENT-01` e suites `EVAL-01` derivados; releases são retirados/reconstruídos e evidência afetada perde aprovação. Restore não reintroduz corpus, asset, conteúdo ou dataset revogado sem nova decisão.

### Gate de custo

**Evidência de entrada:** forecast integral `FORM-04` de cards/audio/review/rebuild antes da aprovação, cardinalidade/cache por pronunciation signature `AUDIO-02` e limites `AISEC-01` de bytes/chars/tokens/records/rate/concurrency/retry/budget; dry-run usa Core identities, 3000 headwords, `N`, cada `O`, levels e Expansion separados, prices/version, storage/egress e hard caps.

**Condições bloqueantes:** `FORM-04` sem forecast completo, `AUDIO-02` sem full-signature cache/idempotency ou `AISEC-01` sem limites/preço/provider/budget bloqueiam a operação; cap ausente/excedido, retry ilimitado ou estimate baseado em 3000 cards também bloqueia. Cap interrompe antes da publicação e nunca trunca forma Core já aprovada.

**Evidência de saída:** `FORM-04` reconcilia workload aprovado com `LOAD-01`, `AUDIO-02` reconcilia signature hits/misses/bytes/calls e `AISEC-01` prova rate/concurrency/token/budget/retry caps; estimate/actual por identity/headword/form/role/level/source e confirmação nova quando exigida demonstram interrupção segura sem inventário truncado.

**Auditoria e retenção:** registrar `FORM-04` policy/workload hash, `AUDIO-02` provider/model/signature hash e `AISEC-01` limit-policy hash, unidades, counts, cache, retries e estimate/actual/decision sem secret ou payload; reter agregados pelo prazo financeiro e itemização somente enquanto necessária.

**Rollback/revogação:** revogar budget/policy cancela jobs `AISEC-01`, preserva checkpoint e retoma somente com aprovação nova; mudança `AUDIO-02` invalida apenas signatures incompatíveis; mudança `FORM-04` exige novo forecast/diff/review. Cards Core já aprovados não são truncados: o release inteiro permanece bloqueado até capacidade suficiente.

### Gate de qualidade

**Evidência de entrada:** todos os 20 contratos e, em especial, decisão/client matrix `ANKI-01`, manifests `RANK-01`, policies `FORM-04`/`DISPLAY-01`/`AUDIO-02`/`AISEC-01`/`CONTENT-01`, datasets/metrics/rubricas/thresholds/drift `EVAL-01`, validators determinísticos, samples/strata e plano de review humano/especialista independente.

**Condições bloqueantes:** candidate/client unresolved em `ANKI-01`; rank não reproduzível em `RANK-01`; forma/workload incorreto em `FORM-04`; prompt/identity ambíguo em `DISPLAY-01`; signature/asset divergente em `AUDIO-02`; injection/disclosure/HTML ativo em `AISEC-01`; Core learner-mutated em `CONTENT-01`; ou threshold/regression/review falho em `EVAL-01`. Checks estruturais/security/fail-closed são 100%-blocking e LLM judge nunca é sole approver.

**Evidência de saída:** `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01` possuem suites positivas/negativas, manifests/hashes, per-language metrics/strata e review independente; topology round-trip, deterministic ranks/forms/signatures, canonical hashes e 100% HTML/script blockers passam sem aprovação transitiva entre profiles.

**Auditoria e retenção:** reter decisões/versions/hashes e artefatos reproduzíveis de `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` e `EVAL-01`, incluindo datasets, analyzer/prompt/provider/policy, numerator/denominator, sample/strata, thresholds/drift e reviewer; mudança material invalida a suite afetada.

**Rollback/revogação:** falha/revogação em `ANKI-01`, `RANK-01`, `FORM-04`, `DISPLAY-01`, `AUDIO-02`, `AISEC-01`, `CONTENT-01` ou `EVAL-01` suspende profile/capability/release, quarentena derivados e restaura última versão compatível; correção gera nova decisão/version/diff/review, nunca sobrescreve evidência nem reduz blocker por média/waiver.

## 7. Dependências e caminho de promoção

Grafo normativo:

```text
G0 -> 35
35 -> 36, 37 and 38
36 + 37 + 38 -> 39
39 -> 40, 41, 42, 43 and 44
40 + 41 + 42 + 43 + 44 -> 45
45 -> 46
46 -> 47
45 + 47 -> 48
45 + 48 -> 49
46 + 47 + 48 + 49 -> 50
50 -> 51
```

Depois de os contratos da Fase 35 fecharem, fontes/cobertura e morfologia/curadoria podem avançar com ownership e write sets separados; a Fase 36 é inalcançável até a decisão `ANKI-01` da Fase 35 estar assinada, sem schema provisório, persistência de candidate ou bypass. Somente então os três ramos integram no piloto da Fase 39. As pesquisas e rollouts linguísticos das Fases 40–44 podem ser paralelos apenas com ownership por idioma/família realmente disjunto. Schema compartilhado, contratos, manifests, freeze, export e integração permanecem controlados e serializados nas arestas acima. Falha em qualquer gate transversal continua bloqueando a aresta correspondente mesmo quando a dependência funcional anterior terminou.

O caminho de promoção possui duas decisões humanas que não se confundem com a escrita deste documento:

1. **Prontidão para planejar/implementar:** depois de a v3.0 terminar e G0 produzir evidência, uma ação separada pode aprovar alterações em `.planning/SPEC.md` e `.planning/ROADMAP.md` e autorizar a Fase 35. Sem essa ação, a proposta permanece não ativa.
2. **Aceite da baseline/release v4:** depois da Fase 51, outra decisão separada avalia evidência integrada, riscos e limitações antes de declarar a v4 como baseline/release ativa.

Persistir este arquivo não executa nenhuma dessas decisões. O planejamento ativo só é editado por seu workflow aprovado, nunca como efeito colateral desta proposta.

## 8. Auditoria final de rastreabilidade e cobertura

### 8.1 Decisões fixas

| Decisão fixa | Fase(s) principal(is) | Evidência posterior | Status |
|---|---|---|---|
| D-01 | G0 e 51 | Diff de escopo prova documento isolado; promoção possui decisão separada | Coberto |
| D-02 | G0 e 35–51 | Manifest de fases e gates contém G0 mais todas as 17 fases numeradas | Coberto |
| D-03 | 35 e 39–45 | Contratos, piloto, cinco rollouts e freeze contam 22 perfis modernos; `la` permanece isolado | Coberto |
| D-04 | 35, 39–44, 49–51 | Policies, amostras, conteúdo e migração provam inglês/português e transição coreana | Coberto |
| D-05 | 35, 37, 39–46, 48, 50 e 51 | Contagens distinguem 3000 identidades/3000 headwords do total variável pelas fórmulas total/per-level; freeze prova 66.000 identidades e Expansion opt-in sem drift | Coberto |
| D-06 | 35, 36, 38 e 45 | Contrato, persistência, goldens e freeze comprovam identidade versionada | Coberto |
| D-07 | 35, 38–46, 48–51 | `FORM-04`/`DISPLAY-01`/`AUDIO-02` ligam toda forma aprovada à análise, prompt/cue, áudio, destino do pai, forecast e sequência depois do lema | Coberto |
| D-08 | 35, 38–51 | Goldens/rollouts/edições/migração provam MWE, sentido, fonte/inventário do pai, rota e card role separados, sem recategorizar forma como identidade | Coberto |
| D-09 | 35, 46, 48 e 49 | `CONTENT-01` fixa Core canônico por edição; adaptação pessoal altera somente fila e Custom/Highlight permanecem privados | Coberto |
| D-10 | 47 | Hashes antes/depois, parser read-only e mappings com confiança/quarentena | Coberto |
| D-11 | 48 | Scores explicados, reset/override e diffs nulos em rank, histórico, GUID e bundle Core `CONTENT-01` | Coberto |
| D-12 | 35, 38–46, 48, 50 e 51 | `ANKI-01` seleciona por prova real a topologia; Level 1/2/3, deck ID, prerequisite e burying nativo ou alternativa honesta são testados | Coberto |
| D-13 | 36, 50 e 51 | Backup/restore, rehearsal-only, confirmação hash-bound, apply e rollback | Coberto |
| D-14 | G0 e 35–51 | Matriz de gates inclui `AISEC-01`, evidence/retention/revocation e bloqueios sem waiver implícito ou sole LLM judge | Coberto |
| D-15 | G0 e 51 | Ausência de alteração ativa e registros separados de promoção/release | Coberto |
| D-16 | 35, 36, 39, 46, 47, 50 e 51 | `ANKI-01` compara ambos os modelos em quatro clientes, assina um, bloqueia persistence anterior e prova aliases/update/scheduling/round-trip | Coberto |
| D-17 | 35, 37, 39–45 | `RANK-01` versiona corpora/pesos/alocações/dispersão/MWE/fórmula/tie-break e reproduz ranks/hash com diff de drift | Coberto |
| D-18 | 35, 38–46, 50 e 51 | `FORM-04` aplica score/thresholds/dedup/order/forecast e impede truncamento de toda forma Core aprovada | Coberto |
| D-19 | 35, 38–51 | `DISPLAY-01` preserva parent/form/analysis/sense/context IDs, prompts inequívocos e same-spelling analyses distintos | Coberto |
| D-20 | 35, 38–45, 49 e 51 | `AUDIO-02` exige pronunciation signature integral, artifact integrity e casos heterófonos/polifônicos sem text-only reuse | Coberto |
| D-21 | G0, 35, 39–45, 49 e 51 | `AISEC-01` isola controles/dados, limita consumo/contexto, valida/escapa output e audita hashes sem autoridade lexical do LLM | Coberto |
| D-22 | 35, 39–45, 48, 49 e 51 | `CONTENT-01` assina bundle Core learner-independent, permite só queue/module/order/eligibility e isola Custom/Highlight | Coberto |
| D-23 | G0, 35, 39–45, 49 e 51 | `EVAL-01` versiona datasets/métricas/rubricas/thresholds/drift e combina validators com review independente, nunca LLM-only | Coberto |

### 8.2 Capacidades e fases responsáveis

| Capacidade | Fase responsável | Dependências | Evidência de saída |
|---|---|---|---|
| 20 contratos explícitos CARD/FORM/SENSE/MWE/ROUTE/DEF/AUDIO/LOAD/DEPEND/GUID/ANKI/RANK/DISPLAY/AISEC/CONTENT/EVAL | 35 | G0 | Manifest contém exatamente os 20 IDs, fórmulas/defaults, cenários positivos/negativos, owners, blockers e evidência requerida |
| Topologia de note/card (`ANKI-01`) | 35 decide; 36 persiste; 46 implementa; 47 mapeia; 50 migra; 51 libera | G0 e decisão real-client da 35 | Dois candidates comparados sem preselection; modelo assinado prova note/card identity, aliases, update, scheduling, prerequisite/burying-or-alternative e round-trip por cliente |
| Ranking agregado (`RANK-01`) | 37; validação 39–45 | Contratos/fontes | Corpus manifests, weights, shares/confidence, quarantine, MWE dedup, fórmula/precision/tie-break e rank/manifest hashes reproduzíveis |
| Policy de formas (`FORM-04`) | 38; validação 39–46/50–51 | `RANK-01` e analyzers | Score/thresholds/dedup/order/forecast versionados; todas as formas Core aprovadas são obrigatórias sem truncamento |
| Display semântico de forma (`DISPLAY-01`) | 38; implementação 46/49; mapping/migração 47/50–51 | `FORM-04` e `ANKI-01` | Parent/form/analysis/sense/context IDs, prompt/cue inequívoco, exact answer/audio e same-spelling analyses distintos |
| Pronunciation signature (`AUDIO-02`) | 38 evidencia; 45 congela; 49 materializa; 51 valida | `DISPLAY-01` e provider/licença | Assinatura contextual completa + artifact integrity controlam cache; heterófonos/polifonia recusam text-only hash |
| Segurança de geração/output (`AISEC-01`) | 35 contrata; 39–45 valida; 49 implementa; 51 preflight | Privacy/license/cost gates | Untrusted data isolado, limits/context minimization, typed validation, escaping/allowlist, hash-only audit e LLM não autoritativo |
| Conteúdo Core canônico (`CONTENT-01`) | 35 contrata; 45 congela; 48 limita adaptação; 49 materializa; 51 valida | Edição assinada e gates | Bundle Core por `deck_edition_id` não muda por learner history; Custom/Highlight usam namespaces privados e correção cria diff/new edition |
| Avaliação multilíngue (`EVAL-01`) | G0 baselines; 35 thresholds; 39–45/49 suites; 51 release | Datasets/licenças e policies | Reference hashes, metrics/rubrics/strata/thresholds/drift, deterministic blockers e independent specialist review sem sole LLM judge |
| Migração exporter atual -> modelo selecionado | 36 baseline; 46 compatibility; 50 rehearsal; 51 apply | `ANKI-01`, `GUID-01`, `FORM-04`, `DISPLAY-01` | One-row/one-`genanki.Note`/one-`Card 1`/single-deck e GUID `job_id`/`sort_index` são reconciliados por aliases/tests, não declarados v4-compliant |
| Persistência e backups | 36 | 35 | Restore, ORM/Alembic parity, fingerprints, parent inventory/level/destination e estruturas inativas sem membership de forma |
| Perfis e política de idioma | 35, 36 e 38–44 | G0 e contratos | 22 perfis qualificados individualmente; `la` persistido somente no caminho isolado |
| Registry de fontes/licenças e coverage | 37 | 35 | Pools de identidades >3000, corpora held-out, relatórios de identidades 1k/2k/3k/expansão e direitos auditados |
| Identidade lexical estável | 36, 38 e 45 | contratos/persistência | IDs reproduzíveis, sentidos separados e freeze sem duplicatas |
| Morfologia e target matching | 38 | 35 | 120/200 goldens, precisão aceita 100%, resolução >=98% e ambiguidade fail-closed |
| Piloto representativo | 39 | 36, 37 e 38 | 800 identidades candidatas offline, fan-out variável de cards, destino herdado, sequência, todos os contratos e estimates/invalidation testados |
| Rollout românico | 40 | 39 | Cinco planos, 450 cards diagnósticos e projeções `LOAD-01` sem cap de export |
| Rollout germânico | 41 | 39 | Seis planos, 540 cards diagnósticos e formas no mesmo nível do pai |
| Rollout eslavo/grego | 42 | 39 | Cinco planos, 450 cards diagnósticos e herança de destino/análise |
| Rollout aglutinativo | 43 | 39 | Três planos, 270 cards diagnósticos e formas depois do lema |
| Rollout do Leste Asiático | 44 | 39 | Três planos, 270 cards diagnósticos e Grammar sem absorver formas Core |
| Núcleo `Core 3x1000` | 45 | 40–44 | 66.000 IDs e 66.000 headwords, 3000/3000 por idioma e 1000/1000 por nível, mais cards de forma/opcionais reconciliados |
| Expansão opcional | 45 | 40–44 | Somente 0–3000 identidades adicionais opt-in, sem padding/Core drift; headwords/formas/opcionais reportados separadamente |
| `SurfaceForms`, `Important Forms` e workload | 35, 38–46 e 48–51 | identidade/analyzers | Seleção justificada, fora da quota de identidades, card Core obrigatório no mesmo deck ID depois do lema, herança para outras fontes e contagens por nível |
| Reconhecimento padrão e papéis opcionais | 35, 45 e 46 | contratos/freeze | 3000 headwords Core por idioma; reverse/listening/cloze desabilitados por padrão e contabilizados somente quando habilitados |
| MWE/sentido/rota/card role | 35, 38–51 | contratos/analyzers/rollouts | Rotas reproduzíveis resolvem fonte/inventário/nível antes do papel; ambiguidade e reroute são bloqueados |
| GUID, edições e subdecks reais | 35, 36 e 46 | `ANKI-01`/contratos/freeze | Modelo selecionado distingue note/card identity, GUID semântico, aliases, mixed updates, Level 1/2/3, mesmo deck ID e nenhum forms destination |
| Listas personalizadas | 35, 46, 48 e 49 | profile/export/adaptação/conteúdo | Proveniência privada, subdeck, prioridade e output isolado/redigido |
| Highlights | 35, 46, 48 e 49 | profile/export/adaptação/conteúdo | Contexto mínimo, provenance, subdeck e provider opt-in |
| Histórico APKG read-only | 47 | 46 | Parser sandboxed, raw deletion, zero escrita e mapping de identidade/form role/análise/destino com quarentena |
| Fila adaptativa | 48 | 45 e 47 | `CONTENT-01` limita sinais a queue/module/order/eligibility; módulos/prerequisites/reset preservam Core content/GUID/rank/edition hashes |
| `Definitions`, sentenças e i+1 | 49 | 45 e 48 | Core meaning-first/sense-aware canônico por edição; known concepts condicionam somente Custom/Highlight privados |
| Áudio da forma/frase exatas | 49 | 45 e 48 | `AUDIO-02` liga pronunciation signature completa a artifact integrity, cache, metadata, budget e review |
| Ensaio de migração | 50 | 46–49 | `ANKI-01` preview/aliases parte do exporter atual; `FORM-04`/`DISPLAY-01` cobrem dynamic forms, scheduling e rollback por cliente |
| Apply e release | 51 | 50 | Pre/postflight valida topology/client, canonical edition, secure output, signatures, evaluation drift, migration reconciliation e monitoring |

### 8.3 Aplicação dos gates por fase

| Fase | Privacidade | Licença | Custo | Qualidade |
|---|---|---|---|---|
| G0 | Baseline `AISEC-01` inventaria trust/privacy/consent e separa Core/private | Direitos de corpus/audio/content/eval têm source/version/checksum | Budgets/limits partem de workload real e fixtures | `ANKI-01`/`GUID-01` source baseline e datasets/threshold evidence `EVAL-01` aprovados sem claim v4 |
| 35 | `AISEC-01`/`CONTENT-01` fecham trust e namespaces | Direitos entram nos 20 contratos/policies | `FORM-04` forecast, `AUDIO-02` cache e `AISEC-01` caps contratados | Todos os 20 e dois `ANKI-01` prototypes/client results fecham ou bloqueiam 36 |
| 36 | Backup/access/retention protegem IDs `ANKI-01` | Proveniência/aliases sobrevivem ao selected schema | Storage/migration estimate cobre note/card model escolhido | `ANKI-01` assinado precede schema; restore/parity provam somente candidate selecionada |
| 37 | `RANK-01` minimiza/isola corpora privados | Corpora/derivados/weights têm direito e checksum | Acquisition/allocation/scoring/storage têm caps | `RANK-01` reproduz shares, MWE dedup, formula/order e manifest hash |
| 38 | Review de `FORM-04`/`DISPLAY-01`/`AUDIO-02` retém mínimo | Analyzer/evidence/form/audio policy têm termos | Forecast forms e contextual audio/review é integral | `FORM-04` approvals, `DISPLAY-01` cues e `AUDIO-02` signatures passam goldens/fail-closed |
| 39 | `AISEC-01` mantém piloto offline/private-safe | Somente sources/policies/datasets aprovados entram | Paid provider default zero; full form/audio workload estimado | Os 20 contratos e seis famílias positivas/negativas passam, sem generic/LLM-only waiver |
| 40 | `AISEC-01`/`CONTENT-01` isolam amostras românicas | `RANK-01`/`FORM-04`/`AUDIO-02`/`EVAL-01` têm direitos por idioma | `FORM-04`/`AUDIO-02` workload e `AISEC-01` limits são orçados | Sete IDs `RANK-01`..`EVAL-01` passam separadamente nos cinco profiles |
| 41 | `AISEC-01`/`CONTENT-01` isolam amostras germânicas | Sources/forms/audio/eval rights são por seis idiomas | Fan-out/pitch/stød/voz usam forecast e caps | Sete IDs passam por idioma, incluindo variants, display e pronunciation evidence |
| 42 | `AISEC-01` minimiza contexto e `CONTENT-01` fixa Core | Rights cobrem corpora/forms/stress/audio/eval por idioma | Case/aspect/stress workload e calls têm caps | Sete IDs passam por idioma para case/aspect/script/analysis/risk strata |
| 43 | `AISEC-01` limita cadeias/contexto e isola private | Analyzer/form/audio/eval datasets têm direitos | Long analyses, forms/audio e tokens usam forecasts/caps | Sete IDs passam 200 goldens por profile, sem suffix ou LLM-only waiver |
| 44 | `AISEC-01` protege contexto e `CONTENT-01` preserva v3/private | UniDic/segmenter/Kiwi/corpus/audio/eval rights são individuais | Reading/polyphony/regeneration/forms têm workload/caps | Sete IDs passam por `ja`/`zh`/`ko`, incluindo contextual `AUDIO-02` e local `EVAL-01` |
| 45 | `AISEC-01` exclui payload pessoal; `CONTENT-01` assina Core | 66k IDs, forms, audio, content e eval datasets têm rights | Rebuild/review/signatures/fan-out/Expansion cabem no budget | Sete policies/datasets/hashes ficam assinados; qualquer rank/content/eval drift invalida freeze |
| 46 | `ANKI-01` preserva classes de Custom/Highlight | Attribution/media acompanha note/card/destination | APKG/CSV/TSV e dynamic `FORM-04` usam totals reais | `ANKI-01`/`FORM-04`/`DISPLAY-01` passam identity/alias/update/scheduling/client migration |
| 47 | Sandbox/consent protegem mapping `ANKI-01`/`DISPLAY-01` | Uso de package/schema/aliases respeita termos | File/CPU/memory/mapping limits são medidos | Note GUID/card ordinal/role/analysis são mapeados ou quarantined sem scheduling transfer |
| 48 | `CONTENT-01` separa Core canônico de Custom/Highlight | Edition/private namespaces mantêm source restrictions | Queue/module/order/eligibility têm budget computacional | `CONTENT-01` prova hashes de Core content/GUID/rank/edition imutáveis sob adaptação |
| 49 | `AISEC-01` isola input/output e `CONTENT-01` separa namespaces | Grounding/content/audio/eval rights acompanham a edição | `AUDIO-02` cache e `AISEC-01` rate/token/retry caps cobrem workload | `DISPLAY-01`/`AUDIO-02`/`AISEC-01`/`CONTENT-01`/`EVAL-01` passam release evidence |
| 50 | Clone-only protege private/live mappings `ANKI-01` | Aliases/assets/forms mantêm provenance | Preview/rehearsal calcula dynamic forms/client costs | `ANKI-01`/`FORM-04`/`DISPLAY-01` passam current-baseline aliases, scheduling e rollback por cliente |
| 51 | `AISEC-01`/`CONTENT-01` revalidam consent/namespaces | Licenses/attributions/revocations ficam verdes | Confirmação inclui real workload, signatures e rollout caps | `ANKI-01`/`AUDIO-02`/`AISEC-01`/`CONTENT-01`/`EVAL-01` passam pre/postflight ou bloqueiam release |

### 8.4 Invariantes da migração

| Invariante de migração | Evidência da prévia | Evidência de backup/restauração | Confirmação | Comportamento de falha/rollback |
|---|---|---|---|---|
| IDs estáveis | Fase 50 classifica 1:1/merge/split/drop/unresolved e lista lexical/content/note/card IDs/GUIDs | Fases 36/50 restauram clone e reconciliam referências/hashes | Fase 51 exige aceite hash-bound somente de mappings/aliases 1:1 provados | Conflito/ambiguidade bloqueia; journal/rollback restaura referências sem scheduling transfer |
| Exporter atual -> topologia `ANKI-01` | Prévia parte de um `genanki.Note` por row, template `Card 1`, uma deck instance e um card por nota; compara note GUID/card ordinal com modelo selecionado | Clone preserva package/source manifests e executa imports nos quatro clients | Confirmação nomeia candidate/version selecionada, aliases, updates e client evidence; não chama baseline atual de v4 | Modelo não assinado, client mismatch, collision/duplication ou round-trip falho bloqueia e restaura package/schema anterior |
| Drift de job/rank e aliases semânticos | Prévia mostra GUID atual com `job_id`/`sort_index`, reruns com novo job/rank e mapping para semantic identity | Snapshot conserva GUID/source input antigo e alias table candidata para comparação 1:1 | Só alias bijetivo provado pode preservar note/scheduling; rank/job não entra no futuro semantic GUID | Alias ausente/não bijetivo, split/merge ou identity uncertainty não transfere scheduling e bloqueia apply |
| Formas dinâmicas e scheduling | `FORM-04`/`DISPLAY-01` listam add/remove, parent/form/analysis/sense/context IDs, prerequisite e mecanismo burying-or-alternative selecionado | Fixtures restauram antes/depois por cliente e preservam scheduling conhecido somente quando mapping é inequívoco | Confirmação explicita cards adicionados/removidos, non-transfer ambígua e custo integral sem cap | Dynamic form collision, prompt ambíguo, sibling claim falso ou perda de scheduling aciona rollback |
| Identidades, headwords e carga de frequência | Prévia lista por idioma 3000 Core identities, 3000 headwords, `N`, cada `O`, total computado e reconciliação Level 1/2/3; Expansion aparece separada | Snapshot/clone preserva manifests de identidade e cards para comparação componente a componente | Fase 51 mostra identidade versus card/workload e não oferece aceite para truncar forma Core | Diferença de fórmula, forma omitida ou teto de 3000 cards invalida confirmação e restaura o manifest anterior |
| Destino e sequência de formas | Prévia prova parent inventory, nível/deck ID, papel/análise e ordem lema->formas, sem destino top-level de `Important Forms` | Restore recompõe os mesmos deck IDs, vínculos e prerequisites | Confirmação destaca qualquer mudança de topology; Core forms nunca migram para Expansion/Grammar | Reroute, forms subdeck, forma antes do lema ou deck ID divergente bloqueia apply e aciona rollback |
| Conteúdo Core canônico | Prévia lista `deck_edition_id`, content versions/GUIDs, definitions/examples/translations, render policy e asset hashes; learner deltas ficam só em queue/module/order/eligibility | Backup restaura bundle `CONTENT-01` assinado e namespaces Custom/Highlight separados | Confirmação aceita nova edição/diff/review material, nunca mutation individual de Core | Hash/diff ausente, Core personalizado ou overwrite de namespace privado bloqueia; rollback restaura edição assinada |
| Dados do usuário/privados | Fase 50 lista classe, consentimento, retenção e transformação | Backup controlado é restaurado no clone e testa exclusão | Fase 51 destaca payload pessoal e usos autorizados | Vazamento/consentimento inválido impede apply e remove derivados |
| Histórico de estudo | Fases 47/50 listam reviews, confiança, quarentena e perdas; só 1:1 transfere | Pacote original fica intacto e mappings são restaurados isoladamente | Fase 51 explicita mappings 1:1; ambíguos não transferem/apagam | Nunca escrever no Anki; mapping incerto fica em quarentena/rollback |
| Coreano português->inglês | Fases 44/49/50 quantificam regeneração, review, custo e diff de policy | Conteúdo v3 português permanece recuperável no backup/clone | Fase 51 confirma regeneração, nunca relabel | Falha mantém português v3 e bloqueia release v4 |
| Explicações do inglês-alvo em português | Prévia comprova que `en` mantém português, inclusive forms | Restore preserva conteúdo/policy aprovada | Confirmação inclui a exceção normativa | Conversão indevida bloqueia postflight e reverte lote |
| Isolamento do Latim | Prévia comprova zero `la` no mapping moderno e português preservado | Restore do caminho latino passa hashes isolados | Confirmação explicita exclusão do Latim da migration moderna | Qualquer mutation moderna em `la` bloqueia e restaura isolamento |
| Assets e mídia | Fase 50 lista reuse/regenerate/drop, hashes, espaço e licença | Bytes/manifests são restaurados e resolvidos no clone | Fase 51 aceita staging/switch e descarte pelo hash da prévia | Falta/hash/licença impede switch; rollback restaura manifest/bytes |
| Pronunciation signatures | Prévia lista todos os campos `AUDIO-02`, artifact hashes e cache reuse/regenerate decisions, inclusive heterófonos/polifonia | Restore valida bytes/codec/signature manifests contra o conteúdo exibido | Confirmação mostra assinatura/provider/model/policy drift e custo de regeneration | Text-only reuse, signature incompleta ou artifact integrity falha bloqueia switch e invalida cache afetado |
| Prompt, privacidade e HTML/Anki safety | Prévia `AISEC-01` lista trust/limit/output policies, schema/escaping/allowlist versions e apenas hashes/counts sanitizados | Clone usa fixtures benignas/injection/`<script>`/handler/`javascript:` sem provider secret/raw private log | Confirmação referencia suites 100%-blocking e namespaces autorizados, não payload privado | Injection que muda controle, disclosure, script/URL/markup ativo ou unapproved directive bloqueia e remove derivado |
| Baselines e regressão de avaliação | Prévia liga `EVAL-01` dataset hashes, eligible counts, strata, thresholds/drift e signed baseline a cada policy/analyzer/provider afetado | Restore reproduz datasets/results/reviewer evidence sem alterar baseline assinado | Confirmação mostra dimension rates, critical failures e regression deltas por idioma | Dataset drift não rerodado, threshold/regression falho ou sole LLM judge bloqueia release e restaura versão aprovada |
| Custos de provider | Prévia estima provider/capacidade/storage e hard caps sobre todos os headwords, forms e opcionais computados | Backup/restore não depende de chamada paga | Confirmação é vinculada ao orçamento vigente e à carga reconciliada | Cap interrompe antes do excesso sem publicar deck truncado; resume reutiliza cache/journal |
| Interrupção e retomada | Fase 50 define lotes, checkpoints e falhas ensaiadas | Clone testa restore completo e por journal | Fase 51 aceita estratégia transacional/resumível | Apply incompleto reverte ou retoma atomicamente sem estado híbrido |
| Idempotência de rerun | Ensaio prevê segunda execução sem mudança salvo drift declarado e repete as mesmas fórmulas/destinos | Snapshot permite comparação antes/depois/repetição | Confirmação vincula versões exatas de código/dados | Drift invalida confirmação; rerun não duplica IDs/cards/assets/custos nem altera sequência |

A auditoria conclui que as 23 decisões fixas, os 20 contratos explícitos, as 23 linhas de requisitos linguísticos, G0 e as Fases 35–51 possuem ownership, dependências e evidência posterior consistentes com a alocação fixa. A rastreabilidade distingue 3000 identidades Core e 3000 headwords padrão da contagem variável de cards, mantém toda forma Core aprovada no nível/deck ID do pai depois do lema, preserva Expansion como inventário opt-in somente de identidades adicionais e deixa a topologia Anki não selecionada até a decisão bloqueante da Fase 35. Itens externos ainda sem prova permanecem bloqueados nos gates; nenhum foi silenciosamente aprovado por este documento.
