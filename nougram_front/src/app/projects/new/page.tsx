
'use client';

import React from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { QuoteBuilderProvider } from '@/context/QuoteBuilderContext';
import { QuoteBuilderLayout } from '@/components/quotes/builder/QuoteBuilderLayout';

export default function NewProjectPage() {
    return (
        <AdminLayout hideRightPanel>
            <QuoteBuilderProvider>
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Nueva Cotización</h1>
                        <p className="text-gray-500">Calculadora Viva: Los márgenes se actualizan en tiempo real.</p>
                    </div>
                </div>

                <QuoteBuilderLayout />
            </QuoteBuilderProvider>
        </AdminLayout>
    );
}
