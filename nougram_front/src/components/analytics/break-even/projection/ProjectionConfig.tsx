import React from 'react';
import { Input } from '@/components/ui/Input';
import { Settings } from 'lucide-react';

interface ProjectionConfigProps {
    months: number;
    setMonths: (m: number) => void;
    growthRate: number;
    setGrowthRate: (r: number) => void;
}

export function ProjectionConfig({ months, setMonths, growthRate, setGrowthRate }: ProjectionConfigProps) {
    return (
        <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 h-full">
            <div className="flex items-center gap-2 mb-6">
                <Settings size={20} className="text-gray-400" />
                <h3 className="font-semibold text-gray-900">Configuración</h3>
            </div>

            <div className="space-y-6">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Meses a proyectar</label>
                    <Input
                        type="number"
                        min={1} max={36}
                        value={months}
                        onChange={(e) => setMonths(parseInt(e.target.value) || 12)}
                    />
                    <p className="text-xs text-gray-500">Rango: 1 - 36 meses</p>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Tasa de crecimiento mensual</label>
                    <div className="flex items-center gap-3">
                        <Input
                            type="number"
                            step="0.5"
                            value={growthRate}
                            onChange={(e) => setGrowthRate(parseFloat(e.target.value) || 0)}
                        />
                        <span className="font-medium text-gray-600">%</span>
                    </div>
                    <p className="text-xs text-gray-500">Simula incremento de asignaciones por mes.</p>
                </div>
            </div>
        </div>
    );
}
