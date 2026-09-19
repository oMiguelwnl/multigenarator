# Conclusão do piloto linguístico e expansão por idioma

O usuário aprovou executar a sequência: resolver pendências e conflitos, completar evidências de importância, gerar dez cards completos, exportar/validar APKG e repetir o processo nos demais idiomas. A implementação evolui os serviços nativos existentes; não usa GSDD operacional, não altera campos Anki e não faz deploy.

## Estado e decisões

A campanha PT tem 139 acordos individuais, cinco pendências, 126 mapeamentos lexicais aproveitáveis e dois mapeamentos de `beber` separados por conflito de glosa. A revisão dirigida precisa reabrir acordos e cruzar itens sem alterar os contratos de acompanhamento v1. Um plano novo vincula estado efetivo, hashes dos resultados de origem, motivo, seleção e fontes adicionais. Sua consolidação revalida cobertura, fontes, contexto, ancestralidade e atualidade.

Correções de corpus serão projeções identificadas como derivadas de máquina: conservar observação original, texto, offsets e fonte, registrar substituições/exclusões e recalcular os grupos. A análise derivada nunca será apresentada como uma nova saída do modelo original. O alias documental `newdoc_id` de CoNLL-U precisa ser reconhecido em novas leituras, com testes e dados antigos preservados.

A rubrica integral exige dados de aprendizagem e currículo que não estão preparados. Não produzir 66 notas fictícias. Executar também uma política exploratória limitada aos critérios sustentados, avaliá-la contra rótulos novos de um corpus separado e manter explícitas as dimensões indisponíveis. Contagens e frequência vêm exclusivamente de ocorrências reais; exemplos didáticos gerados não são corpus.

## Cards e áudio

O piloto consome mapeamentos sem conflitos e IPA de candidatos verificados, por variante. Conteúdo gerado e julgamento separado devem estar vinculados ao pedido, às fontes e ao inventário. Texto e mídia permanecem de origem máquina e com revisão nativa pendente. Não criar recibos humanos nem habilitar capacidades do perfil.

Reutilizar `ContentVersion`, `ContentPresentation`, `AudioVersion`, `SemanticCard`, verificações de mídia e `export_semantic_anki(model="B", prototype=True)`. O lote de dez pertence a uma edição de piloto e inventário de expansão; sua ordem não é um ranking Core. Preservar nove campos PT e os schemas existentes dos demais idiomas, com `Image` vazio. O export contém aviso de protótipo e manifesto rastreável.

Azure é a opção de áudio configurada e preferida. Preparar texto, assinaturas e previsão limitada de consumo antes da execução. Nenhuma chamada paga sem teto explicitamente disponível; mídia ausente nunca pode ser substituída por silêncio ou bytes de testes. Anki deve ser verificado por integridade do pacote, campos, GUIDs, mídia e retomada; uma inspeção estrutural não equivale à matriz de aceitação de clientes de produção.

## Expansão

Reutilizar a mesma preparação e execução em lotes pequenos para os 22 idiomas modernos do catálogo, com Latim no caminho próprio. Cada idioma conserva perfil, variante, fontes, limites de direitos, análise e lacunas. Fonte ou pronúncia ausente é um bloqueio explícito daquele item, sem inventar conteúdo ou declarar o idioma qualificado.

## Segurança e isolamento

Somente a branch `feature/roadmap-4-0-native-architecture`. O estado inicial e hashes de 312 arquivos previamente alterados estão em `.multilang/verification/ai-completion/before.json`. Trabalhar somente em caminhos próprios; testar snapshot de HEAD mais alterações desta entrega. Não incorporar código concorrente, limpar dados de outros trabalhos, expor segredos ou publicar arquivos. Históricos de revisão e artefatos reais permanecem imutáveis, com novas saídas para cada alteração.
