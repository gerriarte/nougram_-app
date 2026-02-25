
'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { Info, ArrowUpRight, Percent, Users, Receipt, Plus, Pencil, Trash2, Save, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export function QuoteFinancialSummary() {
    const { summary, state, toggleTax, taxes, setTargetMargin, teamMembers, createTax, updateTax, deleteTax, refreshTaxes } = useQuoteBuilder();
    const [showTaxManager, setShowTaxManager] = useState(false);
    const [taxError, setTaxError] = useState<string | null>(null);
    const [taxBusyId, setTaxBusyId] = useState<number | null>(null);
    const [refreshingTaxes, setRefreshingTaxes] = useState(false);
    const [newTax, setNewTax] = useState({
        name: '',
        code: '',
        percentage: '',
    });
    const [editableTaxes, setEditableTaxes] = useState<Record<number, { name: string; code: string; percentage: string }>>({});

    useEffect(() => {
        const next: Record<number, { name: string; code: string; percentage: string }> = {};
        taxes.forEach((tax) => {
            next[tax.id] = {
                name: tax.name,
                code: tax.code || '',
                percentage: String(tax.percentage ?? 0),
            };
        });
        setEditableTaxes(next);
    }, [taxes]);

    const taxCodeExists = useMemo(() => {
        const code = newTax.code.trim().toUpperCase();
        if (!code) return false;
        return taxes.some((tax) => (tax.code || '').toUpperCase() === code);
    }, [newTax.code, taxes]);

    const parsePercent = (value: string) => {
        const num = Number(value);
        if (!Number.isFinite(num)) return null;
        if (num < 0 || num > 100) return null;
        return num;
    };

    const handleCreateTax = async () => {
        setTaxError(null);
        const name = newTax.name.trim();
        const code = newTax.code.trim().toUpperCase();
        const percentage = parsePercent(newTax.percentage);

        if (!name) {
            setTaxError('El nombre del impuesto es obligatorio.');
            return;
        }
        if (!code) {
            setTaxError('El código del impuesto es obligatorio.');
            return;
        }
        if (taxCodeExists) {
            setTaxError('Ya existe un impuesto con ese código.');
            return;
        }
        if (percentage === null) {
            setTaxError('El porcentaje debe ser un número entre 0 y 100.');
            return;
        }

        try {
            setTaxBusyId(-1);
            await createTax({ name, code, percentage });
            setNewTax({ name: '', code: '', percentage: '' });
        } catch (error) {
            setTaxError(error instanceof Error ? error.message : 'No se pudo crear el impuesto.');
        } finally {
            setTaxBusyId(null);
        }
    };

    const handleUpdateTax = async (taxId: number) => {
        setTaxError(null);
        const current = editableTaxes[taxId];
        if (!current) return;

        const name = current.name.trim();
        const code = current.code.trim().toUpperCase();
        const percentage = parsePercent(current.percentage);

        if (!name || !code || percentage === null) {
            setTaxError('Para actualizar, completa nombre, código y porcentaje válido (0-100).');
            return;
        }

        try {
            setTaxBusyId(taxId);
            await updateTax(taxId, { name, code, percentage });
        } catch (error) {
            setTaxError(error instanceof Error ? error.message : 'No se pudo actualizar el impuesto.');
        } finally {
            setTaxBusyId(null);
        }
    };

    const handleDeleteTax = async (taxId: number) => {
        setTaxError(null);
        const ok = window.confirm('¿Eliminar este impuesto?');
        if (!ok) return;
        try {
            setTaxBusyId(taxId);
            await deleteTax(taxId);
        } catch (error) {
            setTaxError(error instanceof Error ? error.message : 'No se pudo eliminar el impuesto.');
        } finally {
            setTaxBusyId(null);
        }
    };

    const handleRefreshTaxes = async () => {
        setTaxError(null);
        try {
            setRefreshingTaxes(true);
            await refreshTaxes();
        } catch (error) {
            setTaxError(error instanceof Error ? error.message : 'No se pudo recargar impuestos.');
        } finally {
            setRefreshingTaxes(false);
        }
    };

    // Margin Color Logic
    let marginColor = 'text-red-500';
    let marginBg = 'bg-red-50 border-red-100';
    let marginLabel = 'Bajo';

    if (summary.netMarginPercent >= 30) {
        marginColor = 'text-green-600';
        marginBg = 'bg-green-50 border-green-100';
        marginLabel = 'Excelente';
    } else if (summary.netMarginPercent >= 20) {
        marginColor = 'text-yellow-600';
        marginBg = 'bg-yellow-50 border-yellow-100';
        marginLabel = 'Aceptable';
    }

    return (
        <Card className="h-full bg-white shadow-[0_20px_50px_rgba(0,0,0,0.05)] border-0 ring-1 ring-gray-100 sticky top-4 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-full blur-3xl -mr-16 -mt-16 opacity-50" />

            <CardContent className="p-6 space-y-5 relative">
                {/* 0. Critical Alerts */}
                {summary.totalClientPrice < summary.totalInternalCost && (
                    <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-md flex items-start gap-3">
                        <div className="text-red-500 mt-0.5"><Info size={16} /></div>
                        <div>
                            <h4 className="text-xs font-black text-red-700 uppercase tracking-wide">Pérdida Crítica</h4>
                            <p className="text-xs text-red-600 font-medium">El precio es menor que el costo operativo.</p>
                        </div>
                    </div>
                )}
                {summary.totalClientPrice >= summary.totalInternalCost && summary.netMarginPercent < 20 && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r-md flex items-start gap-3">
                        <div className="text-yellow-600 mt-0.5"><Info size={16} /></div>
                        <div>
                            <h4 className="text-xs font-black text-yellow-700 uppercase tracking-wide">Margen Bajo</h4>
                            <p className="text-xs text-yellow-600 font-medium">El margen es inferior al objetivo del 20%.</p>
                        </div>
                    </div>
                )}

                {/* 1. Header: Primary Metric */}
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Presupuesto para Cliente</p>
                        <Receipt size={14} className="text-gray-300" />
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className="text-sm font-bold text-gray-400">$</span>
                        <p className="text-5xl font-black text-gray-900 tracking-tighter">
                            {summary.totalClientPrice.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </p>
                    </div>
                </div>

                {/* 2. Interactive Controls Section */}
                <div className="space-y-6">
                    {/* Taxes */}
                    <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100 space-y-3">
                        <div className="flex items-center justify-between">
                            <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Impuestos</h4>
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] bg-white px-2 py-0.5 rounded-full border border-gray-100 font-bold text-gray-400">
                                    {state.selectedTaxIds.length} Activos
                                </span>
                                <button
                                    type="button"
                                    onClick={() => setShowTaxManager((prev) => !prev)}
                                    className="text-[10px] font-black text-blue-600 hover:text-blue-700 uppercase tracking-widest flex items-center gap-1"
                                >
                                    <Pencil size={10} />
                                    Gestionar
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2.5">
                            {taxes.map(tax => {
                                const isSelected = state.selectedTaxIds.includes(tax.id);
                                const amount = isSelected ? summary.totalClientPrice * (tax.percentage / 100) : 0;

                                return (
                                    <div
                                        key={tax.id}
                                        className={`flex items-center justify-between p-2 rounded-xl transition-all ${isSelected ? 'bg-white shadow-sm ring-1 ring-gray-100' : 'opacity-60'}`}
                                    >
                                        <label className="flex items-center gap-3 cursor-pointer text-xs font-bold text-gray-600">
                                            <input
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={() => toggleTax(tax.id)}
                                                className="w-4 h-4 rounded-lg border-gray-200 text-blue-600 focus:ring-blue-500/20"
                                            />
                                            {tax.name} <span className="text-[10px] text-gray-400">({tax.percentage}%)</span>
                                        </label>
                                        <span className={`text-xs font-black ${isSelected ? 'text-gray-900' : 'text-gray-400'}`}>
                                            ${amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>

                        {showTaxManager && (
                            <div className="mt-4 bg-white rounded-2xl border border-gray-100 p-3 space-y-3">
                                <div className="flex items-center justify-between">
                                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Editar / agregar impuestos</p>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleRefreshTaxes}
                                        disabled={refreshingTaxes}
                                        className="h-7 px-2 text-[10px] font-black text-blue-600"
                                    >
                                        <RefreshCw size={10} className={refreshingTaxes ? 'animate-spin mr-1' : 'mr-1'} />
                                        Recargar
                                    </Button>
                                </div>

                                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                                    {taxes.map((tax) => (
                                        <div key={tax.id} className="grid grid-cols-12 gap-2 items-center">
                                            <Input
                                                value={editableTaxes[tax.id]?.name || ''}
                                                onChange={(e) => setEditableTaxes((prev) => ({
                                                    ...prev,
                                                    [tax.id]: { ...(prev[tax.id] || { name: '', code: '', percentage: '0' }), name: e.target.value }
                                                }))}
                                                className="h-8 text-xs col-span-5"
                                                placeholder="Nombre"
                                            />
                                            <Input
                                                value={editableTaxes[tax.id]?.code || ''}
                                                onChange={(e) => setEditableTaxes((prev) => ({
                                                    ...prev,
                                                    [tax.id]: { ...(prev[tax.id] || { name: '', code: '', percentage: '0' }), code: e.target.value.toUpperCase() }
                                                }))}
                                                className="h-8 text-xs col-span-3 uppercase"
                                                placeholder="Código"
                                            />
                                            <Input
                                                type="number"
                                                min={0}
                                                max={100}
                                                step="0.01"
                                                value={editableTaxes[tax.id]?.percentage || ''}
                                                onChange={(e) => setEditableTaxes((prev) => ({
                                                    ...prev,
                                                    [tax.id]: { ...(prev[tax.id] || { name: '', code: '', percentage: '0' }), percentage: e.target.value }
                                                }))}
                                                className="h-8 text-xs col-span-2 text-right"
                                                placeholder="%"
                                            />
                                            <div className="col-span-2 flex items-center justify-end gap-1">
                                                <Button
                                                    type="button"
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => handleUpdateTax(tax.id)}
                                                    disabled={taxBusyId !== null}
                                                    className="h-8 w-8 p-0 text-blue-600 hover:bg-blue-50"
                                                    title="Guardar impuesto"
                                                >
                                                    <Save size={12} />
                                                </Button>
                                                <Button
                                                    type="button"
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => handleDeleteTax(tax.id)}
                                                    disabled={taxBusyId !== null}
                                                    className="h-8 w-8 p-0 text-red-600 hover:bg-red-50"
                                                    title="Eliminar impuesto"
                                                >
                                                    <Trash2 size={12} />
                                                </Button>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="pt-2 border-t border-gray-100 space-y-2">
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Nuevo impuesto</p>
                                    <div className="grid grid-cols-12 gap-2 items-center">
                                        <Input
                                            value={newTax.name}
                                            onChange={(e) => setNewTax((prev) => ({ ...prev, name: e.target.value }))}
                                            className="h-8 text-xs col-span-5"
                                            placeholder="Nombre"
                                        />
                                        <Input
                                            value={newTax.code}
                                            onChange={(e) => setNewTax((prev) => ({ ...prev, code: e.target.value.toUpperCase() }))}
                                            className="h-8 text-xs col-span-3 uppercase"
                                            placeholder="Código"
                                        />
                                        <Input
                                            type="number"
                                            min={0}
                                            max={100}
                                            step="0.01"
                                            value={newTax.percentage}
                                            onChange={(e) => setNewTax((prev) => ({ ...prev, percentage: e.target.value }))}
                                            className="h-8 text-xs col-span-2 text-right"
                                            placeholder="%"
                                        />
                                        <Button
                                            type="button"
                                            size="sm"
                                            onClick={handleCreateTax}
                                            disabled={taxBusyId !== null}
                                            className="h-8 text-xs col-span-2"
                                        >
                                            <Plus size={12} className="mr-1" />
                                            Agregar
                                        </Button>
                                    </div>
                                    {taxError && (
                                        <p className="text-[11px] font-medium text-red-600">{taxError}</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Margin Control */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Margen de Ganancia</label>
                            <div className="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full text-[10px] font-black">
                                <Percent size={10} />
                                {(state.targetMargin * 100).toFixed(0)}%
                            </div>
                        </div>
                        <div className="relative pt-1 px-1">
                            <input
                                type="range"
                                min="0"
                                max="0.80"
                                step="0.05"
                                value={state.targetMargin}
                                onChange={(e) => setTargetMargin(parseFloat(e.target.value))}
                                className="w-full h-1.5 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-blue-600 hover:accent-blue-700 transition-all"
                            />
                            <div className="flex justify-between text-[8px] font-bold text-gray-300 mt-2 uppercase tracking-tighter">
                                <span>Volumen</span>
                                <span>Equilibrio</span>
                                <span>Alta Rentabilidad</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 3. Final Total */}
                <div className="flex justify-between items-center p-5 bg-blue-900 rounded-[1.5rem] text-white shadow-xl shadow-blue-100 ring-4 ring-blue-50">
                    <div className="space-y-0.5">
                        <p className="text-[9px] font-black text-blue-300 uppercase tracking-widest">Total Factura</p>
                        <p className="text-xs text-blue-100 font-medium">Incluye impuestos</p>
                    </div>
                        <p className="text-2xl font-black tracking-tighter">
                        ${summary.totalWithTaxes.toLocaleString()}
                    </p>
                </div>

                {/* 4. Business Reality Section */}
                <div className="pt-2">
                    <div className="flex items-center gap-2 mb-6">
                        <div className="h-0.5 w-6 bg-blue-500 rounded-full" />
                        <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Realidad Financiera</h3>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between items-center px-1">
                            <span className="text-xs font-bold text-gray-500">Ingreso Neto (Excl. Impuestos)</span>
                            <span className="text-sm font-black text-gray-900">${summary.realIncome.toLocaleString()}</span>
                        </div>

                        <div className="flex justify-between items-center px-1">
                            <span className="text-xs font-bold text-gray-500">Costo Operativo (Total BCR)</span>
                            <span className="text-sm font-black text-red-500">-${summary.totalInternalCost.toLocaleString()}</span>
                        </div>

                        {/* Resulting Benefit */}
                        <div className={`relative p-4 rounded-2xl border ${marginBg} transition-all duration-500`}>
                            <div className="flex justify-between items-start mb-1">
                                <div className="space-y-1">
                                    <p className={`text-[10px] font-black uppercase tracking-widest ${marginColor}`}>Utilidad Neta ({marginLabel})</p>
                                    <p className={`text-3xl font-black ${marginColor} tracking-tighter`}>
                                        {summary.netMarginPercent.toFixed(1)}%
                                    </p>
                                </div>
                                <div className={`p-2 rounded-xl bg-white shadow-sm border border-gray-100 ${marginColor}`}>
                                    <ArrowUpRight size={20} />
                                </div>
                            </div>
                            <p className={`text-xl font-black ${marginColor} mt-2 opacity-80`}>
                                ${summary.netMarginAmount.toLocaleString()}
                            </p>
                        </div>
                    </div>
                </div>

                {/* 5. Resource Quickview */}
                {state.showResourceAllocation && state.resourceAllocations.length > 0 && (
                    <div className="pt-6 border-t border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex flex-col">
                                <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">Capacidad Asignada</span>
                                <span className="text-xs font-black text-blue-600">
                                    {state.resourceAllocations.reduce((sum, a) => sum + a.hours, 0)} Horas Totales
                                </span>
                            </div>
                            <Users size={16} className="text-gray-200" />
                        </div>

                        <div className="flex -space-x-3 overflow-hidden p-1">
                            {state.resourceAllocations.slice(0, 5).map((alloc, idx) => {
                                const member = teamMembers.find(m => m.id === alloc.teamMemberId);
                                if (!member) return null;
                                return (
                                    <div
                                        key={idx}
                                        className="inline-flex h-9 w-9 rounded-full ring-4 ring-white bg-gradient-to-br from-blue-50 to-blue-100 items-center justify-center text-[10px] font-black text-blue-700 border border-blue-50 shadow-sm transition-transform hover:scale-110 active:scale-95 cursor-pointer"
                                        title={`${member.name} (${alloc.hours}h)`}
                                    >
                                        {member.name[0]}
                                    </div>
                                );
                            })}
                            {state.resourceAllocations.length > 5 && (
                                <div className="inline-flex h-9 w-9 rounded-full ring-4 ring-white bg-gray-50 items-center justify-center text-[10px] font-black text-gray-400 border border-gray-100 shadow-sm">
                                    +{state.resourceAllocations.length - 5}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
