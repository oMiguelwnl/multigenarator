export type SourceKind = 'word-list' | 'highlights';
export type SourceAttachment = { file: File; preview?: string; previewTruncated: boolean };
export const MAX_SOURCE_BYTES = 5_000_000;
export const MAX_PREVIEW_CHARACTERS = 2000;

export function sourceKindFor(material: string): SourceKind | undefined {
  if (material === 'Lista personalizada') return 'word-list';
  if (material === 'Destaques de leitura') return 'highlights';
  return undefined;
}

export function acceptedSourceFiles(kind: SourceKind): string {
  return kind === 'word-list' ? '.txt' : '.txt,.html,.htm';
}

// This checks the attachment envelope, not lexical content or Kindle structure.
// The original File remains local; never render HTML or derive a server path from its name.
export async function readSourceFile(file: File, kind: SourceKind): Promise<SourceAttachment> {
  const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!acceptedSourceFiles(kind).split(',').includes(extension)) {
    throw new Error(kind === 'word-list' ? 'Selecione um arquivo .txt com sua lista de palavras.' : 'Selecione uma exportação do Kindle em .txt, .html ou .htm.');
  }
  if (file.size === 0) throw new Error('O arquivo está vazio. Escolha um arquivo com conteúdo.');
  if (file.size > MAX_SOURCE_BYTES) throw new Error('O limite deste protótipo é 5 MB por arquivo. Divida o conteúdo em arquivos menores.');
  let bytes: ArrayBuffer;
  try { bytes = await file.arrayBuffer(); }
  catch { throw new Error('Não foi possível ler o arquivo. Selecione o arquivo novamente.'); }
  let text: string;
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { throw new Error('Não foi possível ler o texto em UTF-8. Salve o arquivo nessa codificação e tente novamente.'); }
  if (!text.trim()) throw new Error('O arquivo está vazio. Escolha um arquivo com conteúdo.');
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(text)) {
    throw new Error('O arquivo contém dados que não são texto. Exporte como texto UTF-8 e tente novamente.');
  }
  return {
    file,
    preview: extension === '.txt' ? text.slice(0, MAX_PREVIEW_CHARACTERS) : undefined,
    previewTruncated: extension === '.txt' && text.length > MAX_PREVIEW_CHARACTERS,
  };
}
