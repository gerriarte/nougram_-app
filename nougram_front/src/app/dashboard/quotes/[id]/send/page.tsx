
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { QuoteSendView } from '@/components/quotes/QuoteSendView';
import type { QuoteSendPayload } from '@/components/quotes/QuoteSendView';
import { quoteService } from '@/services/quoteService';
import { Quote } from '@/components/dashboard/QuoteCard';

export default function SendQuotePage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;
    const [quote, setQuote] = useState<Quote | null>(null);
    const [clientEmail, setClientEmail] = useState<string>('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadQuote = async () => {
            if (!id) return;
            const [data, email] = await Promise.all([
                quoteService.getByProjectId(id),
                quoteService.getProjectClientEmail(id),
            ]);
            setQuote(data);
            setClientEmail(email);
            setLoading(false);
        };
        loadQuote();
    }, [id]);

    const handleSend = async (data: QuoteSendPayload) => {
        if (!id) return;
        try {
            await quoteService.sendEmail(id, data);
            // Navigate back to dashboard or to tracking view
            router.push('/dashboard');
        } catch (error) {
            console.error("Failed to send quote", error);
            const message = error instanceof Error ? error.message : "Error al enviar la cotización";
            alert(message);
        }
    };

    if (loading) {
        return <div className="flex h-screen items-center justify-center">Cargando...</div>;
    }

    if (!quote) {
        return <div className="flex h-screen items-center justify-center">Cotización no encontrada</div>;
    }

    return (
        <QuoteSendView
            quote={quote}
            initialToEmail={clientEmail}
            onSend={handleSend}
            onCancel={() => router.back()}
        />
    );
}
