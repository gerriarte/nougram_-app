
import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Toggle } from '@/components/ui/Toggle';
import { ArrowLeft, Send, Sparkles, Save, Link as LinkIcon, Copy, LayoutDashboard, Check, FileText, Eye } from 'lucide-react';
import { Quote } from '@/components/dashboard/QuoteCard';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';

export interface QuoteSendPayload {
    to: string;
    subject: string;
    message: string;
    includePdf: boolean;
    trackingOpen: boolean;
    proposalId?: number;
    useCustomAccessCode?: boolean;
    accessCode?: string;
}

type ActionResult = { ok: boolean; message: string };
type AccessLinkResult = {
    ok: boolean; message: string;
    publicUrl?: string; accessCode?: string; accessExpiresAt?: string;
};
type ProposalBranding = {
    brandColor?: string;
    logoUrl?: string;
    coverImageUrl?: string;
};

interface QuoteSendViewProps {
    quote: Quote;
    initialToEmail?: string;
    initialProposalTitle?: string;
    initialProposalText?: string;
    initialProposalBranding?: ProposalBranding;
    proposalVersion?: number;
    initialProposalId?: number;
    onSend: (data: QuoteSendPayload) => Promise<ActionResult>;
    onGenerateAccessLink: (data: { proposalId?: number; useCustomAccessCode?: boolean; accessCode?: string; message?: string }) => Promise<AccessLinkResult>;
    onSaveProposal: (payload: { title: string; text: string }) => Promise<{ proposalId?: number; message: string }>;
    onGenerateProposalAI: () => Promise<{ title: string; text: string; version?: number; message: string } | null>;
    onOpenStructuredBuilder?: () => void;
    onGoToDashboard?: () => void;
    onCancel: () => void;
}

// ── Choice card ────────────────────────────────────────────────────
function ChoiceCard({
    icon: Icon, title, subtitle, bullets, active, accent, onClick,
}: {
    icon: React.ElementType; title: string; subtitle: string;
    bullets: string[]; active: boolean; accent?: boolean; onClick: () => void;
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={cn(
                'flex-1 min-w-0 rounded-2xl border p-5 text-left transition-all shadow-sm',
                active
                    ? accent ? 'border-primary bg-primary-soft shadow' : 'border-gray-900 bg-white shadow'
                    : 'border-gray-200 bg-white hover:border-gray-300'
            )}
        >
            <div className="mb-3 flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                    <div className={cn(
                        'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl',
                        accent ? 'bg-primary text-white' : 'bg-gray-900 text-white'
                    )}>
                        <Icon size={18} strokeWidth={2} />
                    </div>
                    <div>
                        <div className="text-[14.5px] font-semibold text-gray-900">{title}</div>
                        <div className="mt-0.5 text-[12px] text-gray-500">{subtitle}</div>
                    </div>
                </div>
                <div className={cn(
                    'mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full border transition-colors',
                    active
                        ? accent ? 'border-primary bg-primary' : 'border-gray-900 bg-gray-900'
                        : 'border-gray-300'
                )}>
                    {active && <Check size={9} strokeWidth={3} className="text-white" />}
                </div>
            </div>
            <ul className="space-y-1.5">
                {bullets.map((b, i) => (
                    <li key={i} className="flex items-start gap-2 text-[12.5px] text-gray-600">
                        <Check size={11} strokeWidth={2.5} className={cn('mt-0.5 shrink-0', accent ? 'text-primary' : 'text-gray-400')} />
                        {b}
                    </li>
                ))}
            </ul>
        </button>
    );
}

