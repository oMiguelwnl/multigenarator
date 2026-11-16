import { useEffect, useId, useRef, useState } from 'react';
import { acceptedSourceFiles, readSourceFile } from './source-files';
import type { SourceAttachment, SourceKind } from './source-files';

type Props = {
  kind: SourceKind;
  attachment?: SourceAttachment;
  disabled: boolean;
  onChange: (attachment: SourceAttachment | undefined) => void;
  onBusyChange: (busy: boolean) => void;
};

export function SourceFileInput({ kind, attachment, disabled, onChange, onBusyChange }: Props) {
  const id = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const version = useRef(0);
  useEffect(() => () => { version.current++; onBusyChange(false); }, [onBusyChange]);

  async function selectFile(file: File) {
    const request = ++version.current;
    setError(''); setBusy(true); onBusyChange(true);
    try {
      const selected = await readSourceFile(file, kind);
      if (request === version.current) onChange(selected);
    } catch (reason) {
      if (request === version.current) setError(reason instanceof Error ? reason.message : 'Não foi possível ler o arquivo. Tente novamente.');
    } finally {
      if (request === version.current) { setBusy(false); onBusyChange(false); }
    }
  }

  return <div className="source-upload" aria-busy={busy}>
    <label htmlFor={id}>{attachment ? 'Substituir arquivo' : kind === 'word-list' ? 'Arquivo de palavras' : 'Arquivo de destaques'}</label>
    <input id={id} type="file" accept={acceptedSourceFiles(kind)} disabled={disabled || busy} aria-describedby={`${id}-help${error ? ` ${id}-error` : ''}`} aria-invalid={Boolean(error)} onChange={event => {
      const file = event.currentTarget.files?.[0];
      event.currentTarget.value = '';
      if (file) void selectFile(file);
    }}/>
    <p className="field-note" id={`${id}-help`}>{kind === 'word-list'
      ? 'TXT em UTF-8, de preferência com uma palavra ou expressão por linha. Até 5 MB.'
      : 'Exportação do Kindle em TXT, HTML ou HTM. Até 5 MB. No TXT, separe os destaques por uma linha com ==========.'}</p>
    <p className="field-note">O arquivo fica apenas nesta sessão do navegador. Recarregar a página remove os anexos; nenhum arquivo é enviado ao servidor neste protótipo.</p>
    <p className="field-note" role="status">{busy ? 'Lendo arquivo…' : attachment ? 'Arquivo anexado ao rascunho.' : 'Nenhum arquivo anexado.'}</p>
    {error && <p className="file-error" role="alert" id={`${id}-error`}>{error}{attachment && ' O arquivo anterior foi mantido.'}</p>}
    {attachment && <div className="attached-file">
      <div className="attachment-heading"><div><strong>{attachment.file.name}</strong><small>{new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 }).format(attachment.file.size / 1000)} KB · anexado nesta sessão</small></div><button className="text-button" type="button" disabled={disabled || busy} onClick={() => { version.current++; onChange(undefined); setError(''); }}>Remover arquivo</button></div>
      {attachment.preview !== undefined
        ? <details><summary>Conferir início do arquivo</summary><pre className="file-preview">{attachment.preview}</pre>{attachment.previewTruncated && <p className="field-note">Prévia limitada aos primeiros 2.000 caracteres. O arquivo anexado permanece completo.</p>}</details>
        : <p className="field-note">Arquivo HTML anexado. A leitura dos destaques será feita na integração com o sistema.</p>}
      <p className="field-note">Anexo conferido quanto a formato, tamanho e leitura do texto. As palavras e os destaques ainda não foram processados.</p>
    </div>}
  </div>;
}
