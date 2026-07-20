'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
    BadgeCheck,
    Building2,
    Coins,
    CreditCard,
    Download,
    FileText,
    PlusCircle,
    Power,
    RefreshCcw,
    Search,
    ShieldAlert,
    Sparkles,
    TrendingUp,
    Users
} from 'lucide-react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';

import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { useAuth } from '@/hooks/useAuth';
import { apiRequest } from '@/lib/api-client';
import { getAuthToken, setAuthToken } from '@/lib/auth';
import { trackOrganizationSwitched } from '@/lib/analytics';
import { formatDisplayNumber } from '@/lib/utils';

type OrganizationItem = {
    id: number;
    name: string;
    slug: string;
    subscription_plan: string;
    subscription_status: string;
    user_count?: number | null;
    created_at: string;
};

type PaginatedResponse<T> = {
    items: T[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
};

type UsageMetricsResponse = {
    organization: OrganizationItem;
    metrics: {
        user_count: number;
        project_count: number;
        quote_count: number;
        credits_available: number | string | null;
        credits_used_this_month: number | string | null;
        plan_limits?: {
            max_users: number;
            max_projects: number;
            max_services: number;
            max_team_members: number;
            credits_per_month: number;
        };
        remaining_capacity?: {
            users_remaining: number;
            projects_remaining: number;
        };
        quote_policy?: {
            is_credit_based: boolean;
            scope: string;
            message: string;
        };
    };
};

type CreditBalanceResponse = {
    organization_id: number;
    credits_available: number;
    credits_used_total: number;
    credits_used_this_month: number;
    credits_per_month: number | null;
    manual_credits_bonus: number;
    last_reset_at: string | null;
    next_reset_at: string | null;
    is_unlimited: boolean;
};

type CreditTransaction = {
    id: number;
    transaction_type: string;
    amount: number;
    reason: string | null;
    performed_by: number | null;
    created_at: string;
};

type FinancialLedgerItem = {
    id: number;
    organization_id: number;
    event_type: string;
    provider: string;
    amount: number;
    currency: string;
    status: string;
    external_id?: string | null;
    reference?: string | null;
    created_at: string | null;
};

type CreditTransactionListResponse = {
    items: CreditTransaction[];
};

type OrganizationUser = {
    id: number;
    email: string;
    full_name: string;
    role: string;
    created_at?: string | null;
    email_verified?: boolean | null;
    email_verified_at?: string | null;
    job_title?: string | null;
    specialty?: string | null;
};

type OrganizationUsersResponse = {
    items: OrganizationUser[];
};

type FinancialLedgerResponse = {
    items: FinancialLedgerItem[];
};

type SubscriptionHistoryItem = {
    id: number;
    organization_id: number;
    user_id: number | null;
    status: string;
    previous_plan: string | null;
    new_plan: string | null;
    previous_status: string | null;
    new_status: string | null;
    created_at: string | null;
};

type SubscriptionHistoryResponse = {
    items: SubscriptionHistoryItem[];
};

type ComparativeSnapshot = {
    proposal_total_links: number;
    proposal_accept_rate: number;
    ai_total_tokens: number;
    ai_total_cost_usd: number;
    ledger_event_count: number;
    ledger_total_amount: number;
};

type AutomaticAlert = {
    id: string;
    title: string;
    description: string;
    severity: 'warning' | 'critical' | 'info';
};

type ProposalConsumptionItem = {
    organization_id: number;
    total_links: number;
    sent_count: number;
    viewed_count: number;
    accepted_count: number;
    rejected_count: number;
    revision_count: number;
};

type AIUsageItem = {
    organization_id: number;
    event_count: number;
    total_prompt_tokens: number;
    total_completion_tokens: number;
    total_tokens: number;
    total_estimated_cost_usd: number;
};

type PaidAccountItem = {
    organization_id: number;
    plan: string;
    status: string;
    current_period_start: string | null;
    current_period_end: string | null;
};

type BillingRequestItem = {
    id: number;
    organization_id: number;
    organization_name: string | null;
    requested_by_user_id: number;
    requested_by_email: string | null;
    requested_by_name: string | null;
    request_type: string;
    target_plan: string | null;
    target_interval: string | null;
    notes: string | null;
    status: string;
    created_at: string | null;
};

type BillingRequestsResponse = {
    items: BillingRequestItem[];
    total: number;
    limit: number;
    offset: number;
};

const PLAN_OPTIONS = ['free', 'starter', 'professional', 'enterprise'];
const STATUS_OPTIONS = ['active', 'trialing', 'past_due', 'cancelled'];
const TENANT_ROLE_OPTIONS = ['owner', 'admin_financiero', 'product_manager', 'collaborator'];
const SUPPORT_ENDPOINT_PREFIXES = ['/support', '/support/support'] as const;

function getStatusVariant(status: string): 'success' | 'warning' | 'critical' | 'info' | 'default' {
    if (status === 'active') {
        return 'success';
    }
    if (status === 'trialing') {
        return 'info';
    }
    if (status === 'past_due') {
        return 'warning';
    }
    if (status === 'cancelled') {
        return 'critical';
    }
    return 'default';
}

function getRoleLabel(role: string): string {
    const normalized = (role || '').toLowerCase();
    if (normalized === 'owner') return 'Owner';
    if (normalized === 'admin_financiero') return 'Usuario financiero';
    if (normalized === 'product_manager') return 'Project manager';
    if (normalized === 'collaborator') return 'Colaborador';
    return role;
}

function formatLimit(limit: number | undefined): string {
    if (typeof limit !== 'number') return '-';
    return limit === -1 ? 'Ilimitado' : String(limit);
}

function toNumber(value: number | string | null | undefined): number {
    if (typeof value === 'number') {
        return value;
    }
    if (typeof value === 'string') {
        const parsed = Number(value);
        return Number.isNaN(parsed) ? 0 : parsed;
    }
    return 0;
}

function formatDate(value: string | null | undefined): string {
    if (!value) {
        return '-';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString('es-CO');
}

function normalizeSlug(input: string): string {
    return input
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/[\s-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

function buildPeriod(days: number, shiftPeriods = 0): { since: string; until: string } {
    const now = new Date();
    const periodMs = Math.max(1, days) * 24 * 60 * 60 * 1000;
    const end = new Date(now.getTime() - shiftPeriods * periodMs);
    const start = new Date(end.getTime() - periodMs);
    return {
        since: start.toISOString().slice(0, 19),
        until: end.toISOString().slice(0, 19),
    };
}

function pctDelta(current: number, previous: number): number {
    if (previous === 0) {
        return current === 0 ? 0 : 100;
    }
    return ((current - previous) / Math.abs(previous)) * 100;
}

export default function SuperAdminAccountsPage() {
    const supportRequest = async <T,>(pathAfterSupport: string) => {
        let lastError = 'No se pudo resolver endpoint de soporte.';
        for (let index = 0; index < SUPPORT_ENDPOINT_PREFIXES.length; index += 1) {
            const prefix = SUPPORT_ENDPOINT_PREFIXES[index];
            const response = await apiRequest<T>(`${prefix}${pathAfterSupport}`);
            if (!response.error) {
                return response;
            }

            lastError = String(response.error);
            const normalized = lastError.toLowerCase();
            const isNotFound = normalized.includes('not found') || normalized.includes('404');
            const isLast = index === SUPPORT_ENDPOINT_PREFIXES.length - 1;
            if (!isNotFound || isLast) {
                return response;
            }
        }
        return { error: lastError };
    };

    const { user, loading, refreshCurrentUser } = useAuth();
    const isSuperAdmin = user?.role === 'super_admin';

    const [listLoading, setListLoading] = useState(false);
    const [detailLoading, setDetailLoading] = useState(false);
    const [busyAction, setBusyAction] = useState<
        null | 'subscription' | 'grant' | 'reset' | 'create' | 'quick-status' | 'create-user' | 'update-role' | 'remove-user' | 'modules'
    >(null);
    const [quoteAgentModule, setQuoteAgentModule] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [organizations, setOrganizations] = useState<OrganizationItem[]>([]);
    const [selectedOrgId, setSelectedOrgId] = useState<number | null>(null);
    const [includeInactive, setIncludeInactive] = useState(true);
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [usage, setUsage] = useState<UsageMetricsResponse | null>(null);
    const [balance, setBalance] = useState<CreditBalanceResponse | null>(null);
    const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
    const [tenantUsers, setTenantUsers] = useState<OrganizationUser[]>([]);
    const [financialLedger, setFinancialLedger] = useState<FinancialLedgerItem[]>([]);
    const [subscriptionHistory, setSubscriptionHistory] = useState<SubscriptionHistoryItem[]>([]);
    const [proposalStats, setProposalStats] = useState<ProposalConsumptionItem | null>(null);
    const [aiUsageStats, setAiUsageStats] = useState<AIUsageItem | null>(null);
    const [paidAccountInfo, setPaidAccountInfo] = useState<PaidAccountItem | null>(null);
    const [billingRequests, setBillingRequests] = useState<BillingRequestItem[]>([]);

    const [plan, setPlan] = useState('free');
    const [status, setStatus] = useState('active');
    const [manualCreditsAmount, setManualCreditsAmount] = useState('1');
    const [manualCreditsReason, setManualCreditsReason] = useState('Ajuste operativo');
    const [txTypeFilter, setTxTypeFilter] = useState('all');
    const [txFromDate, setTxFromDate] = useState('');
    const [txToDate, setTxToDate] = useState('');
    const [datasetExportScope, setDatasetExportScope] = useState<'all' | 'selected'>('all');
    const [ledgerProviderFilter, setLedgerProviderFilter] = useState('');
    const [ledgerFromDate, setLedgerFromDate] = useState('');
    const [ledgerToDate, setLedgerToDate] = useState('');
    const [ledgerLimit, setLedgerLimit] = useState('20');
    const [historyFromDate, setHistoryFromDate] = useState('');
    const [historyToDate, setHistoryToDate] = useState('');
    const [analyticsRangeDays, setAnalyticsRangeDays] = useState('30');
    const [comparativeLoading, setComparativeLoading] = useState(false);
    const [currentSnapshot, setCurrentSnapshot] = useState<ComparativeSnapshot | null>(null);
    const [previousSnapshot, setPreviousSnapshot] = useState<ComparativeSnapshot | null>(null);
    const [newOrgName, setNewOrgName] = useState('');
    const [newOrgSlug, setNewOrgSlug] = useState('');
    const [newOrgPlan, setNewOrgPlan] = useState('free');
    const [newOrgStatus, setNewOrgStatus] = useState('active');
    const [newUserEmail, setNewUserEmail] = useState('');
    const [newUserFullName, setNewUserFullName] = useState('');
    const [newUserPassword, setNewUserPassword] = useState('');
    const [newUserRole, setNewUserRole] = useState('collaborator');
    const [draftRolesByUser, setDraftRolesByUser] = useState<Record<number, string>>({});
    const [exportLoading, setExportLoading] = useState(false);

    const selectedOrg = useMemo(
        () => organizations.find((org) => org.id === selectedOrgId) || null,
        [organizations, selectedOrgId]
    );
    const ownerUser = useMemo(
        () => tenantUsers.find((member) => member.role === 'owner') || tenantUsers[0] || null,
        [tenantUsers]
    );
    const financialUsersCount = useMemo(
        () => tenantUsers.filter((member) => member.role === 'admin_financiero').length,
        [tenantUsers]
    );
    const projectManagerUsersCount = useMemo(
        () => tenantUsers.filter((member) => member.role === 'product_manager').length,
        [tenantUsers]
    );
    const ownersCount = useMemo(
        () => tenantUsers.filter((member) => member.role === 'owner').length,
        [tenantUsers]
    );
    const extraUsersCount = useMemo(
        () => Math.max(0, tenantUsers.length - ownersCount),
        [tenantUsers.length, ownersCount]
    );

    const filteredOrganizations = useMemo(() => {
        const q = search.trim().toLowerCase();
        if (!q) {
            return organizations;
        }
        return organizations.filter((org) => {
            return (
                org.name.toLowerCase().includes(q) ||
                org.slug.toLowerCase().includes(q) ||
                org.subscription_plan.toLowerCase().includes(q) ||
                org.subscription_status.toLowerCase().includes(q)
            );
        });
    }, [organizations, search]);

    const tenantSelectorOptions = useMemo(() => {
        if (filteredOrganizations.length > 0) return filteredOrganizations;
        return organizations;
    }, [filteredOrganizations, organizations]);

    const filteredTransactions = useMemo(() => {
        const fromDate = txFromDate ? new Date(`${txFromDate}T00:00:00`) : null;
        const toDate = txToDate ? new Date(`${txToDate}T23:59:59`) : null;
        return transactions.filter((item) => {
            if (txTypeFilter !== 'all' && item.transaction_type !== txTypeFilter) {
                return false;
            }
            const createdAt = new Date(item.created_at);
            if (fromDate && createdAt < fromDate) return false;
            if (toDate && createdAt > toDate) return false;
            return true;
        });
    }, [transactions, txTypeFilter, txFromDate, txToDate]);

    const comparativeDeltas = useMemo(() => {
        if (!currentSnapshot || !previousSnapshot) return null;
        return {
            proposals: pctDelta(currentSnapshot.proposal_total_links, previousSnapshot.proposal_total_links),
            aiTokens: pctDelta(currentSnapshot.ai_total_tokens, previousSnapshot.ai_total_tokens),
            aiCost: pctDelta(currentSnapshot.ai_total_cost_usd, previousSnapshot.ai_total_cost_usd),
            ledgerAmount: pctDelta(currentSnapshot.ledger_total_amount, previousSnapshot.ledger_total_amount),
        };
    }, [currentSnapshot, previousSnapshot]);

    const automaticAlerts = useMemo<AutomaticAlert[]>(() => {
        const alerts: AutomaticAlert[] = [];
        const creditsAvailable = Number(balance?.credits_available || 0);
        if (selectedOrg?.subscription_status === 'past_due') {
            alerts.push({
                id: 'past_due',
                title: 'Cuenta en mora (past_due)',
                description: 'El tenant presenta estado past_due. Revisa cobro y método de pago.',
                severity: 'critical'
            });
        }
        if (selectedOrg?.subscription_status === 'cancelled') {
            alerts.push({
                id: 'cancelled',
                title: 'Cuenta cancelada',
                description: 'La cuenta está en estado cancelled y puede requerir reactivación.',
                severity: 'warning'
            });
        }
        if (creditsAvailable > 0 && creditsAvailable <= 5) {
            alerts.push({
                id: 'low_credits',
                title: 'Créditos bajos',
                description: `La cuenta tiene solo ${creditsAvailable} créditos disponibles.`,
                severity: 'warning'
            });
        }
        if (proposalStats && proposalStats.total_links >= 10) {
            const rejectionRatio = proposalStats.rejected_count / Math.max(1, proposalStats.total_links);
            if (rejectionRatio >= 0.35) {
                alerts.push({
                    id: 'high_rejection',
                    title: 'Alta tasa de rechazo en propuestas',
                    description: `Rechazo ${formatDisplayNumber(rejectionRatio * 100, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}% en propuestas del periodo.`,
                    severity: 'warning'
                });
            }
        }
        if (currentSnapshot && currentSnapshot.ai_total_cost_usd >= 25) {
            alerts.push({
                id: 'high_ai_cost',
                title: 'Costo IA alto en el periodo',
                description: `Costo estimado de IA: USD ${formatDisplayNumber(currentSnapshot.ai_total_cost_usd, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.`,
                severity: 'info'
            });
        }
        const failedLedgerEvents = financialLedger.filter((entry) => entry.status === 'failed').length;
        if (failedLedgerEvents > 0) {
            alerts.push({
                id: 'ledger_failed',
                title: 'Eventos financieros fallidos',
                description: `Se detectaron ${failedLedgerEvents} eventos de ledger en estado failed.`,
                severity: 'critical'
            });
        }
        if (tenantUsers.length > 0 && !tenantUsers.some((user) => user.role === 'owner')) {
            alerts.push({
                id: 'no_owner',
                title: 'Tenant sin owner',
                description: 'No hay usuario owner asignado. Riesgo operativo para administración.',
                severity: 'critical'
            });
        }
        const pendingBillingRequests = billingRequests.filter((item) => item.status === 'pending').length;
        if (pendingBillingRequests > 0) {
            alerts.push({
                id: 'manual_billing_queue',
                title: 'Solicitudes manuales pendientes',
                description: `Hay ${pendingBillingRequests} solicitud(es) de billing pendientes para revisión de Super Admin.`,
                severity: 'info'
            });
        }
        return alerts;
    }, [balance?.credits_available, billingRequests, currentSnapshot, financialLedger, proposalStats, selectedOrg?.subscription_status, tenantUsers]);

    const loadFinancialLedger = React.useCallback(async (organizationId: number) => {
        const params = new URLSearchParams();
        params.set('organization_id', String(organizationId));
        params.set('limit', String(Math.max(1, Number(ledgerLimit || 20))));
        params.set('offset', '0');
        if (ledgerProviderFilter.trim()) params.set('provider', ledgerProviderFilter.trim());
        if (ledgerFromDate) params.set('since', `${ledgerFromDate}T00:00:00`);
        if (ledgerToDate) params.set('until', `${ledgerToDate}T23:59:59`);

        const ledgerResponse = await supportRequest<FinancialLedgerResponse>(
            `/analytics/financial-ledger?${params.toString()}`
        );
        if (!ledgerResponse.error && ledgerResponse.data?.items) {
            setFinancialLedger(ledgerResponse.data.items);
        }
    }, [ledgerLimit, ledgerProviderFilter, ledgerFromDate, ledgerToDate]);

    const loadSubscriptionHistory = React.useCallback(async (organizationId: number) => {
        const params = new URLSearchParams();
        params.set('organization_id', String(organizationId));
        params.set('limit', '50');
        params.set('offset', '0');
        if (historyFromDate) params.set('since', `${historyFromDate}T00:00:00`);
        if (historyToDate) params.set('until', `${historyToDate}T23:59:59`);

        const historyResponse = await supportRequest<SubscriptionHistoryResponse>(
            `/analytics/subscription-history?${params.toString()}`
        );
        if (!historyResponse.error && historyResponse.data?.items) {
            setSubscriptionHistory(historyResponse.data.items);
        }
    }, [historyFromDate, historyToDate]);

    const loadBillingRequests = React.useCallback(async (organizationId: number) => {
        const response = await supportRequest<BillingRequestsResponse>(
            `/billing-requests?organization_id=${organizationId}&status=pending&limit=50&offset=0`
        );
        if (!response.error && response.data?.items) {
            setBillingRequests(response.data.items);
        }
    }, []);

    const loadComparativeAnalytics = React.useCallback(async (organizationId: number) => {
        const days = Math.max(1, Number(analyticsRangeDays || 30));
        const currentPeriod = buildPeriod(days, 0);
        const previousPeriod = buildPeriod(days, 1);
        setComparativeLoading(true);

        const [
            currentProposalsResponse,
            currentAiResponse,
            currentLedgerResponse,
            previousProposalsResponse,
            previousAiResponse,
            previousLedgerResponse,
        ] = await Promise.all([
            supportRequest<{ items: ProposalConsumptionItem[] }>(
                `/analytics/proposals?organization_id=${organizationId}&since=${encodeURIComponent(currentPeriod.since)}&until=${encodeURIComponent(currentPeriod.until)}`
            ),
            supportRequest<{ items: AIUsageItem[] }>(
                `/analytics/ai-usage?organization_id=${organizationId}&since=${encodeURIComponent(currentPeriod.since)}&until=${encodeURIComponent(currentPeriod.until)}`
            ),
            supportRequest<FinancialLedgerResponse>(
                `/analytics/financial-ledger?organization_id=${organizationId}&since=${encodeURIComponent(currentPeriod.since)}&until=${encodeURIComponent(currentPeriod.until)}&limit=500&offset=0`
            ),
            supportRequest<{ items: ProposalConsumptionItem[] }>(
                `/analytics/proposals?organization_id=${organizationId}&since=${encodeURIComponent(previousPeriod.since)}&until=${encodeURIComponent(previousPeriod.until)}`
            ),
            supportRequest<{ items: AIUsageItem[] }>(
                `/analytics/ai-usage?organization_id=${organizationId}&since=${encodeURIComponent(previousPeriod.since)}&until=${encodeURIComponent(previousPeriod.until)}`
            ),
            supportRequest<FinancialLedgerResponse>(
                `/analytics/financial-ledger?organization_id=${organizationId}&since=${encodeURIComponent(previousPeriod.since)}&until=${encodeURIComponent(previousPeriod.until)}&limit=500&offset=0`
            ),
        ]);

        const currentProposal = currentProposalsResponse.data?.items?.[0];
        const previousProposal = previousProposalsResponse.data?.items?.[0];
        const currentAi = currentAiResponse.data?.items?.[0];
        const previousAi = previousAiResponse.data?.items?.[0];
        const currentLedgerItems = currentLedgerResponse.data?.items || [];
        const previousLedgerItems = previousLedgerResponse.data?.items || [];

        const currentSnapshotValue: ComparativeSnapshot = {
            proposal_total_links: Number(currentProposal?.total_links || 0),
            proposal_accept_rate: Number(currentProposal?.accepted_count || 0) / Math.max(1, Number(currentProposal?.total_links || 0)),
            ai_total_tokens: Number(currentAi?.total_tokens || 0),
            ai_total_cost_usd: Number(currentAi?.total_estimated_cost_usd || 0),
            ledger_event_count: currentLedgerItems.length,
            ledger_total_amount: currentLedgerItems.reduce((acc, item) => acc + Number(item.amount || 0), 0),
        };

        const previousSnapshotValue: ComparativeSnapshot = {
            proposal_total_links: Number(previousProposal?.total_links || 0),
            proposal_accept_rate: Number(previousProposal?.accepted_count || 0) / Math.max(1, Number(previousProposal?.total_links || 0)),
            ai_total_tokens: Number(previousAi?.total_tokens || 0),
            ai_total_cost_usd: Number(previousAi?.total_estimated_cost_usd || 0),
            ledger_event_count: previousLedgerItems.length,
            ledger_total_amount: previousLedgerItems.reduce((acc, item) => acc + Number(item.amount || 0), 0),
        };

        setCurrentSnapshot(currentSnapshotValue);
        setPreviousSnapshot(previousSnapshotValue);
        setComparativeLoading(false);
    }, [analyticsRangeDays]);

    const loadOrganizations = async (targetPage = page) => {
        if (!isSuperAdmin) {
            return;
        }
        setListLoading(true);
        setError(null);
        const response = await supportRequest<PaginatedResponse<OrganizationItem>>(
            `/organizations?page=${targetPage}&page_size=20&include_inactive=${includeInactive}`
        );

        if (response.error || !response.data) {
            setError(response.error || 'No se pudo cargar la lista de cuentas.');
            setListLoading(false);
            return;
        }

        setOrganizations(response.data.items);
        setPage(response.data.page);
        setTotalPages(Math.max(1, response.data.total_pages || 1));

        if (!selectedOrgId && response.data.items.length > 0) {
            setSelectedOrgId(response.data.items[0].id);
        } else if (
            selectedOrgId &&
            !response.data.items.some((item) => item.id === selectedOrgId)
        ) {
            setSelectedOrgId(response.data.items.length > 0 ? response.data.items[0].id : null);
        }
        setListLoading(false);
    };

    const loadOrganizationContext = async (organizationId: number) => {
        if (!isSuperAdmin) {
            return;
        }

        setDetailLoading(true);
        setError(null);
        setProposalStats(null);
        setAiUsageStats(null);
        setPaidAccountInfo(null);

        const since = new Date();
        since.setDate(since.getDate() - 30);
        const sinceParam = since.toISOString().slice(0, 19);

        const [
            usageResponse,
            balanceResponse,
            transactionsResponse,
            usersResponse,
            proposalsResponse,
            aiUsageResponse,
            paidAccountsResponse
        ] = await Promise.all([
            supportRequest<UsageMetricsResponse>(`/organizations/${organizationId}/usage`),
            apiRequest<CreditBalanceResponse>(`/credits/admin/${organizationId}/balance`),
            apiRequest<CreditTransactionListResponse>(
                `/credits/admin/${organizationId}/transactions?page=1&page_size=15`
            ),
            apiRequest<OrganizationUsersResponse>(`/organizations/${organizationId}/users`),
            supportRequest<{ items: ProposalConsumptionItem[] }>(
                `/analytics/proposals?organization_id=${organizationId}`
            ),
            supportRequest<{ items: AIUsageItem[] }>(
                `/analytics/ai-usage?organization_id=${organizationId}&since=${encodeURIComponent(sinceParam)}`
            ),
            supportRequest<{ items: PaidAccountItem[] }>(
                `/analytics/paid-accounts?organization_id=${organizationId}`
            )
        ]);

        const firstError =
            usageResponse.error ||
            balanceResponse.error ||
            transactionsResponse.error ||
            usersResponse.error;

        if (firstError) {
            setError(firstError);
            setDetailLoading(false);
            return;
        }

        setUsage(usageResponse.data || null);
        setBalance(balanceResponse.data || null);
        setTransactions(transactionsResponse.data?.items || []);
        setTenantUsers(usersResponse.data?.items || []);
        setFinancialLedger([]);
        setSubscriptionHistory([]);
        setBillingRequests([]);

        if (!proposalsResponse.error && proposalsResponse.data?.items?.length) {
            setProposalStats(proposalsResponse.data.items[0]);
        }
        if (!aiUsageResponse.error && aiUsageResponse.data?.items?.length) {
            setAiUsageStats(aiUsageResponse.data.items[0]);
        }
        if (!paidAccountsResponse.error && paidAccountsResponse.data?.items?.length) {
            setPaidAccountInfo(paidAccountsResponse.data.items[0]);
        }
        await loadFinancialLedger(organizationId);
        await loadSubscriptionHistory(organizationId);
        await loadBillingRequests(organizationId);
        await loadComparativeAnalytics(organizationId);

        setDetailLoading(false);
    };

    const switchActiveOrganization = async (organizationId: number): Promise<boolean> => {
        if (!isSuperAdmin) return false;
        const response = await apiRequest<{ access_token: string }>(
            '/auth/switch-organization',
            {
                method: 'POST',
                body: JSON.stringify({ organization_id: organizationId }),
            }
        );
        if (response.error || !response.data?.access_token) {
            setError(response.error || 'No se pudo cambiar el tenant activo.');
            return false;
        }
        setAuthToken(response.data.access_token);
        await refreshCurrentUser();
        trackOrganizationSwitched({ organization_id: String(organizationId) });
        return true;
    };

    useEffect(() => {
        if (!loading && isSuperAdmin) {
            void loadOrganizations(1);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, isSuperAdmin, includeInactive]);

    useEffect(() => {
        if (selectedOrgId && isSuperAdmin) {
            void (async () => {
                const switched = await switchActiveOrganization(selectedOrgId);
                if (!switched) return;
                await loadOrganizationContext(selectedOrgId);
            })();
        } else {
            setUsage(null);
            setBalance(null);
            setTransactions([]);
            setTenantUsers([]);
            setFinancialLedger([]);
            setSubscriptionHistory([]);
            setBillingRequests([]);
            setCurrentSnapshot(null);
            setPreviousSnapshot(null);
            setProposalStats(null);
            setAiUsageStats(null);
            setPaidAccountInfo(null);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedOrgId, isSuperAdmin]);

    useEffect(() => {
        if (selectedOrg) {
            setPlan(selectedOrg.subscription_plan);
            setStatus(selectedOrg.subscription_status);
        }
    }, [selectedOrg]);

    useEffect(() => {
        if (!selectedOrgId || !isSuperAdmin) {
            return;
        }
        void (async () => {
            const response = await apiRequest<{ settings?: { modules?: { quote_agent?: boolean } } }>(
                `/organizations/${selectedOrgId}`
            );
            setQuoteAgentModule(Boolean(response.data?.settings?.modules?.quote_agent));
        })();
    }, [selectedOrgId, isSuperAdmin]);

    const toggleQuoteAgentModule = async () => {
        if (!selectedOrgId) {
            return;
        }
        const next = !quoteAgentModule;
        setBusyAction('modules');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<{ settings?: { modules?: { quote_agent?: boolean } } }>(
            `/organizations/${selectedOrgId}/modules`,
            { method: 'PUT', body: JSON.stringify({ quote_agent: next }) }
        );
        if (response.error) {
            setError(response.error || 'No se pudo actualizar el modulo.');
            setBusyAction(null);
            return;
        }
        setQuoteAgentModule(Boolean(response.data?.settings?.modules?.quote_agent ?? next));
        setSuccess(next ? 'Agente de Cotizacion habilitado.' : 'Agente de Cotizacion deshabilitado.');
        setBusyAction(null);
    };

    useEffect(() => {
        if (selectedOrgId && isSuperAdmin) {
            void loadComparativeAnalytics(selectedOrgId);
        }
    }, [analyticsRangeDays, isSuperAdmin, loadComparativeAnalytics, selectedOrgId]);

    const saveSubscription = async () => {
        if (!selectedOrgId) {
            return;
        }
        setBusyAction('subscription');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<OrganizationItem>(`/organizations/${selectedOrgId}/subscription`, {
            method: 'PUT',
            body: JSON.stringify({ plan, status })
        });
        if (response.error || !response.data) {
            setError(response.error || 'No se pudo actualizar la suscripcion.');
            setBusyAction(null);
            return;
        }
        setSuccess('Suscripcion actualizada y cuenta sincronizada.');
        await loadOrganizations(page);
        await loadOrganizationContext(selectedOrgId);
        setBusyAction(null);
    };

    const grantManualCredits = async () => {
        if (!selectedOrgId) {
            return;
        }
        const amount = Number(manualCreditsAmount);
        if (!Number.isFinite(amount) || amount <= 0) {
            setError('El valor de creditos debe ser mayor a 0.');
            return;
        }
        if (!manualCreditsReason.trim()) {
            setError('Debes indicar una razon para la asignacion manual.');
            return;
        }

        setBusyAction('grant');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<CreditBalanceResponse>(`/credits/admin/${selectedOrgId}/grant`, {
            method: 'POST',
            body: JSON.stringify({
                amount,
                reason: manualCreditsReason.trim()
            })
        });
        if (response.error || !response.data) {
            setError(response.error || 'No se pudieron asignar creditos.');
            setBusyAction(null);
            return;
        }

        setSuccess('Creditos asignados correctamente.');
        await loadOrganizationContext(selectedOrgId);
        setBusyAction(null);
    };

    const resetMonthlyCredits = async () => {
        if (!selectedOrgId) {
            return;
        }
        const confirmed = window.confirm(
            'Esta accion forzara un reset de creditos mensuales para la cuenta seleccionada. Deseas continuar?'
        );
        if (!confirmed) {
            return;
        }

        setBusyAction('reset');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<CreditBalanceResponse>(`/credits/admin/${selectedOrgId}/reset`, {
            method: 'POST',
            body: JSON.stringify({})
        });
        if (response.error || !response.data) {
            setError(response.error || 'No se pudo resetear el cupo mensual.');
            setBusyAction(null);
            return;
        }
        setSuccess('Reset mensual ejecutado correctamente.');
        await loadOrganizationContext(selectedOrgId);
        setBusyAction(null);
    };

    const createTenant = async () => {
        const normalizedName = newOrgName.trim();
        const normalizedSlug = normalizeSlug(newOrgSlug || newOrgName);

        if (!normalizedName) {
            setError('El nombre del tenant es obligatorio.');
            return;
        }
        if (!normalizedSlug || normalizedSlug.length < 3) {
            setError('El slug debe tener al menos 3 caracteres validos.');
            return;
        }

        setBusyAction('create');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<OrganizationItem>('/organizations/', {
            method: 'POST',
            body: JSON.stringify({
                name: normalizedName,
                slug: normalizedSlug,
                subscription_plan: newOrgPlan,
                subscription_status: newOrgStatus
            })
        });
        if (response.error || !response.data) {
            setError(response.error || 'No se pudo crear el tenant.');
            setBusyAction(null);
            return;
        }

        setSuccess(`Tenant creado: ${response.data.name}`);
        setNewOrgName('');
        setNewOrgSlug('');
        setNewOrgPlan('free');
        setNewOrgStatus('active');
        await loadOrganizations(1);
        setSelectedOrgId(response.data.id);
        setBusyAction(null);
    };

    const quickSetStatus = async (targetStatus: 'active' | 'cancelled') => {
        if (!selectedOrgId) {
            return;
        }
        setBusyAction('quick-status');
        setError(null);
        setSuccess(null);

        const response = await apiRequest<OrganizationItem>(`/organizations/${selectedOrgId}/subscription`, {
            method: 'PUT',
            body: JSON.stringify({ plan, status: targetStatus })
        });
        if (response.error || !response.data) {
            setError(response.error || 'No se pudo aplicar el cambio rapido de estado.');
            setBusyAction(null);
            return;
        }

        setStatus(targetStatus);
        setSuccess(targetStatus === 'active' ? 'Cuenta reactivada.' : 'Cuenta suspendida/cancelada.');
        await loadOrganizations(page);
        await loadOrganizationContext(selectedOrgId);
        setBusyAction(null);
    };

    const exportDataset = async (datasetType: 'organizations' | 'projects' | 'quotes' | 'team_members') => {
        setExportLoading(true);
        setError(null);
        setSuccess(null);
        const organizationIdForExport = datasetExportScope === 'selected' ? selectedOrgId : null;
        if (datasetExportScope === 'selected' && !organizationIdForExport) {
            setError('Selecciona un tenant para exportación filtrada.');
            setExportLoading(false);
            return;
        }

        const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!configuredApiUrl) {
            setError('Configuracion faltante: NEXT_PUBLIC_API_URL no esta definida.');
            setExportLoading(false);
            return;
        }
        const apiBase = configuredApiUrl.replace(/\/+$/, '');
        const token = getAuthToken();
        if (!token) {
            setError('No se encontro token de autenticacion para exportar.');
            setExportLoading(false);
            return;
        }

        try {
            let response: Response | null = null;
            for (let index = 0; index < SUPPORT_ENDPOINT_PREFIXES.length; index += 1) {
                const prefix = SUPPORT_ENDPOINT_PREFIXES[index];
                const params = new URLSearchParams({
                    dataset_type: datasetType,
                    export_format: 'csv'
                });
                if (organizationIdForExport) {
                    params.set('organization_id', String(organizationIdForExport));
                }
                const url = `${apiBase}${prefix}/datasets/export?${params.toString()}`;
                const candidate = await fetch(url, {
                    method: 'POST',
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });

                if (candidate.ok) {
                    response = candidate;
                    break;
                }
                const isLast = index === SUPPORT_ENDPOINT_PREFIXES.length - 1;
                if (candidate.status !== 404 || isLast) {
                    response = candidate;
                    break;
                }
            }

            if (!response) {
                setError('No se pudo completar la exportacion CSV.');
                setExportLoading(false);
                return;
            }

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                const message = errorBody?.detail || `Error ${response.status} al exportar`;
                setError(String(message));
                setExportLoading(false);
                return;
            }

            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = `${datasetType}-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.csv`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(blobUrl);
            setSuccess(`Exportacion CSV completada (${datasetType})${organizationIdForExport ? ' para tenant seleccionado' : ' global'}.`);
        } catch {
            setError('No se pudo completar la exportacion CSV.');
        }
        setExportLoading(false);
    };

    const applyLedgerFilters = async () => {
        if (!selectedOrgId) return;
        await loadFinancialLedger(selectedOrgId);
    };

    const applySubscriptionHistoryFilters = async () => {
        if (!selectedOrgId) return;
        await loadSubscriptionHistory(selectedOrgId);
    };

    const exportTransactionsCsv = () => {
        if (!filteredTransactions.length) {
            setError('No hay transacciones para exportar con los filtros actuales.');
            return;
        }
        const headers = ['id', 'transaction_type', 'amount', 'reason', 'performed_by', 'created_at'];
        const rows = filteredTransactions.map((item) => [
            String(item.id),
            item.transaction_type,
            String(item.amount),
            (item.reason || '').replace(/,/g, ' '),
            item.performed_by ? String(item.performed_by) : '',
            item.created_at
        ]);
        const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `credit-transactions-${selectedOrgId || 'org'}-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        setSuccess('Exportación de transacciones completada.');
    };

    const createTenantUser = async () => {
        if (!selectedOrgId) return;
        if (!newUserEmail.trim() || !newUserFullName.trim() || !newUserPassword.trim()) {
            setError('Email, nombre y contraseña son obligatorios para crear usuario.');
            return;
        }
        setBusyAction('create-user');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<OrganizationUser>(`/organizations/${selectedOrgId}/users`, {
            method: 'POST',
            body: JSON.stringify({
                email: newUserEmail.trim().toLowerCase(),
                full_name: newUserFullName.trim(),
                password: newUserPassword,
                role: newUserRole,
            }),
        });
        if (response.error || !response.data) {
            setError(response.error || 'No se pudo crear el usuario.');
            setBusyAction(null);
            return;
        }
        setNewUserEmail('');
        setNewUserFullName('');
        setNewUserPassword('');
        setNewUserRole('collaborator');
        setSuccess('Usuario creado correctamente en el tenant.');
        await loadOrganizationContext(selectedOrgId);
        setBusyAction(null);
    };

    const updateTenantUserRole = async (userId: number, role: string) => {
        if (!selectedOrgId) return;
        setBusyAction('update-role');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<OrganizationUser>(`/organizations/${selectedOrgId}/users/${userId}/role`, {
            method: 'PUT',
            body: JSON.stringify({ role }),
        });
        if (response.error || !response.data) {
            setError(response.error || 'No se pudo actualizar el rol.');
            setBusyAction(null);
            return;
        }
        setSuccess('Rol actualizado correctamente.');
        await loadOrganizationContext(selectedOrgId);
        setBusyAction(null);
    };

    const removeTenantUser = async (userId: number, fullName: string) => {
        if (!selectedOrgId) return;
        const confirmed = window.confirm(`¿Remover a ${fullName} del tenant actual?`);
        if (!confirmed) return;
        setBusyAction('remove-user');
        setError(null);
        setSuccess(null);
        const response = await apiRequest<void>(`/organizations/${selectedOrgId}/users/${userId}`, {
            method: 'DELETE',
        });
        if (response.error) {
            setError(response.error || 'No se pudo remover el usuario.');
            setBusyAction(null);
            return;
        }
        setSuccess('Usuario removido del tenant.');
        await loadOrganizationContext(selectedOrgId);
        setBusyAction(null);
    };

    if (loading) {
        return (
            <AdminLayout hideRightPanel>
                <div className="flex items-center justify-center min-h-[50vh]">
                    <div className="w-10 h-10 border-4 border-gray-200 border-t-gray-500 rounded-full animate-spin" />
                </div>
            </AdminLayout>
        );
    }

    if (!isSuperAdmin) {
        return (
            <AdminLayout hideRightPanel>
                <div className="max-w-[900px] mx-auto">
                    <Alert variant="critical">
                        <div>
                            <AlertTitle>Acceso restringido</AlertTitle>
                            <AlertDescription>
                                Este modulo de gestion de cuentas solo esta habilitado para usuarios super_admin.
                            </AlertDescription>
                        </div>
                    </Alert>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout hideRightPanel>
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8 max-w-[1600px] mx-auto"
            >
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Control de Cuentas</h1>
                        <p className="text-system-gray font-medium text-lg mt-2">
                            Gestion centralizada de tenants, suscripcion, creditos y operacion.
                        </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        <select
                            className="h-11 rounded-xl bg-white px-3 text-sm font-medium text-gray-900 border border-gray-200"
                            value={datasetExportScope}
                            onChange={(event) => setDatasetExportScope(event.target.value as 'all' | 'selected')}
                        >
                            <option value="all">Exportar global</option>
                            <option value="selected">Exportar tenant seleccionado</option>
                        </select>
                        <Button
                            variant="outline"
                            className="h-11 rounded-xl"
                            onClick={() => void exportDataset('organizations')}
                            disabled={exportLoading}
                        >
                            <Download size={15} className="mr-2" />
                            Cuentas
                        </Button>
                        <Button
                            variant="outline"
                            className="h-11 rounded-xl"
                            onClick={() => void exportDataset('projects')}
                            disabled={exportLoading}
                        >
                            <Download size={15} className="mr-2" />
                            Proyectos
                        </Button>
                        <Button
                            variant="outline"
                            className="h-11 rounded-xl"
                            onClick={() => void exportDataset('quotes')}
                            disabled={exportLoading}
                        >
                            <Download size={15} className="mr-2" />
                            Cotizaciones
                        </Button>
                        <Button
                            variant="outline"
                            className="h-11 rounded-xl"
                            onClick={() => void exportDataset('team_members')}
                            disabled={exportLoading}
                        >
                            <Download size={15} className="mr-2" />
                            Nómina
                        </Button>
                        <Button
                            variant="outline"
                            className="h-11 rounded-xl"
                            onClick={() => void loadOrganizations(page)}
                            disabled={listLoading}
                        >
                            <RefreshCcw size={15} className="mr-2" />
                            Actualizar
                        </Button>
                    </div>
                </div>

                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                    <div className="p-6">
                        <div className="flex flex-col md:flex-row md:items-end gap-3">
                            <div className="min-w-0 flex-1">
                                <label className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                    Selector rapido de tenant
                                </label>
                                <select
                                    className="mt-2 h-11 w-full rounded-xl bg-white px-3 text-sm font-medium text-gray-900 border border-gray-200"
                                    value={selectedOrgId ?? ''}
                                    onChange={(event) => {
                                        const next = event.target.value;
                                        setSelectedOrgId(next ? Number(next) : null);
                                    }}
                                    disabled={listLoading || organizations.length === 0}
                                >
                                    <option value="">Selecciona un tenant...</option>
                                    {tenantSelectorOptions.map((org) => (
                                        <option key={org.id} value={org.id}>
                                            {org.name} ({org.slug}) - {org.subscription_status}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <p className="text-xs text-system-gray md:pb-2">
                                Usa este desplegable para cambiar de tenant sin navegar la lista.
                            </p>
                        </div>
                    </div>
                </div>

                {error && (
                    <Alert variant="critical">
                        <div>
                            <AlertTitle>Error operativo</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </div>
                    </Alert>
                )}

                {success && (
                    <Alert variant="success">
                        <div>
                            <AlertTitle>Operacion completada</AlertTitle>
                            <AlertDescription>{success}</AlertDescription>
                        </div>
                    </Alert>
                )}

                <div className="grid grid-cols-1 xl:grid-cols-[420px_minmax(0,1fr)] gap-6">
                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                        <div className="px-6 py-4 border-b border-gray-100 space-y-4">
                            <div className="flex items-center justify-between gap-3">
                                <h3 className="text-[20px] font-bold text-gray-900">Tenants</h3>
                                <Badge variant="info">{organizations.length} en pagina</Badge>
                            </div>
                            <p className="text-[13px] text-gray-500">
                                Vista de cuentas por pagina. Puedes filtrar por texto y seleccionar una para administrar.
                            </p>
                            <div className="relative">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-system-gray" />
                                <Input
                                    value={search}
                                    onChange={(event) => setSearch(event.target.value)}
                                    placeholder="Buscar por nombre, slug, plan o estado..."
                                    className="pl-9"
                                />
                            </div>
                            <label className="inline-flex items-center gap-2 text-sm text-system-gray font-medium">
                                <input
                                    type="checkbox"
                                    checked={includeInactive}
                                    onChange={(event) => setIncludeInactive(event.target.checked)}
                                    className="rounded border-gray-300"
                                />
                                Incluir cuentas inactivas/canceladas
                            </label>
                        </div>
                        <div className="p-6 pt-0">
                            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4 mb-4 space-y-3">
                                <p className="text-[11px] font-black text-gray-500 uppercase tracking-[0.15em]">
                                    Crear nuevo tenant
                                </p>
                                <div className="space-y-3">
                                    <Input
                                        value={newOrgName}
                                        onChange={(event) => setNewOrgName(event.target.value)}
                                        placeholder="Nombre del tenant"
                                    />
                                    <Input
                                        value={newOrgSlug}
                                        onChange={(event) => setNewOrgSlug(event.target.value)}
                                        placeholder="Slug (opcional, se autogenera)"
                                    />
                                    <div className="grid grid-cols-2 gap-3">
                                        <select
                                            className="h-12 w-full rounded-xl bg-white px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/50"
                                            value={newOrgPlan}
                                            onChange={(event) => setNewOrgPlan(event.target.value)}
                                        >
                                            {PLAN_OPTIONS.map((option) => (
                                                <option key={option} value={option}>
                                                    {option}
                                                </option>
                                            ))}
                                        </select>
                                        <select
                                            className="h-12 w-full rounded-xl bg-white px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/50"
                                            value={newOrgStatus}
                                            onChange={(event) => setNewOrgStatus(event.target.value)}
                                        >
                                            {STATUS_OPTIONS.map((option) => (
                                                <option key={option} value={option}>
                                                    {option}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <Button
                                    className="h-11 rounded-xl bg-gray-900 hover:bg-gray-700 text-white"
                                    onClick={() => void createTenant()}
                                    disabled={busyAction === 'create'}
                                >
                                    <PlusCircle size={15} className="mr-2" />
                                    {busyAction === 'create' ? 'Creando...' : 'Crear tenant'}
                                </Button>
                            </div>

                            <div className="space-y-3 max-h-[620px] overflow-y-auto pr-1">
                                {listLoading && (
                                    <div className="py-8 flex justify-center">
                                        <div className="w-7 h-7 border-4 border-gray-200 border-t-gray-500 rounded-full animate-spin" />
                                    </div>
                                )}
                                {!listLoading && filteredOrganizations.length === 0 && (
                                    <div className="rounded-xl border border-dashed border-gray-200 p-5 text-sm text-system-gray">
                                        No hay cuentas para los filtros actuales.
                                    </div>
                                )}

                                {!listLoading && filteredOrganizations.map((org) => {
                                    const isActiveCard = selectedOrgId === org.id;
                                    return (
                                        <button
                                            key={org.id}
                                            type="button"
                                            onClick={() => setSelectedOrgId(org.id)}
                                            className={`w-full text-left rounded-2xl border p-4 transition-all ${isActiveCard
                                                ? 'border-primary bg-primary-soft shadow-sm'
                                                : 'border-gray-100 bg-white hover:border-gray-200'
                                                }`}
                                        >
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="min-w-0">
                                                    <p className="text-base font-bold text-gray-900 truncate">{org.name}</p>
                                                    <p className="text-[11px] font-black text-system-gray uppercase tracking-widest mt-1 truncate">
                                                        {org.slug}
                                                    </p>
                                                </div>
                                                <Badge variant={getStatusVariant(org.subscription_status)}>
                                                    {org.subscription_status}
                                                </Badge>
                                            </div>
                                            <div className="flex items-center gap-3 mt-3 text-xs font-semibold text-system-gray">
                                                <span>Plan: {org.subscription_plan}</span>
                                                <span className="inline-flex items-center gap-1">
                                                    <Users size={12} />
                                                    {org.user_count ?? 0}
                                                </span>
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>

                            <div className="mt-5 flex items-center justify-between gap-3">
                                <Button
                                    variant="outline"
                                    className="rounded-xl"
                                    onClick={() => void loadOrganizations(Math.max(1, page - 1))}
                                    disabled={page <= 1 || listLoading}
                                >
                                    Anterior
                                </Button>
                                <p className="text-sm font-semibold text-system-gray">
                                    Pagina {page} de {totalPages}
                                </p>
                                <Button
                                    variant="outline"
                                    className="rounded-xl"
                                    onClick={() => void loadOrganizations(Math.min(totalPages, page + 1))}
                                    disabled={page >= totalPages || listLoading}
                                >
                                    Siguiente
                                </Button>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        {!selectedOrgId && (
                            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                <div className="p-6">
                                    <div className="py-14 text-center text-system-gray">
                                        Selecciona una cuenta para administrar su operacion.
                                    </div>
                                </div>
                            </div>
                        )}

                        {selectedOrgId && (
                            <>
                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                                            <div>
                                                <h3 className="text-[20px] font-bold text-gray-900 flex items-center gap-2">
                                                    <Building2 size={20} />
                                                    {selectedOrg?.name || `Tenant #${selectedOrgId}`}
                                                </h3>
                                                <p className="text-[13px] text-gray-500 mt-1">
                                                    Gestion de estado de cuenta y plan de suscripcion.
                                                </p>
                                            </div>
                                            <Badge variant={getStatusVariant(status)}>{status}</Badge>
                                        </div>
                                    </div>
                                    <div className="p-6">
                                        <div className="grid grid-cols-1 xl:grid-cols-4 gap-3 mb-4">
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                    Datos del usuario
                                                </p>
                                                <p className="text-sm font-bold text-gray-900 mt-1">
                                                    {ownerUser?.full_name || 'Sin owner asignado'}
                                                </p>
                                                <p className="text-xs text-system-gray">{ownerUser?.email || '-'}</p>
                                                <p className="text-xs text-system-gray mt-1">
                                                    Rol: {ownerUser ? getRoleLabel(ownerUser.role) : '-'}
                                                </p>
                                            </div>
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                    Datos personales
                                                </p>
                                                <p className="text-xs text-system-gray mt-1">
                                                    Cargo: {ownerUser?.job_title || '-'}
                                                </p>
                                                <p className="text-xs text-system-gray">
                                                    Especialidad: {ownerUser?.specialty || '-'}
                                                </p>
                                                <p className="text-xs text-system-gray">
                                                    Verificado: {ownerUser?.email_verified ? 'Si' : 'No'}
                                                </p>
                                            </div>
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                    Datos de la empresa
                                                </p>
                                                <p className="text-sm font-bold text-gray-900 mt-1">{selectedOrg?.name || '-'}</p>
                                                <p className="text-xs text-system-gray">Slug: {selectedOrg?.slug || '-'}</p>
                                                <p className="text-xs text-system-gray">
                                                    Registro empresa: {formatDate(selectedOrg?.created_at)}
                                                </p>
                                            </div>
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                    Usuarios y registro
                                                </p>
                                                <p className="text-xs text-system-gray mt-1">
                                                    Usuarios extras: {extraUsersCount}
                                                </p>
                                                <p className="text-xs text-system-gray">
                                                    Usuario financiero: {financialUsersCount}
                                                </p>
                                                <p className="text-xs text-system-gray">
                                                    Project manager: {projectManagerUsersCount}
                                                </p>
                                                <p className="text-xs text-system-gray">
                                                    Fecha registro usuario: {formatDate(ownerUser?.created_at || ownerUser?.email_verified_at)}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <label className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                    Plan
                                                </label>
                                                <select
                                                    className="h-12 w-full rounded-xl bg-gray-200/50 px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/50"
                                                    value={plan}
                                                    onChange={(event) => setPlan(event.target.value)}
                                                >
                                                    {PLAN_OPTIONS.map((option) => (
                                                        <option key={option} value={option}>
                                                            {option}
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                    Estado
                                                </label>
                                                <select
                                                    className="h-12 w-full rounded-xl bg-gray-200/50 px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/50"
                                                    value={status}
                                                    onChange={(event) => setStatus(event.target.value)}
                                                >
                                                    {STATUS_OPTIONS.map((option) => (
                                                        <option key={option} value={option}>
                                                            {option}
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>

                                        <div className="mt-4 flex items-center gap-3">
                                            <Button
                                                className="h-11 rounded-xl bg-gray-900 hover:bg-gray-700 text-white"
                                                onClick={() => void saveSubscription()}
                                                disabled={busyAction === 'subscription'}
                                            >
                                                <BadgeCheck size={15} className="mr-2" />
                                                {busyAction === 'subscription' ? 'Guardando...' : 'Guardar suscripcion'}
                                            </Button>
                                            <Button
                                                variant="outline"
                                                className="h-11 rounded-xl"
                                                onClick={() => void quickSetStatus('active')}
                                                disabled={busyAction === 'quick-status'}
                                            >
                                                <Power size={15} className="mr-2" />
                                                Reactivar
                                            </Button>
                                            <Button
                                                variant="outline"
                                                className="h-11 rounded-xl"
                                                onClick={() => void quickSetStatus('cancelled')}
                                                disabled={busyAction === 'quick-status'}
                                            >
                                                <Power size={15} className="mr-2" />
                                                Suspender
                                            </Button>
                                        </div>

                                        <div className="mt-5 pt-4 border-t border-gray-100">
                                            <p className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">Modulos</p>
                                            <div className="flex items-center justify-between rounded-xl border border-gray-200 px-4 py-3">
                                                <div>
                                                    <p className="text-sm font-bold text-gray-900">Agente de Cotizacion ✨</p>
                                                    <p className="text-xs text-system-gray">Habilita el chat de cotizacion asistida por IA para este tenant.</p>
                                                </div>
                                                <Button
                                                    variant={quoteAgentModule ? 'primary' : 'outline'}
                                                    className="h-10 rounded-xl min-w-[120px]"
                                                    onClick={() => void toggleQuoteAgentModule()}
                                                    disabled={busyAction === 'modules'}
                                                >
                                                    {busyAction === 'modules'
                                                        ? 'Guardando...'
                                                        : quoteAgentModule
                                                            ? 'Habilitado'
                                                            : 'Deshabilitado'}
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                        <div className="p-6 space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                Creditos disponibles
                                            </p>
                                            <p className="text-3xl font-black text-gray-900">
                                                {balance ? balance.credits_available : '-'}
                                            </p>
                                            <p className="text-xs text-system-gray">
                                                Usados mes: {balance ? balance.credits_used_this_month : '-'}
                                            </p>
                                            <p className="text-[11px] text-system-gray">
                                                A nivel empresa (tenant), no por usuario.
                                            </p>
                                        </div>
                                    </div>
                                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                        <div className="p-6 space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                Cotizaciones y cupo
                                            </p>
                                            <p className="text-3xl font-black text-gray-900">
                                                {usage ? usage.metrics.quote_count : '-'}
                                            </p>
                                            <p className="text-xs text-system-gray">
                                                Proyectos: {usage ? usage.metrics.project_count : '-'} / {formatLimit(usage?.metrics.plan_limits?.max_projects)}
                                            </p>
                                            <p className="text-[11px] text-system-gray">
                                                {usage?.metrics.quote_policy?.message || 'Las cotizaciones se controlan por créditos del tenant.'}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                        <div className="p-6 space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                Usuarios del tenant
                                            </p>
                                            <p className="text-3xl font-black text-gray-900">
                                                {usage ? usage.metrics.user_count : '-'}
                                            </p>
                                            <p className="text-xs text-system-gray">
                                                Owners: {ownersCount} · Financieros: {financialUsersCount} · PM: {projectManagerUsersCount}
                                            </p>
                                            <p className="text-[11px] text-system-gray">
                                                Limite plan: {formatLimit(usage?.metrics.plan_limits?.max_users)}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[16px] font-bold text-gray-900 flex items-center gap-2">
                                            <Coins size={16} />
                                            Limites del plan y disponibilidad
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Todos los tenants inician en free. La disponibilidad se controla por empresa.
                                        </p>
                                    </div>
                                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
                                        <div className="rounded-xl border border-gray-100 bg-white p-3">
                                            <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Usuarios</p>
                                            <p className="text-sm font-bold text-gray-900">
                                                {usage?.metrics.user_count ?? '-'} / {formatLimit(usage?.metrics.plan_limits?.max_users)}
                                            </p>
                                            <p className="text-[11px] text-system-gray">
                                                Disponibles: {formatLimit(usage?.metrics.remaining_capacity?.users_remaining)}
                                            </p>
                                        </div>
                                        <div className="rounded-xl border border-gray-100 bg-white p-3">
                                            <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Proyectos</p>
                                            <p className="text-sm font-bold text-gray-900">
                                                {usage?.metrics.project_count ?? '-'} / {formatLimit(usage?.metrics.plan_limits?.max_projects)}
                                            </p>
                                            <p className="text-[11px] text-system-gray">
                                                Disponibles: {formatLimit(usage?.metrics.remaining_capacity?.projects_remaining)}
                                            </p>
                                        </div>
                                        <div className="rounded-xl border border-gray-100 bg-white p-3">
                                            <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Servicios</p>
                                            <p className="text-sm font-bold text-gray-900">
                                                Limite: {formatLimit(usage?.metrics.plan_limits?.max_services)}
                                            </p>
                                        </div>
                                        <div className="rounded-xl border border-gray-100 bg-white p-3">
                                            <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Team members</p>
                                            <p className="text-sm font-bold text-gray-900">
                                                Limite: {formatLimit(usage?.metrics.plan_limits?.max_team_members)}
                                            </p>
                                        </div>
                                        <div className="rounded-xl border border-primary-soft bg-primary-soft p-3">
                                            <p className="text-[11px] font-black uppercase tracking-[0.15em] text-primary">Creditos mensuales</p>
                                            <p className="text-sm font-bold text-gray-900">
                                                {formatLimit(usage?.metrics.plan_limits?.credits_per_month)}
                                            </p>
                                            <p className="text-[11px] text-primary">
                                                Disponibles ahora: {balance ? balance.credits_available : '-'}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                        <div className="p-6 space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em] flex items-center gap-1.5">
                                                <FileText size={12} />
                                                Propuestas (tenant)
                                            </p>
                                            {detailLoading && <p className="text-sm text-system-gray">Cargando...</p>}
                                            {!detailLoading && !proposalStats && (
                                                <p className="text-sm text-system-gray">Sin datos</p>
                                            )}
                                            {!detailLoading && proposalStats && (
                                                <>
                                                    <p className="text-2xl font-black text-gray-900">
                                                        {proposalStats.total_links} enlaces
                                                    </p>
                                                    <p className="text-xs text-system-gray">
                                                        Enviadas: {proposalStats.sent_count} · Vistas: {proposalStats.viewed_count} · Aceptadas: {proposalStats.accepted_count} · Rechazadas: {proposalStats.rejected_count}
                                                    </p>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                        <div className="p-6 space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em] flex items-center gap-1.5">
                                                <Sparkles size={12} />
                                                Uso IA (30 d)
                                            </p>
                                            {detailLoading && <p className="text-sm text-system-gray">Cargando...</p>}
                                            {!detailLoading && !aiUsageStats && (
                                                <p className="text-sm text-system-gray">Sin datos</p>
                                            )}
                                            {!detailLoading && aiUsageStats && (
                                                <>
                                                    <p className="text-2xl font-black text-gray-900">
                                                        {formatDisplayNumber(aiUsageStats.total_tokens, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} tokens
                                                    </p>
                                                    <p className="text-xs text-system-gray">
                                                        {aiUsageStats.event_count} eventos · ~USD {formatDisplayNumber(aiUsageStats.total_estimated_cost_usd, { minimumFractionDigits: 4, maximumFractionDigits: 4 })}
                                                    </p>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                        <div className="p-6 space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em] flex items-center gap-1.5">
                                                <TrendingUp size={12} />
                                                Cuenta paga
                                            </p>
                                            {detailLoading && <p className="text-sm text-system-gray">Cargando...</p>}
                                            {!detailLoading && !paidAccountInfo && (
                                                <p className="text-sm text-system-gray">No (free/inactiva)</p>
                                            )}
                                            {!detailLoading && paidAccountInfo && (
                                                <>
                                                    <p className="text-2xl font-black text-gray-900 capitalize">
                                                        {paidAccountInfo.plan}
                                                    </p>
                                                    <p className="text-xs text-system-gray">
                                                        Estado: {paidAccountInfo.status}
                                                        {paidAccountInfo.current_period_end ? ` · Vence: ${formatDate(paidAccountInfo.current_period_end)}` : ''}
                                                    </p>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[18px] font-bold text-gray-900 flex items-center gap-2">
                                            <TrendingUp size={18} />
                                            Analitica comparativa
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Compara el periodo actual vs periodo anterior de la misma longitud.
                                        </p>
                                    </div>
                                    <div className="p-6">
                                        <div className="mb-4 flex flex-wrap items-center gap-2">
                                            <span className="text-xs font-semibold text-system-gray">Rango:</span>
                                            <select
                                                className="h-9 rounded-lg bg-white px-3 text-xs font-medium text-gray-900 border border-gray-200"
                                                value={analyticsRangeDays}
                                                onChange={(event) => setAnalyticsRangeDays(event.target.value)}
                                            >
                                                <option value="7">7 días</option>
                                                <option value="14">14 días</option>
                                                <option value="30">30 días</option>
                                                <option value="90">90 días</option>
                                            </select>
                                            {comparativeLoading && <span className="text-xs text-system-gray">Actualizando...</span>}
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Propuestas</p>
                                                <p className="text-2xl font-black text-gray-900">{currentSnapshot?.proposal_total_links ?? '-'}</p>
                                                <p className="text-xs text-system-gray">
                                                    Δ {comparativeDeltas ? `${comparativeDeltas.proposals >= 0 ? '+' : ''}${formatDisplayNumber(comparativeDeltas.proposals, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%` : '-'}
                                                </p>
                                            </div>
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Tokens IA</p>
                                                <p className="text-2xl font-black text-gray-900">{currentSnapshot ? formatDisplayNumber(currentSnapshot.ai_total_tokens, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) : '-'}</p>
                                                <p className="text-xs text-system-gray">
                                                    Δ {comparativeDeltas ? `${comparativeDeltas.aiTokens >= 0 ? '+' : ''}${formatDisplayNumber(comparativeDeltas.aiTokens, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%` : '-'}
                                                </p>
                                            </div>
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Costo IA (USD)</p>
                                                <p className="text-2xl font-black text-gray-900">{currentSnapshot ? formatDisplayNumber(currentSnapshot.ai_total_cost_usd, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}</p>
                                                <p className="text-xs text-system-gray">
                                                    Δ {comparativeDeltas ? `${comparativeDeltas.aiCost >= 0 ? '+' : ''}${formatDisplayNumber(comparativeDeltas.aiCost, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%` : '-'}
                                                </p>
                                            </div>
                                            <div className="rounded-xl border border-gray-100 bg-white p-3">
                                                <p className="text-[11px] font-black uppercase tracking-[0.15em] text-system-gray">Monto ledger</p>
                                                <p className="text-2xl font-black text-gray-900">{currentSnapshot ? formatDisplayNumber(currentSnapshot.ledger_total_amount, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}</p>
                                                <p className="text-xs text-system-gray">
                                                    Δ {comparativeDeltas ? `${comparativeDeltas.ledgerAmount >= 0 ? '+' : ''}${formatDisplayNumber(comparativeDeltas.ledgerAmount, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%` : '-'}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[18px] font-bold text-gray-900 flex items-center gap-2">
                                            <FileText size={18} />
                                            Fallback Super Admin: solicitudes manuales
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Cola operativa de solicitudes de billing del tenant (visible aunque falle email).
                                        </p>
                                    </div>
                                    <div className="p-6">
                                        <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
                                            {detailLoading && (
                                                <div className="text-sm text-system-gray">Cargando solicitudes...</div>
                                            )}
                                            {!detailLoading && billingRequests.length === 0 && (
                                                <div className="text-sm text-system-gray">Sin solicitudes manuales pendientes.</div>
                                            )}
                                            {!detailLoading && billingRequests.map((item) => (
                                                <div key={item.id} className="rounded-xl border border-gray-100 bg-white p-3">
                                                    <div className="flex items-center justify-between gap-2">
                                                        <p className="text-sm font-bold text-gray-900">#{item.id} · {item.request_type}</p>
                                                        <Badge variant={item.status === 'pending' ? 'warning' : 'default'}>
                                                            {item.status}
                                                        </Badge>
                                                    </div>
                                                    <p className="text-xs text-system-gray mt-1">
                                                        Solicitante: {item.requested_by_name || 'N/A'} ({item.requested_by_email || 'sin email'})
                                                    </p>
                                                    <p className="text-xs text-system-gray mt-1">
                                                        Plan destino: {item.target_plan || '-'} · Intervalo: {item.target_interval || '-'}
                                                    </p>
                                                    <p className="text-xs text-system-gray mt-1">Notas: {item.notes || 'Sin notas'}</p>
                                                    <p className="text-[11px] text-system-gray mt-1">{formatDate(item.created_at || undefined)}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[18px] font-bold text-gray-900 flex items-center gap-2">
                                            <ShieldAlert size={18} />
                                            Alertas automaticas
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Deteccion automatica de señales de riesgo operativo y financiero.
                                        </p>
                                    </div>
                                    <div className="p-6">
                                        {automaticAlerts.length === 0 ? (
                                            <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl p-3">
                                                Sin alertas criticas para este tenant en el estado actual.
                                            </div>
                                        ) : (
                                            <div className="space-y-2">
                                                {automaticAlerts.map((alertItem) => (
                                                    <div key={alertItem.id} className="rounded-xl border border-gray-100 bg-white p-3">
                                                        <div className="flex items-center justify-between gap-2">
                                                            <p className="text-sm font-bold text-gray-900">{alertItem.title}</p>
                                                            <Badge variant={alertItem.severity === 'critical' ? 'critical' : alertItem.severity === 'warning' ? 'warning' : 'info'}>
                                                                {alertItem.severity}
                                                            </Badge>
                                                        </div>
                                                        <p className="text-xs text-system-gray mt-1">{alertItem.description}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[18px] font-bold text-gray-900 flex items-center gap-2">
                                            <CreditCard size={18} />
                                            Operaciones de creditos
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Controles de soporte para ajustes manuales y reset de ciclo.
                                        </p>
                                    </div>
                                    <div className="p-6">
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                            <div className="md:col-span-1">
                                                <Input
                                                    type="number"
                                                    min={1}
                                                    value={manualCreditsAmount}
                                                    onChange={(event) => setManualCreditsAmount(event.target.value)}
                                                    placeholder="Cantidad"
                                                />
                                            </div>
                                            <div className="md:col-span-2">
                                                <Input
                                                    value={manualCreditsReason}
                                                    onChange={(event) => setManualCreditsReason(event.target.value)}
                                                    placeholder="Razon del ajuste"
                                                />
                                            </div>
                                        </div>
                                        <div className="mt-4 flex flex-wrap items-center gap-3">
                                            <Button
                                                className="h-11 rounded-xl bg-gray-900 hover:bg-gray-700 text-white"
                                                onClick={() => void grantManualCredits()}
                                                disabled={busyAction === 'grant'}
                                            >
                                                <Coins size={15} className="mr-2" />
                                                {busyAction === 'grant' ? 'Asignando...' : 'Asignar creditos'}
                                            </Button>
                                            <Button
                                                variant="outline"
                                                className="h-11 rounded-xl"
                                                onClick={() => void resetMonthlyCredits()}
                                                disabled={busyAction === 'reset'}
                                            >
                                                <RefreshCcw size={15} className="mr-2" />
                                                {busyAction === 'reset' ? 'Reseteando...' : 'Forzar reset mensual'}
                                            </Button>
                                            <p className="text-xs text-system-gray">
                                                Proximo reset: {formatDate(balance?.next_reset_at)}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[18px] font-bold text-gray-900 flex items-center gap-2">
                                            <ShieldAlert size={18} />
                                            Trazabilidad de cuenta
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Ultimos movimientos de creditos y usuarios del tenant seleccionado.
                                        </p>
                                    </div>
                                    <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        <div>
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">
                                                Transacciones recientes
                                            </p>
                                            <div className="mb-3 grid grid-cols-1 md:grid-cols-4 gap-2">
                                                <select
                                                    className="h-9 rounded-lg bg-white px-3 text-xs font-medium text-gray-900 border border-gray-200"
                                                    value={txTypeFilter}
                                                    onChange={(event) => setTxTypeFilter(event.target.value)}
                                                >
                                                    <option value="all">Todos los tipos</option>
                                                    {Array.from(new Set(transactions.map((item) => item.transaction_type))).map((txType) => (
                                                        <option key={txType} value={txType}>
                                                            {txType}
                                                        </option>
                                                    ))}
                                                </select>
                                                <Input
                                                    type="date"
                                                    className="h-9 text-xs"
                                                    value={txFromDate}
                                                    onChange={(event) => setTxFromDate(event.target.value)}
                                                />
                                                <Input
                                                    type="date"
                                                    className="h-9 text-xs"
                                                    value={txToDate}
                                                    onChange={(event) => setTxToDate(event.target.value)}
                                                />
                                                <Button
                                                    variant="outline"
                                                    className="h-9 text-xs"
                                                    onClick={exportTransactionsCsv}
                                                    disabled={filteredTransactions.length === 0}
                                                >
                                                    <Download size={13} className="mr-1" />
                                                    Exportar CSV
                                                </Button>
                                            </div>
                                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                                {detailLoading && (
                                                    <div className="text-sm text-system-gray">Cargando actividad...</div>
                                                )}
                                                {!detailLoading && filteredTransactions.length === 0 && (
                                                    <div className="text-sm text-system-gray">Sin movimientos registrados.</div>
                                                )}
                                                {!detailLoading && filteredTransactions.map((item) => (
                                                    <div key={item.id} className="rounded-xl border border-gray-100 bg-white p-3">
                                                        <div className="flex items-center justify-between gap-3">
                                                            <Badge variant={item.amount >= 0 ? 'success' : 'warning'}>
                                                                {item.transaction_type}
                                                            </Badge>
                                                            <p className="text-sm font-bold text-gray-900">
                                                                {item.amount > 0 ? '+' : ''}
                                                                {toNumber(item.amount)}
                                                            </p>
                                                        </div>
                                                        <p className="text-xs text-system-gray mt-2">{item.reason || 'Sin razon'}</p>
                                                        <p className="text-[11px] text-system-gray mt-1">{formatDate(item.created_at)}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        <div>
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">
                                                Usuarios del tenant (gestion)
                                            </p>
                                            <div className="mb-4 rounded-xl border border-gray-200 bg-gray-50 p-3 space-y-2">
                                                <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Crear usuario</p>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                    <Input
                                                        value={newUserEmail}
                                                        onChange={(event) => setNewUserEmail(event.target.value)}
                                                        placeholder="Email"
                                                        className="h-9 text-xs bg-white"
                                                    />
                                                    <Input
                                                        value={newUserFullName}
                                                        onChange={(event) => setNewUserFullName(event.target.value)}
                                                        placeholder="Nombre completo"
                                                        className="h-9 text-xs bg-white"
                                                    />
                                                    <Input
                                                        value={newUserPassword}
                                                        onChange={(event) => setNewUserPassword(event.target.value)}
                                                        placeholder="Contraseña temporal"
                                                        className="h-9 text-xs bg-white"
                                                        type="password"
                                                    />
                                                    <select
                                                        className="h-9 rounded-lg bg-white px-3 text-xs font-medium text-gray-900 border border-gray-200"
                                                        value={newUserRole}
                                                        onChange={(event) => setNewUserRole(event.target.value)}
                                                    >
                                                        {TENANT_ROLE_OPTIONS.map((option) => (
                                                            <option key={option} value={option}>
                                                                {option}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                                <Button
                                                    className="h-9 text-xs bg-gray-900 hover:bg-gray-700 text-white"
                                                    onClick={() => void createTenantUser()}
                                                    disabled={busyAction === 'create-user'}
                                                >
                                                    {busyAction === 'create-user' ? 'Creando...' : 'Crear usuario en tenant'}
                                                </Button>
                                            </div>
                                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                                {detailLoading && (
                                                    <div className="text-sm text-system-gray">Cargando usuarios...</div>
                                                )}
                                                {!detailLoading && tenantUsers.length === 0 && (
                                                    <div className="text-sm text-system-gray">No hay usuarios asociados.</div>
                                                )}
                                                {!detailLoading && tenantUsers.map((member) => (
                                                    <div key={member.id} className="rounded-xl border border-gray-100 bg-white p-3">
                                                        <div className="flex items-start justify-between gap-3 mb-2">
                                                            <div className="min-w-0">
                                                                <p className="text-sm font-bold text-gray-900 truncate">{member.full_name}</p>
                                                                <p className="text-xs text-system-gray truncate">{member.email}</p>
                                                            </div>
                                                            <Badge variant={member.role === 'owner' ? 'info' : 'default'}>
                                                                {getRoleLabel(member.role)}
                                                            </Badge>
                                                        </div>
                                                        <p className="text-[11px] text-system-gray mb-2">
                                                            Cargo: {member.job_title || '-'} · Especialidad: {member.specialty || '-'} · Registro: {formatDate(member.created_at || member.email_verified_at)}
                                                        </p>
                                                        <div className="flex items-center gap-2">
                                                            <select
                                                                className="h-8 rounded-lg bg-white px-2 text-xs font-medium text-gray-900 border border-gray-200"
                                                                value={draftRolesByUser[member.id] || member.role}
                                                                onChange={(event) => setDraftRolesByUser((prev) => ({
                                                                    ...prev,
                                                                    [member.id]: event.target.value
                                                                }))}
                                                            >
                                                                {Array.from(new Set([...TENANT_ROLE_OPTIONS, member.role])).map((option) => (
                                                                    <option key={option} value={option}>
                                                                        {option}
                                                                    </option>
                                                                ))}
                                                            </select>
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                className="h-8 text-xs"
                                                                disabled={busyAction === 'update-role'}
                                                                onClick={() => void updateTenantUserRole(member.id, draftRolesByUser[member.id] || member.role)}
                                                            >
                                                                Guardar rol
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="destructive"
                                                                className="h-8 text-xs"
                                                                disabled={busyAction === 'remove-user'}
                                                                onClick={() => void removeTenantUser(member.id, member.full_name)}
                                                            >
                                                                Remover
                                                            </Button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[18px] font-bold text-gray-900 flex items-center gap-2">
                                            <ShieldAlert size={18} />
                                            Ledger financiero
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Eventos financieros con filtros por proveedor y rango de fechas.
                                        </p>
                                    </div>
                                    <div className="p-6">
                                        <div className="mb-3 grid grid-cols-1 md:grid-cols-5 gap-2">
                                            <Input
                                                value={ledgerProviderFilter}
                                                onChange={(event) => setLedgerProviderFilter(event.target.value)}
                                                placeholder="Proveedor (manual, wompi...)"
                                                className="h-9 text-xs"
                                            />
                                            <Input
                                                type="date"
                                                value={ledgerFromDate}
                                                onChange={(event) => setLedgerFromDate(event.target.value)}
                                                className="h-9 text-xs"
                                            />
                                            <Input
                                                type="date"
                                                value={ledgerToDate}
                                                onChange={(event) => setLedgerToDate(event.target.value)}
                                                className="h-9 text-xs"
                                            />
                                            <Input
                                                type="number"
                                                min={1}
                                                max={200}
                                                value={ledgerLimit}
                                                onChange={(event) => setLedgerLimit(event.target.value)}
                                                className="h-9 text-xs"
                                                placeholder="Limite"
                                            />
                                            <Button
                                                variant="outline"
                                                className="h-9 text-xs"
                                                onClick={() => void applyLedgerFilters()}
                                                disabled={!selectedOrgId}
                                            >
                                                Aplicar filtros
                                            </Button>
                                        </div>
                                        <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
                                            {detailLoading && <div className="text-sm text-system-gray">Cargando ledger...</div>}
                                            {!detailLoading && financialLedger.length === 0 && (
                                                <div className="text-sm text-system-gray">Sin eventos de ledger.</div>
                                            )}
                                            {!detailLoading && financialLedger.map((entry) => (
                                                <div key={entry.id} className="rounded-xl border border-gray-100 bg-white p-3">
                                                    <div className="flex items-center justify-between gap-3">
                                                        <Badge variant="default">{entry.event_type}</Badge>
                                                        <p className="text-sm font-bold text-gray-900">
                                                            {entry.amount > 0 ? '+' : ''}{entry.amount} {entry.currency}
                                                        </p>
                                                    </div>
                                                    <p className="text-xs text-system-gray mt-2">
                                                        Proveedor: {entry.provider} · Estado: {entry.status}
                                                    </p>
                                                    <p className="text-[11px] text-system-gray mt-1">{formatDate(entry.created_at || undefined)}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
                                    <div className="px-6 py-4 border-b border-gray-100">
                                        <h3 className="text-[18px] font-bold text-gray-900 flex items-center gap-2">
                                            <BadgeCheck size={18} />
                                            Historial de suscripcion
                                        </h3>
                                        <p className="text-[13px] text-gray-500">
                                            Trazabilidad de cambios de plan y estado por tenant.
                                        </p>
                                    </div>
                                    <div className="p-6">
                                        <div className="mb-3 grid grid-cols-1 md:grid-cols-3 gap-2">
                                            <Input
                                                type="date"
                                                value={historyFromDate}
                                                onChange={(event) => setHistoryFromDate(event.target.value)}
                                                className="h-9 text-xs"
                                            />
                                            <Input
                                                type="date"
                                                value={historyToDate}
                                                onChange={(event) => setHistoryToDate(event.target.value)}
                                                className="h-9 text-xs"
                                            />
                                            <Button
                                                variant="outline"
                                                className="h-9 text-xs"
                                                onClick={() => void applySubscriptionHistoryFilters()}
                                                disabled={!selectedOrgId}
                                            >
                                                Filtrar historial
                                            </Button>
                                        </div>
                                        <div className="space-y-2 max-h-[240px] overflow-y-auto pr-1">
                                            {detailLoading && <div className="text-sm text-system-gray">Cargando historial...</div>}
                                            {!detailLoading && subscriptionHistory.length === 0 && (
                                                <div className="text-sm text-system-gray">Sin cambios de suscripcion registrados.</div>
                                            )}
                                            {!detailLoading && subscriptionHistory.map((entry) => (
                                                <div key={entry.id} className="rounded-xl border border-gray-100 bg-white p-3">
                                                    <div className="flex items-center justify-between gap-2">
                                                        <Badge variant="info">subscription.update</Badge>
                                                        <span className="text-[11px] text-system-gray">{formatDate(entry.created_at || undefined)}</span>
                                                    </div>
                                                    <p className="text-xs text-gray-700 mt-2">
                                                        Plan: <b>{entry.previous_plan || '-'}</b> → <b>{entry.new_plan || '-'}</b>
                                                    </p>
                                                    <p className="text-xs text-gray-700">
                                                        Estado: <b>{entry.previous_status || '-'}</b> → <b>{entry.new_status || '-'}</b>
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </motion.div>
        </AdminLayout>
    );
}
