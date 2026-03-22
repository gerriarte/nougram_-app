
'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { useNougram } from '@/context/NougramCoreContext';
import { QuoteItem, ResourceAllocation } from '@/types/quote-builder';
import { teamCellsService, TeamCellSummary, TeamCellVersion } from '@/services/teamCellsService';
import { Trash2, Plus, Clock, Calendar } from 'lucide-react';
import { formatCurrency, formatMoneyAmount } from '@/lib/utils';

interface QuoteItemRowProps {
    item: QuoteItem;
}

export function QuoteItemRow({ item }: QuoteItemRowProps) {
    const { updateItem, removeItem, teamMembers } = useQuoteBuilder();
    const { state: coreState } = useNougram();
    const [isAddingResource, setIsAddingResource] = useState(false);
    const [selectedMemberId, setSelectedMemberId] = useState<number | ''>('');
    const [newResourceHours, setNewResourceHours] = useState<number>(10);
    const [availableCells, setAvailableCells] = useState<TeamCellSummary[]>([]);
    const [availableVersions, setAvailableVersions] = useState<TeamCellVersion[]>([]);
    const [selectedCellId, setSelectedCellId] = useState<number>(item.cellAssignment?.cellId || 0);
    const [selectedVersionId, setSelectedVersionId] = useState<number>(item.cellAssignment?.cellVersionId || 0);
    const [occupancyPercentage, setOccupancyPercentage] = useState<number>(item.cellAssignment?.occupancyPercentage || 100);
    const [cellDurationMonths, setCellDurationMonths] = useState<number>(item.cellAssignment?.durationMonths || 1);

    React.useEffect(() => {
        let mounted = true;
        const loadCells = async () => {
            if (!coreState.features.teamCellsEnabled) return;
            const cells = await teamCellsService.listCells();
            if (mounted) setAvailableCells(cells);
        };
        void loadCells();
        return () => { mounted = false; };
    }, [coreState.features.teamCellsEnabled]);

    React.useEffect(() => {
        let mounted = true;
        const loadVersions = async () => {
            if (!selectedCellId || !coreState.features.teamCellsEnabled) {
                if (mounted) setAvailableVersions([]);
                return;
            }
            const versions = await teamCellsService.listCellVersions(selectedCellId);
            if (!mounted) return;
            setAvailableVersions(versions);
            if (!selectedVersionId && versions.length > 0) {
                setSelectedVersionId(versions[0].id);
            }
        };
        void loadVersions();
        return () => { mounted = false; };
    }, [selectedCellId, selectedVersionId, coreState.features.teamCellsEnabled]);

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

    const updateResourceHours = (allocId: string, hours: number) => {
        const safeHours = Math.max(0, Number.isFinite(hours) ? hours : 0);
        const currentAllocations = item.allocations || [];
        updateItem(item.id, {
            allocations: currentAllocations.map((allocation) =>
                allocation.id === allocId ? { ...allocation, hours: safeHours } : allocation
            ),
        });
    };

    // Calculate total hours from allocations
    const totalAllocatedHours = (item.allocations || []).reduce((sum, a) => sum + a.hours, 0);
    const effectiveHours = totalAllocatedHours > 0 ? totalAllocatedHours : Number(item.estimatedHours || 0);
    const durationMultiplier = item.pricingType === 'recurring' ? Math.max(1, Number(item.durationMonths || 1)) : 1;
    const estimatedProjectHours = effectiveHours * durationMultiplier;
    const blendedRate = Number(coreState.financials.bcr || 0);
    const totalResourceCost = effectiveHours * blendedRate * durationMultiplier;
    const billingLabel = (() => {
        switch (item.pricingType) {
            case 'hourly':
                return 'Por hora';
            case 'recurring':
                return 'Fee mensual';
            case 'fixed':
            case 'project_value':
            default:
                return 'Precio fijo';
        }
    })();

    const applyCellAssignment = () => {
        const selectedVersion = availableVersions.find((version) => version.id === selectedVersionId);
        if (!selectedCellId || !selectedVersion) return;

        const activeMembers = (selectedVersion.members || []).filter((member) => member.is_active !== false);
        const totalWeight = activeMembers.reduce((acc, member) => acc + (Number(member.weight) || 0), 0);
        const occupancyRatio = Math.max(0, Number(occupancyPercentage || 0)) / 100;
        const duration = Math.max(1, Number(cellDurationMonths || 1));

        const generatedAllocations: ResourceAllocation[] = activeMembers.map((member) => {
            const weight = Number(member.weight || 0);
            const normalizedWeight = totalWeight > 0 ? (weight / totalWeight) : 0;
            const teamMember = teamMembers.find((tm) => tm.id === Number(member.team_member_id));
            const monthlyCapacity = Number(teamMember?.availableHours || 0);
            const hours = Number((monthlyCapacity * occupancyRatio * duration * normalizedWeight).toFixed(2));

            return {
                id: crypto.randomUUID(),
                teamMemberId: Number(member.team_member_id),
                hours: Math.max(0, hours),
                role: member.role_override || teamMember?.role || undefined,
            };
        }).filter((alloc) => alloc.hours > 0);

        const estimatedHours = generatedAllocations.reduce((acc, alloc) => acc + Number(alloc.hours || 0), 0);

        updateItem(item.id, {
            cellAssignment: {
                cellId: selectedCellId,
                cellVersionId: selectedVersion.id,
                occupancyPercentage: Math.max(0, Number(occupancyPercentage || 0)),
                durationMonths: duration,
            },
            allocations: generatedAllocations,
            estimatedHours,
        });
    };

    const clearCellAssignment = () => {
        updateItem(item.id, { cellAssignment: undefined });
    };

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
                {/* Header with Billing Focus */}
                <div className="flex items-center gap-3 border-b border-gray-50 pb-3">
                    <div className={`p-2 rounded-lg ${item.pricingType === 'recurring' ? 'bg-purple-50 text-purple-600' : 'bg-blue-50 text-blue-600'}`}>
                        {item.pricingType === 'recurring' ? <Calendar size={18} /> : <Clock size={18} />}
                    </div>
                    <div className="flex-1">
                        <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider block mb-1">
                            Forma de cobro
                        </span>
                        <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold tracking-wide uppercase ${
                            item.pricingType === 'recurring'
                                ? 'bg-purple-100 text-purple-700'
                                : 'bg-blue-100 text-blue-700'
                        }`}>
                            {billingLabel}
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
                                    Recursos estimados {item.pricingType === 'recurring' ? '(mensual)' : ''}
                                </label>
                                {item.pricingType === 'hourly' && (
                                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                                        Total: {effectiveHours}h
                                    </span>
                                )}
                            </div>

                            {coreState.features.teamCellsEnabled && (
                                <div className="mb-3 rounded-lg border border-purple-200 bg-purple-50/60 p-3 space-y-2">
                                    <div className="flex items-center justify-between gap-2">
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-purple-700">
                                            Asignacion por equipo
                                        </span>
                                        {item.cellAssignment && (
                                            <button
                                                type="button"
                                                onClick={clearCellAssignment}
                                                className="text-[10px] font-semibold text-purple-700 hover:text-purple-900"
                                            >
                                                Volver a manual
                                            </button>
                                        )}
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <select
                                            className="h-8 rounded-md border border-purple-200 bg-white text-xs"
                                            value={selectedCellId || ''}
                                            onChange={(e) => {
                                                setSelectedCellId(Number(e.target.value) || 0);
                                                setSelectedVersionId(0);
                                            }}
                                        >
                                            <option value="">Seleccionar equipo...</option>
                                            {availableCells.map((cell) => (
                                                <option key={cell.id} value={cell.id}>{cell.name}</option>
                                            ))}
                                        </select>
                                        <select
                                            className="h-8 rounded-md border border-purple-200 bg-white text-xs"
                                            value={selectedVersionId || ''}
                                            onChange={(e) => setSelectedVersionId(Number(e.target.value) || 0)}
                                            disabled={!selectedCellId}
                                        >
                                            <option value="">Version...</option>
                                            {availableVersions.map((version) => (
                                                <option key={version.id} value={version.id}>
                                                    V{version.version_number} ({version.status})
                                                </option>
                                            ))}
                                        </select>
                                        <Input
                                            type="number"
                                            min={1}
                                            max={100}
                                            className="h-8 text-xs bg-white border-purple-200"
                                            value={occupancyPercentage}
                                            onChange={(e) => setOccupancyPercentage(Math.max(1, Number(e.target.value) || 1))}
                                            placeholder="% ocupacion equipo"
                                        />
                                        <Input
                                            type="number"
                                            min={1}
                                            className="h-8 text-xs bg-white border-purple-200"
                                            value={cellDurationMonths}
                                            onChange={(e) => setCellDurationMonths(Math.max(1, Number(e.target.value) || 1))}
                                            placeholder="Meses"
                                        />
                                    </div>
                                    <Button
                                        type="button"
                                        size="sm"
                                        variant="ghost"
                                        className="w-full h-8 text-xs text-purple-700 hover:text-purple-900 hover:bg-purple-100"
                                        onClick={applyCellAssignment}
                                        disabled={!selectedCellId || !selectedVersionId}
                                    >
                                        Aplicar equipo
                                    </Button>
                                </div>
                            )}

                            {(!item.allocations || item.allocations.length === 0) && (
                                <div className="text-center py-4 text-xs text-gray-400 italic">
                                    No hay recursos asignados.
                                    {item.pricingType === 'hourly' && ' Agrega recursos para calcular el costo.'}
                                </div>
                            )}

                            <div className="space-y-2">
                                {item.allocations?.map(alloc => {
                                    const member = teamMembers.find(m => m.id === alloc.teamMemberId);
                                    const allocCost = Number(alloc.hours || 0) * blendedRate * durationMultiplier;
                                    return (
                                        <div key={alloc.id} className="flex items-center justify-between bg-white p-2 rounded-lg border border-gray-100 shadow-sm text-sm">
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-500">
                                                    {member?.name[0]}
                                                </div>
                                                <span className="font-medium text-gray-700">{member?.name || 'Desconocido'}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <div className="flex items-center gap-1 text-xs text-gray-500">
                                                    <Input
                                                        type="number"
                                                        min={0}
                                                        step="0.5"
                                                        className="h-7 w-20 text-xs text-right"
                                                        value={Number(alloc.hours || 0)}
                                                        onChange={(e) => updateResourceHours(alloc.id, parseFloat(e.target.value))}
                                                    />
                                                    <span>h{item.pricingType === 'recurring' ? '/mes' : ''}</span>
                                                </div>
                                                <span className="text-gray-700 bg-gray-50 px-2 py-0.5 rounded text-xs font-semibold">
                                                    {formatCurrency(allocCost, coreState.identity.primaryCurrency || 'COP')}
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
                                {item.pricingType === 'hourly' && (
                                    <div className="mb-3 flex items-center justify-between gap-2">
                                        <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                                            Esfuerzo base (si no asignas recursos)
                                        </label>
                                        <Input
                                            type="number"
                                            min={0}
                                            step="0.5"
                                            className="h-7 w-24 text-xs text-right"
                                            value={Number(item.estimatedHours || 0)}
                                            onChange={(e) => updateItem(item.id, { estimatedHours: Math.max(0, parseFloat(e.target.value) || 0) })}
                                        />
                                    </div>
                                )}
                                <div className="mb-3 flex items-center justify-between text-[11px] font-semibold text-gray-500">
                                    <span>Horas estimadas proyecto: {formatMoneyAmount(estimatedProjectHours)}h</span>
                                    <span>Costo recursos: {formatCurrency(totalResourceCost, coreState.identity.primaryCurrency || 'COP')}</span>
                                </div>
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
                                        {formatCurrency(item.internalCost, coreState.identity.primaryCurrency || 'COP')}
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
                                        {formatCurrency(((item.clientPrice || 0) / (item.durationMonths || 1)), coreState.identity.primaryCurrency || 'COP')}
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
                                    <label className="text-xs font-medium text-gray-400">Costo Recursos</label>
                                    <div className="text-sm font-mono text-gray-600">
                                        {formatCurrency(totalResourceCost, coreState.identity.primaryCurrency || 'COP')}
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-blue-700">Presupuesto Cliente (Sin Impuestos)</label>
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
                                            {formatCurrency(item.clientPrice, coreState.identity.primaryCurrency || 'COP')}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Card>
    );
}
