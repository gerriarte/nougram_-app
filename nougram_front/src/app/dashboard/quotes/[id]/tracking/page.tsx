
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { QuoteTrackingView } from '@/components/quotes/QuoteTrackingView';
import { quoteService } from '@/services/quoteService';
import { Quote } from '@/components/dashboard/QuoteCard';

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
        <QuoteTrackingView
            quote={quote}
            onBack={() => router.back()}
        />
    );
}
