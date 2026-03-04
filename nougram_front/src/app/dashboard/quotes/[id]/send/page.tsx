
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { QuoteSendView } from '@/components/quotes/QuoteSendView';
import type { QuoteSendPayload } from '@/components/quotes/QuoteSendView';
import { quoteService } from '@/services/quoteService';
import { Quote } from '@/components/dashboard/QuoteCard';
import { proposalService, ProposalBody, ProposalDocument } from '@/services/proposalService';

/** Renders hybrid proposal body (guided sections + free_text) for preview and email. */
function proposalBodyToText(body: ProposalBody): string {
    const chunks: string[] = [];
    if (typeof body.executive_summary === 'string' && body.executive_summary.trim()) {
        chunks.push(body.executive_summary.trim());
    }
    if (typeof body.description === 'string' && body.description.trim()) {
        chunks.push(`Descripcion del proyecto:\n${body.description.trim()}`);
    }
    if (Array.isArray(body.objectives) && body.objectives.length > 0) {
        chunks.push(`Objetivos:\n${body.objectives.map((obj) => `- ${obj}`).join('\n')}`);
    }
    if (Array.isArray(body.deliverables) && body.deliverables.length > 0) {
        chunks.push(
            `Entregables:\n${body.deliverables
                .map((item) => `- ${item.name}${item.status ? ` (${item.status})` : ''}`)
                .join('\n')}`
        );
    }
    if (typeof body.scope === 'string' && body.scope.trim()) {
        chunks.push(`Alcance:\n${body.scope.trim()}`);
    }
    if (typeof body.timeline === 'string' && body.timeline.trim()) {
        chunks.push(`Cronograma / hitos:\n${body.timeline.trim()}`);
    }
    if (typeof body.conditions === 'string' && body.conditions.trim()) {
        chunks.push(`Condiciones:\n${body.conditions.trim()}`);
    }
    if (typeof body.free_text === 'string' && body.free_text.trim()) {
        chunks.push(body.free_text.trim());
    }
    return chunks.join('\n\n');
}

function textToProposalBody(text: string): ProposalBody {
    return { free_text: text };
}

export default function SendQuotePage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;
    const [quote, setQuote] = useState<Quote | null>(null);
    const [clientEmail, setClientEmail] = useState<string>('');
    const [proposal, setProposal] = useState<ProposalDocument | null>(null);
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
            const latestProposal = await proposalService.getLatest(id);
            setProposal(latestProposal);
            setLoading(false);
        };
        loadQuote();
    }, [id]);

    const handleSend = async (data: QuoteSendPayload) => {
        if (!id) return { ok: false, message: 'Proyecto inválido' };
        try {
            const result = await quoteService.sendEmail(id, data, quote?.quoteId);
            return { ok: true, message: result.message || 'Cotización enviada correctamente' };
        } catch (error) {
            console.error("Failed to send quote", error);
            const message = error instanceof Error ? error.message : "Error al enviar la cotización";
            return { ok: false, message };
        }
    };

    if (loading) {
        return <div className="flex h-screen items-center justify-center">Cargando...</div>;
    }

    if (!quote) {
        return <div className="flex h-screen items-center justify-center">Cotización no encontrada</div>;
    }

    const handleSaveProposal = async (payload: { title: string; text: string }) => {
        if (!id) return { message: 'Proyecto inválido' };
        const body = textToProposalBody(payload.text);
        let saved: ProposalDocument | null = null;
        if (proposal?.id) {
            saved = await proposalService.update(id, proposal.id, {
                title: payload.title,
                body_json: body,
            });
        } else {
            saved = await proposalService.create(id, {
                title: payload.title,
                body_json: body,
                status: 'draft',
            });
        }
        if (saved) {
            setProposal(saved);
            return {
                proposalId: saved.id,
                message: `Propuesta guardada (V${saved.version})`,
            };
        }
        throw new Error('No se pudo guardar la propuesta');
    };

    const handleGenerateProposalAI = async () => {
        if (!id) throw new Error('Proyecto inválido');
        const generated = await proposalService.generateAI(id, { language: 'es' });
        if (!generated) {
            throw new Error('No se pudo generar propuesta con IA');
        }
        setProposal(generated);
        return {
            title: generated.title,
            text: proposalBodyToText(generated.body_json || {}),
            version: generated.version,
            message: 'Propuesta generada con IA',
        };
    };

    return (
        <QuoteSendView
            quote={quote}
            initialToEmail={clientEmail}
            initialProposalTitle={proposal?.title}
            initialProposalText={proposal ? proposalBodyToText(proposal.body_json || {}) : ''}
            proposalVersion={proposal?.version}
            initialProposalId={proposal?.id}
            onSend={handleSend}
            onSaveProposal={handleSaveProposal}
            onGenerateProposalAI={handleGenerateProposalAI}
            onCancel={() => router.back()}
        />
    );
}
