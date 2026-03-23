
import React, { useEffect, useMemo, useState } from 'react';
import { PricingTable } from './PricingTable';
import { CreditTracker } from './CreditTracker';
import { SubscriptionStatus } from './SubscriptionStatus';
import { TransactionHistory } from './TransactionHistory';
import { Plan, Subscription, CreditUsage, CreditTransaction, Transaction, PlanTier } from '@/types/billing';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'; // Assuming standard Shadcn-like tabs
import { Wallet, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { apiRequest } from '@/lib/api-client';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';

type BackendPlanInfo = {
    name: string;
    display_name: string;
    description: string;
    monthly_price: string | null;
    yearly_price: string | null;
    limits: Record<string, number>;
};

type BackendSubscription = {
    id: number;
    plan: PlanTier;
    status: string;
    current_period_start: string | null;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
    billing_provider?: string | null;
    manual_mode?: boolean;
};

type BackendCreditBalance = {
    credits_available: number;
    credits_used_total: number;
    credits_used_this_month: number;
    credits_per_month: number | null;
    next_reset_at: string | null;
};

type BackendCreditTx = {
    id: number;
    transaction_type: string;
    amount: number;
    reason?: string | null;
    created_at: string;
};

type BackendManualBillingRequest = {
    id: number;
    request_type: string;
    status: string;
};

const SUPPORT_LEVEL_BY_PLAN: Record<PlanTier, Plan['features']['supportLevel']> = {
    free: 'community',
    starter: 'email',
    professional: 'priority',
    enterprise: 'dedicated',
};

export function BillingDashboard() {
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [plans, setPlans] = useState<Plan[]>([]);
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [manualBillingMode, setManualBillingMode] = useState(false);
    const [usage, setUsage] = useState<CreditUsage | null>(null);
    const [creditActivity, setCreditActivity] = useState<CreditTransaction[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);

    const toPlan = (item: BackendPlanInfo): Plan => {
        const toLimit = (value: unknown): number | 'unlimited' =>
            typeof value === 'number' && value >= 0 ? value : 'unlimited';
        const planId = item.name as PlanTier;
        const monthly = item.monthly_price ? Number(item.monthly_price) : 0;
        const yearly = item.yearly_price ? Number(item.yearly_price) : 0;
        const limits = item.limits || {};
        return {
            id: planId,
            name: item.display_name || item.name,
            description: item.description || '',
            priceMonthly: Number.isFinite(monthly) ? monthly : 0,
            priceYearly: Number.isFinite(yearly) ? yearly : 0,
            currency: 'USD',
            isPopular: planId === 'professional',
            features: {
                creditsPerMonth: toLimit(limits.credits_per_month),
                maxUsers: toLimit(limits.max_users),
                maxProjects: toLimit(limits.max_projects),
                maxServices: toLimit(limits.max_services),
                maxTeamMembers: toLimit(limits.max_team_members),
                supportLevel: SUPPORT_LEVEL_BY_PLAN[planId] || 'community',
            },
        };
    };

    const loadBillingData = async (showSpinner: boolean = true) => {
        if (showSpinner) {
            setLoading(true);
        }
        setError(null);

        const [plansRes, subRes, balanceRes, historyRes] = await Promise.all([
            apiRequest<{ plans: BackendPlanInfo[] }>('/billing/plans'),
            apiRequest<BackendSubscription>('/billing/subscription'),
            apiRequest<BackendCreditBalance>('/credits/me/balance'),
            apiRequest<{ items: BackendCreditTx[] }>('/credits/me/history?page=1&page_size=20'),
        ]);

        if (plansRes.error || subRes.error || balanceRes.error || historyRes.error) {
            setError(
                plansRes.error ||
                subRes.error ||
                balanceRes.error ||
                historyRes.error ||
                'No se pudo cargar la información de facturación.'
            );
            setLoading(false);
            return;
        }

        const mappedPlans = (plansRes.data?.plans || [])
            .filter((item) => ['free', 'starter', 'professional', 'enterprise'].includes(item.name))
            .map(toPlan);
        setPlans(mappedPlans);

        if (subRes.data) {
            const isManualMode = Boolean(subRes.data.manual_mode) || (subRes.data.billing_provider === 'manual');
            setManualBillingMode(isManualMode);
            setSubscription({
                id: String(subRes.data.id),
                planId: subRes.data.plan,
                status: subRes.data.status === 'cancelled' ? 'cancelled' : (subRes.data.status as Subscription['status']),
                interval: 'monthly',
                currentPeriodStart: subRes.data.current_period_start || new Date().toISOString(),
                currentPeriodEnd: subRes.data.current_period_end || new Date().toISOString(),
                cancelAtPeriodEnd: subRes.data.cancel_at_period_end,
                billingProvider: subRes.data.billing_provider || undefined,
                manualMode: isManualMode,
            });
        }

        if (balanceRes.data) {
            setUsage({
                available: balanceRes.data.credits_available,
                usedThisMonth: balanceRes.data.credits_used_this_month,
                usedTotal: balanceRes.data.credits_used_total,
                limitMonthly: balanceRes.data.credits_per_month,
                nextResetDate: balanceRes.data.next_reset_at || new Date().toISOString(),
            });
        }

        const historyItems = historyRes.data?.items || [];
        setCreditActivity(
            historyItems.slice(0, 6).map((item) => ({
                id: String(item.id),
                action: item.reason || item.transaction_type,
                credits: item.amount,
                timestamp: new Date(item.created_at).toLocaleString(),
            }))
        );

        setTransactions(
            historyItems.map((item) => ({
                id: String(item.id),
                invoiceNumber: `CR-${item.id}`,
                amount: Math.abs(item.amount),
                currency: 'CR',
                status: 'paid',
                date: item.created_at,
                planName: item.transaction_type,
                periodStart: item.created_at,
                periodEnd: item.created_at,
            }))
        );

        setLoading(false);
    };

    useEffect(() => {
        void loadBillingData();
    }, []);

    const currentPlan = useMemo(() => {
        if (!subscription) return null;
        return plans.find((item) => item.id === subscription.planId) || null;
    }, [plans, subscription]);

    const handleUpgrade = () => {
        setActiveTab('plans');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleSelectPlan = async (planId: PlanTier, interval: 'monthly' | 'yearly') => {
        if (!subscription) return;
        if (manualBillingMode) {
            setActionLoading(true);
            setError(null);
            setSuccess(null);
            const intervalForApi = interval === 'yearly' ? 'year' : 'month';
            const response = await apiRequest<BackendManualBillingRequest>('/billing/manual-requests', {
                method: 'POST',
                body: JSON.stringify({
                    request_type: 'change_plan',
                    target_plan: planId,
                    target_interval: intervalForApi,
                    notes: `Solicitud de cambio desde Billing Dashboard. Plan actual: ${subscription.planId}`,
                }),
            });
            if (response.error) {
                setError(response.error);
                setActionLoading(false);
                return;
            }
            setSuccess(`Solicitud #${response.data?.id ?? ''} enviada: cambio al plan '${planId}'. Soporte/Super Admin fue notificado.`);
            setActionLoading(false);
            return;
        }
        if (planId === 'enterprise') {
            setError('Para Enterprise, contacta a soporte para activación personalizada.');
            return;
        }

        setActionLoading(true);
        setError(null);
        setSuccess(null);

        const intervalForApi = interval === 'yearly' ? 'year' : 'month';
        const samePlan = subscription.planId === planId;
        const hasExternalSubscription = subscription.id !== '0';

        if (hasExternalSubscription && !samePlan) {
            const response = await apiRequest<BackendSubscription>('/billing/subscription', {
                method: 'PUT',
                body: JSON.stringify({
                    plan: planId,
                    interval: intervalForApi,
                }),
            });
            if (response.error) {
                setError(response.error);
                setActionLoading(false);
                return;
            }
            setSuccess('Plan actualizado correctamente.');
            await loadBillingData(false);
            setActionLoading(false);
            return;
        }

        const currentUrl = typeof window !== 'undefined' ? window.location.origin + '/billing' : '';
        const checkoutResponse = await apiRequest<{ url: string }>('/billing/checkout-session', {
            method: 'POST',
            body: JSON.stringify({
                plan: planId,
                interval: intervalForApi,
                success_url: `${currentUrl}?billing=success`,
                cancel_url: `${currentUrl}?billing=cancelled`,
            }),
        });
        if (checkoutResponse.error) {
            setError(checkoutResponse.error);
            setActionLoading(false);
            return;
        }
        if (checkoutResponse.data?.url && typeof window !== 'undefined') {
            window.location.href = checkoutResponse.data.url;
            return;
        }
        setActionLoading(false);
    };

    const handleCancelSubscription = async () => {
        if (manualBillingMode) {
            setActionLoading(true);
            setError(null);
            setSuccess(null);
            const response = await apiRequest<BackendManualBillingRequest>('/billing/manual-requests', {
                method: 'POST',
                body: JSON.stringify({
                    request_type: 'cancel_subscription',
                    notes: 'Solicitud de cancelación manual al final del periodo',
                }),
            });
            if (response.error) {
                setError(response.error);
                setActionLoading(false);
                return;
            }
            setSuccess(`Solicitud #${response.data?.id ?? ''} enviada: cancelación manual pendiente por soporte.`);
            setActionLoading(false);
            return;
        }
        if (!window.confirm('¿Quieres cancelar la suscripción al final del periodo actual?')) return;
        setActionLoading(true);
        setError(null);
        setSuccess(null);
        const response = await apiRequest<BackendSubscription>('/billing/subscription/cancel', {
            method: 'POST',
            body: JSON.stringify({ cancel_immediately: false }),
        });
        if (response.error) {
            setError(response.error);
            setActionLoading(false);
            return;
        }
        setSuccess('Cancelación programada al final del periodo.');
        await loadBillingData(false);
        setActionLoading(false);
    };

    const handleUpdatePayment = async () => {
        if (!subscription) return;
        if (manualBillingMode) {
            setActionLoading(true);
            setError(null);
            setSuccess(null);
            const response = await apiRequest<BackendManualBillingRequest>('/billing/manual-requests', {
                method: 'POST',
                body: JSON.stringify({
                    request_type: 'update_payment_method',
                    notes: 'Solicitud de actualización de método de pago en modo manual',
                }),
            });
            if (response.error) {
                setError(response.error);
                setActionLoading(false);
                return;
            }
            setSuccess(
                `Solicitud #${response.data?.id ?? ''} enviada: actualización de pago será gestionada por soporte/super admin.`
            );
            setActionLoading(false);
            return;
        }
        await handleSelectPlan(subscription.planId, subscription.interval);
    };

    const handleTopUp = () => {
        handleUpgrade();
    };

    return (
        <div className="min-h-screen bg-[#F5F5F7] text-[#1D1D1F]">
            {/* Apple-style Blur Header */}
            <div className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard/quotes" className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-black">
                            <ArrowLeft size={20} />
                        </Link>
                        <h1 className="text-xl font-semibold -tracking-[0.01em] flex items-center gap-3">
                            <div className="h-8 w-8 rounded-full bg-black text-white flex items-center justify-center shadow-lg shadow-black/10">
                                <Wallet size={16} strokeWidth={2.5} />
                            </div>
                            <span className="opacity-90">Facturación y Créditos</span>
                        </h1>
                    </div>
                </div>
            </div>

            <div className="max-w-5xl mx-auto px-6 py-12">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-10">

                    {/* IOS Segmented Control Style Tabs */}
                    <div className="flex justify-center mb-8">
                        <TabsList className="bg-gray-200/50 p-1 rounded-full inline-flex relative shadow-inner">
                            {['overview', 'plans', 'invoices'].map((tab) => (
                                <TabsTrigger
                                    key={tab}
                                    value={tab}
                                    className="rounded-full px-8 py-2 text-sm font-medium transition-all duration-300 data-[state=active]:bg-white data-[state=active]:text-black data-[state=active]:shadow-sm text-gray-500 hover:text-gray-900 capitalize"
                                >
                                    {tab === 'overview' ? 'Resumen' : tab === 'plans' ? 'Planes' : 'Facturas'}
                                </TabsTrigger>
                            ))}
                        </TabsList>
                    </div>

                    {error && (
                        <Alert variant="critical">
                            <div>
                                <AlertTitle>Error de facturación</AlertTitle>
                                <AlertDescription>{error}</AlertDescription>
                            </div>
                        </Alert>
                    )}
                    {success && (
                        <Alert variant="success">
                            <div>
                                <AlertTitle>Operación completada</AlertTitle>
                                <AlertDescription>{success}</AlertDescription>
                            </div>
                        </Alert>
                    )}
                    {manualBillingMode && (
                        <Alert variant="info">
                            <div>
                                <AlertTitle>Facturación en modo manual</AlertTitle>
                                <AlertDescription>
                                    La activación/cambio/cancelación de planes se realiza manualmente por soporte.
                                </AlertDescription>
                            </div>
                        </Alert>
                    )}
                    {actionLoading && (
                        <p className="text-sm text-system-gray">Procesando acción de facturación...</p>
                    )}

                    <TabsContent value="overview" className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out">
                        {/* 1. Credit Tracker */}
                        {!loading && usage && (
                            <CreditTracker
                                usage={usage}
                                recentActivity={creditActivity}
                                onUpgrade={handleUpgrade}
                                onTopUp={handleTopUp}
                            />
                        )}

                        {/* 2. Subscription Details */}
                        {!loading && subscription && currentPlan && (
                            <SubscriptionStatus
                                subscription={subscription}
                                currentPlan={currentPlan}
                                onChangePlan={handleUpgrade}
                                onUpdatePayment={() => void handleUpdatePayment()}
                                onCancel={() => void handleCancelSubscription()}
                            />
                        )}
                    </TabsContent>

                    <TabsContent value="plans" className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <PricingTable
                            currentPlanId={currentPlan?.id || 'free'}
                            manualMode={manualBillingMode}
                            onSelectPlan={(planId, interval) => void handleSelectPlan(planId, interval)}
                        />
                    </TabsContent>

                    <TabsContent value="invoices" className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <TransactionHistory transactions={transactions} />
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
}
