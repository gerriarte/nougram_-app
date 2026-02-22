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
            <div className="text-center space-y-2 mb-8">
                <h2 className="text-2xl font-bold tracking-tight">Información del Proyecto</h2>
                <p className="text-gray-500">Comencemos por definir los detalles básicos.</p>
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
                            <Label>Moneda</Label>
                            <select
                                value={state.currency}
                                onChange={(e) => updateProjectInfo({ currency: e.target.value as 'USD' | 'COP' })}
                                className="w-full glass-input h-10 rounded-md px-3"
                            >
                                <option value="USD">USD ($)</option>
                                <option value="COP">COP ($)</option>
                            </select>
                        </div>
                    </div>
                </Card>
            </motion.div>
        </div>
    );
}
