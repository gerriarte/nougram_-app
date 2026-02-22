
import React from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ArrowLeft, Clock, Eye, Download } from 'lucide-react';
import { Quote } from '@/components/dashboard/QuoteCard';

interface QuoteTrackingViewProps {
    quote: Quote;
    onBack: () => void;
}

export function QuoteTrackingView({ quote, onBack }: QuoteTrackingViewProps) {

    // Calculate Interest Level
    const interestLevel = quote.viewedCount > 3 ? 'Alto' : quote.viewedCount > 0 ? 'Medio' : 'Bajo';
    const interestColor = quote.viewedCount > 3 ? 'text-green-600 bg-green-50' : quote.viewedCount > 0 ? 'text-yellow-600 bg-yellow-50' : 'text-gray-600 bg-gray-50';
    const lastActivity = quote.lastViewedAt || quote.sentAt || 'Sin actividad reciente';

    const events = [
        quote.sentAt ? {
            id: 'sent',
            type: 'sent' as const,
            at: quote.sentAt,
            label: 'Cotización enviada',
            detail: 'La propuesta fue enviada al cliente.',
        } : null,
        quote.viewedCount > 0 ? {
            id: 'viewed',
            type: 'viewed' as const,
            at: quote.lastViewedAt || 'Reciente',
            label: 'Cotización consultada',
            detail: `Aperturas registradas: ${quote.viewedCount}`,
        } : null,
        quote.downloadCount > 0 ? {
            id: 'downloaded',
            type: 'downloaded' as const,
            at: 'Reciente',
            label: 'Archivo descargado',
            detail: `Descargas registradas: ${quote.downloadCount}`,
        } : null,
    ].filter(Boolean) as Array<{
        id: string;
        type: 'sent' | 'viewed' | 'downloaded';
        at: string;
        label: string;
        detail: string;
    }>;

    return (
        <div className="min-h-screen bg-[#F5F5F7] p-6 lg:p-12">
            <div className="max-w-5xl mx-auto space-y-6">

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" onClick={onBack} className="h-10 w-10 p-0 rounded-full hover:bg-white/50">
                            <ArrowLeft size={20} />
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold text-[#1D1D1F]">Trazabilidad</h1>
                            <p className="text-gray-500">{quote.project} - {quote.client}</p>
                        </div>
                    </div>
                    <div className={`px-4 py-1.5 rounded-full font-bold text-sm ${interestColor}`}>
                        Interés: {interestLevel}
                    </div>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>
                        <CardContent className="pt-6 flex items-center gap-4">
                            <div className="p-3 bg-yellow-50 text-yellow-600 rounded-full">
                                <Eye size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 font-medium">Total Aperturas</p>
                                <p className="text-2xl font-bold text-gray-900">{quote.viewedCount}</p>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-6 flex items-center gap-4">
                            <div className="p-3 bg-blue-50 text-blue-600 rounded-full">
                                <Download size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 font-medium">Descargas PDF</p>
                                <p className="text-2xl font-bold text-gray-900">{quote.downloadCount}</p>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-6 flex items-center gap-4">
                            <div className="p-3 bg-green-50 text-green-600 rounded-full">
                                <Clock size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 font-medium">Última Actividad</p>
                                <p className="text-2xl font-bold text-gray-900">{lastActivity}</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Timeline */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Timeline de Eventos</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
                            {(events.length > 0 ? events : [{
                                id: 'no-activity',
                                type: 'sent' as const,
                                at: 'Pendiente',
                                label: 'Sin eventos registrados',
                                detail: 'Cuando el cliente abra o descargue la cotización aparecerá aquí.',
                            }]).map((event) => (
                                <div key={event.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">

                                    {/* Icon */}
                                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                                        {event.type === 'viewed' && <Eye size={16} className="text-yellow-600" />}
                                        {event.type === 'downloaded' && <Download size={16} className="text-blue-600" />}
                                        {event.type === 'sent' && <Clock size={16} className="text-gray-400" />}
                                    </div>

                                    {/* Content */}
                                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                                        <div className="flex items-center justify-between space-x-2 mb-1">
                                            <div className="font-bold text-gray-900">
                                                {event.label}
                                            </div>
                                            <time className="font-caveat font-medium text-indigo-500 text-xs">{event.at}</time>
                                        </div>
                                        <div className="text-gray-500 text-sm">
                                            <div className="mt-1">{event.detail}</div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
