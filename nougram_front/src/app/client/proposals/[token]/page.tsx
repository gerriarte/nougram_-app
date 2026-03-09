'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
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

const SESSION_STORAGE_PREFIX = 'nougram:proposal-portal:session:';

function getApiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL || '';
  return base.replace(/\/+$/, '');
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

  const prettyBody = useMemo(() => {
    if (!portalData?.proposal_body_json) return '';
    try {
      return JSON.stringify(portalData.proposal_body_json, null, 2);
    } catch {
      return '';
    }
  }, [portalData?.proposal_body_json]);

  return (
    <div className="min-h-screen bg-background py-10 px-4">
      <div className="mx-auto w-full max-w-4xl space-y-6">
        <header className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-gray-900 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white">
            Nougram
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Portal de propuesta</h1>
          <p className="mt-2 text-sm text-system-gray">
            Revisa la propuesta, la cotizacion y responde si deseas aceptar, rechazar o solicitar
            revision.
          </p>
        </header>

        {!sessionToken && (
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
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
            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">{portalData.proposal_title}</h2>
              <div className="mt-3 grid gap-2 text-sm text-system-gray md:grid-cols-2">
                <p>
                  <strong>Proyecto:</strong> {portalData.project_name}
                </p>
                <p>
                  <strong>Cliente:</strong> {portalData.client_name}
                </p>
                <p>
                  <strong>Estado actual:</strong> {portalData.decision_status}
                </p>
                <p>
                  <strong>Disponible hasta:</strong>{' '}
                  {new Date(portalData.access_expires_at).toLocaleString()}
                </p>
              </div>
            </section>

            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <h3 className="text-base font-semibold text-gray-900">Cotizacion</h3>
              <div className="mt-2 grid gap-2 text-sm text-system-gray md:grid-cols-3">
                <p>
                  <strong>Version:</strong> {portalData.quote_version ?? '-'}
                </p>
                <p>
                  <strong>Total:</strong> {portalData.quote_total_client_price ?? '-'}
                </p>
                <p>
                  <strong>Moneda:</strong> {portalData.quote_currency ?? '-'}
                </p>
              </div>
            </section>

            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <h3 className="text-base font-semibold text-gray-900">Detalle de propuesta</h3>
              <pre className="mt-3 max-h-[420px] overflow-auto rounded-xl bg-gray-50 p-4 text-xs text-gray-700">
                {prettyBody || 'No hay contenido disponible.'}
              </pre>
            </section>

            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <h3 className="text-base font-semibold text-gray-900">Tu respuesta</h3>
              <div className="space-y-2">
                <Label htmlFor="decisionComment">Comentario (opcional)</Label>
                <Input
                  id="decisionComment"
                  value={decisionComment}
                  onChange={(event) => setDecisionComment(event.target.value)}
                  placeholder="Ej: Solicito ajustar el alcance en fase 2"
                  disabled={submittingDecision}
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
                  Rechazar
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
    </div>
  );
}
