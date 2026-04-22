'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ProposalBuilderHybrid } from '@/components/quotes/ProposalBuilderHybrid';
import { quoteService } from '@/services/quoteService';
import { proposalService, ProposalBody, ProposalDocument } from '@/services/proposalService';
import { Quote } from '@/components/dashboard/QuoteCard';
import { getQuoteEditorMeta } from '@/lib/quote-editor-meta';
import { trackProposalGeneratedWithAI } from '@/lib/analytics';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';

export default function ProposalBuilderPage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;
    const [quote, setQuote] = useState<Quote | null>(null);
    const [proposal, setProposal] = useState<ProposalDocument | null>(null);
    const [suggestedServicesText, setSuggestedServicesText] = useState<string>('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) {
            setLoading(false);
            return;
        }
        Promise.all([
            quoteService.getByProjectId(id),
            proposalService.getLatest(id),
            quoteService.getBuilderData(id),
        ]).then(([q, p, builderData]) => {
            setQuote(q ?? null);
            setProposal(p ?? null);
            const services = (builderData?.items || [])
                .map((item) => item.serviceName?.trim())
                .filter((name): name is string => Boolean(name));
            if (services.length) {
                setSuggestedServicesText(Array.from(new Set(services)).join('\n'));
            }
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

    const handleGenerateAI = async (payload: {
        title?: string;
        language?: 'es' | 'en';
        extra_instructions?: string;
        services_context?: string;
        proposal_objective?: string;
        estimated_timeline?: string;
        payment_conditions?: string;
        execution_conditions?: string;
        persist_context?: boolean;
    }) => {
        const generated = await proposalService.generateAI(id, payload);
        if (!generated) {
            throw new Error('No se pudo generar la propuesta con IA');
        }
        setProposal(generated);
        trackProposalGeneratedWithAI({
            project_id: id,
            quote_id: quote?.quoteId != null ? String(quote.quoteId) : undefined,
            proposal_id: generated?.id != null ? String(generated.id) : undefined,
        });
        return {
            title: generated.title,
            body_json: generated.body_json,
            message: `Propuesta generada con IA (V${generated.version}).`,
        };
    };

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background">
                <p className="text-gray-500">Cargando...</p>
            </div>
        );
    }

    if (!quote) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background">
                <p className="text-gray-600">Cotización no encontrada.</p>
                <button type="button" className="mt-4 text-primary" onClick={() => router.push('/dashboard')}>
                    Volver al dashboard
                </button>
            </div>
        );
    }

    const editorMeta = getQuoteEditorMeta(id);
    const initialProposalBody: ProposalBody | undefined = proposal?.body_json ?? (
        editorMeta.projectDescription
            ? { description: editorMeta.projectDescription }
            : undefined
    );

    return (
        <AdminLayout hideRightPanel>
            <div className="max-w-[1200px] mx-auto w-full px-1 sm:px-0 pb-6">
                <ProposalBuilderHybrid
                    projectId={id}
                    projectName={quote.project}
                    initialTitle={proposal?.title ?? `Propuesta comercial - ${quote.project}`}
                    initialBody={initialProposalBody}
                    initialProposalId={proposal?.id}
                    onSave={handleSave}
                    onGenerateAI={handleGenerateAI}
                    onContinueToSend={() => router.push(`/dashboard/quotes/${id}/send`)}
                    onCancel={() => router.push(`/dashboard/quotes/${id}/send`)}
                    suggestedServicesText={suggestedServicesText}
                />
            </div>
        </AdminLayout>
    );
}
