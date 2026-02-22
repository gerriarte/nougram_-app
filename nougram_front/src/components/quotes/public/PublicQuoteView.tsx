'use client';

import React, { useState } from 'react';
import { Quote } from '@/components/dashboard/QuoteCard';
import { Button } from '@/components/ui/Button';
import { CheckCircle2, XCircle, Download, Calendar, Mail, Building, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { quoteService } from '@/services/quoteService';

interface PublicQuoteViewProps {
    quote: Quote;
}

export function PublicQuoteView({ quote: initialQuote }: PublicQuoteViewProps) {
    const [quote, setQuote] = useState(initialQuote);
    const [actionState, setActionState] = useState<'idle' | 'accepting' | 'rejecting' | 'success_accepted' | 'success_rejected'>('idle');
    const [rejectReason, setRejectReason] = useState('');
    const [showRejectModal, setShowRejectModal] = useState(false);

    const handleAccept = async () => {
        setActionState('accepting');
        try {
            await quoteService.acceptQuote(quote.publicToken!);
            setActionState('success_accepted');
            setQuote({ ...quote, status: 'accepted' });
        } catch (error) {
            console.error('Error accepting quote', error);
            setActionState('idle');
        }
    };

    const handleReject = async () => {
        setActionState('rejecting');
        try {
            await quoteService.rejectQuote(quote.publicToken!, rejectReason);
            setActionState('success_rejected');
            setQuote({ ...quote, status: 'rejected' });
            setShowRejectModal(false);
        } catch (error) {
            console.error('Error rejecting quote', error);
            setActionState('idle');
        }
    };

    if (actionState === 'success_accepted') {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white p-12 rounded-[32px] shadow-xl text-center max-w-md w-full"
                >
                    <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle2 size={40} />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">¡Gracias por tu confianza!</h2>
                    <p className="text-gray-500 mb-8">Hemos recibido tu aceptación para el proyecto <strong>{quote.project}</strong>. Nuestro equipo se pondrá en contacto contigo a la brevedad.</p>
                    <Button onClick={() => window.print()} variant="outline" className="w-full">
                        Descargar Comprobante
                    </Button>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#F5F5F7] font-sans text-[#1D1D1F]">
            {/* Header Branding */}
            <header className="bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-200/50">
                <div className="max-w-4xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-black rounded-xl flex items-center justify-center text-white font-bold text-xl">
                            N
                        </div>
                        <span className="font-bold text-lg tracking-tight">Nougram</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide
                            ${quote.status === 'accepted' ? 'bg-green-100 text-green-700' :
                                quote.status === 'rejected' ? 'bg-red-100 text-red-700' :
                                    quote.status === 'expired' ? 'bg-gray-100 text-gray-500' : 'bg-blue-50 text-blue-600'}`}>
                            {quote.status === 'sent' || quote.status === 'viewed' ? 'Propuesta Activa' :
                                quote.status === 'accepted' ? 'Aceptada' :
                                    quote.status === 'rejected' ? 'Rechazada' : quote.status}
                        </span>
                        {quote.tokenExpiresAt && (
                            <span className="text-xs text-gray-400 font-medium hidden sm:flex items-center gap-1.5">
                                <ClockIcon /> Vence: {new Date(quote.tokenExpiresAt).toLocaleDateString()}
                            </span>
                        )}
                    </div>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Main Content */}
                    <div className="md:col-span-2 space-y-8">
                        {/* Cover / Title */}
                        <div className="bg-white rounded-[32px] p-8 shadow-sm border border-gray-100">
                            <span className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-2 block">Propuesta Comercial</span>
                            <h1 className="text-4xl font-bold text-gray-900 leading-tight mb-4">{quote.project}</h1>
                            <p className="text-lg text-gray-500 font-medium">Preparado para: <span className="text-gray-900">{quote.client}</span></p>
                        </div>

                        {/* Scope / Items (Mock for now, needs real items in future) */}
                        <div className="bg-white rounded-[32px] p-8 shadow-sm border border-gray-100">
                            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                                <FileText size={20} className="text-blue-500" />
                                Alcance del Servicio
                            </h3>

                            {/* Placeholder Items List - In real app, quote.items would be available */}
                            <div className="space-y-6">
                                <div className="flex items-start justify-between pb-6 border-b border-gray-50 last:border-0 last:pb-0">
                                    <div>
                                        <h4 className="font-bold text-gray-900">Desarrollo {quote.project}</h4>
                                        <p className="text-sm text-gray-500 mt-1">Implementación completa según requerimientos.</p>
                                    </div>
                                    <span className="font-bold text-gray-900">
                                        ${quote.amount.toLocaleString()} {quote.currency}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Terms */}
                        <div className="prose prose-sm max-w-none text-gray-500">
                            <p>Esta propuesta es válida por 30 días. Los precios no incluyen IVA a menos que se especifique.</p>
                        </div>
                    </div>

                    {/* Sidebar / Summary */}
                    <div className="space-y-6">
                        <div className="bg-white rounded-[32px] p-8 shadow-[0_20px_40px_rgba(0,0,0,0.06)] border border-gray-100 sticky top-28">
                            <h3 className="text-gray-400 text-xs font-bold uppercase tracking-widest mb-6">Resumen de Inversión</h3>

                            <div className="flex items-baseline gap-2 mb-2">
                                <span className="text-4xl font-bold text-gray-900 tracking-tight">
                                    ${quote.amount.toLocaleString()}
                                </span>
                                <span className="text-lg font-medium text-gray-400">{quote.currency}</span>
                            </div>
                            <p className="text-sm text-gray-400 font-medium mb-8">Total + Impuestos de Ley</p>

                            {/* Actions */}
                            {quote.status !== 'accepted' && quote.status !== 'rejected' && (
                                <div className="space-y-3">
                                    <Button
                                        onClick={handleAccept}
                                        disabled={actionState === 'accepting'}
                                        className="w-full h-14 text-base font-bold bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-2xl shadow-lg shadow-blue-200 transition-all active:scale-95"
                                    >
                                        {actionState === 'accepting' ? 'Procesando...' : 'Aceptar Propuesta'}
                                    </Button>
                                    <Button
                                        onClick={() => setShowRejectModal(true)}
                                        variant="ghost"
                                        className="w-full text-gray-500 hover:text-red-500 font-medium h-12 hover:bg-red-50 rounded-2xl"
                                    >
                                        Rechazar
                                    </Button>

                                    <div className="pt-4 border-t border-gray-100 mt-4 flex justify-center">
                                        <Button variant="outline" size="sm" className="gap-2 rounded-full text-xs">
                                            <Download size={14} /> Descargar PDF
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {(quote.status === 'accepted' || quote.status === 'rejected') && (
                                <div className={`p-4 rounded-2xl text-center font-bold text-sm ${quote.status === 'accepted' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                                    Propuesta {quote.status === 'accepted' ? 'Aceptada' : 'Rechazada'}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>

            {/* Reject Modal */}
            <AnimatePresence>
                {showRejectModal && (
                    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-white rounded-[24px] p-8 max-w-md w-full shadow-2xl"
                        >
                            <h3 className="text-xl font-bold text-gray-900 mb-2">Rechazar Propuesta</h3>
                            <p className="text-gray-500 text-sm mb-6">Lamentamos que la propuesta no sea de tu agrado. ¿Podrías indicarnos la razón? Esto nos ayuda a mejorar.</p>

                            <textarea
                                value={rejectReason}
                                onChange={(e) => setRejectReason(e.target.value)}
                                placeholder="Ej: Precio alto, alcance insuficiente..."
                                className="w-full min-h-[100px] p-4 bg-gray-50 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 outline-none text-sm mb-6 resize-none"
                            />

                            <div className="flex gap-3">
                                <Button
                                    variant="outline"
                                    onClick={() => setShowRejectModal(false)}
                                    className="flex-1 rounded-xl"
                                >
                                    Cancelar
                                </Button>
                                <Button
                                    onClick={handleReject}
                                    variant="destructive"
                                    className="flex-1 rounded-xl bg-red-500 hover:bg-red-600 text-white"
                                >
                                    Confirmar Rechazo
                                </Button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}

function ClockIcon() {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
    )
}
