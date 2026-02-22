
import { Quote } from '@/types/dashboard';

const STORAGE_KEY = 'nougram_quotes_db';

/**
 * Simulates a Backend Database for Quotes using LocalStorage.
 * Handles delay to mimic network latency.
 */

// Helper to get DB
function getDB(): Quote[] {
    if (typeof window === 'undefined') return [];

    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];

    try {
        return JSON.parse(stored);
    } catch (e) {
        return [];
    }
}

// Helper to save DB
function saveDB(quotes: Quote[]) {
    if (typeof window === 'undefined') return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(quotes));
}

export const quoteStorage = {

    getAll: async (): Promise<Quote[]> => {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 300));
        return getDB().sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    },

    getById: async (id: string): Promise<Quote | undefined> => {
        await new Promise(resolve => setTimeout(resolve, 200));
        return getDB().find(q => q.id === id);
    },

    create: async (quote: Omit<Quote, 'id' | 'createdAt'>): Promise<Quote> => {
        await new Promise(resolve => setTimeout(resolve, 500));
        const db = getDB();

        const newQuote: Quote = {
            ...quote,
            id: crypto.randomUUID(),
            createdAt: new Date().toISOString(),
            status: 'Draft',
            version: 1,
            viewCount: 0,
            downloadCount: 0
        };

        db.push(newQuote);
        saveDB(db);
        return newQuote;
    },

    update: async (id: string, updates: Partial<Quote>): Promise<Quote> => {
        await new Promise(resolve => setTimeout(resolve, 400));
        let db = getDB();
        const index = db.findIndex(q => q.id === id);

        if (index === -1) throw new Error('Quote not found');

        const updatedQuote = { ...db[index], ...updates };
        db[index] = updatedQuote;

        saveDB(db);
        return updatedQuote;
    },

    delete: async (id: string) => {
        await new Promise(resolve => setTimeout(resolve, 300));
        let db = getDB();
        db = db.filter(q => q.id !== id);
        saveDB(db);
    }
};

// Seed initial data if empty
if (typeof window !== 'undefined') {
    const current = getDB();
    if (current.length === 0) {
        saveDB([
            {
                id: '1', projectName: 'Web App React', clientName: 'Acme Inc', version: 1, amount: 15000000,
                currency: 'COP', marginPercentage: 42, status: 'Viewed', createdAt: '2026-01-20T10:00:00Z',
                viewCount: 5, downloadCount: 2, requiresAttention: true, alertMessage: 'Abierta 5 veces.'
            }
        ]);
    }
}
