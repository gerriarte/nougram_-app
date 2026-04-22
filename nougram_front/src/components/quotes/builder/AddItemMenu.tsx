'use client';

import React from 'react';
import { Clock, Briefcase, Repeat, Truck } from 'lucide-react';
import { cn } from '@/lib/utils';

type ItemType = 'hourly' | 'fixed' | 'recurring' | 'vendor';

interface ItemTypeConfig {
    id: ItemType;
    label: string;
    description: string;
    Icon: React.ElementType;
    tintClass: string;
    inkClass: string;
}

const ITEM_TYPES: ItemTypeConfig[] = [
    {
        id: 'hourly',
        label: 'Por horas',
        description: 'Recurso × horas',
        Icon: Clock,
        tintClass: 'bg-primary-soft text-primary',
        inkClass: 'text-primary',
    },
    {
        id: 'fixed',
        label: 'Cobro fijo',
        description: 'Precio cerrado',
        Icon: Briefcase,
        tintClass: 'bg-blue-50 text-blue-700',
        inkClass: 'text-blue-700',
    },
    {
        id: 'recurring',
        label: 'Mensual',
        description: 'Retainer / fee',
        Icon: Repeat,
        tintClass: 'bg-success-soft text-green-700',
        inkClass: 'text-green-700',
    },
    {
        id: 'vendor',
        label: 'Proveedor',
        description: 'Costo pass-through',
        Icon: Truck,
        tintClass: 'bg-warning-soft text-amber-700',
        inkClass: 'text-amber-700',
    },
];

interface AddItemMenuProps {
    onAdd: (type: ItemType) => void;
    className?: string;
}

export function AddItemMenu({ onAdd, className }: AddItemMenuProps) {
    return (
        <div className={cn('grid grid-cols-2 gap-3 sm:grid-cols-4', className)}>
            {ITEM_TYPES.map(({ id, label, description, Icon, tintClass, inkClass }) => (
                <button
                    key={id}
                    type="button"
                    onClick={() => onAdd(id)}
                    className="group flex flex-col items-start gap-3 rounded-xl border border-dashed border-gray-200 bg-white p-4 text-left transition-all hover:border-primary hover:bg-primary-soft"
                >
                    <div className={cn('flex h-8 w-8 items-center justify-center rounded-lg', tintClass)}>
                        <Icon size={15} strokeWidth={2} />
                    </div>
                    <div>
                        <div className={cn('text-[13px] font-semibold', inkClass, 'group-hover:text-primary')}>
                            {label}
                        </div>
                        <div className="mt-0.5 text-[11px] text-gray-400">{description}</div>
                    </div>
                </button>
            ))}
        </div>
    );
}

export { ITEM_TYPES };
export type { ItemType };
