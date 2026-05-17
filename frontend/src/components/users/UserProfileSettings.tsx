
'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/hooks/useAuth';
import { userService } from '@/services/userService';
import {
    User, Mail, Briefcase, Award, Linkedin,
    Globe, Instagram, Shield, Save,
    Calendar, Languages, Clock, CheckCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function UserProfileSettings() {
    const { user, refreshCurrentUser } = useAuth();
    const [formData, setFormData] = useState({
        fullName: user?.fullName || '',
        job_title: user?.job_title || '',
        specialty: user?.specialty || '',
        bio: user?.bio || '',
        linkedin_url: user?.linkedin_url || '',
        portfolio_url: user?.portfolio_url || '',
        instagram_url: user?.instagram_url || '',
        behance_url: user?.behance_url || '',
        timezone: user?.timezone || 'America/Bogota',
        language: user?.language || 'es'
    });
    const [status, setStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
    });
    const [passwordStatus, setPasswordStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
    const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

    useEffect(() => {
        if (!user) return;
        setFormData({
            fullName: user.fullName || '',
            job_title: user.job_title || '',
            specialty: user.specialty || '',
            bio: user.bio || '',
            linkedin_url: user.linkedin_url || '',
            portfolio_url: user.portfolio_url || '',
            instagram_url: user.instagram_url || '',
            behance_url: user.behance_url || '',
            timezone: user.timezone || 'America/Bogota',
            language: user.language || 'es',
        });
    }, [user]);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;

        setStatus('saving');
        try {
            await userService.updateProfile(user.id, formData);
            await refreshCurrentUser();
            setStatus('success');
            setTimeout(() => setStatus('idle'), 2000);
        } catch {
            setStatus('error');
            setTimeout(() => setStatus('idle'), 3000);
        }
    };

    const handleChangePassword = async () => {
        setPasswordStatus('saving');
        setPasswordMessage(null);

        if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
            setPasswordStatus('error');
            setPasswordMessage('Completa todos los campos de contraseña.');
            return;
        }
        if (passwordData.newPassword.length < 8) {
            setPasswordStatus('error');
            setPasswordMessage('La nueva contraseña debe tener mínimo 8 caracteres.');
            return;
        }
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            setPasswordStatus('error');
            setPasswordMessage('La confirmación no coincide con la nueva contraseña.');
            return;
        }

        try {
            await userService.changePassword(passwordData.currentPassword, passwordData.newPassword);
            setPasswordStatus('success');
            setPasswordMessage('Contraseña actualizada correctamente.');
            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
            setTimeout(() => {
                setPasswordStatus('idle');
                setPasswordMessage(null);
            }, 2200);
        } catch (error) {
            setPasswordStatus('error');
            setPasswordMessage(error instanceof Error ? error.message : 'No se pudo actualizar la contraseña.');
        }
    };

    const userInitials = user?.fullName
        ? user.fullName
            .split(' ')
            .filter(Boolean)
            .slice(0, 2)
            .map((part) => part[0]?.toUpperCase())
            .join('')
        : 'U';

    return (
        <form onSubmit={handleSave} className="space-y-10">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                {/* Profile Card */}
                <div className="lg:col-span-1 space-y-8">
                    <Card className="p-10 text-center relative overflow-hidden group">
                        {/* Material dynamic background */}
                        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-br from-blue-500/10 to-indigo-600/10 animate-pulse" />

                        <div className="relative mt-4 mb-8">
                            <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-primary to-secondary text-white flex items-center justify-center text-2xl font-bold shadow-lg">
                                {userInitials}
                            </div>
                        </div>

                        <h3 className="text-2xl font-bold text-gray-900 tracking-tight">{user?.fullName}</h3>
                        <p className="text-system-gray font-bold text-[10px] uppercase tracking-[0.2em] mt-2 leading-none">
                            {user?.role?.replace('_', ' ')}
                        </p>

                        <div className="mt-10 pt-10 border-t border-gray-100/50 space-y-5 text-left">
                            <div className="flex items-center gap-4 text-sm font-medium text-gray-700">
                                <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                                    <Mail size={16} strokeWidth={1.5} />
                                </div>
                                {user?.email}
                            </div>
                            <div className="flex items-center gap-4 text-sm font-medium text-gray-700">
                                <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                                    <Clock size={16} strokeWidth={1.5} />
                                </div>
                                {formData.timezone}
                            </div>
                            <div className="flex items-center gap-4 text-sm font-medium text-gray-700">
                                <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
                                    <Calendar size={16} strokeWidth={1.5} />
                                </div>
                                Unido:{' '}
                                {user?.created_at
                                    ? new Date(user.created_at).toLocaleDateString()
                                    : '—'}
                            </div>
                        </div>
                    </Card>

                    <Card className="p-8 bg-blue-600/5 border-blue-500/10 shadow-none space-y-5">
                        <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                            <Shield size={24} strokeWidth={1.5} />
                        </div>
                        <div>
                            <h4 className="font-bold text-lg text-gray-900">Seguridad</h4>
                            <p className="text-system-gray text-sm font-medium leading-relaxed mt-1">Protege tu acceso y mantén tus datos a salvo.</p>
                        </div>
                        <div className="space-y-3">
                            <Input
                                type="password"
                                placeholder="Contraseña actual"
                                value={passwordData.currentPassword}
                                onChange={e => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                            />
                            <Input
                                type="password"
                                placeholder="Nueva contraseña"
                                value={passwordData.newPassword}
                                onChange={e => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                            />
                            <Input
                                type="password"
                                placeholder="Confirmar nueva contraseña"
                                value={passwordData.confirmPassword}
                                onChange={e => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                            />
                        </div>
                        <Button
                            type="button"
                            onClick={() => void handleChangePassword()}
                            disabled={passwordStatus === 'saving'}
                            className="w-full bg-white border border-gray-100 font-bold rounded-xl h-12 shadow-sm"
                        >
                            {passwordStatus === 'saving' ? 'Actualizando...' : 'Cambiar contraseña'}
                        </Button>
                        {passwordMessage && (
                            <p className={`text-xs font-semibold ${passwordStatus === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                                {passwordMessage}
                            </p>
                        )}
                    </Card>
                </div>

                {/* Information Settings */}
                <div className="lg:col-span-2 space-y-10">
                    <Card className="p-10">
                        <div className="flex items-center gap-4 mb-10">
                            <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center text-blue-600 border border-gray-100 shadow-sm">
                                <User size={24} strokeWidth={1.5} />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900 tracking-tight leading-none">Información Personal</h2>
                                <p className="text-system-gray font-medium text-sm mt-1.5">Cómo te ven los demás en la plataforma.</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Nombre Completo</label>
                                <Input
                                    value={formData.fullName}
                                    onChange={e => setFormData({ ...formData, fullName: e.target.value })}
                                    placeholder="Ej: Juan Pérez"
                                />
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Cargo / Título</label>
                                <div className="relative group">
                                    <Input
                                        value={formData.job_title}
                                        onChange={e => setFormData({ ...formData, job_title: e.target.value })}
                                        placeholder="Ej: Senior Product Designer"
                                        className="pl-12"
                                    />
                                    <Briefcase className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                </div>
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Especialidad</label>
                                <div className="relative group">
                                    <Input
                                        value={formData.specialty}
                                        onChange={e => setFormData({ ...formData, specialty: e.target.value })}
                                        placeholder="Ej: UI/UX, React, Backend"
                                        className="pl-12"
                                    />
                                    <Award className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                </div>
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Email (Sólo Lectura)</label>
                                <div className="relative group">
                                    <Input
                                        value={user?.email || ''}
                                        readOnly
                                        className="pl-12 bg-gray-50 text-gray-400 cursor-not-allowed border-transparent"
                                    />
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300" size={18} strokeWidth={1.5} />
                                </div>
                            </div>
                            <div className="md:col-span-2 space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Biografía</label>
                                <textarea
                                    value={formData.bio}
                                    onChange={e => setFormData({ ...formData, bio: e.target.value })}
                                    maxLength={500}
                                    rows={4}
                                    className="w-full p-5 border border-transparent bg-gray-200/50 focus:bg-white focus:ring-2 focus:ring-blue-500/50 outline-none rounded-2xl font-medium transition-all text-sm leading-relaxed"
                                    placeholder="Cuéntanos un poco sobre ti..."
                                />
                                <p className="text-right text-[9px] font-black text-system-gray uppercase tracking-widest">{formData.bio.length}/500</p>
                            </div>
                        </div>
                    </Card>

                    <Card className="p-10">
                        <div className="flex items-center gap-4 mb-10">
                            <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center text-blue-600 border border-gray-100 shadow-sm">
                                <Globe size={24} strokeWidth={1.5} />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900 tracking-tight leading-none">Presencia Digital</h2>
                                <p className="text-system-gray font-medium text-sm mt-1.5">Tus perfiles públicos para propuestas.</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">LinkedIn</label>
                                <div className="relative group">
                                    <Input
                                        value={formData.linkedin_url}
                                        onChange={e => setFormData({ ...formData, linkedin_url: e.target.value })}
                                        placeholder="linkedin.com/in/usuario"
                                        className="pl-12"
                                    />
                                    <Linkedin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                </div>
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Instagram</label>
                                <div className="relative group">
                                    <Input
                                        value={formData.instagram_url}
                                        onChange={e => setFormData({ ...formData, instagram_url: e.target.value })}
                                        placeholder="instagram.com/usuario"
                                        className="pl-12"
                                    />
                                    <Instagram className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                </div>
                            </div>
                        </div>
                    </Card>

                    <Card className="p-10">
                        <div className="flex items-center gap-4 mb-10">
                            <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center text-blue-600 border border-gray-100 shadow-sm">
                                <Languages size={24} strokeWidth={1.5} />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900 tracking-tight leading-none">Preferencias</h2>
                                <p className="text-system-gray font-medium text-sm mt-1.5">Configuración regional de tu perfil.</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Zona horaria</label>
                                <Input
                                    value={formData.timezone}
                                    onChange={e => setFormData({ ...formData, timezone: e.target.value })}
                                    placeholder="America/Bogota"
                                />
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">Idioma</label>
                                <select
                                    value={formData.language}
                                    onChange={e => setFormData({ ...formData, language: e.target.value })}
                                    className="w-full h-12 rounded-2xl border border-transparent bg-gray-200/50 px-4 text-sm font-medium focus:bg-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                                >
                                    <option value="es">Español</option>
                                    <option value="en">English</option>
                                </select>
                            </div>
                        </div>
                    </Card>

                    <div className="flex justify-end pt-4 pb-20">
                        <AnimatePresence mode='wait'>
                            <motion.button
                                type="submit"
                                layout
                                disabled={status === 'saving'}
                                className={`
                                    h-14 px-10 rounded-2xl font-bold flex items-center gap-3 transition-all shadow-xl active:scale-95 disabled:opacity-70
                                    ${status === 'success'
                                        ? 'bg-green-500 shadow-green-200 text-white'
                                        : status === 'error'
                                            ? 'bg-red-500 shadow-red-200 text-white'
                                            : 'bg-blue-600 shadow-blue-200 text-white hover:bg-blue-700'}
                                `}
                            >
                                {status === 'saving' ? (
                                    <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                ) : status === 'success' ? (
                                    <CheckCircle size={22} className="animate-in zoom-in" strokeWidth={2} />
                                ) : status === 'error' ? (
                                    <span className="text-sm font-black">!</span>
                                ) : (
                                    <Save size={22} strokeWidth={2} />
                                )}
                                <span>
                                    {status === 'saving'
                                        ? 'Guardando...'
                                        : status === 'success'
                                            ? '¡Guardado!'
                                            : status === 'error'
                                                ? 'Error al guardar'
                                                : 'Guardar Cambios'}
                                </span>
                            </motion.button>
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </form>
    );
}
