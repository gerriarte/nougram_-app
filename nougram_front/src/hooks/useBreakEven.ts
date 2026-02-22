import { useState, useEffect, useCallback } from 'react';
import {
    BreakEvenAnalysisResponse,
    ScenarioConfig,
    ScenarioResult,
    BreakEvenProjectionResponse
} from '@/types/break-even';
import { breakEvenService } from '@/services/breakEvenService';

export function useBreakEven() {
    const [data, setData] = useState<BreakEvenAnalysisResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const result = await breakEvenService.getAnalysis();
            setData(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Error al cargar datos de punto de equilibrio');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const calculateScenario = async (config: ScenarioConfig): Promise<ScenarioResult | null> => {
        if (!data) return null;
        try {
            return await breakEvenService.calculateScenario(data, config);
        } catch (err) {
            console.error("Error calculating scenario", err);
            return null;
        }
    };

    const generateProjection = async (months: number, growthRate: number): Promise<BreakEvenProjectionResponse | null> => {
        if (!data) return null;
        try {
            return await breakEvenService.generateProjection(data, months, growthRate);
        } catch (err) {
            console.error("Error generating projection", err);
            return null;
        }
    };

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return {
        data,
        isLoading,
        error,
        refresh: fetchData,
        calculateScenario,
        generateProjection
    };
}
