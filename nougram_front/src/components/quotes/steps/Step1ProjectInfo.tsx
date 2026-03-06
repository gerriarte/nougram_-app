import React from 'react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { ClientAutocomplete } from '../ClientAutocomplete'; // Reusing this one
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Card } from '@/components/ui/Card';
import { motion } from 'framer-motion';

export function Step1ProjectInfo() {
    // Switching to QuoteBuilderContext
    const { state, updateProjectInfo } = useQuoteBuilder();

    return (
        <div className="space-y-6">
            <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
                <p className="text-[10px] font-black uppercase tracking-wider text-blue-700">Paso 1</p>
                <h2 className="text-xl font-bold tracking-tight text-blue-900">Información del proyecto</h2>
                <p className="text-sm text-blue-800/80">Define el contexto inicial de la estimación y del cliente.</p>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-xl mx-auto space-y-6"
            >
                <Card className="p-6 glass-card space-y-6">
                    <div className="space-y-2">
                        <Label>Nombre del Proyecto</Label>
                        <Input
                            value={state.projectName}
                            onChange={(e) => updateProjectInfo({ projectName: e.target.value })}
                            placeholder="Ej: Rediseño E-commerce 2024"
                            className="glass-input"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label>Cliente</Label>
                        <ClientAutocomplete
                            value={state.clientName}
                            onChange={(name) => updateProjectInfo({ clientName: name })}
                            onSelect={(client) => updateProjectInfo({
                                clientName: client.name,
                                clientEmail: client.email
                                // clientSector not in QuoteBuilderState, ignoring for now or extending state later
                            })}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Email (Opcional)</Label>
                            <Input
                                value={state.clientEmail || ''}
                                onChange={(e) => updateProjectInfo({ clientEmail: e.target.value })}
                                placeholder="cliente@empresa.com"
                                className="glass-input"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Moneda de operación</Label>
                            <Input value={state.currency} disabled className="glass-input" />
                        </div>
                    </div>
                    <div className="rounded-lg border border-gray-200 bg-white/70 px-3 py-2 text-xs text-gray-600">
                        El tipo de proyecto y la descripción se usarán en el paso siguiente para construir la propuesta comercial con IA.
                    </div>
                </Card>
            </motion.div>
        </div>
    );
}
