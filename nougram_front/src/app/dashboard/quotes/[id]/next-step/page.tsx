'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { ArrowLeft, FileText, Send } from 'lucide-react';
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
        if (!id) {
            setLoading(false);
            return;
        }
        quoteService.getByProjectId(id).then((data) => {
            setQuote(data);
            setLoading(false);
        }).catch(() => setLoading(false));
    }, [id]);

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#F5F5F7]">
                <p className="text-gray-500">Cargando...</p>
            </div>
        );
    }

    if (!quote) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#F5F5F7]">
                <Card className="max-w-md">
                    <CardContent className="pt-6">
                        <p className="text-gray-600">Cotización no encontrada.</p>
                        <Button variant="secondary" className="mt-4" onClick={() => router.push('/dashboard')}>
                            Volver al dashboard
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <AdminLayout hideRightPanel>
            <div className="max-w-2xl mx-auto space-y-6 sm:space-y-8 pb-24 md:pb-8 px-1">
                <div className="flex items-center gap-3 sm:gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard')} className="rounded-2xl h-11 w-11 shrink-0">
                        <ArrowLeft size={20} />
                    </Button>
                    <div className="min-w-0">
                        <h1 className="text-xl sm:text-2xl font-bold text-[#1D1D1F]">Cotización guardada</h1>
                        <p className="text-xs sm:text-sm text-gray-500 mt-1 truncate">
                            {quote.project} · V{quote.version}
                        </p>
                    </div>
                </div>

                <Card className="border border-gray-200 shadow-sm rounded-2xl">
                    <CardContent className="p-5 sm:p-8 space-y-5 sm:space-y-6">
                        <p className="text-sm sm:text-base text-gray-700">
                            Opcionalmente puedes construir una <strong>propuesta comercial</strong> (descripción, objetivos, entregables, alcance) para que el cliente reciba un documento claro junto con la cotización.
                        </p>
                        <p className="text-sm text-gray-500">
                            La descripción de la solicitud que cargaste durante la cotización se usa como base inicial para este paso con IA.
                        </p>
                        <div className="flex flex-col gap-3 sm:flex-row sm:gap-4 pt-2 sm:pt-4">
                            <Button
                                className="flex-1 min-h-12 rounded-2xl bg-[#1D1D1F] text-white hover:bg-gray-800 flex items-center justify-center gap-2 font-bold"
                                onClick={() => router.push(`/dashboard/quotes/${id}/proposal`)}
                            >
                                <FileText size={18} />
                                Construir propuesta comercial
                            </Button>
                            <Button
                                variant="outline"
                                className="flex-1 min-h-12 rounded-2xl flex items-center justify-center gap-2 font-bold"
                                onClick={() => router.push(`/dashboard/quotes/${id}/send`)}
                            >
                                <Send size={18} />
                                Ir a enviar
                            </Button>
                        </div>
                        <p className="text-xs text-gray-400 pt-2">
                            Si saltas este paso, podrás editar un texto libre en la pantalla de envío.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </AdminLayout>
    );
}
