
'use client';

import React, { useEffect, useState } from 'react';
import { QuoteCard, Quote } from '@/components/dashboard/QuoteCard';
import { KPIWidgets } from '@/components/dashboard/KPIWidgets';
import { Search, Plus, Layout, List, Copy, Link as LinkIcon, KeyRound, SlidersHorizontal, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useQuotePipeline } from '@/hooks/useQuotePipeline';
import { motion, AnimatePresence } from 'framer-motion';
import { QuoteTable } from '@/components/dashboard/QuoteTable';
import { cn } from '@/lib/utils';
import { proposalService } from '@/services/proposalService';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { toast } from 'sonner';

export function QuotePipeline() {
    const {
        quotes: filteredQuotes,
        allQuotes,
        showInactiveQuotes,
        setShowInactiveQuotes,
        clients,
        error,
        search,
        setSearch,
        viewMode,
        setViewMode,
        handleStatusChange,
        columns,
        loading,
        filters,
        updateFilter,
        clearFilters,
        kpiSummary,
        kpiPreviousSummary,
        kpiLoading,
        kpiError,
        kpiFilter,
        updateKpiFilter,
    } = useQuotePipeline();
    const [publicAccessLoadingQuoteId, setPublicAccessLoadingQuoteId] = useState<string | null>(null);
    const [publicAccessModalOpen, setPublicAccessModalOpen] = useState(false);
    const [publicAccessData, setPublicAccessData] = useState<{
        quoteId: string;
        project: string;
        publicUrl: string;
        accessCode?: string;
        accessExpiresAt?: string;
    } | null>(null);
    const [publicAccessError, setPublicAccessError] = useState<string | null>(null);
    const [kpiFilterModalOpen, setKpiFilterModalOpen] = useState(false);
    const [kpiDraftFilter, setKpiDraftFilter] = useState(kpiFilter);
    const [isApplyingKpiFilter, setIsApplyingKpiFilter] = useState(false);
    const inactiveCount = allQuotes.filter((q) => q.isActive === false).length;

    const openKpiFilterModal = () => {
        setKpiDraftFilter(kpiFilter);
        setKpiFilterModalOpen(true);
    };

    const applyKpiFilter = () => {
        setIsApplyingKpiFilter(true);
        updateKpiFilter(kpiDraftFilter);
    };

    const kpiFilterLabel = kpiFilter.rangeMode === 'relative'
        ? `Últimos ${kpiFilter.monthsBack} mes${kpiFilter.monthsBack === 1 ? '' : 'es'}`
        : (kpiFilter.customStart && kpiFilter.customEnd
            ? `${kpiFilter.customStart} → ${kpiFilter.customEnd}`
            : 'Rango personalizado');

    useEffect(() => {
        if (isApplyingKpiFilter && !kpiLoading) {
            if (kpiError) {
                toast.error('No se pudo aplicar el filtro KPI', {
                    description: kpiError,
                });
                setIsApplyingKpiFilter(false);
                return;
            }
            toast.success('Filtro KPI aplicado', {
                description: `Rango activo: ${kpiFilterLabel}`,
            });
            setKpiFilterModalOpen(false);
            setIsApplyingKpiFilter(false);
        }
    }, [isApplyingKpiFilter, kpiLoading, kpiError, kpiFilterLabel]);

    const copyToClipboard = async (value: string) => {
        try {
            await navigator.clipboard.writeText(value);
        } catch (error) {
            console.error('No se pudo copiar al portapapeles', error);
        }
    };

    const handleOpenPublicAccess = async (quote: Quote) => {
        setPublicAccessLoadingQuoteId(quote.id);
        setPublicAccessError(null);
        try {
            const proposal = await proposalService.getLatest(quote.id);
            if (!proposal) {
                setPublicAccessData(null);
                setPublicAccessError('Esta cotización todavía no tiene una propuesta comercial guardada.');
                setPublicAccessModalOpen(true);
                return;
            }

            const share = await proposalService.shareWithClient(quote.id, proposal.id, {
                quote_id: quote.quoteId,
                send_email: false,
            });
            if (!share?.success || !share.public_url) {
                setPublicAccessData(null);
                setPublicAccessError('No se pudo recuperar el enlace público del cliente.');
                setPublicAccessModalOpen(true);
                return;
            }

            setPublicAccessData({
                quoteId: quote.id,
                project: quote.project,
                publicUrl: share.public_url,
                accessCode: share.access_code || undefined,
                accessExpiresAt: share.access_expires_at,
            });
            setPublicAccessModalOpen(true);
        } catch (error) {
            const message = error instanceof Error ? error.message : 'No fue posible abrir el acceso público.';
            setPublicAccessData(null);
            setPublicAccessError(message);
            setPublicAccessModalOpen(true);
        } finally {
            setPublicAccessLoadingQuoteId(null);
        }
    };

    if (error) {
        return (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
                <h3 className="text-base font-bold text-red-700">No se pudo cargar el pipeline</h3>
                <p className="mt-1 text-sm text-red-600">{error}</p>
            </div>
        );
    }

    return (
        <div className="space-y-12 pb-20">
            {/* 1. KPIs */}
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="min-w-0">
                        <h2 className="text-[15px] font-semibold text-gray-900">Indicadores (KPI)</h2>
                        <p className="text-[12.5px] text-gray-500 mt-0.5 max-w-xl">
                            Última cotización por proyecto, sin borradores. Filtro por fecha de actualización.
                        </p>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 w-full md:w-auto">
                        <span className="text-[11.5px] font-semibold text-gray-500 bg-surface-2 border border-gray-200 px-3 py-1.5 rounded-full w-fit">
                            {kpiFilterLabel}
                        </span>
                        <Button
                            type="button"
                            variant="secondary"
                            className="h-9 rounded-lg px-3 text-[12.5px] w-full sm:w-auto justify-center"
                            onClick={openKpiFilterModal}
                        >
                            <SlidersHorizontal size={13} className="mr-1.5" />
                            Ajustar rango
                        </Button>
                    </div>
                </div>

                <KPIWidgets kpiSummary={kpiSummary} kpiPreviousSummary={kpiPreviousSummary} kpiLoading={kpiLoading} kpiError={kpiError} />
            </div>

            {/* 2. Pipeline Controls */}
            {loading ? (
                <div className="flex h-[320px] items-center justify-center rounded-2xl border border-gray-200 bg-surface-2">
                    <div className="flex flex-col items-center gap-3">
                        <div className="w-8 h-8 border-[3px] border-gray-200 border-t-gray-500 rounded-full animate-spin" />
                        <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest">Cargando pipeline…</p>
                    </div>
                </div>
            ) : null}

            {!loading ? (
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div>
                        <h2 className="text-[17px] font-semibold text-gray-900 tracking-tight">Ventas & Pipeline</h2>
                        <p className="text-[12.5px] text-gray-500 mt-0.5">Monitorea el flujo de tus propuestas comerciales.</p>
                    </div>

                    <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-3 w-full md:w-auto">
                        {/* Search */}
                        <div className="relative group flex-1 min-w-0 w-full md:w-72">
                            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-gray-600 transition-colors" strokeWidth={1.5} />
                            <input
                                type="text"
                                placeholder="Buscar proyecto o cliente..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full h-9 border border-gray-200 rounded-lg bg-white pl-9 pr-3 text-[13px] text-gray-800 placeholder:text-gray-400 focus:border-gray-400 focus:outline-none transition-colors"
                            />
                        </div>

                        {/* Client filter */}
                        <select
                            value={filters.clientId === '' ? '' : String(filters.clientId)}
                            onChange={(e) => updateFilter('clientId', e.target.value === '' ? '' : Number(e.target.value))}
                            className="h-9 px-3 rounded-lg border border-gray-200 bg-white text-[13px] text-gray-800 focus:border-gray-400 focus:outline-none min-w-0 w-full sm:min-w-[160px] sm:w-auto"
                        >
                            <option value="">Todos los clientes</option>
                            {clients.map((c) => (
                                <option key={c.id} value={String(c.id)}>
                                    {c.display_name}
                                </option>
                            ))}
                        </select>

                        {/* View Switcher */}
                        <div className="bg-surface-2 border border-gray-200 p-0.5 rounded-lg flex gap-0.5 h-9 w-full sm:w-auto justify-center sm:justify-start">
                            <button
                                onClick={() => setViewMode('board')}
                                className={cn(
                                    "px-3 rounded-md transition-all flex items-center justify-center",
                                    viewMode === 'board' ? "bg-white text-gray-900 shadow-sm" : "text-gray-400 hover:text-gray-700"
                                )}
                            >
                                <Layout size={15} strokeWidth={2} />
                            </button>
                            <button
                                onClick={() => setViewMode('list')}
                                className={cn(
                                    "px-3 rounded-md transition-all flex items-center justify-center",
                                    viewMode === 'list' ? "bg-white text-gray-900 shadow-sm" : "text-gray-400 hover:text-gray-700"
                                )}
                            >
                                <List size={15} strokeWidth={2} />
                            </button>
                        </div>
                        <Button
                            type="button"
                            variant={showInactiveQuotes ? 'primary' : 'secondary'}
                            className="h-9 rounded-lg px-3 text-[12.5px] w-full sm:w-auto justify-center"
                            onClick={() => setShowInactiveQuotes((prev) => !prev)}
                        >
                            {showInactiveQuotes ? 'Ocultar inactivas' : 'Ver inactivas (PM)'}
                            {inactiveCount > 0 ? ` (${inactiveCount})` : ''}
                        </Button>
                    </div>
                </div>

                {/* Pipeline Board */}
                <AnimatePresence mode="wait">
                    {viewMode === 'board' ? (
                        <motion.div
                            key="board"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="flex gap-6 overflow-x-auto pb-8 scrollbar-hide snap-x"
                        >
                            {columns.map(col => {
                                const quotesInCol = filteredQuotes.filter(q => q.status === col.id);
                                return (
                                    <div
                                        key={col.id}
                                        className="min-w-[min(90vw,320px)] sm:min-w-[340px] flex flex-col gap-4 snap-start"
                                        onDragOver={(e) => e.preventDefault()}
                                        onDrop={(e) => {
                                            e.preventDefault();
                                            const quoteId = e.dataTransfer.getData('quoteId');
                                            if (quoteId) handleStatusChange(quoteId, col.id as Quote['status']);
                                        }}
                                    >
                                        <div className="flex items-center justify-between px-2">
                                            <div className="flex items-center gap-2.5">
                                                <div className={cn("w-2 h-2 rounded-full", col.color.replace('bg-', 'bg-').replace('-50', '-500').replace('-100', '-500'))} />
                                                <h3 className="text-[11px] font-black text-system-gray uppercase tracking-[0.15em]">{col.title}</h3>
                                            </div>
                                            <span className="text-[10px] font-black text-gray-400 bg-gray-100 px-2 py-0.5 rounded-lg border border-gray-200/50">
                                                {quotesInCol.length}
                                            </span>
                                        </div>

                                        <div className="flex-1 space-y-4 min-h-[300px]">
                                            {quotesInCol.map(quote => (
                                                <QuoteCard
                                                    key={quote.id}
                                                    quote={quote}
                                                    draggable
                                                    onDragStart={(e) => e.dataTransfer.setData('quoteId', quote.id)}
                                                    onStatusChange={handleStatusChange}
                                                    onOpenPublicAccess={handleOpenPublicAccess}
                                                    isPublicAccessLoading={publicAccessLoadingQuoteId === quote.id}
                                                    className="cursor-grab active:cursor-grabbing"
                                                />
                                            ))}
                                            {quotesInCol.length === 0 && (
                                                <div className="h-40 bg-gray-200/20 border-2 border-dashed border-gray-200/50 rounded-3xl flex flex-col items-center justify-center gap-2 text-gray-400 italic text-sm">
                                                    <Plus size={20} strokeWidth={1} />
                                                    <span className="font-medium text-[12px]">Sin cotizaciones</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="list"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                        >
                            <QuoteTable
                                quotes={filteredQuotes}
                                onStatusChange={handleStatusChange}
                                onOpenPublicAccess={handleOpenPublicAccess}
                                publicAccessLoadingQuoteId={publicAccessLoadingQuoteId}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
            ) : null}

            <Dialog open={publicAccessModalOpen} onOpenChange={setPublicAccessModalOpen}>
                <DialogContent className="sm:max-w-[620px]">
                    <DialogHeader>
                        <DialogTitle>Acceso público del cliente</DialogTitle>
                        <DialogDescription>
                            Usa este acceso rápido para compartir el portal del cliente.
                        </DialogDescription>
                    </DialogHeader>

                    {publicAccessError ? (
                        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                            {publicAccessError}
                        </div>
                    ) : publicAccessData ? (
                        <div className="space-y-4">
                            <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
                                Proyecto: <span className="font-semibold text-gray-800">{publicAccessData.project}</span>
                            </div>

                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-gray-700 flex items-center gap-1">
                                    <LinkIcon size={12} /> Enlace público
                                </label>
                                <div className="flex gap-2">
                                    <Input value={publicAccessData.publicUrl} readOnly />
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        onClick={() => void copyToClipboard(publicAccessData.publicUrl)}
                                    >
                                        <Copy size={14} className="mr-1" /> Copiar
                                    </Button>
                                </div>
                            </div>

                            {publicAccessData.accessCode && (
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-gray-700 flex items-center gap-1">
                                        <KeyRound size={12} /> Clave temporal
                                    </label>
                                    <div className="flex gap-2">
                                        <Input value={publicAccessData.accessCode} readOnly />
                                        <Button
                                            type="button"
                                            variant="secondary"
                                            onClick={() => void copyToClipboard(publicAccessData.accessCode!)}
                                        >
                                            <Copy size={14} className="mr-1" /> Copiar
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {publicAccessData.accessExpiresAt && (
                                <p className="text-xs text-gray-500">
                                    Vigencia: {new Date(publicAccessData.accessExpiresAt).toLocaleString()}
                                </p>
                            )}
                        </div>
                    ) : null}

                    <DialogFooter>
                        <Button variant="secondary" onClick={() => setPublicAccessModalOpen(false)}>
                            Cerrar
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <Dialog open={kpiFilterModalOpen} onOpenChange={setKpiFilterModalOpen}>
                <DialogContent className="sm:max-w-[560px]">
                    <DialogHeader>
                        <DialogTitle>Filtro temporal de KPI</DialogTitle>
                        <DialogDescription>
                            Unifica rango parametrizado y rango personalizado para actualizar las métricas.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-5">
                        <div className="inline-flex rounded-xl bg-gray-100/80 p-1">
                            <button
                                type="button"
                                onClick={() => setKpiDraftFilter((prev) => ({ ...prev, rangeMode: 'relative' }))}
                                disabled={isApplyingKpiFilter}
                                className={cn(
                                    'px-4 py-2 text-xs font-bold rounded-lg transition-all',
                                    kpiDraftFilter.rangeMode === 'relative'
                                        ? 'bg-white text-gray-900 shadow-sm'
                                        : 'text-gray-500 hover:text-gray-800'
                                )}
                            >
                                Últimos N meses
                            </button>
                            <button
                                type="button"
                                onClick={() => setKpiDraftFilter((prev) => ({ ...prev, rangeMode: 'custom' }))}
                                disabled={isApplyingKpiFilter}
                                className={cn(
                                    'px-4 py-2 text-xs font-bold rounded-lg transition-all',
                                    kpiDraftFilter.rangeMode === 'custom'
                                        ? 'bg-white text-gray-900 shadow-sm'
                                        : 'text-gray-500 hover:text-gray-800'
                                )}
                            >
                                Rango personalizado
                            </button>
                        </div>

                        {kpiDraftFilter.rangeMode === 'relative' ? (
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Ventana</label>
                                <select
                                    value={kpiDraftFilter.monthsBack}
                                    onChange={(e) => setKpiDraftFilter((prev) => ({ ...prev, monthsBack: Number(e.target.value) }))}
                                    disabled={isApplyingKpiFilter}
                                    className="h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm font-semibold text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-400/30"
                                >
                                    <option value={1}>Último mes</option>
                                    <option value={3}>Últimos 3 meses</option>
                                    <option value={6}>Últimos 6 meses</option>
                                    <option value={12}>Últimos 12 meses</option>
                                </select>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div className="flex flex-col gap-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Desde</label>
                                    <input
                                        type="date"
                                        value={kpiDraftFilter.customStart}
                                        onChange={(e) => setKpiDraftFilter((prev) => ({ ...prev, customStart: e.target.value }))}
                                        disabled={isApplyingKpiFilter}
                                        className="h-11 rounded-xl border border-gray-200 bg-white px-3 text-sm font-semibold text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-400/30"
                                    />
                                </div>
                                <div className="flex flex-col gap-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Hasta</label>
                                    <input
                                        type="date"
                                        value={kpiDraftFilter.customEnd}
                                        onChange={(e) => setKpiDraftFilter((prev) => ({ ...prev, customEnd: e.target.value }))}
                                        disabled={isApplyingKpiFilter}
                                        className="h-11 rounded-xl border border-gray-200 bg-white px-3 text-sm font-semibold text-gray-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-400/30"
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    <DialogFooter>
                        <Button
                            variant="secondary"
                            onClick={() => setKpiFilterModalOpen(false)}
                            disabled={isApplyingKpiFilter}
                        >
                            Cancelar
                        </Button>
                        <Button
                            onClick={applyKpiFilter}
                            disabled={
                                isApplyingKpiFilter ||
                                (kpiDraftFilter.rangeMode === 'custom' &&
                                    (!kpiDraftFilter.customStart || !kpiDraftFilter.customEnd))
                            }
                        >
                            {isApplyingKpiFilter ? (
                                <>
                                    <Loader2 size={14} className="mr-2 animate-spin" />
                                    Aplicando...
                                </>
                            ) : (
                                'Aplicar'
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
