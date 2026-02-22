
'use client';

import React, { useEffect } from 'react';
import { QuoteBuilderProvider, useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { QuoteBuilderLayout } from '@/components/quotes/builder/QuoteBuilderLayout';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';
import { useRouter, useParams } from 'next/navigation';

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
        <QuoteBuilderProvider>
            <div className="max-w-[1400px] mx-auto p-6 space-y-6">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft size={20} />
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Editar Cotización</h1>
                        <p className="text-sm text-gray-500">Modifica los detalles de la propuesta.</p>
                    </div>
                </div>

                <EditQuoteLoader />
            </div>
        </QuoteBuilderProvider>
    );
}
