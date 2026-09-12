# ADR 0002 — Identidade semântica e edições canônicas

Data: 2026-09-12. Estado: contratos implementados; topologia Anki não selecionada.

## Decisão

Separar identidade lexical, identidade do card pedagógico, note GUID e ordinal
do template. Rank e texto gerado não definem identidade. Toda forma importante
aprovada acompanha o pai no mesmo nível e deck ID, sem teto de cards.

Produzir protótipos A (nota por família) e B (notas separadas) e exigir comparação
assinada nos quatro clientes antes da liberação. O Modelo B não promete burying
de siblings. Alteração dinâmica de templates do Modelo A continua sujeita a
prova real de preservação de ordinais e scheduling.

Uma edição Core fixa explicitamente versões de conteúdo e dos dois áudios para
todos os cards. Nova revisão produz nova versão; o histórico do usuário não
personaliza o bundle compartilhado. AudioVersion inclui assinatura completa,
hash de bytes e evidência de review/licença.

## Consequências

Um `.apkg` estruturalmente válido não prova comportamento de reimportação em
Anki Desktop, AnkiDroid ou AnkiMobile. Sem esses resultados, somente protótipos
podem ser exportados. O legado permanece preservado.
