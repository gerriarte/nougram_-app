
import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OnboardingStepperProps {
    currentStep: number;
    maxReachedStep?: number;
    onStepClick?: (step: number) => void;
}

const steps = [
    { id: 1, label: 'Identidad', sub: 'Sobre tu empresa' },
    { id: 2, label: 'Inventario', sub: 'Gastos operativos' },
    { id: 3, label: 'Mi Equipo', sub: 'Nómina y horas' },
    { id: 4, label: 'Listo', sub: 'Tu costo por hora' },
];

export function OnboardingStepper({ currentStep, maxReachedStep = currentStep, onStepClick }: OnboardingStepperProps) {
    const progress = (currentStep / steps.length) * 100;

    return (
        <div className="w-full border-b border-gray-100 bg-white/80 py-5 backdrop-blur">
            <div className="mx-auto max-w-4xl space-y-3 px-1 md:space-y-4">
                <div className="relative h-1 w-full overflow-hidden rounded-full bg-gray-100">
                    <div
                        className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                <div className="flex gap-2 overflow-x-auto pb-1 snap-x snap-mandatory md:grid md:grid-cols-4 md:overflow-visible scrollbar-hide">
                    {steps.map((step) => {
                        const isCompleted = currentStep > step.id;
                        const isActive = currentStep === step.id;
                        const isReachable = step.id <= maxReachedStep;
                        const clickable = Boolean(onStepClick && isReachable && !isActive);

                        return (
                            <button
                                key={step.id}
                                type="button"
                                disabled={!clickable}
                                onClick={() => clickable && onStepClick?.(step.id)}
                                className={cn(
                                    'flex min-w-[8rem] shrink-0 snap-center items-center gap-2 rounded-2xl px-2.5 py-2 text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/25 md:min-w-0 md:justify-center',
                                    isActive && 'bg-primary-soft',
                                    clickable ? 'cursor-pointer hover:bg-gray-50' : 'cursor-default',
                                    !isReachable && 'opacity-55'
                                )}
                            >
                                <div
                                    className={cn(
                                        'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold transition-all duration-300',
                                        isCompleted
                                            ? 'border-primary bg-primary text-white'
                                            : isActive
                                                ? 'border-primary bg-primary text-white'
                                                : 'border-gray-200 bg-white text-gray-400'
                                    )}
                                >
                                    {isCompleted ? (
                                        <Check size={13} strokeWidth={3} />
                                    ) : (
                                        step.id
                                    )}
                                </div>
                                <div className="min-w-0">
                                    <div className={cn('text-[12px] font-bold leading-tight', isCompleted || isActive ? 'text-primary' : 'text-gray-600')}>
                                        {step.label}
                                    </div>
                                    <div className="mt-0.5 truncate text-[10.5px] text-gray-400">{step.sub}</div>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
