# Multilang Output — lógica dos decks e template

**Estado:** proposta de design, 20 de setembro de 2026. **Confirmado:** perguntas em inglês; entrega de lógica completa e protótipo visual. Temas, quotas, variedades linguísticas e detalhes do piloto abaixo são propostas. [Protótipo interativo](../output/previews/output-deck/prototype.html). Esta etapa não gera decks APKG, áudios ou notas de produção.

**Revisão visual confirmada pelo usuário:** frases como elementos principais; instrução curta; remoção de “Optional speaking extension” e “What counts as correct?”, além de parágrafos explicativos no cartão. Áudio automático **ao revelar a resposta**, com botão ▶ para repetir. O [HTML completo](../output/previews/output-deck/card.html) usa síntese de voz do navegador para demonstrar a interação; depende das vozes disponíveis no dispositivo. Os arquivos Azure da versão final continuam sendo uma etapa futura.

## 1. O que o deck treina

O aluno lê uma intenção expressa em inglês, entende a situação e **fala uma frase na língua estudada antes de revelar a resposta**. O objetivo é recuperar vocabulário e construções para falar: pedir, explicar, recusar, descrever, negociar e justificar. A tradução funciona como ponto de partida; a resposta deve soar natural naquele contexto.

Cada card tem uma intenção comunicativa e um foco principal verificável. “Classe gramatical” descreve palavras, como substantivo ou verbo. Para uma frase, a instrução deve indicar **construção, tempo, aspecto, caso, ordem, registro ou ato comunicativo**. Exemplo: “Faça um pedido educado usando o Konjunktiv II de haben”, em vez de “classe gramatical: verbo”.

A proposta é uma família independente, `Multilang Output`, com novo note type e campos próprios. Não inverter automaticamente os decks de vocabulário: uma frase útil para reconhecer uma palavra pode ser ambígua ou inadequada como pergunta de produção.

