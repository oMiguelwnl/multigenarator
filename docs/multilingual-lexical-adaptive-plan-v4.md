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
3. um núcleo moderno congelado de três níveis e uma expansão opcional separada;
4. formas de superfície, formas importantes, definições específicas da forma e áudio do texto exato;
5. MWE, resolução de sentido, roteamento de fonte e papéis de card como conceitos distintos;
6. listas personalizadas e highlights sob gates por perfil e controles de privacidade;
7. integração somente de leitura de histórico APKG;
8. priorização adaptativa explicável sem alteração da ordem canônica nem do histórico importado;
9. exportação para subdecks Anki reais;
10. migração in-place do Multilang com prévia, backup, confirmação, recuperação e auditoria;
11. G0 e todas as Fases 35–51, com dependências e gates de saída.

### Evolução in-place, não produto paralelo

A v4 é uma evolução in-place do Multilang. Ela deve preservar identidades válidas, dados do usuário, histórico de estudo mapeável, contratos de exportação compatíveis e assets aprovados. Não será criado um segundo produto, banco ou fluxo paralelo para contornar a migração. Isolamentos linguísticos necessários, especialmente o Latim clássico, são limites dentro do mesmo produto e não justificam duplicar a aplicação.

### Não objetivos

- Não promover a v4 durante a persistência deste documento.
- Não alterar numeração, estado, requisitos ou política das Fases 30–34.
- Não implementar modelos, schemas, migrations, registries, providers, filas, integração Anki, CLI, API, UI, testes, decks ou assets neste trabalho de documentação.
- Não escolher uma fonte lexical, licença de redistribuição, provider, orçamento ou limiar de qualidade sem a evidência exigida pelo gate correspondente.
- Não incorporar o Latim clássico ao pipeline moderno nem migrá-lo por suposições modernas.
- Não transformar formas, cards, exemplos, áudios ou grafias duplicadas em novas vagas do núcleo lexical.
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
| Capacidades | flags explícitas para Core, expansão, listas personalizadas, highlights, mapeamento de histórico APKG e comportamento adaptativo |

As flags de capacidade possuem estado `disabled`, `evidence_pending` ou `enabled` e referenciam a evidência que autoriza o estado. Uma operação solicitada para capacidade não habilitada deve ser recusada com motivo acionável; nunca deve cair silenciosamente em heurística genérica. O perfil do Latim declara explicitamente seu isolamento e não herda flags modernas por padrão.

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

Cada um dos 22 idiomas modernos possui exatamente 3000 identidades lexicais únicas aprovadas e ordenadas:

- Nível 1: ranks 1–1000;
- Nível 2: ranks 1001–2000;
- Nível 3: ranks 2001–3000.

O rank pertence à versão congelada da identidade lexical no núcleo. Não pertence a um card nem a uma forma. Uma identidade pode produzir mais de um card pedagógico sem aumentar a contagem. Identidade sem sentido resolvido, duplicata de identidade, forma flexionada redundante, exemplo, áudio ou card não pode preencher uma vaga.

#### `Optional expansion 0-3000`

A expansão opcional contém de zero a 3000 identidades adicionais aprovadas por idioma, sempre depois do núcleo e em namespace, versão, proveniência e subdeck próprios. A quantidade é configurável dentro desse intervalo; não há padding. Habilitar, desabilitar ou regenerar a expansão não renumera, substitui nem altera o pertencimento das 3000 identidades do núcleo.

O Latim clássico não recebe automaticamente `Core 3x1000` nem `Optional expansion 0-3000`; sua escala e evolução continuam governadas pelo caminho isolado e por aprovações próprias.

### 3.4 Formas, definições e áudio

`SurfaceForms` liga uma identidade às realizações observadas ou geradas, com texto normalizado e exibido, features morfológicas, proveniência, confiança, adapter e versão. Uma forma submetida pelo usuário permanece preservada mesmo quando mapeada a um lema.

`Important Forms` é o subconjunto pedagogicamente justificado de `SurfaceForms`. Uma forma somente pode entrar nesse conjunto por pelo menos um destes motivos registrados: irregularidade, frequência própria comprovada, imprevisibilidade a partir do lema, ambiguidade, pronúncia inesperada, valor de pré-requisito ou dificuldade inferida a partir do lema e da evidência de aprendizagem. Conveniência de geração, mera existência no paradigma e desejo de aumentar o deck não são critérios válidos. Uma forma importante nunca vira nova identidade somente para ganhar um card.

`Definitions` possui dois escopos relacionados e distintos:

1. definição da identidade e do sentido;
2. definição específica da forma exibida, ligada ao `surface_form_id`, que explica os atributos aplicáveis sem substituir o sentido lexical.

O bundle canônico de features admite, quando aplicável ao idioma e à forma, os identificadores técnicos `tense`, `mood`, `person`, `number`, `case`, `gender`, `aspect` e `register`. Campos não aplicáveis são explicitamente ausentes, não inventados. A definição específica da forma deve explicar somente análise comprovada pelo adapter e pela evidência; análise ambígua fica em quarentena.

`Exact-form audio` exige que o texto sintetizado ou resolvido seja exatamente a forma exibida no card, após a normalização declarada. Se o card mostra uma forma diferente do lema, áudio do lema não pode substituí-la. O asset registra texto exibido, texto falado, hash, idioma, locale, voz, provider, versão, SSML quando houver, licença, custo, status de revisão e hash do arquivo. Áudio da frase usa o texto exato do exemplo aprovado sob o mesmo princípio.

`SurfaceForms`, `Important Forms`, seus `Definitions`, cards de forma e assets de `Exact-form audio` ficam fora da quota de 3000 identidades. O mesmo vale para exemplos, traduções, cards adicionais, mídia e grafias duplicadas.

### 3.5 Contratos normativos de card, forma, sentido, carga e GUID

| ID | Contrato obrigatório |
|---|---|
| `CARD-01` | Cada identidade lexical aprovada produz, por padrão, exatamente um card de reconhecimento. Cards reversos, de listening e cloze são opcionais, têm papéis próprios e ficam **desabilitados por padrão**; habilitá-los exige configuração explícita, evidência de qualidade e relatório de carga. |
| `FORM-01` | Toda `SurfaceForm` referencia uma identidade, análise morfológica versionada, texto exato, proveniência e confiança. Formas, inclusive seus cards, ficam fora das 3000 vagas do Core. |
| `FORM-02` | Uma `Important Form` só é selecionada por irregularidade, frequência, imprevisibilidade, ambiguidade, pronúncia inesperada, valor de pré-requisito ou dificuldade inferida do lema; a razão e a evidência são obrigatórias. |
| `FORM-03` | O card de forma referencia `surface_form_id` e `morphological_analysis_id`, mostra a forma analisada, recebe `Definitions` e áudio dessa forma exata e não duplica a identidade lexical. |
| `SENSE-01` | Identidade e conteúdo são sense-aware; homógrafo, POS ou sentido inconclusivo fica em quarentena, sem escolher a primeira acepção nem compartilhar GUID indevidamente. |
| `MWE-01` | MWE com unidade lexical própria mantém identidade, segmentação, variantes, sentido e rota próprios; não é quebrada por espaço nem inflada por cada token. |
| `ROUTE-01` | A decisão determinística segue `source type -> identity/sense -> content route -> card role -> real subdeck`; rota não suportada ou ambígua falha fechado. |
| `DEF-01` | `Definitions` são concisas e meaning-first: começam pelo significado relevante e acrescentam gramática contextual da identidade ou da forma, sem despejo de paradigma nem metadado morfológico como falsa definição. |
| `AUDIO-01` | O áudio de palavra usa a forma exatamente exibida e o áudio de sentença usa a sentença exatamente aprovada; hashes, locale, voz, provider, custo, licença e revisão são vinculados ao texto. |
| `LOAD-01` | Cada idioma publica contagens por identidade, card padrão, papel opcional e `Important Form`, mais o total e a variação de workload por subdeck. Todo deck extra de formas exige relatório antes de habilitação/exportação. |
| `DEPEND-01` | Card de forma só fica elegível depois do card do lema ou do pré-requisito explicitamente aprovado. Formas irmãs da mesma identidade usam sibling burying para evitar exposição concorrente indevida. |
| `GUID-01` | O GUID deriva de inputs semânticos versionados: identidade lexical + papel do card + análise da forma quando aplicável. Rank, texto de definição, sentença, template, provider, ordem de geração e timestamp não entram no GUID. |

