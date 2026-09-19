# Curso de partículas e terminações do coreano

O conteúdo versionado fica em `data/korean_grammar/v1/`: 108 cartões de gramática,
com exemplos coreanos originais, tradução para português, formação, registro,
notas de uso, vocabulário e pré-requisitos explícitos.

## Organização

- **G0: 8 cartões de introdução guiada.** Explicam cópula, forma de dicionário,
  radical, substantivo, verbo, adjetivo, ordem da frase e omissão contextual.
  Este bloco não alega um único conceito desconhecido por cartão.
- **G1–G13: 100 cartões de gramática.** A sequência pressupõe o guia completo,
  o vocabulário lexical de apoio e os cartões anteriores. A verificação
  recalcula os conceitos desconhecidos de cada anotação, exigindo somente o alvo.
- **Apoio: 57 entradas lexicais e 29 usos construcionais.** Os usos de uma palavra
  que pertencem a uma construção são introduzidos pelo cartão dessa construção,
  e não apresentados antecipadamente como simples vocabulário conhecido.

O bootstrap tem 57 cartões próprios, definidos em `bootstrap-lessons.json`,
antes de G0. Cada um apresenta o lema, sua definição e um contexto em português
que distingue o sentido selecionado. O lema isolado é um rótulo lexical; não
antecipa domínio de conjugação. A sequência exportada tem, portanto, 165 notas.
No G7, a regra de bieup ensina explicitamente `춥다 → 추워요` e
`쉽다 → 쉬워요`, preparando a reutilização de `쉬워요` no G10.

As observações semânticas cobrem os exemplos e as amostras faladas. São dados
explícitos sujeitos à revisão, não uma inferência feita por espaços, sufixos ou
busca literal. Os `target_surfaces` são âncoras editoriais; não provam identidade
morfológica. O resultado `resolved` do Kiwi também não prova concordância entre
todas as alternativas de lema, classe e sentido.

## Preparar e ler

```bash
uv run multilang korean prepare-grammar-course --output-dir .multilang/grammar-review
```

O comando é local e não chama serviços pagos. Produz `index.html`, `cards.csv`,
`course.json`, `lexical-support.json`, `grammar-observations.json`,
`evidence-schema.json`, `preflight.json` e `manifest.json`. Abra `index.html`
para ler o guia, o vocabulário e todos os cartões. O diretório de destino deve
ser novo; uma execução não sobrescreve uma revisão anterior.

`--no-analyze` omite a execução do Kiwi, mantendo essa ausência explícita no
relatório. `--source-dir` permite preparar uma versão editada dos quatro JSONs;
as referências ao curso precisam acompanhar seu hash atual.
`--lexical-source-bundle` permite verificar linhas adicionais contra o snapshot
NIKL completo já aprovado. Sem essa opção, a fonte é o extrato mínimo incluído
no pacote, cujo hash é fixado no código.

O manifesto vincula os bytes reais dos arquivos. Alterações em texto, sentidos
ou observações invalidam as respectivas evidências. O preflight informa o hash
do curso e do conjunto de apoio, a progressão recalculada e a lista exata de
textos para áudio. O áudio do vocabulário de apoio é uma etapa adicional.

## Compilar para o fluxo existente

```bash
uv run multilang korean build-grammar-course \
  --evidence evidence.json --output grammar-bundle.json
```

O arquivo de evidências segue `evidence-schema.json`. Deve conter os hashes
atuais do curso e do apoio, todas as entradas do bootstrap lexical e uma
entrada de evidência para cada lição. Fornece fontes, observações, pronúncia,
revisões e vínculos de mídia reais; não substitui o texto autoral.

As identidades lexicais são `lexicon:<entry_id>` e vinculam o hash canônico da
entrada completa de apoio (incluindo sentido e uso), além da linha exata da
fonte. Somente entradas `teaching_mode=lexical` entram no bootstrap. As
identidades gramaticais são `grammar:<entry_id>`. O contrato já existente de
currículo inclui o fechamento dos pré-requisitos nos conceitos observados;
a anotação separada conserva quais conceitos aparecem no exemplo. Não se
confundem pré-requisitos didáticos com morfemas presentes na frase.

G0 usa evidência `contextual` e fica em `orientation_entries`; G1–G13 usam
`strict` e ficam em `grammar_entries`. Todos os conceitos de G0 se tornam
conhecidos somente depois de validar o guia inteiro. Fonte, revisão e mídia
continuam obrigatórias para cartões prontos. As notas de uso são preservadas
no campo de formação do bundle. Bundles antigos sem guia conservam seus hashes.

