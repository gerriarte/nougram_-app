'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface NumInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value'> {
    value: number | string;
    onChange: (value: number | '') => void;
    prefix?: string;
    suffix?: string;
    className?: string;
}

export function NumInput({ value, onChange, prefix, suffix, className, ...rest }: NumInputProps) {
    return (
        <div
            className={cn(
                'flex h-9 items-center gap-1 rounded-lg border border-gray-200 bg-white px-3 text-sm transition-colors focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/10',
                className
            )}
        >
            {prefix && <span className="select-none text-gray-400 text-xs">{prefix}</span>}
            <input
                type="text"
                inputMode="decimal"
                value={value ?? ''}
                onChange={e => {
                    const raw = e.target.value.replace(/[^\d.]/g, '');
                    onChange(raw === '' ? '' : Number(raw));
                }}
                className="min-w-0 flex-1 bg-transparent tabular-nums outline-none placeholder:text-gray-400"
                {...rest}
            />
            {suffix && <span className="select-none text-gray-400 text-xs">{suffix}</span>}
        </div>
    );
}
