
import React from 'react';

interface OnboardingStepperProps {
    currentStep: number;
}

const steps = [
    { id: 1, label: 'Identidad' },
    { id: 2, label: 'Mis Costos' },
    { id: 3, label: 'Mi Equipo' },
    { id: 4, label: '¡Listo!' },
];

export function OnboardingStepper({ currentStep }: OnboardingStepperProps) {
    return (
        <div className="w-full py-6">
            <div className="relative flex items-center justify-between w-full max-w-3xl mx-auto">
                {/* Connecting Lines */}
                <div className="absolute top-1/2 left-0 w-full h-1 bg-gray-200 -z-10 transform -translate-y-1/2 rounded-full"></div>
                <div
                    className="absolute top-1/2 left-0 h-1 bg-blue-500 -z-10 transform -translate-y-1/2 rounded-full transition-all duration-500 ease-in-out"
                    style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
                ></div>

                {steps.map((step) => {
                    const isCompleted = currentStep > step.id;
                    const isActive = currentStep === step.id;

                    return (
                        <div key={step.id} className="flex flex-col items-center bg-white px-2">
                            <div
                                className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors duration-300 ${isActive
                                        ? 'border-blue-500 bg-white text-blue-500'
                                        : isCompleted
                                            ? 'border-blue-500 bg-blue-500 text-white'
                                            : 'border-gray-300 bg-white text-gray-300'
                                    }`}
                            >
                                {isCompleted ? (
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                ) : (
                                    <span className={`text-sm font-semibold ${isActive ? 'text-blue-600' : ''}`}>
                                        {isActive ? '●' : '○'}
                                    </span>
                                )}
                            </div>
                            <span
                                className={`mt-2 text-xs font-medium transition-colors duration-300 ${isActive || isCompleted ? 'text-blue-600' : 'text-gray-400'
                                    }`}
                            >
                                {step.label}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
