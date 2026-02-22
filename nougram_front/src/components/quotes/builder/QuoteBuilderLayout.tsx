import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { QuoteFinancialSummary } from './QuoteFinancialSummary';
import { QuoteBuilderForm } from './QuoteBuilderForm';
import { VersionSelector } from './VersionSelector';

export function QuoteBuilderLayout() {
    return (
        <div className="flex flex-col gap-6 h-[calc(100vh-140px)]">
            {/* Toolbar / Header Extensions could go here */}
            <div className="flex justify-end lg:hidden">
                <VersionSelector currentVersion="v1" />
            </div>

            <div className="flex flex-col lg:flex-row gap-6 h-full">
                {/* Left: Inputs & Items (Scrollable) */}
                <div className="flex-1 overflow-y-auto space-y-6 pr-2">
                    <div className="hidden lg:flex justify-end mb-2">
                        <VersionSelector currentVersion="v1" />
                    </div>
                    <QuoteBuilderForm />
                </div>

                {/* Right: Sticky Financial Summary */}
                <div className="w-full lg:w-[420px] flex-shrink-0">
                    <QuoteFinancialSummary />
                </div>
            </div>
        </div>
    );
}