// ── Email preview ──────────────────────────────────────────────────
function EmailPreview({
    to, subject, message, projectName, version, total, currency, mode, branding,
}: {
    to: string; subject: string; message: string;
    projectName: string; version: string | number; total: number; currency: string; mode: 'standard' | 'ai';
    branding?: ProposalBranding;
}) {
    const firstName = to.split('@')[0] || 'cliente';
    const brandColor = branding?.brandColor && /^#[0-9a-fA-F]{6}$/.test(branding.brandColor)
        ? branding.brandColor
        : '#D97757';
    return (
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow">
            {branding?.coverImageUrl && (
                <div
                    className="h-20 bg-cover bg-center"
                    style={{ backgroundImage: `linear-gradient(135deg, ${brandColor}55, rgba(17,24,39,0.25)), url(${branding.coverImageUrl})` }}
                />
            )}
            {/* Browser dots */}
            <div className="flex items-center gap-1.5 border-b border-gray-100 bg-surface-2 px-4 py-2.5">
                {['#ff5f57', '#febc2e', '#28c840'].map(c => (
                    <div key={c} className="h-2.5 w-2.5 rounded-full" style={{ background: c }} />
                ))}
                <div className="flex-1 text-center font-mono text-[10.5px] text-gray-400">mail.cliente.com</div>
            </div>
            {/* Headers */}
            <div className="grid grid-cols-[44px_1fr] gap-y-1 border-b border-gray-100 px-5 py-3.5 text-[11.5px]">
                <span className="text-gray-400">De:</span>
                <span className="text-gray-700">Nougram &lt;hola@nougram.co&gt;</span>
                <span className="text-gray-400">Para:</span>
                <span className="text-gray-700">{to || 'cliente@email.com'}</span>
                <span className="text-gray-400">Asunto:</span>
                <span className="font-semibold text-gray-800">{subject || '—'}</span>
            </div>
            {/* Body */}
            <div className="space-y-3 px-5 py-4 text-[13px] leading-relaxed text-gray-700">
                <div>Hola {firstName},</div>
                {message ? (
                    <div className="whitespace-pre-wrap text-gray-700">{message}</div>
                ) : (
                    <div className="italic text-gray-400">Tu mensaje personalizado aparecerá aquí.</div>
                )}
                <div>
                    {mode === 'ai'
                        ? <>Adjunto encontrarás una propuesta comercial personalizada para el proyecto <b>{projectName}</b>, generada con base en los objetivos compartidos.</>
                        : <>Adjunto encontrarás la cotización para el proyecto <b>{projectName}</b>.</>
                    }
                </div>
                {/* Proposal card */}
                <div className="rounded-xl border border-gray-100 bg-surface-2 p-3.5 mt-2">
                    <div className="flex items-center gap-2">
                        {branding?.logoUrl && (
                            <span
                                className="h-5 w-5 rounded bg-contain bg-center bg-no-repeat"
                                style={{ backgroundImage: `url(${branding.logoUrl})` }}
                            />
                        )}
                        <div className="text-[13px] font-semibold text-gray-900">{projectName}</div>
                    </div>
                    <div className="mt-0.5 text-[10.5px] text-gray-400">V{version} · Válida por 30 días</div>
                    <div className="mt-2 text-[22px] font-bold tabular-nums text-gray-900 tracking-tight">
                        {formatCurrency(total, currency)}
                    </div>
                    <div className="mt-2.5 w-full rounded-lg py-1.5 text-center text-[12px] font-semibold text-white" style={{ backgroundColor: brandColor }}>
                        Ver Propuesta Online →
                    </div>
                </div>
                <div className="text-[10.5px] text-gray-400">Enviado con Nougram · Trazabilidad activada</div>
            </div>
        </div>
    );
}

