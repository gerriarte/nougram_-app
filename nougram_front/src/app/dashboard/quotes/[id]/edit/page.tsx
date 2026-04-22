
'use client';

import React, { useEffect } from 'react';
import { QuoteBuilderProvider, useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { QuoteBuilderLayout } from '@/components/quotes/builder/QuoteBuilderLayout';
import { QuoteStepPills } from '@/components/quotes/builder/QuoteStepPills';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';
import { useRouter, useParams } from 'next/navigation';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';

// Inner component to access context
function EditQuoteLoader() {
    const { loadQuote } = useQuoteBuilder();
    const params = useParams();
    const id = params.id as string;

    useEffect(() => {
        if (id) {
            loadQuote(id);
        }
    }, [id, loadQuote]);

    return <QuoteBuilderLayout />;
}

export default function EditQuotePage() {
    const router = useRouter();

    return (
        <AdminLayout hideRightPanel>
            <QuoteBuilderProvider>
                <div className="max-w-[1400px] mx-auto space-y-4 sm:space-y-6">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 sm:gap-4 min-w-0">
                            <Button variant="ghost" size="icon" className="shrink-0 h-9 w-9 rounded-xl border border-gray-200" onClick={() => router.back()}>
                                <ArrowLeft size={16} />
                            </Button>
                            <div className="min-w-0">
                                <h1 className="text-[22px] font-bold tracking-tight text-gray-900 truncate">Editar Cotización</h1>
                                <p className="text-[13px] text-gray-500">Modifica los detalles de la propuesta.</p>
                            </div>
                        </div>
                        <QuoteStepPills />
                    </div>

                    <EditQuoteLoader />
                </div>
            </QuoteBuilderProvider>
        </AdminLayout>
    );
}
