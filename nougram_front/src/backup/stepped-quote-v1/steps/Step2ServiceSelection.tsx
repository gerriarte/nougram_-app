import React, { useEffect, useState } from 'react';
import { useQuoteCreation } from '@/context/QuoteCreationContext';
// import { useGetServices } from '@/hooks/useGetServices'; // Assuming this exists or using mock
import { ServiceBentoGrid, ServiceItem } from '../ServiceBentoGrid';
import { Loader2 } from 'lucide-react';

// Temporary Mock Data if hook doesn't exist
const MOCK_SERVICES: ServiceItem[] = [
    { id: 1, name: 'Diseño UI/UX', description: 'Interfaces modernas y experiencias de usuario optimizadas.', defaultPrice: 1500 },
    { id: 2, name: 'Desarrollo Frontend', description: 'Implementación fiel del diseño con React/Next.js.', defaultPrice: 3000 },
    { id: 3, name: 'Desarrollo Backend', description: 'APIs robustas, bases de datos y lógica de servidor.', defaultPrice: 3500 },
    { id: 4, name: 'Consultoría Estratégica', description: 'Análisis de negocio y roadmap digital.', defaultPrice: 2000 },
    { id: 5, name: 'SEO & Marketing', description: 'Optimización para buscadores y estrategias de crecimiento.', defaultPrice: 1200 },
    { id: 6, name: 'Mantenimiento', description: 'Soporte continuo y actualizaciones mensuales.', defaultPrice: 500 },
];

export function Step2ServiceSelection() {
    const { services: selectedServices, addService, removeService } = useQuoteCreation();
    const [availableServices, setAvailableServices] = useState<ServiceItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Simulate fetch
        setTimeout(() => {
            setAvailableServices(MOCK_SERVICES);
            setIsLoading(false);
        }, 500);
    }, []);

    const handleToggle = (service: ServiceItem) => {
        const isSelected = selectedServices.some(s => s.serviceId === service.id);
        if (isSelected) {
            removeService(service.id);
        } else {
            addService({
                serviceId: service.id,
                serviceName: service.name,
                hours: 10, // Default estimate
                price: service.defaultPrice,
                quantity: 1
            });
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="text-center space-y-2 mb-8">
                <h2 className="text-2xl font-bold tracking-tight">Selecciona los Servicios</h2>
                <p className="text-gray-500">¿Qué incluye esta propuesta?</p>
            </div>

            <ServiceBentoGrid
                services={availableServices}
                selectedIds={selectedServices.map(s => s.serviceId)}
                onToggle={handleToggle}
            />
        </div>
    );
}
