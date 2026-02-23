
import { Invitation, InvitationStatus, TenantRole } from '@/types/user';
import { apiRequest } from '@/lib/api-client';

type OrganizationMeResponse = {
    id: number;
};

type InvitationApiItem = {
    id: number;
    email: string;
    role: TenantRole;
    status: InvitationStatus;
    expires_at: string;
    created_at: string;
    created_by_id?: number;
};

type InvitationListResponse = {
    items: InvitationApiItem[];
    total: number;
};

type InvitationCreateResponse = InvitationApiItem;

async function getCurrentOrganizationId(): Promise<number> {
    const response = await apiRequest<OrganizationMeResponse>('/organizations/me');
    if (response.error || !response.data?.id) {
        throw new Error(response.error || 'No se pudo resolver la organización actual');
    }
    return response.data.id;
}

function mapInvitation(item: InvitationApiItem): Invitation {
    return {
        id: String(item.id),
        email: item.email,
        role: item.role,
        status: item.status,
        expiresAt: item.expires_at,
        createdAt: item.created_at,
        createdBy: item.created_by_id ? String(item.created_by_id) : undefined,
    };
}

export const invitationService = {
    getInvitations: async (): Promise<Invitation[]> => {
        const organizationId = await getCurrentOrganizationId();
        const response = await apiRequest<InvitationListResponse>(`/organizations/${organizationId}/invitations`);
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudieron cargar las invitaciones');
        }

        return response.data.items.map(mapInvitation);
    },

    createInvitation: async (data: { email: string; role: TenantRole; message?: string; createdBy?: string }): Promise<Invitation> => {
        const organizationId = await getCurrentOrganizationId();
        const response = await apiRequest<InvitationCreateResponse>(`/organizations/${organizationId}/invitations`, {
            method: 'POST',
            body: JSON.stringify({
                email: data.email,
                role: data.role,
            }),
        });
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo enviar la invitación');
        }

        return mapInvitation(response.data);
    },

    cancelInvitation: async (id: string): Promise<void> => {
        const organizationId = await getCurrentOrganizationId();
        const response = await apiRequest(`/organizations/${organizationId}/invitations/${id}`, {
            method: 'DELETE',
        });
        if (response.error) {
            throw new Error(response.error);
        }
    }
};
