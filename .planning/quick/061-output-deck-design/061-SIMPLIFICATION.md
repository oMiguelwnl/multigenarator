# Revisão do protótipo — frases e áudio

Pedido do usuário: reduzir texto, remover “Optional speaking extension” e “What counts as correct?”, priorizar as frases e incluir áudio automático com botão de repetição. Esclarecimento confirmado: tocar **ao revelar a resposta**.

Alterados o fragmento, o HTML completo e o documento de design. Frases maiores; instruções curtas na frente; alternativas e leituras recolhidas; verso sem parágrafos de explicação. Reprodução com Web Speech do navegador, cancelamento ao trocar de idioma/voltar à frente, idioma de voz compatível e recuperação após indisponibilidade/bloqueio. Não foram gerados arquivos de áudio Azure.

Validação: `node .multilang/verification/output-deck-design/check-preview.cjs` passou no HTML completo exportado em 360/736 pixels, claro/escuro. Seis idiomas conferidos; frente silenciosa, autoplay ao revelar, repetição, cancelamento, voz ausente, vozes carregadas depois e erros de permissão verificados. Nenhum erro JavaScript nem requisição externa de página. Foram retiradas do export três bibliotecas remotas do wrapper que o cartão não utiliza. As capturas mostram frases predominantes e ausência de corte horizontal.

Evidência atual: `.multilang/verification/output-deck-design/simplified/report.json`, com hashes do fragmento e do arquivo completo, e oito screenshots na mesma pasta. Checks estruturais foram executados antes da edição e falharam nas duas seções presentes e na ausência de reprodução; passaram depois.

Limite: testes de despacho de fala usaram vozes simuladas na fronteira da API. O Chromium headless real não possui vozes instaladas e exibiu corretamente a mensagem de indisponibilidade. Isso valida o comportamento da interface e da integração, não som audível nem qualidade de pronúncia. Reprodução real no HTML depende de vozes disponíveis no navegador do usuário. Compatibilidade Anki continua fora desta entrega.

Os arquivos SUMMARY, VERIFICATION e UI-PROOF originais documentam a revisão anterior e seus hashes; esta nota e o relatório `simplified` descrevem a revisão atual.
