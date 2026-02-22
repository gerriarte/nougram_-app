

export type SupportRole = "super_admin" | "support_manager" | "data_analyst";
export type TenantRole = "owner" | "admin_financiero" | "product_manager" | "collaborator";

export type UserRole = SupportRole | TenantRole;

export interface UserProfile {
    id: string;
    email: string;
    fullName: string;
    role: UserRole;
    avatarUrl?: string; // photo_url in requirements
    status: 'ACTIVE' | 'INACTIVE';
    lastLoginAt?: string;
    organization_id?: number | null;
}

export interface UserProfileExtended extends UserProfile {
    bio?: string;
    specialty?: string;
    job_title?: string;

    // Social links
    linkedin_url?: string;
    portfolio_url?: string;
    github_url?: string;
    behance_url?: string;

    // Preferences
    timezone?: string;
    language?: string;

    // Metadata
    created_at: string;
    updated_at: string;
}

export type InvitationStatus = "pending" | "accepted" | "expired" | "cancelled";

export interface Invitation {
    id: string;
    email: string;
    role: TenantRole;
    status: InvitationStatus;
    expiresAt: string;
    createdAt: string;
    createdBy?: string;
    message?: string;
}

export const ROLE_CONFIG: Record<UserRole, { label: string; color: string; badge: string }> = {
    super_admin: { label: 'Super Admin', color: 'text-amber-800', badge: 'bg-amber-100 border-amber-200' },
    support_manager: { label: 'Support Manager', color: 'text-indigo-800', badge: 'bg-indigo-100 border-indigo-200' },
    data_analyst: { label: 'Data Analyst', color: 'text-cyan-800', badge: 'bg-cyan-100 border-cyan-200' },
    owner: {
        label: 'Owner',
        color: 'text-green-800',
        badge: 'bg-green-100 border-green-200'
    },
    admin_financiero: {
        label: 'Admin Financiero',
        color: 'text-blue-800',
        badge: 'bg-blue-100 border-blue-200'
    },
    product_manager: {
        label: 'Product Manager',
        color: 'text-purple-800',
        badge: 'bg-purple-100 border-purple-200'
    },
    collaborator: {
        label: 'Collaborator',
        color: 'text-gray-800',
        badge: 'bg-gray-100 border-gray-200'
    }
};

// RBAC Permissions Logic
export function canViewFinancials(role: UserRole): boolean {
    return role === 'super_admin' || role === 'owner' || role === 'admin_financiero';
}

export function canManageUsers(role: UserRole): boolean {
    return role === 'super_admin' || role === 'owner';
}

export function canInviteUsers(role: UserRole): boolean {
    return role === 'super_admin' || role === 'owner';
}
