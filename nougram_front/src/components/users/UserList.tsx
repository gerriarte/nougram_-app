
'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { RoleBadge } from './RoleBadge';
import { UserRole, ROLE_CONFIG } from '@/types/user';
import { InviteUserModal } from './InviteUserModal';
import { useUserManagement } from '@/hooks/useUserManagement';
import { useAuth } from '@/hooks/useAuth';
import { Search, Filter, MoreVertical, UserPlus, Mail, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function UserList() {
    const { members, loading, actions } = useUserManagement();
    const { permissions, user: currentUser } = useAuth();
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState<string>('all');
    const [isInviteOpen, setIsInviteOpen] = useState(false);

    const filteredUsers = members.filter(u => {
        const matchesSearch = u.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
            u.email.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesRole = roleFilter === 'all' || u.role === roleFilter;
        return matchesSearch && matchesRole;
    });

    if (loading) return <div className="p-12 text-center text-system-gray font-medium animate-pulse">Cargando equipo...</div>;

    return (
        <div className="space-y-8">
            {/* Header & Filters */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} strokeWidth={1.5} />
                    <Input
                        placeholder="Buscar por nombre o email..."
                        className="pl-11"
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="flex items-center gap-4 w-full md:w-auto">
                    <div className="relative flex-1 md:flex-none">
                        <select
                            value={roleFilter}
                            onChange={(e) => setRoleFilter(e.target.value)}
                            className="w-full md:w-48 h-12 appearance-none bg-gray-200/50 rounded-xl px-5 py-2 text-sm font-bold text-gray-900 focus:ring-2 focus:ring-blue-500/50 focus:bg-white focus:outline-none pr-10 transition-all"
                        >
                            <option value="all">Todos los roles</option>
                            {Object.entries(ROLE_CONFIG).map(([slug, config]) => (
                                <option key={slug} value={slug}>{config.label}</option>
                            ))}
                        </select>
                        <Filter className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={14} strokeWidth={1.5} />
                    </div>

                    {permissions.canInviteUsers && (
                        <Button
                            onClick={() => setIsInviteOpen(true)}
                            className="h-12 px-6 bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2 rounded-xl font-bold shadow-lg shadow-blue-500/20 active:scale-95 transition-all"
                        >
                            <UserPlus size={18} strokeWidth={1.5} />
                            <span>Invitar</span>
                        </Button>
                    )}
                </div>
            </div>

            {/* Users Table */}
            <Card>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-100/30 border-b border-gray-100/50 font-bold text-system-gray uppercase text-[10px] tracking-[0.15em]">
                            <tr>
                                <th className="px-8 py-5">Miembro</th>
                                <th className="px-8 py-5">Rol & Permisos</th>
                                <th className="px-8 py-5">Estado</th>
                                <th className="px-8 py-5 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100/50">
                            <AnimatePresence mode='popLayout'>
                                {filteredUsers.map(user => (
                                    <motion.tr
                                        key={user.id}
                                        layout
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="group hover:bg-white/40 transition-colors"
                                    >
                                        <td className="px-8 py-6">
                                            <div className="flex items-center gap-4">
                                                <div className="relative">
                                                    <div className="w-11 h-11 rounded-xl bg-gray-100 flex items-center justify-center text-gray-400 font-bold text-lg overflow-hidden border border-gray-200/50">
                                                        {user.avatarUrl ? (
                                                            <img src={user.avatarUrl} alt={user.fullName} className="w-full h-full object-cover" />
                                                        ) : (
                                                            user.fullName.charAt(0)
                                                        )}
                                                    </div>
                                                    <div className={`absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full border-2 border-white ${user.status === 'ACTIVE' ? 'bg-green-500' : 'bg-gray-300'}`} />
                                                </div>
                                                <div>
                                                    <p className="font-bold text-gray-900 text-base flex items-center gap-2">
                                                        {user.fullName}
                                                        {user.id === currentUser?.id && <span className="bg-blue-50 text-blue-600 text-[9px] font-black px-2 py-0.5 rounded-full tracking-widest uppercase border border-blue-100">Tú</span>}
                                                    </p>
                                                    <p className="text-system-gray text-xs font-medium flex items-center gap-1.5 mt-0.5">
                                                        <Mail size={12} strokeWidth={1.5} />
                                                        {user.email}
                                                    </p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex flex-col gap-1.5 items-start">
                                                <RoleBadge role={user.role} />
                                                {user.job_title && (
                                                    <span className="text-[10px] font-bold text-system-gray flex items-center gap-1 mt-0.5">
                                                        <Shield size={10} strokeWidth={2} />
                                                        {user.job_title}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${user.status === 'ACTIVE' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                                <div className={`w-1.5 h-1.5 rounded-full ${user.status === 'ACTIVE' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                                                {user.status === 'ACTIVE' ? 'Activo' : 'Inactivo'}
                                            </span>
                                        </td>
                                        <td className="px-8 py-6 text-right">
                                            {permissions.canManageUsers && (
                                                <button className="p-2.5 text-gray-400 hover:text-blue-600 hover:bg-white rounded-xl transition-all shadow-sm shadow-transparent hover:shadow-gray-200/50">
                                                    <MoreVertical size={18} strokeWidth={1.5} />
                                                </button>
                                            )}
                                        </td>
                                    </motion.tr>
                                ))}
                            </AnimatePresence>
                        </tbody>
                    </table>
                </div>

                {filteredUsers.length === 0 && (
                    <div className="p-24 text-center">
                        <div className="w-20 h-20 bg-gray-100 rounded-[2.5rem] flex items-center justify-center mx-auto mb-6 text-gray-300">
                            <Search size={32} strokeWidth={1.5} />
                        </div>
                        <p className="text-gray-900 font-bold text-xl">No se encontraron miembros</p>
                        <p className="text-system-gray font-medium mt-2">Intenta con otros términos de búsqueda.</p>
                    </div>
                )}
            </Card>

            <InviteUserModal
                isOpen={isInviteOpen}
                onClose={() => setIsInviteOpen(false)}
            />
        </div>
    );
}
