import React from 'react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { ServiceBentoGrid, ServiceItem } from '../ServiceBentoGrid';
// import { Loader2 } from 'lucide-react';

export function Step2ServiceSelection() {
    const { state, services, addItem, removeItem } = useQuoteBuilder();

    // Map QuoteBuilder services to BentoGrid items
    const availableServices: ServiceItem[] = services.map(s => ({
        id: s.id,
        name: s.name,
        description: s.pricingType === 'hourly' ? 'Facturación por horas.' : 'Precio fijo o recurrente.',
        defaultPrice: 0 // Not relevant for selection per se, logic handled in context
    }));

    const selectedServiceIds = state.items.map(i => i.serviceId);

    const handleToggle = (service: ServiceItem) => {
        const isSelected = selectedServiceIds.includes(service.id);
        if (isSelected) {
            // Find the item(s) with this serviceId and remove them
            const itemsToRemove = state.items.filter(i => i.serviceId === service.id);
            itemsToRemove.forEach(i => removeItem(i.id));
        } else {
            addItem(service.id);
        }
    };

    return (
        <div className="space-y-6">
            <div className="text-center space-y-2 mb-8">
                <h2 className="text-2xl font-bold tracking-tight">Selecciona los Servicios</h2>
                <p className="text-gray-500">¿Qué incluye esta propuesta?</p>
            </div>

            <ServiceBentoGrid
                services={availableServices}
                selectedIds={selectedServiceIds}
                onToggle={handleToggle}
            />
        </div>
    );
}
