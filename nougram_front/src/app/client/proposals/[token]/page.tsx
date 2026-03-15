'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';

type PortalVerifyResponse = {
  session_token: string;
  expires_at: string;
  proposal_status: string;
};

type PortalDataResponse = {
  proposal_id: number;
  proposal_title: string;
  proposal_body_json: Record<string, unknown>;
  project_name: string;
  client_name: string;
  quote_id?: number | null;
  quote_version?: number | null;
  quote_total_client_price?: string | null;
  quote_currency?: string | null;
  decision_status: string;
  decision_comment?: string | null;
  decided_at?: string | null;
  access_expires_at: string;
};

type DecisionType = 'accepted' | 'rejected' | 'revision_requested';
type ProposalBody = Record<string, unknown>;
type ProposalDeliverable = { name: string; status?: string };

const SESSION_STORAGE_PREFIX = 'nougram:proposal-portal:session:';

function getApiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL || '';
  return base.replace(/\/+$/, '');
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is string => typeof item === 'string')
    .map((item) => item.trim())
    .filter(Boolean);
}

function asDeliverables(value: unknown): ProposalDeliverable[] {
  if (!Array.isArray(value)) return [];
  const normalized: ProposalDeliverable[] = [];
  for (const item of value) {
    if (typeof item === 'string' && item.trim()) {
      normalized.push({ name: item.trim() });
      continue;
    }
    if (item && typeof item === 'object') {
      const raw = item as Record<string, unknown>;
      const name = asString(raw.name);
      const status = asString(raw.status);
      if (name) normalized.push({ name, status: status || undefined });
    }
  }
  return normalized;
}

function formatMoney(value: string | null | undefined, currency: string | null | undefined): string {
  if (!value) return '-';
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return value;
  try {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: currency || 'COP',
      maximumFractionDigits: 0,
    }).format(parsed);
  } catch {
    return value;
  }
}

function decisionLabel(status: string): string {
  const normalized = (status || '').toLowerCase();
  if (normalized === 'accepted') return 'Aceptada';
  if (normalized === 'rejected') return 'Rechazada';
  if (normalized === 'revision_requested') return 'Revision solicitada';
  if (normalized === 'viewed') return 'Vista';
  if (normalized === 'sent') return 'Enviada';
  return 'Pendiente';
}

function decisionBadgeClass(status: string): string {
  const normalized = (status || '').toLowerCase();
  if (normalized === 'accepted') return 'bg-emerald-100 text-emerald-800';
  if (normalized === 'rejected') return 'bg-rose-100 text-rose-800';
  if (normalized === 'revision_requested') return 'bg-amber-100 text-amber-800';
  return 'bg-slate-100 text-slate-700';
}

