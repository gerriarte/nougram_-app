'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ProposalBuilderHybrid } from '@/components/quotes/ProposalBuilderHybrid';
import { quoteService } from '@/services/quoteService';
import { proposalService, ProposalBody, ProposalDocument } from '@/services/proposalService';
import { Quote } from '@/components/dashboard/QuoteCard';

export default function ProposalBuilderPage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;
    const [quote, setQuote] = useState<Quote | null>(null);
    const [proposal, setProposal] = useState<ProposalDocument | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) {
            setLoading(false);
            return;
        }
        Promise.all([
            quoteService.getByProjectId(id),
            proposalService.getLatest(id),
        ]).then(([q, p]) => {
            setQuote(q ?? null);
            setProposal(p ?? null);
        }).finally(() => setLoading(false));
    }, [id]);

    const handleSave = async (payload: { title: string; body_json: ProposalBody }) => {
        if (!id) return { message: 'Proyecto inválido' };
        let saved: ProposalDocument | null = null;
        if (proposal?.id) {
            saved = await proposalService.update(id, proposal.id, {
                title: payload.title,
                body_json: payload.body_json,
            });
        } else {
            saved = await proposalService.create(id, {
                title: payload.title,
                body_json: payload.body_json,
                status: 'draft',
            });
        }
        if (saved) {
            setProposal(saved);
            const isUpdate = !!proposal?.id;
            return {
                proposalId: saved.id,
                message: isUpdate ? `Borrador actualizado (V${saved.version})` : 'Guardado. Listo para revisar o continuar a envío.',
            };
        }
        throw new Error('No se pudo guardar la propuesta');
    };

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
                <p className="text-gray-600">Cotización no encontrada.</p>
                <button type="button" className="mt-4 text-blue-600" onClick={() => router.push('/dashboard')}>
                    Volver al dashboard
                </button>
            </div>
        );
    }

    return (
        <ProposalBuilderHybrid
            projectId={id}
            projectName={quote.project}
            initialTitle={proposal?.title ?? `Propuesta comercial - ${quote.project}`}
            initialBody={proposal?.body_json}
            initialProposalId={proposal?.id}
            onSave={handleSave}
            onContinueToSend={() => router.push(`/dashboard/quotes/${id}/send`)}
            onCancel={() => router.push(`/dashboard/quotes/${id}/next-step`)}
        />
    );
}
