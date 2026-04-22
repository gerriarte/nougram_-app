'use client';

import { useState, useEffect } from 'react';

const KEY_STORAGE = 'nougram:ai:key';
const PROVIDER_STORAGE = 'nougram:ai:provider';

export type AIProvider = 'openai' | 'anthropic';

export function useAIApiKey() {
    const [provider, setProviderState] = useState<AIProvider>('openai');
    const [apiKey, setApiKeyState] = useState<string>('');
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        const savedKey = localStorage.getItem(KEY_STORAGE) || '';
        const savedProvider = (localStorage.getItem(PROVIDER_STORAGE) as AIProvider) || 'openai';
        setApiKeyState(savedKey);
        setProviderState(savedProvider);
        setLoaded(true);
    }, []);

    const setProvider = (p: AIProvider) => {
        setProviderState(p);
        localStorage.setItem(PROVIDER_STORAGE, p);
    };

    const setApiKey = (key: string) => {
        setApiKeyState(key);
        if (key) {
            localStorage.setItem(KEY_STORAGE, key);
        } else {
            localStorage.removeItem(KEY_STORAGE);
        }
    };

    const clearKey = () => {
        setApiKeyState('');
        localStorage.removeItem(KEY_STORAGE);
    };

    return { provider, apiKey, setProvider, setApiKey, clearKey, loaded };
}
