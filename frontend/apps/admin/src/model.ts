import type { SourceAttachment } from './source-files';

export type Card = { id: string; word: string; definition: string; sentence: string; translation: string; status: 'ready' | 'review' | 'failed'; audio: 'available' | 'missing' | 'outdated' };
const supportLanguages = ['pt', 'en', 'es'] as const;
export type SupportLanguage = typeof supportLanguages[number];
export const supportLanguageLabels: Record<SupportLanguage, string> = { pt: 'Português', en: 'Inglês', es: 'Espanhol' };
export type Draft = { id: string; name: string; language: string; supportLanguage: SupportLanguage; kind: string; attachment?: SourceAttachment; highlightInput?: 'text' | 'vocabulary' };

// Prototype projection; production progress and history must come from persisted backend jobs/exports.
export type CompletedDeck = {
  id: string;
  name: string;
  language: string;
  supportLanguage: SupportLanguage;
  kind: string;
  completedAt: string;
  cards: Card[];
};

export function progressPercentage(completed: number, total: number): number {
  if (!Number.isFinite(completed) || !Number.isFinite(total) || total <= 0) return 0;
  return Math.min(100, Math.max(0, Math.round((completed / total) * 100)));
}

export function recordCompletedDeck(history: CompletedDeck[], deck: CompletedDeck): CompletedDeck[] {
  return [deck, ...history.filter(item => item.id !== deck.id)];
}

// Mirrors the support-language contract in architecture commit bdb0548.
export function availableSupportLanguages(language: string): readonly SupportLanguage[] {
  return language === 'Coreano' ? ['pt'] : supportLanguages;
}

export function isSupportLanguageAllowed(language: string, supportLanguage: string): supportLanguage is SupportLanguage {
  return availableSupportLanguages(language).some(option => option === supportLanguage);
}

export function changeStudyLanguage(draft: Draft, language: string): Draft {
  const next: Draft = { ...draft, language, supportLanguage: isSupportLanguageAllowed(language, draft.supportLanguage) ? draft.supportLanguage : 'pt' };
  if (language === 'Coreano' && draft.kind === 'Destaques de leitura') next.highlightInput = 'text';
  return next;
}

export function changeMaterial(draft: Draft, kind: string): Draft {
  if (draft.kind === kind) return draft;
  return { ...draft, kind, attachment: undefined, highlightInput: kind === 'Destaques de leitura' ? 'text' : undefined };
}

export function saveProductionDraft(drafts: Draft[], draft: Draft): Draft[] {
  const saved = { ...draft, name: draft.name.trim() };
  if (!saved.name) throw new Error('A production name is required.');
  if (!isSupportLanguageAllowed(saved.language, saved.supportLanguage)) throw new Error('Unsupported support language for this deck.');
  if (saved.kind === 'Destaques de leitura' && saved.language === 'Coreano' && saved.highlightInput === 'vocabulary') throw new Error('Korean highlights require text mode.');
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
