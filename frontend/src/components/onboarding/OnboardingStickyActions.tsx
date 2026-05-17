'use client';

import React from 'react';
import { cn } from '@/lib/utils';

/**
 * Mobile-first sticky action bar (Material-style bottom sheet edge).
 * On md+ screens, children render in normal flow (caller should use md:static wrapper).
 */
export function OnboardingStickyActions({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'fixed inset-x-0 bottom-0 z-40 md:static md:z-auto border-t border-gray-200/90 bg-white/95 backdrop-blur-md',
        'shadow-[0_-6px_24px_rgba(15,23,42,0.06)] md:shadow-none md:border-0 md:bg-transparent md:backdrop-blur-none',
        'px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] md:p-0',
        className
      )}
    >
      <div className="max-w-2xl mx-auto w-full">{children}</div>
    </div>
  );
}
