import React from 'react';
import { QuoteFinancialSummary } from './QuoteFinancialSummary';
import { QuoteBuilderForm } from './QuoteBuilderForm';
import { QuoteBuilderActions } from './QuoteBuilderActions';
import { VersionSelector } from './VersionSelector';

export function QuoteBuilderLayout() {
    return (
        <div className="flex flex-col gap-6 pb-4 md:pb-0">
            <div className="flex justify-end lg:hidden">
                <VersionSelector currentVersion="v1" />
            </div>

            <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
                {/* Columna principal: formulario + acciones solo en desktop (sticky) */}
                <div className="flex min-w-0 flex-1 flex-col gap-6 order-1">
                    <div className="hidden lg:flex justify-end mb-2">
                        <VersionSelector currentVersion="v1" />
                    </div>
                    <QuoteBuilderForm />
                    <div className="hidden lg:block sticky bottom-4 z-30 w-full max-w-5xl mx-auto lg:mx-0">
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