O comportamento padrão é, portanto, um card de reconhecimento por identidade lexical. Reverse, listening e cloze não aparecem por inferência nem por expansão de template; permanecem desabilitados até uma decisão explícita por edição/perfil. Quando habilitados, não alteram o Core, usam papéis e GUIDs distintos, respeitam `DEPEND-01` e aparecem no relatório `LOAD-01`.

O sequencing de formas é dirigido por pré-requisitos: primeiro o lema/identidade, depois a forma importante elegível. O scheduler interno enterra siblings da mesma identidade conforme a política versionada; o export fornece metadata suficiente para a política compatível do cliente, sem escrever no scheduler importado do Anki.

#### Exemplo normativo: `be`, `is`, `was` e `were`

- `be` é a identidade lexical do verbo e recebe o card de reconhecimento padrão.
- `is` pode ser `Important Form` como presente indicativo, terceira pessoa singular; uma frase como “She is ready.” sustenta uma definição meaning-first com gramática contextual e áudio exatamente de `is`.
- `was` pode ser `Important Form` como passado indicativo singular; “He was tired.” ancora sentido, pessoa/número aplicáveis e áudio exatamente de `was`.
- `were` requer análise contextual. “They were ready.” registra passado indicativo plural, enquanto “If I were ready, I would go.” registra irrealis. A grafia igual pode apontar para análises de forma distintas; `DEF-01`, `FORM-03` e `GUID-01` impedem que o irrealis seja rotulado como simples plural ou receba o GUID errado.
- Esses cards de forma não consomem slots do Core, só ficam elegíveis depois de `be`, usam sibling burying entre si e entram nas contagens de workload do inglês.

### 3.6 MWE, sentidos, fontes, rotas e papéis de card

Os seguintes conceitos são persistidos separadamente:

- **MWE:** identidade lexical multiword com segmentação, composição, variantes e sentido próprios;
- **resolução de sentido:** evidência que conecta ocorrência, POS e contexto a uma identidade;
- **tipo de fonte:** núcleo, expansão, lista personalizada, highlight, histórico APKG ou fundação linguística;
- **rota de conteúdo:** conjunto aprovado de adapters e providers para enriquecer o item;
- **papel de card:** finalidade pedagógica e contrato de campos do card;
- **destino de subdeck:** caminho Anki real derivado somente após as decisões anteriores.

Papéis mínimos: headword de núcleo, expansão, `Important Form`, MWE, personalizado, highlight e fundação específica do idioma. Uma decisão determinística segue `source type -> identity/sense -> content route -> card role -> real subdeck`. Uma rota sem suporte ou com sentido ambíguo não cai em um card genérico: fica bloqueada ou em quarentena com diagnóstico.

### 3.7 Dados pessoais e histórico Anki

Listas personalizadas e highlights só são habilitados quando o `LanguageProfile` comprova normalização, morfologia, matching, conteúdo e áudio para aquela capacidade. Os dados preservam forma e ordem submetidas, proveniência privada e consentimento. Podem mapear uma identidade compartilhada ou criar identidade privada, mas nunca mudam rank, pertencimento ou conteúdo curado do núcleo compartilhado.

A integração **`read-only APKG history`** lê pacotes suportados e histórico de revisão para produzir um mapeamento com proveniência, confiança e quarentena. Ela não escreve no arquivo importado, na coleção, no Anki ou no AnkiConnect. O mapeamento é derivado e revogável; incerteza não vira certeza por conveniência.

A **`adaptive queue`** consome rank, pré-requisitos, prontidão de conteúdo, sinais pessoais autorizados e histórico mapeado. Ela é determinística para a mesma versão e entrada, explica cada componente do score, permite reset e override e separa prioridade de estudo de identidade/rank/exportação. Ela nunca altera rank canônico, histórico importado ou intervalos do Anki.

## 4. Fluxo de capacidade ponta a ponta

| Etapa | Entrada e transformação | Evidência persistida | Falha e recuperação |
|---|---|---|---|
| 1. Aprovação de fonte | Registro de fonte lexical, frequência, exemplo, tradução ou áudio | licença, finalidade, atribuição, direitos de aquisição/redistribuição, versão e checksum | uso e redistribuição bloqueados; revogação identifica derivados para rebuild |
| 2. Ingestão versionada | Bytes congelados entram por adapter declarado | hash de entrada, versão do adapter, contagens, rejeições e rerun ID | lote atômico falha ou retoma; entrada alterada exige nova versão |
| 3. Perfil linguístico | `LanguageProfile` aplica script, normalização, segmentação e morfologia | perfil, normalizador, analyzer e versões | indisponibilidade ou ambiguidade vai para quarentena; nenhuma heurística silenciosa |
| 4. Identidade | lema, POS, sentido e MWE resolvem ID estável | evidência de resolução, aliases, proveniência e confiança | conflito preserva ambas as candidatas e bloqueia promoção |
| 5. Inventário | identidade aprovada recebe Core ou expansão e rank versionado | membership, rank, versão e decisão de curadoria | duplicata, falta ou licença incerta bloqueia congelamento |
| 6. Formas | ocorrências viram `SurfaceForms`; formas pedagógicas viram `Important Forms` | features, attestation/generation, forma exata e vínculo à identidade | análise duvidosa não cria definição nem card aprovado |
| 7. Enriquecimento | definição, exemplo e tradução seguem sentido, forma e política do idioma | grounding, prompt/policy quando houver, versões, validações e revisão | saída incorreta é rejeitada, regenerada sob nova tentativa ou enviada à revisão |
| 8. Áudio | forma exibida e frase aprovada geram assets separados | texto e hash exatos, voz, locale, provider, custo, licença e revisão | cache evita chamada repetida; divergência, custo ou provider bloqueado impede exportação |
| 9. Roteamento | fonte, identidade/sentido, conteúdo e papel determinam destino | decisão reproduzível e razão por regra | rota não suportada ou ambígua fica em quarentena |
| 10. Exportação | cards estáveis compõem `real subdecks` e mídia | GUID, schema, campos, manifest, subdeck, hashes e round-trip | validação falha antes de publicar artefato parcial |
| 11. Histórico | parser seguro executa mapeamento somente de leitura | schema detectado, limites, IDs candidatos, confiança e proveniência | arquivo suspeito ou mapping incerto é rejeitado/quarentenado sem escrita |
| 12. Adaptação | sinais autorizados alimentam score versionado | componentes do score, policy, snapshot e explicação | reset restaura baseline; ausência de sinal usa cold-start canônico |
| 13. Migração | `in-place Multilang migration` aplica plano confirmado em lotes | prévia, backup, confirmação, checkpoints, auditoria e hashes | interrupção retoma; invariantes rompidos acionam rollback/restore |

