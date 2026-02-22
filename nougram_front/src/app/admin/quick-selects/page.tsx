
import React from 'react';
import { QuickSelectList } from '@/components/admin/quick-selects/QuickSelectList';

export default function AdminQuickSelectsPage() {
    return (
        <main className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-5xl mx-auto space-y-6">

                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Administración de Quick Selects</h1>
                        <p className="text-gray-500">Gestiona las industrias y templates sugeridos para el onboarding.</p>
                    </div>
                    <div className="text-right hidden md:block">
                        <p className="text-sm font-medium text-gray-900">Nougram Admin</p>
                        <p className="text-xs text-gray-400">v1.0.0</p>
                    </div>
                </div>

                {/* Content */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <QuickSelectList />
                </div>
            </div>
        </main>
    );
}
