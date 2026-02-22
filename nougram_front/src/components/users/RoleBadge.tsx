
'use client';

import React from 'react';
import { UserRole, ROLE_CONFIG } from '@/types/user';

const APPLE_ROLE_STYLES: Record<UserRole, { bg: string; text: string }> = {
    super_admin: { bg: 'bg-amber-100', text: 'text-amber-900' },
    support_manager: { bg: 'bg-indigo-100', text: 'text-indigo-900' },
    data_analyst: { bg: 'bg-cyan-100', text: 'text-cyan-900' },
    owner: { bg: 'bg-green-100', text: 'text-green-900' },
    admin_financiero: { bg: 'bg-blue-100', text: 'text-blue-900' },
    product_manager: { bg: 'bg-purple-100', text: 'text-purple-900' },
    collaborator: { bg: 'bg-gray-100', text: 'text-gray-900' }
};

export function RoleBadge({ role }: { role: UserRole }) {
    const config = ROLE_CONFIG[role] || ROLE_CONFIG.collaborator;
    const appleStyle = APPLE_ROLE_STYLES[role] || APPLE_ROLE_STYLES.collaborator;

    return (
        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest ${appleStyle.bg} ${appleStyle.text}`}>
            {config.label}
        </span>
    );
}
