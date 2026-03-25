
import React from 'react';

interface OnboardingStepperProps {
    currentStep: number;
}

const steps = [
    { id: 1, label: 'Identidad' },
    { id: 2, label: 'Inventario' },
    { id: 3, label: 'Mi Equipo' },
    { id: 4, label: '¡Listo!' },
];

export function OnboardingStepper({ currentStep }: OnboardingStepperProps) {
    const progress = ((currentStep - 1) / (steps.length - 1)) * 100;

    return (
        <div className="w-full py-4 md:py-6">
            <div className="max-w-4xl mx-auto space-y-3 md:space-y-4 px-1">
                <div className="relative h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                    <div
                        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                <div className="flex gap-2 overflow-x-auto pb-1 snap-x snap-mandatory md:grid md:grid-cols-4 md:overflow-visible scrollbar-hide">
                    {steps.map((step) => {
                        const isCompleted = currentStep > step.id;
                        const isActive = currentStep === step.id;

                        return (
                            <div
                                key={step.id}
                                className="flex flex-col items-center text-center min-w-[4.5rem] snap-center shrink-0 md:min-w-0"
                            >
                                <div
                                    className={`flex items-center justify-center w-9 h-9 rounded-full border-2 shadow-sm transition-all duration-300 ${
                                        isCompleted
                                            ? 'bg-blue-600 border-blue-600 text-white'
                                            : isActive
                                                ? 'bg-blue-50 border-blue-500 text-blue-700'
                                                : 'bg-white border-gray-300 text-gray-400'
                                    }`}
                                >
                                    {isCompleted ? (
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : (
                                        <span className="text-xs font-semibold">{step.id}</span>
                                    )}
                                </div>
                                <span
                                    className={`mt-1.5 text-[10px] md:text-xs font-semibold max-w-[5.5rem] leading-tight ${
                                        isCompleted || isActive ? 'text-blue-700' : 'text-gray-500'
                                    }`}
                                >
                                    {step.label}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