// ── Main component ─────────────────────────────────────────────────
export function QuoteSendView({
    quote, initialToEmail, initialProposalTitle, initialProposalText,
    initialProposalBranding, proposalVersion, initialProposalId,
    onSend, onGenerateAccessLink, onSaveProposal, onGenerateProposalAI,
    onOpenStructuredBuilder, onGoToDashboard, onCancel,
}: QuoteSendViewProps) {
    const [mode, setMode] = useState<'standard' | 'ai'>('standard');
    const [to, setTo] = useState(initialToEmail || '');
    const [subject, setSubject] = useState(`Cotización para ${quote.project} - ${quote.version}`);
    const [message, setMessage] = useState('');
    const [proposalTitle, setProposalTitle] = useState(initialProposalTitle || `Propuesta para ${quote.project}`);
    const [proposalText, setProposalText] = useState(initialProposalText || '');
    const [currentProposalVersion, setCurrentProposalVersion] = useState<number | undefined>(proposalVersion);
    const [proposalId, setProposalId] = useState<number | undefined>(initialProposalId);
    const [includePdf, setIncludePdf] = useState(true);
    const [trackingOpen, setTrackingOpen] = useState(true);
    const [useCustomAccessCode, setUseCustomAccessCode] = useState(false);
    const [accessCode, setAccessCode] = useState('');
    const [generatedAccess, setGeneratedAccess] = useState<{ publicUrl: string; accessCode: string; accessExpiresAt?: string } | null>(null);

    const [isSending, setIsSending] = useState(false);
    const [isSavingProposal, setIsSavingProposal] = useState(false);
    const [isGeneratingProposal, setIsGeneratingProposal] = useState(false);
    const [isGeneratingAccessLink, setIsGeneratingAccessLink] = useState(false);
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const setMsg = (type: 'success' | 'error', text: string) => setFeedback({ type, text });

    const handleSend = async () => {
        if (!to.trim()) { setMsg('error', 'Ingresa el correo del destinatario.'); return; }
        if (useCustomAccessCode) {
            const c = accessCode.trim();
            if (c.length < 4 || c.length > 16) { setMsg('error', 'La clave debe tener entre 4 y 16 caracteres.'); return; }
        }
        setIsSending(true);
        try {
            const result = await onSend({ to, subject, message, includePdf, trackingOpen, proposalId, useCustomAccessCode, accessCode: useCustomAccessCode ? accessCode.trim() : undefined });
            setMsg(result.ok ? 'success' : 'error', result.message);
        } catch (e) { setMsg('error', e instanceof Error ? e.message : 'No se pudo enviar.'); }
        finally { setIsSending(false); }
    };

    const handleSaveProposal = async () => {
        setIsSavingProposal(true);
        try {
            const result = await onSaveProposal({ title: proposalTitle, text: proposalText });
            if (result.proposalId) setProposalId(result.proposalId);
            setMsg('success', result.message);
        } catch (e) { setMsg('error', e instanceof Error ? e.message : 'No se pudo guardar.'); }
        finally { setIsSavingProposal(false); }
    };

    const handleGenerateProposal = async () => {
        setIsGeneratingProposal(true);
        try {
            const generated = await onGenerateProposalAI();
            if (generated) {
                setProposalTitle(generated.title);
                setProposalText(generated.text);
                setCurrentProposalVersion(generated.version);
                setMsg('success', generated.message);
            }
        } catch (e) { setMsg('error', e instanceof Error ? e.message : 'No se pudo generar.'); }
        finally { setIsGeneratingProposal(false); }
    };

    const handleGenerateAccessLink = async () => {
        if (useCustomAccessCode) {
            const c = accessCode.trim();
            if (c.length < 4 || c.length > 16) { setMsg('error', 'La clave debe tener entre 4 y 16 caracteres.'); return; }
        }
        setIsGeneratingAccessLink(true);
        try {
            const result = await onGenerateAccessLink({ proposalId, useCustomAccessCode, accessCode: useCustomAccessCode ? accessCode.trim() : undefined, message });
            setMsg(result.ok ? 'success' : 'error', result.message);
            if (result.ok && result.publicUrl && result.accessCode) {
                setGeneratedAccess({ publicUrl: result.publicUrl, accessCode: result.accessCode, accessExpiresAt: result.accessExpiresAt });
            }
        } catch (e) { setMsg('error', e instanceof Error ? e.message : 'No se pudo generar el acceso.'); }
        finally { setIsGeneratingAccessLink(false); }
    };

    const copyToClipboard = async (value: string, label: string) => {
        try { await navigator.clipboard.writeText(value); setMsg('success', `${label} copiado.`); }
        catch { setMsg('error', `No se pudo copiar.`); }
    };

    const total = Number(quote.totalWithTaxes || 0);

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* ── Page header ── */}
            <div className="border-b border-gray-100 bg-white px-6 py-4 lg:px-10">
                <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <button type="button" onClick={onCancel} className="flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-white hover:bg-surface-2 transition-colors">
                            <ArrowLeft size={16} />
                        </button>
                        <div>
                            <div className="text-[10px] font-semibold uppercase tracking-wider text-primary">Paso 3 de 3</div>
                            <h1 className="text-[18px] font-semibold text-gray-900">Envío de propuesta</h1>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="hidden items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 sm:flex">
                            <span className="text-[11.5px] text-gray-400">Total</span>
                            <span className="text-[15px] font-semibold tabular-nums text-gray-900">
                                {formatCurrency(total, quote.currency)}
                            </span>
                        </div>
                        {onGoToDashboard && (
                            <Button variant="ghost" size="sm" onClick={onGoToDashboard} className="gap-1.5">
                                <LayoutDashboard size={14} /> Dashboard
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-6 lg:px-10">
                {/* Feedback */}
                {feedback && (
                    <div className={cn(
                        'mb-4 rounded-xl border px-4 py-3 text-[13px]',
                        feedback.type === 'success' ? 'border-green-200 bg-success-soft text-green-800' : 'border-red-200 bg-critical-soft text-red-800'
                    )}>
                        {feedback.text}
                    </div>
                )}

                {/* ── Choice cards ── */}
                <div className="mb-5">
                    <div className="mb-2.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">Modalidad de entrega</div>
                    <div className="flex gap-3">
                        <ChoiceCard
                            icon={FileText}
                            title="Plantilla estándar"
                            subtitle="Lista para enviar · Rápido y directo"
                            bullets={['Detalle automático de ítems y valores', 'El cliente acepta, rechaza o solicita cambios', 'Sin configuración adicional']}
                            active={mode === 'standard'}
                            onClick={() => setMode('standard')}
                        />
                        <ChoiceCard
                            icon={Sparkles}
                            title="Propuesta con IA"
                            subtitle="Guiada · Narrativa profesional a medida"
                            bullets={['La IA redacta una presentación personalizada', 'Mejor conversión en proyectos estratégicos', 'Incluye objetivos, alcance y entregables']}
                            active={mode === 'ai'}
                            accent
                            onClick={() => setMode('ai')}
                        />
                    </div>
                </div>

                {/* ── Two-column layout ── */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_400px]">
                    {/* LEFT: Form */}
                    <div className="space-y-4">
                        {/* Email section */}
                        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                            <div className="mb-4">
                                <div className="text-[14.5px] font-semibold text-gray-900">Correo al cliente</div>
                                <div className="text-[11.5px] text-gray-400">El cliente recibirá este mensaje en su bandeja.</div>
                            </div>
                            <div className="space-y-3">
                                <div className="space-y-1">
                                    <label className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">Para</label>
                                    <Input
                                        value={to}
                                        onChange={e => setTo(e.target.value)}
                                        placeholder="cliente@empresa.com"
                                        className="h-9 bg-white"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">Asunto</label>
                                    <Input value={subject} onChange={e => setSubject(e.target.value)} className="h-9 bg-white" />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">Mensaje personalizado <span className="font-normal normal-case">· Opcional</span></label>
                                    <textarea
                                        value={message}
                                        onChange={e => setMessage(e.target.value)}
                                        placeholder="Escribe un mensaje breve al cliente…"
                                        rows={3}
                                        className="flex min-h-[80px] w-full resize-y rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Proposal section */}
                        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                            <div className="mb-4 flex items-start justify-between">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <div className="text-[14.5px] font-semibold text-gray-900">
                                            {mode === 'ai' ? 'Propuesta con IA' : 'Propuesta comercial'}
                                        </div>
                                        {mode === 'ai' && (
                                            <span className="rounded-full bg-primary-soft px-2 py-px text-[9.5px] font-semibold uppercase tracking-wide text-primary">IA</span>
                                        )}
                                        {currentProposalVersion && (
                                            <span className="text-[11px] text-gray-400">V{currentProposalVersion}</span>
                                        )}
                                    </div>
                                    <div className="text-[11.5px] text-gray-400">
                                        {mode === 'ai' ? 'La IA redacta y diseña la propuesta según tus objetivos.' : 'Título y descripción que verá el cliente.'}
                                    </div>
                                </div>
                                <div className="flex shrink-0 gap-2">
                                    {onOpenStructuredBuilder && (
                                        <Button variant="outline" size="sm" onClick={onOpenStructuredBuilder} className="text-xs">
                                            Estructurada
                                        </Button>
                                    )}
                                    {mode === 'ai' && (
                                        <Button variant="outline" size="sm" onClick={handleGenerateProposal} disabled={isGeneratingProposal} className="gap-1.5 text-xs">
                                            <Sparkles size={12} />
                                            {isGeneratingProposal ? 'Generando…' : 'Generar'}
                                        </Button>
                                    )}
                                    <Button variant="outline" size="sm" onClick={handleSaveProposal} disabled={isSavingProposal} className="gap-1.5 text-xs">
                                        <Save size={12} />
                                        {isSavingProposal ? 'Guardando…' : 'Guardar'}
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <div className="space-y-1">
                                    <label className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">Título de la propuesta</label>
                                    <Input value={proposalTitle} onChange={e => setProposalTitle(e.target.value)} className="h-9 bg-white" />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                                        {mode === 'ai' ? 'Brief para la IA' : 'Descripción'}
                                        <span className="ml-1.5 font-normal normal-case text-gray-400">
                                            {mode === 'ai' ? '· Objetivos, tono, entregables' : '· Contexto y entregables'}
                                        </span>
                                    </label>
                                    <textarea
                                        value={proposalText}
                                        onChange={e => setProposalText(e.target.value)}
                                        placeholder={mode === 'ai' ? 'Ej: Tono profesional y cercano. Enfatizar ROI. Incluir caso de estudio…' : 'Describe alcance, objetivos y entregables…'}
                                        rows={5}
                                        className="flex min-h-[100px] w-full resize-y rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                                    />
                                </div>
                                {proposalId && proposalText && (
                                    <div className="flex items-center gap-1.5 text-[11.5px] font-medium text-success">
                                        <Check size={12} strokeWidth={2.5} /> Propuesta guardada · lista para enviar
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Attachments + Options */}
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                            {/* Attachments */}
                            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                                <div className="mb-3 text-[13px] font-semibold text-gray-800">Adjuntos</div>
                                <label className={cn(
                                    'flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 transition-colors',
                                    includePdf ? 'border-gray-200 bg-white shadow-sm' : 'border-transparent bg-surface-2 opacity-60'
                                )}>
                                    <input type="checkbox" checked={includePdf} onChange={e => setIncludePdf(e.target.checked)} className="h-3.5 w-3.5 rounded border-gray-300 text-primary" />
                                    <div className="min-w-0 flex-1">
                                        <div className="truncate text-[12px] font-medium text-gray-700">{`Cotización_${quote.project}_v${quote.version}.pdf`}</div>
                                        <div className="text-[10.5px] text-gray-400">PDF</div>
                                    </div>
                                </label>
                            </div>

                            {/* Options */}
                            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm space-y-3">
                                <div className="text-[13px] font-semibold text-gray-800">Opciones de acceso</div>
                                <div className="flex items-start gap-3">
                                    <Toggle checked={useCustomAccessCode} onChange={setUseCustomAccessCode} />
                                    <div>
                                        <div className="text-[12.5px] font-medium text-gray-700">Clave temporal manual</div>
                                        <div className="text-[11px] text-gray-400">Si no la activas, la generamos automáticamente.</div>
                                    </div>
                                </div>
                                {useCustomAccessCode && (
                                    <Input
                                        value={accessCode}
                                        onChange={e => setAccessCode(e.target.value.toUpperCase())}
                                        placeholder="Ej: ABRA2026"
                                        maxLength={16}
                                        className="h-9 bg-white font-mono tracking-widest"
                                    />
                                )}
                                <div className="border-t border-gray-100 pt-2 flex items-start gap-3">
                                    <Toggle checked={trackingOpen} onChange={setTrackingOpen} />
                                    <div>
                                        <div className="flex items-center gap-1.5 text-[12.5px] font-medium text-gray-700">
                                            <Eye size={11} /> Pixel de seguimiento
                                            {trackingOpen && <span className="rounded-full bg-success-soft px-1.5 py-px text-[9.5px] font-semibold text-success">ON</span>}
                                        </div>
                                        <div className="text-[11px] text-gray-400">Notificación cuando el cliente abra el correo.</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Generated access display */}
                        {generatedAccess && (
                            <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 space-y-3">
                                <div className="flex items-center gap-2 text-[13px] font-semibold text-blue-900">
                                    <LinkIcon size={14} /> Acceso generado (sin envío de correo)
                                </div>
                                <div className="space-y-1">
                                    <div className="text-[10.5px] font-semibold uppercase tracking-wide text-blue-600">Link portal</div>
                                    <div className="flex gap-2">
                                        <Input value={generatedAccess.publicUrl} readOnly className="bg-white border-blue-200 text-[12px]" />
                                        <Button type="button" variant="outline" size="sm" onClick={() => void copyToClipboard(generatedAccess.publicUrl, 'Link')}>
                                            <Copy size={13} />
                                        </Button>
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <div className="text-[10.5px] font-semibold uppercase tracking-wide text-amber-600">Clave temporal</div>
                                    <div className="flex gap-2">
                                        <Input value={generatedAccess.accessCode} readOnly className="bg-amber-50 border-amber-200 font-mono text-amber-900 font-semibold text-[12px]" />
                                        <Button type="button" variant="outline" size="sm" onClick={() => void copyToClipboard(generatedAccess.accessCode, 'Clave')}>
                                            <Copy size={13} />
                                        </Button>
                                    </div>
                                    {generatedAccess.accessExpiresAt && (
                                        <div className="text-[10.5px] text-blue-600">Vigente hasta: {new Date(generatedAccess.accessExpiresAt).toLocaleString()}</div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* RIGHT: Sticky preview */}
                    <div className="sticky top-4 self-start space-y-2">
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 px-1">Vista previa del correo</div>
                        <EmailPreview
                            to={to} subject={subject} message={message}
                            projectName={quote.project} version={quote.version}
                            total={total} currency={quote.currency} mode={mode}
                            branding={initialProposalBranding}
                        />
                    </div>
                </div>
            </div>

            {/* ── Sticky footer ── */}
            <div className="sticky bottom-0 z-10 border-t border-gray-200 bg-white/90 backdrop-blur px-6 py-3 lg:px-10">
                <div className="mx-auto flex max-w-7xl items-center justify-between gap-3">
                    <div className="text-[12px] text-gray-400">
                        Modalidad: <span className="font-semibold text-gray-700">{mode === 'ai' ? 'Propuesta con IA' : 'Plantilla estándar'}</span>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="ghost" onClick={onCancel} className="text-[13px]">Volver</Button>
                        <Button
                            variant="outline"
                            onClick={handleGenerateAccessLink}
                            disabled={isGeneratingAccessLink}
                            className="gap-1.5 text-[13px]"
                        >
                            <LinkIcon size={13} />
                            {isGeneratingAccessLink ? 'Generando…' : 'Guardar acceso sin enviar'}
                        </Button>
                        <Button
                            onClick={handleSend}
                            disabled={isSending}
                            className="gap-1.5 bg-gray-900 text-white hover:bg-gray-800 text-[13px]"
                        >
                            <Send size={13} />
                            {isSending ? 'Enviando…' : 'Enviar propuesta'}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
