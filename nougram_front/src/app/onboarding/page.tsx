
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { OnboardingStepper } from '@/components/onboarding/OnboardingStepper';
import { StepIdentity } from '@/components/onboarding/StepIdentity';
import { StepFixedCosts } from '@/components/onboarding/StepFixedCosts';
import { StepMyTeam } from '@/components/onboarding/StepMyTeam';
import { StepReady } from '@/components/onboarding/StepReady';
import { useOnboarding } from '@/hooks/useOnboarding';
import { apiRequest } from '@/lib/api-client';
import { FixedCostTemplate } from '@/types/onboarding';

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

export default function OnboardingPage() {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState(1);
    const [persistError, setPersistError] = useState<string | null>(null);
    const [persisting, setPersisting] = useState(false);
    const [backendBcr, setBackendBcr] = useState<number | null>(null);
    const [backendBcrLoading, setBackendBcrLoading] = useState(false);

    // Use the hook for state management
    const {
        data: onboardingData,
        updateIdentity,
        updateFixedCosts,
        updateTeam
    } = useOnboarding();

    const handleNext = () => {
        setCurrentStep((prev) => prev + 1);
        window.scrollTo(0, 0);
    };

    const handleBackStep = () => {
        setCurrentStep((prev) => Math.max(1, prev - 1));
        window.scrollTo(0, 0);
    };

    const buildOnboardingPayload = () => {
        const currency = onboardingData.identity.primaryCurrency || 'COP';
        const country = onboardingData.identity.country || 'COL';
        const selectedTemplates: FixedCostTemplate[] = onboardingData.fixedCosts?.selectedTemplates || [];
        const nonAmortizableExpenses = selectedTemplates
            .filter((item) => !(item.amortizable || item.category === 'Tools'))
            .map((item) => ({
                name: item.name,
                category: item.category === 'Software' ? 'software' : 'services',
                amount_monthly: String(item.amount || 0),
                currency: item.currency || currency,
                quantity: item.quantity || 1,
            }));
        const inventoryItems = selectedTemplates.map((item) => ({
            id: item.id,
            name: item.name,
            category: item.category,
            amount_monthly: String(item.amount || 0),
            currency: item.currency || currency,
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
        const payload = buildOnboardingPayload();
        if (!payload.team_members.length) {
            setBackendBcr(null);
            return;
        }

        const calculate = async () => {
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
        const alreadyPersisted = localStorage.getItem('nougram_onboarding_persisted_v1') === 'true';
        if (alreadyPersisted) {
            return true;
        }
        setPersistError(null);
        setPersisting(true);
        const response = await apiRequest('/onboarding/complete', {
            method: 'POST',
            body: JSON.stringify(buildOnboardingPayload()),
        });
        setPersisting(false);
        if (response.error) {
            setPersistError(response.error);
            return false;
        }
        localStorage.setItem('nougram_onboarding_persisted_v1', 'true');
        return true;
    };

    const handleGoToDashboard = async () => {
        const ok = await persistOnboardingInBackend();
        if (!ok) return;
        router.push('/dashboard');
    };

    const handleCreateQuote = async () => {
        const ok = await persistOnboardingInBackend();
        if (!ok) return;
        router.push('/projects/new');
    };

    return (
        <main className="min-h-screen bg-gray-50 pb-20">
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
                        <p className="text-[10px] font-black text-system-gray uppercase tracking-[0.2em]">
                            Business OS
                        </p>
                    </div>
                    <span className="text-sm text-gray-500">Configuración Inicial</span>
                </div>
            </div>

            <div className="max-w-5xl mx-auto px-4">
                <OnboardingStepper currentStep={currentStep} />

                <div className="mt-8 transition-all duration-300 ease-in-out">
                    {currentStep === 1 && (
                        <StepIdentity
                            onNext={(data) => {
                                updateIdentity(data);
                                handleNext();
                            }}
                            initialData={onboardingData.identity}
                        />
                    )}

                    {currentStep === 2 && (
                        <StepFixedCosts
                            onNext={(data) => {
                                updateFixedCosts(data);
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
