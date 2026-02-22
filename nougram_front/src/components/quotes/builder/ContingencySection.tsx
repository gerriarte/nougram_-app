'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Shield } from 'lucide-react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';

export function ContingencySection() {
    const { state, setContingency, summary } = useQuoteBuilder();

    const contingency = state.contingency || { description: '', type: 'percentage', value: 0 };
    const isActive = !!state.contingency;

    const handleToggle = () => {
        if (isActive) {
            setContingency(undefined);
        } else {
            setContingency({ description: 'Imprevistos Generales', type: 'percentage', value: 5 });
        }
    };

    const updateContingency = (updates: Partial<typeof contingency>) => {
        setContingency({ ...contingency, ...updates });
    };

    return (
        <Card className={`transition-all duration-300 ${isActive ? 'border-orange-200 bg-orange-50/30' : 'border-gray-200 bg-white'}`}>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${isActive ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500'}`}>
                            <Shield size={20} />
                        </div>
                        <div>
                            <CardTitle className="text-lg">Gestión de Imprevistos</CardTitle>
                            <CardDescription>Reserva fondos para cubrir riesgos o costos no planeados.</CardDescription>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={isActive} onChange={handleToggle} />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-500"></div>
                        </label>
                    </div>
                </div>
            </CardHeader>

            {isActive && (
                <CardContent className="space-y-4 animate-in fade-in slide-in-from-top-2">
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                        {/* Description */}
                        <div className="md:col-span-6">
                            <label className="text-xs font-semibold text-gray-600 uppercase mb-1 block">Descripción del Riesgo</label>
                            <Input
                                value={contingency.description}
                                onChange={e => updateContingency({ description: e.target.value })}
                                placeholder="Ej: Variación en tasa de cambio, Licencias extra..."
                                className="bg-white border-orange-200 focus:border-orange-400"
                            />
                        </div>

                        {/* Type Selector */}
                        <div className="md:col-span-3">
                            <label className="text-xs font-semibold text-gray-600 uppercase mb-1 block">Tipo de Cálculo</label>
                            <div className="flex rounded-lg border border-orange-200 bg-white p-1">
                                <button
                                    onClick={() => updateContingency({ type: 'percentage' })}
                                    className={`flex-1 text-xs py-1.5 px-2 rounded-md transition-colors ${contingency.type === 'percentage' ? 'bg-orange-100 text-orange-800 font-medium' : 'text-gray-500 hover:bg-gray-50'}`}
                                >
                                    Porcentaje (%)
                                </button>
                                <button
                                    onClick={() => updateContingency({ type: 'fixed' })}
                                    className={`flex-1 text-xs py-1.5 px-2 rounded-md transition-colors ${contingency.type === 'fixed' ? 'bg-orange-100 text-orange-800 font-medium' : 'text-gray-500 hover:bg-gray-50'}`}
                                >
                                    Valor Fijo ($)
                                </button>
                            </div>
                        </div>

                        {/* Value Input */}
                        <div className="md:col-span-3">
                            <label className="text-xs font-semibold text-gray-600 uppercase mb-1 block">
                                {contingency.type === 'percentage' ? 'Porcentaje' : 'Valor Total'}
                            </label>
                            <div className="relative">
                                <Input
                                    type="number"
                                    min="0"
                                    value={contingency.value}
                                    onChange={e => updateContingency({ value: parseFloat(e.target.value) || 0 })}
                                    className="bg-white border-orange-200 focus:border-orange-400 font-bold text-gray-800 pr-8"
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 font-bold">
                                    {contingency.type === 'percentage' ? '%' : '$'}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Summary Feedback */}
                    <div className="bg-orange-100/50 rounded-lg p-3 flex justify-between items-center text-sm border border-orange-100">
                        <span className="text-orange-800">
                            Impacto en la cotización:
                        </span>
                        <div className="flex gap-4">
                            <div className="text-right">
                                <span className="block text-xs text-orange-600/70">Costo Adicional</span>
                                <span className="font-bold text-orange-900">
                                    + {summary.contingencyAmount?.toLocaleString('es-CO', { style: 'currency', currency: state.currency, maximumFractionDigits: 0 })}
                                </span>
                            </div>
                            <div className="text-right pl-4 border-l border-orange-200/50">
                                <span className="block text-xs text-orange-600/70">Total con Imprevistos</span>
                                <span className="font-bold text-orange-900">
                                    {summary.contingencyTotal?.toLocaleString('es-CO', { style: 'currency', currency: state.currency, maximumFractionDigits: 0 })}
                                </span>
                            </div>
                        </div>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
