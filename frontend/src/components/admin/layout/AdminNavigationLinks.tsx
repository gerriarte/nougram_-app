'use client';

import React from 'react';
import Link from 'next/link';
import {
  LayoutDashboard,
  UsersRound,
  Building2,
  PlusCircle,
  ChevronRight,
  UserCircle2,
  ShieldCheck,
  Receipt,
  Calculator,
  BarChart3,
  Truck,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { UserProfileExtended } from '@/types/user';
import { CANONICAL_NEW_QUOTE_PATH } from '@/lib/mobile-routes';
import { useNougram } from '@/context/NougramCoreContext';

export type AdminNavItem = { label: string; href: string; icon: LucideIcon };

type AdminNavigationLinksProps = {
  pathname: string;
  user: UserProfileExtended | null;
  isCollapsed: boolean;
  /** Close mobile drawer after navigation */
  onNavigate?: () => void;
  variant?: 'sidebar' | 'drawer';
};

export function AdminNavigationLinks({
  pathname,
  user,
  isCollapsed,
  onNavigate,
  variant = 'sidebar',
}: AdminNavigationLinksProps) {
  const allowedOperationalRoles = ['owner', 'admin_financiero', 'super_admin'];
  const showOperationalCosts = user?.role && allowedOperationalRoles.includes(user.role);
  const { state } = useNougram();
  const quoteAgentEnabled = state.features.quoteAgentEnabled;

  const MAIN_ITEMS: AdminNavItem[] = [
    { label: 'Nueva Cotización', href: CANONICAL_NEW_QUOTE_PATH, icon: PlusCircle },
    ...(quoteAgentEnabled
      ? [{ label: 'Cotizar con IA ✨', href: '/dashboard/quotes/agent', icon: Sparkles }]
      : []),
  ];

  const BUSINESS_ITEMS: AdminNavItem[] = [
    { label: 'Dashboard & Pipeline', href: '/dashboard', icon: LayoutDashboard },
    { label: 'Gestión de Clientes', href: '/dashboard/clients', icon: UserCircle2 },
    { label: 'Nómina (Equipo)', href: '/admin/payroll', icon: UsersRound },
    { label: 'Capacidad del Equipo', href: '/dashboard/resources/availability', icon: BarChart3 },
    { label: 'Inventario de Gastos', href: '/admin/overhead', icon: Building2 },
    { label: 'Impuestos', href: '/admin/taxes', icon: Receipt },
    { label: 'Proveedores', href: '/admin/vendors', icon: Truck },
    ...(showOperationalCosts
      ? [{ label: 'Costo operacional', href: '/dashboard/operational-costs', icon: Calculator }]
      : []),
  ];

  const sectionTitle = (text: string) =>
    !isCollapsed ? (
      <p className="px-4 text-[10px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">{text}</p>
    ) : null;

  const linkWrapClass =
    variant === 'drawer'
      ? 'rounded-2xl text-[14px]'
      : 'rounded-2xl text-[13px]';

  return (
    <>
      <div className="space-y-1.5">
        {sectionTitle('Principal')}
        {MAIN_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            title={item.label}
            onClick={onNavigate}
            className={cn(
              'flex items-center justify-between px-4 py-3 font-bold transition-all group',
              linkWrapClass,
              pathname.startsWith(item.href)
                ? 'bg-primary text-white shadow-lg'
                : 'text-gray-600 hover:bg-white hover:shadow-sm',
              isCollapsed && 'justify-center px-0'
            )}
          >
            <div className={cn('flex items-center', isCollapsed ? 'justify-center' : 'gap-3')}>
              <item.icon size={18} strokeWidth={pathname.startsWith(item.href) ? 2.5 : 1.5} />
              {!isCollapsed && <span>{item.label}</span>}
            </div>
            {!isCollapsed && !pathname.startsWith(item.href) && (
              <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
            )}
          </Link>
        ))}
      </div>

      <div className="space-y-1.5">
        {sectionTitle('Negocio')}
        {BUSINESS_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              onClick={onNavigate}
              className={cn(
                'flex items-center justify-between px-4 py-3 font-bold transition-all group',
                linkWrapClass,
                isActive
                  ? 'bg-accent/70 text-secondary ring-1 ring-accent'
                  : 'text-gray-600 hover:bg-white hover:shadow-sm',
                isCollapsed && 'justify-center px-0'
              )}
            >
              <div className={cn('flex items-center', isCollapsed ? 'justify-center' : 'gap-3')}>
                <item.icon
                  size={18}
                  strokeWidth={isActive ? 2 : 1.5}
                  className={isActive ? 'text-secondary' : 'text-system-gray'}
                />
                {!isCollapsed && <span>{item.label}</span>}
              </div>
              {!isCollapsed && isActive && <div className="w-1.5 h-1.5 rounded-full bg-secondary" />}
              {!isCollapsed && !isActive && (
                <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
              )}
            </Link>
          );
        })}
      </div>

      {user?.role === 'super_admin' && (
        <div className="space-y-1.5">
          {sectionTitle('Super Admin')}
          <Link
            href="/dashboard/super-admin/accounts"
            title="Control de Cuentas"
            onClick={onNavigate}
            className={cn(
              'flex items-center justify-between px-4 py-3 font-bold transition-all group',
              linkWrapClass,
              pathname === '/dashboard/super-admin/accounts' || pathname.startsWith('/dashboard/super-admin/accounts/')
                ? 'bg-accent/70 text-secondary ring-1 ring-accent'
                : 'text-gray-600 hover:bg-white hover:shadow-sm',
              isCollapsed && 'justify-center px-0'
            )}
          >
            <div className={cn('flex items-center', isCollapsed ? 'justify-center' : 'gap-3')}>
              <ShieldCheck
                size={18}
                strokeWidth={2}
                className={
                  pathname === '/dashboard/super-admin/accounts' ||
                  pathname.startsWith('/dashboard/super-admin/accounts/')
                    ? 'text-secondary'
                    : 'text-system-gray'
                }
              />
              {!isCollapsed && <span>Control de Cuentas</span>}
            </div>
            {!isCollapsed &&
              !(
                pathname === '/dashboard/super-admin/accounts' ||
                pathname.startsWith('/dashboard/super-admin/accounts/')
              ) && (
                <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
              )}
          </Link>
        </div>
      )}
    </>
  );
}
