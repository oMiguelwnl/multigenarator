# Plano dos decks de japonês

Data: 20/09/2026. Escopo solicitado: pesquisar as fontes, detalhar o plano e implementar frequência, kana e highlights. A referência inicial de frequência é um núcleo de 3.000 entradas em três níveis. **3.000 não é um limite de cartões para o japonês nem para qualquer outra língua**: vocabulário adicional, sentidos distintos e formas importantes podem ampliar o total conforme sua utilidade e qualidade. Os comandos estão em [japanese-generation.md](japanese-generation.md).

Organização adotada: cartões adicionais de uma entrada existente permanecem no nível dessa entrada; vocabulário novo além do núcleo usa expansões de frequência. Assim, um nível pode ter 1.000 entradas principais e mais de 1.000 cartões. Sentidos lexicais distintos mantêm identidades próprias. Faixas de frequência não equivalem automaticamente a níveis de proficiência.

## Ponto de partida e resultado esperado

O arquivo de frequência japonês existente, `assets/frequency/ja/curated-v1.csv`, deriva do fluxo de wordfreq. Ele continua ativo até a revisão e ativação de uma nova edição. O comando antigo `export-japanese` gera uma coleção demonstrativa de 12 exemplos; ele não representa os três níveis completos.

O deck de kana já tinha 208 cartões de símbolos e combinações. A implementação conserva esses cartões e seus GUIDs, acrescenta dez lições explícitas de leitura e permite gerar áudio e traços verificáveis. O campo de imagem manual permanece vazio.

Os highlights passam pela análise lexical japonesa: o modo `text` extrai palavras de um trecho; `vocabulary` preserva expressões selecionadas. Lema, leitura, classe gramatical e posição no texto são rastreáveis. Trechos particulares não se tornam arquivos públicos de frequência.

Os três caminhos reutilizam os serviços existentes de geração, tradução, validação, persistência e exportação. As adaptações japonesas tratam análise, leituras, fontes e campos específicos da língua.

## Escolha das fontes

| Função | Fonte | Decisão implementada |
| --- | --- | --- |
| Candidatos de frequência | TUBELEX-JA, tabela UniDic 3.1.0 base | Importar contagens e dispersão por vídeos/canais; comparar com wordfreq antes de congelar uma edição. Manter a variante lemma separada. |
| Evidência lexical | JMdict_e da EDRDG | Preservar escritas, leituras, POS, sentidos, etiquetas e restrições. IDs e ordinais identificam evidência do snapshot; identidades semânticas exigem revisão. |
| Análise e leitura | Fugashi + UniDic explicitamente selecionado | Usar o mesmo dicionário em análise, furigana e romaji; registrar o hash dos arquivos reais. Permitir UniDic completo instalado e o modo local explícito UniDic-lite. |
| Comparação e lacunas | wordfreq e importador existente de Wiktextract | Manter como evidência complementar, sem substituir uma leitura ou um sentido ambíguo por suposição. |
| Traços de kana | KanjiVG | Fixar um commit, verificar arquivos, preservar atribuição e licença, recompor SVGs seguros e informar cobertura. |
| Áudio | Azure Speech, ja-JP | Usar a voz configurada e cache por texto/voz/localidade/formato; exigir MP3 válido na exportação com áudio. |

TUBELEX é a fonte candidata recomendada para a nova edição, pela disponibilidade de contagens e dispersão que podem ser inspecionadas. A comparação executada mede diferenças de cobertura e ordenação; não demonstra, sozinha, qual lista produz o melhor aprendizado. Contagem de uma escrita também não é contagem de um sentido: o importador não inventa ocorrências nem divide contagens entre leituras.

