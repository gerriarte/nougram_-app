
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { UserList } from '@/components/users/UserList';
import { InvitationList } from '@/components/users/InvitationList';
import { UserProfileSettings } from '@/components/users/UserProfileSettings';
import { Users, Mail, Settings, ShieldCheck, ArrowLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';

type Tab = 'members' | 'invitations' | 'profile';

export default function UserManagementPage() {
    const [activeTab, setActiveTab] = useState<Tab>('members');

    const tabs = [
        { id: 'members', label: 'Miembros', icon: Users, description: 'Gestiona tu equipo y sus niveles de acceso' },
        { id: 'invitations', label: 'Invitaciones', icon: Mail, description: 'Invitaciones pendientes de procesar' },
        { id: 'profile', label: 'Mi Perfil', icon: Settings, description: 'Configura tu identidad profesional' }
    ] as const;

    return (
        <AdminLayout>
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-[1200px] mx-auto"
            >
                {/* Page Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-8">
                    <div className="space-y-2">
                        <Link
                            href="/dashboard"
                            className="inline-flex items-center gap-1.5 text-[12px] text-gray-400 hover:text-gray-700 transition-colors"
                        >
                            <ArrowLeft size={12} />
                            Volver al dashboard
                        </Link>
                        <div className="flex items-center gap-2.5">
                            <div className="w-9 h-9 bg-gray-900 rounded-xl flex items-center justify-center text-white">
                                <ShieldCheck size={18} strokeWidth={1.5} />
                            </div>
                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.15em]">Administración</span>
                        </div>
                        <h1 className="text-[22px] font-bold text-gray-900 tracking-tight">Equipo</h1>
                        <p className="text-[13px] text-gray-500 max-w-xl">
                            Gestiona el talento de tu organización, define roles y personaliza tu perfil.
                        </p>
                    </div>

                    <div className="flex items-center gap-1 rounded-lg bg-surface-2 border border-gray-200 p-1 w-full md:w-auto">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex flex-1 md:flex-none items-center justify-center gap-1.5 px-4 py-1.5 rounded-md text-[12.5px] font-semibold transition-colors ${
                                    activeTab === tab.id ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
                                }`}
                            >
                                <tab.icon size={13} strokeWidth={2} />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
                {/* Content Area */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3, type: 'spring', damping: 25, stiffness: 200 }}
                    >
                        {activeTab === 'members' && <UserList />}
                        {activeTab === 'invitations' && <InvitationList />}
                        {activeTab === 'profile' && <UserProfileSettings />}
                    </motion.div>
                </AnimatePresence>
            </motion.div>
        </AdminLayout>
    );
}
