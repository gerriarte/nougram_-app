
'use client';

import React, { useState } from 'react';
import { UserList } from '@/components/users/UserList';
import { InvitationList } from '@/components/users/InvitationList';
import { UserProfileSettings } from '@/components/users/UserProfileSettings';
import { Users, Mail, Settings, ShieldCheck } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type Tab = 'members' | 'invitations' | 'profile';

export default function UserManagementPage() {
    const [activeTab, setActiveTab] = useState<Tab>('members');

    const tabs = [
        { id: 'members', label: 'Miembros', icon: Users, description: 'Gestiona tu equipo y sus niveles de acceso' },
        { id: 'invitations', label: 'Invitaciones', icon: Mail, description: 'Invitaciones pendientes de procesar' },
        { id: 'profile', label: 'Mi Perfil', icon: Settings, description: 'Configura tu identidad profesional' }
    ] as const;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-[1200px] mx-auto px-6 py-12"
        >
            {/* Page Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-10 mb-12">
                <div className="space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                            <ShieldCheck size={22} strokeWidth={1.5} />
                        </div>
                        <span className="text-[10px] font-black text-blue-600 uppercase tracking-[0.2em] bg-blue-50 px-3 py-1 rounded-full border border-blue-100">Administración</span>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">Equipo</h1>
                    <p className="text-system-gray font-medium text-lg max-w-2xl leading-relaxed">
                        Gestiona el talento de tu organización, define roles y personaliza tu perfil profesional.
                    </p>
                </div>

                {/* Apple Style Segmented Control */}
                <div className="bg-gray-200/50 p-1.5 rounded-2xl flex w-full md:w-auto backdrop-blur-sm border border-gray-200/20">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`
                                flex-1 md:flex-none flex items-center justify-center gap-2.5 px-6 py-2.5 rounded-xl text-sm font-bold transition-all
                                ${activeTab === tab.id
                                    ? 'bg-white text-gray-900 shadow-[0_4px_12px_rgba(0,0,0,0.08)] scale-100'
                                    : 'text-system-gray hover:text-gray-900 hover:bg-white/40 scale-95 hover:scale-100'}
                            `}
                        >
                            <tab.icon size={16} strokeWidth={2} />
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
    );
}
