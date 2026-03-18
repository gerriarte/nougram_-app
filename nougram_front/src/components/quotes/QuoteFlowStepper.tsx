'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export type QuoteFlowStep = {
  id: number;
  title: string;
};

interface QuoteFlowStepperProps {
  steps: QuoteFlowStep[];
  currentStepId: number;
  label?: string;
  className?: string;
  gridClassName?: string;
  showMobileProgress?: boolean;
  mobileProgressPercent?: number;
  onStepClick?: (stepId: number) => void;
}

export function QuoteFlowStepper({
  steps,
  currentStepId,
  label,
  className,
  gridClassName = 'grid grid-cols-1 sm:grid-cols-3 gap-2',
  showMobileProgress = false,
  mobileProgressPercent = 0,
  onStepClick,
}: QuoteFlowStepperProps) {
  return (
    <div className={className}>
      {label && (
        <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2">
          {label}
        </p>
      )}

      <div className={gridClassName}>
        {steps.map((step) => (
          <button
            key={step.id}
            type="button"
            onClick={() => onStepClick?.(step.id)}
            disabled={!onStepClick}
            className={cn(
              'w-full text-left rounded-xl border px-3 py-2 transition-colors',
              onStepClick ? 'cursor-pointer hover:border-blue-200 hover:bg-blue-50/40' : 'cursor-default',
              currentStepId === step.id
                ? 'border-blue-100 bg-blue-50'
                : currentStepId > step.id
                  ? 'border-emerald-100 bg-emerald-50'
                  : 'border-gray-200 bg-white'
            )}
          >
            <p
              className={cn(
                'text-[10px] font-black uppercase tracking-wider',
                currentStepId === step.id
                  ? 'text-blue-700'
                  : currentStepId > step.id
                    ? 'text-emerald-700'
                    : 'text-gray-500'
              )}
            >
              Paso {step.id}
            </p>
            <p
              className={cn(
                'text-xs font-semibold',
                currentStepId === step.id
                  ? 'text-blue-900'
                  : currentStepId > step.id
                    ? 'text-emerald-900'
                    : 'text-gray-700'
              )}
            >
              {step.title}
            </p>
          </button>
        ))}
      </div>

      {showMobileProgress && (
        <div className="h-1 bg-gray-200 w-full md:hidden mt-3">
          <div
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${Math.max(0, Math.min(100, mobileProgressPercent))}%` }}
          />
        </div>
      )}
    </div>
  );
}
