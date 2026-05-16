
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { QuoteTrackingView } from '@/components/quotes/QuoteTrackingView';
import { quoteService } from '@/services/quoteService';
import { Quote } from '@/components/dashboard/QuoteCard';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';

export default function TrackingQuotePage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;
    const [quote, setQuote] = useState<Quote | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadQuote = async () => {
            if (!id) return;
            const data = await quoteService.getByProjectId(id);
            setQuote(data);
            setLoading(false);
        };
        loadQuote();
    }, [id]);

    if (loading) {
        return <div className="flex h-screen items-center justify-center">Cargando Trazabilidad...</div>;
    }

    if (!quote) {
        return <div className="flex h-screen items-center justify-center">Cotización no encontrada</div>;
    }

    return (
        <AdminLayout hideRightPanel>
            <div className="max-w-[960px] mx-auto w-full px-1 sm:px-0 pb-24 md:pb-8">
                <QuoteTrackingView
                    quote={quote}
                    onBack={() => router.back()}
                />
            </div>
        </AdminLayout>
    );
}
