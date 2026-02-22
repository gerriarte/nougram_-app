
import { UserProfile, UserProfileExtended, UserRole } from '@/types/user';

const KEY_USERS = 'nougram_users';

const INITIAL_USERS: UserProfileExtended[] = [
    {
        id: '1',
        email: 'juan.perez@agency.com',
        fullName: 'Juan Pérez',
        role: 'owner',
        status: 'ACTIVE',
        lastLoginAt: '2026-01-25T10:00:00Z',
        bio: 'Fundador de Agency y entusiasta del diseño.',
        specialty: 'Dirección de Arte',
        job_title: 'CEO & Founder',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-25T10:00:00Z'
    },
    {
        id: '2',
        email: 'maria.gomez@agency.com',
        fullName: 'María Gómez',
        role: 'admin_financiero',
        status: 'ACTIVE',
        lastLoginAt: '2026-01-24T15:30:00Z',
        job_title: 'CFO',
        created_at: '2026-01-02T00:00:00Z',
        updated_at: '2026-01-24T15:30:00Z'
    },
    {
        id: '3',
        email: 'carlos.lopez@agency.com',
        fullName: 'Carlos López',
        role: 'product_manager',
        status: 'ACTIVE',
        lastLoginAt: '2026-01-20T09:00:00Z',
        job_title: 'PM',
        created_at: '2026-01-03T00:00:00Z',
        updated_at: '2026-01-20T09:00:00Z'
    },
    {
        id: '4',
        email: 'ana.martinez@agency.com',
        fullName: 'Ana Martínez',
        role: 'collaborator',
        status: 'INACTIVE',
        job_title: 'Developer',
        created_at: '2026-01-04T00:00:00Z',
        updated_at: '2026-01-04T00:00:00Z'
    },
];

export const userService = {
    getUsers: async (): Promise<UserProfileExtended[]> => {
        if (typeof window === 'undefined') return INITIAL_USERS;
        const stored = localStorage.getItem(KEY_USERS);
        return stored ? JSON.parse(stored) : INITIAL_USERS;
    },

    saveUsers: (users: UserProfileExtended[]) => {
        if (typeof window !== 'undefined') {
            localStorage.setItem(KEY_USERS, JSON.stringify(users));
        }
    },

    updateUserRole: async (userId: string, newRole: UserRole): Promise<void> => {
        const users = await userService.getUsers();
        const updated = users.map(u => u.id === userId ? { ...u, role: newRole, updated_at: new Date().toISOString() } : u);
        userService.saveUsers(updated);
    },

    deleteUser: async (userId: string): Promise<void> => {
        const users = await userService.getUsers();
        const updated = users.filter(u => u.id !== userId);
        userService.saveUsers(updated);
    },

    updateProfile: async (userId: string, updates: Partial<UserProfileExtended>): Promise<void> => {
        const users = await userService.getUsers();
        const updated = users.map(u => u.id === userId ? { ...u, ...updates, updated_at: new Date().toISOString() } : u);
        userService.saveUsers(updated);
    }
};
