import type { Draft } from './model';

const storeName = 'productions';
type StoredDraft = Draft & { savedAt: number };

async function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('multilang-studio-drafts', 1);
    request.onupgradeneeded = () => request.result.createObjectStore(storeName, { keyPath: 'id' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function loadDrafts(): Promise<Draft[]> {
  const db = await database();
  try {
    return await new Promise<Draft[]>((resolve, reject) => {
      const request = db.transaction(storeName).objectStore(storeName).getAll();
      request.onsuccess = () => resolve((request.result as StoredDraft[]).sort((a, b) => b.savedAt - a.savedAt));
      request.onerror = () => reject(request.error);
    });
  } finally { db.close(); }
}

export async function persistDraft(draft: Draft): Promise<void> {
  const db = await database();
  try {
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      transaction.oncomplete = () => resolve();
      transaction.onabort = () => reject(transaction.error);
      transaction.objectStore(storeName).put({ ...draft, savedAt: Date.now() });
    });
  } finally { db.close(); }
}
