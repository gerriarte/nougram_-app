
'use client';

import { Equipment, DepreciationResult } from '@/types/equipment';
import { calculateDepreciation } from '@/lib/depreciation';
import { useNougram } from '@/context/NougramCoreContext';

export function useEquipment() {
    const { state, addEquipment: addToCore, updateEquipment: updateInCore, removeEquipment: removeFromCore } = useNougram();

    const equipment = state.equipment;

    const addEquipment = async (data: Omit<Equipment, 'id' | 'createdAt'>) => {
        const newEq: Equipment = {
            ...data,
            id: crypto.randomUUID(),
            createdAt: new Date().toISOString()
        };
        addToCore(newEq);
        return newEq;
    };

    const updateEquipment = async (id: string, data: Partial<Equipment>) => {
        updateInCore(id, data);
        const updated = equipment.find(e => e.id === id);
        return updated ? { ...updated, ...data } : null;
    };

    const removeEquipment = async (id: string) => {
        removeFromCore(id);
    };

    const getStats = (eq: Equipment): DepreciationResult => {
        return calculateDepreciation(eq);
    };

    return {
        equipment,
        loading: false,
        error: null,
        addEquipment,
        updateEquipment,
        removeEquipment,
        getStats,
        refresh: async () => undefined
    };
}
