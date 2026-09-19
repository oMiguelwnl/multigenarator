# Qualidade das definições e limites de geração

## Contrato compartilhado de Definition (2026-09-19)

Novas definições genéricas seguem `definition-single-sense-v2`: um sentido
selecionado, uma linha de texto simples, formato `classe: significado`, rótulo
gramatical canônico em inglês e significado no idioma solicitado pelo perfil.
O limite de saída é 500 caracteres. O prompt traz exemplos para substantivos,
verbos, adjetivos e palavras funcionais; não permite HTML nem combinar sentidos.
Os idiomas de cada perfil/modo continuam explícitos, sem renomear conteúdo
existente. Os caminhos especializados de coreano e latim mantêm seus contratos.

A validação compartilhada rejeita classe gramatical incompatível, placeholders,
metadados de flexão usados como significado, marcação ativa, quebras de linha
(incluindo separadores Unicode), pontuação sem conteúdo e circularidade simples
como `verb: to run` para `run`. Essas verificações não certificam significado.

O índice lexical pode declarar `definition_senses`, uma lista de objetos com
`sense_id`, `meaning` e `language`. Quando essa lista existe, somente o significado
associado ao `sense_id` selecionado é usado. Ausência ou conflito nessa associação
exige revisão; a ordem da lista nunca escolhe um sentido. Sem mapeamento, o fluxo
tradicional continua aceitando somente um significado inequívoco da fonte.

### Novas gerações nativas

Antes de chamar o provedor, o runtime busca no índice configurado por
`lexicon_data_dir` o registro correspondente ao lema, classe gramatical, sentido,
fonte, versão e SHA-256 da fonte da identidade persistida. Para esse caminho,
o registro precisa declarar `source_version`, `source_sha256` e o idioma real
da definição (`definition_language` ou `definition_senses[].language`). Os hashes
devem ser os da fonte real que originou a identidade, não hashes inventados nem
o hash de uma nova cópia de texto gerado.

O contexto `definition_evidence` é preenchido pelo runtime e inclui o significado
legível e o hash do registro lexical exato. Evidência fornecida pelo cliente deve
coincidir com a fonte local. Fonte ausente, ambígua ou de outra versão interrompe
a geração antes de gastar chamadas de provedor. A validação desse vínculo depende
da curadoria e integridade do índice local; ela não transforma uma fonte em verdade
linguística por si só.

### Coerência entre Definition e exemplo

O runtime tradicional exige uma avaliação do par exato definição/frase, inclusive
em cartões cuja tradução está no mesmo idioma. O avaliador retorna apenas
`consistent`, `mismatch` ou `uncertain`. Divergência, indisponibilidade ou resposta
inválida gera `definition_mismatch`, permitindo o fluxo existente de reparação/revisão.
Ele recebe o idioma real da definição e não aprova a frase apenas pela presença
da palavra. O cache inclui ambos os textos, idiomas, palavra, modelo e versão do
prompt; resultados inconclusivos não ficam armazenados. Tentativas reais usam
o limitador e a telemetria do job/item.

No caminho nativo, a avaliação também compara definição e frase com o significado
da fonte. Uma resposta inconclusiva ou divergente interrompe o rascunho; as versões
que passam continuam `pending`, sujeitas à revisão independente já existente.
A chamada adicional tem limite de 128 tokens e timeout de 45 segundos. Ela é uma
avaliação automática consultiva, não aprovação humana nem prova de correção.

Campos opcionais ausentes são omitidos na serialização para preservar hashes de
conteúdo histórico. Cartões existentes não são reescritos nem aprovados novamente
automaticamente. Índices antigos continuam legíveis, mas novas gerações nativas
precisam dos metadados de fonte descritos acima.

O fluxo legado de definições separa o rascunho do modelo da decisão de admitir
esse texto no cartão. O pedido inclui significado de origem, idioma desse
significado, lema, classe gramatical, fonte e identificador de sentido quando
disponível. A implementação fica em `services/content/` e é composta por
`runtime.py` com os adapters existentes.

## Evidência, fallback e revisão

Uma única definição da fonte, no idioma solicitado, pode ser reproduzida. Sem
um revisor independente configurado, o serviço usa essa evidência diretamente,
sem pagar por um rascunho que seria descartado. Com revisor configurado, se o
modelo mudar o significado sem aprovação válida, o serviço conserva a
definição da fonte e registra o rascunho rejeitado. Essa comparação é uma política
conservadora de reprodução da fonte: não mede a qualidade semântica geral de um
LLM nem certifica que um dicionário esteja correto.

