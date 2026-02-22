import React from 'react';
import { useQuoteCreation } from '@/context/QuoteCreationContext';
import { ClientAutocomplete } from '../ClientAutocomplete';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Card } from '@/components/ui/Card'; // Assuming exist
import { motion } from 'framer-motion';

export function Step1ProjectInfo() {
    const { projectInfo, updateProjectInfo } = useQuoteCreation();

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
                            value={projectInfo.name}
                            onChange={(e) => updateProjectInfo({ name: e.target.value })}
                            placeholder="Ej: Rediseño E-commerce 2024"
                            className="glass-input"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label>Cliente</Label>
                        <ClientAutocomplete
                            value={projectInfo.clientName}
                            onChange={(name) => updateProjectInfo({ clientName: name })}
                            onSelect={(client) => updateProjectInfo({
                                clientName: client.name,
                                clientEmail: client.email,
                                clientSector: client.sector
                            })}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Email (Opcional)</Label>
                            <Input
                                value={projectInfo.clientEmail || ''}
                                onChange={(e) => updateProjectInfo({ clientEmail: e.target.value })}
                                placeholder="cliente@empresa.com"
                                className="glass-input"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Moneda</Label>
                            <select
                                value={projectInfo.currency}
                                onChange={(e) => updateProjectInfo({ currency: e.target.value })}
                                className="w-full glass-input h-10 rounded-md px-3"
                            >
                                <option value="USD">USD ($)</option>
                                <option value="COP">COP ($)</option>
                                <option value="EUR">EUR (€)</option>
                            </select>
                        </div>
                    </div>
                </Card>
            </motion.div>
        </div>
    );
}
