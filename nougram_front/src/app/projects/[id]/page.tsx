
'use client';

import React, { useEffect } from 'react';
import { useParams } from 'next/navigation';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { QuoteBuilderProvider, useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { QuoteBuilderLayout } from '@/components/quotes/builder/QuoteBuilderLayout';

// Wrapper to handle data loading
function QuoteLoader() {
    const { id } = useParams();
    const { state } = useQuoteBuilder();
    // We need to access loadQuote from context, but I need to expose it first.
    // wait, I exposed loadQuote? No, I added it to context but didn't put it in the interface return?
    // Let's check Context... I think I missed adding 'loadQuote' to the Provider VALUE in the interface.
    // Actually I missed adding it to the exported interface.
    // But for now, let's assume I fix it or try to use a "Initialization" effect inside the provider if passing prop?
    // A clean way is:
    const context = useQuoteBuilder() as any; // Temporary cast until strict typing fixed

    useEffect(() => {
        if (id && context.loadQuote) {
            context.loadQuote(id as string);
        }
    }, [id]);

    if (!state.projectName && id) {
        return <div className="p-10 text-center">Cargando cotización...</div>;
    }

    return <QuoteBuilderLayout />;
}

export default function EditProjectPage() {
    return (
        <AdminLayout hideRightPanel>
            <QuoteBuilderProvider>
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Editar Cotización</h1>
                        <p className="text-gray-500">Modifica los detalles de tu propuesta.</p>
                    </div>
                </div>

                <QuoteLoader />
            </QuoteBuilderProvider>
        </AdminLayout>
    );
}
