
'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { RoleBadge } from './RoleBadge';
import { useUserManagement } from '@/hooks/useUserManagement';
import { Mail, Clock, CheckCircle, XCircle, Ban, RefreshCw, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function InvitationList() {
    const { invitations, loading, actions } = useUserManagement();

    const getStatusStyles = (status: string) => {
        switch (status) {
            case 'pending': return 'bg-blue-50 text-blue-700';
            case 'accepted': return 'bg-green-50 text-green-700';
            case 'expired': return 'bg-orange-50 text-orange-700';
            case 'cancelled': return 'bg-gray-100 text-gray-500';
            default: return 'bg-gray-50 text-gray-600';
        }
    };

    const StatusIcon = ({ status, size }: { status: string; size: number }) => {
        switch (status) {
            case 'pending': return <Clock size={size} strokeWidth={2} />;
            case 'accepted': return <CheckCircle size={size} strokeWidth={2} />;
            case 'expired': return <XCircle size={size} strokeWidth={2} />;
            case 'cancelled': return <Ban size={size} strokeWidth={2} />;
            default: return null;
        }
    };

    if (loading) return <div className="p-12 text-center text-system-gray font-medium animate-pulse">Cargando invitaciones...</div>;

    const pendingInvitations = invitations.filter(i => i.status !== 'accepted');

    return (
        <Card>
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-gray-100/30 border-b border-gray-100/50 font-bold text-system-gray uppercase text-[10px] tracking-[0.15em]">
                        <tr>
                            <th className="px-8 py-5">Invitado</th>
                            <th className="px-8 py-5">Rol Asignado</th>
                            <th className="px-8 py-5">Estado</th>
                            <th className="px-8 py-5 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100/50">
                        <AnimatePresence mode='popLayout'>
                            {pendingInvitations.map(invite => (
                                <motion.tr
                                    key={invite.id}
                                    layout
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="group hover:bg-white/40 transition-colors"
                                >
                                    <td className="px-8 py-6">
                                        <div className="flex items-center gap-4">
                                            <div className="w-11 h-11 rounded-xl bg-gray-50 flex items-center justify-center text-gray-400 border border-gray-100">
                                                <Mail size={20} strokeWidth={1.5} />
                                            </div>
                                            <div>
                                                <p className="font-bold text-gray-900 text-base">{invite.email}</p>
                                                <p className="text-system-gray text-[10px] font-bold uppercase tracking-tight mt-0.5">
                                                    Enviada el {new Date(invite.createdAt).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-8 py-6">
                                        <RoleBadge role={invite.role} />
                                    </td>
                                    <td className="px-8 py-6">
                                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${getStatusStyles(invite.status)}`}>
                                            <StatusIcon status={invite.status} size={12} />
                                            {invite.status === 'pending' ? 'Pendiente' :
                                                invite.status === 'expired' ? 'Expirada' : invite.status}
                                        </span>
                                    </td>
                                    <td className="px-8 py-6 text-right">
                                        <div className="flex justify-end gap-2">
                                            {(invite.status === 'pending' || invite.status === 'expired') && (
                                                <button
                                                    title="Reenviar"
                                                    className="p-2.5 text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
                                                >
                                                    <RefreshCw size={16} strokeWidth={2} />
                                                </button>
                                            )}
                                            {invite.status === 'pending' && (
                                                <button
                                                    onClick={() => actions.cancelInvitation(invite.id)}
                                                    className="p-2.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                                    title="Cancelar Invitación"
                                                >
                                                    <X size={16} strokeWidth={2} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </motion.tr>
                            ))}
                        </AnimatePresence>
                    </tbody>
                </table>
            </div>

            {pendingInvitations.length === 0 && (
                <div className="p-24 text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-[2.5rem] flex items-center justify-center mx-auto mb-6 text-gray-300">
                        <Mail size={32} strokeWidth={1.5} />
                    </div>
                    <p className="text-gray-900 font-bold text-xl">Sin invitaciones pendientes</p>
                    <p className="text-system-gray font-medium mt-2">Cuando invites a alguien, aparecerá aquí.</p>
                </div>
            )}
        </Card>
    );
}
