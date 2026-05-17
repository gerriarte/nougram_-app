
'use client';

import React from 'react';
import { UserList } from '@/components/users/UserList';

export default function UsersPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Gestión de Usuarios</h1>
                <p className="text-gray-500">Administra los miembros de tu organización y sus permisos.</p>
            </div>

            <UserList />
        </div>
    );
}
