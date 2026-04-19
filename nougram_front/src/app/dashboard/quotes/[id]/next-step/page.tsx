'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, FileText, Send, CheckCircle2, Loader2 } from 'lucide-react';
import { quoteService } from '@/services/quoteService';
import { Quote } from '@/components/dashboard/QuoteCard';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';

export default function QuoteNextStepPage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;
    const [quote, setQuote] = useState<Quote | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) { setLoading(false); return; }
        quoteService.getByProjectId(id)
            .then(data => setQuote(data))
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background">
                <Loader2 size={20} className="animate-spin text-gray-400" />
            </div>
        );
    }

    if (!quote) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background">
                <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm text-center max-w-sm w-full">
                    <p className="text-[14px] text-gray-600 mb-4">Cotización no encontrada.</p>
                    <Button variant="secondary" onClick={() => router.push('/dashboard')}>Volver al dashboard</Button>
                </div>
            </div>
        );
    }

    return (
        <AdminLayout hideRightPanel>
            <div className="mx-auto max-w-lg px-4 py-10">
                {/* Success header */}
                <div className="mb-8 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success-soft text-success">
                        <CheckCircle2 size={32} strokeWidth={2} />
                    </div>
                    <h1 className="text-[24px] font-semibold tracking-tight text-gray-900">Cotización guardada</h1>
                    <p className="mt-1.5 text-[13.5px] text-gray-500">
                        {quote.project} · V{quote.version}
                    </p>
                </div>

                {/* Status pills */}
                <div className="mb-6 grid grid-cols-3 gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                    {[
                        { label: 'Estado', value: 'Guardada', color: 'text-success' },
                        { label: 'Trazabilidad', value: 'Activa' },
                        { label: 'Recordatorio', value: '7 días' },
                    ].map(s => (
                        <div key={s.label} className="text-center">
                            <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{s.label}</div>
                            <div className={`mt-1 text-[13.5px] font-semibold ${s.color || 'text-gray-800'}`}>{s.value}</div>
                        </div>
                    ))}
                </div>

                {/* Next step card */}
                <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                    <div>
                        <h2 className="text-[15px] font-semibold text-gray-900">¿Cuál es el siguiente paso?</h2>
                        <p className="mt-1 text-[13px] text-gray-500">
                            Puedes construir una propuesta comercial con objetivos, entregables y alcance, o pasar directo al envío.
                        </p>
                    </div>
                    <div className="space-y-2.5">
                        <button
                            type="button"
                            onClick={() => router.push(`/dashboard/quotes/${id}/send`)}
                            className="flex w-full items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 text-left transition-colors hover:border-gray-900 hover:bg-surface-2"
                        >
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gray-900 text-white">
                                <FileText size={17} />
                            </div>
                            <div>
                                <div className="text-[13.5px] font-semibold text-gray-900">Construir propuesta comercial</div>
                                <div className="text-[11.5px] text-gray-400">Con IA · Objetivos, entregables, alcance</div>
                            </div>
                        </button>
                        <button
                            type="button"
                            onClick={() => router.push(`/dashboard/quotes/${id}/send`)}
                            className="flex w-full items-center gap-4 rounded-xl border border-dashed border-gray-200 bg-white p-4 text-left transition-colors hover:border-primary hover:bg-primary-soft"
                        >
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
                                <Send size={17} />
                            </div>
                            <div>
                                <div className="text-[13.5px] font-semibold text-gray-900">Ir directo a enviar</div>
                                <div className="text-[11.5px] text-gray-400">Podrás agregar un mensaje personalizado</div>
                            </div>
                        </button>
                    </div>
                    <p className="text-[11.5px] text-gray-400">
                        Si saltas la propuesta, podrás editar un texto libre en la pantalla de envío.
                    </p>
                </div>

                <div className="mt-4 text-center">
                    <button
                        type="button"
                        onClick={() => router.push('/dashboard')}
                        className="inline-flex items-center gap-1.5 text-[12.5px] text-gray-400 hover:text-gray-700 transition-colors"
                    >
                        <ArrowLeft size={12} /> Volver al dashboard
                    </button>
                </div>
            </div>
        </AdminLayout>
    );
}
