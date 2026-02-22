
'use client';

import React from 'react';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AdminProvider } from '@/context/AdminContext';
import { AdminSidebar } from './AdminSidebar';
import { BCRSummaryCard } from './BCRSummaryCard';
import { AdminHeader } from './AdminHeader';
import { useAuth } from '@/hooks/useAuth';

export function AdminLayout({ children, hideRightPanel = false }: { children: React.ReactNode, hideRightPanel?: boolean }) {
    const router = useRouter();
    const { isAuthenticated, loading } = useAuth();

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.replace('/login');
        }
    }, [loading, isAuthenticated, router]);

    if (loading || !isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="w-10 h-10 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <AdminProvider>
            <div className="flex min-h-screen bg-background">
                {/* Sidebar */}
                <AdminSidebar />

                {/* Main Content Column */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Header */}
                    <AdminHeader />

                    <main className="flex-1 p-12">
                        <div className="flex gap-12 items-start max-w-[1600px] mx-auto">
                            <div className="flex-1 min-w-0">
                                {children}
                            </div>

                            {/* Right Column / BCR Card - "Always Visible" unless hidden */}
                            {!hideRightPanel && (
                                <div className="w-80 flex-shrink-0 hidden xl:block sticky top-32">
                                    <BCRSummaryCard />
                                </div>
                            )}
                        </div>
                    </main>
                </div>
            </div>
        </AdminProvider>
    );
}

