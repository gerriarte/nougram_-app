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
        description: s.description || 'Componente de la estimación de tu proyecto.',
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
            <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
                <p className="text-[10px] font-black uppercase tracking-wider text-gray-500">Paso 2</p>
                <h2 className="text-xl font-bold tracking-tight text-gray-900">Servicios y alcance</h2>
                <p className="text-sm text-gray-600">Selecciona los componentes de una única estimación del proyecto.</p>
            </div>

            <ServiceBentoGrid
                services={availableServices}
                selectedIds={selectedServiceIds}
                onToggle={handleToggle}
            />
        </div>
    );
}
