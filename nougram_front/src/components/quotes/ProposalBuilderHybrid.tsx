'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import {
    ArrowLeft, Save, Send, Plus, Trash2, Sparkles,
    ChevronDown, ChevronUp, Key, Eye, EyeOff, CheckCircle2, AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAIApiKey, type AIProvider } from '@/hooks/useAIApiKey';
import { proposalService, type ProposalBody, type ProposalBranding, type ProposalSectionPlanItem } from '@/services/proposalService';
import { VersionSelector } from '@/components/quotes/builder/VersionSelector';

const SECTION_LABELS: Record<string, string> = {
    description: 'Descripción del proyecto',
    objectives: 'Objetivos',
    deliverables: 'Entregables',
    scope: 'Alcance',
    timeline: 'Cronograma / hitos',
    conditions: 'Condiciones',
    free_text: 'Notas adicionales',
};

const AI_TONES = [
    { id: 'consultive', label: 'Consultivo', hint: 'Experto y estratégico' },
    { id: 'close', label: 'Cercano', hint: 'Humano y conversacional' },
    { id: 'formal', label: 'Formal', hint: 'Corporativo y conciso' },
    { id: 'bold', label: 'Enérgico', hint: 'Directo y persuasivo' },
];

const AI_SECTION_PLAN: ProposalSectionPlanItem[] = [
    { id: 'executive_summary', label: 'Resumen ejecutivo', enabled: true },
    { id: 'description', label: 'Contexto y diagnóstico', enabled: true },
    { id: 'objectives', label: 'Objetivos del proyecto', enabled: true },
    { id: 'deliverables', label: 'Entregables y alcance', enabled: true },
    { id: 'timeline', label: 'Cronograma', enabled: true },
    { id: 'conditions', label: 'Términos y condiciones', enabled: true },
    { id: 'team', label: 'Equipo asignado', enabled: false },
    { id: 'case_studies', label: 'Casos de estudio', enabled: false },
];

function emptyBody(): ProposalBody {
    return {
        description: '',
        objectives: [],
        deliverables: [],
        scope: '',
        timeline: '',
        conditions: '',
        free_text: '',
        branding: {
            brandColor: '#D97757',
            logoUrl: '',
            coverImageUrl: '',
        },
    };
}

function brandingFromDoc(body: ProposalBody): ProposalBranding {
    const branding = body.branding && typeof body.branding === 'object'
        ? body.branding as ProposalBranding
        : {};
    return {
        brandColor: typeof branding.brandColor === 'string' && branding.brandColor ? branding.brandColor : '#D97757',
        logoUrl: typeof branding.logoUrl === 'string' ? branding.logoUrl : '',
        coverImageUrl: typeof branding.coverImageUrl === 'string' ? branding.coverImageUrl : '',
    };
}

function bodyFromDoc(body: ProposalBody | undefined): ProposalBody {
    if (!body || typeof body !== 'object') return emptyBody();
    return {
        ...body,
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
        branding: brandingFromDoc(body),
    };
}

