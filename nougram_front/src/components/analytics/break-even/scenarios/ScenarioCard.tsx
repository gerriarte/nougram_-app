import React from 'react';
import { ScenarioResult } from '@/types/break-even';
import { Pencil, Trash2, ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface ScenarioCardProps {
    scenario: ScenarioResult;
    onEdit: (scenario: ScenarioResult) => void;
    onDelete: (id: string) => void;
    currency: string;
}

export function ScenarioCard({ scenario, onEdit, onDelete, currency }: ScenarioCardProps) {
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(amount);
    };

    const isPositive = scenario.impact.is_improvement;
    const impactColor = isPositive ? 'text-green-600' : 'text-red-500';
    const impactBg = isPositive ? 'bg-green-50' : 'bg-red-50';

    return (
        <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 relative group">
            <div className="flex justify-between items-start mb-6">
                <h3 className="font-semibold text-lg text-gray-900">{scenario.name}</h3>
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="ghost" size="sm" onClick={() => onEdit(scenario)} className="h-8 w-8 p-0 text-gray-500 hover:text-blue-600">
                        <Pencil size={16} />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => onDelete(scenario.id)} className="h-8 w-8 p-0 text-gray-500 hover:text-red-600">
                        <Trash2 size={16} />
                    </Button>
                </div>
            </div>

            {/* Config Summary - What changed? */}
            <div className="mb-6 p-3 bg-gray-50 rounded-xl text-sm text-gray-600 space-y-1">
                <p className="font-medium text-xs uppercase tracking-wide text-gray-400 mb-2">Cambios Aplicados</p>
                {scenario.config.bcr_multiplier !== 1 && (
                    <div className="flex justify-between">
                        <span>Multiplicador BCR:</span>
                        <span className="font-medium">{scenario.config.bcr_multiplier}x</span>
                    </div>
                )}
                {scenario.config.fixed_costs_adjustment !== 0 && (
                    <div className="flex justify-between">
                        <span>Ajuste Costos Fijos:</span>
                        <span className="font-medium">{scenario.config.fixed_costs_adjustment > 0 ? '+' : ''}{formatCurrency(scenario.config.fixed_costs_adjustment)}</span>
                    </div>
                )}
                {scenario.config.average_margin_adjustment !== 0 && (
                    <div className="flex justify-between">
                        <span>Ajuste Margen:</span>
                        <span className="font-medium">{scenario.config.average_margin_adjustment > 0 ? '+' : ''}{(scenario.config.average_margin_adjustment * 100).toFixed(0)}%</span>
                    </div>
                )}
            </div>

            {/* Impact Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                    <span className="text-xs text-gray-400 uppercase tracking-wide">Nuevo Equilibrio</span>
                    <div className="text-xl font-bold text-gray-900">{scenario.break_even_hours}h</div>
                </div>
                <div>
                    <span className="text-xs text-gray-400 uppercase tracking-wide">Impacto</span>
                    <div className={`flex items-center gap-1 font-medium ${impactColor}`}>
                        {isPositive ? <ArrowDown size={16} /> : <ArrowUp size={16} />}
                        {Math.abs(scenario.impact.hours_change)}h ({scenario.impact.impact_percentage}%)
                    </div>
                </div>
            </div>

            <div className={`p-3 rounded-xl flex items-center gap-3 ${impactBg}`}>
                <div className={`p-1.5 rounded-full ${isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {isPositive ? <ArrowDown size={14} /> : <ArrowUp size={14} />}
                </div>
                <span className={`text-sm font-medium ${isPositive ? 'text-green-800' : 'text-red-800'}`}>
                    {isPositive ? 'Mejora tu posición' : 'Empeora tu posición'}
                </span>
            </div>
        </div>
    );
}
