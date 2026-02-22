
'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useNougram } from '@/context/NougramCoreContext';

export default function ProfilePage() {
    const { state } = useNougram();

    return (
        <div className="space-y-6 max-w-2xl mx-auto">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Mi Perfil</h1>
                <p className="text-gray-500">Gestiona tu información personal y seguridad.</p>
            </div>

            {/* Personal Info */}
            <Card>
                <CardContent className="p-6 space-y-4">
                    <h3 className="font-semibold text-gray-800 border-b pb-2">Información Básica</h3>

                    <div className="flex items-center gap-6 pb-4">
                        <div className="w-20 h-20 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-3xl border-2 border-blue-50">
                            U
                        </div>
                        <Button variant="secondary" size="sm">Cambiar Foto</Button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-gray-700">Nombre Completo</label>
                            <Input defaultValue="Usuario Demo" />
                        </div>
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-gray-700">Email</label>
                            <Input defaultValue="usuario@nougram.com" disabled className="bg-gray-50" />
                        </div>
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-gray-700">Cargo</label>
                            <Input placeholder="Ej: Senior Designer" />
                        </div>
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-gray-700">Rol</label>
                            <Input defaultValue={state.user.role} disabled className="bg-gray-50" />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-sm font-medium text-gray-700">Biografía (para propuestas)</label>
                        <textarea
                            className="w-full min-h-[100px] p-3 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Escribe una breve descripción profesional..."
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Security */}
            <Card>
                <CardContent className="p-6 space-y-4">
                    <h3 className="font-semibold text-gray-800 border-b pb-2">Seguridad</h3>
                    <div className="flex justify-between items-center">
                        <div>
                            <p className="font-medium text-gray-900">Contraseña</p>
                            <p className="text-sm text-gray-500">Cambiar tu contraseña de acceso.</p>
                        </div>
                        <Button variant="secondary">Cambiar Contraseña</Button>
                    </div>
                </CardContent>
            </Card>

            <div className="flex justify-end gap-4">
                <Button variant="secondary">Cancelar</Button>
                <Button>Guardar Cambios</Button>
            </div>
        </div>
    );
}
