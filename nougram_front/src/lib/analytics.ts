/**
 * Analytics layer: GTM dataLayer push (SSR-safe), dedupe, and typed event wrappers.
 * No PII (emails, names, free text). Use stable IDs and enums only.
 */

const DEDUPE_TTL_MS = 2000;
const recentEventIds = new Set<string>();
let dedupeTimer: ReturnType<typeof setTimeout> | null = null;

function clearDedupeAfterTtl(): void {
  dedupeTimer = setTimeout(() => {
    recentEventIds.clear();
    dedupeTimer = null;
  }, DEDUPE_TTL_MS);
}

function consumeDedupeId(eventId: string): boolean {
  if (recentEventIds.has(eventId)) return false;
  recentEventIds.add(eventId);
  if (!dedupeTimer) clearDedupeAfterTtl();
  return true;
}

declare global {
  interface Window {
    dataLayer?: Record<string, unknown>[];
  }
}

/** SSR-safe push to GTM dataLayer. No-op on server. */
export function pushToDataLayer(
  payload: Record<string, unknown>,
  options?: { eventId?: string; skipDedupe?: boolean }
): void {
  if (typeof window === "undefined") return;
  const eventId = options?.eventId;
  if (eventId && !options?.skipDedupe && !consumeDedupeId(eventId)) return;
  window.dataLayer = window.dataLayer ?? [];
  window.dataLayer.push(payload);
}

/** Stable page_view for route changes (App Router). */
export function trackPageView(params: {
  path: string;
  search?: string;
  title?: string;
}): void {
  pushToDataLayer(
    {
      event: "page_view",
      page_path: params.path,
      page_search: params.search ?? undefined,
      page_title: params.title ?? undefined,
    },
    { eventId: `pv_${params.path}_${params.search ?? ""}`, skipDedupe: false }
  );
}

// --- Auth ---
export function trackLoginAttempt(): void {
  pushToDataLayer({ event: "login_attempt" });
}

export function trackLoginResult(params: {
  success: boolean;
  user_id?: string;
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "login_result",
    success: params.success,
    user_id: params.user_id != null ? String(params.user_id) : undefined,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

export function trackLogout(): void {
  pushToDataLayer({ event: "logout" });
}

export function trackOrganizationSwitched(params: {
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "organization_switched",
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

// --- Onboarding ---
export function trackOnboardingStepCompleted(params: {
  step: string;
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "onboarding_step_completed",
    step: params.step,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

export function trackOnboardingImportStarted(params: { organization_id?: string }): void {
  pushToDataLayer({
    event: "onboarding_import_started",
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

export function trackOnboardingImportApplied(params: {
  organization_id?: string;
  row_count?: number;
}): void {
  pushToDataLayer({
    event: "onboarding_import_applied",
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
    row_count: params.row_count,
  });
}

export function trackOnboardingComplete(params: { organization_id?: string }): void {
  pushToDataLayer({
    event: "onboarding_complete",
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

export function trackOnboardingStarted(params: { organization_id?: string }): void {
  pushToDataLayer(
    {
      event: "onboarding_started",
      organization_id:
        params.organization_id != null ? String(params.organization_id) : undefined,
    },
    { skipDedupe: true }
  );
}

export function trackOnboardingStepViewed(params: {
  step: string;
  organization_id?: string;
}): void {
  pushToDataLayer(
    {
      event: "onboarding_step_viewed",
      step: params.step,
      organization_id:
        params.organization_id != null ? String(params.organization_id) : undefined,
    },
    { skipDedupe: true }
  );
}

export function trackOnboardingAbandoned(params: {
  step: string;
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "onboarding_abandoned",
    step: params.step,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

// --- Quote lifecycle ---
export function trackQuoteCreated(params: {
  project_id?: string;
  quote_id?: string;
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "quote_created",
    project_id: params.project_id != null ? String(params.project_id) : undefined,
    quote_id: params.quote_id != null ? String(params.quote_id) : undefined,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

export function trackQuoteSaved(params: {
  project_id?: string;
  quote_id?: string;
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "quote_saved",
    project_id: params.project_id != null ? String(params.project_id) : undefined,
    quote_id: params.quote_id != null ? String(params.quote_id) : undefined,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

// --- Proposal ---
export function trackProposalGeneratedWithAI(params: {
  project_id?: string;
  quote_id?: string;
  proposal_id?: string;
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "proposal_generated_with_ai",
    project_id: params.project_id != null ? String(params.project_id) : undefined,
    quote_id: params.quote_id != null ? String(params.quote_id) : undefined,
    proposal_id:
      params.proposal_id != null ? String(params.proposal_id) : undefined,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

export function trackProposalShared(params: {
  quote_id?: string;
  proposal_id?: string;
  organization_id?: string;
  sent_email: boolean;
}): void {
  pushToDataLayer({
    event: "proposal_shared",
    quote_id: params.quote_id != null ? String(params.quote_id) : undefined,
    proposal_id:
      params.proposal_id != null ? String(params.proposal_id) : undefined,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
    sent_email: params.sent_email,
  });
}

// --- Client portal (view/decision) ---
export function trackProposalViewed(params: {
  proposal_id?: string;
  organization_id?: string;
}): void {
  pushToDataLayer({
    event: "proposal_viewed",
    proposal_id:
      params.proposal_id != null ? String(params.proposal_id) : undefined,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
  });
}

export function trackProposalDecision(params: {
  proposal_id?: string;
  organization_id?: string;
  decision: "accepted" | "rejected" | "revision";
}): void {
  pushToDataLayer({
    event: "proposal_decision",
    proposal_id:
      params.proposal_id != null ? String(params.proposal_id) : undefined,
    organization_id:
      params.organization_id != null ? String(params.organization_id) : undefined,
    decision: params.decision,
  });
}
