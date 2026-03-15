'use client';

import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { ArrowLeft, Save, Send, Plus, Trash2, Sparkles } from 'lucide-react';
import type { ProposalBody } from '@/services/proposalService';

const SECTION_LABELS: Record<string, string> = {
    description: 'Descripción del proyecto',
    objectives: 'Objetivos',
    deliverables: 'Entregables',
    scope: 'Alcance',
    timeline: 'Cronograma / hitos',
    conditions: 'Condiciones',
    free_text: 'Notas adicionales',
};

function emptyBody(): ProposalBody {
    return {
        description: '',
        objectives: [],
        deliverables: [],
        scope: '',
        timeline: '',
        conditions: '',
        free_text: '',
    };
}

function bodyFromDoc(body: ProposalBody | undefined): ProposalBody {
    if (!body || typeof body !== 'object') return emptyBody();
    return {
        description: typeof body.description === 'string' ? body.description : '',
        objectives: Array.isArray(body.objectives) ? body.objectives.filter((o): o is string => typeof o === 'string') : [],
        deliverables: Array.isArray(body.deliverables)
            ? body.deliverables.map((d) => (typeof d === 'object' && d && typeof (d as { name?: string }).name === 'string'
                ? { name: (d as { name: string }).name, status: (d as { status?: string }).status }
                : { name: String(d), status: '' }))
            : [],
        scope: typeof body.scope === 'string' ? body.scope : '',
        timeline: typeof body.timeline === 'string' ? body.timeline : '',
        conditions: typeof body.conditions === 'string' ? body.conditions : '',
        free_text: typeof body.free_text === 'string' ? body.free_text : '',
    };
}

export interface ProposalBuilderHybridProps {
    projectId: string;
    projectName: string;
    initialTitle: string;
    initialBody: ProposalBody | undefined;
    initialProposalId?: number;
    onSave: (payload: { title: string; body_json: ProposalBody }) => Promise<{ proposalId?: number; message: string }>;
    onGenerateAI: (payload: {
        title?: string;
        language?: 'es' | 'en';
        extra_instructions?: string;
        services_context?: string;
        proposal_objective?: string;
        estimated_timeline?: string;
        payment_conditions?: string;
        execution_conditions?: string;
        persist_context?: boolean;
    }) => Promise<{ title: string; body_json: ProposalBody; message: string }>;
    onContinueToSend: () => void;
    onCancel: () => void;
    suggestedServicesText?: string;
}

