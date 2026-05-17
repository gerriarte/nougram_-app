import React, { useEffect, useState } from 'react';
import { useQuoteCreation } from '@/context/QuoteCreationContext';
import { Card } from '@/components/ui/Card'; // Assuming exist
import { Button } from '@/components/ui/Button'; // Assuming exist
import { Loader2, Sparkles, Send } from 'lucide-react';
import { AnimatedCounter } from '../AnimatedCounter';
import { MarginIndicator } from '../MarginIndicator';
import { motion } from 'framer-motion';

export function Step4Summary() {
    const {
        projectInfo,
        services,
        totalAmount,
        margin,
        executiveSummary,
        generateSummary,
        isGeneratingSummary
    } = useQuoteCreation();

    useEffect(() => {
        if (!executiveSummary && services.length > 0 && !isGeneratingSummary) {
            generateSummary();
        }
    }, []);

    // Derived costs (Mock logic)
    const totalCost = totalAmount * (1 - (margin / 100));

    return (
        <div className="space-y-6">
            <div className="text-center space-y-2 mb-8">
                <h2 className="text-2xl font-bold tracking-tight">Resumen y Cierre</h2>
                <p className="text-gray-500">Revisa los detalles antes de crear la cotización.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Financials */}
                <div className="lg:col-span-1 space-y-6">
                    <Card className="p-6 glass-card space-y-6">
                        <h3 className="font-bold text-gray-900">Métricas Financieras</h3>

                        <div className="space-y-4">
                            <div>
                                <p className="text-sm text-gray-500">Precio al Cliente</p>
                                <AnimatedCounter
                                    value={totalAmount}
                                    currency={projectInfo.currency}
                                    className="text-3xl font-bold block"
                                />
                            </div>

                            <div className="pt-4 border-t border-gray-100">
                                <p className="text-sm text-gray-500 mb-1">Costo Interno</p>
                                <span className="text-lg font-medium text-gray-700">
                                    {projectInfo.currency} {totalCost.toLocaleString()}
                                </span>
                            </div>

                            <div className="pt-4 border-t border-gray-100">
                                <MarginIndicator margin={margin} />
                            </div>
                        </div>
                    </Card>

                    <Card className="p-6 glass-card">
                        <h3 className="font-bold text-gray-900 mb-4">Servicios Incluidos</h3>
                        <ul className="space-y-2 text-sm">
                            {services.map(s => (
                                <li key={s.serviceId} className="flex justify-between">
                                    <span>{s.serviceName}</span>
                                    <span className="font-medium text-gray-600">{s.hours}h</span>
                                </li>
                            ))}
                        </ul>
                    </Card>
                </div>

                {/* Right Column: AI Summary */}
                <div className="lg:col-span-2">
                    <Card className="p-6 glass-card h-full flex flex-col">
                        <div className="flex justify-between items-center mb-4">
                            <div className="flex items-center gap-2">
                                <div className="bg-purple-100 p-2 rounded-lg text-purple-600">
                                    <Sparkles size={18} />
                                </div>
                                <h3 className="font-bold text-gray-900">Resumen Ejecutivo (IA)</h3>
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={generateSummary}
                                disabled={isGeneratingSummary}
                            >
                                {isGeneratingSummary ? <Loader2 className="animate-spin w-4 h-4" /> : 'Regenerar'}
                            </Button>
                        </div>

                        <div className="flex-1 bg-white/50 rounded-xl p-6 min-h-[300px] border border-gray-100 relative">
                            {isGeneratingSummary ? (
                                <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm rounded-xl z-10">
                                    <Loader2 className="w-8 h-8 animate-spin text-purple-500 mb-2" />
                                    <span className="text-sm text-purple-600 font-medium">Redactando propuesta...</span>
                                </div>
                            ) : (
                                <textarea
                                    className="w-full h-full bg-transparent border-0 resize-none focus:ring-0 text-gray-700 leading-relaxed font-sans"
                                    value={executiveSummary}
                                    onChange={(e) => { }} // ReadOnly for now or add setter in context
                                    placeholder="El resumen generado aparecerá aquí..."
                                />
                            )}
                        </div>

                        <div className="mt-4 flex justify-end">
                            <span className="text-xs text-gray-400">Powered by MockAI API</span>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
}
