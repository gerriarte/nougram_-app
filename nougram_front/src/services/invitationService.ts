
import { Invitation, InvitationStatus, TenantRole } from '@/types/user';

const KEY_INVITATIONS = 'nougram_invitations';

const INITIAL_INVITATIONS: Invitation[] = [
    {
        id: 'inv_1',
        email: 'nuevo.talento@agency.com',
        role: 'collaborator',
        status: 'pending',
        createdAt: '2026-02-01T10:00:00Z',
        expiresAt: '2026-02-08T10:00:00Z',
        createdBy: 'Juan Pérez',
        message: '¡Bienvenido al equipo!'
    }
];

export const invitationService = {
    getInvitations: async (): Promise<Invitation[]> => {
        if (typeof window === 'undefined') return INITIAL_INVITATIONS;
        const stored = localStorage.getItem(KEY_INVITATIONS);
        return stored ? JSON.parse(stored) : INITIAL_INVITATIONS;
    },

    saveInvitations: (invitations: Invitation[]) => {
        if (typeof window !== 'undefined') {
            localStorage.setItem(KEY_INVITATIONS, JSON.stringify(invitations));
        }
    },

    createInvitation: async (data: { email: string; role: TenantRole; message?: string; createdBy?: string }): Promise<Invitation> => {
        const invitations = await invitationService.getInvitations();
        const newInvite: Invitation = {
            id: `inv_${Date.now()}`,
            email: data.email,
            role: data.role,
            status: 'pending',
            createdAt: new Date().toISOString(),
            expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            createdBy: data.createdBy,
            message: data.message
        };
        invitationService.saveInvitations([...invitations, newInvite]);
        return newInvite;
    },

    updateStatus: async (id: string, status: InvitationStatus): Promise<void> => {
        const invitations = await invitationService.getInvitations();
        const updated = invitations.map(i => i.id === id ? { ...i, status } : i);
        invitationService.saveInvitations(updated);
    },

    cancelInvitation: async (id: string): Promise<void> => {
        await invitationService.updateStatus(id, 'cancelled');
    }
};
