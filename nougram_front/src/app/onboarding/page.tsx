
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { OnboardingStepper } from '@/components/onboarding/OnboardingStepper';
import { StepIdentity } from '@/components/onboarding/StepIdentity';
import { StepFixedCosts } from '@/components/onboarding/StepFixedCosts';
import { StepMyTeam } from '@/components/onboarding/StepMyTeam';
import { StepReady } from '@/components/onboarding/StepReady';
import { useOnboarding } from '@/hooks/useOnboarding';
import { apiRequest } from '@/lib/api-client';
import { FixedCostTemplate } from '@/types/onboarding';

export default function OnboardingPage() {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState(1);
    const [persistError, setPersistError] = useState<string | null>(null);
    const [persisting, setPersisting] = useState(false);

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

        return {
            organization_name: onboardingData.identity.organizationName || undefined,
            country,
            currency,
            profile_type: 'agency',
            team_members: normalizedTeamMembers,
            expenses: nonAmortizableExpenses,
            inventory_items: inventoryItems,
        };
    };

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
                <div className="max-w-7xl mx-auto flex items-center gap-2">
                    <span className="font-bold text-xl text-blue-600">Nougram</span>
                    <span className="text-gray-300">|</span>
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
                        />
                    )}

                    {currentStep === 4 && (
                        <StepReady
                            data={onboardingData}
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
