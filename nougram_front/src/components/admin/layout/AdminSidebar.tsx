
'use client';

import React from 'react';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { AdminNavigationLinks } from '@/components/admin/layout/AdminNavigationLinks';

interface AdminSidebarProps {
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

export function AdminSidebar({ isCollapsed, onToggleCollapse }: AdminSidebarProps) {
    const pathname = usePathname() || '';
    const { user } = useAuth();

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
                <AdminNavigationLinks
                    pathname={pathname}
                    user={user}
                    isCollapsed={isCollapsed}
                    variant="sidebar"
                />
            </nav>

        </aside>
    );
}