Todos os limites usam IDs estáveis e registros de proveniência/versionamento. Reruns com as mesmas entradas e versões devem produzir os mesmos resultados ou uma divergência bloqueante explícita. Quarentena mantém payload mínimo necessário, razão, candidato, regra/versão e ação possível. Recuperação nunca apaga silenciosamente a entrada original nem converte falha em aprovação.

## 5. G0 e especificações das fases

### G0: Pré-requisitos de promoção e baseline congelada

**Resultado:** Existe evidência suficiente para decidir, separadamente, se a proposta v4 pode entrar no planejamento ativo sem sobrepor a v3.0, perder dados atuais ou assumir fontes, privacidade, custos e qualidade ainda não aprovados.

**Depende de:** Conclusão, verificação e arquivamento formais da v3.0; nenhuma dependência v4 pode substituir esse requisito.

**Entregáveis:**

- inventário atual e datado de schemas, dados persistidos, IDs estáveis, migrations, exports/APKG, note types, subdecks, assets, testes, providers, registries e riscos da árvore de trabalho;
- snapshots checksummed e recuperáveis de banco, configurações, manifests, assets e mapeamentos existentes;
- ensaio documentado de restore em ambiente isolado, com RPO/RTO ou limites equivalentes aprovados;
- reconciliação do baseline com toda evolução ocorrida após a escrita deste documento;
- escopo v4, matriz dos 22 idiomas modernos e perfil isolado do Latim aprovados;
- estudo de viabilidade e evidência de fonte/licença/atribuição/redistribuição por idioma, sem commit de asset não aprovado;
- regras aprovadas de processamento, minimização, consentimento, retenção, exclusão e provider para dados pessoais/APKG;
- estimativas dry-run, budgets e hard caps por provider, item, lote e execução;
- limiares mensuráveis de morfologia, sentido, matching, texto, tradução, áudio, exportação e migração;
- pacote de evidência e registro explícito da decisão de promover ou rejeitar/deferir a v4.

**Critérios de saída:**

1. A v3.0 consta como concluída, verificada e arquivada nas fontes canônicas, sem fase aberta.
2. O inventário cobre 100% das superfícies listadas e registra riscos/diffs da árvore de trabalho sem alterá-los.
3. Um snapshot completo é restaurado e reconciliado por hashes e contagens em ambiente isolado.
4. Cada idioma possui decisão de viabilidade de fonte/licença e regras de privacidade, ainda que o resultado seja bloqueado.
5. Budgets/hard caps e limiares de qualidade têm responsáveis, evidência e comportamento fail-closed.
6. Uma aprovação separada, registrada e explícita autoriza a futura alteração de SPEC/ROADMAP; sem ela, nenhuma Fase 35 começa.

### Fase 35: Contratos

**Resultado:** Glossário, contagens, variantes, políticas linguísticas, papéis de card, semântica de edição e todos os contratos normativos estão fechados antes de qualquer asset ou schema v4.

**Depende de:** G0 aprovado e promoção separada registrada.

**Entregáveis:**

- glossário normativo para identidade, sentido, `SurfaceForms`, `Important Forms`, MWE, Core, expansão, edição, módulo, tag, subdeck e workload;
- regras exatas de 3000 identidades, três bandas de 1000 e expansão adicional de zero a 3000, com variantes e Latim isolado;
- política de explicações, exceção de inglês-alvo e transição coreana português-v3 para inglês-v4;
- papéis de card, reconhecimento padrão, opcionais reverse/listening/cloze desabilitados, formas fora da quota, módulos de 50–200 e tags suplementares;
- inputs semânticos de GUID e estudo de viabilidade APKG/edições/mixed updates;
- especificações aprovadas de `CARD-01`, `FORM-01`, `FORM-02`, `FORM-03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01` e `GUID-01`.

**Critérios de saída:**

1. Um manifest de contratos contém todos os 12 IDs sem conflito, campo indefinido ou decisão implícita.
2. Casos de contagem provam que identidade, não card/forma, ocupa a quota e que opcionais/formas só alteram workload.
3. Matriz dos 22 idiomas e Latim fecha variantes, explicações e requisitos individuais sem escolher fonte/provider pendente.
4. Protótipos de GUID/APKG demonstram viabilidade sem escrever schema ou asset de produção.
5. Privacidade, licença, custo e qualidade possuem donos/evidência exigida; qualquer decisão aberta bloqueia a Fase 36–38 afetada.

### Fase 36: Persistência

**Resultado:** A persistência v4 existe de forma versionada e inativa, protegida por backups imutáveis restaurados antes de qualquer mutation e sem alterar o runtime atual.

**Depende de:** Fase 35.

**Entregáveis:**

- inventário de schemas/dados e backups imutáveis, checksummed e restore-tested antes da primeira migration;
- contratos persistentes para `LanguageProfile`, identidade/sentido lexical, `SurfaceForm`, `MorphologicalAnalysis`, `CardTarget`, collection/version/entry, deck edition e aliases de GUID;
- extensão de candidate/snapshot metadata, proveniência, versões de analyzer/policy e fingerprints;
- migrations forward/backward, modelos ORM e constraints equivalentes;
- feature/cutover flags que mantêm todas as estruturas novas inativas até a Fase 51.

**Critérios de saída:**

1. Restore de backup reconcilia hashes, contagens e referências antes e depois dos ensaios de migration.
2. Alembic/schema e ORM têm paridade comprovada para campos, constraints, índices e relações.
3. Fingerprints idênticos são determinísticos e mudanças semânticas geram nova versão.
4. Estruturas inativas não alteram geração, exportação, dados pessoais nem comportamento v3 existente.
5. Rollback, segurança de dados, custo de armazenamento e qualidade de compatibilidade passam seus gates.

### Fase 37: Fontes e cobertura

**Resultado:** Cada idioma moderno possui fontes e pools candidatos auditáveis, maiores que 3000, com cobertura mensurada e redistribuição bloqueada até aprovação.

**Depende de:** Fase 35.

**Entregáveis:**

- registry por fonte/idioma para aquisição, licença, derivação, redistribuição, atribuição, versão e revogação;
- corpora balanceados e held-out, com domínio, período, variante, qualidade e privacidade documentados;
- candidate pools maiores que 3000 por idioma e reservas separadas;
- scoring reproduzível de frequência, dispersão e diversidade contextual;
- relatórios separados para cobertura das bandas 1k/2k/3k e expansão;
- `wordfreq` restrito a bootstrap, nunca fonte final nem autorização de CSV redistribuído.

**Critérios de saída:**

1. Todo idioma tem pool >3000 e held-out independente, ou permanece explicitamente bloqueado.
2. Relatórios mostram cobertura, lacunas, contaminação, domínios e variantes por 1k/2k/3k/expansão.
3. Cada byte/derivado aponta para versão, checksum, licença, atribuição e decisão de redistribuição.
4. Direito incerto impede commit/publicação; corpus privado não entra em asset compartilhado.
5. Aquisição/processamento têm orçamento/caps e os scores passam revisão de qualidade/viés.

### Fase 38: Morfologia e curadoria

**Resultado:** Profiles e analyzers fixados resolvem identidade, forma, sentido, MWE, target matching e rota com precisão aceita de 100% e falha fechada mensurável.

