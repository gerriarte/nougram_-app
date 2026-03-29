
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { OnboardingStepper } from '@/components/onboarding/OnboardingStepper';
import { StepIdentity } from '@/components/onboarding/StepIdentity';
import { StepFixedCosts } from '@/components/onboarding/StepFixedCosts';
import { StepMyTeam } from '@/components/onboarding/StepMyTeam';
import { StepReady } from '@/components/onboarding/StepReady';
import { Button } from '@/components/ui/Button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { useOnboarding } from '@/hooks/useOnboarding';
import { useAuth } from '@/hooks/useAuth';
import { apiRequest } from '@/lib/api-client';
import { onboardingService } from '@/services/onboardingService';
import {
    trackOnboardingStepCompleted,
    trackOnboardingImportStarted,
    trackOnboardingImportApplied,
    trackOnboardingComplete,
    trackOnboardingStarted,
    trackOnboardingStepViewed,
    trackOnboardingAbandoned,
} from '@/lib/analytics';
import { CANONICAL_NEW_QUOTE_PATH } from '@/lib/mobile-routes';
import { FixedCostTemplate } from '@/types/onboarding';
import { normalizeCountryCode, normalizeCurrencyCode } from '@/lib/onboarding-geo';
import { Step3MyTeamData } from '@/types/onboarding';
import { formatCurrency } from '@/lib/utils';

type TemporaryBcrResponse = {
    blended_cost_rate: string;
    total_monthly_costs: string;
    total_fixed_overhead: string;
    total_tools_costs?: string;
    total_salaries: string;
    total_monthly_hours: number;
    team_members_count: number;
    currency: string;
    note: string;
};

type ImportPayload = {
    organization_name?: string;
    country: string;
    currency: string;
    team_members: Array<{ name: string; role: string; salary_monthly_brute: string; billable_hours_per_month: number }>;
    expenses: Array<{ name: string; category: 'rent' | 'software' | 'services'; amount_monthly: string; quantity: number }>;
    inventory_items: Array<{
        name: string;
        category: string;
        amount_monthly?: string;
        purchase_price?: string;
        useful_life_months?: number;
        salvage_value?: string;
        purchase_date?: string;
        depreciation_method?: 'straight_line' | 'declining_balance';
        payment_type?: 'monthly' | 'annual';
        quantity: number;
        amortizable: boolean;
    }>;
};

