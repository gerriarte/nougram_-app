import React from 'react';
import { useQuoteCreation } from '@/context/QuoteCreationContext';
import { ResourceSlider } from '../ResourceSlider';
import { Card } from '@/components/ui/Card'; // Assuming exist
import { motion } from 'framer-motion';

export function Step3ResourceConfiguration() {
    const { services, updateServiceResource } = useQuoteCreation();

    if (services.length === 0) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500">No has seleccionado servicios aún.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="text-center space-y-2 mb-8">
                <h2 className="text-2xl font-bold tracking-tight">Configuración de Recursos</h2>
                <p className="text-gray-500">¿Cuánto tiempo requiere cada servicio?</p>
            </div>

            <motion.div
                className="grid gap-6 max-w-2xl mx-auto"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
            >
                {services.map((service, index) => (
                    <motion.div
                        key={service.serviceId}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                    >
                        <Card className="p-6 glass-card">
                            <h3 className="font-bold text-lg mb-4">{service.serviceName}</h3>
                            <ResourceSlider
                                label="Horas Estimadas"
                                value={service.hours}
                                onChange={(val) => updateServiceResource(service.serviceId, val)}
                                max={200}
                            />

                            <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between text-sm">
                                <span className="text-gray-500">Precio Base: ${service.price}</span>
                                <span className="font-medium text-blue-600">
                                    Subtotal: ${(service.price * (service.quantity || 1)).toLocaleString()}
                                </span>
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </motion.div>
        </div>
    );
}
