
'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/hooks/useAuth';
import { userService } from '@/services/userService';
import {
    User, Mail, Briefcase, Award, Linkedin,
    Globe, Github, Camera, Shield, Save,
    Calendar, Languages, Clock, CheckCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function UserProfileSettings() {
    const { user } = useAuth();
    const [formData, setFormData] = useState({
        fullName: user?.fullName || '',
        job_title: user?.job_title || '',
        specialty: user?.specialty || '',
        bio: user?.bio || '',
        linkedin_url: user?.linkedin_url || '',
        portfolio_url: user?.portfolio_url || '',
        github_url: user?.github_url || '',
        behance_url: user?.behance_url || '',
        timezone: user?.timezone || 'America/Bogota',
        language: user?.language || 'es'
    });
    const [status, setStatus] = useState<'idle' | 'saving' | 'success'>('idle');

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;

        setStatus('saving');
        await userService.updateProfile(user.id, formData);
        setStatus('success');
        setTimeout(() => setStatus('idle'), 2000);
    };

    return (
        <form onSubmit={handleSave} className="space-y-10">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                {/* Profile Card */}
                <div className="lg:col-span-1 space-y-8">
                    <Card className="p-10 text-center relative overflow-hidden group">
                        {/* Material dynamic background */}
                        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-br from-blue-500/10 to-indigo-600/10 animate-pulse" />

                        <div className="relative mt-4 mb-8">
                            <div className="w-32 h-32 rounded-[2.5rem] bg-white p-1 shadow-2xl mx-auto group-hover:rotate-2 transition-transform duration-500 overflow-hidden ring-4 ring-white/50">
                                <div className="w-full h-full rounded-[2.2rem] bg-gray-100 flex items-center justify-center text-gray-400 overflow-hidden relative">
                                    {user?.avatarUrl ? (
                                        <img src={user.avatarUrl} alt={user.fullName} className="w-full h-full object-cover" />
                                    ) : (
                                        <User size={48} strokeWidth={1.5} />
                                    )}
                                    <button type="button" className="absolute inset-0 bg-black/20 backdrop-blur-sm opacity-0 group-hover:opacity-100 flex items-center justify-center text-white transition-opacity">
                                        <Camera size={24} strokeWidth={1.5} />
                                    </button>
                                </div>
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
                                Unido: {new Date(user?.created_at || Date.now()).toLocaleDateString()}
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
                        <Button type="button" variant="secondary" className="w-full bg-white border border-gray-100 font-bold rounded-xl h-12 shadow-sm">
                            Cambiar Contraseña
                        </Button>
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
                                <label className="text-[10px] font-black text-system-gray uppercase tracking-[0.15em] px-1">GitHub</label>
                                <div className="relative group">
                                    <Input
                                        value={formData.github_url}
                                        onChange={e => setFormData({ ...formData, github_url: e.target.value })}
                                        placeholder="github.com/usuario"
                                        className="pl-12"
                                    />
                                    <Github className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={18} strokeWidth={1.5} />
                                </div>
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
                                    ${status === 'success' ? 'bg-green-500 shadow-green-200 text-white' : 'bg-blue-600 shadow-blue-200 text-white hover:bg-blue-700'}
                                `}
                            >
                                {status === 'saving' ? (
                                    <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                ) : status === 'success' ? (
                                    <CheckCircle size={22} className="animate-in zoom-in" strokeWidth={2} />
                                ) : (
                                    <Save size={22} strokeWidth={2} />
                                )}
                                <span>{status === 'saving' ? 'Guardando...' : status === 'success' ? '¡Guardado!' : 'Guardar Cambios'}</span>
                            </motion.button>
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </form>
    );
}