O resultado alimenta o fluxo já existente de importação, processamento e
exportação de gramática. A exportação verifica novamente fontes, revisões,
estado atual das fundações e bytes reais do áudio; uma prévia não é uma
autorização de publicação nem um `.apkg` aprovado.

## Verificar a entrega

`korean_grammar_morphology` conserva os dois caminhos reais do analisador e exige
uma escolha contextual explícita, com referências de morfemas para cada lema,
classe, sentido e construção. Concordância estrutural não se transforma em
aprovação linguística automática.

`korean_grammar_release.prepare_release_candidates` congela todo o conteúdo
visível e o grafo para revisão. `validate_release_reviews` exige três pareceres
independentes sobre os 165 candidatos exatos. `assemble_reviewed_release` refaz
o plano e rejeita alterações em texto, fonte, dependências ou mídia. O recibo
final também verifica a execução das sessões de revisão e os hashes dos
resultados brutos, incluindo cada julgamento atômico.

As análises de áudio vinculam a transcrição ou avaliação de pronúncia aos bytes
MP3 e ao WAV decodificado. A entrega exige integridade do sinal e transcrição
correspondente ou avaliação com precisão mínima 90, completude 95 e precisão
por palavra 80, sem omissões ou inserções. O status é
`automated_integrity_passed`; não representa audição humana nem certificação
de todos os contrastes fonéticos ou da entonação de perguntas. Cada chamada
fica reservada em um journal, inclusive resultados desconhecidos; retomadas
respeitam o orçamento acumulado e não repetem chamadas automaticamente.

As posições dos cartões novos no Anki seguem a sequência de ensino. Reimportar
o mesmo pacote conserva as identidades e o histórico de estudo.

## Entrega local concluída — 2026-09-19

Pacote: `.multilang/verification/korean-grammar/production/delivery/coreano-gramatica-v1.apkg`.
Contém **165 notas/cartões**, na ordem: 57 de vocabulário, 8 de introdução
guiada G0 e 100 de gramática G1–G13. Os 159 MP3s distintos, sintetizados com
Azure `ko-KR-SunHiNeural`, atendem aos 330 campos de áudio de palavra e frase.
Textos iguais reutilizam o mesmo arquivo. O campo Image permanece vazio.

As 216 análises morfológicas reais foram verificadas e suas escolhas contextuais
foram incluídas nos três pareceres de IA sobre o conteúdo final. Todos os 165
candidatos receberam aprovação nos sete critérios de cada parecer. Os recibos
preservam os julgamentos, a execução e o escopo de independência: contextos
separados do mesmo modelo, cuja versão não foi informada pelo runtime.

Todos os áudios passaram pelos critérios automatizados descritos acima. Para
uma frase em que o ASR do Azure divergiu na grafia, três transcrições independentes
do áudio, sem acesso ao texto esperado, concordaram exatamente com o alvo.
Os resultados originais do Azure continuam preservados; os limites de avaliação
não foram reduzidos. Os nomes dos arquivos exportados usam o hash dos bytes,
evitando a renomeação automática de nomes longos pelo Anki.

A verificação usou uma coleção temporária no backend **Anki 26.8.1**: importação,
campos, mídia, ordem inicial e reimportação após uma revisão de estudo passaram.
O HTML produzido pelo Anki passou por **660 verificações** no Chromium, em
larguras de 1280 e 390 pixels, sem transbordamento horizontal ou erros de página.
Os **159 arquivos de áudio** reproduziram até o fim. A suíte específica passou
com **101 testes**. Esses resultados cobrem backend e navegador; a interface
nativa do Anki Desktop e os aplicativos móveis ainda não foram exercitados.

O resumo versionado fica em `data/korean_grammar/v1/production-review-summary.json`.
Os recibos completos ficam no diretório local de produção, incluindo
`delivery/review-receipt.json`, `delivery/anki-backend-report.json` e
`delivery/browser-report.json`. O SHA-256 do pacote é
`11ef7e9d4007746e9b9cc4c5f9b8a54a289177bd3ad397eeb853845a406f3419`.

A prévia gerada por `prepare-grammar-course` continua sendo um artefato de autoria,
sem anexar automaticamente os recibos dessa entrega. Seu estado pendente de
revisão não invalida o pacote final vinculado acima. A conclusão desta entrega
de gramática está registrada como KPROD-03; os demais itens de produção coreana
permanecem em `.planning/KOREAN-PRODUCTION-BACKLOG.md`.
