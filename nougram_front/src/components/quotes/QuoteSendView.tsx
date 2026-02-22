
import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { ArrowLeft, Send, Paperclip, Eye } from 'lucide-react';
import { Quote } from '@/components/dashboard/QuoteCard';

export interface QuoteSendPayload {
    to: string;
    subject: string;
    message: string;
    includePdf: boolean;
    trackingOpen: boolean;
}

interface QuoteSendViewProps {
    quote: Quote;
    initialToEmail?: string;
    onSend: (data: QuoteSendPayload) => Promise<void>;
    onCancel: () => void;
}

export function QuoteSendView({ quote, initialToEmail, onSend, onCancel }: QuoteSendViewProps) {
    const [to, setTo] = useState(initialToEmail || '');
    const [subject, setSubject] = useState(`Cotización para ${quote.project} - ${quote.version}`);
    const [message, setMessage] = useState('');
    const [includePdf, setIncludePdf] = useState(true);
    const [trackingOpen, setTrackingOpen] = useState(true);
    const [isSending, setIsSending] = useState(false);

    const handleSend = async () => {
        if (!to.trim()) {
            alert('Ingresa el correo del cliente antes de enviar.');
            return;
        }
        setIsSending(true);
        await onSend({ to, subject, message, includePdf, trackingOpen });
        setIsSending(false);
    };

    return (
        <div className="min-h-screen bg-[#F5F5F7] p-6 lg:p-12">
            <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">

                {/* Left: Configuration Form */}
                <div className="space-y-6">
                    <div className="flex items-center gap-4 mb-8">
                        <Button variant="ghost" onClick={onCancel} className="h-10 w-10 p-0 rounded-full hover:bg-white/50">
                            <ArrowLeft size={20} />
                        </Button>
                        <h1 className="text-2xl font-bold text-[#1D1D1F]">Enviar Cotización</h1>
                    </div>

                    <Card>
                        <CardContent className="space-y-6 pt-6">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-700">Para</label>
                                <Input value={to} onChange={e => setTo(e.target.value)} placeholder="cliente@empresa.com" />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-700">Asunto</label>
                                <Input value={subject} onChange={e => setSubject(e.target.value)} />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-700">Mensaje Personalizado</label>
                                <textarea
                                    className="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                                    placeholder="Escribe un mensaje opcional..."
                                    value={message}
                                    onChange={e => setMessage(e.target.value)}
                                />
                            </div>

                            <div className="border-t border-gray-100 pt-4 space-y-4">
                                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                                    <Paperclip size={16} /> Adjuntos
                                </h3>
                                <div className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg bg-gray-50/50">
                                    <input
                                        type="checkbox"
                                        checked={includePdf}
                                        onChange={e => setIncludePdf(e.target.checked)}
                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <span className="text-sm text-gray-700 font-medium">{`Cotización_${quote.project}_${quote.version}.pdf`}</span>
                                </div>
                            </div>

                            <div className="border-t border-gray-100 pt-4 space-y-4">
                                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                                    <Eye size={16} /> Tracking Inteligente
                                </h3>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        checked={trackingOpen}
                                        onChange={e => setTrackingOpen(e.target.checked)}
                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <div>
                                        <p className="text-sm font-medium text-gray-900">Activar Pixel de Seguimiento</p>
                                        <p className="text-xs text-gray-500">Recibe una notificación cuando el cliente abra el correo.</p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <div className="flex gap-4 pt-4">
                        <Button variant="secondary" onClick={onCancel} className="flex-1">
                            Cancelar
                        </Button>
                        <Button
                            className="flex-1 bg-black text-white hover:bg-gray-800"
                            onClick={handleSend}
                            disabled={isSending}
                        >
                            {isSending ? 'Enviando...' : (
                                <span className="flex items-center gap-2">
                                    <Send size={16} /> Enviar Cotización
                                </span>
                            )}
                        </Button>
                    </div>
                </div>

                {/* Right: Preview */}
                <div className="hidden lg:block space-y-6">
                    <h2 className="text-lg font-semibold text-gray-500 mb-8 pt-2">Vista Previa del Correo</h2>

                    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                        {/* Fake Browser/Mail Header */}
                        <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 flex gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-400"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                            <div className="w-3 h-3 rounded-full bg-green-400"></div>
                        </div>

                        <div className="p-8 space-y-6">
                            <div className="border-b border-gray-100 pb-6 space-y-1">
                                <p className="text-sm text-gray-500">De: <span className="text-gray-900 font-medium">Juan Pérez &lt;juan@nougram.co&gt;</span></p>
                                <p className="text-sm text-gray-500">Para: <span className="text-gray-900 font-medium">{to || 'Destinatario'}</span></p>
                                <p className="text-sm text-gray-500">Asunto: <span className="text-gray-900 font-medium">{subject}</span></p>
                            </div>

                            <div className="space-y-4 text-gray-600 text-sm leading-relaxed">
                                <p>Hola,</p>
                                {message ? (
                                    <p className="whitespace-pre-wrap">{message}</p>
                                ) : (
                                    <p className="italic text-gray-400">[Tu mensaje personalizado aparecerá aquí]</p>
                                )}

                                <p>Adjunto encontrarás la cotización para el proyecto <strong>{quote.project}</strong>.</p>

                                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 mt-4">
                                    <p className="font-semibold text-gray-900">{quote.project}</p>
                                    <p className="text-gray-500">Versión: {quote.version}</p>
                                    <p className="text-lg font-bold text-gray-900 mt-1">
                                        ${quote.amount.toLocaleString()} {quote.currency}
                                    </p>
                                    <div className="mt-3">
                                        <Button size="sm" className="w-full bg-[#1D1D1F] text-white">
                                            Ver Propuesta Online
                                        </Button>
                                    </div>
                                </div>
                            </div>

                            <div className="pt-6 border-t border-gray-100">
                                <p className="text-xs text-gray-400">
                                    Enviado con Nougram · Trazabilidad activada
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
