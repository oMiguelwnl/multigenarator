# Resultados locais da qualificação linguística

Os totais abaixo são candidatos e propostas locais. Há zero revisões humanas reais autenticadas incorporadas a estes pilotos, zero idiomas qualificados e zero chamadas a provedores de geração, tradução ou áudio nos manifestos. Análises locais de morfologia foram executadas anteriormente. Este agregador não executa modelos nem provedores e não autentica revisões externas.

**22/22 pilotos verificados**, 0 aguardando e 0 com falha de integridade. Latim clássico segue um caminho separado deste conjunto de línguas modernas.

Na cópia local do projeto, abra `.multilang/verification/qualification/review-index.html` no navegador. O inventário com hashes está em `.multilang/verification/qualification/aggregate-results.json`. Esses artefatos locais não são publicados junto com a documentação.

[Guia do fluxo de qualificação e revisão](linguistic-qualification.md).

Léxico: revisar lema, classe gramatical e sentido; candidatos flexionados ainda podem precisar de normalização. Formas do dicionário: propostas, sem frequência presumida. Formas medidas: atestação contextual para posterior julgamento e calibração, sem sentido ou importância inventados. Avaliação: casos reservados de teste, separados da calibração; a proposta do analisador não substitui anotação humana independente. Categoria pendente: corrigir a interpretação da fonte antes da aceitação. Os totais dessas categorias não equivalem a cartas.

| Idioma | Situação | Entradas | Candidatos lexicais | Flexionados na fonte | Formas do dicionário | Formas medidas | Casos |
|---|---|---:|---:|---:|---:|---:|---:|
| Português (`pt`) | Preparado; revisão pendente | 100 | 568 | 199 | 894 | 89 | 200 |
| Inglês (`en`) | Preparado; revisão pendente | 100 | 1306 | 55 | 765 | 144 | 200 |
| Turco (`tr`) | Preparado; revisão pendente | 100 | 338 | 149 | 4340 | 0 | 200 |
| Coreano (`ko`) | Preparado; revisão pendente | 100 | 2542 | 211 | 1020 | 0 | 200 |
| Japonês (`ja`) | Preparado; revisão pendente | 100 | 799 | 19 | 1871 | 0 | 200 |
| Chinês (`zh`) | Preparado; revisão pendente | 100 | 314 | 0 | 36 | 0 | 200 |
| Espanhol (`es`) | Preparado; revisão pendente | 100 | 415 | 218 | 1209 | 0 | 200 |
| Francês (`fr`) | Preparado; revisão pendente | 100 | 424 | 176 | 837 | 0 | 200 |
| Alemão (`de`) | Preparado; revisão pendente | 100 | 432 | 217 | 1498 | 0 | 200 |
| Italiano (`it`) | Preparado; revisão pendente | 100 | 454 | 160 | 868 | 0 | 200 |
| Polonês (`pl`) | Preparado; revisão pendente | 100 | 535 | 161 | 724 | 0 | 200 |
| Romeno (`ro`) | Preparado; revisão pendente | 100 | 317 | 140 | 1050 | 0 | 200 |
| Russo (`ru`) | Preparado; revisão pendente | 100 | 418 | 118 | 935 | 0 | 200 |
| Neerlandês (`nl`) | Preparado; revisão pendente | 100 | 464 | 291 | 1026 | 0 | 200 |
| Dinamarquês (`da`) | Preparado; revisão pendente | 100 | 364 | 90 | 602 | 0 | 200 |
| Norueguês (Bokmål) (`nb`) | Preparado; revisão pendente | 100 | 280 | 116 | 311 | 0 | 200 |
| Sueco (`sv`) | Preparado; revisão pendente | 100 | 413 | 130 | 990 | 0 | 200 |
| Finlandês (`fi`) | Preparado; revisão pendente | 100 | 386 | 423 | 6324 | 0 | 200 |
| Húngaro (`hu`) | Preparado; revisão pendente | 100 | 265 | 273 | 4672 | 0 | 200 |
| Tcheco (`cs`) | Preparado; revisão pendente | 100 | 244 | 168 | 735 | 0 | 200 |
| Croata (`hr`) | Preparado; revisão pendente | 100 | 288 | 0 | 0 | 0 | 200 |
| Grego (`el`) | Preparado; revisão pendente | 100 | 276 | 129 | 718 | 0 | 200 |

Totais somente dos pilotos com integridade verificada: 2200 entradas candidatas, 11842 candidatos lexicais, 31425 propostas de formas do dicionário, 233 formas medidas, 4400 casos e 152 pacotes. Esses totais não são cartas aprovadas.

Croata: neste piloto, o wordfreq 3.1.1 recebeu hr e usou a correspondência mais próxima sh (servo-croata). Isso serviu apenas à ordenação inicial de candidatos; não estabelece frequência exclusiva do croata, corpus croata balanceado ou qualificação linguística. O aviso e os hashes do pedido/piloto foram preservados em seed-provenance/hr.json.

