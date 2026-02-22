
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { OnboardingStepper } from '@/components/onboarding/OnboardingStepper';
import { StepIdentity } from '@/components/onboarding/StepIdentity';
import { StepFixedCosts } from '@/components/onboarding/StepFixedCosts';
import { StepMyTeam } from '@/components/onboarding/StepMyTeam';
import { StepReady } from '@/components/onboarding/StepReady';
import { useOnboarding } from '@/hooks/useOnboarding';

export default function OnboardingPage() {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState(1);

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

    const handleGoToDashboard = () => {
        router.push('/dashboard');
    };

    const handleCreateQuote = () => {
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
                            onGoToDashboard={handleGoToDashboard}
                            onCreateQuote={handleCreateQuote}
                        />
                    )}
                </div>
            </div>
        </main>
    );
}