**Depende de:** Fase 35.

**Entregáveis:**

- seleção, qualificação e pin de analyzer/tokenizer por `LanguageProfile`;
- normalização, lema/POS/sentido, MWE, features de forma e roteamento determinísticos;
- reservas revisadas e congeladas para substituições posteriores;
- remoção de live fallback heurístico de qualquer caminho candidato v4;
- no mínimo 120 casos dourados por idioma e 200 para cada idioma CJK ou aglutinativo, com positivos/negativos;
- revisão humana estratificada e 100% dos casos de alto risco, ambiguidade, OOV e mudança de analyzer.

**Critérios de saída:**

1. Entre análises aceitas, a precisão é 100%; falso aceite reprova o profile/lote.
2. Pelo menos 98% dos casos inequivocamente resolvíveis são resolvidos; o restante é explicado/quarentenado.
3. Ambiguidade tem 100% de fail-closed e target matching positivo/negativo passa 100% dos goldens aprovados.
4. Rerun com versões fixadas reproduz identidade, análise, rota, quarentena e hash.
5. Termos de analyzer/modelo, custo de execução, payload mínimo de review e thresholds têm aprovação; nenhum live fallback mascara falha.

### Fase 39: Piloto representativo

**Resultado:** Um piloto offline de oito idiomas prova os contratos ponta a ponta antes do rollout por famílias e produz estimates confiáveis de runtime, custo e invalidação.

**Depende de:** Fases 36, 37 e 38.

**Entregáveis:**

- exatamente 100 candidatos offline para cada `pt`, `en`, `de`, `pl`, `tr`, `ja`, `zh` e `ko` (800 no total);
- evidência de identidade/sentido, formas, MWE/rota, card padrão e `Important Forms` fora da quota;
- casos ingleses de `be`, `is`, `was` e `were`, incluindo indicativo versus irrealis contextual;
- `Definitions` meaning-first e contratos de áudio da forma/sentença exatas sem chamada paga;
- estimates de runtime, memória, storage, workload, chamadas/custo e regras de promotion/invalidation.

**Critérios de saída:**

1. Cada idioma produz 100 decisões reproduzíveis, com aceites, rejeições e quarentena reconciliados.
2. Todos os 12 contratos normativos têm pelo menos uma prova positiva e uma negativa aplicável no piloto.
3. `is/was/were` mantêm contexto, análise, GUID e áudio pretendido distintos quando semanticamente necessário.
4. Budget padrão de provider pago é zero; tentativa de chamada bloqueia e rollout não avança com threshold falho.
5. Privacidade, licença, estimates de custo e métricas de qualidade geram decisão explícita de promover ou invalidar cada componente.

### Fase 40: Rollout românico

**Resultado:** `pt`, `es`, `fr`, `it` e `ro` possuem planos linguísticos completos e amostras verticais aprováveis sob os contratos comuns.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada idioma: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato, reserva, `Important Forms`, expansão e coverage report;
- regras românicas para gênero, clíticos, contrações, conjugação, modo e, em romeno, `ș/ț` com vírgula;
- amostra vertical de 90 cards por idioma (450 no total), incluindo reconhecimento padrão e formas justificadas;
- plano de voz/áudio da forma exata, workload por subdeck e revisão humana estratificada;
- manifests reproduzíveis sem freeze global nem provider pago implícito.

**Critérios de saída:**

1. Os cinco idiomas completam todos os itens do plano, sem lacuna escondida por adapter genérico.
2. Cada amostra de 90 passa identidade/sentido, target matching, definição, forma, rota e exportability estática.
3. `Important Forms` têm somente razões `FORM-02`, ficam fora do Core e aparecem no workload.
4. Fonte/licença e variantes/locales são aprovadas ou bloqueiam somente o idioma afetado, sem redistribuição antecipada.
5. Custos/vozes são estimates; qualidade e human review aprovam a promoção para freeze.

### Fase 41: Rollout germânico

**Resultado:** `en`, `de`, `nl`, `da`, `nb` e `sv` possuem planos completos e amostras verticais que preservam suas diferenças estruturais e fonológicas.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos seis idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato, reserva, `Important Forms`, expansão, coverage report, amostra, voz/áudio e revisão humana;
- capitalização alemã, compostos e verbos separáveis; definitude; pitch accent/stød; identidade Bokmål `nb`;
- inglês-alvo com explicações em português e formas contextuais de `be`;
- amostra vertical de 90 cards por idioma (540 no total);
- planos de áudio/voz, workload e revisão humana por idioma/variante.

**Critérios de saída:**

1. Os seis idiomas atendem ao checklist completo e a identidade `nb` nunca cai em `no`.
2. Capitalização, compostos, separáveis e definitude passam goldens positivos/negativos.
3. Pitch/stød são qualificados por evidência e nunca inventados por ortografia ou voz não revisada.
4. As 540 amostras respeitam Core/form quota, GUIDs semânticos e explicações portuguesas para `en`.
5. Gates de privacidade, licença, custo e qualidade aprovam ou bloqueiam granularmente cada profile.

### Fase 42: Rollout eslavo e grego moderno

**Resultado:** `pl`, `ru`, `cs`, `hr` e `el` possuem planos completos e amostras verticais com caso, aspecto, escrita e identidade específicos.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos cinco idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato, reserva, `Important Forms`, expansão, coverage report, amostra, voz/áudio e revisão humana;
- caso, aspecto, animacidade, reflexivos, stress/script e clíticos por profile;
- política russa `е/ё`, stress e pares aspectuais; identidade croata `hr` sem fallback `sh`; normalização grega;
- amostra vertical de 90 cards por idioma (450 no total);
- planos de áudio/voz, workload e revisão de risco morfológico.

**Critérios de saída:**

1. Os cinco idiomas completam o checklist sem fundir sentidos, aspectos ou identidades nacionais.
2. Goldens cobrem caso/aspecto/animacidade/reflexivos e matching positivo/negativo.
3. `е/ё`, acento russo, `hr` e diacríticos/sigma gregos sobrevivem a round-trip e fingerprints.
4. As 450 amostras respeitam forms outside Core, Definitions contextuais e áudio exato planejado.
5. Fonte/licença, privacidade, custo e quality review têm decisão por idioma antes do freeze.

### Fase 43: Rollout aglutinativo

**Resultado:** `tr`, `fi` e `hu` possuem planos completos e amostras verticais que analisam cadeias morfológicas sem heurística de sufixo.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos três idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato, reserva, `Important Forms`, expansão, coverage report, amostra, voz/áudio e revisão humana;
- cadeias de sufixos, harmonia, casos, derivação versus flexão, gradação, posse e sistemas de conjugação;
- regras locale-aware turcas, gradação finlandesa e conjugação definida/indefinida húngara;
- amostra vertical de 90 cards por idioma (270 no total);
- planos de áudio/voz, workload e revisão de análises longas/ambíguas.

**Critérios de saída:**

1. Os três idiomas atingem o mínimo de 200 goldens e o checklist completo.
2. Derivação não é fundida com flexão e cadeias não são resolvidas por suffix stripping.
3. Formas importantes justificadas mantêm análise, dependência, sibling burying e carga reportada.
4. As 270 amostras passam identidade/sentido/MWE/rota/target matching com falha fechada.
5. Privacidade, licença, custo computacional e qualidade permitem ou bloqueiam cada profile.

### Fase 44: Rollout do Leste Asiático

