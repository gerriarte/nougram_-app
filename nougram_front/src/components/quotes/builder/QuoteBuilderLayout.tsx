import React from 'react';
import { QuoteFinancialSummary } from './QuoteFinancialSummary';
import { QuoteBuilderForm } from './QuoteBuilderForm';
import { QuoteBuilderActions } from './QuoteBuilderActions';

export function QuoteBuilderLayout() {
    return (
        <div className="flex flex-col gap-6 pb-4 md:pb-0">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
                {/* Columna principal: formulario + acciones solo en desktop (sticky) */}
                <div className="flex min-w-0 flex-1 flex-col gap-6 order-1">
                    <QuoteBuilderForm />
                    <div className="hidden lg:block sticky bottom-4 z-30 w-full">
                        <QuoteBuilderActions variant="desktop" />
                    </div>
                </div>

                {/* Resumen rentabilidad */}
                <div
                    className="w-full shrink-0 order-2 lg:w-[420px] lg:sticky lg:top-24"
                    id="quote-final-proposal-summary"
                >
                    <QuoteFinancialSummary />
                </div>

                {/* Móvil: acciones al final, después del resumen (no fijas — no tapan la card) */}
                <div className="order-3 w-full lg:hidden pb-[max(1rem,env(safe-area-inset-bottom))]">
                    <QuoteBuilderActions variant="mobile" />
                </div>
            </div>
        </div>
    );
}
