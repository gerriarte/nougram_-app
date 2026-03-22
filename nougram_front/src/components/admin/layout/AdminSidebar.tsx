
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    UsersRound,
    Building2,
    PlusCircle,
    ChevronRight,
    UserCircle2,
    PanelLeftClose,
    PanelLeftOpen,
    ShieldCheck,
    Receipt,
    Calculator,
    BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

interface AdminSidebarProps {
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

export function AdminSidebar({ isCollapsed, onToggleCollapse }: AdminSidebarProps) {
    const pathname = usePathname();
    const { user } = useAuth();

    const MAIN_ITEMS = [
        { label: 'Nueva Cotización', href: '/projects/new', icon: PlusCircle },
    ];

    const allowedOperationalRoles = ['owner', 'admin_financiero', 'super_admin'];
    const showOperationalCosts = user?.role && allowedOperationalRoles.includes(user.role);

    const BUSINESS_ITEMS = [
        { label: 'Dashboard & Pipeline', href: '/dashboard', icon: LayoutDashboard },
        { label: 'Gestión de Clientes', href: '/dashboard/clients', icon: UserCircle2 },
        { label: 'Nómina (Equipo)', href: '/admin/payroll', icon: UsersRound },
        { label: 'Capacidad del Equipo', href: '/dashboard/resources/availability', icon: BarChart3 },
        { label: 'Inventario de Gastos', href: '/admin/overhead', icon: Building2 },
        { label: 'Impuestos', href: '/admin/taxes', icon: Receipt },
        ...(showOperationalCosts
            ? [{ label: 'Costo operacional', href: '/dashboard/operational-costs', icon: Calculator }]
            : []),
    ];

    return (
        <aside className={cn(
            "bg-white/70 backdrop-blur-xl border-r border-white/20 min-h-screen flex flex-col z-20 hidden md:flex sticky top-0 transition-all duration-300",
            isCollapsed ? "w-24" : "w-72"
        )}>
            <div className={cn("pb-8", isCollapsed ? "p-4" : "p-8")}>
                <div className={cn("mb-1", isCollapsed ? "flex justify-center" : "flex items-center gap-3")}>
                    <Image
                        src={isCollapsed ? "/brand/Logo-iso-orange.svg" : "/brand/Logo-orange.svg"}
                        alt="Nougram"
                        width={isCollapsed ? 36 : 130}
                        height={30}
                        priority
                    />
                </div>
                <div className={cn("mt-4", isCollapsed ? "flex justify-center" : "flex justify-end")}>
                    <button
                        type="button"
                        onClick={onToggleCollapse}
                        className="h-9 w-9 rounded-xl border border-gray-200 bg-white text-system-gray hover:text-secondary hover:border-secondary/30 transition-colors flex items-center justify-center"
                        aria-label={isCollapsed ? 'Expandir menú lateral' : 'Colapsar menú lateral'}
                        title={isCollapsed ? 'Expandir menú lateral' : 'Colapsar menú lateral'}
                    >
                        {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
                    </button>
                </div>
            </div>

            <nav className={cn("flex-1 space-y-8", isCollapsed ? "px-2" : "px-4")}>
                {/* Main Action */}
                <div className="space-y-1.5">
                    {!isCollapsed && (
                        <p className="px-4 text-[10px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">Principal</p>
                    )}
                    {MAIN_ITEMS.map(item => (
                        <Link
                            key={item.href}
                            href={item.href}
                            title={item.label}
                            className={cn(
                                "flex items-center justify-between px-4 py-3 rounded-2xl text-[13px] font-bold transition-all group",
                                pathname.startsWith(item.href)
                                    ? "bg-primary text-white shadow-lg"
                                    : "text-gray-600 hover:bg-white hover:shadow-sm",
                                isCollapsed && "justify-center px-0"
                            )}
                        >
                            <div className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-3")}>
                                <item.icon size={18} strokeWidth={pathname.startsWith(item.href) ? 2.5 : 1.5} />
                                {!isCollapsed && <span>{item.label}</span>}
                            </div>
                            {!isCollapsed && !pathname.startsWith(item.href) && <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />}
                        </Link>
                    ))}
                </div>

                {/* Business Config */}
                <div className="space-y-1.5">
                    {!isCollapsed && (
                        <p className="px-4 text-[10px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">Negocio</p>
                    )}
                    {BUSINESS_ITEMS.map(item => {
                        const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                title={item.label}
                                className={cn(
                                    "flex items-center justify-between px-4 py-3 rounded-2xl text-[13px] font-bold transition-all group",
                                    isActive
                                    ? "bg-accent/70 text-secondary ring-1 ring-accent"
                                        : "text-gray-600 hover:bg-white hover:shadow-sm",
                                    isCollapsed && "justify-center px-0"
                                )}
                            >
                                <div className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-3")}>
                                    <item.icon size={18} strokeWidth={isActive ? 2 : 1.5} className={isActive ? "text-secondary" : "text-system-gray"} />
                                    {!isCollapsed && <span>{item.label}</span>}
                                </div>
                                {!isCollapsed && isActive && <div className="w-1.5 h-1.5 rounded-full bg-secondary" />}
                                {!isCollapsed && !isActive && <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />}
                            </Link>
                        );
                    })}
                </div>

                {user?.role === 'super_admin' && (
                    <div className="space-y-1.5">
                        {!isCollapsed && (
                            <p className="px-4 text-[10px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">Super Admin</p>
                        )}
                        <Link
                            href="/dashboard/super-admin/accounts"
                            title="Control de Cuentas"
                            className={cn(
                                "flex items-center justify-between px-4 py-3 rounded-2xl text-[13px] font-bold transition-all group",
                                pathname === '/dashboard/super-admin/accounts' || pathname.startsWith('/dashboard/super-admin/accounts/')
                                    ? "bg-accent/70 text-secondary ring-1 ring-accent"
                                    : "text-gray-600 hover:bg-white hover:shadow-sm",
                                isCollapsed && "justify-center px-0"
                            )}
                        >
                            <div className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-3")}>
                                <ShieldCheck
                                    size={18}
                                    strokeWidth={2}
                                    className={(pathname === '/dashboard/super-admin/accounts' || pathname.startsWith('/dashboard/super-admin/accounts/'))
                                        ? "text-secondary"
                                        : "text-system-gray"}
                                />
                                {!isCollapsed && <span>Control de Cuentas</span>}
                            </div>
                            {!isCollapsed && !(pathname === '/dashboard/super-admin/accounts' || pathname.startsWith('/dashboard/super-admin/accounts/')) && (
                                <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
                            )}
                        </Link>
                    </div>
                )}

            </nav>

        </aside>
    );
}