Grego: três sementes do wordfreq 3.1.1 precisaram de normalização Unicode NFC antes do preparo. Apenas essas strings foram normalizadas, mantendo a ordem; fontes, frases, offsets e candidatos não foram alterados. As formas originais, as normalizadas e os hashes dos pedidos foram preservados em seed-provenance/el.json. Essa correção de entrada não aprova frequência nem conteúdo linguístico.

## Diagnósticos da análise

Diagnósticos do avaliador versão 3 sobre a amostra reservada de teste. O estado complete significa cobertura da análise, não correção linguística: mesmo uma análise completa pode discordar da referência. Inconclusive preserva bloqueios e incertezas. Os percentuais abaixo só usam métricas declaradas comparáveis com a anotação dessa referência; não são uma nota global nem um ranking entre idiomas. n/c significa não comparável. Em coreano (Kiwi) e japonês (Fugashi/UniDic), lema, POS e traços permanecem null devido às diferenças de inventário e unidade de anotação; resultados brutos incompatíveis não são publicados aqui. Todas estas avaliações mantêm qualification=false. Sentidos, strict-i+1, áudio e aceitação do conteúdo real ainda não são certificados por estes números.

| Idioma | Versão | Frases | complete | inconclusive | Demais | Lema / POS / traços |
|---|---|---:|---:|---:|---:|---|
| Português | 3 | 200 | 54 | 146 | 0 | 97.47% / 96.66% / 95.74% |
| Inglês | 3 | 200 | 197 | 3 | 0 | 96.14% / 95.04% / 94.33% |
| Turco | 3 | 200 | 200 | 0 | 0 | 95.90% / 93.94% / 88.25% |
| Coreano | 3 | 200 | 11 | 189 | 0 | n/c / n/c / n/c |
| Japonês | 3 | 200 | 69 | 131 | 0 | n/c / n/c / n/c |
| Chinês | 3 | 200 | 187 | 13 | 0 | 94.41% / 90.28% / 94.37% |
| Espanhol | 3 | 200 | 120 | 80 | 0 | 96.80% / 98.62% / 98.91% |
| Francês | 3 | 200 | 106 | 94 | 0 | 98.46% / 97.57% / 95.54% |
| Alemão | 3 | 200 | 149 | 51 | 0 | 97.53% / 96.13% / 86.93% |
| Italiano | 3 | 200 | 76 | 124 | 0 | 97.06% / 96.76% / 95.83% |
| Polonês | 3 | 200 | 190 | 10 | 0 | 97.15% / 97.58% / 93.57% |
| Romeno | 3 | 200 | 200 | 0 | 0 | 97.90% / 97.76% / 97.37% |
| Russo | 3 | 200 | 200 | 0 | 0 | 96.67% / 96.13% / 79.04% |
| Neerlandês | 3 | 200 | 196 | 4 | 0 | 94.57% / 96.13% / 94.84% |
| Dinamarquês | 3 | 200 | 198 | 2 | 0 | 96.78% / 97.59% / 96.32% |
| Norueguês (Bokmål) | 3 | 200 | 198 | 2 | 0 | 95.69% / 97.69% / 90.25% |
| Sueco | 3 | 200 | 200 | 0 | 0 | 97.71% / 97.74% / 95.29% |
| Finlandês | 3 | 200 | 199 | 1 | 0 | 94.44% / 96.61% / 91.65% |
| Húngaro | 3 | 200 | 200 | 0 | 0 | 94.12% / 96.06% / 92.31% |
| Tcheco | 3 | 200 | 188 | 12 | 0 | 98.24% / 96.89% / 93.02% |
| Croata | 3 | 200 | 196 | 4 | 0 | 96.63% / 98.04% / 94.07% |
| Grego | 3 | 200 | 178 | 22 | 0 | 95.03% / 96.42% / 91.27% |

Os diagnósticos só aparecem quando o manifesto da avaliação e suas observações conferem com os hashes fixados pelo piloto. Ausência de vínculo verificável fica como indisponível; metadados alterados ficam como falha de integridade. O JSON agregado preserva as razões de comparabilidade e os hashes, sem publicar métricas brutas incompatíveis.

## Corpora efetivamente observados

### pt-wikimedia

Observado; revisão pendente. Cinco artigos, amostra provisória e temática; não representa frequência geral. Dispersão disponível apenas nesses documentos e tokens alinhados.

66/66 unidades analisadas; 2360 tokens lexicais alinhados; 1037 grupos de formas; documentos medidos: 5. Caracteres sem espaço: 12853 alinhados, 792 bloqueados e 0 não analisados/alinhados. Estados: `{"complete": 11, "inconclusive": 55}`.

SHA-256 do arquivo de observações: `cf21bed992fab11f2182560a7ff1f0c2427294bde8c6e241cb0fe164886135c8`. SHA-256 das medições: `e59aabeba3b87506b903346d9bf7c0d4ee2cf1907f030262dc00be440a4b0b3b`.

### en-UD-train-content-hashes-v2

