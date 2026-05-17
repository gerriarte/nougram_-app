'use client';

import React, { useEffect, useState } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { NumInput } from '@/components/ui/NumInput';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { useNougram } from '@/context/NougramCoreContext';
import { QuoteItem, ResourceAllocation } from '@/types/quote-builder';
import { Trash2, Plus, Clock, Briefcase, Repeat, TrendingUp, ChevronDown, ChevronUp, AlertCircle, Users } from 'lucide-react';
import { formatCurrency, formatMoneyAmount } from '@/lib/utils';
import { cn } from '@/lib/utils';

// ── Type badge config ──────────────────────────────────────────────
const TYPE_CONFIG = {
    hourly:        { label: 'Por horas',   Icon: Clock,       tint: 'bg-primary-soft text-primary' },
    fixed:         { label: 'Cobro fijo',  Icon: Briefcase,   tint: 'bg-blue-50 text-blue-700' },
    recurring:     { label: 'Mensual',     Icon: Repeat,      tint: 'bg-success-soft text-green-700' },
    project_value: { label: 'Valor proy.', Icon: TrendingUp,  tint: 'bg-purple-50 text-purple-700' },
} as const;

function TypeBadge({ type }: { type: keyof typeof TYPE_CONFIG }) {
    const cfg = TYPE_CONFIG[type] ?? TYPE_CONFIG.fixed;
    const { Icon, label, tint } = cfg;
    return (
        <span className={cn('inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-semibold', tint)}>
            <Icon size={11} strokeWidth={2.2} />
            {label}
        </span>
    );
}

function LabeledField({ label, align = 'left', children }: { label: string; align?: 'left' | 'right'; children: React.ReactNode }) {
    return (
        <div className="min-w-0">
            <div className={cn('mb-1 text-[9.5px] font-semibold uppercase tracking-[0.5px] text-gray-400', align === 'right' && 'text-right')}>
                {label}
            </div>
            {children}
        </div>
    );
}

// ── Margin color ───────────────────────────────────────────────────
function marginToneClass(marginPct: number, hasValue: boolean) {
    if (!hasValue) return { text: 'text-gray-400', pct: 'text-gray-400' };
    if (marginPct < 20) return { text: 'text-critical', pct: 'text-red-300' };
    if (marginPct < 30) return { text: 'text-warning', pct: 'text-amber-300' };
    return { text: 'text-success', pct: 'text-green-300' };
}

// Read-only field that signals "cost is unknown — assign hours or resources"
function UnknownCostField() {
    return (
        <div className="flex h-9 items-center gap-1.5 rounded-lg border border-amber-200/80 bg-amber-50/60 px-3 text-[11px] font-medium text-amber-700">
            <AlertCircle size={11} strokeWidth={2.2} className="shrink-0" />
            Sin horas
        </div>
    );
}

// ── Props ──────────────────────────────────────────────────────────
interface QuoteItemRowProps {
    item: QuoteItem;
    index?: number;
}

