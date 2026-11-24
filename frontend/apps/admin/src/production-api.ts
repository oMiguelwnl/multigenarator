import { LANGUAGE_CODES } from './anki-preview.ts';
import type { Draft } from './model';
import { studioApi } from './studio-api.ts';

export const materialLabels = {
  frequency: 'Frequência', 'word-list': 'Lista personalizada', highlights: 'Destaques de leitura',
  foundations: 'Escrita e fundamentos', phonetics: 'Pronúncia e fonética', grammar: 'Gramática', latin: 'Latim clássico',
} as const;
export type Material = keyof typeof materialLabels;
export type Catalog = Record<string, Material[]>;
export type Production = {
  id: string; name: string; language: string; supportLanguage: string; kind: Material;
  status: 'queued' | 'running' | 'completed' | 'failed'; stage: string; message: string;
  updatedAt: string; jobId: string | null; canDownload: boolean;
};
export const statusLabels = { queued: 'Na fila', running: 'Em andamento', completed: 'Concluída', failed: 'Falhou' };
export const languageName = (code: string) => Object.keys(LANGUAGE_CODES).find(label => LANGUAGE_CODES[label] === code) ?? code;
export const materialId = (label: string) => (Object.keys(materialLabels) as Material[]).find(id => materialLabels[id] === label);

export async function startProduction(draft: Draft, id: string): Promise<Production> {
  const kind = materialId(draft.kind);
  if (!kind) throw new Error('Selecione um tipo de material disponível.');
  const file = kind === 'highlights' || kind === 'word-list' ? draft.attachment?.file : undefined;
  return studioApi('productions', 'POST', {
    id, name: draft.name.trim(), language: LANGUAGE_CODES[draft.language], supportLanguage: draft.supportLanguage,
    kind, ...(kind === 'frequency' ? { level: draft.level ?? 1 } : {}),
    ...(kind === 'highlights' ? { highlightInput: draft.highlightInput ?? 'text' } : {}),
    ...(file ? { sourceText: await file.text(), sourceExtension: file.name.split('.').pop()?.toLowerCase() } : {}),
  });
}

export function repairProduction(id: string, attempt: string): Promise<Production> {
  return studioApi(`productions/${id}/repair`, 'POST', { id: attempt });
}
