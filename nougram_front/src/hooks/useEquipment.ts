
'use client';

import { useState, useEffect, useCallback } from 'react';
import { Equipment, DepreciationResult } from '@/types/equipment';
import { equipmentService } from '@/services/equipmentService';

export function useEquipment() {
    const [equipment, setEquipment] = useState<Equipment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchEquipment = useCallback(async () => {
        try {
            setLoading(true);
            const data = await equipmentService.getAll();
            setEquipment(data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch equipment');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchEquipment();
    }, [fetchEquipment]);

    const addEquipment = async (data: Omit<Equipment, 'id' | 'createdAt'>) => {
        try {
            const newEq = await equipmentService.create(data);
            setEquipment(prev => [newEq, ...prev]);
            return newEq;
        } catch (err) {
            setError('Failed to create equipment');
            throw err;
        }
    };

    const updateEquipment = async (id: string, data: Partial<Equipment>) => {
        try {
            const updated = await equipmentService.update(id, data);
            setEquipment(prev => prev.map(e => e.id === id ? updated : e));
            return updated;
        } catch (err) {
            setError('Failed to update equipment');
            throw err;
        }
    };

    const removeEquipment = async (id: string) => {
        try {
            await equipmentService.delete(id);
            setEquipment(prev => prev.filter(e => e.id !== id));
        } catch (err) {
            setError('Failed to delete equipment');
            throw err;
        }
    };

    const getStats = (eq: Equipment): DepreciationResult => {
        return equipmentService.calculateCurrentStats(eq);
    };

    return {
        equipment,
        loading,
        error,
        addEquipment,
        updateEquipment,
        removeEquipment,
        getStats,
        refresh: fetchEquipment
    };
}
