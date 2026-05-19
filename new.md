1.  --max-items
    Para rodar em lotes controlados:
    --missing-only --max-items 100
    Isso evita deixar um processo enorme rodando por horas e reduz risco de bloqueio.
2.  Progresso granular
    Mostrar contadores durante a execução:
    processed=42 accepted=38 review=4 missing=786 last_item=level-2-rank-0131
3.  Rate limit simples
    Limitar chamadas por minuto para evitar novo 403:
    --rate-limit-per-minute 30
4.  Backoff em erro temporário
    Se provider retornar 403, 429 ou timeout, esperar e tentar novamente em vez de derrubar o job.
5.  --refresh-snapshots no export
    Para garantir que o .apkg usa os dados mais recentes de IPA/definição/frases:
    python -m multilang.cli export --job-id <JOB_ID> --format apkg --refresh-snapshots
    Mensagem boa para pedir a próxima implementação:
    Implemente a próxima etapa do plano em docs/generation-performance-improvements.md: adicionar --max-items ao comando generate. Ele deve limitar quantos candidatos elegíveis são processados nesta execução, funcionar junto com --missing-only e manter compatibilidade com o comportamento atual. Adicione testes focados.
