'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, ClipboardList, PlusCircle, Menu } from 'lucide-react';
import { cn } from '@/lib/utils';
import { CANONICAL_NEW_QUOTE_PATH } from '@/lib/mobile-routes';

type MobileBottomNavProps = {
  onOpenMenu: () => void;
};

export function MobileBottomNav({ onOpenMenu }: MobileBottomNavProps) {
  const pathname = usePathname() || '';

  const items: Array<{
    href: string;
    label: string;
    icon: typeof LayoutDashboard;
    match: (p: string) => boolean;
  }> = [
    {
      href: '/dashboard',
      label: 'Inicio',
      icon: LayoutDashboard,
      match: (p) => p === '/dashboard' || p === '/dashboard/',
    },
    {
      href: '/dashboard/quotes',
      label: 'Cotizaciones',
      icon: ClipboardList,
      match: (p) => p.startsWith('/dashboard/quotes') && !p.startsWith(CANONICAL_NEW_QUOTE_PATH),
    },
    {
      href: CANONICAL_NEW_QUOTE_PATH,
      label: 'Nueva',
      icon: PlusCircle,
      match: (p) => p.startsWith(CANONICAL_NEW_QUOTE_PATH),
    },
  ];

  return (
    <nav
      className="fixed bottom-0 inset-x-0 z-50 md:hidden border-t border-slate-200/80 bg-white/95 backdrop-blur-md pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 px-2 shadow-[0_-8px_30px_rgba(15,23,42,0.08)]"
      aria-label="Navegación principal"
    >
      <div className="flex items-stretch justify-around max-w-lg mx-auto gap-1">
        {items.map(({ href, label, icon: Icon, match }) => {
          const active = match(pathname);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex flex-1 flex-col items-center justify-center gap-0.5 py-2 rounded-2xl min-h-[52px] transition-colors',
                active ? 'text-primary bg-primary/8' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
              )}
            >
              <Icon size={22} strokeWidth={active ? 2.25 : 1.75} aria-hidden />
              <span className="text-[10px] font-bold tracking-tight">{label}</span>
            </Link>
          );
        })}
        <button
          type="button"
          onClick={onOpenMenu}
          className="flex flex-1 flex-col items-center justify-center gap-0.5 py-2 rounded-2xl min-h-[52px] text-slate-500 hover:text-slate-800 hover:bg-slate-50"
        >
          <Menu size={22} strokeWidth={1.75} aria-hidden />
          <span className="text-[10px] font-bold tracking-tight">Más</span>
        </button>
      </div>
    </nav>
  );
}
