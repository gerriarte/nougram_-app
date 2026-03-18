
'use client';

import React, { useState } from 'react';
import { QuoteCard, Quote } from '@/components/dashboard/QuoteCard';
import { KPIWidgets } from '@/components/dashboard/KPIWidgets';
import { Search, Plus, Layout, List, Copy, Link as LinkIcon, KeyRound } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { useQuotePipeline } from '@/hooks/useQuotePipeline';
import { motion, AnimatePresence } from 'framer-motion';
import { QuoteTable } from '@/components/dashboard/QuoteTable';
import { cn } from '@/lib/utils';
import { BCRSummaryCard } from '@/components/admin/BCRSummaryCard';
import { proposalService } from '@/services/proposalService';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';

export function QuotePipeline() {
    const {
        quotes: filteredQuotes,
        allQuotes,
        clients,
        error,
        search,
        setSearch,
        viewMode,
        setViewMode,
        handleStatusChange,
        columns,
        loading,
        metrics,
        filters,
        updateFilter,
        clearFilters
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

    if (loading) {
        return (
            <div className="flex h-[400px] items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
                    <p className="text-sm font-bold text-system-gray uppercase tracking-widest">Sincronizando Pipeline...</p>
                </div>
            </div>
        );
    }

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
            {/* 1. KPIs Section */}
            {/* 1. KPIs Section */}
            <div className="space-y-6">
                <KPIWidgets metrics={metrics} />
            </div>

            {/* 2. Pipeline Controls */}
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Ventas & Pipeline</h2>
                        <p className="text-sm text-system-gray font-medium mt-1">Monitorea el flujo de tus propuestas comerciales.</p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
                        {/* Search */}
                        <div className="relative group flex-1 min-w-[200px] md:w-80">
                            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" strokeWidth={1.5} />
                            <input
                                type="text"
                                placeholder="Buscar proyecto o cliente..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full h-12 bg-gray-200/50 border-none rounded-2xl pl-12 pr-4 text-sm font-bold text-gray-900 placeholder:text-system-gray focus:ring-2 focus:ring-blue-500/50 focus:bg-white transition-all outline-none"
                            />
                        </div>

                        {/* Client filter */}
                        <select
                            value={filters.clientId === '' ? '' : String(filters.clientId)}
                            onChange={(e) => updateFilter('clientId', e.target.value === '' ? '' : Number(e.target.value))}
                            className="h-12 px-4 rounded-2xl border-0 bg-gray-200/50 text-sm font-bold text-gray-900 focus:ring-2 focus:ring-blue-500/50 focus:bg-white outline-none min-w-[180px]"
                        >
                            <option value="">Todos los clientes</option>
                            {clients.map((c) => (
                                <option key={c.id} value={String(c.id)}>
                                    {c.display_name}
                                </option>
                            ))}
                        </select>

                        {/* View Switcher */}
                        <div className="bg-gray-200/50 p-1 rounded-xl flex gap-1 h-12">
                            <button
                                onClick={() => setViewMode('board')}
                                className={cn(
                                    "px-4 rounded-lg transition-all flex items-center justify-center",
                                    viewMode === 'board' ? "bg-white text-gray-900 shadow-sm" : "text-system-gray hover:text-gray-900"
                                )}
                            >
                                <Layout size={20} strokeWidth={2} />
                            </button>
                            <button
                                onClick={() => setViewMode('list')}
                                className={cn(
                                    "px-4 rounded-lg transition-all flex items-center justify-center",
                                    viewMode === 'list' ? "bg-white text-gray-900 shadow-sm" : "text-system-gray hover:text-gray-900"
                                )}
                            >
                                <List size={20} strokeWidth={2} />
                            </button>
                        </div>
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
                                        className="min-w-[340px] flex flex-col gap-4 snap-start"
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
        </div>
    );
}
