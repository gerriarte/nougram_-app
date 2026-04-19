'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle2, Loader2, AlertCircle, X, Sparkles, RefreshCw, Building2 } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import {
    Dialog, DialogContent, DialogDescription, DialogFooter,
    DialogHeader, DialogTitle,
} from '@/components/ui/Dialog';
import { cn } from '@/lib/utils';

// ── Types ─────────────────────────────────────────────────────────
type PortalVerifyResponse = { session_token: string; expires_at: string; proposal_status: string };
type PortalDataResponse = {
    proposal_id: number; proposal_title: string; proposal_body_json: Record<string, unknown>;
    project_name: string; client_name: string; organization_name?: string | null;
    quote_id?: number | null; quote_version?: number | null;
    quote_total_client_price?: string | null; quote_currency?: string | null;
    decision_status: string; decision_comment?: string | null; decided_at?: string | null;
    access_expires_at: string;
};
type DecisionType = 'accepted' | 'rejected' | 'revision_requested';
type ProposalBody = Record<string, unknown>;
type ProposalDeliverable = { name: string; status?: string };

const SESSION_STORAGE_PREFIX = 'nougram:proposal-portal:session:';

function getApiBase() { return (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/+$/, ''); }
function asString(v: unknown) { return typeof v === 'string' ? v.trim() : ''; }
function asStringArray(v: unknown): string[] {
    if (!Array.isArray(v)) return [];
    return v.filter((i): i is string => typeof i === 'string').map(s => s.trim()).filter(Boolean);
}
function asDeliverables(v: unknown): ProposalDeliverable[] {
    if (!Array.isArray(v)) return [];
    const out: ProposalDeliverable[] = [];
    for (const item of v) {
        if (typeof item === 'string' && item.trim()) { out.push({ name: item.trim() }); continue; }
        if (item && typeof item === 'object') {
            const r = item as Record<string, unknown>;
            const name = asString(r.name);
            if (name) out.push({ name, status: asString(r.status) || undefined });
        }
    }
    return out;
}
function formatMoney(value: string | null | undefined, currency: string | null | undefined) {
    if (!value) return '—';
    const n = Number(value);
    if (!Number.isFinite(n)) return value;
    try { return new Intl.NumberFormat('es-CO', { style: 'currency', currency: currency || 'COP', maximumFractionDigits: 0 }).format(n); }
    catch { return value; }
}

// ── Content section card ───────────────────────────────────────────
function ContentCard({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-[17px] font-semibold leading-snug tracking-tight text-gray-900">{title}</h2>
            {children}
        </div>
    );
}

