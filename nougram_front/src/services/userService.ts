
import { UserProfileExtended, UserRole } from '@/types/user';
import { apiRequest } from '@/lib/api-client';

type OrganizationMeResponse = {
    id: number;
};

type OrganizationUsersResponse = {
    items: Array<{
        id: number;
        email: string;
        full_name: string;
        role: UserRole;
        created_at?: string | null;
    }>;
};

async function getCurrentOrganizationId(): Promise<number> {
    const response = await apiRequest<OrganizationMeResponse>('/organizations/me');
    if (response.error || !response.data?.id) {
        throw new Error(response.error || 'No se pudo resolver la organización actual');
    }
    return response.data.id;
}

export const userService = {
    getUsers: async (): Promise<UserProfileExtended[]> => {
        const organizationId = await getCurrentOrganizationId();
        const response = await apiRequest<OrganizationUsersResponse>(`/organizations/${organizationId}/users`);
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo cargar el equipo');
        }

        return response.data.items.map((user) => ({
            id: String(user.id),
            email: user.email,
            fullName: user.full_name,
            role: user.role,
            status: 'ACTIVE',
            created_at: user.created_at || new Date().toISOString(),
            updated_at: new Date().toISOString(),
        }));
    },

    updateUserRole: async (userId: string, newRole: UserRole): Promise<void> => {
        const organizationId = await getCurrentOrganizationId();
        const response = await apiRequest(`/organizations/${organizationId}/users/${userId}/role`, {
            method: 'PUT',
            body: JSON.stringify({ role: newRole }),
        });
        if (response.error) {
            throw new Error(response.error);
        }
    },

    deleteUser: async (userId: string): Promise<void> => {
        const organizationId = await getCurrentOrganizationId();
        const response = await apiRequest(`/organizations/${organizationId}/users/${userId}`, {
            method: 'DELETE',
        });
        if (response.error) {
            throw new Error(response.error);
        }
    },

    updateProfile: async (_userId: string, updates: Partial<UserProfileExtended>): Promise<void> => {
        const response = await apiRequest('/auth/me', {
            method: 'PUT',
            body: JSON.stringify({
                full_name: updates.fullName,
                job_title: updates.job_title,
                specialty: updates.specialty,
                bio: updates.bio,
                linkedin_url: updates.linkedin_url,
                portfolio_url: updates.portfolio_url,
                instagram_url: updates.instagram_url,
                behance_url: updates.behance_url,
                timezone: updates.timezone,
                language: updates.language,
            }),
        });
        if (response.error) {
            throw new Error(response.error);
        }
    },

    changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
        const response = await apiRequest('/auth/me/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });
        if (response.error) {
            throw new Error(response.error);
        }
    },
};
