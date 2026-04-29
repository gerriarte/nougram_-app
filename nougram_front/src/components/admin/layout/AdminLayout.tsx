
'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Image from 'next/image';
import { AdminProvider } from '@/context/AdminContext';
import { AdminSidebar } from './AdminSidebar';
import { BCRSummaryCard } from './BCRSummaryCard';
import { AdminHeader } from './AdminHeader';
import { useAuth } from '@/hooks/useAuth';
import { useIsMobile } from '@/hooks/useIsMobile';
import { isDesktopOnlyPath } from '@/lib/desktop-only-routes';
import { DesktopOnlyBlock } from '@/components/mobile/DesktopOnlyBlock';
import { MobileBottomNav } from '@/components/mobile/MobileBottomNav';
import { MobileDrawer } from '@/components/mobile/MobileDrawer';
import { AdminNavigationLinks } from '@/components/admin/layout/AdminNavigationLinks';
import { apiRequest } from '@/lib/api-client';

type OrganizationResponse = {
    id: number;
    name: string;
};

export function AdminLayout({ children, hideRightPanel = false }: { children: React.ReactNode, hideRightPanel?: boolean }) {
    const router = useRouter();
    const pathname = usePathname();
    const { isAuthenticated, loading, user } = useAuth();
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
    const [workspaceName, setWorkspaceName] = useState('Workspace');
    const isMobile = useIsMobile();

    const desktopOnly = isDesktopOnlyPath(pathname);
    const blockDesktopModule = desktopOnly && isMobile === true;
    const desktopOnlyPending = desktopOnly && isMobile === undefined;

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            const redirect = encodeURIComponent(pathname || '/dashboard');
            router.replace(`/login?redirect=${redirect}`);
        }
    }, [loading, isAuthenticated, router, pathname]);

    useEffect(() => {
        if (!isAuthenticated) return;

        const loadOrganization = async () => {
            const response = await apiRequest<OrganizationResponse>('/organizations/me');
            setWorkspaceName(response.data?.name || 'Workspace');
        };

        void loadOrganization();
    }, [isAuthenticated]);

    if (loading || !isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="w-8 h-8 border-[3px] border-gray-200 border-t-gray-500 rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <AdminProvider>
            <div className="flex min-h-screen bg-background">
                <AdminSidebar
                    isCollapsed={isSidebarCollapsed}
                    onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
                    workspaceName={workspaceName}
                />

                <div className="flex-1 flex flex-col min-w-0">
                    <AdminHeader
                        onOpenMobileNav={() => setMobileDrawerOpen(true)}
                        workspaceName={workspaceName}
                    />

                    <main className="flex-1 p-4 sm:p-8 md:p-12 pb-24 md:pb-12">
                        <div className="flex gap-6 lg:gap-12 items-start max-w-[1600px] mx-auto">
                            <div className="flex-1 min-w-0 w-full">
                                {desktopOnlyPending ? (
                                    <div className="min-h-[40vh] flex items-center justify-center">
                                        <div className="w-8 h-8 border-[3px] border-gray-200 border-t-gray-500 rounded-full animate-spin" />
                                    </div>
                                ) : blockDesktopModule ? (
                                    <DesktopOnlyBlock />
                                ) : (
                                    children
                                )}
                            </div>

                            {!hideRightPanel && (
                                <div className="w-80 flex-shrink-0 hidden xl:block sticky top-32">
                                    <BCRSummaryCard />
                                </div>
                            )}
                        </div>
                    </main>
                </div>

                <MobileDrawer
                    open={mobileDrawerOpen}
                    onClose={() => setMobileDrawerOpen(false)}
                    title="Navegación"
                >
                    <div className="pb-4 border-b border-gray-100 mb-4 flex justify-center">
                        <Image src="/brand/Logo-orange.svg" alt="Nougram" width={120} height={28} priority />
                    </div>
                    <nav className="space-y-6">
                        <AdminNavigationLinks
                            pathname={pathname || ''}
                            user={user}
                            isCollapsed={false}
                            variant="drawer"
                            onNavigate={() => setMobileDrawerOpen(false)}
                        />
                    </nav>
                </MobileDrawer>

                <MobileBottomNav onOpenMenu={() => setMobileDrawerOpen(true)} />
            </div>
        </AdminProvider>
    );
}
