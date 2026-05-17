
import React from 'react';
import { QuickSelectList } from '@/components/admin/quick-selects/QuickSelectList';

export default function AdminQuickSelectsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-[20px] font-bold text-gray-900">Quick selects</h1>
                <p className="text-[13px] text-gray-500 mt-0.5">Gestiona las industrias y templates sugeridos para el onboarding.</p>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6">
                <QuickSelectList />
            </div>
        </div>
    );
}