| Situação | Resultado |
|---|---|
| Sem revisor de reescrita, com uma definição de fonte válida no idioma solicitado | `source_verified`, sem chamada de geração |
| Modelo reproduz a definição da fonte no idioma solicitado | `source_verified` |
| Modelo diverge ou falha, mas existe definição da fonte no idioma solicitado | `source_fallback` |
| Fonte sem idioma declarado, sem significado ou com sentidos não resolvidos | `review_required` |
| Só existe definição em outro idioma | Mantém o idioma real e exige revisão |
| Reescrita aprovada por fonte ou revisão humana independente | `independently_reviewed` |
| Só existe candidato de frequência, sem evidência lexical | Continua sem grounding |
| Evidência excede os limites do pedido de geração | `review_required`, com motivo `source_evidence_invalid` |

`DefinitionRecord` persiste `actual_language`, `quality_decision`,
`fallback_reason`, `evidence_source`, `generated_draft` e `review_reference`
quando aplicáveis. `fallback_used` indica a utilização efetiva de outro valor;
uma saída ausente não é um fallback bem-sucedido. Esses metadados ficam fora dos
campos exibidos ao estudante. Definições explicitamente pendentes de revisão
não são exportadas como conteúdo pronto.

A saída coreana mantém normalização NFC; caracteres de controle inválidos
produzem revisão pendente. Correções editoriais já existentes, como a de
`достичь`, são tratadas como fonte interna identificada, com idioma inglês
explícito. Elas não recebem uma aprovação humana inventada.

`IndependentDefinitionReviewer` é uma dependência de aplicação injetável em
`LexicalGroundingService`. O parecer deve corresponder aos hashes SHA-256 do
pedido e do rascunho exatos, e apontar a referência da decisão. Um parecer de IA
é consultivo. Não há um aprovador humano automático configurado no runtime.
Enquanto essa integração não for fornecida, a evidência da fonte é reutilizada
ou o item fica pendente; a geração não inventa aprovação. A
[qualificação linguística](linguistic-qualification.md) documenta o processo de
obter evidências reais; seus artefatos não são automaticamente convertidos em
aprovações de definição.

## Atualização de índices lexicais existentes

O novo campo `definition_language` descreve o idioma **do texto da definição**,
independentemente da língua do verbete. Valores antigos sem esse campo continuam
legíveis, mas seu idioma não é inferido. Para cada registro, confira o texto e
adicione seu idioma real; mantenha fonte rastreável e o sentido selecionado.

Exemplo de formato, que não constitui uma fonte lexical qualificada:

```json
{
  "house": {
    "term": "house",
    "display_form": "house",
    "lemma": "house",
    "part_of_speech": "noun",
    "sense_id": "building",
    "definitions": ["a building where people live"],
    "definition_language": "en",
    "source": "replace-with-the-actual-source-reference"
  }
}
```

Esse registro só fornece fallback em inglês. Um baralho que pede definições em
português precisa de evidência em português ou da revisão independente da
tradução. Não altere o código de idioma para mascarar o texto estrangeiro.
Quando há vários registros distintos para a mesma palavra, `lookup_candidates`
preserva todos; `lookup` não escolhe o primeiro silenciosamente. A seleção de
sentido precisa ser resolvida antes da admissão.

## Execução dos providers

`DefinitionGenerationService` compartilha cache, repetição limitada de chamadas,
circuit breaker e registro de chamadas com o aplicativo. A chave do cache inclui
o pedido completo, modelo, provider, versão do prompt e schema da resposta.
Mudanças na fonte invalidam o cache. O cache guarda rascunhos; toda admissão passa
novamente pela política de evidência.

Uma entrada inválida no cache é tratada como cache ausente e pode ser substituída
após uma nova geração válida. Uma entrada lexical grande demais permanece
pendente sem interromper a ingestão das demais palavras.

As chamadas LiteLLM de definição usam timeout de 45 segundos, até 1.024 tokens
de saída e desativam repetições internas do SDK. O serviço limita a quantidade
de tentativas entre uma e cinco; erros de cota não são repetidos. O campo de
definição retornado é limitado a 4.096 caracteres. Falhas de transporte podem
recuperar uma definição da fonte sem atribuir a ela a origem do modelo.

No runtime, esse orçamento de uma a cinco tentativas é aplicado à configuração
geral de retries sem alterar o valor usado pelos demais serviços.

