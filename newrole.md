Esse é documento mostra todos os erros e impressisoes na geração de cards. Quero que voce mude tudo o que for descrito abaixo, e utilize em todos os casos.

## Erros Relacionados ao IPA

- Erro: Em todas os cards, o IPA sempre repete a word ao inves de usar a forma como se pronuncia a palavra.
  Exemplo: Word = громко, IPA = [ˈɡromkə] (гро́мко)
  Esse "(гро́мко)" nao é a forma como se pronuncia a palavra "громко" mas ele apenas repete a palavra.
- Caso voce nao saiba determinar a forma como se pronuncia a palavra, use a palavra em si como o IPA.

## Erros Relacionados á defenition

- Esse projeto existe um padronizador de defenitions, no entanto tem cards onde essa padronização nao foi utilizada. Faça com que todas as defenitions sejam padronizadas.
- Faça uma analise completa do deck dbda4eb2-f0ec-402b-864f-48cdcf982b09.apkg para determinar em que casos a padronização nao foi utilizada, irei apontar algumas que vem em mente e quero que voce crie padroes para evitar esses erros.
- Descubra uma forma para com que as defenitions sempre sejam certas.
  1.  Exemplos de padroes de erros - Adição de caso ao inves de definição clara
      - word = дальнего, Definitions = adjective: masculine animate accusative singular. Nesse caso a defenitions deve descrever uma definição clara do significado da palavra, ao invés de descrever o caso da palavra.
      - word = местности, Defenitions = noun: genitive/dative/prepositional singular
      - word = поги́бли, DEFINITION= verb: short plural past indicative perfective of поги́бнуть (pogíbnutʹ)

2.  Definitions erradas das palavras:
    - word: дости́чь, Defenitions: verb: to amount to, to come to. O Significado é achieve e nao o que esta no card
3.  Definitions da palavra que diz que a word é inflection ao inves de dizer o significado da palavra.
    - word: заболевания, Defenitions: noun: inflection of заболева́ние (zabolevánije).

## Erros Relacionados á Translation

- Tem cards onde o Translation nao corresponde ao Example Sentence. Faça com que em TODOS os decks ele sejam corretos.

## Mudancas da configuração do cards

- Quero que voce remova o campo "Front of Card" pois ele apenas repete o "Word". Com essa remoção voce vai ter que mudar o css dos cards para nao quebrar o layout.

- Tem decks onde a imagem do sentence_audio esta abaixo do Example Sentence ao inves de estar ao lado, isso é diferente nos tamanhos de tela. Em menores ela fica ao lado, mas em telas maiores ela fica abaixo. Faça com que ele sempre esteja ao lado, independente do tamanho da tela.

## Erros de audio

- Em alguns cards, o word_audio esta diferente do word. Faça com que sempre o audio do word_audio seja igual ao word.