Há suporte limitado para a escolha de recuperação produtiva: Yanagisawa encontrou benefício no teste produtivo em estudo com 18 universitários e pseudopalavras. Isso não demonstra fluência com este deck. Mizugaki, com 67 estudantes, não encontrou diferença geral significativa entre condições com expressões e frases. Portanto, escolhemos frases pela utilidade comunicativa, sem afirmar superioridade universal. [Yanagisawa, 2016](https://www.jstage.jst.go.jp/article/katejournal/30/0/30_11/_article/-char/en); [Mizugaki, 2025](https://www.jstage.jst.go.jp/article/jaselejournal/36/0/36_161/_article/-char/en).

## 2. Unidade de estudo e fluxo

**Frente:** idioma e nível discretos; tema; situação curta; frase em inglês em destaque; foco obrigatório; indicação para falar; dica opcional recolhida. Situação e instruções também ficam em inglês, mantendo a língua de apoio consistente.

**Verso:** frase inglesa e resposta principal em destaque, botão de áudio ao lado da resposta, variantes válidas e leitura opcional recolhidas. Contexto e instrução não se repetem no verso. Sem blocos de explicação, critérios de correção ou exercício extra. O campo `Image` existe e permanece vazio para preenchimento manual posterior.

Sequência de revisão:

1. Ler situação, frase e foco. Formular e falar sem consultar o verso.
2. Se necessário, abrir uma dica estrutural; depois, uma dica lexical. Ambas são opcionais; consultá-las torna a tentativa assistida, mesmo que o aluno feche a dica depois.
3. Revelar. Comparar o que foi efetivamente dito com o sentido, o foco e o registro esperados.
4. Ouvir o modelo, observar a diferença e repetir uma vez para corrigir. Essa repetição não transforma a tentativa inicial em acerto.
5. Avaliar a recuperação inicial e avançar para o próximo cartão.

Não exigir digitação como resposta padrão. Não apresentar a tradução-alvo na frente, nem por áudio escondido. A instrução obrigatória faz parte da pergunta: lê-la **não** equivale a usar dica. Dicas devem orientar a recuperação, sem simplesmente exibir a frase completa.

## 3. Quando a resposta está correta

Aceitar respostas que preservem sentido, intenção, informações relevantes e registro, cumprindo o foco obrigatório. Não exigir correspondência palavra por palavra. Uma variante regional compatível pode estar correta; uma frase gramatical que muda negação, quantidade, pessoa ou tempo pode não estar.

As variantes exibidas no verso precisam **cumprir o exercício**. Alternativas que comunicam a ideia sem praticar o foco ficam nas notas de autoria, fora da interface de estudo. Quando o aluno produz uma forma natural fora da construção pedida, reconhecer a validade comunicativa e considerar o objetivo específico ainda não recuperado. Se a equivalência for incerta, marcar para revisão; a lista de variantes não pretende enumerar toda a língua. Os critérios desta seção são regras de curadoria e de uso; não formam um bloco de texto no cartão.

| Botão | Regra proposta para este deck |
|---|---|
| Again | Errou o sentido ou foco, não recuperou a frase ou consultou uma dica opcional. |
| Hard | Acertou sentido e foco **sem ajuda**, mas com muita hesitação. |
| Good | Acertou sem ajuda, com esforço normal de recuperação. |
| Easy | Acertou imediatamente, com segurança e sem ajuda. |

Esta adaptação conserva a distinção do Anki entre falha e acerto difícil. Usar Hard para esquecimento prejudica a interpretação do histórico. Dicas são avaliadas manualmente: o template não registra seu uso no agendador nativo. O tempo também não deve virar aprovação automática. [Botões de resposta](https://docs.ankiweb.net/studying.html#answer-buttons); [opções de agendamento](https://docs.ankiweb.net/deck-options.html#fsrs).

Para pronúncia, não exigir imitação perfeita do sotaque. Considerar erros que comprometem a mensagem ou um contraste explicitamente praticado; detalhes novos devem virar outro objetivo. O MVP não terá nota automática de fala.

## 4. Três níveis de 1000 cards

Cada idioma terá **3000 notas e 3000 cards**, distribuídos em três níveis de 1000. Os níveis expressam dificuldade pedagógica deste currículo; não são equivalência CEFR, ranking de frequência ou promessa de proficiência.

| Nível | Objetivo | Perfil das frases |
|---|---|---|
| L1 — Falar no cotidiano | Necessidades, preferências, pessoas, rotina, perguntas e pedidos. | Enunciados curtos; uma oração como ponto de partida; fórmulas úteis e vocabulário básico. |
| L2 — Conectar ideias | Relatar, comparar, explicar problemas, combinar planos e trabalhar. | Expansão de tempos e aspectos; conexões simples; mais escolhas de registro. |
| L3 — Expressar nuances | Argumentar, negociar, explicar consequências e falar de assuntos abstratos. | Hipóteses, ressalvas e relações entre ideias, conforme a língua. |

Comprimento é sinal auxiliar, não critério universal: contar espaços não mede igualmente alemão, japonês e coreano. Negócios e economia ganham espaço depois da base; no início, trabalho significa atividades concretas e situações frequentes.

### Matriz inicial de temas

Cada card pertence a **um tema principal para contagem**, com tags secundárias opcionais. As quotas abaixo somam exatamente 1000 por coluna e podem ser revistas antes da produção.

| Tema proposto | L1 | L2 | L3 |
|---|---:|---:|---:|
| Apresentações e convivência | 100 | 40 | 20 |
| Família e relações | 70 | 35 | 20 |
| Rotina e tempo | 100 | 50 | 20 |
| Casa e tarefas | 70 | 45 | 25 |
| Comida, bebidas e restaurante | 100 | 65 | 40 |
| Compras e serviços | 80 | 60 | 45 |
| Corpo, saúde e cuidados | 70 | 60 | 50 |
| Emoções e necessidades | 50 | 55 | 50 |
| Cidade, transporte e direções | 70 | 45 | 30 |
| Viagens e hospedagem | 60 | 60 | 45 |
| Clima e natureza | 30 | 30 | 30 |
| Estudos e aprendizagem | 40 | 45 | 40 |
| Lazer, cultura e esportes | 40 | 35 | 30 |
| Tecnologia e comunicação | 25 | 50 | 55 |
| Trabalho e carreira | 40 | 75 | 70 |
| Negócios, reuniões e negociação | 10 | 70 | 100 |
| Dinheiro e finanças pessoais | 25 | 45 | 50 |
| Economia e notícias | 0 | 35 | 95 |
| Sociedade e ambiente | 10 | 35 | 65 |
| Opiniões, decisões e argumentos | 10 | 65 | 120 |
| **Total** | **1000** | **1000** | **1000** |

Partes do corpo entram em ações comunicativas: indicar dor, localizar um ferimento, descrever movimento. Evitar preencher a quota com nomenclatura isolada. Intercalar temas depois da introdução dos pré-requisitos; não produzir centenas de substituições mecânicas da mesma frase.

### Progressão operacional

Cada idioma precisa de um inventário de vocabulário, construções e pré-requisitos, com sequência versionada. Para cada candidato, registrar o foco novo, os conceitos já introduzidos e os desconhecidos incidentais. Tentar manter **uma novidade principal**, reutilizando o restante.

Se a frase exigir outra novidade importante, simplificar, mover para depois ou criar preparação. Fórmulas como pedidos podem ser apresentadas inicialmente como blocos funcionais; explicar depois sua composição sem fingir que o aluno já domina toda a gramática interna.

“Introduzido no currículo” não significa “dominado pelo aluno”. Sem histórico individual e análise linguística suficiente, chamar a proposta de progressão **inspirada em i+1**, não de i+1 estrito. Exportar em ordem de pré-requisitos não garante que todo modo de estudo preserve essa ordem; o primeiro contato deve seguir a sequência, enquanto revisões seguem o Anki.

## 5. Adaptação para todas as línguas

O enum atual possui 23 códigos: `pt`, `es`, `en`, `fr`, `de`, `el`, `it`, `pl`, `tr`, `ro`, `ru`, `nl`, `da`, `nb`, `sv`, `fi`, `hu`, `cs`, `hr`, `la`, `ja`, `zh`, `ko`. Compartilhar intenção e critérios; adaptar frases e currículos, sem traduzir em massa uma única estrutura inglesa.

- **Inglês como alvo:** perguntas em inglês não servem ao mesmo formato de tradução produtiva. Proposta pendente: origem `pt-BR` para esse deck. Não criar inglês→inglês silenciosamente; reformulação monolíngue seria outro produto.
- **Latim:** manter política própria de variedade, época, pronúncia e fontes. A matriz moderna é referência para adaptação, não autorização para inventar terminologia empresarial antiga ou neolatina. As quotas só se fecham após essa curadoria.
- **Coreano:** NFC; identidade e validação por morfemas; partículas, terminações, níveis de fala e relação entre interlocutores explícitos. Não usar sufixos ou espaços como prova de correção. Hangul na resposta; romanização desligada por padrão.
- **Japonês:** contexto de polidez e omissão de argumentos; leituras revisadas por token, com furigana opcional no verso. Não aplicar uma leitura única indiscriminadamente à frase.
- **Mandarim:** definir escrita e variedade; pinyin alinhado à frase, com tons e tratamento de alterações de pronúncia revisados. Pinyin é apoio no verso, não resposta disponível na frente.
- **Demais idiomas:** selecionar os focos relevantes de gênero, concordância, caso, aspecto, posição verbal, artigos, preposições, tratamento e pronúncia. Nem todas essas categorias existem ou se comportam igualmente em todas as línguas.

Escolher uma variedade principal por deck e identificar alternativas. A construção inglesa não obriga a língua-alvo a usar o mesmo tempo ou a explicitar os mesmos pronomes. Fonética e informações de pronúncia precisam de base revisada; não gerar IPA sem verificação.

## 6. Exemplos que definem o comportamento

Os exemplos são demonstrativos e ainda não representam revisão linguística nativa ou aprovação de produção.

**Alemão · restaurante.** Situação: “At a café.” Pergunta: “I'd like a coffee, please.” Foco: “Polite request · Konjunktiv II of haben.” Dica estrutural recolhida: “Conjugated verb second; drink as the direct object.” Resposta: **Ich hätte gern einen Kaffee, bitte.** Variante recolhida: **Ich hätte gerne einen Kaffee, bitte.** Nota de autoria, fora do cartão: `gern/gerne` são variantes aqui; o objeto aparece no acusativo.

**Espanhol · corpo.** Situação: “Tell a friend how you feel.” Pergunta: “My head hurts.” Foco: “Present tense · doler.” Resposta: **Me duele la cabeza.** Nota de curadoria, fora do cartão: **Tengo dolor de cabeza** comunica a ideia, mas não cumpre o foco `doler`; por isso não aparece entre as alternativas aceitas nesse exercício.

| Idioma / tema | Pergunta em inglês | Foco demonstrativo | Resposta principal |
|---|---|---|---|
| Francês / economia | Prices have increased this year. | Relatar a mudança com passé composé de augmenter. | Les prix ont augmenté cette année. |
| Coreano / cafeteria | One Americano, please. | Pedido educado para receber algo, com contador para copos; sem exigir uma terminação única. | 아메리카노 한 잔 주세요. |
| Japonês / direções | Where is the station? | Pergunta educada sobre localização com です. | 駅はどこですか。 |
| Mandarim / negócios | Can we have the meeting tomorrow? | Pergunta de possibilidade com partícula interrogativa final. | 我们可以明天开会吗？ |

Nos cards finais, as instruções dessa tabela serão apresentadas em inglês. Mencionar uma construção solicitada, como です, não elimina o trabalho de formular o restante; o objetivo desse card deve refletir esse apoio explícito. Para testar recuperação da própria construção, usar outro objetivo e uma instrução que não a entregue.

## 7. Contrato de dados proposto

Novo note type: `Multilang Output v1`. **Uma nota gera um card**, sem reverso automático. Campos vazios opcionais desaparecem do layout.

| Campo | Conteúdo e exibição |
|---|---|
| `OutputID` | Identificador estável, não exibido durante estudo. |
| `SourceLanguage`, `TargetLanguage` | Códigos canônicos de origem e alvo. |
| `Level`, `Topic` | Nível e tema principal, discretos na frente. |
| `Situation` | Contexto suficiente para pessoa, relação e registro. |
| `Prompt` | Frase na língua de origem, em destaque. |
| `RequiredFocus` | Critério obrigatório, visível antes da tentativa. |
| `TargetSentence` | Resposta principal, somente verso. |
| `TargetAudio` | Referência completa de mídia da frase, somente verso. |
| `FocusNote` | Nota de autoria/curadoria; não exibida no cartão. |
| `Image` | Campo preservado, vazio por padrão. |

Opcionais de apresentação: `StructuralHint`, `LexicalHint`, `AcceptedVariants`, `Pronunciation`, `TargetAudioSlow`. `OtherValidExpressions` e `CommonError` podem servir à curadoria, fora da interface de estudo. Remover `MicroVariation` do template proposto. Variantes precisam cumprir o foco e o contexto; começar com poucas variantes úteis, provisoriamente zero a duas, mantendo esse número sujeito ao piloto.

Fora do Anki, guardar `scenario_id`, `objective_id`, sequência, pré-requisitos, identidade lexical, morfologia, registro, locale, referências, licença, versões de currículo/prompt/validadores, revisões, hashes de texto/mídia e proveniência de geração. Não expor rastros técnicos no card.

O namespace da identidade deve incluir família, origem, alvo, cenário, objetivo e versão da **política de identidade**. Correções pequenas e novos arquivos de áudio preservam `OutputID`/GUID; mudança de intenção ou foco cria nova nota. Versão do conteúdo não deve mudar automaticamente o GUID. A fórmula será implementada depois, sem alterar identidades dos decks existentes.

## 8. Áudio, template e organização Anki

O áudio-alvo aparece exclusivamente no verso. Não inserir áudio na frente escondido por CSS ou campo de dica: o manual avisa que áudio em dicas pode tocar mesmo fechado. Guardar a referência de mídia completa no campo correspondente, em vez de montar nomes a partir de outros campos. [Campos e mídia do Anki](https://docs.ankiweb.net/templates/fields.html).

Confirmado: reprodução ao revelar, com botão para repetir; velocidade menor é opcional e exige revisão. No Anki, a preferência de reprodução automática pertence às opções do usuário. No HTML, o botão “Show answer” dispara a síntese da frase; ▶ interrompe a fala anterior e reproduz novamente. Trocar de idioma ou voltar à frente interrompe a fala. O protótipo informa quando não há voz do idioma, sem usar outra língua como fallback. [Opções de áudio do Anki](https://docs.ankiweb.net/deck-options.html#audio); [vozes disponíveis no navegador](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/getVoices).

No Anki desktop, a função nativa de gravar a própria voz permite comparação temporária e descarta a gravação ao avançar. Isso pode ajudar sem desenvolver um gravador próprio; disponibilidade e interface dos outros clientes precisam de verificação específica. Reconhecimento de fala futuro não será tratado como prova de boa pronúncia. [Gravação durante estudo](https://docs.ankiweb.net/studying.html#editing-and-more).

Organização sugerida: `Multilang::Output::German::L1`, `L2`, `L3`, repetida por idioma. Temas e focos viram tags, evitando dezenas de subdecks pequenos. Cada nível precisa conter 1000 cards distintos aprovados; variantes não entram nessa contagem. Não sortear uma frase diferente dentro do mesmo card agendado.

O template final deve funcionar com recursos simples, navegação por teclado, texto legível e modo escuro. O protótipo demonstra a interação; compatibilidade com Anki desktop, AnkiDroid e AnkiMobile exige testes posteriores. Botões de avaliação do mock não agendam revisões.

## 9. Produção futura e aprovação

Pipeline proposto:

1. Planejar intenção, situação, foco e pré-requisitos por idioma.
2. Redigir primeiro uma resposta natural no alvo; construir depois a pergunta inglesa fiel. Revisar ambas conjuntamente.
3. Validar sentido, pragmática, foco, dificuldade, duplicação e ausência de pistas indevidas. A tradução de volta é evidência auxiliar, não aprovação automática.
4. Revisar frase principal, variantes, notas e pronúncia; desacordos ou análises inconclusivas bloqueiam publicação.
5. Sintetizar com Azure quando houver voz adequada à variedade aprovada. Cache vinculado ao texto exato, SSML, voz, locale e configurações; mudança relevante exige nova mídia.
6. Conferir integridade, correspondência textual, pronúncia e duração do áudio. Sucesso da API não significa aprovação pedagógica.
7. Congelar manifesto, contagens, identidades e revisões; depois exportar e verificar importação, reimportação, mídia e apresentação nos clientes previstos.

Gates obrigatórios: fontes/licenças resolvidas; conteúdo aprovado; objetivo inequívoco; pré-requisitos registrados; áudio revisado; nenhuma resposta exposta na frente; mídia íntegra; 1000 cards por nível; GUIDs sem colisões. Rejeições devem ser reparadas ou substituídas antes de completar quotas, sem preencher lacunas com duplicatas. Não usar respostas de provedores como verdade permanente sem persistência e revisão.

## 10. Piloto e melhorias úteis

Começar com **20 cards por idioma**, cobrindo contextos e dificuldades representativos; revisar antes de ampliar para 100 e depois para os lotes de 1000. A meta continua 3000 por idioma, mas o piloto permite corrigir problemas antes de multiplicá-los.

Proposta inicial de uso: 5–10 novos cards por dia, ajustando à carga de revisões. É parâmetro de piloto, não dose cientificamente estabelecida. Observar ambiguidades, dependência de dicas, naturalidade, esforço e capacidade de usar o padrão em outra situação. Não otimizar apenas a porcentagem de Good.

Prática livre pode acontecer fora do Anki, mas foi retirada do template a sugestão de exercício extra. A seleção da nota deve avançar normalmente para o próximo cartão.

Melhorias prioritárias: variantes válidas recolhidas, reprodução automática e comparação com a própria voz. Conversação aberta, compreensão auditiva e interação com outras pessoas continuam necessárias para avaliar progresso além das frases estudadas.

Uma evolução possível é o formato **situação → fala**: apresentar “You are at a café. Order a coffee politely” sem uma frase inglesa completa para traduzir. Isso propõe praticar a formulação a partir da intenção, com maior liberdade. Deve ser um objetivo separado e estável, com critérios próprios e novas notas se adotado; não alternar silenciosamente entre tradução e situação no mesmo card agendado. É uma proposta para um piloto posterior, sem ganho de fluência presumido.

Antes da produção, fechar temas e quotas, origem do deck de inglês, variedades/sotaques, política do latim, quantidade de variantes e idiomas iniciais do piloto. O layout pode evoluir com o uso; o critério central permanece estável: **recuperar uma mensagem natural com o foco solicitado antes de consultar o modelo**.
