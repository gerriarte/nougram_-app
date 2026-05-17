'use client';

import React from 'react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const STEPS = [
    { id: 1, label: 'Información general',  section: 'quote-step-project-info' },
    { id: 2, label: 'Servicios y alcance',  section: 'quote-step-estimation' },
    { id: 3, label: 'Validación final',     section: 'quote-final-proposal-summary' },
];

export function QuoteStepPills() {
    const { state } = useQuoteBuilder();

    const hasProjectName = typeof state.projectName === 'string' && state.projectName.trim().length > 0;
    const hasClient = Boolean(
        state.clientId ||
        (typeof state.clientCompany === 'string' && state.clientCompany.trim().length > 0) ||
        (typeof state.clientName  === 'string' && state.clientName.trim().length  > 0)
    );
    const hasItems = state.items.length > 0 || state.expenses.length > 0;

    const step1Done = hasProjectName && hasClient;
    const step2Done = hasItems;
    const currentStepId = !step1Done ? 1 : !step2Done ? 2 : 3;

    const isDone = (id: number) => (id === 1 && step1Done) || (id === 2 && step2Done);

    const scrollTo = (section: string) => {
        document.getElementById(section)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    return (
        <div className="hidden sm:flex items-center gap-1.5 shrink-0">
            {STEPS.map((step, i) => {
                const done = isDone(step.id);
                const current = step.id === currentStepId;
                return (
                    <React.Fragment key={step.id}>
                        <button
                            type="button"
                            onClick={() => scrollTo(step.section)}
                            className={cn(
                                'flex items-center gap-2 rounded-full border px-3 py-[5px] text-[12.5px] font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/25',
                                done    ? 'border-transparent bg-success-soft text-success'
                                : current ? 'border-primary/20 bg-primary-soft text-primary'
                                          : 'border-transparent bg-transparent text-gray-400'
                            )}
                        >
                            <div className={cn(
                                'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10.5px] font-bold',
                                done    ? 'bg-success text-white'
                                : current ? 'bg-primary text-white'
                                          : 'bg-gray-200 text-gray-400'
                            )}>
                                {done ? <Check size={11} strokeWidth={3} /> : step.id}
                            </div>
                            {step.label}
                        </button>
                        {i < STEPS.length - 1 && (
                            <div className="h-px w-3 bg-gray-200 shrink-0" />
                        )}
                    </React.Fragment>
                );
            })}
        </div>
    );
}
