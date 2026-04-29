
'use client';

import React from 'react';
import { QuoteBuilderProvider } from '@/context/QuoteBuilderContext';
import { QuoteBuilderLayout } from '@/components/quotes/builder/QuoteBuilderLayout';
import { QuoteBuilderSubheader } from '@/components/quotes/builder/QuoteBuilderSubheader';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { QuoteJourneyNav } from '@/components/quotes/QuoteJourneyNav';

export default function CreateQuotePage() {
    const router = useRouter();

    return (
        <AdminLayout hideRightPanel>
            <QuoteBuilderProvider>
                <div className="max-w-[1400px] mx-auto space-y-2 sm:space-y-3">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 sm:gap-4 min-w-0">
                            <Button variant="ghost" size="icon" className="shrink-0 h-9 w-9 rounded-xl border border-gray-200" onClick={() => router.back()}>
                                <ArrowLeft size={16} />
                            </Button>
                            <div className="min-w-0">
                                <h1 className="text-[22px] font-bold tracking-tight text-gray-900 truncate">Nueva Cotización</h1>
                                <p className="text-[13px] text-gray-500">Crea una propuesta rentable en minutos.</p>
                            </div>
                        </div>
                    </div>

                    <QuoteJourneyNav currentStage="quote" />
                    <QuoteBuilderSubheader />
                    <QuoteBuilderLayout />
                </div>
            </QuoteBuilderProvider>
        </AdminLayout>
    );
}
