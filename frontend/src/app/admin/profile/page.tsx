
'use client';

import React, { useState } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { userService } from '@/services/userService';

export default function ProfilePage() {
    const { user } = useAuth();

    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
    });
    const [passwordStatus, setPasswordStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
    const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

    const userInitials = user?.fullName
        ? user.fullName
            .split(' ')
            .filter(Boolean)
            .slice(0, 2)
            .map((part) => part[0]?.toUpperCase())
            .join('')
        : 'U';

    const handleChangePassword = async () => {
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
        if (passwordData.currentPassword === passwordData.newPassword) {
            setPasswordStatus('error');
            setPasswordMessage('La nueva contraseña debe ser diferente a la actual.');
            return;
        }

        setPasswordStatus('saving');
        try {
            await userService.changePassword(passwordData.currentPassword, passwordData.newPassword);
            setPasswordStatus('success');
            setPasswordMessage('Contraseña actualizada correctamente.');
            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
            setTimeout(() => {
                setPasswordStatus('idle');
                setPasswordMessage(null);
            }, 2500);
        } catch (error) {
            setPasswordStatus('error');
            setPasswordMessage(error instanceof Error ? error.message : 'No se pudo actualizar la contraseña.');
        }
    };

    return (
        <div className="space-y-5 max-w-2xl">
            <div>
                <h1 className="text-[20px] font-bold text-gray-900">Mi perfil</h1>
                <p className="text-[13px] text-gray-500 mt-0.5">Gestiona tu información personal y seguridad.</p>
            </div>

            {/* Personal Info */}
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                <div className="pb-3 border-b border-gray-100">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">Información básica</span>
                </div>

                <div className="flex items-center gap-4 pb-2">
                    <div className="w-14 h-14 rounded-full bg-primary-soft text-primary flex items-center justify-center font-bold text-2xl">
                        {userInitials}
                    </div>
                    <div>
                        <p className="text-[14px] font-semibold text-gray-900">{user?.fullName || '—'}</p>
                        <p className="text-[12px] text-gray-500">{user?.email || '—'}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Nombre completo</label>
                        <Input value={user?.fullName || ''} readOnly className="bg-surface-2 text-gray-400" />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Email</label>
                        <Input value={user?.email || ''} readOnly className="bg-surface-2 text-gray-400" />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Rol</label>
                        <Input value={(user?.role || '').replace('_', ' ')} readOnly className="bg-surface-2 text-gray-400" />
                    </div>
                </div>
            </div>

            {/* Security — functional password change */}
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                <div className="pb-3 border-b border-gray-100">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">Seguridad</span>
                </div>
                <div>
                    <p className="text-[13.5px] font-semibold text-gray-900">Cambiar contraseña</p>
                    <p className="text-[12px] text-gray-500">Actualiza tu contraseña de acceso. Mínimo 8 caracteres.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Contraseña actual</label>
                        <Input
                            type="password"
                            autoComplete="current-password"
                            placeholder="••••••••"
                            value={passwordData.currentPassword}
                            onChange={e => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Nueva contraseña</label>
                        <Input
                            type="password"
                            autoComplete="new-password"
                            placeholder="••••••••"
                            value={passwordData.newPassword}
                            onChange={e => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Confirmar nueva</label>
                        <Input
                            type="password"
                            autoComplete="new-password"
                            placeholder="••••••••"
                            value={passwordData.confirmPassword}
                            onChange={e => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                        />
                    </div>
                </div>

                {passwordMessage && (
                    <p className={`text-[12px] font-semibold ${passwordStatus === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                        {passwordMessage}
                    </p>
                )}

                <div className="flex justify-end">
                    <Button
                        type="button"
                        onClick={() => void handleChangePassword()}
                        disabled={passwordStatus === 'saving'}
                        className="bg-gray-900 text-white hover:bg-gray-700"
                    >
                        {passwordStatus === 'saving' ? 'Actualizando...' : 'Cambiar contraseña'}
                    </Button>
                </div>
            </div>
        </div>
    );
}