export function ProposalBuilderHybrid({
    projectId,
    projectName,
    initialTitle,
    initialBody,
    initialProposalId,
    onSave,
    onGenerateAI,
    onContinueToSend,
    onCancel,
    suggestedServicesText,
}: ProposalBuilderHybridProps) {
    const [title, setTitle] = useState(initialTitle || `Propuesta comercial - ${projectName}`);
    const [body, setBody] = useState<ProposalBody>(() => bodyFromDoc(initialBody));
    const [saving, setSaving] = useState(false);
    const [generatingAI, setGeneratingAI] = useState(false);
    const [isAIModalOpen, setIsAIModalOpen] = useState(false);
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [aiServicesContext, setAiServicesContext] = useState<string>(
        typeof body.ai_context === 'object' && body.ai_context && typeof (body.ai_context as { services_context?: unknown }).services_context === 'string'
            ? String((body.ai_context as { services_context?: string }).services_context)
            : (suggestedServicesText || '')
    );
    const [aiObjective, setAiObjective] = useState<string>(
        typeof body.ai_context === 'object' && body.ai_context && typeof (body.ai_context as { proposal_objective?: unknown }).proposal_objective === 'string'
            ? String((body.ai_context as { proposal_objective?: string }).proposal_objective)
            : ''
    );
    const [aiTimeline, setAiTimeline] = useState<string>(
        typeof body.ai_context === 'object' && body.ai_context && typeof (body.ai_context as { estimated_timeline?: unknown }).estimated_timeline === 'string'
            ? String((body.ai_context as { estimated_timeline?: string }).estimated_timeline)
            : ''
    );
    const [aiPaymentConditions, setAiPaymentConditions] = useState<string>(
        typeof body.ai_context === 'object' && body.ai_context && typeof (body.ai_context as { payment_conditions?: unknown }).payment_conditions === 'string'
            ? String((body.ai_context as { payment_conditions?: string }).payment_conditions)
            : ''
    );
    const [aiExecutionConditions, setAiExecutionConditions] = useState<string>(
        typeof body.ai_context === 'object' && body.ai_context && typeof (body.ai_context as { execution_conditions?: unknown }).execution_conditions === 'string'
            ? String((body.ai_context as { execution_conditions?: string }).execution_conditions)
            : ''
    );

    const update = useCallback(<K extends keyof ProposalBody>(key: K, value: ProposalBody[K]) => {
        setBody((prev) => ({ ...prev, [key]: value }));
    }, []);

    const addObjective = () => {
        setBody((prev) => ({
            ...prev,
            objectives: [...(prev.objectives || []), ''],
        }));
    };
    const setObjective = (index: number, value: string) => {
        setBody((prev) => {
            const list = [...(prev.objectives || [])];
            list[index] = value;
            return { ...prev, objectives: list };
        });
    };
    const removeObjective = (index: number) => {
        setBody((prev) => ({
            ...prev,
            objectives: (prev.objectives || []).filter((_, i) => i !== index),
        }));
    };

    const addDeliverable = () => {
        setBody((prev) => ({
            ...prev,
            deliverables: [...(prev.deliverables || []), { name: '', status: '' }],
        }));
    };
    const setDeliverable = (index: number, name: string, status?: string) => {
        setBody((prev) => {
            const list = [...(prev.deliverables || [])];
            list[index] = { name, status: status ?? list[index]?.status ?? '' };
            return { ...prev, deliverables: list };
        });
    };
    const removeDeliverable = (index: number) => {
        setBody((prev) => ({
            ...prev,
            deliverables: (prev.deliverables || []).filter((_, i) => i !== index),
        }));
    };

    const handleSave = async () => {
        setSaving(true);
        setFeedback(null);
        try {
            const result = await onSave({ title, body_json: body });
            setFeedback({ type: 'success', text: result.message });
        } catch (e) {
            setFeedback({ type: 'error', text: e instanceof Error ? e.message : 'Error al guardar' });
        } finally {
            setSaving(false);
        }
    };

    const handleGenerateWithAI = async () => {
        setGeneratingAI(true);
        setFeedback(null);
        try {
            const generated = await onGenerateAI({
                title: title || undefined,
                language: 'es',
                services_context: aiServicesContext,
                proposal_objective: aiObjective,
                estimated_timeline: aiTimeline,
                payment_conditions: aiPaymentConditions,
                execution_conditions: aiExecutionConditions,
                persist_context: true,
            });
            setTitle(generated.title || title);
            setBody(bodyFromDoc(generated.body_json));
            setFeedback({ type: 'success', text: generated.message });
            setIsAIModalOpen(false);
        } catch (error) {
            setFeedback({ type: 'error', text: error instanceof Error ? error.message : 'No se pudo generar contenido con IA' });
        } finally {
            setGeneratingAI(false);
        }
    };

    const objectives = body.objectives ?? [];
    const deliverables = body.deliverables ?? [];
    const nonEmptySections = [
        body.description,
        objectives.filter((o) => o.trim()).length ? "obj" : "",
        deliverables.filter((d) => d.name.trim()).length ? "del" : "",
        body.scope,
        body.timeline,
        body.conditions,
        body.free_text,
    ].filter((value) => typeof value === "string" && value.trim().length > 0).length;
    const readyToSend = nonEmptySections >= 2;

    return (
        <div className="min-h-screen bg-[#F5F5F7] p-6">
            <div className="max-w-3xl mx-auto space-y-6">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={onCancel} className="rounded-full">
                        <ArrowLeft size={20} />
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold text-[#1D1D1F]">Propuesta comercial</h1>
                        <p className="text-sm text-gray-500">{projectName}</p>
                        <p className="text-xs text-gray-400">Proyecto #{projectId}</p>
                    </div>
                </div>

                <div className="flex justify-end">
                    <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setIsAIModalOpen(true)}
                        className="inline-flex items-center gap-2"
                    >
                        <Sparkles size={16} />
                        Generar propuesta con IA
                    </Button>
                </div>

                {feedback && (
                    <div
                        className={`rounded-lg border px-4 py-2 text-sm ${
                            feedback.type === 'success' ? 'border-green-200 bg-green-50 text-green-800' : 'border-red-200 bg-red-50 text-red-800'
                        }`}
                        role="status"
                        aria-live="polite"
                    >
                        {feedback.text}
                    </div>
                )}

                <p className="text-sm text-gray-500">
                    Recomendado: completa al menos descripción u objetivos para una propuesta más clara. Todos los campos son opcionales.
                </p>

                <Card>
                    <CardContent className="p-6 space-y-6">
                        <div className={`rounded-md border px-3 py-2 text-xs ${
                            readyToSend ? "border-green-200 bg-green-50 text-green-700" : "border-amber-200 bg-amber-50 text-amber-700"
                        }`}>
                            {readyToSend
                                ? "Listo para enviar: propuesta con contenido suficiente."
                                : "Completa al menos 2 secciones para una propuesta comercial más clara."}
                            {initialProposalId ? ` (ID propuesta: ${initialProposalId})` : ""}
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">Título de la propuesta</label>
                            <Input
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Ej: Propuesta comercial - Rediseño Ecommerce"
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">{SECTION_LABELS.description}</label>
                            <textarea
                                className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                placeholder="Contexto y descripción del proyecto para el cliente."
                                value={body.description ?? ''}
                                onChange={(e) => update('description', e.target.value)}
                            />
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-sm font-medium text-gray-700">{SECTION_LABELS.objectives}</label>
                                <Button type="button" variant="ghost" size="sm" onClick={addObjective}>
                                    <Plus size={14} className="mr-1" /> Añadir
                                </Button>
                            </div>
                            <div className="space-y-2">
                                {objectives.map((obj, i) => (
                                    <div key={i} className="flex gap-2">
                                        <Input
                                            value={obj}
                                            onChange={(e) => setObjective(i, e.target.value)}
                                            placeholder={`Objetivo ${i + 1}`}
                                            className="flex-1"
                                        />
                                        <Button type="button" variant="ghost" size="icon" onClick={() => removeObjective(i)}>
                                            <Trash2 size={16} className="text-gray-400" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-sm font-medium text-gray-700">{SECTION_LABELS.deliverables}</label>
                                <Button type="button" variant="ghost" size="sm" onClick={addDeliverable}>
                                    <Plus size={14} className="mr-1" /> Añadir
                                </Button>
                            </div>
                            <div className="space-y-2">
                                {deliverables.map((d, i) => (
                                    <div key={i} className="flex gap-2 items-center">
                                        <Input
                                            value={d.name}
                                            onChange={(e) => setDeliverable(i, e.target.value, d.status)}
                                            placeholder="Nombre del entregable"
                                            className="flex-1"
                                        />
                                        <Input
                                            value={d.status ?? ''}
                                            onChange={(e) => setDeliverable(i, d.name, e.target.value)}
                                            placeholder="Estado (opcional)"
                                            className="w-28"
                                        />
                                        <Button type="button" variant="ghost" size="icon" onClick={() => removeDeliverable(i)}>
                                            <Trash2 size={16} className="text-gray-400" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">{SECTION_LABELS.scope}</label>
                            <textarea
                                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                placeholder="Alcance incluido y exclusiones."
                                value={body.scope ?? ''}
                                onChange={(e) => update('scope', e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">{SECTION_LABELS.timeline}</label>
                            <textarea
                                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                placeholder="Fases, hitos o cronograma resumido."
                                value={body.timeline ?? ''}
                                onChange={(e) => update('timeline', e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">{SECTION_LABELS.conditions}</label>
                            <textarea
                                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                placeholder="Condiciones comerciales, forma de pago, validez."
                                value={body.conditions ?? ''}
                                onChange={(e) => update('conditions', e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">{SECTION_LABELS.free_text}</label>
                            <textarea
                                className="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                placeholder="Cualquier texto adicional para el cliente."
                                value={body.free_text ?? ''}
                                onChange={(e) => update('free_text', e.target.value)}
                            />
                        </div>
                    </CardContent>
                </Card>

                <div className="flex flex-wrap gap-3 justify-end sticky bottom-4">
                    <Button variant="ghost" onClick={onCancel}>
                        Cancelar
                    </Button>
                    <Button variant="secondary" onClick={handleSave} disabled={saving}>
                        <Save size={16} className="mr-2" />
                        {saving ? 'Guardando...' : 'Guardar borrador'}
                    </Button>
                    <Button className="bg-[#1D1D1F] text-white hover:bg-gray-800" onClick={onContinueToSend}>
                        <Send size={16} className="mr-2" />
                        Continuar a envío
                    </Button>
                </div>
            </div>

            <Dialog open={isAIModalOpen} onOpenChange={setIsAIModalOpen}>
                <DialogContent className="max-w-2xl w-full max-h-[88vh] overflow-hidden p-0">
                    <div className="p-6 border-b border-gray-100">
                        <DialogHeader>
                            <DialogTitle>Contexto para generación con IA</DialogTitle>
                            <DialogDescription>
                                Completa el contexto clave y la IA redactará la propuesta comercial. Este contexto se guardará para mejorar futuras propuestas.
                            </DialogDescription>
                        </DialogHeader>
                    </div>
                    <div className="p-6 space-y-4 overflow-y-auto">
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">Servicios que estás cotizando</label>
                            <textarea
                                className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                value={aiServicesContext}
                                onChange={(e) => setAiServicesContext(e.target.value)}
                                placeholder="Ej: Desarrollo Frontend, UX/UI, Integración de pagos..."
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">¿Cuál es el objetivo de la propuesta?</label>
                            <textarea
                                className="flex min-h-[90px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                value={aiObjective}
                                onChange={(e) => setAiObjective(e.target.value)}
                                placeholder="Ej: Lanzar un MVP en 8 semanas para validar mercado y captar primeros clientes."
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">Tiempo estimado de desarrollo</label>
                            <Input
                                value={aiTimeline}
                                onChange={(e) => setAiTimeline(e.target.value)}
                                placeholder="Ej: 10 semanas, dividido en 4 fases."
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">Condiciones de pago</label>
                            <textarea
                                className="flex min-h-[90px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                value={aiPaymentConditions}
                                onChange={(e) => setAiPaymentConditions(e.target.value)}
                                placeholder="Ej: 40% anticipo, 40% avance, 20% entrega final."
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-2">Condiciones de ejecución</label>
                            <textarea
                                className="flex min-h-[90px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                                value={aiExecutionConditions}
                                onChange={(e) => setAiExecutionConditions(e.target.value)}
                                placeholder="Ej: Reunión semanal, máximo 2 rondas de ajustes por entrega, aprobaciones en 48h."
                            />
                        </div>
                    </div>
                    <DialogFooter className="p-4 border-t border-gray-100 bg-gray-50">
                        <Button variant="secondary" onClick={() => setIsAIModalOpen(false)} disabled={generatingAI}>
                            Cancelar
                        </Button>
                        <Button onClick={handleGenerateWithAI} disabled={generatingAI}>
                            {generatingAI ? 'Generando...' : 'Generar textos con IA'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