// ── Section card wrapper ───────────────────────────────────────────
function SectionCard({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
    return (
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">{title}</span>
                {action}
            </div>
            <div className="p-4 space-y-3">{children}</div>
        </div>
    );
}

// ── Textarea styled to match design system ─────────────────────────
function Textarea({ value, onChange, placeholder, minRows = 3 }: {
    value: string; onChange: (v: string) => void; placeholder?: string; minRows?: number;
}) {
    return (
        <textarea
            style={{ minHeight: `${minRows * 1.6}rem` }}
            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-[13px] text-gray-800 placeholder:text-gray-400 focus:border-gray-400 focus:outline-none resize-none transition-colors"
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
        />
    );
}

// ── AI Key Settings panel ─────────────────────────────────────────
function AIKeyPanel() {
    const { provider, apiKey, setProvider, setApiKey, clearKey, loaded } = useAIApiKey();
    const [showKey, setShowKey] = useState(false);
    const [draft, setDraft] = useState('');
    const [saved, setSaved] = useState(false);

    if (!loaded) return null;

    const hasKey = !!apiKey;
    const maskedKey = apiKey ? `${apiKey.slice(0, 8)}${'•'.repeat(Math.min(20, apiKey.length - 8))}` : '';

    const handleSave = () => {
        const trimmed = draft.trim();
        if (!trimmed) return;
        setApiKey(trimmed);
        setDraft('');
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const handleClear = () => {
        clearKey();
        setDraft('');
    };

    return (
        <div className="space-y-3">
            {/* Provider selector */}
            <div>
                <label className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 block mb-1.5">Proveedor de IA</label>
                <div className="flex gap-1 rounded-lg bg-surface-2 p-1">
                    {(['openai', 'anthropic'] as AIProvider[]).map(p => (
                        <button
                            key={p}
                            type="button"
                            onClick={() => setProvider(p)}
                            className={cn(
                                'flex-1 h-7 rounded-md text-[12px] font-semibold transition-colors',
                                provider === p ? 'bg-white shadow-sm text-gray-800' : 'text-gray-400 hover:text-gray-600'
                            )}
                        >
                            {p === 'openai' ? 'OpenAI' : 'Anthropic'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Current key status */}
            {hasKey ? (
                <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2">
                    <div className="flex items-center gap-2 min-w-0">
                        <CheckCircle2 size={13} className="text-success shrink-0" />
                        <span className="text-[12px] text-gray-600 font-mono truncate">
                            {showKey ? apiKey : maskedKey}
                        </span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0 ml-2">
                        <button type="button" onClick={() => setShowKey(v => !v)} className="text-gray-400 hover:text-gray-600">
                            {showKey ? <EyeOff size={13} /> : <Eye size={13} />}
                        </button>
                        <button type="button" onClick={handleClear} className="text-[11px] text-red-400 hover:text-red-600 font-medium">
                            Borrar
                        </button>
                    </div>
                </div>
            ) : (
                <div className="flex items-center gap-1.5 rounded-lg border border-dashed border-gray-200 bg-surface-2 px-3 py-2">
                    <AlertCircle size={12} className="text-gray-400 shrink-0" />
                    <span className="text-[11.5px] text-gray-400">Sin clave configurada · se usará la API interna</span>
                </div>
            )}

            {/* Key input */}
            <div className="flex gap-2">
                <div className="relative flex-1">
                    <input
                        type={showKey ? 'text' : 'password'}
                        value={draft}
                        onChange={e => setDraft(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') handleSave(); }}
                        placeholder={provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
                        className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-[12.5px] font-mono placeholder:text-gray-400 focus:border-gray-400 focus:outline-none"
                    />
                </div>
                <button
                    type="button"
                    onClick={handleSave}
                    disabled={!draft.trim()}
                    className={cn(
                        'px-3 rounded-lg text-[12px] font-semibold transition-colors',
                        draft.trim()
                            ? saved
                                ? 'bg-success text-white'
                                : 'bg-gray-900 text-white hover:bg-gray-700'
                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    )}
                >
                    {saved ? '✓' : 'Guardar'}
                </button>
            </div>
            <p className="text-[10.5px] text-gray-400">
                La clave se guarda solo en tu navegador. Nunca se almacena en el servidor.
            </p>
        </div>
    );
}

// ── Props ─────────────────────────────────────────────────────────
export interface ProposalBuilderHybridProps {
    projectId: string;
    projectName: string;
    initialTitle: string;
    initialBody: ProposalBody | undefined;
    initialProposalId?: number;
    currentVersion?: number;
    versions?: Array<{ version: number }>;
    onSelectVersion?: (version: number) => void;
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
        tone?: string;
        audience?: string;
        differentiators?: string;
        section_plan?: ProposalSectionPlanItem[];
        persist_context?: boolean;
        user_api_key?: string;
        ai_provider?: 'openai' | 'anthropic';
    }) => Promise<{ title: string; body_json: ProposalBody; message: string }>;
    onContinueToSend: () => void;
    onCancel: () => void;
    suggestedServicesText?: string;
}

// ── Main component ────────────────────────────────────────────────
export function ProposalBuilderHybrid({
    projectName,
    initialTitle,
    initialBody,
    initialProposalId,
    currentVersion,
    versions,
    onSelectVersion,
    onSave,
    onGenerateAI,
    onContinueToSend,
    onCancel,
    suggestedServicesText,
}: ProposalBuilderHybridProps) {
    const { provider, apiKey, loaded } = useAIApiKey();

    const [title, setTitle] = useState(initialTitle || `Propuesta comercial - ${projectName}`);
    const [body, setBody] = useState<ProposalBody>(() => bodyFromDoc(initialBody));
    const [saving, setSaving] = useState(false);
    const [generatingAI, setGeneratingAI] = useState(false);
    const [uploadingAsset, setUploadingAsset] = useState<'logo' | 'cover' | null>(null);
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    // AI context fields
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
    const aiBrief = body.ai_brief && typeof body.ai_brief === 'object' ? body.ai_brief as {
        tone?: unknown;
        audience?: unknown;
        differentiators?: unknown;
    } : {};
    const initialLayout = body.layout && typeof body.layout === 'object' ? body.layout as {
        section_plan?: unknown;
    } : {};
    const [aiTone, setAiTone] = useState<string>(
        typeof aiBrief.tone === 'string' && aiBrief.tone ? aiBrief.tone : 'consultive'
    );
    const [aiAudience, setAiAudience] = useState<string>(
        typeof aiBrief.audience === 'string' ? aiBrief.audience : ''
    );
    const [aiDifferentiators, setAiDifferentiators] = useState<string>(
        typeof aiBrief.differentiators === 'string' ? aiBrief.differentiators : ''
    );
    const [aiSectionPlan, setAiSectionPlan] = useState<ProposalSectionPlanItem[]>(() => {
        if (Array.isArray(initialLayout.section_plan)) {
            const saved = initialLayout.section_plan
                .filter((item): item is ProposalSectionPlanItem => (
                    Boolean(item) &&
                    typeof item === 'object' &&
                    typeof (item as ProposalSectionPlanItem).id === 'string'
                ))
                .map((item) => ({
                    id: item.id,
                    label: item.label,
                    enabled: item.enabled !== false,
                }));
            if (saved.length > 0) return saved;
        }
        return AI_SECTION_PLAN;
    });

    useEffect(() => {
        const nextBody = bodyFromDoc(initialBody);
        const nextContext = nextBody.ai_context && typeof nextBody.ai_context === 'object'
            ? nextBody.ai_context as Record<string, unknown>
            : {};
        const nextBrief = nextBody.ai_brief && typeof nextBody.ai_brief === 'object'
            ? nextBody.ai_brief as Record<string, unknown>
            : {};
        const nextLayout = nextBody.layout && typeof nextBody.layout === 'object'
            ? nextBody.layout as { section_plan?: unknown }
            : {};

        setTitle(initialTitle || `Propuesta comercial - ${projectName}`);
        setBody(nextBody);
        setAiServicesContext(
            typeof nextContext.services_context === 'string'
                ? nextContext.services_context
                : (suggestedServicesText || '')
        );
        setAiObjective(typeof nextContext.proposal_objective === 'string' ? nextContext.proposal_objective : '');
        setAiTimeline(typeof nextContext.estimated_timeline === 'string' ? nextContext.estimated_timeline : '');
        setAiPaymentConditions(typeof nextContext.payment_conditions === 'string' ? nextContext.payment_conditions : '');
        setAiExecutionConditions(typeof nextContext.execution_conditions === 'string' ? nextContext.execution_conditions : '');
        setAiTone(typeof nextBrief.tone === 'string' && nextBrief.tone ? nextBrief.tone : 'consultive');
        setAiAudience(typeof nextBrief.audience === 'string' ? nextBrief.audience : '');
        setAiDifferentiators(typeof nextBrief.differentiators === 'string' ? nextBrief.differentiators : '');
        setAiSectionPlan(
            Array.isArray(nextLayout.section_plan)
                ? nextLayout.section_plan
                    .filter((item): item is ProposalSectionPlanItem => (
                        Boolean(item) &&
                        typeof item === 'object' &&
                        typeof (item as ProposalSectionPlanItem).id === 'string'
                    ))
                    .map((item) => ({
                        id: item.id,
                        label: item.label,
                        enabled: item.enabled !== false,
                    }))
                : AI_SECTION_PLAN
        );
        setFeedback(null);
    }, [initialTitle, initialBody, projectName, suggestedServicesText]);

    // Panel collapse states
    const [aiKeyOpen, setAiKeyOpen] = useState(false);

    const update = useCallback(<K extends keyof ProposalBody>(key: K, value: ProposalBody[K]) => {
        setBody((prev) => ({ ...prev, [key]: value }));
    }, []);
    const updateBranding = (patch: Partial<ProposalBranding>) => {
        setBody((prev) => ({
            ...prev,
            branding: {
                ...brandingFromDoc(prev),
                ...patch,
            },
        }));
    };
    const handleAssetUpload = async (assetType: 'logo' | 'cover', file?: File | null) => {
        if (!file) return;
        if (!initialProposalId) {
            setFeedback({ type: 'error', text: 'Guarda la propuesta antes de subir logo o portada.' });
            return;
        }
        setUploadingAsset(assetType);
        setFeedback(null);
        try {
            const uploaded = await proposalService.uploadAsset(projectId, initialProposalId, assetType, file);
            if (!uploaded) throw new Error('No se pudo subir el asset a Contabo');
            setBody(bodyFromDoc(uploaded.body_json));
            setFeedback({ type: 'success', text: assetType === 'logo' ? 'Logo actualizado.' : 'Portada actualizada.' });
        } catch (error) {
            setFeedback({ type: 'error', text: error instanceof Error ? error.message : 'Error subiendo asset.' });
        } finally {
            setUploadingAsset(null);
        }
    };

    const addObjective = () => setBody(p => ({ ...p, objectives: [...(p.objectives || []), ''] }));
    const setObjective = (i: number, v: string) => setBody(p => { const l = [...(p.objectives || [])]; l[i] = v; return { ...p, objectives: l }; });
    const removeObjective = (i: number) => setBody(p => ({ ...p, objectives: (p.objectives || []).filter((_, j) => j !== i) }));

    const addDeliverable = () => setBody(p => ({ ...p, deliverables: [...(p.deliverables || []), { name: '', status: '' }] }));
    const setDeliverable = (i: number, name: string, status?: string) => setBody(p => {
        const l = [...(p.deliverables || [])];
        l[i] = { name, status: status ?? l[i]?.status ?? '' };
        return { ...p, deliverables: l };
    });
    const removeDeliverable = (i: number) => setBody(p => ({ ...p, deliverables: (p.deliverables || []).filter((_, j) => j !== i) }));
    const toggleAISection = (sectionId: string) => {
        setAiSectionPlan((prev) => prev.map((item) => (
            item.id === sectionId ? { ...item, enabled: !item.enabled } : item
        )));
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
                tone: aiTone,
                audience: aiAudience,
                differentiators: aiDifferentiators,
                section_plan: aiSectionPlan,
                persist_context: true,
                user_api_key: (loaded && apiKey) ? apiKey : undefined,
                ai_provider: (loaded && apiKey) ? provider : undefined,
            });
            setTitle(generated.title || title);
            setBody(bodyFromDoc(generated.body_json));
            setFeedback({ type: 'success', text: generated.message });
        } catch (error) {
            setFeedback({ type: 'error', text: error instanceof Error ? error.message : 'No se pudo generar contenido con IA' });
        } finally {
            setGeneratingAI(false);
        }
    };

    const objectives = body.objectives ?? [];
    const deliverables = body.deliverables ?? [];
    const branding = brandingFromDoc(body);
    const nonEmptySections = [
        body.description,
        objectives.filter(o => o.trim()).length ? 'obj' : '',
        deliverables.filter(d => d.name.trim()).length ? 'del' : '',
        body.scope,
        body.timeline,
        body.conditions,
        body.free_text,
    ].filter(v => typeof v === 'string' && v.trim().length > 0).length;
    const readyToSend = nonEmptySections >= 2;

    return (
        <div className="min-h-screen bg-background">
            {/* Top bar */}
            <div className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-surface-2 hover:text-gray-700 transition-colors"
                    >
                        <ArrowLeft size={16} />
                    </button>
                    <div>
                        <div className="text-[13.5px] font-semibold text-gray-900 leading-tight">Propuesta comercial</div>
                        <div className="text-[11px] text-gray-400">{projectName}{initialProposalId ? ` · ID ${initialProposalId}` : ''}</div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {versions && versions.length > 0 && currentVersion && (
                        <VersionSelector
                            currentVersion={`v${currentVersion}`}
                            versions={versions}
                            onSelectVersion={(version) => {
                                const numeric = Number(version.replace(/[^0-9]/g, ''));
                                if (Number.isFinite(numeric)) onSelectVersion?.(numeric);
                            }}
                        />
                    )}
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-[12.5px] font-semibold text-gray-700 hover:bg-surface-2 disabled:opacity-50 transition-colors"
                    >
                        <Save size={13} />
                        {saving ? 'Guardando...' : 'Guardar'}
                    </button>
                    <button
                        type="button"
                        onClick={onContinueToSend}
                        className="flex items-center gap-1.5 rounded-lg bg-gray-900 px-3 py-1.5 text-[12.5px] font-semibold text-white hover:bg-gray-700 transition-colors"
                    >
                        <Send size={13} />
                        Continuar a envío
                    </button>
                </div>
            </div>

            <div className="mx-auto max-w-5xl px-6 py-8 grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">
                {/* ── Left: Form ── */}
                <div className="space-y-4">
                    {/* Feedback */}
                    {feedback && (
                        <div className={cn(
                            'flex items-start gap-2.5 rounded-xl border px-4 py-3 text-[13px]',
                            feedback.type === 'success'
                                ? 'border-green-200 bg-success-soft text-green-800'
                                : 'border-red-200 bg-critical-soft text-red-800'
                        )}>
                            {feedback.type === 'success'
                                ? <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                                : <AlertCircle size={14} className="mt-0.5 shrink-0" />}
                            {feedback.text}
                        </div>
                    )}

                    {/* Readiness indicator */}
                    <div className={cn(
                        'rounded-xl border px-4 py-2.5 text-[12px] font-medium',
                        readyToSend ? 'border-green-200 bg-success-soft text-green-700' : 'border-amber-200 bg-warning-soft text-amber-700'
                    )}>
                        {readyToSend
                            ? '✓ Propuesta con contenido suficiente para enviar'
                            : 'Completa al menos 2 secciones para una propuesta más clara'}
                    </div>

                    {/* Title */}
                    <SectionCard title="Título de la propuesta">
                        <Input
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            placeholder="Ej: Propuesta comercial — Rediseño Ecommerce"
                        />
                    </SectionCard>

                    {/* Branding */}
                    <SectionCard title="Personalización visual">
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-[120px_1fr]">
                            <div
                                className="min-h-[96px] overflow-hidden rounded-xl border border-gray-200 bg-surface-2"
                                style={{
                                    background: branding.coverImageUrl
                                        ? `linear-gradient(135deg, ${branding.brandColor || '#D97757'}33, rgba(0,0,0,0.1)), url(${branding.coverImageUrl}) center/cover`
                                        : `linear-gradient(135deg, ${branding.brandColor || '#D97757'}33, #fff)`,
                                }}
                            >
                                <div className="flex h-full items-end p-3">
                                    <div
                                        className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/90 text-[11px] font-black shadow-sm"
                                        style={{ color: branding.brandColor || '#D97757' }}
                                    >
                                        {branding.logoUrl ? (
                                            <span
                                                className="h-7 w-7 rounded bg-contain bg-center bg-no-repeat"
                                                style={{ backgroundImage: `url(${branding.logoUrl})` }}
                                            />
                                        ) : 'NG'}
                                    </div>
                                </div>
                            </div>
                            <div className="grid gap-3">
                                <div className="grid grid-cols-[auto_1fr] gap-2">
                                    <input
                                        type="color"
                                        value={branding.brandColor || '#D97757'}
                                        onChange={e => updateBranding({ brandColor: e.target.value })}
                                        className="h-9 w-11 cursor-pointer rounded-lg border border-gray-200 bg-white p-1"
                                        aria-label="Color de marca"
                                    />
                                    <Input
                                        value={branding.brandColor || ''}
                                        onChange={e => updateBranding({ brandColor: e.target.value })}
                                        placeholder="#D97757"
                                        className="font-mono text-[12.5px]"
                                    />
                                </div>
                                <Input
                                    value={branding.logoUrl || ''}
                                    onChange={e => updateBranding({ logoUrl: e.target.value })}
                                    placeholder="URL del logo (opcional)"
                                    className="text-[12.5px]"
                                />
                                <label className={cn(
                                    'flex h-9 cursor-pointer items-center justify-center rounded-lg border border-dashed border-gray-200 bg-surface-2 text-[12px] font-semibold text-gray-500 hover:border-primary/40 hover:text-primary',
                                    (!initialProposalId || uploadingAsset === 'logo') && 'cursor-not-allowed opacity-60'
                                )}>
                                    {uploadingAsset === 'logo' ? 'Subiendo logo...' : 'Subir logo a Contabo'}
                                    <input
                                        type="file"
                                        accept="image/png,image/jpeg,image/webp,image/svg+xml"
                                        className="hidden"
                                        disabled={!initialProposalId || uploadingAsset !== null}
                                        onChange={(event) => {
                                            void handleAssetUpload('logo', event.target.files?.[0]);
                                            event.target.value = '';
                                        }}
                                    />
                                </label>
                                <Input
                                    value={branding.coverImageUrl || ''}
                                    onChange={e => updateBranding({ coverImageUrl: e.target.value })}
                                    placeholder="URL de imagen de portada (opcional)"
                                    className="text-[12.5px]"
                                />
                                <label className={cn(
                                    'flex h-9 cursor-pointer items-center justify-center rounded-lg border border-dashed border-gray-200 bg-surface-2 text-[12px] font-semibold text-gray-500 hover:border-primary/40 hover:text-primary',
                                    (!initialProposalId || uploadingAsset === 'cover') && 'cursor-not-allowed opacity-60'
                                )}>
                                    {uploadingAsset === 'cover' ? 'Subiendo portada...' : 'Subir portada a Contabo'}
                                    <input
                                        type="file"
                                        accept="image/png,image/jpeg,image/webp"
                                        className="hidden"
                                        disabled={!initialProposalId || uploadingAsset !== null}
                                        onChange={(event) => {
                                            void handleAssetUpload('cover', event.target.files?.[0]);
                                            event.target.value = '';
                                        }}
                                    />
                                </label>
                                {!initialProposalId && (
                                    <p className="text-[10.5px] text-gray-400">
                                        Guarda la propuesta antes de subir archivos.
                                    </p>
                                )}
                            </div>
                        </div>
                    </SectionCard>

                    {/* Description */}
                    <SectionCard title={SECTION_LABELS.description}>
                        <Textarea
                            value={body.description ?? ''}
                            onChange={v => update('description', v)}
                            placeholder="Contexto y descripción del proyecto para el cliente."
                            minRows={4}
                        />
                    </SectionCard>

                    {/* Objectives */}
                    <SectionCard
                        title={SECTION_LABELS.objectives}
                        action={
                            <button type="button" onClick={addObjective}
                                className="flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/80">
                                <Plus size={11} /> Añadir
                            </button>
                        }
                    >
                        {objectives.length === 0 ? (
                            <p className="text-[12px] text-gray-400">
                                Sin objetivos. Pulsa &ldquo;Añadir&rdquo; para agregar.
                            </p>
                        ) : (
                            <div className="space-y-2">
                                {objectives.map((obj, i) => (
                                    <div key={i} className="flex gap-2">
                                        <Input
                                            value={obj}
                                            onChange={e => setObjective(i, e.target.value)}
                                            placeholder={`Objetivo ${i + 1}`}
                                            className="flex-1 text-[13px]"
                                        />
                                        <button type="button" onClick={() => removeObjective(i)}
                                            className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 hover:bg-critical-soft hover:text-critical transition-colors">
                                            <Trash2 size={13} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </SectionCard>

                    {/* Deliverables */}
                    <SectionCard
                        title={SECTION_LABELS.deliverables}
                        action={
                            <button type="button" onClick={addDeliverable}
                                className="flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/80">
                                <Plus size={11} /> Añadir
                            </button>
                        }
                    >
                        {deliverables.length === 0 ? (
                            <p className="text-[12px] text-gray-400">
                                Sin entregables. Pulsa &ldquo;Añadir&rdquo; para agregar.
                            </p>
                        ) : (
                            <div className="space-y-2">
                                {deliverables.map((d, i) => (
                                    <div key={i} className="flex gap-2 items-center">
                                        <Input
                                            value={d.name}
                                            onChange={e => setDeliverable(i, e.target.value, d.status)}
                                            placeholder="Nombre del entregable"
                                            className="flex-1 text-[13px]"
                                        />
                                        <Input
                                            value={d.status ?? ''}
                                            onChange={e => setDeliverable(i, d.name, e.target.value)}
                                            placeholder="Estado"
                                            className="w-28 text-[13px]"
                                        />
                                        <button type="button" onClick={() => removeDeliverable(i)}
                                            className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 hover:bg-critical-soft hover:text-critical transition-colors">
                                            <Trash2 size={13} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </SectionCard>

                    {/* Scope */}
                    <SectionCard title={SECTION_LABELS.scope}>
                        <Textarea
                            value={body.scope ?? ''}
                            onChange={v => update('scope', v)}
                            placeholder="Alcance incluido y exclusiones."
                        />
                    </SectionCard>

                    {/* Timeline */}
                    <SectionCard title={SECTION_LABELS.timeline}>
                        <Textarea
                            value={body.timeline ?? ''}
                            onChange={v => update('timeline', v)}
                            placeholder="Fases, hitos o cronograma resumido."
                        />
                    </SectionCard>

                    {/* Conditions */}
                    <SectionCard title={SECTION_LABELS.conditions}>
                        <Textarea
                            value={body.conditions ?? ''}
                            onChange={v => update('conditions', v)}
                            placeholder="Condiciones comerciales, forma de pago, validez."
                        />
                    </SectionCard>

                    {/* Free text */}
                    <SectionCard title={SECTION_LABELS.free_text}>
                        <Textarea
                            value={body.free_text ?? ''}
                            onChange={v => update('free_text', v)}
                            placeholder="Cualquier texto adicional para el cliente."
                            minRows={4}
                        />
                    </SectionCard>
                </div>

                {/* ── Right: AI panel ── */}
                <aside className="sticky top-20 space-y-3">
                    {/* Generate button */}
                    <button
                        type="button"
                        onClick={handleGenerateWithAI}
                        disabled={generatingAI}
                        className={cn(
                            'flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-[13.5px] font-semibold transition-colors',
                            generatingAI
                                ? 'bg-gray-100 text-gray-400 cursor-wait'
                                : 'bg-gray-900 text-white hover:bg-gray-700'
                        )}
                    >
                        <Sparkles size={15} className={generatingAI ? 'animate-pulse' : ''} />
                        {generatingAI ? 'Generando propuesta...' : 'Generar con IA'}
                    </button>

                    {/* AI context card */}
                    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
                        <div className="px-4 py-3 border-b border-gray-100">
                            <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">Contexto para IA</span>
                        </div>
                        <div className="p-4 space-y-3">
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Servicios cotizados</label>
                                <Textarea
                                    value={aiServicesContext}
                                    onChange={setAiServicesContext}
                                    placeholder="Ej: Desarrollo Frontend, UX/UI, Pagos..."
                                    minRows={2}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Objetivo de la propuesta</label>
                                <Textarea
                                    value={aiObjective}
                                    onChange={setAiObjective}
                                    placeholder="Ej: Lanzar MVP en 8 semanas..."
                                    minRows={2}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Tono</label>
                                <div className="grid grid-cols-2 gap-2">
                                    {AI_TONES.map((tone) => {
                                        const active = aiTone === tone.id;
                                        return (
                                            <button
                                                key={tone.id}
                                                type="button"
                                                onClick={() => setAiTone(tone.id)}
                                                className={cn(
                                                    'rounded-lg border px-2.5 py-2 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/25',
                                                    active
                                                        ? 'border-primary bg-primary-soft text-primary'
                                                        : 'border-gray-200 bg-white text-gray-600 hover:bg-surface-2'
                                                )}
                                            >
                                                <div className="text-[11.5px] font-bold">{tone.label}</div>
                                                <div className="mt-0.5 text-[10px] text-gray-400">{tone.hint}</div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Audiencia</label>
                                <Input
                                    value={aiAudience}
                                    onChange={e => setAiAudience(e.target.value)}
                                    placeholder="Ej: CEO y CFO de una startup fintech"
                                    className="text-[12.5px]"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Diferenciadores</label>
                                <Textarea
                                    value={aiDifferentiators}
                                    onChange={setAiDifferentiators}
                                    placeholder="Ej: Experiencia en fintech LATAM, equipo in-house, casos similares..."
                                    minRows={2}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Tiempo estimado</label>
                                <Input
                                    value={aiTimeline}
                                    onChange={e => setAiTimeline(e.target.value)}
                                    placeholder="Ej: 10 semanas, 4 fases"
                                    className="text-[12.5px]"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Condiciones de pago</label>
                                <Textarea
                                    value={aiPaymentConditions}
                                    onChange={setAiPaymentConditions}
                                    placeholder="Ej: 40% anticipo, 40% avance, 20% entrega"
                                    minRows={2}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Condiciones de ejecución</label>
                                <Textarea
                                    value={aiExecutionConditions}
                                    onChange={setAiExecutionConditions}
                                    placeholder="Ej: Reunión semanal, 2 rondas de ajustes"
                                    minRows={2}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10.5px] font-semibold text-gray-500">Secciones a incluir</label>
                                <div className="space-y-1.5 rounded-lg border border-gray-200 bg-surface-2 p-2">
                                    {aiSectionPlan.map((section) => (
                                        <label
                                            key={section.id}
                                            className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-[12px] text-gray-600 hover:bg-white"
                                        >
                                            <input
                                                type="checkbox"
                                                checked={section.enabled}
                                                onChange={() => toggleAISection(section.id)}
                                                className="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary"
                                            />
                                            <span className="flex-1">{section.label || section.id}</span>
                                            {section.enabled && <span className="text-[10px] font-semibold text-primary">Incluida</span>}
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* API key settings */}
                    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
                        <button
                            type="button"
                            onClick={() => setAiKeyOpen(v => !v)}
                            className="flex w-full items-center justify-between px-4 py-3 hover:bg-surface-2 transition-colors"
                        >
                            <div className="flex items-center gap-2">
                                <Key size={13} className="text-gray-400" />
                                <span className="text-[11px] font-semibold text-gray-500">API key propia</span>
                                {loaded && apiKey && (
                                    <span className="rounded-full bg-success-soft px-1.5 py-px text-[9.5px] font-bold text-success">ACTIVA</span>
                                )}
                            </div>
                            {aiKeyOpen ? <ChevronUp size={13} className="text-gray-400" /> : <ChevronDown size={13} className="text-gray-400" />}
                        </button>
                        {aiKeyOpen && (
                            <div className="border-t border-gray-100 p-4 animate-in fade-in slide-in-from-top-1">
                                <AIKeyPanel />
                            </div>
                        )}
                    </div>

                    {/* Info note */}
                    <p className="text-[10.5px] text-gray-400 text-center px-2">
                        {loaded && apiKey
                            ? `Usando tu clave de ${provider === 'openai' ? 'OpenAI' : 'Anthropic'} para generar la propuesta.`
                            : 'Sin clave propia, se usará la API interna de Nougram.'}
                    </p>
                </aside>
            </div>
        </div>
    );
}
