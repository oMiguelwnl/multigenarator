export type Card = { id: string; word: string; definition: string; sentence: string; translation: string; status: 'ready' | 'review' | 'failed'; audio: 'available' | 'missing' | 'outdated' };
export type Draft = { id: string; name: string; language: string; kind: string };

export function saveProductionDraft(drafts: Draft[], draft: Draft): Draft[] {
  const saved = { ...draft, name: draft.name.trim() };
  if (!saved.name) throw new Error('A production name is required.');
  return drafts.some(item => item.id === saved.id)
    ? drafts.map(item => item.id === saved.id ? saved : item)
    : [...drafts, saved];
}

export function editCard(card: Card, patch: Partial<Pick<Card, 'definition' | 'sentence' | 'translation'>>): Card {
  const next = { ...card, ...patch };
  const changed = next.definition !== card.definition || next.sentence !== card.sentence || next.translation !== card.translation;
  return { ...next, status: changed ? 'review' : card.status, audio: next.sentence !== card.sentence ? 'outdated' : card.audio };
}
export function selectCards(cards: Card[], query: string, filter: string): Card[] {
  const term = query.trim().toLocaleLowerCase('pt-BR');
  return cards.filter(card => (filter !== 'pending' || card.status !== 'ready') && `${card.word} ${card.definition}`.toLocaleLowerCase('pt-BR').includes(term));
}
export function canExport(cards: Card[], demo: boolean): boolean {
  return !demo && cards.length > 0 && cards.every(card => card.status === 'ready' && card.audio === 'available');
}
