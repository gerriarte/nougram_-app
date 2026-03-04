
'use client';

import { useCallback, useEffect, useState } from 'react';
import { Equipment, DepreciationResult } from '@/types/equipment';
import { calculateDepreciation } from '@/lib/depreciation';
import { equipmentService } from '@/services/equipmentService';

export function useEquipment() {
    const [equipment, setEquipment] = useState<Equipment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        setLoading(true);
        const items = await equipmentService.getAll();
        setEquipment(items);
        setLoading(false);
    }, []);

    useEffect(() => {
        void refresh();
    }, [refresh]);

    const addEquipment = async (data: Omit<Equipment, 'id' | 'createdAt'>) => {
        setError(null);
        const created = await equipmentService.create(data);
        if (!created) {
            setError('No se pudo crear el equipo');
            return null;
        }
        setEquipment(prev => [created, ...prev]);
        return created;
    };

    const updateEquipment = async (id: string, data: Partial<Equipment>) => {
        setError(null);
        const updated = await equipmentService.update(id, data);
        if (!updated) {
            setError('No se pudo actualizar el equipo');
            return null;
        }
        setEquipment(prev => prev.map(item => (item.id === id ? updated : item)));
        return updated;
    };

    const removeEquipment = async (id: string) => {
        setError(null);
        const ok = await equipmentService.remove(id);
        if (!ok) {
            setError('No se pudo eliminar el equipo');
            return;
        }
        setEquipment(prev => prev.filter(item => item.id !== id));
    };

    const getStats = (eq: Equipment): DepreciationResult => {
        return calculateDepreciation(eq);
    };

    return {
        equipment,
        loading,
        error,
        addEquipment,
        updateEquipment,
        removeEquipment,
        getStats,
        refresh
    };
}
