import { studioApi } from './studio-api.ts';

export type ReviewField = { name: string; text: string; editable: boolean; imageField: boolean; hasImage: boolean; audio: string[] };
export type ReviewNote = { id: string; title: string; model: string; revision: string; fields: ReviewField[] };
type ApprovalReceipt = { productionId: string; operator: string; approvedAt: string; revision: string; snapshotSha256: string };
export type Approval = { revision: string; state: 'pending' | 'approved' | 'needs_approval'; latest: ApprovalReceipt | null };
export type ResultPage = { total: number; notes: ReviewNote[]; approval: Approval };
export const pageSize = 25;

export function productionResult(id: string) {
  const base = 'productions/' + encodeURIComponent(id);
  const notePath = (note: ReviewNote) => base + '/result/' + encodeURIComponent(note.id);
  const imagePath = (note: ReviewNote, field: string) =>
    notePath(note) + '/image?' + new URLSearchParams({ field, revision: note.revision });
  return {
    page(q: string, offset: number, signal: AbortSignal): Promise<ResultPage> {
      const query = new URLSearchParams({ q, offset: String(offset), limit: String(pageSize) });
      return studioApi(base + '/result?' + query, 'GET', undefined, signal);
    },
    approve(revision: string): Promise<Approval> {
      return studioApi(base + '/approvals', 'POST', { revision });
    },
    edit(note: ReviewNote, fields: Record<string, string>): Promise<ReviewNote> {
      return studioApi(notePath(note), 'PATCH', { revision: note.revision, fields });
    },
    upload(note: ReviewNote, field: string, file: File): Promise<ReviewNote> {
      if (file.size > 5_000_000) throw new Error('Escolha uma imagem PNG de até 5 MB.');
      return studioApi(imagePath(note, field), 'PUT', file.slice(0, file.size, 'image/png'));
    },
    audioUrl: (number: string) => '/studio-api/' + base + '/media/' + encodeURIComponent(number),
    imageUrl: (note: ReviewNote, field: string) => '/studio-api/' + imagePath(note, field),
    exportUrl: '/studio-api/' + base + '/export',
  };
}
