'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Check } from 'lucide-react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { VersionSelector } from './VersionSelector';
import { cn } from '@/lib/utils';

type QuoteBuilderSubheaderProps = {
    quoteId?: string;
};

const BUILDER_STEPS = [
    { id: 1, label: 'Información general', section: 'quote-step-project-info' },
    { id: 2, label: 'Tipo de cotización', section: 'quote-step-estimation' },
    { id: 3, label: 'Diseño de propuesta', section: 'quote-final-proposal-summary' },
];

export function QuoteBuilderSubheader({ quoteId }: QuoteBuilderSubheaderProps) {
    const router = useRouter();
    const { state } = useQuoteBuilder();

    const hasProjectName = typeof state.projectName === 'string' && state.projectName.trim().length > 0;
    const hasClient = Boolean(
        state.clientId ||
        (typeof state.clientCompany === 'string' && state.clientCompany.trim().length > 0) ||
        (typeof state.clientName === 'string' && state.clientName.trim().length > 0)
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
        <div className="rounded-xl border border-gray-200 bg-white/80 px-3 py-2.5 shadow-sm">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div className="flex flex-wrap items-center gap-1.5">
                    {BUILDER_STEPS.map((step, i) => {
                        const done = isDone(step.id);
                        const current = step.id === currentStepId;
                        return (
                            <React.Fragment key={step.id}>
                                <button
                                    type="button"
                                    onClick={() => scrollTo(step.section)}
                                    className={cn(
                                        'flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11.5px] font-semibold transition-colors',
                                        done
                                            ? 'border-transparent bg-success-soft text-success'
                                            : current
                                            ? 'border-primary/20 bg-primary-soft text-primary'
                                            : 'border-gray-200 bg-white text-gray-500 hover:bg-gray-50'
                                    )}
                                >
                                    <span
                                        className={cn(
                                            'flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full text-[9.5px] font-bold',
                                            done
                                                ? 'bg-success text-white'
                                                : current
                                                ? 'bg-primary text-white'
                                                : 'bg-gray-200 text-gray-500'
                                        )}
                                    >
                                        {done ? <Check size={10} strokeWidth={3} /> : step.id}
                                    </span>
                                    {step.label}
                                </button>
                                {i < BUILDER_STEPS.length - 1 && <span className="text-gray-300">/</span>}
                            </React.Fragment>
                        );
                    })}

                    <span className="text-gray-300">/</span>
                    <button
                        type="button"
                        disabled={!quoteId}
                        onClick={() => quoteId && router.push(`/dashboard/quotes/${quoteId}/proposal`)}
                        className={cn(
                            'rounded-full border px-2.5 py-1 text-[11.5px] font-semibold',
                            quoteId
                                ? 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                : 'cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400'
                        )}
                    >
                        4. Preview
                    </button>
                    <span className="text-gray-300">/</span>
                    <button
                        type="button"
                        disabled={!quoteId}
                        onClick={() => quoteId && router.push(`/dashboard/quotes/${quoteId}/send`)}
                        className={cn(
                            'rounded-full border px-2.5 py-1 text-[11.5px] font-semibold',
                            quoteId
                                ? 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                : 'cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400'
                        )}
                    >
                        5. Envío
                    </button>
                </div>

                <VersionSelector currentVersion="v1" />
            </div>
        </div>
    );
}