**Resultado:** `ja`, `zh` e `ko` possuem planos completos e amostras verticais com segmentação, leitura, morfemas e scripts específicos.

**Depende de:** Fase 39.

**Entregáveis:**

- para cada um dos três idiomas: fonte/licença, variante/locale, analyzer/goldens, pool candidato, identidade/sentido/forma/MWE, Core exato, reserva, `Important Forms`, expansão, coverage report, amostra, voz/áudio/leitura e revisão humana;
- japonês com lema/POS/leitura UniDic; Mandarim com segmentação, Simplificado/Tradicional e polifonia; coreano com NFC/Kiwi/assinaturas de morfema;
- roteamento de partículas, auxiliares, classifiers, endings e demais itens gramaticais;
- política revisada de regeneração coreana português-v3 para inglês-v4, sem relabel;
- amostra vertical de 90 cards por idioma (270 no total), planos de áudio/leitura, workload e revisão humana.

**Critérios de saída:**

1. Os três idiomas atingem o mínimo de 200 goldens e o checklist completo.
2. UniDic, fronteiras chinesas/polifonia e Kiwi/NFC passam casos positivos/negativos sem fallback por espaço.
3. Variantes de script/leitura preservam identidade/proveniência e itens gramaticais seguem a rota correta.
4. A política coreana define regeneração e review; conteúdo v3 em português permanece intacto até migração confirmada.
5. As 270 amostras e planos de provider satisfazem gates de privacidade, licença, custo e qualidade.

### Fase 45: Freeze multilíngue

**Resultado:** O Core moderno fica congelado em exatamente 66.000 identidades aprovadas, com form packs e expansões separados e nenhum drift de hash.

**Depende de:** Fases 40, 41, 42, 43 e 44.

**Entregáveis:**

- 3000 identidades por cada um dos 22 idiomas, em bandas disjuntas de 1000/1000/1000;
- validação global contra POS desconhecido, identidade duplicada, sentido ambíguo e contaminação por idioma/script;
- licenças, atribuições, source manifests, analyzer/profile versions, ranks e hashes congelados;
- reservas e form packs versionados fora da quota, com workload por idioma;
- expansão configurável 0–3000 por idioma com proveniência própria e diff de Core;
- segunda revisão humana obrigatória, independente da primeira passagem.

**Critérios de saída:**

1. A soma é exatamente 66.000 e cada idioma valida 3000 e três bandas de 1000 IDs únicos.
2. Unknown POS, duplicata, ambiguidade não resolvida ou foreign contamination têm contagem zero entre aceitos.
3. Toda identidade possui licença/manifest/curadoria aprovados; direito pendente bloqueia o idioma/release.
4. Form packs não alteram contagem; expansões 0/intermediária/3000 não mudam nenhum Core hash.
5. Segunda revisão, métricas de qualidade, custo de rebuild e privacidade/proveniência passam antes do freeze assinado.

### Fase 46: Edições e exportação

**Resultado:** Edições versionadas exportam cards com GUIDs estáveis e subdecks reais, permitindo updates 1:1 sem conflar níveis, papéis ou dados pessoais.

**Depende de:** Fase 45.

**Entregáveis:**

- GUID por identidade + card role + form analysis conforme `GUID-01`, com alias apenas quando provado;
- subdecks reais para Core, `Important Forms`, Grammar, Expansion, Custom e Highlight;
- module tags suplementares, módulos de 50–200, mixed editions e manifests de composição;
- APKG e manifests CSV/TSV, mídia resolvível, `Image` vazio e model/deck IDs isolados;
- cards de reconhecimento padrão e opcionais reverse/listening/cloze ainda desabilitados salvo edição explícita;
- testes de import/update 1:1, GUID collision, reexport e round-trip por cliente suportado em nível estrutural.

**Critérios de saída:**

1. Inspeção prova hierarquia real; tags nunca simulam level/role subdeck.
2. Mesma semântica mantém GUID; mudança de texto/rank/provider não o troca; role/análise diferente gera GUID distinto.
3. Update 1:1 preserva nota e scheduling em fixtures suportadas sem duplicação.
4. Campo, mídia, model/deck ID, manifest e blank `Image` passam validação; dados pessoais permanecem isolados.
5. Licenças/atribuições, tamanho/custo e qualidade de APKG/CSV/TSV bloqueiam artefato incompleto.

### Fase 47: Histórico Anki somente de leitura

**Resultado:** Um importador APKG local e sandboxed deriva estado mínimo de aprendizagem de conteúdo Multilang sem abrir nem escrever coleções vivas.

**Depende de:** Fase 46.

**Entregáveis:**

- importador local de scheduling APKG com limites de path, members, tamanho, razão de compressão, tempo, CPU/memória e SQLite;
- cópia read-only e proibição técnica de AnkiConnect, coleção viva e qualquer write no pacote;
- mapping apenas de identidade/review Multilang, com confiança, proveniência, quarentena e schema drift;
- learner states minimizados; raw package e conteúdo extraído apagados conforme retenção;
- cold start, corrupção, archive bomb, traversal e formato não suportado;
- segunda revisão independente de privacidade e segurança.

**Critérios de saída:**

1. Hashes antes/depois comprovam zero escrita e nenhuma chamada de coleção/AnkiConnect existe.
2. Somente notas Multilang mapeáveis alimentam learner state; ambiguidade fica em quarentena.
3. Raw package/content é removido no prazo aprovado e exclusão é verificável.
4. Cold start é funcional; corrupção/ataque falha dentro dos limites sem vazamento/exaustão.
5. Privacy/security second review, termos de pacote/schema, custo de processamento e qualidade do mapping passam.

### Fase 48: Ranking adaptativo

**Resultado:** A prioridade adaptativa é explicável e determinística, separada do rank editorial, e organiza módulos/formas sem alterar histórico importado.

**Depende de:** Fases 45 e 47.

**Entregáveis:**

- diagnostics, marcação de itens conhecidos, metas e history signals minimizados;
- rank editorial imutável e adaptive priority versionada separados;
- modos `core_first`, `balanced` e `reading_first`, com explicação por componente;
- prerequisite eligibility, expansão opt-in e proveniência pessoal para custom/highlight;
- módulos determinísticos de 50–200 itens;
- `Important Forms` depois do lema, sibling burying e workload conforme `DEPEND-01`/`LOAD-01`;
- cold start, reset, override, audit e invalidação de policy.

**Critérios de saída:**

1. Snapshot/policy iguais produzem mesma fila, módulos e explicação.
2. Nenhum modo muda Core rank, GUID, membership ou review importado; expansão exige opt-in.
3. Forma não fica elegível antes do lema e siblings não são apresentados conjuntamente contra a policy.
4. Reset/cold start removem adaptação sem apagar conteúdo/histórico; override é reversível/auditável.
5. Sinais pessoais respeitam consentimento; custo computacional, efeitos e qualidade passam benchmarks/review.

### Fase 49: `Definitions`, sentenças, i+1 e áudio exato

**Resultado:** Conteúdo final combina identidade, sentido, forma, morfologia e conceitos conhecidos para gerar definições meaning-first, frases naturais/i+1 e áudio do texto exato.

**Depende de:** Fases 45 e 48.

**Entregáveis:**