export default function OnboardingPage() {
    const router = useRouter();
    const { loading: authLoading, isAuthenticated } = useAuth();
    const [currentStep, setCurrentStep] = useState(1);
    const [persistError, setPersistError] = useState<string | null>(null);
    const [persisting, setPersisting] = useState(false);
    const [backendBcr, setBackendBcr] = useState<number | null>(null);
    const [backendBcrLoading, setBackendBcrLoading] = useState(false);
    const [importLoading, setImportLoading] = useState(false);
    const [importError, setImportError] = useState<string | null>(null);
    const [showImportReview, setShowImportReview] = useState(false);
    const [importPreview, setImportPreview] = useState<{
        success: boolean;
        issues: Array<{ sheet: string; row: number; field: string; message: string }>;
        payload?: ImportPayload;
        temporary_bcr?: { blended_cost_rate: string };
    } | null>(null);

    // Use the hook for state management
    const {
        data: onboardingData,
        isLoading,
        isSaving,
        saveError,
        lastSavedAt,
        updateIdentity,
        updateFixedCosts,
        updateTeam,
        updateProgress
    } = useOnboarding();

    const stepNames: Record<number, string> = { 1: 'identity', 2: 'fixed_costs', 3: 'team', 4: 'ready' };

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [authLoading, isAuthenticated, router]);

    useEffect(() => {
        if (isLoading) return;
        if (onboardingData.lastStep > 1 && currentStep === 1) {
            setCurrentStep(onboardingData.lastStep);
        }
    }, [isLoading, onboardingData.lastStep, currentStep]);

    const onboardingStartedRef = React.useRef(false);
    useEffect(() => {
        if (authLoading || !isAuthenticated || isLoading) return;
        if (onboardingStartedRef.current) return;
        onboardingStartedRef.current = true;
        trackOnboardingStarted({});
    }, [authLoading, isAuthenticated, isLoading]);

    useEffect(() => {
        if (authLoading || !isAuthenticated) return;
        const key = stepNames[currentStep];
        if (key) trackOnboardingStepViewed({ step: key });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- funnel: log per step index
    }, [currentStep, authLoading, isAuthenticated]);

    useEffect(() => {
        if (typeof window === 'undefined') return;
        const onLeave = () => {
            if (currentStep >= 4) return;
            const key = stepNames[currentStep];
            trackOnboardingAbandoned({ step: key ?? String(currentStep) });
        };
        window.addEventListener('beforeunload', onLeave);
        return () => window.removeEventListener('beforeunload', onLeave);
    }, [currentStep]);
    const handleNext = () => {
        const completedKey = stepNames[currentStep];
        if (completedKey) {
            trackOnboardingStepCompleted({ step: completedKey });
        }
        setCurrentStep((prev) => prev + 1);
        window.scrollTo(0, 0);
    };

    const handleBackStep = () => {
        setCurrentStep((prev) => Math.max(1, prev - 1));
        window.scrollTo(0, 0);
    };

    const mapImportedCategoryToFixedCost = (category: string): FixedCostTemplate['category'] => {
        const normalized = (category || '').toLowerCase();
        if (normalized === 'tools') return 'Tools';
        if (normalized === 'software') return 'Software';
        if (normalized === 'rent' || normalized === 'services' || normalized === 'overhead') return 'Overhead';
        return 'Other';
    };

    const applyImportedPayload = (payload?: ImportPayload) => {
        if (!payload) return;

        updateIdentity({
            organizationName: payload.organization_name || onboardingData.identity.organizationName,
            primaryCurrency: payload.currency,
            country: payload.country,
        });

        const importedCosts: FixedCostTemplate[] = [
            ...payload.expenses.map<FixedCostTemplate>((expense, index) => ({
                id: `import-expense-${index}`,
                name: expense.name,
                amount: Number(expense.amount_monthly) || 0,
                currency: payload.currency,
                quantity: expense.quantity || 1,
                category: mapImportedCategoryToFixedCost(expense.category),
                amortizable: false,
                icon: '💼',
                isCustom: true,
                paymentType: 'monthly',
            })),
            ...payload.inventory_items.map<FixedCostTemplate>((item, index) => ({
                id: `import-inventory-${index}`,
                name: item.name,
                amount: Number(item.amount_monthly) || 0,
                purchasePrice: Number(item.purchase_price ?? item.amount_monthly) || 0,
                usefulLifeMonths: item.useful_life_months || undefined,
                salvageValue: Number(item.salvage_value) || 0,
                purchaseDate: item.purchase_date || undefined,
                depreciationMethod: item.depreciation_method || 'straight_line',
                currency: payload.currency,
                quantity: item.quantity || 1,
                category: mapImportedCategoryToFixedCost(item.category),
                amortizable: Boolean(item.amortizable),
                costType: item.amortizable ? 'amortization' : 'operational',
                icon: item.amortizable ? '💻' : '📦',
                isCustom: true,
                paymentType: item.amortizable ? undefined : (item.payment_type || 'monthly'),
            })),
        ];

        updateFixedCosts({
            selectedTemplates: importedCosts,
            totalMonthly: importedCosts.reduce((sum, item) => sum + (item.amount || 0), 0),
        });

        const importedTeamMembers = payload.team_members.map((member) => {
            const weeklyBillableHours = Math.max(1, Math.round((member.billable_hours_per_month || 1) / 4.33));
            return {
                name: member.name,
                role: member.role,
                level: 'Mid' as const,
                salary: Number(member.salary_monthly_brute) || 0,
                totalHours: Math.max(40, weeklyBillableHours + 10),
                billableHours: weeklyBillableHours,
                vacationDays: 20,
                applySocialCharges: payload.country === 'COL',
            };
        });

        const lead = importedTeamMembers[0];
        const teamData: Partial<Step3MyTeamData> = {
            payrollHeadcount: importedTeamMembers.length || onboardingData.team.payrollHeadcount,
            name: lead?.name || onboardingData.team.name,
            role: lead?.role || onboardingData.team.role,
            level: lead?.level || onboardingData.team.level,
            salary: lead?.salary || onboardingData.team.salary,
            totalHours: lead?.totalHours || onboardingData.team.totalHours,
            billableHours: lead?.billableHours || onboardingData.team.billableHours,
            vacationDays: lead?.vacationDays || onboardingData.team.vacationDays,
            applySocialCharges: lead?.applySocialCharges ?? onboardingData.team.applySocialCharges,
            teamMembers: importedTeamMembers,
        };
        updateTeam(teamData);

        const previewBcr = importPreview?.temporary_bcr?.blended_cost_rate;
        if (previewBcr) {
            const parsed = Number(previewBcr);
            if (Number.isFinite(parsed)) setBackendBcr(parsed);
        }

        const rowCount = (payload.expenses?.length ?? 0) + (payload.inventory_items?.length ?? 0);
        trackOnboardingImportApplied({ row_count: rowCount });
        updateProgress(3);
        setCurrentStep(3);
        setImportPreview(null);
        setImportError(null);
        setShowImportReview(false);
    };

    const buildImportDelta = (payload: ImportPayload) => {
        const currentOrgName = onboardingData.identity.organizationName || '(sin nombre)';
        const nextOrgName = payload.organization_name || currentOrgName;
        const currentCountry = onboardingData.identity.country || '(sin país)';
        const nextCountry = payload.country;
        const currentCurrency = onboardingData.identity.primaryCurrency || '(sin moneda)';
        const nextCurrency = payload.currency;

        const currentTeamCount = onboardingData.team?.teamMembers?.length || 0;
        const nextTeamCount = payload.team_members.length;
        const currentFixedCount = onboardingData.fixedCosts?.selectedTemplates?.length || 0;
        const nextFixedCount = payload.expenses.length + payload.inventory_items.length;

        const currentFixedTotal = Number(onboardingData.fixedCosts?.totalMonthly || 0);
        const nextFixedTotal = payload.expenses.reduce((sum, item) => sum + (Number(item.amount_monthly) || 0), 0)
            + payload.inventory_items.reduce((sum, item) => {
                if (!item.amortizable) {
                    return sum + (Number(item.amount_monthly) || 0);
                }
                const purchase = Number(item.purchase_price ?? item.amount_monthly) || 0;
                const salvage = Number(item.salvage_value) || 0;
                const life = Math.max(1, Number(item.useful_life_months) || 36);
                return sum + Math.max(0, (purchase - salvage) / life);
            }, 0);

        return [
            { label: 'Nombre organización', current: currentOrgName, next: nextOrgName, critical: false },
            { label: 'País', current: currentCountry, next: nextCountry, critical: true },
            { label: 'Moneda primaria', current: currentCurrency, next: nextCurrency, critical: true },
            { label: 'Miembros de equipo', current: String(currentTeamCount), next: String(nextTeamCount), critical: false },
            { label: 'Ítems de costos', current: String(currentFixedCount), next: String(nextFixedCount), critical: false },
            {
                label: 'Total mensual costos',
                current: `${currentFixedTotal.toLocaleString()} ${currentCurrency}`,
                next: `${nextFixedTotal.toLocaleString()} ${nextCurrency}`,
                critical: true
            },
        ].map((row) => ({ ...row, changed: row.current !== row.next }));
    };

    const handleDownloadTemplate = async () => {
        const result = await onboardingService.downloadImportTemplate();
        if (!result.ok) {
            setImportError(result.error || 'No se pudo descargar la plantilla.');
        }
    };

    const handleImportFile = async (file?: File | null) => {
        if (!file) return;
        trackOnboardingImportStarted({});
        setImportError(null);
        setImportLoading(true);
        const result = await onboardingService.previewImportExcel(file);
        setImportLoading(false);
        if (result.error || !result.data) {
            setImportPreview(null);
            setImportError(result.error || 'No se pudo analizar el archivo.');
            return;
        }
        setImportPreview({
            success: result.data.success,
            issues: result.data.issues || [],
            payload: result.data.payload,
            temporary_bcr: result.data.temporary_bcr,
        });
    };

    const buildOnboardingPayload = () => {
        const currency = normalizeCurrencyCode(onboardingData.identity.primaryCurrency);
        const country = normalizeCountryCode(onboardingData.identity.country);
        if (!currency) {
            throw new Error('Moneda inválida. Selecciona una moneda soportada.');
        }
        if (!country) {
            throw new Error('País inválido. Selecciona un país soportado.');
        }
        const selectedTemplates: FixedCostTemplate[] = onboardingData.fixedCosts?.selectedTemplates || [];
        const nonAmortizableExpenses = selectedTemplates
            .filter((item) => !(item.amortizable || item.category === 'Tools'))
            .map((item) => ({
                name: item.name,
                category: item.category === 'Software' ? 'software' : 'services',
                amount_monthly: String(
                    item.paymentType === 'annual'
                        ? (Number(item.amount || 0) / 12)
                        : Number(item.amount || 0)
                ),
                currency,
                quantity: item.quantity || 1,
            }));
        const inventoryItems = selectedTemplates.map((item) => ({
            id: item.id,
            name: item.name,
            category: item.category,
            amount_monthly: String(
                item.paymentType === 'annual' && !(item.amortizable || item.category === 'Tools')
                    ? (Number(item.amount || 0) / 12)
                    : Number(item.amount || 0)
            ),
            purchase_price: String(item.purchasePrice ?? item.amount ?? 0),
            useful_life_months: item.usefulLifeMonths || (item.category === 'Software' ? 24 : 36),
            salvage_value: String(item.salvageValue || 0),
            purchase_date: item.purchaseDate,
            depreciation_method: item.depreciationMethod || 'straight_line',
            payment_type: item.paymentType || 'monthly',
            currency,
            quantity: item.quantity || 1,
            amortizable: Boolean(item.amortizable || item.category === 'Tools'),
        }));

        const normalizedTeamMembers = (onboardingData.team?.teamMembers || [])
            .filter((member) => member.name && member.role && member.salary > 0)
            .map((member) => ({
                name: member.name,
                role: member.role || 'Generalista',
                salary_monthly_brute: String(member.salary || 0),
                currency,
                billable_hours_per_month: Math.max(1, Math.round((member.billableHours || 28) * 4.33)),
            }));

        const includeSocialCharges = Boolean(onboardingData.team?.applySocialCharges);
        const socialChargesConfig = includeSocialCharges
            ? {
                enable_social_charges: true,
                health_percentage: 8.5,
                pension_percentage: 12.0,
                arl_percentage: 0.522,
                parafiscales_percentage: 4.0,
                prima_services_percentage: 8.33,
                cesantias_percentage: 8.33,
                int_cesantias_percentage: 1.0,
                vacations_percentage: 4.17,
                total_percentage: 52.852,
            }
            : undefined;

        return {
            organization_name: onboardingData.identity.organizationName || undefined,
            country,
            currency,
            profile_type: 'agency',
            team_members: normalizedTeamMembers,
            expenses: nonAmortizableExpenses,
            inventory_items: inventoryItems,
            social_charges_config: socialChargesConfig,
        };
    };

    useEffect(() => {
        const calculate = async () => {
            let payload;
            try {
                payload = buildOnboardingPayload();
            } catch {
                setBackendBcr(null);
                return;
            }
            if (!payload.team_members.length) {
                setBackendBcr(null);
                return;
            }
            setBackendBcrLoading(true);
            const response = await apiRequest<TemporaryBcrResponse>('/onboarding/calculate-bcr', {
                method: 'POST',
                body: JSON.stringify({
                    team_members: payload.team_members,
                    expenses: payload.expenses,
                    inventory_items: payload.inventory_items,
                    social_charges_config: payload.social_charges_config,
                    currency: payload.currency,
                }),
            });
            setBackendBcrLoading(false);
            if (response.error || !response.data?.blended_cost_rate) {
                return;
            }
            const parsed = Number(response.data.blended_cost_rate);
            if (Number.isFinite(parsed)) {
                setBackendBcr(parsed);
            }
        };

        void calculate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [onboardingData.identity, onboardingData.fixedCosts, onboardingData.team]);

    const persistOnboardingInBackend = async (): Promise<boolean> => {
        setPersistError(null);
        let payload;
        try {
            payload = buildOnboardingPayload();
        } catch (error) {
            setPersistError(error instanceof Error ? error.message : 'Datos de onboarding inválidos.');
            return false;
        }
        setPersisting(true);
        const response = await apiRequest('/onboarding/complete', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        setPersisting(false);
        if (response.error) {
            setPersistError(response.error);
            return false;
        }
        updateProgress(4, 'completed');
        return true;
    };

    const handleGoToDashboard = async () => {
        const ok = await persistOnboardingInBackend();
        if (!ok) return;
        trackOnboardingComplete({});
        router.push('/dashboard');
    };

    const handleCreateQuote = async () => {
        const ok = await persistOnboardingInBackend();
        if (!ok) return;
        trackOnboardingComplete({});
        router.push(CANONICAL_NEW_QUOTE_PATH);
    };

    if (authLoading || !isAuthenticated) {
        return (
            <main className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Validando sesión...
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-gray-50 pb-28 md:pb-20">
            {/* Header / Nav */}
            <div className="bg-white border-b border-gray-200 px-4 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <Image
                            src="/brand/Logo-orange.svg"
                            alt="Nougram"
                            width={130}
                            height={30}
                            priority
                        />
                    </div>
                    <span className="text-sm text-gray-500">Configuración Inicial</span>
                </div>
                <div className="max-w-7xl mx-auto mt-2 flex justify-end">
                    <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium border ${
                        saveError
                            ? 'text-red-700 border-red-200 bg-red-50'
                            : isSaving
                                ? 'text-amber-700 border-amber-200 bg-amber-50'
                                : 'text-green-700 border-green-200 bg-green-50'
                    }`}>
                        {saveError ? (
                            <AlertCircle className="h-3.5 w-3.5" />
                        ) : isSaving ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <CheckCircle2 className="h-3.5 w-3.5" />
                        )}
                        <span>
                            {saveError
                                ? 'Error al guardar borrador'
                                : isSaving
                                    ? 'Guardando borrador...'
                                    : lastSavedAt
                                        ? `Guardado ${lastSavedAt.toLocaleTimeString()}`
                                        : 'Borrador listo'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="max-w-5xl mx-auto px-4">
                <div className="mt-6 rounded-xl border border-gray-200 bg-white p-4">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                        <div>
                            <p className="text-sm font-semibold text-gray-900">Importación rápida desde Excel</p>
                            <p className="text-xs text-gray-500">Descarga plantilla, cárgala y aplica el preview sin guardar automáticamente.</p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                            <Button variant="secondary" onClick={handleDownloadTemplate} className="w-full sm:w-auto h-11 rounded-xl font-semibold">
                                Descargar plantilla
                            </Button>
                            <label className="inline-flex items-center justify-center px-4 py-2.5 text-sm font-bold rounded-xl bg-primary text-white hover:opacity-95 cursor-pointer w-full sm:w-auto min-h-11">
                                {importLoading ? 'Procesando...' : 'Cargar Excel'}
                                <input
                                    type="file"
                                    accept=".xlsx"
                                    className="hidden"
                                    onChange={(e) => void handleImportFile(e.target.files?.[0])}
                                    disabled={importLoading}
                                />
                            </label>
                        </div>
                    </div>
                    {importError && (
                        <p className="mt-3 text-sm text-red-600">{importError}</p>
                    )}
                    {importPreview && (
                        <div className="mt-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
                            <p className={`text-sm font-semibold ${importPreview.success ? 'text-green-700' : 'text-amber-700'}`}>
                                {importPreview.success ? 'Preview válido para aplicar' : 'Preview con validaciones pendientes'}
                            </p>
                            {importPreview.temporary_bcr?.blended_cost_rate && (
                                <p className="text-xs text-gray-600 mt-1">
                                    BCR estimado del import: {Number(importPreview.temporary_bcr.blended_cost_rate).toFixed(2)}
                                </p>
                            )}
                            {importPreview.issues.length > 0 && (
                                <div className="mt-2 max-h-40 overflow-auto text-xs text-amber-800 space-y-1">
                                    {importPreview.issues.slice(0, 12).map((issue, index) => (
                                        <p key={`${issue.sheet}-${issue.row}-${issue.field}-${index}`}>
                                            {issue.sheet} fila {issue.row} - {issue.field}: {issue.message}
                                        </p>
                                    ))}
                                </div>
                            )}
                            <div className="mt-3 flex justify-end">
                                <Button
                                    onClick={() => setShowImportReview(true)}
                                    disabled={!importPreview.success || !importPreview.payload}
                                >
                                    Revisar y aplicar
                                </Button>
                            </div>
                        </div>
                    )}
                </div>

                <Dialog open={showImportReview && Boolean(importPreview?.payload)} onOpenChange={setShowImportReview}>
                    <DialogContent className="max-w-3xl w-full max-h-[88vh] overflow-hidden p-0">
                        <div className="p-6 border-b border-gray-100">
                            <DialogHeader>
                                <DialogTitle>Revisión de cambios importados</DialogTitle>
                                <DialogDescription>
                                    Revisa la información detectada antes de aplicarla al onboarding.
                                </DialogDescription>
                            </DialogHeader>
                        </div>
                        {importPreview?.payload && (
                            <div className="p-6 space-y-4 overflow-y-auto">
                                <div className="rounded-lg border border-amber-100 bg-amber-50 p-3">
                                    <p className="font-semibold text-amber-900 text-sm">Delta vs valores actuales</p>
                                    <div className="mt-2 space-y-2">
                                        {buildImportDelta(importPreview.payload).map((row) => (
                                            <div key={row.label} className="rounded border border-amber-100 bg-white p-2">
                                                <div className="flex items-center justify-between gap-2">
                                                    <p className="text-xs font-semibold text-gray-900">{row.label}</p>
                                                    {row.changed ? (
                                                        <span className="text-[10px] font-bold uppercase tracking-wide text-amber-800 bg-amber-100 border border-amber-200 rounded px-2 py-0.5">
                                                            Cambia
                                                        </span>
                                                    ) : (
                                                        <span className="text-[10px] font-bold uppercase tracking-wide text-gray-600 bg-gray-100 border border-gray-200 rounded px-2 py-0.5">
                                                            Igual
                                                        </span>
                                                    )}
                                                </div>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    Actual: <span className="font-medium text-gray-800">{row.current}</span>
                                                </p>
                                                <p className="text-xs text-gray-500">
                                                    Nuevo: <span className="font-medium text-gray-800">{row.next}</span>
                                                </p>
                                                {row.critical && (
                                                    <p className="text-[10px] text-red-700 mt-1">Campo crítico</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                                    <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
                                        <p className="font-semibold text-gray-900 mb-2">Identidad</p>
                                        <div className="flex flex-wrap gap-2 mb-2">
                                            <span className="text-[11px] font-bold uppercase tracking-wide text-amber-700 bg-amber-100 border border-amber-200 rounded px-2 py-0.5">
                                                Campo Crítico
                                            </span>
                                        </div>
                                        <p className="text-gray-700">Organización: {importPreview.payload.organization_name || '(sin nombre)'}</p>
                                        <p className="text-gray-700 mt-1">
                                            País:
                                            <span className="ml-1 inline-flex text-xs font-semibold text-white bg-blue-700 rounded px-2 py-0.5">
                                                {importPreview.payload.country}
                                            </span>
                                        </p>
                                        <p className="text-gray-700 mt-1">
                                            Moneda:
                                            <span className="ml-1 inline-flex text-xs font-semibold text-white bg-indigo-700 rounded px-2 py-0.5">
                                                {importPreview.payload.currency}
                                            </span>
                                        </p>
                                    </div>
                                    <div className="rounded-lg border border-gray-200 bg-white p-3">
                                        <p className="font-semibold text-gray-900 mb-2">Resumen</p>
                                        <p className="text-gray-700">Equipo: {importPreview.payload.team_members.length} miembros</p>
                                        <p className="text-gray-700">Gastos: {importPreview.payload.expenses.length} ítems</p>
                                        <p className="text-gray-700">Inventario: {importPreview.payload.inventory_items.length} ítems</p>
                                    </div>
                                </div>

                                {importPreview.payload.inventory_items.length > 0 && (
                                    <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-3">
                                        <p className="font-semibold text-gray-900 text-sm">Inventario y amortización</p>
                                        <div className="mt-2 space-y-1 text-xs text-gray-700">
                                            {importPreview.payload.inventory_items.slice(0, 8).map((item, idx) => (
                                                <p key={`${item.name}-${idx}`} className="flex flex-wrap items-center gap-1">
                                                    <span>{item.name}</span>
                                                    {item.amortizable ? (
                                                        <span>
                                                            - compra {formatCurrency(item.purchase_price ?? item.amount_monthly ?? 0, importPreview.payload?.currency || 'COP')}
                                                            {' / '}
                                                            vida util {item.useful_life_months ?? 36} meses
                                                        </span>
                                                    ) : (
                                                        <span>
                                                            - mensual {formatCurrency(item.amount_monthly ?? 0, importPreview.payload?.currency || 'COP')}
                                                        </span>
                                                    )}
                                                    {item.amortizable && (
                                                        <span className="inline-flex text-[10px] font-semibold uppercase tracking-wide text-indigo-700 bg-indigo-100 border border-indigo-200 rounded px-2 py-0.5">
                                                            Amortizable
                                                        </span>
                                                    )}
                                                </p>
                                            ))}
                                            {importPreview.payload.inventory_items.length > 8 && (
                                                <p>... y {importPreview.payload.inventory_items.length - 8} más</p>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {importPreview.payload.team_members.length > 0 && (
                                    <div className="rounded-lg border border-gray-200 bg-white p-3">
                                        <p className="font-semibold text-gray-900 text-sm">Equipo (preview)</p>
                                        <div className="mt-2 space-y-1 text-xs text-gray-700">
                                            {importPreview.payload.team_members.slice(0, 8).map((member, idx) => (
                                                <p key={`${member.name}-${idx}`}>
                                                    {member.name} - {member.role} - {formatCurrency(member.salary_monthly_brute, importPreview.payload?.currency || 'COP')}
                                                </p>
                                            ))}
                                            {importPreview.payload.team_members.length > 8 && (
                                                <p>... y {importPreview.payload.team_members.length - 8} más</p>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        <DialogFooter className="p-4 border-t border-gray-100 bg-gray-50">
                            <Button variant="secondary" onClick={() => setShowImportReview(false)}>
                                Cancelar
                            </Button>
                            <Button onClick={() => applyImportedPayload(importPreview?.payload)}>
                                Confirmar y aplicar
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                <OnboardingStepper currentStep={currentStep} />

                <div className="mt-8 transition-all duration-300 ease-in-out">
                    {currentStep === 1 && (
                        <StepIdentity
                            onNext={(data) => {
                                updateIdentity(data);
                                updateProgress(2);
                                handleNext();
                            }}
                            initialData={onboardingData.identity}
                        />
                    )}

                    {currentStep === 2 && (
                        <StepFixedCosts
                            onNext={(data) => {
                                updateFixedCosts(data);
                                updateProgress(3);
                                handleNext();
                            }}
                            onBack={handleBackStep}
                            initialData={onboardingData.fixedCosts}
                            primaryCurrency={onboardingData.identity.primaryCurrency}
                        />
                    )}

                    {currentStep === 3 && (
                        <StepMyTeam
                            onNext={(data) => {
                                updateTeam(data);
                                updateProgress(4);
                                handleNext();
                            }}
                            onBack={handleBackStep}
                            initialData={onboardingData.team}
                            currency={onboardingData.identity.primaryCurrency}
                            backendBcr={backendBcr}
                            backendBcrLoading={backendBcrLoading}
                        />
                    )}

                    {currentStep === 4 && (
                        <StepReady
                            data={onboardingData}
                            backendBcr={backendBcr}
                            backendBcrLoading={backendBcrLoading}
                            persistError={persistError}
                            isPersisting={persisting}
                            onGoToDashboard={handleGoToDashboard}
                            onCreateQuote={handleCreateQuote}
                        />
                    )}
                </div>
            </div>
        </main>
    );
}
