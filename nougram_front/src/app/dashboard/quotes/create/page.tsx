
'use client';

import React from 'react';
import { QuoteBuilderProvider } from '@/context/QuoteBuilderContext';
import { QuoteBuilderLayout } from '@/components/quotes/builder/QuoteBuilderLayout';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function CreateQuotePage() {
    const router = useRouter();

    return (
        <QuoteBuilderProvider>
            <div className="max-w-[1400px] mx-auto p-6 space-y-6">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft size={20} />
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Nueva Cotización</h1>
                        <p className="text-sm text-gray-500">Crea una propuesta rentable en minutos.</p>
                    </div>
                </div>

                <QuoteBuilderLayout />
            </div>
        </QuoteBuilderProvider>
    );
}