- geração/curadoria condicionada por identidade, sentido, forma, analysis e known concepts;
- `Definitions` concisas com gramática contextual, inclusive distinção entre indicativo e irrealis em `were`;
- sentenças naturais com target matching sense-aware e policy strict/adaptive/contextual i+1;
- casos contextualizados `be/is/was/were` e formas equivalentes por idioma;
- `Exact-form audio` e áudio da sentença exata, com cache, hashes, locale/voz/provider e review;
- isolamento/redaction de custom/highlight, output LLM tipado/sanitizado e grounding/proveniência;
- rate limits, retries, budgets/hard caps, idempotência e drift invalidation.

**Critérios de saída:**

1. Toda saída aprovada casa identidade, sentido, análise e alvo; ambiguidade ou target ausente falha fechado.
2. `is`, `was` e os dois usos de `were` têm contexto/gramática/análise corretos, sem definição morfológica vazia.
3. i+1 nunca sacrifica naturalidade; strict exige exatamente o desconhecido permitido e os demais modos declaram incidental concepts.
4. Áudio casa por hash com forma/sentença exibida; cache evita nova cobrança e drift invalida conteúdo/asset dependente.
5. Dados pessoais, licença/grounding, custo/rate e qualidade/human review passam antes de export learner-ready.

### Fase 50: Ensaio de migração

**Resultado:** A migração é integralmente ensaiada em clone restaurado, com prévia assinada e rollback provado, sem aplicar qualquer mutation à instalação viva.

**Depende de:** Fases 46, 47, 48 e 49.

**Entregáveis:**

- inventário de tokens, ranks, IDs/GUIDs, schemas, configurações, assets, mídia e scheduling mappings antigos;
- classificação `1:1`, `merge`, `split`, `drop` ou `unresolved` por mapping, com confiança e perdas;
- prévia assinada vinculada aos hashes de source, target e backup, incluindo contagens, espaço, custo e mudanças de idioma;
- ensaio **somente** em clone restaurado e isolado;
- reuse de GUID antigo apenas em mapping 1:1 provado;
- proibição de transferir ou apagar scheduling em mapping ambíguo;
- testes de preservação isolada do scheduler, interruption/resume, journal, rollback, idempotência e unresolved blocking.

**Critérios de saída:**

1. Banco/config/assets vivos e Anki permanecem byte a byte intocados; toda mutation ocorre no clone.
2. Prévia e ensaio reconciliam contagens/mappings/perdas/custos; divergência invalida a assinatura.
3. Somente 1:1 reutiliza GUID/scheduling; merge/split/drop/unresolved nunca transfere ou apaga review ambiguamente.
4. Interrupção retoma pelo journal, rollback restaura hashes e segunda execução é no-op idempotente.
5. Regeneração coreana, exceção inglesa, Latim isolado, privacidade, licenças, custos e thresholds são auditados; unresolved bloqueia a Fase 51.

### Fase 51: Preflight, aplicação confirmada e release

**Resultado:** A instalação viva só migra após preflight completo e confirmação hash-bound; aplicação transacional, postflight, rollback e rollout gradual produzem release auditável.

**Depende de:** Fase 50.

**Entregáveis:**

- preflight estrutural, vertical, de clientes, privacidade, licença, custo, espaço, backup e qualidade antes de qualquer apply;
- prévia da Fase 50 revalidada contra source/target/backup atuais;
- confirmação explícita do usuário vinculada aos hashes e ao resumo de mappings/perdas/custo;
- transação de banco e staging de assets com switch atômico, journal e checkpoints;
- postflight, rollback automático/manual e reconciliação de IDs/GUIDs/mídia/scheduling;
- validação separada no Anki Desktop atual/anterior, AnkiDroid atual e AnkiMobile atual;
- pilots seguidos por famílias linguísticas, monitorando retention, leeches, time/item e abandonment;
- auditoria final do milestone, limitações e decisão separada de release/promoção.

**Critérios de saída:**

1. A sequência **prévia -> backup -> confirmação explícita** é tecnicamente obrigatória e a confirmação expira com qualquer hash/drift.
2. Nenhum apply começa antes de todos os checks; DB/assets mudam atomicamente ou rollback restaura o estado anterior.
3. Mappings 1:1 preservam IDs/GUIDs/scheduling; ambiguidades permanecem bloqueadas sem perda silenciosa.
4. Todos os quatro clientes-alvo passam separadamente; um resultado não substitui outro.
5. Pilots e famílias só avançam com privacidade/licença/custo/qualidade verdes e métricas dentro dos thresholds aprovados.
6. Postflight, rollback drill, monitoramento e auditoria não têm bloqueante aberto antes do release.

## 6. Contratos de gates transversais

### Gate de privacidade

**Evidência de entrada:** inventário de dados e finalidade; privacy class; consentimento granular; diagrama de fluxo; minimização; campos autorizados para provider; política de logs, retenção, exclusão, exportação e acesso; threat model atualizado.

**Condições bloqueantes:** consentimento ausente; finalidade indefinida; contexto bruto desnecessário; caminho/título/texto privado em log ou asset; envio a provider não autorizado; mistura de dados pessoais com assets compartilhados; ausência de exclusão verificável; APKG processado fora dos limites read-only/sandbox.

**Evidência de saída:** testes de minimização e redaction; prova de autorização; logs sanitizados; isolamento de storage; exercício de exportação/exclusão; hashes antes/depois do APKG; aprovação do responsável pelo gate. Custom, highlights e histórico APKG devem ter evidência separada por capacidade e perfil.

**Auditoria e retenção:** registrar versão da policy, consentimento, finalidade, acessos administrativos, subprocessadores, data de expiração e evidência de exclusão sem armazenar payload sensível no audit log. Retenção é mínima e configurável; backups seguem prazo e processo de expurgo documentados.

**Rollback/revogação:** revogar consentimento desabilita novos usos, remove o sinal da fila, agenda exclusão de payload/derivados e invalida caches pessoais. Incidente suspende a capacidade afetada por perfil; restore não pode reativar dados cujo consentimento expirou.

### Gate de licença

**Evidência de entrada:** fonte, proprietário, versão/checksum, método de aquisição, finalidade, termos, decisão de uso/derivação/redistribuição, atribuição e análise dos outputs derivados.

**Condições bloqueantes:** direito desconhecido ou incompatível; atribuição ausente; fonte sem versão reproduzível; redistribuição de asset derivado não aprovada; provider sem termos adequados; cadeia de proveniência quebrada. Asset pendente não pode ser commitado, empacotado nem publicado.

**Evidência de saída:** decisão assinada/revisada, texto de atribuição validado, manifest de derivados, teste de exportação da atribuição, checksum e lista de releases permitidos. Aprovação é por fonte, versão, finalidade e tipo de distribuição; não é genérica.

**Auditoria e retenção:** manter termos capturados ou referência durável, data, reviewer, escopo, atribuições publicadas e cadeia fonte->derivado->release durante a vida do derivado e pelo período legal aprovado.

**Rollback/revogação:** marcar a versão revogada, bloquear novos builds, localizar todos os derivados, retirar releases quando aplicável e reconstruir a partir de fontes aprovadas. Restore não pode reintroduzir asset revogado sem revalidação.

### Gate de custo

**Evidência de entrada:** dry-run por provider e capacidade; quantidade de itens/chars/áudio; preços/versionamento; cache hit esperado; retries; armazenamento/egress; budget e hard caps por item, lote, execução e período.

**Condições bloqueantes:** preço ou credencial/provider não aprovado; estimativa ausente; cap não configurado; operação excede cap; retry ilimitado; cache/idempotency ausente; expansão ou migração sem prévia de custo. Exceder limiar exige confirmação explícita nova, nunca continuação silenciosa.

