import type { Card } from './model';

// Illustrative interface fixtures, not reviewed vocabulary or production assets.
export const demoCards: Card[] = [
  { id: '01', word: 'gather', definition: 'Reunir pessoas ou coisas em um lugar.', sentence: 'We gather in the garden every Sunday.', translation: 'Nós nos reunimos no jardim todos os domingos.', status: 'ready', audio: 'available' },
  { id: '02', word: 'enough', definition: 'Suficiente; na quantidade necessária.', sentence: 'We have enough time.', translation: 'Temos tempo suficiente.', status: 'review', audio: 'missing' },
  { id: '03', word: 'nearby', definition: 'Perto; a uma pequena distância.', sentence: 'There is a park nearby.', translation: 'Há um parque por perto.', status: 'ready', audio: 'available' },
  { id: '04', word: 'notice', definition: 'Perceber algo; notar.', sentence: 'Did you notice the new door?', translation: 'Você notou a porta nova?', status: 'review', audio: 'available' },
  { id: '05', word: 'borrow', definition: 'Pegar algo emprestado.', sentence: 'Can I borrow your pen?', translation: 'Posso pegar sua caneta emprestada?', status: 'ready', audio: 'available' },
  { id: '06', word: 'through', definition: '', sentence: '', translation: '', status: 'failed', audio: 'missing' },
];
