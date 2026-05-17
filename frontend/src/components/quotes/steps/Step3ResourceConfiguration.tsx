import React from 'react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { ResourceSlider } from '../ResourceSlider';
import { Card } from '@/components/ui/Card';
import { motion } from 'framer-motion';
import { formatCurrency } from '@/lib/utils';

export function Step3ResourceConfiguration() {
    const { state, updateItem } = useQuoteBuilder();

    // Filter items that are relevant for resource configuration (e.g., hourly)
    // We could also include 'fixed' items if we want to adjust quantity or price manually.
    const relevantItems = state.items.filter(item =>
        item.pricingType === 'hourly' || item.pricingType === 'fixed'
    );

    if (relevantItems.length === 0) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500">No has seleccionado servicios configurables aún.</p>
                <p className="text-sm text-gray-400 mt-2">Selecciona al menos un servicio en el paso anterior para continuar con la estimación.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
                <p className="text-[10px] font-black uppercase tracking-wider text-gray-500">Paso 3</p>
                <h2 className="text-xl font-bold tracking-tight text-gray-900">Estimación operativa</h2>
                <p className="text-sm text-gray-600">Ajusta esfuerzo, cantidades y recursos para consolidar el costo del proyecto.</p>
            </div>

            <motion.div
                className="grid gap-6 max-w-2xl mx-auto"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
            >
                {relevantItems.map((item, index) => (
                    <motion.div
                        key={item.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                    >
                        <Card className="p-6 glass-card">
                            <h3 className="font-bold text-lg mb-4">{item.serviceName}</h3>

                            {item.pricingType === 'hourly' ? (
                                <ResourceSlider
                                    label="Horas Estimadas"
                                    value={item.estimatedHours || 0}
                                    onChange={(val) => updateItem(item.id, { estimatedHours: val })}
                                    max={300}
                                />
                            ) : (
                                <ResourceSlider
                                    label="Cantidad / Unidades"
                                    value={item.quantity || 1}
                                    onChange={(val) => updateItem(item.id, { quantity: val })}
                                    max={50}
                                    unit="ud"
                                />
                            )}

                            <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between text-sm">
                                <span className="text-gray-500">
                                    {item.pricingType === 'hourly' ? 'Costo por Hora (BCR)' : 'Precio Unitario'}:
                                    {/* 
                                        Note: internalCost in item is total. 
                                        We don't easily expose unit cost in QuoteItem interface for UI, 
                                        but we can infer or leave it generic 
                                    */}
                                </span>
                                <span className="font-medium text-blue-600">
                                    Precio Cliente: {formatCurrency((item.clientPrice || 0), state.currency)}
                                </span>
                            </div>

                            {/* Margin Feedback */}
                            <div className="mt-2 flex justify-end">
                                <span className={`text-xs ${(item.marginPercentage || 0) < 30 ? 'text-red-500' : 'text-green-500'}`}>
                                    Margen: {Math.round((item.marginPercentage || 0) * 100)}%
                                </span>
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </motion.div>
        </div>
    );
}
