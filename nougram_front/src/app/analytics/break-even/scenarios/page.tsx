'use client';

import React, { useState } from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { useBreakEven } from '@/hooks/useBreakEven';
import { ScenarioResult, ScenarioConfig } from '@/types/break-even';
import { ScenarioCard } from '@/components/analytics/break-even/scenarios/ScenarioCard';
import { ScenarioComparisonChart } from '@/components/analytics/break-even/scenarios/ScenarioComparisonChart';
import { ScenarioFormModal } from '@/components/analytics/break-even/scenarios/ScenarioFormModal';
import { BreakEvenNav } from '@/components/analytics/break-even/BreakEvenNav';
import { ArrowLeft, Plus } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function BreakEvenScenariosPage() {
    const { data: baseData, isLoading, error, calculateScenario } = useBreakEven();

    // Default Scenarios
    const [scenarios, setScenarios] = useState<ScenarioResult[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingScenario, setEditingScenario] = useState<ScenarioConfig | undefined>(undefined);
    const [isCalculating, setIsCalculating] = useState(false);

    const handleSaveScenario = async (config: Omit<ScenarioConfig, 'id'>) => {
        setIsCalculating(true);
        try {
            if (editingScenario) {
                // Update
                const updatedConfig = { ...config, id: editingScenario.id };
                const result = await calculateScenario(updatedConfig);
                if (result) {
                    setScenarios(scenarios.map(s => s.id === editingScenario.id ? result : s));
                    setEditingScenario(undefined);
                    setIsModalOpen(false);
                }
            } else {
                // Create
                const newConfig = { ...config, id: Math.random().toString(36).substr(2, 9) };
                const result = await calculateScenario(newConfig);
                if (result) {
                    setScenarios([...scenarios, result]);
                    setIsModalOpen(false);
                }
            }
        } catch (e) {
            console.error("Failed to save scenario", e);
        } finally {
            setIsCalculating(false);
        }
    };

    const handleDelete = (id: string) => {
        setScenarios(scenarios.filter(s => s.id !== id));
    };

    const handleEdit = (scenario: ScenarioResult) => {
        setEditingScenario(scenario.config);
        setIsModalOpen(true);
    };

    const openCreateModal = () => {
        setEditingScenario(undefined);
        setIsModalOpen(true);
    };

    if (isLoading) {
        return (
            <AdminLayout>
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
            </AdminLayout>
        );
    }

    if (error || !baseData) {
        return (
            <AdminLayout>
                <div className="p-8 text-center text-red-600">
                    <p>Error: {error || 'No se pudieron cargar los datos base.'}</p>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout>
            <div className="space-y-8 pb-20">
                {/* Header */}
                <BreakEvenNav />

                {/* Header */}
                <div className="flex flex-col gap-4">
                    <div className="flex justify-between items-end">
                        <div className="max-w-2xl">
                            <h1 className="text-2xl font-bold text-gray-900 mb-2">Simulador de Escenarios</h1>
                            <p className="text-gray-500">Crea escenarios hipotéticos para visualizar cómo cambios en BCR, Costos Fijos o Margen afectan tu punto de equilibrio.</p>
                        </div>
                    </div>
                </div>

                {/* Base Scenario Card Mock */}
                <div className="bg-blue-50/50 border border-blue-100 rounded-[24px] p-6">
                    <h3 className="text-blue-900 font-semibold mb-4">Escenario Base (Actual)</h3>
                    <div className="flex gap-8 text-blue-800">
                        <div>
                            <span className="text-xs uppercase tracking-wide opacity-70 block">Horas Equilibrio</span>
                            <span className="text-xl font-bold">{baseData.break_even_hours}h</span>
                        </div>
                        <div>
                            <span className="text-xs uppercase tracking-wide opacity-70 block">Ingresos Equilibrio</span>
                            <span className="text-xl font-bold">{new Intl.NumberFormat('en-US', { style: 'currency', currency: baseData.currency }).format(baseData.break_even_revenue)}</span>
                        </div>
                        <div>
                            <span className="text-xs uppercase tracking-wide opacity-70 block">Horas Faltantes</span>
                            <span className="text-xl font-bold">{baseData.hours_to_break_even}h</span>
                        </div>
                    </div>
                </div>

                {/* Comparison Chart */}
                {scenarios.length > 0 && (
                    <ScenarioComparisonChart baseBreakEven={baseData.break_even_hours} scenarios={scenarios} />
                )}

                {/* List */}
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h2 className="text-lg font-semibold text-gray-900">Escenarios Simulados</h2>
                        <Button
                            onClick={openCreateModal}
                            disabled={isCalculating}
                            className="bg-black text-white hover:bg-gray-800 rounded-full h-9 shadow-md"
                        >
                            <Plus size={16} className="mr-2" /> Agregar Escenario
                        </Button>
                    </div>

                    {scenarios.length === 0 ? (
                        <div className="border-2 border-dashed border-gray-200 rounded-[24px] h-64 flex flex-col items-center justify-center text-center p-8 bg-gray-50/50">
                            <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-gray-400 mb-4">
                                <Plus size={24} />
                            </div>
                            <h3 className="text-gray-900 font-medium mb-1">No hay escenarios creados</h3>
                            <p className="text-gray-500 text-sm max-w-sm mb-4">Empieza simulando cambios en tu nómina, costos o precios para ver el impacto.</p>
                            <Button onClick={openCreateModal} variant="secondary">Simular Primer Escenario</Button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                            {scenarios.map(scenario => (
                                <ScenarioCard
                                    key={scenario.id}
                                    scenario={scenario}
                                    currency={baseData.currency}
                                    onEdit={handleEdit}
                                    onDelete={handleDelete}
                                />
                            ))}
                        </div>
                    )}
                </div>

                <ScenarioFormModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSave={handleSaveScenario}
                    initialData={editingScenario}
                    isLoading={isCalculating}
                />
            </div>
        </AdminLayout>
    );
}