**Evidência de saída:** estimativa vinculada ao snapshot de entrada, confirmação quando exigida, medição real reconciliada, chamadas/cache/retries auditáveis e prova de que hard caps interrompem com segurança antes de ultrapassar o limite.

**Auditoria e retenção:** registrar provider/version, unidade tarifável, quantidade, cache, tentativas, custo estimado/real e decisão, sem segredo. Reter dados agregados pelo período financeiro aprovado e dados itemizados somente quando necessários.

**Rollback/revogação:** cancelar novos jobs, preservar checkpoint idempotente e retomar apenas com novo budget. Assets já aprovados/cacheados permanecem reutilizáveis conforme licença; cobrança parcial aparece na auditoria e nunca é escondida por rollback de dados.

### Gate de qualidade

**Evidência de entrada:** limiares aprovados por perfil/capacidade; golden sets; amostras; validators para normalização, morphology, POS/sense, MWE, target matching, conteúdo, tradução, áudio, export e migração; plano de review humano.

**Condições bloqueantes:** análise indisponível/ambígua; sentido não aterrado; alvo ausente; idioma de explicação errado; exemplo/tradução incompatível; áudio não exato ou não aprovado; subdeck/GUID/mídia inválidos; contagem do Core incorreta; preview/migração divergente; métrica abaixo do limiar. Toda incerteza relevante falha fechado.

**Evidência de saída:** suites determinísticas, métricas por perfil e estrato, review dos itens obrigatórios, manifests/hashes, round-trip de export, comparação preview/execução e relatório de limitações. Aprovação de um perfil não aprova automaticamente outro.

**Auditoria e retenção:** reter versões de dados, analyzer, policy/prompt/provider, limiares, resultados agregados, amostra/review e artefatos necessários à reprodução. Mudança material invalida a evidência afetada e exige requalificação.

**Rollback/revogação:** suspender profile/capability/release afetado, reverter para última versão aprovada quando compatível, colocar derivados em quarentena e reconstruir/revisar. Correção nunca sobrescreve silenciosamente a evidência anterior.

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

Depois de os contratos da Fase 35 fecharem, persistência, fontes/cobertura e morfologia/curadoria podem avançar em paralelo somente com ownership e write sets separados; a integração ocorre no piloto da Fase 39. As pesquisas e rollouts linguísticos das Fases 40–44 podem ser paralelos apenas com ownership por idioma/família realmente disjunto. Schema compartilhado, contratos, manifests, freeze, export e integração permanecem controlados e serializados nas arestas acima. Gates transversais podem bloquear qualquer aresta, mesmo quando a dependência funcional anterior terminou.

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
| D-05 | 35, 37, 40–45 | Contagens/coverage por banda e freeze 66.000 provam Core e expansão sem drift | Coberto |
| D-06 | 35, 36, 38 e 45 | Contrato, persistência, goldens e freeze comprovam identidade versionada | Coberto |
| D-07 | 35, 38–45 e 49 | Regras/goldens/form packs e conteúdo final ligam forma, definição e áudio exatos | Coberto |
| D-08 | 35, 38–46 e 49 | Goldens/rollouts/edições/conteúdo provam MWE, sentido, rota e card role | Coberto |
| D-09 | 35, 46, 48 e 49 | Contratos/subdecks, proveniência adaptativa e isolamento de conteúdo pessoal | Coberto |
| D-10 | 47 | Hashes antes/depois, parser read-only e mappings com confiança/quarentena | Coberto |
| D-11 | 48 | Scores explicados, reset/override e diffs nulos em rank/histórico | Coberto |
| D-12 | 35 e 46 | Contrato de topology e inspeção APKG comprovam subdecks reais | Coberto |
| D-13 | 36, 50 e 51 | Backup/restore, rehearsal-only, confirmação hash-bound, apply e rollback | Coberto |
| D-14 | G0 e 35–51 | Matriz de gates, evidência de saída e bloqueios sem waiver implícito | Coberto |
| D-15 | G0 e 51 | Ausência de alteração ativa e registros separados de promoção/release | Coberto |

### 8.2 Capacidades e fases responsáveis

| Capacidade | Fase responsável | Dependências | Evidência de saída |
|---|---|---|---|
| Contratos CARD/FORM/SENSE/MWE/ROUTE/DEF/AUDIO/LOAD/DEPEND/GUID | 35 | G0 | Manifest completo, contagens, defaults e APKG feasibility aprovados |
| Persistência e backups | 36 | 35 | Restore, ORM/Alembic parity, fingerprints e estruturas inativas |
| Perfis e política de idioma | 35, 36 e 38–44 | G0 e contratos | 22 perfis qualificados individualmente; `la` persistido somente no caminho isolado |
| Registry de fontes/licenças e coverage | 37 | 35 | Pools >3000, corpora held-out, relatórios 1k/2k/3k/expansão e direitos auditados |
| Identidade lexical estável | 36, 38 e 45 | contratos/persistência | IDs reproduzíveis, sentidos separados e freeze sem duplicatas |
| Morfologia e target matching | 38 | 35 | 120/200 goldens, precisão aceita 100%, resolução >=98% e ambiguidade fail-closed |
| Piloto representativo | 39 | 36, 37 e 38 | 800 candidatos offline, todos os contratos e estimates/invalidation testados |
| Rollout românico | 40 | 39 | Cinco planos completos e 450 cards verticais |
| Rollout germânico | 41 | 39 | Seis planos completos e 540 cards verticais |
| Rollout eslavo/grego | 42 | 39 | Cinco planos completos e 450 cards verticais |
| Rollout aglutinativo | 43 | 39 | Três planos completos e 270 cards verticais |
| Rollout do Leste Asiático | 44 | 39 | Três planos completos e 270 cards verticais |
| Núcleo `Core 3x1000` | 45 | 40–44 | 66.000 IDs, 3000 por idioma e 1000 por banda |
| Expansão opcional | 45 | 40–44 | 0–3000 adicionais sem padding ou Core hash drift |
| `SurfaceForms`, `Important Forms` e workload | 35, 38, 40–45 e 48 | identidade/analyzers | Seleção justificada, fora da quota, sequencing/sibling burying e contagens por idioma |
| Reconhecimento padrão e papéis opcionais | 35 e 46 | contratos/freeze | Um reconhecimento por identidade; reverse/listening/cloze desabilitados por padrão |
| MWE/sentido/rota/card role | 35, 38–46 | contratos/analyzers/rollouts | Rotas reproduzíveis e ambiguidade bloqueada |
| GUID, edições e subdecks reais | 35, 36 e 46 | contratos/freeze | GUID semântico, mixed editions, updates 1:1 e hierarquia APKG real |
| Listas personalizadas | 35, 46, 48 e 49 | profile/export/adaptação/conteúdo | Proveniência privada, subdeck, prioridade e output isolado/redigido |
| Highlights | 35, 46, 48 e 49 | profile/export/adaptação/conteúdo | Contexto mínimo, provenance, subdeck e provider opt-in |
| Histórico APKG read-only | 47 | 46 | Parser sandboxed, raw deletion, zero escrita e learner state minimizado |
| Fila adaptativa | 48 | 45 e 47 | Modos, módulos 50–200, explicação/reset e facts imutáveis |
| `Definitions`, sentenças e i+1 | 49 | 45 e 48 | Conteúdo meaning-first/sense-aware, naturalidade e known-concept evidence |
| Áudio da forma/frase exatas | 49 | 45 e 48 | Hash texto-asset, cache, metadata, budget e review |
| Ensaio de migração | 50 | 46–49 | Preview assinado e clone-only com journal/rollback/idempotência |
| Apply e release | 51 | 50 | Preflight, confirmação hash-bound, switch atômico, clients e rollout auditado |

