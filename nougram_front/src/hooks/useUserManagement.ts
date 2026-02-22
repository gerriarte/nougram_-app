
import { useState, useEffect, useCallback } from 'react';
import { UserProfileExtended, Invitation, UserRole, TenantRole } from '@/types/user';
import { userService } from '@/services/userService';
import { invitationService } from '@/services/invitationService';

export function useUserManagement() {
    const [members, setMembers] = useState<UserProfileExtended[]>([]);
    const [invitations, setInvitations] = useState<Invitation[]>([]);
    const [loading, setLoading] = useState(true);

    const refreshData = useCallback(async () => {
        setLoading(true);
        const [u, i] = await Promise.all([
            userService.getUsers(),
            invitationService.getInvitations()
        ]);
        setMembers(u);
        setInvitations(i);
        setLoading(false);
    }, []);

    useEffect(() => {
        refreshData();
    }, [refreshData]);

    // Member Actions
    const updateMemberRole = async (id: string, role: UserRole) => {
        await userService.updateUserRole(id, role);
        await refreshData();
    };

    const deleteMember = async (id: string) => {
        await userService.deleteUser(id);
        await refreshData();
    };

    // Invitation Actions
    const inviteUser = async (email: string, role: TenantRole, message?: string, inviterName?: string) => {
        await invitationService.createInvitation({ email, role, message, createdBy: inviterName });
        await refreshData();
    };

    const cancelInvitation = async (id: string) => {
        await invitationService.cancelInvitation(id);
        await refreshData();
    };

    return {
        members,
        invitations,
        loading,
        actions: {
            updateMemberRole,
            deleteMember,
            inviteUser,
            cancelInvitation,
            refreshData
        }
    };
}
