import { useEffect, useState } from 'react';
import { studioApi } from './studio-api';
import type { Catalog, Production } from './production-api';

export function useProductions() {
  const [items, setItems] = useState<Production[]>([]);
  const [catalog, setCatalog] = useState<Catalog>({});
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const [jobs, capabilities] = await Promise.all([
          studioApi('productions', 'GET', undefined, controller.signal),
          studioApi('productions/catalog', 'GET', undefined, controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setItems(jobs); setCatalog(capabilities); setError('');
        if (jobs.some((item: Production) => ['running', 'queued'].includes(item.status))) {
          timer = setTimeout(load, 2000);
        }
      } catch (e) {
        if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Falha ao consultar as produções.');
      }
    }
    void load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [revision]);
  return { items, catalog, error, refresh: () => setRevision(n => n + 1) };
}