### 8.3 Aplicação dos gates por fase

| Fase | Privacidade | Licença | Custo | Qualidade |
|---|---|---|---|---|
| G0 | Regras/consentimentos inventariados e aprovados | Viabilidade por fonte/idioma documentada | Budgets e hard caps aprovados | Limiares e baseline/restore aprovados |
| 35 | Privacy classes/consentimento entram nos contratos | Semântica de direitos/atribuição fica obrigatória | Defaults, workload e caps ficam contratados | Os 12 contratos e contagens não admitem lacuna |
| 36 | Backup/acesso/retention protegem dados persistidos | Proveniência e licença sobrevivem ao schema | Storage/migration estimates são medidos | Restore e ORM/Alembic parity são obrigatórios |
| 37 | Corpora privados ficam separados/minimizados | Fonte/derivado/redistribuição é o gate central | Aquisição/scoring/storage têm caps | Coverage, dispersão e held-out são auditados |
| 38 | Quarentena/review retêm payload mínimo | Analyzer/modelo e goldens têm termos aprovados | Compute/review medidos e capados | 100% precisão aceita, >=98% resolução e fail-closed |
| 39 | Piloto offline não usa dados pessoais brutos | Somente fontes aprovadas entram nos 800 casos | Provider pago default zero; estimates reportados | Threshold falho invalida/bloqueia rollout |
| 40 | Amostras românicas não misturam dados pessoais | Cinco source plans têm decisão individual | 450 cards e voz são orçados sem chamada implícita | Checklist/90 cards/goldens e review passam |
| 41 | Amostras germânicas não misturam dados pessoais | Seis source plans têm decisão individual | 540 cards, pitch/stød e voz são estimados | Capitalização/compostos/variantes passam review |
| 42 | Amostras eslavas/gregas minimizam contexto | Cinco source plans têm decisão individual | 450 cards/stress/voz são estimados | Caso/aspecto/script/identidade passam review |
| 43 | Amostras aglutinativas minimizam contexto | Três source plans têm decisão individual | 270 cards e análise longa têm caps | Cadeias/derivação/forms passam 200 goldens |
| 44 | Dados coreanos v3 permanecem intactos/privados | Três source plans e scripts têm direitos claros | 270 cards, leitura/voz/regeneração estimados | UniDic/segmentation/Kiwi e policy coreana passam |
| 45 | Core/form packs não incorporam payload pessoal | 66.000 IDs/manifests têm licença aprovada | Rebuild/review/expansão dentro de budget | Contagens exatas, zero contaminação, second review |
| 46 | Custom/highlight isolados em edições/subdecks | Atribuição/mídia acompanha cada export | APKG/CSV/TSV/tamanho dentro de caps | GUID/update/subdeck/model/media round-trip válidos |
| 47 | Consentimento, sandbox, retenção e zero escrita | Uso do pacote/schema respeita termos aplicáveis | Limites de arquivo/CPU/memória | Archive/SQLite/schema/mapping validados |
| 48 | Só sinais autorizados; reset/exclusão propagam | Sinais mantêm origem/restrições | Score/módulos têm budget computacional | Determinismo, prerequisites, burying e efeitos auditados |
| 49 | Input pessoal é isolado/redigido antes de provider | Grounding/output/voz têm direitos aprovados | Cache/rate/retry/hard caps bloqueiam excesso | Sense/target/i+1/Definition/audio exatos e sanitizados |
| 50 | Só clone restaurado; live/private data não muta | Mappings/assets preservam direitos no ensaio | Preview mostra provider/storage/apply estimado | 1:1/ambiguidade/journal/rollback/idempotência passam |
| 51 | Consentimento/retenção revalidados antes do apply | Licenças/atribuições/revogação verdes no preflight | Confirmação inclui custo e caps de rollout | Apply/postflight/clients/pilots/métricas sem bloqueante |

### 8.4 Invariantes da migração

| Invariante de migração | Evidência da prévia | Evidência de backup/restauração | Confirmação | Comportamento de falha/rollback |
|---|---|---|---|---|
| IDs estáveis | Fase 50 classifica 1:1/merge/split/drop/unresolved e lista IDs/GUIDs | Fases 36/50 restauram clone e reconciliam referências/hashes | Fase 51 exige aceite hash-bound dos mappings 1:1 e perdas permitidas | Conflito/ambiguidade bloqueia; journal/rollback restaura referências |
| Dados do usuário/privados | Fase 50 lista classe, consentimento, retenção e transformação | Backup controlado é restaurado no clone e testa exclusão | Fase 51 destaca payload pessoal e usos autorizados | Vazamento/consentimento inválido impede apply e remove derivados |
| Histórico de estudo | Fases 47/50 listam reviews, confiança, quarentena e perdas; só 1:1 transfere | Pacote original fica intacto e mappings são restaurados isoladamente | Fase 51 explicita mappings 1:1; ambíguos não transferem/apagam | Nunca escrever no Anki; mapping incerto fica em quarentena/rollback |
| Coreano português->inglês | Fases 44/49/50 quantificam regeneração, review, custo e diff de policy | Conteúdo v3 português permanece recuperável no backup/clone | Fase 51 confirma regeneração, nunca relabel | Falha mantém português v3 e bloqueia release v4 |
| Explicações do inglês-alvo em português | Prévia comprova que `en` mantém português, inclusive forms | Restore preserva conteúdo/policy aprovada | Confirmação inclui a exceção normativa | Conversão indevida bloqueia postflight e reverte lote |
| Isolamento do Latim | Prévia comprova zero `la` no mapping moderno e português preservado | Restore do caminho latino passa hashes isolados | Confirmação explicita exclusão do Latim da migration moderna | Qualquer mutation moderna em `la` bloqueia e restaura isolamento |
| Assets e mídia | Fase 50 lista reuse/regenerate/drop, hashes, espaço e licença | Bytes/manifests são restaurados e resolvidos no clone | Fase 51 aceita staging/switch e descarte pelo hash da prévia | Falta/hash/licença impede switch; rollback restaura manifest/bytes |
| Custos de provider | Prévia estima provider/capacidade/storage e hard caps | Backup/restore não depende de chamada paga | Confirmação é vinculada ao orçamento vigente | Cap interrompe antes do excesso; resume reutiliza cache/journal |
| Interrupção e retomada | Fase 50 define lotes, checkpoints e falhas ensaiadas | Clone testa restore completo e por journal | Fase 51 aceita estratégia transacional/resumível | Apply incompleto reverte ou retoma atomicamente sem estado híbrido |
| Idempotência de rerun | Ensaio prevê segunda execução sem mudança salvo drift declarado | Snapshot permite comparação antes/depois/repetição | Confirmação vincula versões exatas de código/dados | Drift invalida confirmação; rerun não duplica IDs/cards/assets/custos |

A auditoria conclui que as 15 decisões fixas, todos os contratos explícitos, as 23 linhas de requisitos linguísticos, G0 e as Fases 35–51 possuem ownership, dependências e evidência posterior consistentes com a alocação fixa. Itens externos ainda sem prova permanecem bloqueados nos gates; nenhum foi silenciosamente aprovado por este documento.
