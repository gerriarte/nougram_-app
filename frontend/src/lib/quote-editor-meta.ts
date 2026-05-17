export type QuoteEditorMeta = {
  projectType?: string;
  projectDescription?: string;
};

const STORAGE_KEY = 'nougram_quote_editor_meta_v1';

function readStorage(): Record<string, QuoteEditorMeta> {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return typeof parsed === 'object' && parsed ? parsed : {};
  } catch {
    return {};
  }
}

function writeStorage(payload: Record<string, QuoteEditorMeta>) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore storage write failures.
  }
}

export function saveQuoteEditorMeta(projectId: string, meta: QuoteEditorMeta) {
  if (!projectId) return;
  const snapshot = readStorage();
  snapshot[projectId] = {
    projectType: (meta.projectType || '').trim(),
    projectDescription: (meta.projectDescription || '').trim(),
  };
  writeStorage(snapshot);
}

export function getQuoteEditorMeta(projectId: string): QuoteEditorMeta {
  if (!projectId) return {};
  const snapshot = readStorage();
  return snapshot[projectId] || {};
}
