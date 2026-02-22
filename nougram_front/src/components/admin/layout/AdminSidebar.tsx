
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    Scale,
    UsersRound,
    Building2,
    Zap,
    PlusCircle,
    ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function AdminSidebar() {
    const pathname = usePathname();

    const MAIN_ITEMS = [
        { label: 'Nueva Cotización', href: '/projects/new', icon: PlusCircle },
    ];

    const BUSINESS_ITEMS = [
        { label: 'Dashboard & Pipeline', href: '/dashboard', icon: LayoutDashboard },
        { label: 'Punto de Equilibrio', href: '/analytics/break-even', icon: Scale },
        { label: 'Nómina (Equipo)', href: '/admin/payroll', icon: UsersRound },
        { label: 'Overhead (Gastos)', href: '/admin/overhead', icon: Building2 },
        { label: 'Quick Selects', href: '/admin/quick-selects', icon: Zap },
    ];

    return (
        <aside className="w-72 bg-white/70 backdrop-blur-xl border-r border-white/20 min-h-screen flex flex-col z-20 hidden md:flex sticky top-0">
            <div className="p-8 pb-10">
                <div className="flex items-center gap-3 mb-1">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <div className="w-4 h-4 bg-white/20 rounded-sm rotate-45" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 tracking-tighter">Nougram</h1>
                </div>
                <p className="text-[10px] font-black text-system-gray uppercase tracking-[0.2em] ml-11">Business OS</p>
            </div>

            <nav className="flex-1 px-4 space-y-8">
                {/* Main Action */}
                <div className="space-y-1.5">
                    <p className="px-4 text-[10px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">Principal</p>
                    {MAIN_ITEMS.map(item => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center justify-between px-4 py-3 rounded-2xl text-[13px] font-bold transition-all group",
                                pathname.startsWith(item.href)
                                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                                    : "text-gray-600 hover:bg-white hover:shadow-sm"
                            )}
                        >
                            <div className="flex items-center gap-3">
                                <item.icon size={18} strokeWidth={pathname.startsWith(item.href) ? 2.5 : 1.5} />
                                <span>{item.label}</span>
                            </div>
                            {!pathname.startsWith(item.href) && <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />}
                        </Link>
                    ))}
                </div>

                {/* Business Config */}
                <div className="space-y-1.5">
                    <p className="px-4 text-[10px] font-black text-system-gray uppercase tracking-[0.15em] mb-3">Negocio</p>
                    {BUSINESS_ITEMS.map(item => {
                        const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={cn(
                                    "flex items-center justify-between px-4 py-3 rounded-2xl text-[13px] font-bold transition-all group",
                                    isActive
                                        ? "bg-blue-50/50 text-blue-600 ring-1 ring-blue-100/50"
                                        : "text-gray-600 hover:bg-white hover:shadow-sm"
                                )}
                            >
                                <div className="flex items-center gap-3">
                                    <item.icon size={18} strokeWidth={isActive ? 2 : 1.5} className={isActive ? "text-blue-600" : "text-system-gray"} />
                                    <span>{item.label}</span>
                                </div>
                                {isActive && <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />}
                                {!isActive && <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />}
                            </Link>
                        );
                    })}
                </div>
            </nav>

            <div className="p-6 m-4 mt-auto rounded-3xl bg-gray-200/30 backdrop-blur-sm border border-white/40">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
                        JD
                    </div>
                    <div className="min-w-0">
                        <p className="text-[13px] font-bold text-gray-900 truncate tracking-tight">Usuario Demo</p>
                        <p className="text-[11px] font-medium text-system-gray truncate">Owner</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
