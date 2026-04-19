'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle2, Loader2, AlertCircle, X, Sparkles } from 'lucide-react';
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
    project_name: string; client_name: string;
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
    if (!value) return '-';
    const n = Number(value);
    if (!Number.isFinite(n)) return value;
    try { return new Intl.NumberFormat('es-CO', { style: 'currency', currency: currency || 'COP', maximumFractionDigits: 0 }).format(n); }
    catch { return value; }
}
function decisionLabel(status: string) {
    const s = (status || '').toLowerCase();
    if (s === 'accepted') return 'Aceptada';
    if (s === 'rejected') return 'Rechazada';
    if (s === 'revision_requested') return 'Revisión solicitada';
    if (s === 'viewed') return 'Vista';
    if (s === 'sent') return 'Enviada';
    return 'Pendiente';
}

// ── Section wrapper ────────────────────────────────────────────────
function Section({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-gray-400">{label}</div>
            {children}
        </section>
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

    return (
        <div className="min-h-screen bg-[#EFE9DF]">
            {/* Top bar */}
            <div className="sticky top-0 z-20 flex items-center justify-between border-b border-gray-700/30 bg-gray-900 px-5 py-2.5">
                <div className="flex items-center gap-2 text-[11.5px] text-white/70">
                    <div className="flex h-5 w-5 items-center justify-center rounded-md bg-primary text-white text-[10px] font-bold">N</div>
                    <span>Propuesta comercial · Enlace seguro</span>
                </div>
                {portalData && (
                    <div className="text-[11px] text-white/50">
                        Válida hasta {new Date(portalData.access_expires_at).toLocaleDateString('es', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </div>
                )}
            </div>

            <div className="mx-auto w-full max-w-2xl px-4 py-10 space-y-4">

                {/* Access gate */}
                {!sessionToken && !loadingPortal && (
                    <div className="rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">
                        <div className="mb-1 flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-900 text-white font-bold text-lg">N</div>
                        <h1 className="mt-4 text-[22px] font-semibold text-gray-900">Accede a tu propuesta</h1>
                        <p className="mt-1 text-[13.5px] text-gray-500">Usa la clave enviada por correo para abrirla.</p>
                        <form onSubmit={onVerify} className="mt-5 space-y-3">
                            <Input
                                value={accessCode}
                                onChange={e => setAccessCode(e.target.value)}
                                placeholder="Ej: NGRM-7X2K"
                                autoComplete="one-time-code"
                                disabled={verifying}
                                className="h-10 bg-white font-mono tracking-widest text-gray-800"
                                required
                            />
                            <Button type="submit" disabled={verifying || !apiBase} className="w-full">
                                {verifying ? <><Loader2 size={14} className="mr-2 animate-spin" /> Validando…</> : 'Ver propuesta'}
                            </Button>
                        </form>
                        {error && <p className="mt-3 rounded-lg bg-critical-soft px-3 py-2 text-[12.5px] text-critical">{error}</p>}
                    </div>
                )}

                {loadingPortal && (
                    <div className="flex items-center justify-center rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                        <Loader2 size={18} className="animate-spin text-gray-400 mr-2" />
                        <span className="text-[13px] text-gray-500">Cargando propuesta…</span>
                    </div>
                )}

                {portalData && !loadingPortal && (
                    <>
                        {/* Hero */}
                        <div className="rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">
                            <div className="mb-3 flex items-center gap-2">
                                <span className="font-mono text-[10px] font-semibold uppercase tracking-widest text-primary">Propuesta comercial</span>
                                <span className="h-1 w-1 rounded-full bg-gray-300" />
                                <span className="text-[11px] text-gray-400">Para {portalData.client_name}</span>
                            </div>
                            <h1 className="text-[34px] font-bold leading-tight tracking-tight text-gray-900">
                                {portalData.proposal_title}
                            </h1>
                            <p className="mt-2 max-w-[540px] text-[14px] leading-relaxed text-gray-500">
                                {description || 'Una propuesta diseñada para acompañarte en el siguiente paso de tu negocio.'}
                            </p>
                        </div>

                        {/* Key metrics */}
                        <div className="grid grid-cols-3 gap-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                            {[
                                { label: 'Inversión total', value: totalFormatted },
                                { label: 'Versión', value: portalData.quote_version ? `V${portalData.quote_version}` : '—' },
                                { label: 'Validez', value: '30 días' },
                            ].map(s => (
                                <div key={s.label}>
                                    <div className="text-[10.5px] font-semibold uppercase tracking-wide text-gray-400">{s.label}</div>
                                    <div className="mt-1 text-[20px] font-semibold tabular-nums text-gray-900 tracking-tight">{s.value}</div>
                                </div>
                            ))}
                        </div>

                        {/* Proposal content */}
                        {(executiveSummary || objectives.length > 0 || deliverables.length > 0 || scope || timeline || conditions || freeText) && (
                            <Section label="01 — Detalle de la propuesta">
                                {executiveSummary && (
                                    <article className="mb-4 rounded-xl border border-orange-100 bg-primary-soft p-4">
                                        <h4 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-primary">Resumen ejecutivo</h4>
                                        <p className="whitespace-pre-line text-[13.5px] leading-relaxed text-gray-800">{executiveSummary}</p>
                                    </article>
                                )}
                                {objectives.length > 0 && (
                                    <article className="mb-4 rounded-xl border border-gray-100 p-4">
                                        <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-gray-500">Objetivos</h4>
                                        <ul className="space-y-1.5">
                                            {objectives.map((o, i) => (
                                                <li key={i} className="flex items-start gap-2 text-[13.5px] text-gray-800">
                                                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                                                    {o}
                                                </li>
                                            ))}
                                        </ul>
                                    </article>
                                )}
                                {deliverables.length > 0 && (
                                    <article className="mb-4 rounded-xl border border-gray-100 p-4">
                                        <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-gray-500">Entregables</h4>
                                        <div className="grid gap-2 sm:grid-cols-2">
                                            {deliverables.map((d, i) => (
                                                <div key={i} className="rounded-lg border border-gray-100 bg-surface-2 p-3">
                                                    <div className="text-[13px] font-medium text-gray-900">{d.name}</div>
                                                    {d.status && <div className="mt-0.5 text-[11px] uppercase text-gray-400">{d.status}</div>}
                                                </div>
                                            ))}
                                        </div>
                                    </article>
                                )}
                                <div className="grid gap-3 sm:grid-cols-2">
                                    {[
                                        { label: 'Alcance', content: scope },
                                        { label: 'Cronograma', content: timeline },
                                        { label: 'Condiciones comerciales', content: conditions },
                                        { label: 'Información adicional', content: freeText },
                                    ].filter(s => s.content).map(s => (
                                        <article key={s.label} className="rounded-xl border border-gray-100 p-4">
                                            <h4 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-gray-500">{s.label}</h4>
                                            <p className="text-[13.5px] leading-relaxed text-gray-800">{s.content}</p>
                                        </article>
                                    ))}
                                </div>
                            </Section>
                        )}

                        {/* Investment */}
                        <Section label="02 — Inversión">
                            <div className="flex items-baseline justify-between">
                                <div>
                                    <div className="text-[13px] text-gray-500">Total a facturar</div>
                                    <div className="text-[11px] text-gray-400">Incluye impuestos</div>
                                </div>
                                <div className="text-[30px] font-bold tabular-nums text-gray-900 tracking-tight">{totalFormatted}</div>
                            </div>
                        </Section>

                        {/* Decision area */}
                        <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
                            {hasDecision ? (
                                <div className="text-center py-4">
                                    <div className={cn(
                                        'mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full',
                                        decisionStatus === 'accepted' ? 'bg-success-soft text-success'
                                        : decisionStatus === 'rejected' ? 'bg-critical-soft text-critical'
                                        : 'bg-warning-soft text-warning'
                                    )}>
                                        {decisionStatus === 'accepted' ? <CheckCircle2 size={24} /> : decisionStatus === 'rejected' ? <X size={22} /> : <Sparkles size={22} />}
                                    </div>
                                    <div className="text-[19px] font-semibold text-gray-900">
                                        {decisionStatus === 'accepted' ? '¡Propuesta aceptada!' : decisionStatus === 'rejected' ? 'Propuesta rechazada' : 'Solicitud enviada'}
                                    </div>
                                    <div className="mt-1.5 text-[13px] text-gray-500">{decisionLabel(decisionStatus)}</div>
                                </div>
                            ) : showModify ? (
                                <div>
                                    <div className="mb-1 text-[14px] font-semibold text-gray-900">¿Qué te gustaría ajustar?</div>
                                    <div className="mb-3 text-[12.5px] text-gray-500">Cuéntanos los cambios y te enviamos una versión ajustada.</div>
                                    <textarea
                                        value={decisionComment}
                                        onChange={e => setDecisionComment(e.target.value)}
                                        placeholder="Ej: Reducir alcance del diseño, extender el plazo…"
                                        rows={4}
                                        className="w-full resize-y rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-[13.5px] text-gray-900 placeholder:text-gray-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                                    />
                                    <div className="mt-3 flex justify-end gap-2">
                                        <Button variant="ghost" onClick={() => setShowModify(false)}>Cancelar</Button>
                                        <Button onClick={() => void onDecision('revision_requested')} disabled={submittingDecision || !decisionComment.trim()}>
                                            {submittingDecision ? <Loader2 size={13} className="animate-spin mr-1" /> : null}
                                            Enviar solicitud
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <div>
                                    <div className="mb-4 text-center">
                                        <div className="text-[15px] font-semibold text-gray-900">¿Avanzamos con la propuesta?</div>
                                        <div className="mt-1 text-[12.5px] text-gray-400">Tu respuesta se comparte con el equipo en tiempo real.</div>
                                    </div>
                                    <div className="grid grid-cols-3 gap-3">
                                        <button
                                            type="button"
                                            onClick={() => setShowModify(true)}
                                            className="flex flex-col items-center rounded-xl border border-gray-200 bg-white p-4 text-center transition-colors hover:border-amber-300 hover:bg-warning-soft"
                                        >
                                            <Sparkles size={18} className="text-warning mb-2" />
                                            <div className="text-[13px] font-semibold text-gray-900">Solicitar cambios</div>
                                            <div className="mt-0.5 text-[11px] text-gray-400">Queremos ajustar algo</div>
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => void onDecision('rejected')}
                                            disabled={submittingDecision}
                                            className="flex flex-col items-center rounded-xl border border-gray-200 bg-white p-4 text-center transition-colors hover:border-red-300 hover:bg-critical-soft"
                                        >
                                            <X size={18} className="text-critical mb-2" />
                                            <div className="text-[13px] font-semibold text-gray-900">Rechazar</div>
                                            <div className="mt-0.5 text-[11px] text-gray-400">No por ahora</div>
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => void onDecision('accepted')}
                                            disabled={submittingDecision}
                                            className="flex flex-col items-center rounded-xl bg-primary p-4 text-center text-white transition-opacity hover:opacity-90"
                                        >
                                            <CheckCircle2 size={18} className="mb-2" strokeWidth={2.5} />
                                            <div className="text-[13px] font-semibold">Aceptar propuesta</div>
                                            <div className="mt-0.5 text-[11px] opacity-80">Listos para empezar</div>
                                        </button>
                                    </div>
                                </div>
                            )}
                        </section>
                    </>
                )}

                {error && (
                    <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-critical-soft px-4 py-3 text-[13px] text-critical">
                        <AlertCircle size={14} className="mt-0.5 shrink-0" />
                        {error}
                    </div>
                )}
                {success && (
                    <div className="flex items-start gap-2.5 rounded-xl border border-green-200 bg-success-soft px-4 py-3 text-[13px] text-success">
                        <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                        {success}
                    </div>
                )}

                <footer className="pb-2 text-center text-[11.5px] text-gray-400">
                    Enviado y gestionado con <span className="font-semibold text-gray-700">Nougram</span>
                </footer>
            </div>

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
