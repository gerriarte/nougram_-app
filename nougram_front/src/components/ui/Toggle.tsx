'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ToggleProps {
    checked: boolean;
    onChange: (value: boolean) => void;
    disabled?: boolean;
    className?: string;
}

export function Toggle({ checked, onChange, disabled, className }: ToggleProps) {
    return (
        <button
            type="button"
            role="switch"
            aria-checked={checked}
            disabled={disabled}
            onClick={() => onChange(!checked)}
            className={cn(
                'relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                checked ? 'bg-primary' : 'bg-gray-200',
                className
            )}
        >
            <span
                className={cn(
                    'pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm ring-0 transition-transform duration-150',
                    checked ? 'translate-x-4' : 'translate-x-0'
                )}
            />
        </button>
    );
}
