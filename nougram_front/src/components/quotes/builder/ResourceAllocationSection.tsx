
import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { ResourceAllocationModal } from './ResourceAllocationModal';
import { ResourceAllocation } from '@/types/quote-builder';
import { Trash2, Edit2, Users, Activity, AlertCircle, Calendar, Plus, UserPlus, Clock } from 'lucide-react';
import { TeamAvailabilityDashboard } from './TeamAvailabilityDashboard';
import { AllocationTimeline } from './AllocationTimeline';

export function ResourceAllocationSection() {
    const {
        state,
        toggleResourceAllocation,
        teamMembers,
        addResourceAllocation,
        updateResourceAllocation,
        removeResourceAllocation,
        getMemberUtilization
    } = useQuoteBuilder();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingAllocation, setEditingAllocation] = useState<ResourceAllocation | null>(null);

    const handleAdd = () => {
        setEditingAllocation(null);
        setIsModalOpen(true);
    };

    const handleEdit = (alloc: ResourceAllocation) => {
        setEditingAllocation(alloc);
        setIsModalOpen(true);
    };

    const handleSaveAllocation = (alloc: ResourceAllocation) => {
        if (editingAllocation) {
            updateResourceAllocation(editingAllocation.id, alloc);
        } else {
            addResourceAllocation(alloc);
        }
    };

    const totalHours = state.resourceAllocations.reduce((sum, a) => sum + a.hours, 0);

    return (
        <Card className="border-0 shadow-xl bg-white overflow-hidden ring-1 ring-gray-100">
            <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-purple-500 to-blue-500" />
            <CardContent className="p-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-2xl transition-all duration-500 ${state.showResourceAllocation ? 'bg-purple-100 text-purple-600 shadow-inner' : 'bg-gray-100 text-gray-400'}`}>
                            <Users size={24} />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h2 className="text-xl font-black text-gray-900 tracking-tight">Asignación de Recursos</h2>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={state.showResourceAllocation}
                                        onChange={toggleResourceAllocation}
                                        className="sr-only peer"
                                    />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                                </label>
                            </div>
                            <p className="text-sm text-gray-500 font-medium mt-1">Gestión avanzada de capacidad y cronogramas del equipo.</p>
                        </div>
                    </div>

                    {state.showResourceAllocation && (
                        <Button
                            onClick={handleAdd}
                            className="bg-purple-600 hover:bg-purple-700 text-white shadow-lg shadow-purple-200 transition-all hover:scale-105 active:scale-95 flex items-center gap-2 group"
                        >
                            <UserPlus size={18} className="group-hover:rotate-12 transition-transform" />
                            <span>Agregar Asignación</span>
                        </Button>
                    )}
                </div>

                {state.showResourceAllocation ? (
                    <div className="space-y-8 animate-in fade-in slide-in-from-top-4 duration-500">
                        {/* Interactive Summary Components */}
                        <div className="grid grid-cols-1 gap-6">
                            <TeamAvailabilityDashboard />
                            <AllocationTimeline />
                        </div>

                        {/* Resource List Section */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em]">Detalle de Asignaciones</h3>
                                <div className="h-px flex-1 bg-gray-100 mx-4" />
                                <span className="text-[10px] font-bold text-gray-500 bg-gray-50 px-2 py-1 rounded">
                                    {state.resourceAllocations.length} {state.resourceAllocations.length === 1 ? 'Recurso' : 'Recursos'}
                                </span>
                            </div>

                            {state.resourceAllocations.length === 0 ? (
                                <div className="text-center py-16 px-4 border-2 border-dashed border-gray-100 rounded-3xl bg-gray-50/50">
                                    <div className="w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-100 flex items-center justify-center mx-auto mb-4 text-gray-300">
                                        <Users size={32} />
                                    </div>
                                    <p className="text-gray-500 font-bold">No haz asignado recursos todavía</p>
                                    <p className="text-xs text-gray-400 mt-1 mb-6">Empieza agregando miembros del equipo a esta cotización.</p>
                                    <Button variant="secondary" onClick={handleAdd} className="border-purple-200 text-purple-600 hover:bg-purple-50">
                                        + Primer Recurso
                                    </Button>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {state.resourceAllocations.map(alloc => {
                                        const member = teamMembers.find(m => m.id === alloc.teamMemberId);
                                        if (!member) return null;

                                        const util = getMemberUtilization(member.id);
                                        const isCritical = util.percentage > 100;

                                        return (
                                            <div
                                                key={alloc.id}
                                                className={`group relative p-5 rounded-2xl border transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${isCritical
                                                    ? 'border-red-100 bg-gradient-to-br from-red-50 to-white'
                                                    : 'border-gray-100 bg-white hover:border-purple-100'
                                                    }`}
                                            >
                                                <div className="flex justify-between items-start">
                                                    <div className="flex gap-4">
                                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-black shrink-0 shadow-sm border-2 border-white ${isCritical ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'
                                                            }`}>
                                                            {member.name[0]}
                                                        </div>
                                                        <div>
                                                            <div className="flex flex-col">
                                                                <h4 className="font-extrabold text-gray-900 group-hover:text-purple-700 transition-colors uppercase text-sm tracking-tight">{member.name}</h4>
                                                                <span className="text-[10px] font-bold text-gray-400 mt-0.5 truncate max-w-[150px]">
                                                                    {alloc.role || member.role}
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center gap-3 mt-3">
                                                                <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-50 rounded-lg border border-gray-100">
                                                                    <Clock size={12} className="text-gray-400" />
                                                                    <span className="text-xs font-black text-gray-700">{alloc.hours}h</span>
                                                                </div>
                                                                {alloc.startDate && (
                                                                    <div className="flex items-center gap-1.5 px-2 py-1 bg-blue-50/50 rounded-lg border border-blue-50">
                                                                        <Calendar size={12} className="text-blue-500" />
                                                                        <span className="text-[10px] font-bold text-blue-600">
                                                                            {new Date(alloc.startDate).toLocaleDateString(undefined, { day: '2-digit', month: 'short' })}
                                                                        </span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <div className="flex flex-col items-end gap-3">
                                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <button
                                                                onClick={() => handleEdit(alloc)}
                                                                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
                                                                title="Editar"
                                                            >
                                                                <Edit2 size={14} />
                                                            </button>
                                                            <button
                                                                onClick={() => removeResourceAllocation(alloc.id)}
                                                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                                                title="Eliminar"
                                                            >
                                                                <Trash2 size={14} />
                                                            </button>
                                                        </div>
                                                        {isCritical && (
                                                            <div className="flex items-center gap-1 text-[9px] text-red-600 font-black bg-red-100/50 px-2 py-1 rounded-full border border-red-200 shadow-sm animate-pulse">
                                                                <AlertCircle size={10} /> CRÍTICO
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                {alloc.notes && (
                                                    <div className="mt-4 pt-3 border-t border-gray-50">
                                                        <p className="text-[11px] text-gray-400 italic line-clamp-2">“{alloc.notes}”</p>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {state.resourceAllocations.length > 0 && (
                                <div className="flex justify-between items-center py-6 px-1 border-t border-gray-100 bg-gradient-to-r from-transparent via-gray-50/30 to-transparent">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-purple-500 animate-ping" />
                                        <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Resumen de Esfuerzo</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-3xl font-black text-gray-900">{totalHours}</span>
                                            <span className="text-sm font-bold text-gray-400 uppercase">Horas Totales</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="bg-gray-50 rounded-3xl p-12 text-center border border-gray-100">
                        <div className="w-20 h-20 bg-white rounded-[2rem] shadow-xl flex items-center justify-center mx-auto mb-6 text-gray-200 border border-gray-50">
                            <Users size={40} className="opacity-50" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-400">La asignación de recursos está desactivada</h3>
                        <p className="text-sm text-gray-400 mt-2 max-w-xs mx-auto">Actívala para gestionar roles específicos, validar la capacidad del equipo y visualizar cronogramas.</p>
                        <Button
                            variant="primary"
                            onClick={toggleResourceAllocation}
                            className="mt-8 bg-purple-600 hover:bg-purple-700 text-white"
                        >
                            Activar Ahora
                        </Button>
                    </div>
                )}

                <ResourceAllocationModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSave={handleSaveAllocation}
                    allocationToEdit={editingAllocation}
                />
            </CardContent>
        </Card>
    );
}
