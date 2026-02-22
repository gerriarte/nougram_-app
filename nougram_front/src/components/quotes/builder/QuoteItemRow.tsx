
'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { QuoteItem, Service, ResourceAllocation } from '@/types/quote-builder';
import { Trash2, Plus, Users, Clock, Calendar, Check, X, Edit2 } from 'lucide-react';

interface QuoteItemRowProps {
    item: QuoteItem;
    service: Service;
}

export function QuoteItemRow({ item, service }: QuoteItemRowProps) {
    const { updateItem, removeItem, state, teamMembers } = useQuoteBuilder();
    const [isAddingResource, setIsAddingResource] = useState(false);
    const [selectedMemberId, setSelectedMemberId] = useState<number | ''>('');
    const [newResourceHours, setNewResourceHours] = useState<number>(10);
    const [isEditingTitle, setIsEditingTitle] = useState(false);

    // Determine Margin Color
    let marginColor = 'text-gray-400';
    if (item.internalCost > 0) {
        if (item.marginPercentage >= 30) marginColor = 'text-green-600';
        else if (item.marginPercentage >= 15) marginColor = 'text-yellow-600';
        else marginColor = 'text-red-500 font-bold';
    }

    const handleAddResource = () => {
        if (!selectedMemberId) return;

        const member = teamMembers.find(m => m.id === Number(selectedMemberId));
        if (!member) return;

        const newAlloc: ResourceAllocation = {
            id: crypto.randomUUID(),
            teamMemberId: member.id,
            hours: newResourceHours,
            role: member.role
        };

        const currentAllocations = item.allocations || [];
        updateItem(item.id, { allocations: [...currentAllocations, newAlloc] });

        setIsAddingResource(false);
        setSelectedMemberId('');
        setNewResourceHours(10);
    };

    const removeResource = (allocId: string) => {
        const currentAllocations = item.allocations || [];
        updateItem(item.id, { allocations: currentAllocations.filter(a => a.id !== allocId) });
    };

    // Calculate total hours from allocations
    const totalAllocatedHours = (item.allocations || []).reduce((sum, a) => sum + a.hours, 0);

    return (
        <Card className="p-5 bg-white border border-gray-100 shadow-sm relative group transition-all hover:shadow-md hover:border-gray-200">
            {/* Delete Button */}
            <Button
                variant="destructive"
                size="sm"
                className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-all h-7 w-7 p-0 rounded-full"
                onClick={() => removeItem(item.id)}
            >
                <Trash2 size={12} />
            </Button>

            <div className="space-y-4">
                {/* Header with Editable Title */}
                <div className="flex items-center gap-3 border-b border-gray-50 pb-3">
                    <div className={`p-2 rounded-lg ${item.pricingType === 'recurring' ? 'bg-purple-50 text-purple-600' : 'bg-blue-50 text-blue-600'}`}>
                        {item.pricingType === 'recurring' ? <Calendar size={18} /> : <Clock size={18} />}
                    </div>
                    <div className="flex-1">
                        {!isEditingTitle ? (
                            <div className="flex items-center gap-2 group/title cursor-pointer" onClick={() => setIsEditingTitle(true)}>
                                <h3 className="font-bold text-gray-900 text-sm hover:text-blue-600 transition-colors">
                                    {item.serviceName}
                                </h3>
                                <Edit2 size={12} className="text-gray-300 opacity-0 group-hover/title:opacity-100 transition-opacity" />
                            </div>
                        ) : (
                            <div className="flex items-center gap-2">
                                <Input
                                    autoFocus
                                    className="h-7 text-sm font-bold bg-gray-50 border-blue-200"
                                    value={item.serviceName}
                                    onChange={e => updateItem(item.id, { serviceName: e.target.value })}
                                    onBlur={() => setIsEditingTitle(false)}
                                    onKeyDown={e => e.key === 'Enter' && setIsEditingTitle(false)}
                                />
                                <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => setIsEditingTitle(false)}>
                                    <Check size={14} className="text-green-600" />
                                </Button>
                            </div>
                        )}
                        <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                            {item.pricingType.replace('_', ' ')}
                        </span>
                    </div>
                </div>

                {/* Inputs Row */}
                <div className="grid grid-cols-12 gap-6 items-start">

                    {/* Resources Section - NOW AVAILABLE FOR ALL TYPES */}
                    <div className="col-span-12 md:col-span-6 space-y-3">
                        <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                            <div className="flex justify-between items-center mb-3">
                                <label className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                                    Recursos {item.pricingType === 'recurring' ? '(Mensual)' : ''}
                                </label>
                                {item.pricingType === 'hourly' && (
                                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                                        Total: {totalAllocatedHours}h
                                    </span>
                                )}
                            </div>

                            {(!item.allocations || item.allocations.length === 0) && (
                                <div className="text-center py-4 text-xs text-gray-400 italic">
                                    No hay recursos asignados.
                                    {item.pricingType === 'hourly' && ' Agrega recursos para calcular el costo.'}
                                </div>
                            )}

                            <div className="space-y-2">
                                {item.allocations?.map(alloc => {
                                    const member = teamMembers.find(m => m.id === alloc.teamMemberId);
                                    return (
                                        <div key={alloc.id} className="flex items-center justify-between bg-white p-2 rounded-lg border border-gray-100 shadow-sm text-sm">
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-500">
                                                    {member?.name[0]}
                                                </div>
                                                <span className="font-medium text-gray-700">{member?.name || 'Desconocido'}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-gray-500 bg-gray-50 px-2 py-0.5 rounded text-xs">
                                                    {alloc.hours}h {item.pricingType === 'recurring' ? '/mes' : ''}
                                                </span>
                                                <button onClick={() => removeResource(alloc.id)} className="text-gray-300 hover:text-red-500">
                                                    <Trash2 size={12} />
                                                </button>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>

                            {/* Add Resource UI */}
                            <div className="mt-3 pt-3 border-t border-gray-200/50">
                                {!isAddingResource ? (
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setIsAddingResource(true)}
                                        className="w-full text-blue-600 hover:text-blue-700 hover:bg-blue-50 text-xs h-8"
                                    >
                                        <Plus size={12} className="mr-1.5" /> Agregar Recurso
                                    </Button>
                                ) : (
                                    <div className="flex items-end gap-2 animate-in fade-in slide-in-from-top-1">
                                        <div className="flex-1 space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400">Miembro</label>
                                            <select
                                                className="w-full h-8 text-xs rounded-md border-gray-200 bg-white"
                                                value={selectedMemberId}
                                                onChange={e => setSelectedMemberId(Number(e.target.value))}
                                            >
                                                <option value="">Seleccionar...</option>
                                                {teamMembers.map(m => (
                                                    <option key={m.id} value={m.id}>{m.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="w-20 space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400">Horas</label>
                                            <Input
                                                type="number"
                                                className="h-8 text-xs"
                                                value={newResourceHours}
                                                onChange={e => setNewResourceHours(Number(e.target.value))}
                                            />
                                        </div>
                                        <div className="flex gap-1">
                                            <Button size="sm" onClick={handleAddResource} disabled={!selectedMemberId} className="h-8 px-3 bg-blue-600">
                                                ✓
                                            </Button>
                                            <Button size="sm" variant="ghost" onClick={() => setIsAddingResource(false)} className="h-8 px-2">
                                                ✕
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Configuration & Financials Column */}
                    <div className="col-span-12 md:col-span-6 space-y-4">

                        {/* Specific Inputs based on Pricing Type */}

                        {/* HOURLY - No specific input needed (driven by resources), just info */}
                        {item.pricingType === 'hourly' && (
                            <div className="bg-blue-50/50 p-3 rounded-xl border border-blue-100 text-xs text-blue-800">
                                <p>El precio se calcula automáticamente basado en las horas asignadas y el margen objetivo.</p>
                            </div>
                        )}

                        {/* FIXED - Client Input + Read-only Cost */}
                        {item.pricingType === 'fixed' && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-gray-500">Costo Base (Recursos)</label>
                                    <div className="text-sm text-gray-500 px-3 py-2 bg-gray-100 rounded border border-transparent font-mono">
                                        ${item.internalCost.toLocaleString()}
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold text-gray-500">Cantidad</label>
                                    <Input
                                        type="number"
                                        className="bg-white h-9"
                                        value={item.quantity || 1}
                                        onChange={e => updateItem(item.id, { quantity: parseFloat(e.target.value) || 1 })}
                                    />
                                </div>
                                <div className="col-span-2 space-y-1.5">
                                    <label className="text-xs font-bold text-gray-700">Precio Fijo (Cliente)</label>
                                    <Input
                                        type="number"
                                        className="bg-white h-9 font-bold"
                                        value={item.fixedPrice || 0}
                                        onChange={e => updateItem(item.id, { fixedPrice: parseFloat(e.target.value) || 0 })}
                                    />
                                </div>
                            </div>
                        )}

                        {/* RECURRING - Duration Input */}
                        {item.pricingType === 'recurring' && (
                            <div className="flex items-center gap-4 bg-purple-50 p-3 rounded-xl border border-purple-100">
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-purple-700">Duración (Meses)</label>
                                    <Input
                                        type="number"
                                        min={1}
                                        className="bg-white h-9 w-24 border-purple-200 focus:ring-purple-200 text-purple-900 font-bold"
                                        value={item.durationMonths || 1}
                                        onChange={e => updateItem(item.id, { durationMonths: Math.max(1, parseInt(e.target.value) || 1) })}
                                    />
                                </div>
                                <div className="h-8 w-px bg-purple-200" />
                                <div className="text-xs text-purple-600">
                                    <div className="font-medium opacity-70">Mensual</div>
                                    <div className="font-bold text-sm">
                                        ${((item.clientPrice || 0) / (item.durationMonths || 1)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* PROJECT VALUE - Value Input */}
                        {item.pricingType === 'project_value' && (
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-gray-500">Valor Proyecto</label>
                                <Input
                                    type="number"
                                    className="bg-white border-blue-200 h-9 font-bold text-gray-700"
                                    value={item.projectValue || 0}
                                    onChange={e => updateItem(item.id, { projectValue: parseFloat(e.target.value) || 0 })}
                                />
                            </div>
                        )}

                        {/* TOTALS DISPLAY */}
                        <div className="pt-4 mt-4 border-t border-gray-100">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-medium text-gray-400">Costo Total</label>
                                    <div className="text-sm font-mono text-gray-600">
                                        ${item.internalCost.toLocaleString()}
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-blue-700">Precio Total</label>
                                    {/* Recurring can be adjusted as a total and is persisted as recurring_price/month. */}
                                    {item.pricingType === 'recurring' ? (
                                        <Input
                                            type="number"
                                            className="bg-blue-50/30 border-blue-200 font-bold text-blue-900 h-9"
                                            value={Math.round(item.manualPrice ? item.manualPrice : item.clientPrice)}
                                            onChange={e => updateItem(item.id, { manualPrice: parseFloat(e.target.value) || 0 })}
                                            placeholder="Auto"
                                        />
                                    ) : (
                                        <div className="text-sm font-bold font-mono text-blue-900">
                                            ${item.clientPrice.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Feedback */}
                <div className="flex justify-between items-center pt-3 border-t border-gray-50">
                    <span className="text-[10px] font-bold text-gray-300 uppercase tracking-widest">
                        Objetivo: {(state.targetMargin * 100).toFixed(0)}%
                    </span>
                    <div className="flex items-center gap-2 bg-gray-50 px-2 py-1 rounded-full border border-gray-100">
                        <span className="text-[10px] font-bold text-gray-500">Margen Real:</span>
                        <span className={`text-xs font-black ${marginColor}`}>
                            {item.marginPercentage.toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>
        </Card>
    );
}