export function QuoteItemRow({ item, index }: QuoteItemRowProps) {
    const { updateItem, removeItem, teamMembers } = useQuoteBuilder();
    const { state: coreState } = useNougram();
    const currency = coreState.identity.primaryCurrency || 'COP';

    const pricingNeedsResource =
        item.pricingType === 'hourly' || item.pricingType === 'recurring';
    const [resourcesOpen, setResourcesOpen] = useState(
        () => pricingNeedsResource && (item.allocations?.length ?? 0) === 0
    );
    const [isAddingResource, setIsAddingResource] = useState(false);
    const [selectedMemberId, setSelectedMemberId] = useState<number | ''>('');
    const [newResourceHours, setNewResourceHours] = useState<number>(10);

    // ── Calculations ───────────────────────────────────────────────
    const blendedRate = Number(coreState.financials.bcr || 0);
    const durationMultiplier = item.pricingType === 'recurring' ? Math.max(1, Number(item.durationMonths || 1)) : 1;
    const totalAllocatedHours = (item.allocations || []).reduce((sum, a) => sum + a.hours, 0);
    const effectiveHours = totalAllocatedHours > 0 ? totalAllocatedHours : Number(item.estimatedHours || 0);
    const estimatedProjectHours = effectiveHours * durationMultiplier;
    const totalResourceCost = effectiveHours * blendedRate * durationMultiplier;

    const subtotal = item.clientPrice || 0;
    const cost = item.internalCost || 0;
    const marginPct = subtotal > 0 ? ((subtotal - cost) / subtotal) * 100 : 0;
    // costUnknown: item has a client price but zero internal cost (no hours/allocations assigned).
    // The 100% margin it would display is fictitious, so we suppress the percentage.
    const costUnknown = subtotal > 0 && cost === 0;
    const toneClass = marginToneClass(marginPct, subtotal > 0 && !costUnknown);

    // ── Resource handlers ──────────────────────────────────────────
    const handleAddResource = () => {
        if (!selectedMemberId) return;
        const member = teamMembers.find(m => m.id === Number(selectedMemberId));
        if (!member) return;
        const newAlloc: ResourceAllocation = {
            id: crypto.randomUUID(),
            teamMemberId: member.id,
            hours: newResourceHours,
            role: member.role,
        };
        updateItem(item.id, { allocations: [...(item.allocations || []), newAlloc] });
        setIsAddingResource(false);
        setSelectedMemberId('');
        setNewResourceHours(10);
    };

    const removeResource = (allocId: string) =>
        updateItem(item.id, { allocations: (item.allocations || []).filter(a => a.id !== allocId) });

    const updateResourceHours = (allocId: string, hours: number) => {
        const safeHours = Math.max(0, Number.isFinite(hours) ? hours : 0);
        updateItem(item.id, {
            allocations: (item.allocations || []).map(a => a.id === allocId ? { ...a, hours: safeHours } : a),
        });
    };

    const allocCount = (item.allocations || []).length;
    const resourceAssigned = allocCount > 0;
    const resourceMissing = pricingNeedsResource && !resourceAssigned;

    useEffect(() => {
        if (resourceMissing) setResourcesOpen(true);
    }, [resourceMissing]);

    return (
        <div
            className={cn(
                'group rounded-xl border overflow-hidden transition-shadow',
                resourceAssigned &&
                    'border-emerald-200/90 bg-gradient-to-br from-emerald-50/[0.85] via-white to-teal-50/50 shadow-sm shadow-emerald-900/[0.04] hover:shadow-md hover:border-emerald-300/90',
                resourceMissing &&
                    'border-amber-300/90 bg-gradient-to-br from-amber-50/40 via-white to-orange-50/25 ring-1 ring-amber-200/50 shadow-sm hover:shadow-md hover:border-amber-400/90',
                !resourceAssigned &&
                    !resourceMissing &&
                    'border-gray-200 bg-white shadow-sm hover:shadow-md hover:border-gray-300'
            )}
        >

            {/* ── Header strip ── */}
            <div className="flex items-center gap-2.5 px-4 py-3">
                {index !== undefined && (
                    <div className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-md bg-surface-2 font-mono text-[10px] font-semibold text-gray-400">
                        {String(index + 1).padStart(2, '0')}
                    </div>
                )}
                <TypeBadge type={item.pricingType} />
                <input
                    value={item.serviceName || ''}
                    onChange={e => updateItem(item.id, { serviceName: e.target.value })}
                    placeholder="Descripción del servicio…"
                    className="min-w-0 flex-1 bg-transparent text-[13.5px] font-semibold text-gray-800 placeholder:text-gray-300 outline-none"
                />
                <button
                    type="button"
                    onClick={() => removeItem(item.id)}
                    className="ml-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-gray-300 opacity-0 transition-all group-hover:opacity-100 hover:bg-red-50 hover:text-red-500"
                >
                    <Trash2 size={13} />
                </button>
            </div>

            {/* ── Fields zone ── */}
            <div className="border-t border-dashed border-gray-100 px-4 pb-4 pt-3">

                {/* HOURLY */}
                {item.pricingType === 'hourly' && (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <LabeledField label="Horas base">
                            <NumInput
                                value={item.estimatedHours ?? ''}
                                onChange={v => updateItem(item.id, { estimatedHours: v === '' ? 0 : v })}
                                suffix="h"
                                placeholder="0"
                            />
                        </LabeledField>
                        <LabeledField label="Costo (BCR)">
                            <div className="flex h-9 items-center rounded-lg border border-gray-100 bg-surface-2 px-3 text-[12px] tabular-nums text-gray-500">
                                {formatCurrency(totalResourceCost, currency)}
                            </div>
                        </LabeledField>
                        <LabeledField label="Precio cliente">
                            <NumInput
                                value={item.manualPrice ?? item.clientPrice ?? ''}
                                onChange={v => updateItem(item.id, { manualPrice: v === '' ? undefined : v })}
                                placeholder="Auto"
                            />
                        </LabeledField>
                        <LabeledField label="Subtotal" align="right">
                            <div className={cn(
                                'flex h-9 items-baseline justify-end gap-1.5 rounded-lg px-3',
                                subtotal > 0 ? 'bg-gray-900' : 'bg-surface-2'
                            )}>
                                <span className={cn('text-[13.5px] font-semibold tabular-nums', subtotal > 0 ? 'text-white' : 'text-gray-400')}>
                                    {formatCurrency(subtotal, currency)}
                                </span>
                                {subtotal > 0 && (
                                    <span className={cn('text-[9.5px] font-semibold', toneClass.pct)}>
                                        {costUnknown ? '—' : `${marginPct.toFixed(0)}%`}
                                    </span>
                                )}
                            </div>
                        </LabeledField>
                    </div>
                )}

                {/* FIXED */}
                {item.pricingType === 'fixed' && (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <LabeledField label="Costo base">
                            {costUnknown ? <UnknownCostField /> : (
                                <div className="flex h-9 items-center rounded-lg border border-gray-100 bg-surface-2 px-3 text-[12px] tabular-nums text-gray-500">
                                    {formatCurrency(cost, currency)}
                                </div>
                            )}
                        </LabeledField>
                        <LabeledField label="Cantidad">
                            <NumInput
                                value={item.quantity}
                                onChange={v => updateItem(item.id, { quantity: v === '' ? 1 : Math.max(1, v) })}
                                placeholder="1"
                            />
                        </LabeledField>
                        <LabeledField label="Precio fijo">
                            <NumInput
                                value={item.fixedPrice ?? ''}
                                onChange={v => updateItem(item.id, { fixedPrice: v === '' ? 0 : v })}
                                placeholder="0"
                            />
                        </LabeledField>
                        <LabeledField label="Subtotal" align="right">
                            <div className={cn(
                                'flex h-9 items-baseline justify-end gap-1.5 rounded-lg px-3',
                                subtotal > 0 ? 'bg-gray-900' : 'bg-surface-2'
                            )}>
                                <span className={cn('text-[13.5px] font-semibold tabular-nums', subtotal > 0 ? 'text-white' : 'text-gray-400')}>
                                    {formatCurrency(subtotal, currency)}
                                </span>
                                {subtotal > 0 && (
                                    <span className={cn('text-[9.5px] font-semibold', toneClass.pct)}>
                                        {costUnknown ? '—' : `${marginPct.toFixed(0)}%`}
                                    </span>
                                )}
                            </div>
                        </LabeledField>
                    </div>
                )}

                {/* RECURRING */}
                {item.pricingType === 'recurring' && (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                        <LabeledField label="H/mes">
                            <NumInput
                                value={item.estimatedHours ?? ''}
                                onChange={v => updateItem(item.id, { estimatedHours: v === '' ? 0 : v })}
                                suffix="h"
                                placeholder="0"
                            />
                        </LabeledField>
                        <LabeledField label="Meses">
                            <NumInput
                                value={item.durationMonths ?? 1}
                                onChange={v => updateItem(item.id, { durationMonths: v === '' ? 1 : Math.max(1, v) })}
                                suffix="m"
                                placeholder="1"
                            />
                        </LabeledField>
                        <LabeledField label="Costo total">
                            {costUnknown ? <UnknownCostField /> : (
                                <div className="flex h-9 items-center rounded-lg border border-gray-100 bg-surface-2 px-3 text-[12px] tabular-nums text-gray-500">
                                    {formatCurrency(totalResourceCost, currency)}
                                </div>
                            )}
                        </LabeledField>
                        <LabeledField label="$/mes (cliente)">
                            <NumInput
                                value={item.manualPrice
                                    ? Math.round(item.manualPrice / durationMultiplier)
                                    : Math.round((item.clientPrice || 0) / durationMultiplier)}
                                onChange={v => updateItem(item.id, { manualPrice: v === '' ? undefined : (v * durationMultiplier) })}
                                placeholder="Auto"
                            />
                        </LabeledField>
                        <LabeledField label="Subtotal" align="right">
                            <div className={cn(
                                'flex h-9 items-baseline justify-end gap-1.5 rounded-lg px-3',
                                subtotal > 0 ? 'bg-gray-900' : 'bg-surface-2'
                            )}>
                                <span className={cn('text-[13.5px] font-semibold tabular-nums', subtotal > 0 ? 'text-white' : 'text-gray-400')}>
                                    {formatCurrency(subtotal, currency)}
                                </span>
                                {subtotal > 0 && (
                                    <span className={cn('text-[9.5px] font-semibold', toneClass.pct)}>
                                        {costUnknown ? '—' : `${marginPct.toFixed(0)}%`}
                                    </span>
                                )}
                            </div>
                        </LabeledField>
                    </div>
                )}

                {/* PROJECT VALUE */}
                {item.pricingType === 'project_value' && (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                        <LabeledField label="Costo base">
                            {costUnknown ? <UnknownCostField /> : (
                                <div className="flex h-9 items-center rounded-lg border border-gray-100 bg-surface-2 px-3 text-[12px] tabular-nums text-gray-500">
                                    {formatCurrency(cost, currency)}
                                </div>
                            )}
                        </LabeledField>
                        <LabeledField label="Valor proyecto (venta)">
                            <NumInput
                                value={item.projectValue ?? ''}
                                onChange={v => updateItem(item.id, { projectValue: v === '' ? 0 : v })}
                                placeholder="0"
                            />
                        </LabeledField>
                        <LabeledField label="Subtotal" align="right">
                            <div className={cn(
                                'flex h-9 items-baseline justify-end gap-1.5 rounded-lg px-3',
                                subtotal > 0 ? 'bg-gray-900' : 'bg-surface-2'
                            )}>
                                <span className={cn('text-[13.5px] font-semibold tabular-nums', subtotal > 0 ? 'text-white' : 'text-gray-400')}>
                                    {formatCurrency(subtotal, currency)}
                                </span>
                                {subtotal > 0 && (
                                    <span className={cn('text-[9.5px] font-semibold', toneClass.pct)}>
                                        {costUnknown ? '—' : `${marginPct.toFixed(0)}%`}
                                    </span>
                                )}
                            </div>
                        </LabeledField>
                    </div>
                )}

                {/* ── Resource allocation (collapsible) ── */}
                <div className="mt-3">
                    {resourceMissing && (
                        <div className="mb-2 flex flex-col gap-2 rounded-xl border border-amber-200/90 bg-amber-50/70 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex min-w-0 items-start gap-2 text-[11px] text-amber-950">
                                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" strokeWidth={2.2} />
                                <p>
                                    <span className="font-semibold">Asigna un recurso</span>
                                    <span className="text-amber-800/90"> para vincular horas al equipo y calcular costo y margen.</span>
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setResourcesOpen(true)}
                                className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-amber-600 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wide text-white shadow-sm transition-colors hover:bg-amber-700"
                            >
                                <Users size={12} strokeWidth={2.2} />
                                Asignar recurso
                            </button>
                        </div>
                    )}

                    <button
                        type="button"
                        onClick={() => setResourcesOpen(v => !v)}
                        className={cn(
                            'flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[11px] font-semibold transition-colors',
                            resourceMissing &&
                                'border border-amber-200/80 bg-amber-50/50 text-amber-900 hover:bg-amber-50',
                            resourceAssigned &&
                                'text-emerald-800 hover:bg-emerald-50/60',
                            !resourceMissing && !resourceAssigned && 'text-gray-400 hover:bg-surface-2 hover:text-gray-600'
                        )}
                    >
                        {resourcesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        {resourceMissing ? (
                            <span className="font-bold tracking-tight">Asignar recurso</span>
                        ) : (
                            <span>Recursos asignados</span>
                        )}
                        {allocCount > 0 && (
                            <span
                                className={cn(
                                    'ml-1 rounded-full px-1.5 py-px text-[10px] font-semibold',
                                    resourceAssigned ? 'bg-emerald-100 text-emerald-800' : 'bg-primary-soft text-primary'
                                )}
                            >
                                {allocCount}
                            </span>
                        )}
                        <span
                            className={cn(
                                'ml-auto text-[10px] font-normal tabular-nums',
                                resourceAssigned ? 'text-emerald-700/90' : 'text-gray-400'
                            )}
                        >
                            {formatMoneyAmount(estimatedProjectHours)}h · {formatCurrency(totalResourceCost, currency)}
                        </span>
                    </button>

                    {resourcesOpen && (
                        <div
                            className={cn(
                                'mt-2 rounded-xl border p-3 space-y-2 animate-in fade-in slide-in-from-top-1',
                                resourceAssigned
                                    ? 'border-emerald-100/90 bg-gradient-to-b from-emerald-50/50 to-white'
                                    : 'border-gray-100 bg-surface-2'
                            )}
                        >
                            {allocCount === 0 && (
                                <p className="text-center text-[11px] text-gray-400 py-2">Sin recursos asignados.</p>
                            )}
                            {(item.allocations || []).map(alloc => {
                                const member = teamMembers.find(m => m.id === alloc.teamMemberId);
                                const allocCost = Number(alloc.hours || 0) * blendedRate * durationMultiplier;
                                return (
                                    <div key={alloc.id} className="flex items-center justify-between rounded-lg border border-gray-100 bg-white px-3 py-2 shadow-sm text-[12px]">
                                        <div className="flex items-center gap-2">
                                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-soft text-[10px] font-bold text-primary">
                                                {member?.name?.[0] ?? '?'}
                                            </div>
                                            <span className="font-medium text-gray-700">{member?.name || 'Desconocido'}</span>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="flex items-center gap-1 text-gray-500">
                                                <Input
                                                    type="number"
                                                    min={0}
                                                    step="0.5"
                                                    className="h-7 w-18 text-xs text-right"
                                                    value={Number(alloc.hours || 0)}
                                                    onChange={e => updateResourceHours(alloc.id, parseFloat(e.target.value))}
                                                />
                                                <span className="text-[11px]">h{item.pricingType === 'recurring' ? '/mes' : ''}</span>
                                            </div>
                                            <span className="text-[11px] font-semibold text-gray-700">
                                                {formatCurrency(allocCost, currency)}
                                            </span>
                                            <button onClick={() => removeResource(alloc.id)} className="text-gray-300 hover:text-red-500 transition-colors">
                                                <Trash2 size={11} />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}

                            {/* Add resource */}
                            <div className={cn('pt-1 border-t', resourceAssigned ? 'border-emerald-100' : 'border-gray-100')}>
                                {!isAddingResource ? (
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setIsAddingResource(true)}
                                        className={cn(
                                            'w-full text-xs h-8',
                                            resourceMissing
                                                ? 'font-bold text-amber-900 hover:bg-amber-100/80 border border-dashed border-amber-300/90 rounded-lg'
                                                : 'text-primary hover:bg-primary-soft'
                                        )}
                                    >
                                        <Plus size={11} className="mr-1.5" />
                                        {resourceMissing ? 'Asignar recurso' : 'Agregar recurso'}
                                    </Button>
                                ) : (
                                    <div className="flex items-end gap-2 animate-in fade-in slide-in-from-top-1">
                                        <div className="flex-1 space-y-1">
                                            <label className="text-[9.5px] font-semibold uppercase tracking-wide text-gray-400">Miembro</label>
                                            <select
                                                className="w-full h-8 text-xs rounded-md border border-gray-200 bg-white px-2"
                                                value={selectedMemberId}
                                                onChange={e => setSelectedMemberId(Number(e.target.value))}
                                            >
                                                <option value="">Seleccionar…</option>
                                                {teamMembers.map(m => (
                                                    <option key={m.id} value={m.id}>{m.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="w-20 space-y-1">
                                            <label className="text-[9.5px] font-semibold uppercase tracking-wide text-gray-400">Horas</label>
                                            <Input
                                                type="number"
                                                className="h-8 text-xs"
                                                value={newResourceHours}
                                                onChange={e => setNewResourceHours(Number(e.target.value))}
                                            />
                                        </div>
                                        <div className="flex gap-1">
                                            <Button size="sm" onClick={handleAddResource} disabled={!selectedMemberId} className="h-8 px-3">
                                                + Agregar
                                            </Button>
                                            <Button size="sm" variant="ghost" onClick={() => setIsAddingResource(false)} className="h-8 px-2">
                                                ✕
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
