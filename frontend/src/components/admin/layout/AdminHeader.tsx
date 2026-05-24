
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Users, LogOut, ChevronDown, ChevronRight, Building2, CreditCard, Menu, HelpCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { HelpPanel } from './HelpPanel';

type AdminHeaderProps = {
    onOpenMobileNav?: () => void;
    workspaceName?: string;
};

type Breadcrumb = {
    label: string;
    href?: string;
};

function getBreadcrumbs(pathname: string): Breadcrumb[] {
    if (pathname === '/dashboard' || pathname === '/dashboard/') {
        return [{ label: 'Dashboard' }];
    }

    if (pathname === '/dashboard/quotes/create') {
        return [
            { label: 'Dashboard', href: '/dashboard' },
            { label: 'Cotizaciones', href: '/dashboard/quotes' },
            { label: 'Nueva cotización' },
        ];
    }

    const quoteMatch = pathname.match(/^\/dashboard\/quotes\/([^/]+)(?:\/([^/]+))?/);
    if (quoteMatch) {
        const quoteId = quoteMatch[1];
        const section = quoteMatch[2] || 'edit';
        const sectionLabels: Record<string, string> = {
            edit: 'Editar cotización',
            proposal: 'Propuesta',
            send: 'Envío',
            tracking: 'Seguimiento',
            'next-step': 'Siguiente paso',
        };

        return [
            { label: 'Dashboard', href: '/dashboard' },
            { label: 'Cotizaciones', href: '/dashboard/quotes' },
            { label: sectionLabels[section] || 'Cotización', href: `/dashboard/quotes/${quoteId}/edit` },
        ];
    }

    if (pathname.startsWith('/dashboard/clients')) {
        return [{ label: 'Dashboard', href: '/dashboard' }, { label: 'Clientes' }];
    }
    if (pathname.startsWith('/dashboard/resources/availability')) {
        return [{ label: 'Dashboard', href: '/dashboard' }, { label: 'Capacidad del equipo' }];
    }
    if (pathname.startsWith('/dashboard/operational-costs')) {
        return [{ label: 'Dashboard', href: '/dashboard' }, { label: 'Costo operacional' }];
    }
    if (pathname.startsWith('/admin/payroll')) {
        return [{ label: 'Dashboard', href: '/dashboard' }, { label: 'Nómina' }];
    }
    if (pathname.startsWith('/admin/overhead')) {
        return [{ label: 'Dashboard', href: '/dashboard' }, { label: 'Inventario de gastos' }];
    }
    if (pathname.startsWith('/admin/taxes')) {
        return [{ label: 'Dashboard', href: '/dashboard' }, { label: 'Impuestos' }];
    }

    return [{ label: 'Dashboard', href: '/dashboard' }];
}