Fontes primárias: [TUBELEX](https://github.com/naist-nlp/tubelex), [avaliação publicada](https://aclanthology.org/2025.coling-main.641/), [JMdict](https://www.edrdg.org/wiki/JMdict-EDICT_Dictionary_Project.html), [termos EDRDG](https://www.edrdg.org/edrdg/licence.html), [Fugashi](https://github.com/polm/fugashi), [KanjiVG](https://github.com/KanjiVG/kanjivg), [vozes Azure](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts).

JMdict exige atribuição CC BY-SA 4.0 e o procedimento de atualização documentado pela EDRDG. KanjiVG exige atribuição CC BY-SA 3.0. A decisão de redistribuição das tabelas TUBELEX é registrada separadamente da licença do software. Corpora NINJAL podem servir de comparação futura, sujeitos aos termos de cada arquivo; não foram incorporados.

## Etapa 1 — Aquisição e preparação lexical

- [x] Integrar JMdict em `native vocabulary prepare --dictionary-format jmdict`.
- [x] Verificar SHA-256 e limites; rejeitar entidades externas/expansivas, restrições inválidas e seleção de língua incompatível.
- [x] Preservar relações permitidas entre escrita, leitura e sentido, POS herdado e etiquetas de uso.
- [x] Importar TSV TUBELEX simples/comprimido, incluindo tokens que contêm aspas, e validar contagens/totais.
- [x] Adicionar fontes japonesas explícitas ao catálogo de aquisição HTTPS.
- [x] Implementar `prepare-japanese`, com candidatos, comparação, diagnóstico e manifesto versionável.
- [x] Integrar revisão e cache ao fluxo existente com `export-japanese-cache`.
- [x] Implementar `japanese-frequency-review-payload` e `freeze-japanese`: verificar recibos, seleção e exatamente 3.000 entradas através do leitor comum de frequência.

Entregáveis: importadores, catálogo, comandos e arquivos de preparação. Critério técnico: uma contagem agregada nunca aparece como evidência de ocorrência ou frequência de um sentido.

## Etapa 2 — Análise japonesa compartilhada

- [x] Selecionar explicitamente o dicionário e registrar seu fingerprint, sem download ou troca silenciosa.
- [x] Separar superfície, base ortográfica, lema, leitura, POS e posições exatas no texto.
- [x] Rejeitar correspondências por substring como `日` em `日本` e `生` em `学生`; aceitar flexões e expressões completas quando a análise permite.
- [x] Relatar ausência ou ambiguidade de evidência para revisão.
- [x] Preservar espaços e pontuação no furigana; gerar romaji a partir da leitura aceita.
- [x] Conservar leituras revisadas após persistência e usá-las na validação e no SSML da palavra.

Entregáveis: analisador local compartilhado e integração com geração textual e áudio. Critério técnico: texto escrito e leitura revisada permanecem relacionados em todas as etapas.

## Etapa 3 — Importação e exportação de highlights

- [x] Extrair tokens japoneses em `text`, mantendo proveniência e ignorando espaços e números de calendário sem tratá-los como erros lexicais.
- [x] Resolver uma palavra flexionada para sua base e preservar expressões intencionais em `vocabulary`.
- [x] Distinguir candidatos por lema, leitura e POS, sem fundir homógrafos indiscriminadamente.
- [x] Criar contrato japonês de 11 campos, com leitura, romaji e áudio, e identidade própria de modelo Anki.
- [x] Manter os 12 campos da frequência e a imagem manual vazia.
- [x] Verificar montagem, exportação TSV/APKG, escape de HTML e estabilidade das identidades.

Entregáveis: extração, resolução lexical e modelo de highlights japonês. Critério técnico: TSV e APKG concordam nos campos; notas antigas de sete campos exigem migração explícita de tipo no Anki.

## Etapa 4 — Deck de kana e confiabilidade do áudio

- [x] Conservar os 208 cartões originais e seus GUIDs.
- [x] Adicionar dez lições identificadas sobre tsu pequeno, duração, kana pequenos, leituras de partículas e katakana semelhantes.
- [x] Corrigir `dji/dzu` para `ji/zu` na apresentação sem mudar GUIDs antigos.
- [x] Usar `あん。`/`アン。` no áudio de ん/ン, com explicação no cartão: a síntese isolada de ん falhou na geração real.
- [x] Adquirir e verificar traços KanjiVG; preservar avisos de copyright e atribuição nas adaptações.
- [x] Reutilizar áudio válido e rejeitar arquivos ausentes/corrompidos; permitir retomada após falha.
- [x] Oferecer `--prototype` sem áudio e registrar essa condição no manifesto.
- [x] Gerar pacote com áudio real e conferir seu conteúdo, mídia e GUIDs.

Entregáveis: 218 cartões, 109 por escrita, com explicações em português, áudio e traços estáticos. `Strokes` recebe o SVG; `Gif` e `Picture` ficam vazios. Animação não foi implementada.

## Etapa 5 — Integração, piloto e documentação

- [x] Executar regressões de frequência, highlights, áudio, exportação e contratos CLI.
- [x] Exercitar análise local real com compostos, flexões, leituras, pontuação e múltiplas escritas.
- [x] Preparar piloto de 100 entradas de frequência e 24 exemplos originais de análise/highlights.
- [x] Preparar o inventário padrão de 6.000 candidatos a partir das fontes reais.
- [x] Documentar aquisição, preparação, revisão, ativação, síntese e exportação.
- [x] Separar resultados automáticos de aprovação linguística e publicação do conteúdo definitivo.

Estratégia de testes: casos de comportamento antes da implementação, fontes sintéticas pequenas nos testes unitários, análise Fugashi real e inspeção do APKG. Testes com fixtures não chamam provedores. As aquisições e a síntese real foram executadas separadamente e deixaram recibos e manifests locais.

## Resultados verificados em 20/09/2026

| Verificação | Resultado |
| --- | --- |
| Fonte TUBELEX base adquirida | 405.505 entradas, com hash do snapshot preservado. |
| Piloto de 100 palavras | 98 com evidência JMdict; 97 com múltiplos candidatos lexicais. As duas sem evidência são os marcadores `<num>` e `[音楽]`. |
| Comparação do piloto | 57 palavras compartilhadas entre os respectivos top 100 de TUBELEX e wordfreq. |
| Inventário padrão de 6.000 palavras | 5.722 com evidência JMdict; 4.459 com múltiplos candidatos; 26.176 combinações lexicais para revisão. |
| Diagnóstico JMdict | Um sentido com restrições incompatíveis ficou em quarentena; nenhum par de escrita/leitura foi inventado. |
| Piloto morfológico | 24/24 expectativas de aceitação/rejeição atendidas; dicionário local registrado por hash. |
| Kana | 218 cartões, 218 MP3s decodificáveis com sinal sonoro e traços em todos os cartões; GUIDs da base preservados. |
| Áudio de kana | Azure `ja-JP-NanamiNeural`; duração dos arquivos de 1,104 a 5,952 segundos. |
| KanjiVG | Commit `422b5538595676da918c288a4230cb5e22a1ee7e`, 161 glifos adquiridos, nenhum arquivo necessário ausente. |
| Testes | 448 casos distintos com resultado mais recente aprovado; lint dos módulos alterados aprovado. |

Os arquivos estão em `.multilang/verification/japanese-implementation/`: `inventory-6000/`, `pilot-100/`, `pilot-report.json`, `test-summary.json`, `package-verification.json` e `artifacts/japanese-kana.apkg`. Scripts locais permitem reproduzir os pilotos e a inspeção do pacote. O resumo de testes registra também o recheck aprovado de um teste de mandarim alterado concorrentemente; a implementação de mandarim não foi modificada nesta tarefa.

## Conteúdo definitivo ainda necessário

As etapas implementadas entregam a capacidade de geração. Os comandos de congelamento descritos aqui tratam o núcleo inicial de 3.000 entradas, não o limite total de cartões da língua. A edição inicial de frequência ainda requer:

1. Selecionar 3.000 identidades lexicais e resolver leituras/POS/sentidos a partir dos candidatos preparados.
2. Registrar a decisão de redistribuição vinculada aos snapshots e à seleção.
3. Congelar e ativar a nova edição; gerar os três níveis pelo fluxo comum.
4. Revisar definições, exemplos, traduções e áudios de palavra/frase.
5. Conferir o pacote no cliente Anki antes de publicar.

Nenhum recibo de revisão independente foi fabricado. Os 3.000 cartões definitivos de frequência ainda não foram gerados. A revisão do áudio por falante nativo e a conferência no cliente Anki também não foram realizadas para o kana; a inspeção automática verificou estrutura e mídia. A comparação entre UniDic completo e lite, assim como corpora alternativos, permanece uma opção de avaliação.
