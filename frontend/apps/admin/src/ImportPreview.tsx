import { useEffect, useState } from 'react';
import type { SourceKind } from './source-files';
import { studioApi } from './studio-api';

type Preview = {
  candidate_count: number;
  highlight_count: number;
  duplicates: number;
  ignored: number;
  items: string[];
  excerpts: string[];
};

type Props = {
  file: File;
  kind: SourceKind;
  language: string;
  mode: 'text' | 'vocabulary';
  onReady?: (ready: boolean) => void;
};

export function ImportPreview({ file, kind, language, mode, onReady }: Props) {
  const [result, setResult] = useState<Preview>();
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setResult(undefined);
    setError('');
    onReady?.(false);
    async function load() {
      if (location.protocol !== 'http:' || location.hostname !== '127.0.0.1') {
        throw new Error('Abra o Estúdio pelo iniciador local para conferir o arquivo.');
      }
      const extension = file.name.split('.').at(-1)?.toLowerCase() ?? '';
      const query = new URLSearchParams({ kind, language, extension, mode });
      const preview: Preview = await studioApi(`sources/preview?${query}`, 'POST', file.slice(), controller.signal);
      if (!controller.signal.aborted) {
        setResult(preview);
        onReady?.(preview.candidate_count > 0);
      }
    }
    void load().catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'Falha ao conferir a importação.');
    });
    return () => { controller.abort(); onReady?.(false); };
  }, [file, kind, language, mode, attempt, onReady]);

  if (error) return <div><p role="alert" className="file-error">{error}</p>
    <button type="button" className="text-button" onClick={() => setAttempt(n => n + 1)}>Conferir novamente</button></div>;
  if (!result) return <p className="field-note" role="status">Conferindo a importação…</p>;
  return <section aria-label="Prévia da importação">
    <p role="status"><strong>{result.candidate_count} {result.candidate_count === 1 ? 'item reconhecido' : 'itens reconhecidos'}</strong></p>
    <p className="field-note">{kind === 'highlights' && `Destaques lidos: ${result.highlight_count}. `}Repetições: {result.duplicates}. Ignorados: {result.ignored}.</p>
    {result.excerpts.length > 0 && <details><summary>Trechos lidos do Kindle</summary><ul>
      {result.excerpts.map((text, index) => <li key={index}>{text}</li>)}
    </ul></details>}
    {result.items.length > 0 && <details open><summary>Palavras e expressões ({result.items.length} de {result.candidate_count})</summary>
      <p className="file-preview">{result.items.join(' · ')}</p></details>}
    {kind === 'highlights' && language === 'ko' && <p className="field-note">Para destaques em coreano, a prévia exibe apenas as contagens.</p>}
  </section>;
}
