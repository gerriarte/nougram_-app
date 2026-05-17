
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
    workspaceName?: string;
}

function getWorkspaceInitials(name: string) {
    const initials = name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join('');

    return initials || 'NW';
}

export function AdminSidebar({ isCollapsed, onToggleCollapse, workspaceName = 'Workspace' }: AdminSidebarProps) {
    const pathname = usePathname() || '';
    const { user } = useAuth();
    const workspaceInitials = getWorkspaceInitials(workspaceName);

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

            <div className={cn("border-t border-white/30", isCollapsed ? "p-3" : "p-4")}>
                <div
                    className={cn(
                        "rounded-2xl border border-white/50 bg-white/65 shadow-sm backdrop-blur transition-all",
                        isCollapsed
                            ? "flex items-center justify-center p-2"
                            : "flex items-center gap-3 px-3 py-3"
                    )}
                    title={`${workspaceName} Workspace`}
                >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gray-900 text-[11px] font-black tracking-wide text-white">
                        {workspaceInitials}
                    </div>
                    {!isCollapsed && (
                        <div className="min-w-0">
                            <p className="truncate text-[13px] font-black tracking-tight text-gray-900">{workspaceName}</p>
                            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-system-gray">Workspace</p>
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
}
