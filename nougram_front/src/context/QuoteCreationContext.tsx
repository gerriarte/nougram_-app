import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { aiService } from '@/services/aiService';

// --- Types ---
export interface QuoteServiceSelection {
    serviceId: number;
    serviceName: string;
    hours: number;
    price: number;
    quantity: number;
    // Add other relevant fields from your service definition
}

export interface ProjectInfo {
    name: string;
    clientName: string;
    clientEmail?: string;
    clientSector?: string;
    currency: string;
}

export interface QuoteCreationState {
    step: number;
    projectInfo: ProjectInfo;
    services: QuoteServiceSelection[];
    executiveSummary?: string;
    isGeneratingSummary: boolean;
    totalAmount: number;
    margin: number;
}

interface QuoteCreationContextType extends QuoteCreationState {
    setStep: (step: number) => void;
    updateProjectInfo: (info: Partial<ProjectInfo>) => void;
    addService: (service: QuoteServiceSelection) => void;
    removeService: (serviceId: number) => void;
    updateServiceResource: (serviceId: number, hours: number) => void;
    generateSummary: () => Promise<void>;
    reset: () => void;
}

// --- Initial State ---
const INITIAL_STATE: QuoteCreationState = {
    step: 1,
    projectInfo: {
        name: '',
        clientName: '',
        currency: 'USD'
    },
    services: [],
    isGeneratingSummary: false,
    totalAmount: 0,
    margin: 30 // Default margin
};

const QuoteCreationContext = createContext<QuoteCreationContextType | undefined>(undefined);

export function QuoteCreationProvider({ children }: { children: ReactNode }) {
    // Lazy load from localStorage
    const [state, setState] = useState<QuoteCreationState>(() => {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('quote_creation_draft');
            if (saved) {
                try {
                    return JSON.parse(saved);
                } catch (e) {
                    console.error('Failed to parse draft', e);
                }
            }
        }
        return INITIAL_STATE;
    });

    // Auto-save
    useEffect(() => {
        localStorage.setItem('quote_creation_draft', JSON.stringify(state));
    }, [state]);

    // Recalculate totals whenever services change
    useEffect(() => {
        const total = state.services.reduce((acc, curr) => acc + (curr.price * curr.quantity), 0);
        setState(prev => ({ ...prev, totalAmount: total }));
    }, [state.services]);

    const setStep = (step: number) => setState(prev => ({ ...prev, step }));

    const updateProjectInfo = (info: Partial<ProjectInfo>) => {
        setState(prev => ({
            ...prev,
            projectInfo: { ...prev.projectInfo, ...info }
        }));
    };

    const addService = (service: QuoteServiceSelection) => {
        setState(prev => {
            const exists = prev.services.find(s => s.serviceId === service.serviceId);
            if (exists) return prev;
            return { ...prev, services: [...prev.services, service] };
        });
    };

    const removeService = (id: number) => {
        setState(prev => ({
            ...prev,
            services: prev.services.filter(s => s.serviceId !== id)
        }));
    };

    const updateServiceResource = (id: number, hours: number) => {
        setState(prev => ({
            ...prev,
            services: prev.services.map(s =>
                s.serviceId === id ? { ...s, hours } : s
            )
        }));
    };

    const generateSummary = async () => {
        setState(prev => ({ ...prev, isGeneratingSummary: true }));
        try {
            const response = await aiService.generateExecutiveSummary({
                projectName: state.projectInfo.name,
                clientName: state.projectInfo.clientName,
                clientSector: state.projectInfo.clientSector,
                services: state.services.map(s => ({ name: s.serviceName, price: s.price })),
                totalPrice: state.totalAmount,
                currency: state.projectInfo.currency
            });
            setState(prev => ({ ...prev, executiveSummary: response.summary }));
        } catch (error) {
            console.error('Error generating summary', error);
        } finally {
            setState(prev => ({ ...prev, isGeneratingSummary: false }));
        }
    };

    const reset = () => {
        setState(INITIAL_STATE);
        localStorage.removeItem('quote_creation_draft');
    };

    return (
        <QuoteCreationContext.Provider value={{
            ...state,
            setStep,
            updateProjectInfo,
            addService,
            removeService,
            updateServiceResource,
            generateSummary,
            reset
        }}>
            {children}
        </QuoteCreationContext.Provider>
    );
}

export function useQuoteCreation() {
    const context = useContext(QuoteCreationContext);
    if (!context) {
        throw new Error('useQuoteCreation must be used within a QuoteCreationProvider');
    }
    return context;
}
