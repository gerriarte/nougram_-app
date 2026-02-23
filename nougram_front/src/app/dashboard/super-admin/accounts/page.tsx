'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
    BadgeCheck,
    Building2,
    Coins,
    CreditCard,
    Download,
    PlusCircle,
    Power,
    RefreshCcw,
    Search,
    ShieldAlert,
    Users
} from 'lucide-react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { useAuth } from '@/hooks/useAuth';
import { apiRequest } from '@/lib/api-client';
import { getAuthToken } from '@/lib/auth';

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

type CreditTransactionListResponse = {
    items: CreditTransaction[];
};

type OrganizationUser = {
    id: number;
    email: string;
    full_name: string;
    role: string;
};

type OrganizationUsersResponse = {
    items: OrganizationUser[];
};

const PLAN_OPTIONS = ['free', 'starter', 'professional', 'enterprise'];
const STATUS_OPTIONS = ['active', 'trialing', 'past_due', 'cancelled'];

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

export default function SuperAdminAccountsPage() {
    const { user, loading } = useAuth();
    const isSuperAdmin = user?.role === 'super_admin';

    const [listLoading, setListLoading] = useState(false);
    const [detailLoading, setDetailLoading] = useState(false);
    const [busyAction, setBusyAction] = useState<null | 'subscription' | 'grant' | 'reset' | 'create' | 'quick-status'>(null);
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

    const [plan, setPlan] = useState('free');
    const [status, setStatus] = useState('active');
    const [manualCreditsAmount, setManualCreditsAmount] = useState('1');
    const [manualCreditsReason, setManualCreditsReason] = useState('Ajuste operativo');
    const [newOrgName, setNewOrgName] = useState('');
    const [newOrgSlug, setNewOrgSlug] = useState('');
    const [newOrgPlan, setNewOrgPlan] = useState('free');
    const [newOrgStatus, setNewOrgStatus] = useState('active');
    const [exportLoading, setExportLoading] = useState(false);

    const selectedOrg = useMemo(
        () => organizations.find((org) => org.id === selectedOrgId) || null,
        [organizations, selectedOrgId]
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

    const loadOrganizations = async (targetPage = page) => {
        if (!isSuperAdmin) {
            return;
        }
        setListLoading(true);
        setError(null);
        const response = await apiRequest<PaginatedResponse<OrganizationItem>>(
            `/support/organizations?page=${targetPage}&page_size=20&include_inactive=${includeInactive}`
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

        const [usageResponse, balanceResponse, transactionsResponse, usersResponse] = await Promise.all([
            apiRequest<UsageMetricsResponse>(`/support/organizations/${organizationId}/usage`),
            apiRequest<CreditBalanceResponse>(`/credits/admin/${organizationId}/balance`),
            apiRequest<CreditTransactionListResponse>(
                `/credits/admin/${organizationId}/transactions?page=1&page_size=15`
            ),
            apiRequest<OrganizationUsersResponse>(`/organizations/${organizationId}/users`)
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
        setDetailLoading(false);
    };

    useEffect(() => {
        if (!loading && isSuperAdmin) {
            void loadOrganizations(1);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, isSuperAdmin, includeInactive]);

    useEffect(() => {
        if (selectedOrgId && isSuperAdmin) {
            void loadOrganizationContext(selectedOrgId);
        } else {
            setUsage(null);
            setBalance(null);
            setTransactions([]);
            setTenantUsers([]);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedOrgId, isSuperAdmin]);

    useEffect(() => {
        if (selectedOrg) {
            setPlan(selectedOrg.subscription_plan);
            setStatus(selectedOrg.subscription_status);
        }
    }, [selectedOrg]);

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

        const apiBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');
        const token = getAuthToken();
        if (!token) {
            setError('No se encontro token de autenticacion para exportar.');
            setExportLoading(false);
            return;
        }

        try {
            const url = `${apiBase}/support/datasets/export?dataset_type=${datasetType}&export_format=csv`;
            const response = await fetch(url, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
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
            setSuccess(`Exportacion CSV completada (${datasetType}).`);
        } catch {
            setError('No se pudo completar la exportacion CSV.');
        }
        setExportLoading(false);
    };

    if (loading) {
        return (
            <AdminLayout hideRightPanel>
                <div className="flex items-center justify-center min-h-[50vh]">
                    <div className="w-10 h-10 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
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
                    <div className="flex items-center gap-3">
                        <Button
                            variant="outline"
                            className="h-11 rounded-xl"
                            onClick={() => void exportDataset('organizations')}
                            disabled={exportLoading}
                        >
                            <Download size={15} className="mr-2" />
                            Exportar cuentas CSV
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
                    <Card>
                        <CardHeader className="space-y-4">
                            <div className="flex items-center justify-between gap-3">
                                <CardTitle className="text-2xl">Tenants</CardTitle>
                                <Badge variant="info">{organizations.length} en pagina</Badge>
                            </div>
                            <CardDescription>
                                Vista de cuentas por pagina. Puedes filtrar por texto y seleccionar una para administrar.
                            </CardDescription>
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
                        </CardHeader>
                        <CardContent className="pt-0">
                            <div className="rounded-2xl border border-blue-100 bg-blue-50/70 p-4 mb-4 space-y-3">
                                <p className="text-[11px] font-black text-blue-700 uppercase tracking-[0.15em]">
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
                                            className="h-12 w-full rounded-xl bg-white px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                                            className="h-12 w-full rounded-xl bg-white px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                                    className="h-11 rounded-xl bg-blue-600 hover:bg-blue-700 text-white"
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
                                        <div className="w-7 h-7 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
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
                                                ? 'border-blue-300 bg-blue-50/70 shadow-sm'
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
                        </CardContent>
                    </Card>

                    <div className="space-y-6">
                        {!selectedOrgId && (
                            <Card>
                                <CardContent>
                                    <div className="py-14 text-center text-system-gray">
                                        Selecciona una cuenta para administrar su operacion.
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {selectedOrgId && (
                            <>
                                <Card>
                                    <CardHeader>
                                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                                            <div>
                                                <CardTitle className="text-2xl flex items-center gap-2">
                                                    <Building2 size={20} />
                                                    {selectedOrg?.name || `Tenant #${selectedOrgId}`}
                                                </CardTitle>
                                                <CardDescription className="mt-1">
                                                    Gestion de estado de cuenta y plan de suscripcion.
                                                </CardDescription>
                                            </div>
                                            <Badge variant={getStatusVariant(status)}>{status}</Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <label className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                    Plan
                                                </label>
                                                <select
                                                    className="h-12 w-full rounded-xl bg-gray-200/50 px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                                                    className="h-12 w-full rounded-xl bg-gray-200/50 px-3 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                                                className="h-11 rounded-xl bg-blue-600 hover:bg-blue-700 text-white"
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
                                    </CardContent>
                                </Card>

                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                                    <Card>
                                        <CardContent className="space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                Creditos disponibles
                                            </p>
                                            <p className="text-3xl font-black text-gray-900">
                                                {balance ? balance.credits_available : '-'}
                                            </p>
                                            <p className="text-xs text-system-gray">
                                                Usados mes: {balance ? balance.credits_used_this_month : '-'}
                                            </p>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardContent className="space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                Actividad comercial
                                            </p>
                                            <p className="text-3xl font-black text-gray-900">
                                                {usage ? usage.metrics.quote_count : '-'}
                                            </p>
                                            <p className="text-xs text-system-gray">
                                                Proyectos: {usage ? usage.metrics.project_count : '-'}
                                            </p>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardContent className="space-y-2">
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">
                                                Usuarios del tenant
                                            </p>
                                            <p className="text-3xl font-black text-gray-900">
                                                {usage ? usage.metrics.user_count : '-'}
                                            </p>
                                            <p className="text-xs text-system-gray">
                                                Owners en cuenta:{' '}
                                                {tenantUsers.filter((member) => member.role === 'owner').length}
                                            </p>
                                        </CardContent>
                                    </Card>
                                </div>

                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-xl flex items-center gap-2">
                                            <CreditCard size={18} />
                                            Operaciones de creditos
                                        </CardTitle>
                                        <CardDescription>
                                            Controles de soporte para ajustes manuales y reset de ciclo.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
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
                                                className="h-11 rounded-xl bg-blue-600 hover:bg-blue-700 text-white"
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
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-xl flex items-center gap-2">
                                            <ShieldAlert size={18} />
                                            Trazabilidad de cuenta
                                        </CardTitle>
                                        <CardDescription>
                                            Ultimos movimientos de creditos y usuarios del tenant seleccionado.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        <div>
                                            <p className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">
                                                Transacciones recientes
                                            </p>
                                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                                {detailLoading && (
                                                    <div className="text-sm text-system-gray">Cargando actividad...</div>
                                                )}
                                                {!detailLoading && transactions.length === 0 && (
                                                    <div className="text-sm text-system-gray">Sin movimientos registrados.</div>
                                                )}
                                                {!detailLoading && transactions.map((item) => (
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
                                                Usuarios del tenant
                                            </p>
                                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                                {detailLoading && (
                                                    <div className="text-sm text-system-gray">Cargando usuarios...</div>
                                                )}
                                                {!detailLoading && tenantUsers.length === 0 && (
                                                    <div className="text-sm text-system-gray">No hay usuarios asociados.</div>
                                                )}
                                                {!detailLoading && tenantUsers.map((member) => (
                                                    <div key={member.id} className="rounded-xl border border-gray-100 bg-white p-3">
                                                        <div className="flex items-start justify-between gap-3">
                                                            <div className="min-w-0">
                                                                <p className="text-sm font-bold text-gray-900 truncate">{member.full_name}</p>
                                                                <p className="text-xs text-system-gray truncate">{member.email}</p>
                                                            </div>
                                                            <Badge variant={member.role === 'owner' ? 'info' : 'default'}>
                                                                {member.role}
                                                            </Badge>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </>
                        )}
                    </div>
                </div>
            </motion.div>
        </AdminLayout>
    );
}