export default function ClientProposalPortalPage() {
  const params = useParams<{ token: string }>();
  const token = params?.token || '';
  const apiBase = useMemo(() => getApiBase(), []);
  const sessionStorageKey = `${SESSION_STORAGE_PREFIX}${token}`;

  const [accessCode, setAccessCode] = useState('');
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [portalData, setPortalData] = useState<PortalDataResponse | null>(null);

  const [loadingPortal, setLoadingPortal] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [submittingDecision, setSubmittingDecision] = useState(false);

  const [decisionComment, setDecisionComment] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [decisionModalMessage, setDecisionModalMessage] = useState<string | null>(null);

  const canUseApi = Boolean(apiBase);

  const fetchPortalData = async (tokenValue: string) => {
    setLoadingPortal(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/public/proposals/${token}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${tokenValue}`,
        },
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const message =
          (typeof body?.detail === 'string' && body.detail) ||
          `Error ${response.status}: ${response.statusText}`;
        throw new Error(message);
      }

      const data = (await response.json()) as PortalDataResponse;
      setPortalData(data);
    } catch (requestError) {
      setSessionToken(null);
      sessionStorage.removeItem(sessionStorageKey);
      setPortalData(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No se pudo cargar la propuesta.',
      );
    } finally {
      setLoadingPortal(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    const storedToken = sessionStorage.getItem(sessionStorageKey);
    if (storedToken) {
      setSessionToken(storedToken);
      void fetchPortalData(storedToken);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionStorageKey, token]);

  const onVerifyAccessCode = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    if (!canUseApi) {
      setError('NEXT_PUBLIC_API_URL no esta configurada.');
      return;
    }
    if (!accessCode.trim()) {
      setError('Ingresa la clave temporal.');
      return;
    }

    setVerifying(true);
    try {
      const response = await fetch(`${apiBase}/public/proposals/${token}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ access_code: accessCode.trim() }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const message =
          (typeof body?.detail === 'string' && body.detail) ||
          `Error ${response.status}: ${response.statusText}`;
        throw new Error(message);
      }

      const data = (await response.json()) as PortalVerifyResponse;
      setSessionToken(data.session_token);
      sessionStorage.setItem(sessionStorageKey, data.session_token);
      setSuccess('Clave validada. Cargando propuesta...');
      await fetchPortalData(data.session_token);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No se pudo validar la clave temporal.',
      );
    } finally {
      setVerifying(false);
    }
  };

  const onSubmitDecision = async (decision: DecisionType) => {
    setError(null);
    setSuccess(null);
    if (!sessionToken) {
      setError('Debes validar tu clave temporal antes de continuar.');
      return;
    }

    setSubmittingDecision(true);
    try {
      const response = await fetch(`${apiBase}/public/proposals/${token}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${sessionToken}`,
        },
        body: JSON.stringify({
          decision,
          comment: decisionComment.trim() || null,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const message =
          (typeof body?.detail === 'string' && body.detail) ||
          `Error ${response.status}: ${response.statusText}`;
        throw new Error(message);
      }

      const updated = (await response.json()) as PortalDataResponse;
      setPortalData(updated);
      setSuccess('Tu respuesta fue registrada correctamente.');
      if (decision === 'accepted') {
        setDecisionModalMessage('Genial, muy pronto nos pondremos en contacto para iniciar');
      } else if (decision === 'revision_requested') {
        setDecisionModalMessage('Ya se informó para una revisión');
      } else {
        setDecisionModalMessage('Lamentamos saberlo, gracias');
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No se pudo registrar tu decision.',
      );
    } finally {
      setSubmittingDecision(false);
    }
  };

  const proposalBody = (portalData?.proposal_body_json ?? {}) as ProposalBody;
  const executiveSummary = asString(proposalBody.executive_summary);
  const description = asString(proposalBody.description);
  const scope = asString(proposalBody.scope);
  const timeline = asString(proposalBody.timeline);
  const conditions = asString(proposalBody.conditions);
  const freeText = asString(proposalBody.free_text);
  const objectives = asStringArray(proposalBody.objectives);
  const deliverables = asDeliverables(proposalBody.deliverables);
  const totalFormatted = formatMoney(portalData?.quote_total_client_price, portalData?.quote_currency);

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 via-background to-background py-10 px-4">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        <header className="rounded-3xl border border-orange-100 bg-white p-6 shadow-sm md:p-8">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-gray-900 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white">
            Nougram
          </div>
          <h1 className="text-2xl font-semibold text-gray-900 md:text-3xl">Tu propuesta comercial</h1>
          <p className="mt-2 max-w-2xl text-sm text-system-gray">
            Disenada para ayudarte a tomar una decision con claridad: valor del proyecto, alcance y
            siguientes pasos.
          </p>
        </header>

        {!sessionToken && (
          <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm md:p-8">
            <h2 className="text-lg font-semibold text-gray-900">Ingresa con clave temporal</h2>
            <p className="mt-1 text-sm text-system-gray">
              Usa la clave enviada por correo para abrir esta propuesta.
            </p>
            <form onSubmit={onVerifyAccessCode} className="mt-4 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="accessCode">Clave temporal</Label>
                <Input
                  id="accessCode"
                  value={accessCode}
                  onChange={(event) => setAccessCode(event.target.value)}
                  placeholder="Ej: 123456"
                  autoComplete="one-time-code"
                  disabled={verifying}
                  required
                />
              </div>
              <Button type="submit" disabled={verifying || !canUseApi}>
                {verifying ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Validando...
                  </>
                ) : (
                  'Ver propuesta'
                )}
              </Button>
            </form>
          </section>
        )}

        {loadingPortal && (
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2 text-sm text-system-gray">
              <Loader2 className="h-4 w-4 animate-spin" />
              Cargando informacion...
            </div>
          </section>
        )}

        {portalData && !loadingPortal && (
          <>
            <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm md:p-8">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-semibold text-gray-900 md:text-2xl">{portalData.proposal_title}</h2>
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${decisionBadgeClass(
                    portalData.decision_status,
                  )}`}
                >
                  {decisionLabel(portalData.decision_status)}
                </span>
              </div>
              <div className="mt-4 grid gap-2 text-sm text-system-gray md:grid-cols-2">
                <p>
                  <strong>Proyecto:</strong> {portalData.project_name}
                </p>
                <p>
                  <strong>Cliente:</strong> {portalData.client_name}
                </p>
                <p>
                  <strong>Disponible hasta:</strong>{' '}
                  {new Date(portalData.access_expires_at).toLocaleString()}
                </p>
              </div>
            </section>

            <section className="rounded-3xl border border-orange-100 bg-white p-6 shadow-sm md:p-8">
              <h3 className="text-base font-semibold text-gray-900">Inversion estimada</h3>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-orange-50 p-4">
                  <p className="text-xs uppercase tracking-wide text-system-gray">Total</p>
                  <p className="mt-1 text-xl font-semibold text-gray-900">{totalFormatted}</p>
                </div>
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs uppercase tracking-wide text-system-gray">Version</p>
                  <p className="mt-1 text-xl font-semibold text-gray-900">{portalData.quote_version ?? '-'}</p>
                </div>
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs uppercase tracking-wide text-system-gray">Moneda</p>
                  <p className="mt-1 text-xl font-semibold text-gray-900">{portalData.quote_currency ?? '-'}</p>
                </div>
              </div>
            </section>

            <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm md:p-8">
              <h3 className="text-base font-semibold text-gray-900">Detalle de la propuesta</h3>

              {executiveSummary && (
                <article className="mt-4 rounded-2xl border border-orange-100 bg-orange-50 p-5">
                  <h4 className="text-sm font-semibold uppercase tracking-wide text-orange-700">
                    Resumen ejecutivo
                  </h4>
                  <p className="mt-2 whitespace-pre-line text-sm leading-7 text-gray-800">{executiveSummary}</p>
                </article>
              )}

              {description && (
                <article className="mt-4 rounded-2xl border border-gray-200 p-5">
                  <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-700">
                    Contexto del proyecto
                  </h4>
                  <p className="mt-2 text-sm leading-7 text-gray-800">{description}</p>
                </article>
              )}

              {objectives.length > 0 && (
                <article className="mt-4 rounded-2xl border border-gray-200 p-5">
                  <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-700">Objetivos</h4>
                  <ul className="mt-2 space-y-2 text-sm leading-7 text-gray-800">
                    {objectives.map((objective) => (
                      <li key={objective} className="flex gap-2">
                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
                        <span>{objective}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              )}

              {deliverables.length > 0 && (
                <article className="mt-4 rounded-2xl border border-gray-200 p-5">
                  <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-700">Entregables</h4>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    {deliverables.map((deliverable, index) => (
                      <div
                        key={`${deliverable.name}-${index}`}
                        className="rounded-xl border border-gray-100 bg-gray-50 p-4"
                      >
                        <p className="text-sm font-medium text-gray-900">{deliverable.name}</p>
                        {deliverable.status && (
                          <p className="mt-1 text-xs uppercase tracking-wide text-system-gray">
                            Estado: {deliverable.status}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </article>
              )}

              <div className="mt-4 grid gap-4 md:grid-cols-2">
                {scope && (
                  <article className="rounded-2xl border border-gray-200 p-5">
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-700">Alcance</h4>
                    <p className="mt-2 text-sm leading-7 text-gray-800">{scope}</p>
                  </article>
                )}
                {timeline && (
                  <article className="rounded-2xl border border-gray-200 p-5">
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-700">
                      Cronograma
                    </h4>
                    <p className="mt-2 text-sm leading-7 text-gray-800">{timeline}</p>
                  </article>
                )}
                {conditions && (
                  <article className="rounded-2xl border border-gray-200 p-5">
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-700">
                      Condiciones comerciales
                    </h4>
                    <p className="mt-2 text-sm leading-7 text-gray-800">{conditions}</p>
                  </article>
                )}
                {freeText && (
                  <article className="rounded-2xl border border-gray-200 p-5">
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-700">
                      Informacion adicional
                    </h4>
                    <p className="mt-2 text-sm leading-7 text-gray-800">{freeText}</p>
                  </article>
                )}
              </div>

              {!executiveSummary &&
                !description &&
                objectives.length === 0 &&
                deliverables.length === 0 &&
                !scope &&
                !timeline &&
                !conditions &&
                !freeText && (
                  <p className="mt-4 rounded-xl bg-gray-50 p-4 text-sm text-system-gray">
                    No hay contenido detallado disponible para esta propuesta.
                  </p>
                )}
            </section>

            <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm space-y-4 md:p-8">
              <h3 className="text-base font-semibold text-gray-900">Tu decision</h3>
              <p className="text-sm text-system-gray">
                Elige una accion para continuar. Tu respuesta sera notificada al equipo comercial.
              </p>
              <div className="space-y-2">
                <Label htmlFor="decisionComment">Comentario (opcional)</Label>
                <textarea
                  id="decisionComment"
                  value={decisionComment}
                  onChange={(event) => setDecisionComment(event.target.value)}
                  placeholder="Ej: Me gusta la propuesta, pero quiero ajustar la fase 2."
                  disabled={submittingDecision}
                  rows={4}
                  className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30 disabled:cursor-not-allowed disabled:opacity-60"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => void onSubmitDecision('accepted')}
                  disabled={submittingDecision}
                >
                  Aceptar propuesta
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => void onSubmitDecision('revision_requested')}
                  disabled={submittingDecision}
                >
                  Solicitar revision
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => void onSubmitDecision('rejected')}
                  disabled={submittingDecision}
                >
                  No continuar
                </Button>
              </div>
            </section>
          </>
        )}

        {error && (
          <Alert variant="critical">
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4" />
              <span>{error}</span>
            </div>
          </Alert>
        )}

        {success && (
          <Alert variant="success">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 h-4 w-4" />
              <span>{success}</span>
            </div>
          </Alert>
        )}

        <footer className="pb-4 text-center text-xs text-system-gray">
          Enviado y gestionado con <span className="font-semibold text-gray-900">Nougram</span>
        </footer>
      </div>

      <Dialog open={Boolean(decisionModalMessage)} onOpenChange={(open) => !open && setDecisionModalMessage(null)}>
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
