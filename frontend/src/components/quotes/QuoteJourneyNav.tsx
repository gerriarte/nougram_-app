'use client';

import React from 'react';
import Link from 'next/link';
import { Check, FileText, Send, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

type QuoteJourneyStage = 'quote' | 'proposal' | 'send';

type QuoteJourneyNavProps = {
    currentStage: QuoteJourneyStage;
    quoteId?: string;
    className?: string;
};

const JOURNEY_STEPS = [
    {
        id: 'quote',
        number: 1,
        label: 'Cotización',
        description: 'Datos, alcance y rentabilidad',
        icon: FileText,
    },
    {
        id: 'proposal',
        number: 2,
        label: 'Propuesta',
        description: 'Narrativa y estructura comercial',
        icon: Sparkles,
    },
    {
        id: 'send',
        number: 3,
        label: 'Envío',
        description: 'Portal cliente y mensaje',
        icon: Send,
    },
] as const;

function hrefForStage(stage: QuoteJourneyStage, quoteId?: string) {
    if (stage === 'quote') {
        return quoteId ? `/dashboard/quotes/${quoteId}/edit` : '/dashboard/quotes/create';
    }
    if (!quoteId) return undefined;
    return stage === 'proposal'
        ? `/dashboard/quotes/${quoteId}/proposal`
        : `/dashboard/quotes/${quoteId}/send`;
}

export function QuoteJourneyNav({ currentStage, quoteId, className }: QuoteJourneyNavProps) {
    const currentIndex = JOURNEY_STEPS.findIndex((step) => step.id === currentStage);

    return (
        <nav
            aria-label="Flujo de cotización"
            className={cn('rounded-2xl border border-gray-200 bg-white/85 p-2 shadow-sm backdrop-blur', className)}
        >
            <div className="grid gap-2 md:grid-cols-3">
                {JOURNEY_STEPS.map((step, index) => {
                    const Icon = step.icon;
                    const active = step.id === currentStage;
                    const complete = currentIndex > index;
                    const href = hrefForStage(step.id, quoteId);
                    const content = (
                        <>
                            <div
                                className={cn(
                                    'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border text-[12px] font-black transition-colors',
                                    complete
                                        ? 'border-transparent bg-success text-white'
                                        : active
                                            ? 'border-primary bg-primary text-white'
                                            : 'border-gray-200 bg-white text-gray-400'
                                )}
                            >
                                {complete ? <Check size={14} strokeWidth={3} /> : <Icon size={15} strokeWidth={2.2} />}
                            </div>
                            <div className="min-w-0">
                                <div
                                    className={cn(
                                        'flex items-center gap-2 text-[13px] font-bold',
                                        active ? 'text-primary' : complete ? 'text-success' : 'text-gray-700'
                                    )}
                                >
                                    <span className="font-mono text-[11px] opacity-70">{String(step.number).padStart(2, '0')}</span>
                                    <span>{step.label}</span>
                                </div>
                                <p className="mt-0.5 truncate text-[11.5px] text-gray-500">{step.description}</p>
                            </div>
                        </>
                    );

                    return href ? (
                        <Link
                            key={step.id}
                            href={href}
                            aria-current={active ? 'step' : undefined}
                            className={cn(
                                'flex items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/25',
                                active
                                    ? 'border-primary/20 bg-primary-soft shadow-sm'
                                    : complete
                                        ? 'border-success/10 bg-success-soft/60 hover:border-success/20'
                                        : 'border-transparent hover:border-gray-200 hover:bg-surface-2'
                            )}
                        >
                            {content}
                        </Link>
                    ) : (
                        <div
                            key={step.id}
                            className="flex cursor-not-allowed items-center gap-3 rounded-xl border border-transparent px-3 py-2.5 text-left opacity-55"
                            aria-disabled="true"
                        >
                            {content}
                        </div>
                    );
                })}
            </div>
        </nav>
    );
}
