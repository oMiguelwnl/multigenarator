---
task: 061-output-deck-design
status: passed
scope: design_only
date: 2026-09-20
---

# Verificação — lógica e protótipo de decks de output

**Resultado: passed, limitado ao design e ao mock HTML.** O documento e o protótipo satisfazem o escopo confirmado: lógica completa de produção oral com perguntas em inglês e uma demonstração visual interativa. Nenhum bloqueador substantivo permaneceu.

## Artefatos verificados

| Artefato | Resultado |
|---|---|
| `docs/output-deck-design.md` | Documento substantivo, 2930 palavras; regras, exemplos, currículo, campos, revisão e limites presentes. |
| `docs/prototypes/output-deck.html` | Seis exemplos, frente/verso, dicas, variantes qualificadas, leitura, rubrica demonstrativa e reinício. |
| `061-SUMMARY.md` e `UI-PROOF.md` | Presentes; escopo e resultados compatíveis com as evidências locais. |
| `.multilang/verification/output-deck-design/report.json` | 32 observações `passed`, `errors: []`, `requests: []`; hash do fragmento igual ao arquivo atual. |
| Screenshots referenciados em `UI-PROOF.md` | 11 arquivos presentes e não vazios; privacidade `local_only`, sem autorização de publicação. |

Hashes SHA-256 observados:

```text
docs/prototypes/output-deck.html
58abff5e3d27b35ab6bb2fbd2e140a302a8f4966871ee729a9c9610cbaf74577

docs/output-deck-design.md
07559304a4524ea561e3682ef234f246c688393baeff4940a120acc0509202e4
```

## Conteúdo e interação

- Recalculo independente da tabela: 20 temas, exatamente **1000/1000/1000** cards previstos. Variantes não aumentam contagens; níveis pedagógicos não são apresentados como CEFR ou ranking.
- Os 23 códigos de idiomas correspondem ao enum atual. Inglês como alvo, latim e variedades permanecem decisões explícitas de produção; não há inglês→inglês implícito.
- As seis respostas principais estão presentes, iguais, no documento e no protótipo. Alternativas fora do foco são qualificadas; japonês não apresenta sua alternativa como aprovação do exercício.
- A rubrica agora considera qualquer dica opcional como tentativa assistida; ler a instrução obrigatória continua parte normal da pergunta. O mock conserva esse estado após fechar a dica e explica Again; não grava avaliação nem controla o Anki.
- Uma nota/um card e identidade estável são definidos. A proposta futura de situação→fala é outro objetivo; não substitui aleatoriamente a pergunta sob o mesmo agendamento.
- O fragmento não contém mídia real, reprodução, síntese, gravação, chamadas de rede ou armazenamento de revisões. O botão de áudio é desabilitado e identifica a ausência de som. O documento proíbe áudio-alvo escondido na frente do template Anki futuro.
- Sintaxe JavaScript conferida. Dados fixos entram no DOM por `textContent`; não há inserção por `innerHTML`, avaliação de entrada, fetch ou armazenamento local. Revisão proporcional orientada pelo skill `code-security`.

## Evidência visual e comandos

O runner existente `node .multilang/verification/output-deck-design/check-preview.cjs` completou a execução final registrada em Chromium 151.0.7922.34. A revisão conferiu o runner, o relatório e a igualdade entre as 32 observações do relatório e do bundle de prova, sem repetir a geração de screenshots.

Cobertura efetiva: **360×800 e 736×900**, ambos em claro/escuro. Em cada combinação, frente e verso e os seis exemplos foram observados; o runner cobre revelação, dicas, avaliação demonstrativa, disclosures, reinício e overflow horizontal. Esta revisão inspecionou visualmente frente mobile clara, verso mobile escuro e japonês mobile escuro; o executor complementou a inspeção dos demais estados descritos no SUMMARY. Não foram observados cortes horizontais, sobreposições ou texto ilegível nessas imagens.

Checks adicionais foram executados apenas com leitura: parsing da matriz e do enum em Python, compilação sintática do script com `node:vm`, comparação SHA-256, existência das 12 referências de artefatos e consistência de exemplos. Os hashes podem ser reconferidos com:

```bash
sha256sum docs/output-deck-design.md docs/prototypes/output-deck.html
```

A primeira execução de navegador foi interrompida; a causa não está confirmada. A conclusão depende da execução final completa, conforme report e SUMMARY. A validação do bundle `UI-PROOF.md` sem erros/avisos foi informada pelo executor; este revisor conferiu diretamente seu conteúdo, referências e correspondência com o relatório.

## Ajustes encerrados e limites

Dois achados de precisão foram corrigidos pelo executor: instrução alemã agora usa **Konjunktiv II of haben**, e o viewport mobile foi alinhado para **360×800**. Documento/protótipo não foram editados durante esta verificação.

Não há aprovação de APKG ou de clientes Anki, áudio real, pronúncia, revisão linguística nativa, scheduler, geração de 3000 cards ou eficácia de fluência. Exemplos e quotas são design, não inventário de produção. A revisão do protótipo foi separada de sua implementação; este verificador também redigiu a versão inicial do documento pedagógico, portanto a checagem de conteúdo não equivale a revisão autoral externa ou especializada.