## Reparos, tradução e pronúncia

Um reparo e uma regeneração manual recebem um identificador de tentativa novo.
A chave de cache inclui esse identificador, a frase rejeitada e os códigos de
validação. O prompt recebe a frase anterior como dado e os motivos do reparo;
uma chamada normal idêntica continua podendo reutilizar o cache. Isso evita
repetir uma resposta reprovada por causa do cache, mas não garante que o modelo
produza uma frase diferente ou correta. Cada tentativa passa pela validação.

Nas traduções entre idiomas do fluxo genérico, o runtime exige também um parecer
de fidelidade sobre a frase e a tradução exatas. O adapter LiteLLM compara o
significado, incluindo entidades, ações, negação e números, com timeout de 45
segundos e saída limitada. `mismatch`, `uncertain`, resposta inválida e falha de
transporte exigem revisão. O cache é vinculado aos dois textos, idiomas, modelo
e versão do prompt; um parecer inconclusivo não é armazenado. O provider local
sem verificador não aprova automaticamente traduções. Essa avaliação de IA é
consultiva e pode errar; não constitui revisão humana. O coreano preserva seu
fluxo separado de avaliação vinculado à identidade e revisão final.

A avaliação de tradução usa o mesmo limite de chamadas da execução, inclusive
nas repetições após falha. Resultados vindos do cache não consomem esse limite.
As chamadas registram o job, o item e os tokens informados pelo provider; esses
metadados de transporte ficam fora do parecer semântico aceito do modelo.

Essa verificação de tradução é aplicada ao validar ou regenerar texto. Cartões
aceitos anteriormente não são reavaliados em massa; precisam passar novamente
por revisão ou regeneração para receber essa verificação.

IPA ausente permanece ausente: a grafia da palavra não preenche esse campo.
Transcrições propostas por LLM preservam incertezas e proveniência, mas ficam
pendentes de verificação. IPA de fonte ou biblioteca passa por validação
estrutural; isso não demonstra, por si só, correção linguística. A exportação
recusa IPA inválido ou explicitamente não verificado, inclusive registros
antigos identificados como saída do gerador de pronúncia do provider. Leituras
de japonês, mandarim e coreano mantêm seus contratos próprios.

## Integridade do áudio e dos campos exportados

O campo Word usa a forma apresentada ao estudante; o lema continua sendo parte
da identidade lexical. O áudio da palavra precisa corresponder a essa forma,
e o áudio da frase precisa corresponder ao ExampleSentence atual. A comparação
confere o texto exibido, sua normalização de síntese e os hashes de texto e SSML.
Apóstrofos tipográficos e normalização NFC são tratados de forma consistente.
Depois de alterar uma frase, seu áudio antigo não pode acompanhar a exportação.

Síntese, reutilização e exportação verificam o arquivo MP3 com `miniaudio`, usando
decodificação real e limitada a 16 MiB e 300 segundos. Arquivos vazios, inválidos,
com tamanho ou hash divergente deixam de ser tratados como mídia pronta. O
decoder recebe bytes locais e não resolve URLs. Essa validação comprova a
integridade técnica do arquivo; não ouve nem certifica a pronúncia sintetizada.

## Contexto do fluxo nativo

O `ContentRequest` completo permanece disponível para autorização, matching e
validação estrita de i+1. A projeção `ProviderContentContext` leva ao modelo os
dados legíveis da tarefa; identificadores administrativos e os conjuntos de
conceitos conhecidos permanecem locais. Contexto privado exige a autorização
já prevista pelo contrato.

O orçamento local admite até 10.000 identificadores, com limite separado de
750.000 bytes serializados. As mensagens efetivamente enviadas ao provider têm
limite de 16.000 bytes UTF-8. A validação não trunca o conjunto conhecido: um
conceito desconhecido adicional continua reprovando o modo estrito.

## Verificação reproduzível

Os testes offline em `tests/services/test_definition_evidence.py` exercitam
significado incorreto, idioma incorreto, ambiguidade, falha de provider,
proveniência, cache, cota e revisão vinculada ao conteúdo. Os testes em
`test_native_content_audio.py` incluem conjuntos de 3.000 e 10.000 conceitos.
São verificações dos contratos de software com fontes sintéticas, sem chamadas
pagas. Não substituem uma avaliação humana de definições, tradução e pronúncia.

A organização dos módulos e a composição transacional estão descritas em
[Arquitetura](architecture.md).