// ── Main ──────────────────────────────────────────────────────────
export default function ClientProposalPortalPage() {
    const params = useParams<{ token: string }>();
    const token = params?.token || '';
    const apiBase = useMemo(() => getApiBase(), []);
    const sessionKey = `${SESSION_STORAGE_PREFIX}${token}`;

    const [accessCode, setAccessCode] = useState('');
    const [sessionToken, setSessionToken] = useState<string | null>(null);
    const [portalData, setPortalData] = useState<PortalDataResponse | null>(null);
    const [loadingPortal, setLoadingPortal] = useState(false);
    const [verifying, setVerifying] = useState(false);
    const [submittingDecision, setSubmittingDecision] = useState(false);
    const [decisionComment, setDecisionComment] = useState('');
    const [showModify, setShowModify] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [decisionModalMessage, setDecisionModalMessage] = useState<string | null>(null);

    const fetchPortalData = async (tok: string) => {
        setLoadingPortal(true); setError(null);
        try {
            const res = await fetch(`${apiBase}/public/proposals/${token}`, { headers: { Authorization: `Bearer ${tok}` } });
            if (!res.ok) { const b = await res.json().catch(() => ({})); throw new Error((typeof b?.detail === 'string' && b.detail) || `Error ${res.status}`); }
            setPortalData(await res.json() as PortalDataResponse);
        } catch (e) {
            setSessionToken(null); sessionStorage.removeItem(sessionKey); setPortalData(null);
            setError(e instanceof Error ? e.message : 'No se pudo cargar la propuesta.');
        } finally { setLoadingPortal(false); }
    };

    useEffect(() => {
        if (!token) return;
        const stored = sessionStorage.getItem(sessionKey);
        if (stored) { setSessionToken(stored); void fetchPortalData(stored); }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sessionKey, token]);

    const onVerify = async (e: React.FormEvent) => {
        e.preventDefault(); setError(null); setSuccess(null);
        if (!apiBase) { setError('NEXT_PUBLIC_API_URL no está configurada.'); return; }
        if (!accessCode.trim()) { setError('Ingresa la clave temporal.'); return; }
        setVerifying(true);
        try {
            const res = await fetch(`${apiBase}/public/proposals/${token}/verify`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ access_code: accessCode.trim() }) });
            if (!res.ok) { const b = await res.json().catch(() => ({})); throw new Error((typeof b?.detail === 'string' && b.detail) || `Error ${res.status}`); }
            const data = await res.json() as PortalVerifyResponse;
            setSessionToken(data.session_token);
            sessionStorage.setItem(sessionKey, data.session_token);
            setSuccess('Clave validada. Cargando propuesta...');
            await fetchPortalData(data.session_token);
        } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo validar la clave.'); }
        finally { setVerifying(false); }
    };

    const onDecision = async (decision: DecisionType) => {
        setError(null); setSuccess(null);
        if (!sessionToken) { setError('Debes validar tu clave antes de continuar.'); return; }
        setSubmittingDecision(true);
        try {
            const res = await fetch(`${apiBase}/public/proposals/${token}/decision`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${sessionToken}` },
                body: JSON.stringify({ decision, comment: decisionComment.trim() || null }),
            });
            if (!res.ok) { const b = await res.json().catch(() => ({})); throw new Error((typeof b?.detail === 'string' && b.detail) || `Error ${res.status}`); }
            setPortalData(await res.json() as PortalDataResponse);
            setSuccess('Tu respuesta fue registrada.');
            setShowModify(false);
            setDecisionModalMessage(
                decision === 'accepted' ? '¡Genial! Muy pronto nos pondremos en contacto para iniciar.'
                : decision === 'revision_requested' ? 'Ya notificamos al equipo para enviarte una versión ajustada.'
                : 'Lamentamos no poder avanzar. Quedamos atentos a futuras oportunidades.'
            );
        } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo registrar tu decisión.'); }
        finally { setSubmittingDecision(false); }
    };

    const body = (portalData?.proposal_body_json ?? {}) as ProposalBody;
    const executiveSummary = asString(body.executive_summary);
    const description = asString(body.description);
    const scope = asString(body.scope);
    const timeline = asString(body.timeline);
    const conditions = asString(body.conditions);
    const freeText = asString(body.free_text);
    const objectives = asStringArray(body.objectives);
    const deliverables = asDeliverables(body.deliverables);
    const totalFormatted = formatMoney(portalData?.quote_total_client_price, portalData?.quote_currency);
    const decisionStatus = (portalData?.decision_status || '').toLowerCase();
    const hasDecision = ['accepted', 'rejected', 'revision_requested'].includes(decisionStatus);
    const senderName = portalData?.organization_name || null;
    const validUntil = portalData ? new Date(portalData.access_expires_at).toLocaleDateString('es', { day: 'numeric', month: 'long', year: 'numeric' }) : null;

    return (
        <div className="min-h-screen bg-[#EFE9DF]">
            {/* ── Top bar ── */}
            <div className="sticky top-0 z-20 flex items-center justify-between border-b border-white/10 bg-gray-900 px-5 py-2.5">
                <div className="flex items-center gap-2 text-[11.5px] text-white/70">
                    <div className="flex h-5 w-5 items-center justify-center rounded-md bg-primary text-white text-[9.5px] font-bold">N</div>
                    <span className="font-medium text-white/90">Propuesta comercial</span>
                    <span className="hidden sm:inline text-white/30">·</span>
                    <span className="hidden sm:inline text-white/40">Enlace seguro</span>
                </div>
                {portalData && validUntil && (
                    <div className="text-[11px] text-white/40">
                        Válida hasta <span className="text-white/60">{validUntil}</span>
                    </div>
                )}
            </div>

            {/* ── Access gate ── */}
            {!sessionToken && !loadingPortal && (
                <div className="flex min-h-[calc(100vh-44px)] items-center justify-center px-4 py-12">
                    <div className="w-full max-w-sm rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">
                        <div className="mb-1 flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-900 text-white font-bold text-lg">N</div>
                        <h1 className="mt-4 text-[22px] font-semibold tracking-tight text-gray-900">Accede a tu propuesta</h1>
                        <p className="mt-1 text-[13.5px] text-gray-500">Usa la clave enviada por correo para abrirla.</p>
                        <form onSubmit={onVerify} className="mt-6 space-y-3">
                            <Input
                                value={accessCode}
                                onChange={e => setAccessCode(e.target.value)}
                                placeholder="Ej: NGRM-7X2K"
                                autoComplete="one-time-code"
                                disabled={verifying}
                                className="h-11 bg-white font-mono tracking-widest text-gray-800"
                                required
                            />
                            <Button type="submit" disabled={verifying || !apiBase} className="w-full h-11">
                                {verifying ? <><Loader2 size={14} className="mr-2 animate-spin" /> Validando…</> : 'Ver propuesta'}
                            </Button>
                        </form>
                        {error && <p className="mt-3 rounded-lg bg-critical-soft px-3 py-2 text-[12.5px] text-critical">{error}</p>}
                        {success && (
                            <p className="mt-3 flex items-center gap-1.5 rounded-lg bg-success-soft px-3 py-2 text-[12.5px] text-success">
                                <CheckCircle2 size={13} /> {success}
                            </p>
                        )}
                    </div>
                </div>
            )}

            {loadingPortal && (
                <div className="flex min-h-[calc(100vh-44px)] items-center justify-center">
                    <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-white px-6 py-4 shadow-sm">
                        <Loader2 size={16} className="animate-spin text-gray-400" />
                        <span className="text-[13px] text-gray-500">Cargando propuesta…</span>
                    </div>
                </div>
            )}

            {/* ── Proposal content ── */}
            {portalData && !loadingPortal && (
                <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:py-12">

                    {/* Hero */}
                    <div className="mb-6 overflow-hidden rounded-3xl bg-white shadow-sm">
                        <div className="p-7 sm:p-10">
                            {/* Sender */}
                            {senderName ? (
                                <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-gray-200 bg-surface-2 px-3 py-1.5">
                                    <Building2 size={13} className="text-gray-500" />
                                    <span className="text-[12.5px] font-medium text-gray-700">{senderName}</span>
                                </div>
                            ) : (
                                <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-gray-200 bg-surface-2 px-3 py-1.5">
                                    <div className="flex h-4 w-4 items-center justify-center rounded-full bg-gray-900 text-[8px] font-bold text-white">N</div>
                                    <span className="text-[12.5px] font-medium text-gray-700">Enviado vía Nougram</span>
                                </div>
                            )}

                            <p className="mb-2 font-mono text-[10.5px] font-semibold uppercase tracking-widest text-primary">
                                Propuesta comercial
                            </p>
                            <h1 className="text-[28px] font-bold leading-tight tracking-tight text-gray-900 sm:text-[36px] lg:text-[42px]">
                                {portalData.proposal_title}
                            </h1>
                            <p className="mt-3 text-[15px] text-gray-500">
                                Preparada para <span className="font-semibold text-gray-800">{portalData.client_name}</span>
                            </p>
                            {description && (
                                <p className="mt-4 max-w-2xl text-[14.5px] leading-relaxed text-gray-600">
                                    {description}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Two-column: content + sidebar */}
                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_300px] lg:items-start">

                        {/* ── Main content ── */}
                        <div className="min-w-0 space-y-5">

                            {executiveSummary && (
                                <div className="rounded-2xl border border-primary/20 bg-primary-soft p-6">
                                    <p className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-primary">Resumen ejecutivo</p>
                                    <p className="text-[15px] leading-relaxed text-gray-800 whitespace-pre-line">{executiveSummary}</p>
                                </div>
                            )}

                            {objectives.length > 0 && (
                                <ContentCard title="Objetivos del proyecto">
                                    <ul className="space-y-3">
                                        {objectives.map((o, i) => (
                                            <li key={i} className="flex items-start gap-3">
                                                <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
                                                    {i + 1}
                                                </div>
                                                <span className="text-[14.5px] leading-relaxed text-gray-800">{o}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </ContentCard>
                            )}

                            {deliverables.length > 0 && (
                                <ContentCard title="Entregables">
                                    <div className="grid gap-2.5 sm:grid-cols-2">
                                        {deliverables.map((d, i) => (
                                            <div key={i} className="flex items-start gap-2.5 rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                                                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                                                <div>
                                                    <div className="text-[13.5px] font-medium text-gray-900">{d.name}</div>
                                                    {d.status && <div className="mt-0.5 text-[11px] uppercase tracking-wide text-gray-400">{d.status}</div>}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </ContentCard>
                            )}

                            {[
                                { key: 'scope', title: 'Alcance del proyecto', content: scope },
                                { key: 'timeline', title: 'Cronograma e hitos', content: timeline },
                                { key: 'conditions', title: 'Condiciones comerciales', content: conditions },
                                { key: 'free', title: 'Información adicional', content: freeText },
                            ].filter(s => s.content).map(s => (
                                <ContentCard key={s.key} title={s.title}>
                                    <p className="text-[14.5px] leading-relaxed text-gray-700 whitespace-pre-line">{s.content}</p>
                                </ContentCard>
                            ))}

                            {/* Modify form (mobile: shown inline below content) */}
                            {showModify && (
                                <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm lg:hidden">
                                    <ModifyForm
                                        comment={decisionComment}
                                        onChangeComment={setDecisionComment}
                                        onSubmit={() => void onDecision('revision_requested')}
                                        onCancel={() => setShowModify(false)}
                                        submitting={submittingDecision}
                                    />
                                </div>
                            )}
                        </div>

                        {/* ── Sidebar ── */}
                        <div className="lg:sticky lg:top-14 space-y-4">
                            {/* Investment card */}
                            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                                <p className="mb-1 font-mono text-[10px] font-semibold uppercase tracking-widest text-gray-400">Inversión total</p>
                                <div className="mb-1 text-[36px] font-bold tabular-nums leading-none tracking-tight text-gray-900">
                                    {totalFormatted}
                                </div>
                                <p className="text-[11.5px] text-gray-400">Incluye impuestos</p>

                                <div className="my-5 grid grid-cols-2 gap-2.5">
                                    <div className="rounded-xl bg-gray-50 px-3 py-2.5">
                                        <p className="text-[9.5px] font-semibold uppercase tracking-wider text-gray-400">Versión</p>
                                        <p className="mt-1 text-[14px] font-semibold text-gray-900">
                                            {portalData.quote_version ? `V${portalData.quote_version}` : 'V1'}
                                        </p>
                                    </div>
                                    <div className="rounded-xl bg-gray-50 px-3 py-2.5">
                                        <p className="text-[9.5px] font-semibold uppercase tracking-wider text-gray-400">Validez</p>
                                        <p className="mt-1 text-[14px] font-semibold text-gray-900">30 días</p>
                                    </div>
                                </div>

                                {/* Decision CTA */}
                                {hasDecision ? (
                                    <DecisionBadge status={decisionStatus} />
                                ) : showModify ? (
                                    <div className="hidden lg:block">
                                        <ModifyForm
                                            comment={decisionComment}
                                            onChangeComment={setDecisionComment}
                                            onSubmit={() => void onDecision('revision_requested')}
                                            onCancel={() => setShowModify(false)}
                                            submitting={submittingDecision}
                                        />
                                    </div>
                                ) : (
                                    <CTAButtons
                                        onAccept={() => void onDecision('accepted')}
                                        onModify={() => setShowModify(true)}
                                        onReject={() => void onDecision('rejected')}
                                        submitting={submittingDecision}
                                    />
                                )}
                            </div>

                            {/* Sender card */}
                            <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gray-900 text-white text-[13px] font-bold">N</div>
                                    <div className="min-w-0">
                                        <p className="truncate text-[13px] font-semibold text-gray-900">
                                            {senderName || 'Enviado vía Nougram'}
                                        </p>
                                        <p className="text-[11px] text-gray-400">Para {portalData.client_name}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Mobile CTA (below content, not sticky) */}
                    {!hasDecision && !showModify && (
                        <div className="mt-6 lg:hidden">
                            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                                <p className="mb-4 text-center text-[14px] font-semibold text-gray-900">¿Avanzamos con la propuesta?</p>
                                <CTAButtons
                                    onAccept={() => void onDecision('accepted')}
                                    onModify={() => setShowModify(true)}
                                    onReject={() => void onDecision('rejected')}
                                    submitting={submittingDecision}
                                />
                            </div>
                        </div>
                    )}

                    {hasDecision && (
                        <div className="mt-6 lg:hidden">
                            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm text-center">
                                <DecisionBadge status={decisionStatus} />
                            </div>
                        </div>
                    )}

                    {/* Feedback messages */}
                    {error && (
                        <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-red-200 bg-critical-soft px-4 py-3 text-[13px] text-critical">
                            <AlertCircle size={14} className="mt-0.5 shrink-0" />
                            {error}
                        </div>
                    )}

                    <footer className="mt-8 pb-2 text-center text-[11.5px] text-gray-400">
                        Enviado y gestionado con <span className="font-semibold text-gray-600">Nougram</span>
                    </footer>
                </div>
            )}

            <Dialog open={Boolean(decisionModalMessage)} onOpenChange={open => !open && setDecisionModalMessage(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Respuesta registrada</DialogTitle>
                        <DialogDescription>{decisionModalMessage}</DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button onClick={() => setDecisionModalMessage(null)}>Entendido</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

// ── Sub-components ─────────────────────────────────────────────────

function CTAButtons({ onAccept, onModify, onReject, submitting }: {
    onAccept: () => void; onModify: () => void; onReject: () => void; submitting: boolean;
}) {
    return (
        <div className="space-y-2.5">
            <button
                type="button"
                onClick={onAccept}
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-[13.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            >
                {submitting ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={15} strokeWidth={2.5} />}
                Aceptar propuesta
            </button>
            <button
                type="button"
                onClick={onModify}
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white py-2.5 text-[13px] font-medium text-gray-700 transition-colors hover:border-amber-300 hover:bg-warning-soft disabled:opacity-60"
            >
                <RefreshCw size={13} />
                Solicitar cambios
            </button>
            <button
                type="button"
                onClick={onReject}
                disabled={submitting}
                className="flex w-full items-center justify-center gap-1.5 rounded-xl py-2 text-[12.5px] font-medium text-gray-400 transition-colors hover:bg-critical-soft hover:text-critical disabled:opacity-60"
            >
                <X size={13} />
                Rechazar
            </button>
        </div>
    );
}

function ModifyForm({ comment, onChangeComment, onSubmit, onCancel, submitting }: {
    comment: string; onChangeComment: (v: string) => void;
    onSubmit: () => void; onCancel: () => void; submitting: boolean;
}) {
    return (
        <div className="space-y-3">
            <div>
                <p className="text-[13.5px] font-semibold text-gray-900">¿Qué te gustaría ajustar?</p>
                <p className="mt-0.5 text-[12px] text-gray-500">Cuéntanos los cambios y te enviamos una versión ajustada.</p>
            </div>
            <textarea
                value={comment}
                onChange={e => onChangeComment(e.target.value)}
                placeholder="Ej: Reducir alcance del diseño, extender el plazo…"
                rows={4}
                className="w-full resize-y rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-[13px] text-gray-900 placeholder:text-gray-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
            <div className="flex gap-2">
                <button type="button" onClick={onCancel}
                    className="flex-1 rounded-xl border border-gray-200 py-2.5 text-[12.5px] font-medium text-gray-600 hover:bg-surface-2">
                    Cancelar
                </button>
                <button
                    type="button"
                    onClick={onSubmit}
                    disabled={submitting || !comment.trim()}
                    className="flex-1 rounded-xl bg-gray-900 py-2.5 text-[12.5px] font-semibold text-white disabled:opacity-50 hover:bg-gray-700"
                >
                    {submitting ? <Loader2 size={13} className="mx-auto animate-spin" /> : 'Enviar solicitud'}
                </button>
            </div>
        </div>
    );
}

function DecisionBadge({ status }: { status: string }) {
    const isAccepted = status === 'accepted';
    const isRejected = status === 'rejected';
    return (
        <div className={cn(
            'flex items-center gap-3 rounded-xl px-4 py-3',
            isAccepted ? 'bg-success-soft text-success' : isRejected ? 'bg-critical-soft text-critical' : 'bg-warning-soft text-warning'
        )}>
            {isAccepted ? <CheckCircle2 size={18} strokeWidth={2.5} /> : isRejected ? <X size={18} /> : <Sparkles size={18} />}
            <div>
                <p className="text-[13px] font-semibold">
                    {isAccepted ? '¡Propuesta aceptada!' : isRejected ? 'Propuesta rechazada' : 'Solicitud de cambios enviada'}
                </p>
                <p className="text-[11.5px] opacity-80">
                    {isAccepted ? 'El equipo se pondrá en contacto pronto.' : isRejected ? 'Quedamos atentos a futuras oportunidades.' : 'El equipo revisará y enviará una versión ajustada.'}
                </p>
            </div>
        </div>
    );
}
