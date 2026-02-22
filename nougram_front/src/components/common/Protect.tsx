
import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { UserRole } from '@/types/user';

interface ProtectProps {
    permission?: 'canViewFinancials' | 'canManageUsers' | 'canInviteUsers';
    confidential?: boolean;
    children: React.ReactNode;
    fallback?: React.ReactNode;
    blur?: boolean;
}

export function Protect({ permission, confidential, children, fallback, blur }: ProtectProps) {
    const { permissions } = useAuth();

    let hasAccess = true;

    if (permission) {
        hasAccess = !!permissions[permission];
    } else if (confidential) {
        hasAccess = permissions.canViewFinancials;
    }

    if (hasAccess) {
        return <>{children}</>;
    }

    if (blur) {
        return (
            <div className="relative group cursor-not-allowed select-none" title="Confidential Information">
                <div className="blur-sm opacity-50 pointer-events-none">
                    {children}
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[10px] bg-red-600 text-white px-2 py-1 rounded-lg font-black uppercase tracking-widest shadow-lg shadow-red-100 opacity-0 group-hover:opacity-100 transition-all scale-90 group-hover:scale-100">
                        🔒 Protegido
                    </span>
                </div>
            </div>
        );
    }

    return <>{fallback || null}</>;
}
