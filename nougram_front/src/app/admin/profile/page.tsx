
'use client';

import React from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useNougram } from '@/context/NougramCoreContext';

export default function ProfilePage() {
    const { state } = useNougram();

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
                        U
                    </div>
                    <Button variant="secondary" size="sm">Cambiar foto</Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Nombre completo</label>
                        <Input defaultValue="Usuario Demo" />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Email</label>
                        <Input defaultValue="usuario@nougram.com" disabled className="bg-surface-2 text-gray-400" />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Cargo</label>
                        <Input placeholder="Ej: Senior Designer" />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11.5px] font-semibold text-gray-600">Rol</label>
                        <Input defaultValue={state.user.role} disabled className="bg-surface-2 text-gray-400" />
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-[11.5px] font-semibold text-gray-600">Biografía (para propuestas)</label>
                    <textarea
                        className="w-full min-h-[90px] rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-[13px] text-gray-800 placeholder:text-gray-400 focus:border-gray-400 focus:outline-none resize-none transition-colors"
                        placeholder="Escribe una breve descripción profesional..."
                    />
                </div>
            </div>

            {/* Security */}
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                <div className="pb-3 border-b border-gray-100">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">Seguridad</span>
                </div>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-[13.5px] font-semibold text-gray-900">Contraseña</p>
                        <p className="text-[12px] text-gray-500">Cambia tu contraseña de acceso.</p>
                    </div>
                    <Button variant="secondary">Cambiar contraseña</Button>
                </div>
            </div>

            <div className="flex justify-end gap-3">
                <Button variant="secondary">Cancelar</Button>
                <Button className="bg-gray-900 text-white hover:bg-gray-700">Guardar cambios</Button>
            </div>
        </div>
    );
}
