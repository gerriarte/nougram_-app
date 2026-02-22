
'use client';

import React, { useState } from 'react';
import { QuoteCard, Quote } from '@/components/dashboard/QuoteCard';
import { KPIWidgets, AlertsWidget } from '@/components/dashboard/KPIWidgets';
import { Search, Filter, Plus, Layout, List, ChevronRight, MoreHorizontal } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { useQuotePipeline } from '@/hooks/useQuotePipeline';
import { motion, AnimatePresence } from 'framer-motion';
import { QuoteTable } from '@/components/dashboard/QuoteTable';
import { cn } from '@/lib/utils';
import { BCRSummaryCard } from '@/components/admin/BCRSummaryCard';

export function QuotePipeline() {
    const {
        quotes: filteredQuotes,
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

    return (
        <div className="space-y-12 pb-20">
            {/* 1. KPIs Section */}
            {/* 1. KPIs Section */}
            <div className="space-y-6">
                <KPIWidgets metrics={metrics} />
                <AlertsWidget />
            </div>

            {/* 2. Pipeline Controls */}
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Ventas & Pipeline</h2>
                        <p className="text-sm text-system-gray font-medium mt-1">Monitorea el flujo de tus propuestas comerciales.</p>
                    </div>

                    <div className="flex items-center gap-3 w-full md:w-auto">
                        {/* Search */}
                        <div className="relative group flex-1 md:w-80">
                            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" strokeWidth={1.5} />
                            <input
                                type="text"
                                placeholder="Buscar proyecto o cliente..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full h-12 bg-gray-200/50 border-none rounded-2xl pl-12 pr-4 text-sm font-bold text-gray-900 placeholder:text-system-gray focus:ring-2 focus:ring-blue-500/50 focus:bg-white transition-all outline-none"
                            />
                        </div>

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
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