export function AdminHeader({ onOpenMobileNav, workspaceName = 'Workspace' }: AdminHeaderProps) {
    const { user, logout } = useAuth();
    const pathname = usePathname() || '';
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isHelpOpen, setIsHelpOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);
    const breadcrumbs = getBreadcrumbs(pathname);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const userInitials = user?.fullName
        ? user.fullName
            .split(' ')
            .filter(Boolean)
            .slice(0, 2)
            .map((part) => part[0]?.toUpperCase())
            .join('')
        : 'U';

    const handleLogout = () => {
        logout();
        window.location.href = '/login';
    };

    return (
        <header className="bg-white/60 backdrop-blur-md border-b border-white/20 h-16 md:h-20 px-4 sm:px-6 md:px-10 flex items-center justify-between sticky top-0 z-30">
            {/* Left: Context */}
            <div className="flex items-center gap-3 min-w-0">
                {onOpenMobileNav ? (
                    <button
                        type="button"
                        onClick={onOpenMobileNav}
                        className="md:hidden h-11 w-11 rounded-2xl border border-gray-200 bg-white flex items-center justify-center text-gray-700 hover:bg-gray-50 shrink-0"
                        aria-label="Abrir menú de navegación"
                    >
                        <Menu size={22} strokeWidth={2} />
                    </button>
                ) : null}
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse shrink-0 hidden sm:block" />
                <div className="min-w-0">
                    <h2 className="text-system-gray text-[10px] sm:text-xs font-black uppercase tracking-[0.15em] sm:tracking-[0.2em] truncate">
                        {workspaceName} Workspace
                    </h2>
                    <nav aria-label="Breadcrumb" className="mt-1 hidden items-center gap-1 text-[12px] font-semibold text-gray-500 sm:flex">
                        {breadcrumbs.map((crumb, index) => {
                            const current = index === breadcrumbs.length - 1;
                            return (
                                <React.Fragment key={`${crumb.label}-${index}`}>
                                    {index > 0 && <ChevronRight size={12} className="text-gray-300" />}
                                    {crumb.href && !current ? (
                                        <Link href={crumb.href} className="truncate hover:text-secondary">
                                            {crumb.label}
                                        </Link>
                                    ) : (
                                        <span className={current ? 'truncate text-gray-900' : 'truncate'}>{crumb.label}</span>
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </nav>
                </div>
            </div>

            {/* Right: Help + User Menu */}
            <div className="flex items-center gap-3">
            <button
                type="button"
                onClick={() => setIsHelpOpen(true)}
                className="h-10 w-10 rounded-2xl border border-gray-200 bg-white flex items-center justify-center text-gray-500 hover:bg-gray-50 hover:text-secondary transition-all hidden sm:flex"
                aria-label="Abrir guía de uso"
            >
                <HelpCircle size={18} strokeWidth={2} />
            </button>
            <HelpPanel open={isHelpOpen} onClose={() => setIsHelpOpen(false)} />

            {/* User Menu */}
            <div className="relative" ref={menuRef}>
                <button
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className="flex items-center gap-4 hover:bg-white/50 p-2 pl-4 rounded-2xl transition-all focus:outline-none group"
                >
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-bold text-gray-900 tracking-tight leading-none">{user?.fullName || 'Usuario'}</p>
                        <p className="text-[10px] font-black text-system-gray uppercase tracking-widest mt-1.5">{user?.role || 'sin_rol'}</p>
                    </div>
                    <div className="relative">
                        <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-primary to-secondary text-white flex items-center justify-center font-bold text-lg shadow-lg border border-white/20">
                            {userInitials || 'U'}
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-100">
                            <ChevronDown size={10} className={user?.role === 'owner' ? "rotate-180" : ""} />
                        </div>
                    </div>
                </button>

                {/* Dropdown */}
                <AnimatePresence>
                    {isMenuOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className="absolute right-0 mt-4 w-64 bg-white/80 backdrop-blur-2xl rounded-3xl shadow-[0_20px_40px_rgba(0,0,0,0.1)] border border-white/20 py-3 z-50 origin-top-right overflow-hidden"
                        >
                            <div className="px-6 py-4 border-b border-gray-100/50 mb-2">
                                <p className="text-[10px] font-black text-system-gray uppercase tracking-widest mb-1">Sesión Actual</p>
                                <p className="text-sm font-bold text-gray-900 truncate">{user?.email || 'sin-email'}</p>
                            </div>

                            <div className="px-2 space-y-1">
                                <Link href="/dashboard/organization" className="flex items-center gap-3 px-4 py-3 text-sm font-bold text-gray-600 hover:bg-white hover:text-secondary hover:shadow-sm rounded-2xl transition-all group">
                                    <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center group-hover:bg-primary-soft transition-colors">
                                        <Building2 size={16} strokeWidth={2} />
                                    </div>
                                    Empresa
                                </Link>
                                {user?.role === 'owner' && (
                                    <a href="/dashboard/users" className="flex items-center gap-3 px-4 py-3 text-sm font-bold text-gray-600 hover:bg-white hover:text-secondary hover:shadow-sm rounded-2xl transition-all group">
                                        <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center group-hover:bg-primary-soft transition-colors">
                                            <Users size={16} strokeWidth={2} />
                                        </div>
                                        Usuarios (Equipo)
                                    </a>
                                )}
                                <Link href="/billing" className="flex items-center gap-3 px-4 py-3 text-sm font-bold text-gray-600 hover:bg-white hover:text-secondary hover:shadow-sm rounded-2xl transition-all group">
                                    <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center group-hover:bg-primary-soft transition-colors">
                                        <CreditCard size={16} strokeWidth={2} />
                                    </div>
                                    Gestionar suscripción
                                </Link>
                            </div>

                            <div className="mt-2 px-2 pt-2 border-t border-gray-100/50">
                                <button
                                    onClick={handleLogout}
                                    className="flex items-center gap-3 w-full px-4 py-3 text-sm font-bold text-red-500 hover:bg-red-50 hover:shadow-sm rounded-2xl transition-all group"
                                >
                                    <div className="w-8 h-8 rounded-xl bg-red-50 flex items-center justify-center group-hover:bg-white transition-colors">
                                        <LogOut size={16} strokeWidth={2} />
                                    </div>
                                    Cerrar Sesión
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
            </div>
        </header>
    );
}
