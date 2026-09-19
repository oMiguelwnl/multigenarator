# Áudio de listas pessoais e destaques em coreano

Os comandos abaixo funcionam diretamente, sem executar GSD. A geração usa somente a palavra ou frase didática aceita; nomes de arquivos e trechos privados não entram no pedido ao Azure. A síntese cria mídia **pendente de revisão**.

A revisão textual importada precisa continuar vinculada ao conteúdo, identidade morfológica, política e revisões atuais. Flags antigas de aceitação ou um hash de recibo isolado não autorizam a chamada.

Configure a cotação atual da voz exata em `MULTILANG_KOREAN_AZURE_TTS_USD_PER_MILLION_CHARACTERS` e `MULTILANG_KOREAN_AZURE_TTS_PRICING_VOICE_ID`. O custo é estimado conservadoramente pelos bytes UTF-8 do SSML completo e limitado antes da chamada.

O perfil aprovado para frequência não autoriza listas ou destaques. Crie um vínculo separado usando `PersonalVoiceAuthority` (`korean-personal-voice-authority-v1`), com fontes explícitas `word-list` e/ou `kindle-highlights`, voz, região, hashes do arquivo/conteúdo do catálogo e da política:

```sh
multilang korean review bind-audio-profile \
  --authority-file personal-voice-authority.json \
  --catalog-file catalog.json \
  --provider-policy-file policy.json \
  --output-file personal-voice-profile.json
```

`PersonalAudioAuthority` (`korean-personal-audio-authority-v1`) autoriza uma única chamada. Ela vincula job, item público, fonte, campo (`word_audio` ou `sentence_audio`), ator, request-id, versão esperada do ponteiro, perfil pessoal, política, texto falado, recibo de revisão textual, pedido SSML, raiz de mídia, cotação e teto de custo. A primeira revisão usa versão `0`. Os modelos e o serializador canônico estão em `src/multilang/services/korean_personal_audio.py`; `build_korean_tts_input` calcula a identidade exata do pedido.

```sh
multilang korean review regenerate-audio \
  --authority-file generation-authority.json \
  --profile-file personal-voice-profile.json \
  --catalog-file catalog.json \
  --provider-policy-file policy.json
```

O resultado contém revision-id, versão do ponteiro, caminho relativo imutável e hashes de pedido, mídia e integridade. Repetir a mesma autorização concluída retorna seu resultado sem nova síntese. Uma autorização diferente para a mesma request-id é recusada.

Para promover o candidato, importe `AudioReviewEvidence` com estado `ai_acoustic_review_passed` e origem `production`, vinculada aos hashes e caminho do resultado. `PersonalAudioReviewAuthority` também fixa a revisão, versão, autorização de geração e hash canônico da evidência:

```sh
multilang korean review apply-audio-review \
  --authority-file review-authority.json \
  --evidence-file acoustic-evidence.json
```

O importador confere os bytes e a decodificação MP3, texto atual, pedido, perfil, política e versão antes de aprovar. Um simples `review approve` não aprova áudio. Os testes com provedores simulados não constituem revisão acústica de conteúdo real.

Para substituir uma versão aprovada, rejeite-a explicitamente. O comando atualiza ponteiro e ativo juntos e preserva o arquivo e o histórico:

```sh
multilang korean review reject-audio \
  --job-id JOB --item-id ITEM --field word_audio \
  --revision-id REVISION --expected-pointer-version VERSION \
  --actor-id OPERATOR --request-id REJECTION_ID
```

Depois use uma **nova** request-id e a versão devolvida na autorização de geração.

Se houver timeout, interrupção ou persistência incerta, não há repetição automática. Consulte e recupere primeiro a reserva com `generation-lease-status` e `recover-generation-lease`, reconhecendo o resultado incerto. Em seguida, forneça `PersonalAudioRecoveryAuthority` (`korean-personal-audio-recovery-authority-v1`): job/item/campo/revisão, versão atual, hashes da autorização e do pedido original, ator, nova request-id de recuperação e `acknowledge_unknown_outcome: true`.

```sh
multilang korean review recover-audio --authority-file recovery-authority.json
```

A recuperação abandona a tentativa antiga sem apagar seus arquivos ou histórico. Ela permite preparar outra autorização com nova request-id; a request-id abandonada permanece bloqueada. Gramática continua usando seu bundle revisado e imutável.

Este fluxo não migra áudios aprovados externos ou legados que não tenham seu registro de geração e revisão pessoal. Esses ativos são preservados e recusados para substituição automática; não há opção de forçar sua alteração.
