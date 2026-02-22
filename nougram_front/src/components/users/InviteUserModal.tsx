
'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { TenantRole, ROLE_CONFIG } from '@/types/user';
import { useUserManagement } from '@/hooks/useUserManagement';
import { useAuth } from '@/hooks/useAuth';
import { X, Send, AlertCircle, CheckCircle, Shield, Mail, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface InviteModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function InviteUserModal({ isOpen, onClose }: InviteModalProps) {
    const { actions } = useUserManagement();
    const { user: currentUser } = useAuth();
    const [email, setEmail] = useState('');
    const [role, setRole] = useState<TenantRole>('collaborator');
    const [message, setMessage] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus('loading');
        try {
            await actions.inviteUser(email, role, message, currentUser?.fullName);
            setStatus('success');
            setTimeout(() => {
                onClose();
                setStatus('idle');
                setEmail('');
                setMessage('');
            }, 2000);
        } catch (error) {
            setStatus('error');
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                {/* Glassmorphic Backdrop */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/40 backdrop-blur-md"
                />

                {/* Modal Container */}
                <motion.div
                    initial={{ scale: 0.95, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.95, opacity: 0, y: 20 }}
                    className="relative w-full max-w-lg bg-white/80 backdrop-blur-2xl border border-white/20 rounded-[2.5rem] shadow-[0_32px_128px_rgba(0,0,0,0.15)] overflow-hidden"
                >
                    {/* Header */}
                    <div className="px-10 py-8 flex justify-between items-center border-b border-gray-100/50">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600">
                                <Send size={24} strokeWidth={1.5} />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900 tracking-tight leading-none">Invitar Miembro</h2>
                                <p className="text-system-gray font-medium text-sm mt-1.5">Suma talento a tu organización.</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2.5 text-gray-400 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all">
                            <X size={20} strokeWidth={1.5} />
                        </button>
                    </div>

                    <div className="p-10">
                        {status === 'success' ? (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="text-center py-10 space-y-6"
                            >
                                <div className="w-24 h-24 bg-green-50 text-green-500 rounded-[2.5rem] flex items-center justify-center mx-auto shadow-inner shadow-green-100/50">
                                    <CheckCircle size={48} strokeWidth={1.5} />
                                </div>
                                <div>
                                    <h3 className="text-2xl font-bold text-gray-900 tracking-tight">¡Invitación Enviada!</h3>
                                    <p className="text-system-gray font-medium text-sm mt-2">Hemos enviado un link a <span className="text-gray-900 font-bold">{email}</span></p>
                                </div>
                            </motion.div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-8">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Email del Invitado</label>
                                    <div className="relative group">
                                        <Input
                                            type="email"
                                            required
                                            placeholder="colab@agencia.com"
                                            className="pl-12"
                                            value={email}
                                            onChange={e => setEmail(e.target.value)}
                                            disabled={status === 'loading'}
                                        />
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Rol a Asignar</label>
                                    <div className="relative group">
                                        <select
                                            className="w-full h-12 pl-12 pr-10 appearance-none bg-gray-200/50 rounded-xl font-bold text-gray-900 focus:ring-2 focus:ring-blue-500/50 focus:bg-white outline-none transition-all"
                                            value={role}
                                            onChange={e => setRole(e.target.value as TenantRole)}
                                            disabled={status === 'loading'}
                                        >
                                            <option value="owner">Owner (Full Control)</option>
                                            <option value="admin_financiero">Admin Financiero (Márgenes & Costos)</option>
                                            <option value="product_manager">Product Manager (Solo Cotizaciones)</option>
                                            <option value="collaborator">Collaborator (Lectura)</option>
                                        </select>
                                        <Shield className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                    </div>
                                    <motion.div
                                        layout
                                        className="text-[10px] font-bold text-blue-600 bg-blue-50/50 px-4 py-3 rounded-xl border border-blue-100/50 flex items-center gap-3"
                                    >
                                        <AlertCircle size={14} strokeWidth={2} />
                                        <span>
                                            {role === 'owner' && 'Control total de facturación y miembros.'}
                                            {role === 'admin_financiero' && 'Gestión de nómina, BCR e impuestos.'}
                                            {role === 'product_manager' && 'Solo puede armar propuestas sin ver costos.'}
                                            {role === 'collaborator' && 'Acceso limitado a proyectos asignados.'}
                                        </span>
                                    </motion.div>
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Mensaje (Opcional)</label>
                                    <div className="relative group">
                                        <textarea
                                            className="w-full p-5 pl-12 border border-transparent bg-gray-200/50 focus:bg-white focus:ring-2 focus:ring-blue-500/50 outline-none rounded-2xl font-medium transition-all text-sm leading-relaxed"
                                            placeholder="¡Hola! Te invito a unirte a Nougram..."
                                            value={message}
                                            onChange={e => setMessage(e.target.value)}
                                            maxLength={500}
                                            disabled={status === 'loading'}
                                        />
                                        <MessageSquare className="absolute left-4 top-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                    </div>
                                    <p className="text-right text-[9px] font-black text-system-gray uppercase tracking-widest">{message.length}/500</p>
                                </div>

                                <div className="flex gap-4 pt-2">
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        onClick={onClose}
                                        className="flex-1 h-14 rounded-2xl font-bold border border-gray-100"
                                        disabled={status === 'loading'}
                                    >
                                        Cancelar
                                    </Button>
                                    <Button
                                        type="submit"
                                        className="flex-[1.5] h-14 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold flex items-center justify-center gap-2 active:scale-95 shadow-xl shadow-blue-200 transition-all disabled:opacity-70 disabled:scale-100"
                                        disabled={status === 'loading'}
                                    >
                                        {status === 'loading' ? (
                                            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                        ) : (
                                            <>
                                                <Send size={20} strokeWidth={2} />
                                                Enviar Invitación
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </form>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