Observado; revisão pendente. Primeiras 200 unidades de treino UD: piloto gramatical, sem avaliação independente nem corpus balanceado. Cinco documentos efetivamente medidos. O texto descritivo antigo sobre documentos desconhecidos não se aplica a este arquivo: os limites presentes são explícitos.

200/12544 unidades analisadas; 3846 tokens lexicais alinhados; 1593 grupos de formas; documentos medidos: 5. Caracteres sem espaço: 20021 alinhados, 0 bloqueados e 810651 não analisados/alinhados. Estados: `{"complete": 200}`.

SHA-256 do arquivo de observações: `c9582dc16da0573414f30f08810b827a470d25f6a6a1c0b37bd13252b51008e4`. SHA-256 das medições: `c9d9e9e79a560dde20aaf0d93bc0afec49520227dbb3f06b1f293621a9d6811a`.

### pt-UD-train-document-boundaries-v3

Observado; revisão pendente. Primeiras 200 unidades de treino UD/Bosque, com limites documentais desconhecidos. Contagens de documentos e dispersão ficam nulas; o identificador da fonte é somente proveniência. Não representa frequência geral.

200/7018 unidades analisadas; 2918 tokens lexicais alinhados; 1637 grupos de formas; documentos medidos: desconhecidos (null). Caracteres sem espaço: 15729 alinhados, 675 bloqueados e 685611 não analisados/alinhados. Estados: `{"complete": 76, "inconclusive": 124}`.

SHA-256 do arquivo de observações: `be5507fdb3081aa99e6a871de6abaa31024db29de7f9f528c765162ef7c17e57`. SHA-256 das medições: `5f414e6510f6d10198697c3899b12528b3ce096cb829ed47ab58131ce29216f8`.

A tabela de pilotos conta formas associadas às entradas selecionadas; os totais de corpus abrangem todos os grupos observados na amostra. O denominador contém apenas tokens lexicais com alinhamento exato nas unidades analisadas. Texto bloqueado, não analisado e tokens não lexicais não viram frequência fictícia. Sentidos continuam não resolvidos. Os dois artefatos UD são de treino; não entram como avaliação independente. As versões corrigidas reutilizaram análises locais, sem novas inferências.

## Pendências e próximos passos

Abra os pacotes pelo índice, preencha decisões explícitas, salve o JSON de rascunho e retome quando necessário. A assinatura e a importação autenticada ficam no fluxo local documentado em linguistic-qualification.md. Depois: resolver correções lexicais, obter evidência e julgamentos das formas, calibrar com dados separados, avaliar e só então habilitar o conteúdo aprovado. Áudio, orçamento de provedores, redistribuição das fontes e aceitação do conteúdo real no Anki continuam pendentes. Nenhum campo do card foi alterado. Não há serviço de deploy.

As propostas de formas do dicionário não possuem atestação medida automaticamente. Quando a coluna de formas medidas é zero, ainda falta corpus contextual adequado para esse idioma. O preparo de 100 entradas e 200 casos é uma meta de amostragem, não uma certificação de qualidade. As grafias e distinções da fonte foram preservadas; homógrafos, maiúsculas e flexões precisam da revisão indicada.

## Verificação e reprodução

SHA-256 dos bytes de cada arquivo listado no manifesto; SHA-256 canônico do manifesto sem pilot_sha256, de cada pacote sem campos computados packet_sha256/item_sha256 e de cada item sem item_sha256. JSON canônico: UTF-8, chaves ordenadas, ensure_ascii=False, separadores compactos e nenhum NaN. Conferência cruzada de idioma, perfil, rubrica, divisão, contagens e manifesto de exportação. Hashes comprovam integridade interna, não assinatura humana nem autenticidade externa. Os hashes dos manifestos encontrados são registrados; não há âncora externa independente neste inventário. Avaliações exigem o SHA dos bytes do manifesto fixado no piloto, o hash canônico evaluation_sha256 e o SHA, número de linhas e estados das observações derivadas.

O agregador só lê os artefatos derivados necessários. Limites: 15.000 leituras, 2 GiB agregados, 128 MiB por arquivo e 32 MiB por pacote JSON; caminhos fora da árvore, links simbólicos, chaves JSON duplicadas e números não finitos são recusados. Não carrega bibliotecas da aplicação, modelos, rede ou serviços. O HTML é estático, com conteúdo escapado e CSP sem scripts. Falhas de integridade saem da soma e geram código de saída 1.

```bash
python3 .multilang/verification/qualification/test_report_results.py
python3 .multilang/verification/qualification/report_results.py
```

As três saídas são substituídas atomicamente por arquivo e são determinísticas para os mesmos artefatos. Reexecute após os pilotos restantes terminarem. O inventário não consulta armazenamento externo de recibos; a contagem zero de revisão autenticada refere-se aos pilotos de preparação aqui incluídos.

SHA-256 canônico do inventário, excluindo seu próprio campo `aggregate_sha256`: `da3d1ad5c76e7b1be9ca388a7e31a87808b9514a7be72f29d5a42cfb83f66d0b`.
