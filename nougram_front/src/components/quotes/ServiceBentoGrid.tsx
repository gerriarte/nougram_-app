import React from 'react';
import { motion } from 'framer-motion';
import { Check, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ServiceItem {
    id: number;
    name: string;
    description?: string;
    defaultPrice: number;
}

interface ServiceBentoGridProps {
    services: ServiceItem[];
    selectedIds: number[];
    onToggle: (service: ServiceItem) => void;
    className?: string;
}

export function ServiceBentoGrid({ services, selectedIds, onToggle, className }: ServiceBentoGridProps) {
    const gridLayout = [
        "lg:col-span-2 lg:row-span-1", // Large
        "lg:col-span-1 lg:row-span-1", // Small
        "lg:col-span-1 lg:row-span-1", // Small
        "lg:col-span-1 lg:row-span-2", // Tall
        "lg:col-span-2 lg:row-span-1", // Large
        "lg:col-span-1 lg:row-span-1", // Small
    ];

    return (
        <div className={cn("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-[160px]", className)}>
            {services.map((service, index) => {
                const isSelected = selectedIds.includes(service.id);
                const layoutClass = gridLayout[index % gridLayout.length];

                return (
                    <motion.div
                        key={service.id}
                        layoutId={`service-${service.id}`}
                        onClick={() => onToggle(service)}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: index * 0.05 }}
                        className={cn(
                            "group relative p-6 rounded-3xl cursor-pointer border transition-all duration-300 flex flex-col justify-between overflow-hidden",
                            layoutClass,
                            isSelected
                                ? "bg-white border-blue-500 ring-2 ring-blue-500/20 shadow-lg"
                                : "glass-card hover:bg-white/80 hover:scale-[1.02]"
                        )}
                    >
                        <div className="flex justify-between items-start z-10">
                            <h3 className={cn("font-bold text-lg", isSelected ? "text-blue-600" : "text-gray-900")}>
                                {service.name}
                            </h3>
                            <div className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center transition-colors",
                                isSelected ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-400 group-hover:bg-blue-100 group-hover:text-blue-500"
                            )}>
                                {isSelected ? <Check size={16} /> : <Plus size={16} />}
                            </div>
                        </div>

                        {service.description && (
                            <p className="text-sm text-gray-500 line-clamp-2 z-10 mt-auto">
                                {service.description}
                            </p>
                        )}

                        {/* Background Decoration */}
                        <div className={cn(
                            "absolute -right-4 -bottom-4 w-24 h-24 rounded-full blur-2xl transition-all duration-500",
                            isSelected ? "bg-blue-200/50" : "bg-gray-200/20 group-hover:bg-blue-100/30"
                        )} />
                    </motion.div>
                );
            })}
        </div>
    );
}
