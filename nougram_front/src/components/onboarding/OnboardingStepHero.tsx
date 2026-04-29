import React from 'react';
import { cn } from '@/lib/utils';

type OnboardingStepHeroProps = {
    eyebrow: string;
    title: string;
    description: string;
    callout?: string;
    align?: 'center' | 'left';
};

export function OnboardingStepHero({
    eyebrow,
    title,
    description,
    callout,
    align = 'center',
}: OnboardingStepHeroProps) {
    return (
        <div className={cn('mx-auto max-w-3xl px-1', align === 'center' ? 'text-center' : 'text-left')}>
            <div className="inline-flex rounded-full bg-primary-soft px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-primary">
                {eyebrow}
            </div>
            <h1 className="mt-4 text-2xl font-black tracking-tight text-gray-950 sm:text-3xl">
                {title}
            </h1>
            <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-gray-600 sm:text-base">
                {description}
            </p>
            {callout && (
                <div className="mx-auto mt-5 max-w-2xl rounded-2xl border border-primary/10 bg-white px-4 py-3 text-sm text-gray-600 shadow-sm">
                    {callout}
                </div>
            )}
        </div>
    );
}
