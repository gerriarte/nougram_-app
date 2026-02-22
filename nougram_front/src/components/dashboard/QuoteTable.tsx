'use client';

import React from 'react';
import { Quote } from './QuoteCard';
import { useRouter } from 'next/navigation';
import { Edit, ArrowUpRight, Link as LinkIcon, Check } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { quoteService } from '@/services/quoteService';

interface QuoteTableProps {
    quotes: Quote[];
    onStatusChange: (id: string, status: Quote['status']) => void;
}

export function QuoteTable({ quotes, onStatusChange }: QuoteTableProps) {
    const router = useRouter();
    const [copiedId, setCopiedId] = React.useState<string | null>(null);

    const handleCopyLink = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const token = await quoteService.generatePublicLink(id);
        const url = `${window.location.origin}/proposal/${token}`;
        await navigator.clipboard.writeText(url);
        setCopiedId(id);
        setTimeout(() => setCopiedId(null), 2000);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'draft': return 'bg-gray-100 text-gray-600';
            case 'sent': return 'bg-blue-50 text-blue-600';
            case 'viewed': return 'bg-yellow-50 text-yellow-600';
            case 'accepted': return 'bg-green-50 text-green-600';
            case 'rejected': return 'bg-red-50 text-red-600';
            default: return 'bg-gray-100 text-gray-600';
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'draft': return 'Borrador';
            case 'sent': return 'Enviada';
            case 'viewed': return 'Visto';
            case 'accepted': return 'Aceptada';
            case 'rejected': return 'Rechazada';
            case 'expired': return 'Vencida';
            default: return status;
        }
    };

    const getMarginColor = (margin: number) => {
        if (margin >= 30) return 'text-green-600';
        if (margin >= 15) return 'text-yellow-600';
        return 'text-red-600';
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return 'Reciente';
        // Try to parse relative "Hace ..." or simple date?
        // The mock data has "Hace 2d". We can just display it.
        return dateStr;
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-500 uppercase bg-gray-50/50 border-b border-gray-100">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Fecha</th>
                            <th className="px-6 py-4 font-semibold">Proyecto</th>
                            <th className="px-6 py-4 font-semibold">Cliente</th>
                            <th className="px-6 py-4 font-semibold text-right">Valor</th>
                            <th className="px-6 py-4 font-semibold text-center">Margen</th>
                            <th className="px-6 py-4 font-semibold">Estado</th>
                            <th className="px-6 py-4 font-semibold text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {quotes.map((quote) => (
                            <tr key={quote.id} className="hover:bg-gray-50/50 transition-colors group">
                                <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                                    {formatDate(quote.sentAt)}
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex flex-col">
                                        <span className="font-semibold text-gray-900">{quote.project}</span>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-md font-medium">
                                                V{quote.version}
                                            </span>
                                            <span className="text-xs text-gray-400">#{quote.id.substring(0, 6)}</span>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 font-medium text-gray-700">
                                    {quote.client}
                                </td>
                                <td className="px-6 py-4 text-right font-bold text-gray-900">
                                    ${quote.amount.toLocaleString()} <span className="text-xs text-gray-400 font-normal">{quote.currency}</span>
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <div className={`font-bold ${getMarginColor(quote.margin)} text-xs px-2 py-1 rounded-full bg-opacity-10 inline-block`}>
                                        {quote.margin}%
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <select
                                        value={quote.status}
                                        onChange={(e) => onStatusChange(quote.id, e.target.value as Quote['status'])}
                                        className={`text-xs font-bold uppercase tracking-wide border-none rounded-full px-2 py-1 cursor-pointer focus:ring-2 focus:ring-blue-500 ${getStatusColor(quote.status)}`}
                                    >
                                        <option value="draft">Borrador</option>
                                        <option value="sent">Enviada</option>
                                        <option value="viewed">Visto</option>
                                        <option value="accepted">Aceptada</option>
                                        <option value="rejected">Rechazada</option>
                                    </select>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-8 w-8 p-0 rounded-full text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                                            onClick={(e) => handleCopyLink(quote.id, e)}
                                            title="Copiar Enlace Público"
                                        >
                                            {copiedId === quote.id ? <Check size={16} className="text-green-600" /> : <LinkIcon size={16} />}
                                        </Button>

                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-8 px-2 text-xs font-medium text-gray-400 hover:text-gray-900 hover:bg-gray-100/50"
                                            onClick={() => router.push(`/dashboard/quotes/${quote.id}/edit`)}
                                        >
                                            <Edit size={14} className="mr-1.5" />
                                            Editar Costos
                                        </Button>

                                        <Button
                                            size="sm"
                                            className="h-8 px-4 text-xs font-bold bg-blue-600 text-white hover:bg-blue-700 shadow-md shadow-blue-100 transition-all rounded-lg flex items-center gap-1.5 active:scale-95"
                                            onClick={() => router.push(`/dashboard/quotes/${quote.id}/tracking`)}
                                        >
                                            Ver Trazabilidad
                                            <ArrowUpRight size={14} strokeWidth={2.5} />
                                        </Button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
