'use client';

import React from 'react';
import { Quote } from './QuoteCard';
import { useRouter } from 'next/navigation';
import { Edit, ArrowUpRight, Link as LinkIcon, Loader2, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useNougram } from '@/context/NougramCoreContext';
import { formatDisplayNumber, formatMoneyAmount } from '@/lib/utils';
import { quoteService } from '@/services/quoteService';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { toast } from 'sonner';

interface QuoteTableProps {
    quotes: Quote[];
    onStatusChange: (id: string, status: Quote['status']) => void;
    onOpenPublicAccess?: (quote: Quote) => void;
    publicAccessLoadingQuoteId?: string | null;
}

export function QuoteTable({ quotes, onStatusChange, onOpenPublicAccess, publicAccessLoadingQuoteId }: QuoteTableProps) {
    const router = useRouter();
    const { state } = useNougram();
    const displayCurrency = state.identity.primaryCurrency || 'COP';
    const [deletingQuoteId, setDeletingQuoteId] = React.useState<string | null>(null);
    const [quoteToConfirmDelete, setQuoteToConfirmDelete] = React.useState<Quote | null>(null);

    const requestDeleteQuote = (quote: Quote) => {
        setQuoteToConfirmDelete(quote);
    };

    const handleDeleteQuote = async () => {
        if (!quoteToConfirmDelete) return;
        const quote = quoteToConfirmDelete;
        if (!quote.quoteId) {
            toast.error('No se encontro el identificador de cotizacion para esta fila.');
            return;
        }
        try {
            setDeletingQuoteId(quote.id);
            const result = await quoteService.deleteOrRequestQuoteDeletion(quote.id, quote.quoteId);
            toast.success(result.message);
            setQuoteToConfirmDelete(null);
            window.location.reload();
        } catch (error) {
            toast.error(error instanceof Error ? error.message : 'No se pudo procesar la eliminacion.');
        } finally {
            setDeletingQuoteId(null);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'draft': return 'bg-gray-100 text-gray-600';
            case 'sent': return 'bg-primary-soft text-primary';
            case 'viewed': return 'bg-warning-soft text-amber-700';
            case 'accepted': return 'bg-success-soft text-success';
            case 'rejected': return 'bg-critical-soft text-critical';
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
        if (margin >= 25) return 'text-success';
        if (margin >= 15) return 'text-warning';
        return 'text-critical';
    };

    const getFollowUpHint = (quote: Quote) => {
        if (quote.status === 'draft') return 'Pendiente por enviar';
        if (quote.status === 'sent' && quote.viewedCount === 0) return 'Enviada, sin apertura';
        if (quote.status === 'viewed') return `Vista ${quote.viewedCount || 1} vez${(quote.viewedCount || 1) > 1 ? 'es' : ''}`;
        if (quote.status === 'accepted') return 'Cerrada como ganada';
        if (quote.status === 'rejected') return 'Cerrada como perdida';
        return 'Seguimiento activo';
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return 'Reciente';
        // Keep backend-formatted relative strings as-is.
        return dateStr;
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Mobile: card list */}
            <div className="md:hidden divide-y divide-gray-100">
                {quotes.map((quote) => (
                    <div key={quote.id} className="p-4 space-y-3">
                        <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                                <p className="font-bold text-gray-900 leading-tight">{quote.project}</p>
                                <p className="text-xs text-gray-500 mt-1">{quote.client}</p>
                                <div className="flex flex-wrap items-center gap-2 mt-2">
                                    <span className="text-[10px] text-primary bg-primary-soft px-2 py-0.5 rounded-full font-bold">
                                        V{quote.version}
                                    </span>
                                    {quote.isActive === false ? (
                                        <span className="text-[10px] text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md font-bold">
                                            Inactiva (PM)
                                        </span>
                                    ) : null}
                                    <span className="text-[10px] text-gray-400">#{quote.id.substring(0, 6)}</span>
                                    <span className="text-[10px] text-gray-400">{formatDate(quote.sentAt)}</span>
                                </div>
                            </div>
                            <select
                                value={quote.status}
                                onChange={(e) => onStatusChange(quote.id, e.target.value as Quote['status'])}
                                className={`text-[11px] font-bold uppercase tracking-wide border-none rounded-full px-2 py-1 cursor-pointer focus:ring-2 focus:ring-gray-400 shrink-0 ${getStatusColor(quote.status)}`}
                            >
                                <option value="draft">Borrador</option>
                                <option value="sent">Enviada</option>
                                <option value="viewed">Visto</option>
                                <option value="accepted">Aceptada</option>
                                <option value="rejected">Rechazada</option>
                            </select>
                        </div>
                        <p className="text-[11px] text-gray-500">{getFollowUpHint(quote)}</p>
                        <div className="flex flex-wrap items-center justify-between gap-2">
                            <div>
                                <p className="text-xs text-gray-500">Total factura</p>
                                <p className="text-sm font-bold text-gray-900">
                                    ${formatMoneyAmount(quote.totalWithTaxes)}{' '}
                                    <span className="text-xs font-normal text-gray-400">{displayCurrency}</span>
                                </p>
                            </div>
                            <div className={`font-bold ${getMarginColor(quote.margin)} text-sm px-3 py-1 rounded-full bg-opacity-10`}>
                                {formatDisplayNumber(quote.margin, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}% margen
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 pt-1">
                            <Button
                                variant="outline"
                                className="w-full h-11 rounded-2xl font-bold justify-center"
                                onClick={() => router.push(`/dashboard/quotes/${quote.id}/edit`)}
                            >
                                <Edit size={16} className="mr-2" />
                                Editar cotización
                            </Button>
                            <Button
                                className="w-full h-11 rounded-2xl font-bold bg-gray-900 text-white hover:bg-gray-700"
                                onClick={() => router.push(`/dashboard/quotes/${quote.id}/tracking`)}
                            >
                                Ver trazabilidad
                                <ArrowUpRight size={16} className="ml-2" strokeWidth={2.5} />
                            </Button>
                            <Button
                                variant="ghost"
                                className="w-full h-10 rounded-xl text-sm font-semibold text-gray-600"
                                onClick={() => onOpenPublicAccess?.(quote)}
                                disabled={publicAccessLoadingQuoteId === quote.id}
                            >
                                {publicAccessLoadingQuoteId === quote.id ? (
                                    <Loader2 size={16} className="animate-spin mr-2 inline" />
                                ) : (
                                    <LinkIcon size={16} className="mr-2 inline" />
                                )}
                                Acceso público
                            </Button>
                            <Button
                                variant="ghost"
                                className="w-full h-10 rounded-xl text-sm font-semibold text-red-600"
                                onClick={() => requestDeleteQuote(quote)}
                                disabled={deletingQuoteId === quote.id}
                            >
                                {deletingQuoteId === quote.id ? (
                                    <Loader2 size={16} className="animate-spin mr-2 inline" />
                                ) : (
                                    <Trash2 size={16} className="mr-2 inline" />
                                )}
                                Eliminar cotización
                            </Button>
                        </div>
                    </div>
                ))}
            </div>

            <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-500 uppercase bg-gray-50/50 border-b border-gray-100">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Fecha</th>
                            <th className="px-6 py-4 font-semibold">Proyecto</th>
                            <th className="px-6 py-4 font-semibold">Cliente</th>
                            <th className="px-6 py-4 font-semibold text-right">Valor Facturado</th>
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
                                            <span className="text-[10px] text-primary bg-primary-soft px-1.5 py-0.5 rounded-full font-semibold">
                                                V{quote.version}
                                            </span>
                                            {quote.isActive === false ? (
                                                <span className="text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded-md font-bold">
                                                    Inactiva (PM)
                                                </span>
                                            ) : null}
                                            <span className="text-xs text-gray-400">#{quote.id.substring(0, 6)}</span>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 font-medium text-gray-700">
                                    {quote.client}
                                </td>
                                <td className="px-6 py-4 text-right font-bold text-gray-900">
                                    ${formatMoneyAmount(quote.totalWithTaxes)} <span className="text-xs text-gray-400 font-normal">{displayCurrency}</span>
                                    <div className="text-[10px] font-medium text-gray-400">Total factura (incluye impuestos)</div>
                                    <div className="text-[10px] text-gray-500 mt-0.5">
                                        Base ${formatMoneyAmount(quote.totalClientPrice || 0)} + Impuestos ${formatMoneyAmount(quote.totalTaxes || 0)}
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <div className={`font-bold ${getMarginColor(quote.margin)} text-xs px-2 py-1 rounded-full bg-opacity-10 inline-block`}>
                                        {formatDisplayNumber(quote.margin, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="mb-1 text-[10px] text-gray-500 uppercase tracking-wide">
                                        {getFollowUpHint(quote)}
                                    </div>
                                    <select
                                        value={quote.status}
                                        onChange={(e) => onStatusChange(quote.id, e.target.value as Quote['status'])}
                                        className={`text-xs font-bold uppercase tracking-wide border-none rounded-full px-2 py-1 cursor-pointer focus:ring-2 focus:ring-gray-400 ${getStatusColor(quote.status)}`}
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
                                            className="h-8 w-8 p-0 rounded-full text-gray-400 hover:text-primary hover:bg-primary-soft transition-colors"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onOpenPublicAccess?.(quote);
                                            }}
                                            title="Ver acceso público"
                                            disabled={publicAccessLoadingQuoteId === quote.id}
                                        >
                                            {publicAccessLoadingQuoteId === quote.id ? <Loader2 size={16} className="animate-spin" /> : <LinkIcon size={16} />}
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
                                            className="h-8 px-3 text-[12px] font-semibold bg-gray-900 text-white hover:bg-gray-700 rounded-lg flex items-center gap-1.5 active:scale-95 transition-all"
                                            onClick={() => router.push(`/dashboard/quotes/${quote.id}/tracking`)}
                                        >
                                            Trazabilidad
                                            <ArrowUpRight size={13} strokeWidth={2.5} />
                                        </Button>

                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-8 px-2 text-xs font-medium text-red-500 hover:text-red-700 hover:bg-red-50"
                                            onClick={() => requestDeleteQuote(quote)}
                                            disabled={deletingQuoteId === quote.id}
                                        >
                                            {deletingQuoteId === quote.id ? (
                                                <Loader2 size={14} className="animate-spin mr-1.5" />
                                            ) : (
                                                <Trash2 size={14} className="mr-1.5" />
                                            )}
                                            Eliminar
                                        </Button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <Dialog open={Boolean(quoteToConfirmDelete)} onOpenChange={(open) => !open && setQuoteToConfirmDelete(null)}>
                <DialogContent className="sm:max-w-[520px]">
                    <DialogHeader>
                        <DialogTitle>Confirmar eliminación de cotización</DialogTitle>
                        <DialogDescription>
                            Esta acción aplica según rol:
                            <br />- Project Manager: desactiva la cotización para que no sume en dashboard.
                            <br />- Admin Financiero / Owner / Super Admin: elimina la cotización.
                        </DialogDescription>
                    </DialogHeader>
                    {quoteToConfirmDelete ? (
                        <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
                            Proyecto: <span className="font-semibold text-gray-800">{quoteToConfirmDelete.project}</span>
                            <br />
                            Cliente: <span className="font-semibold text-gray-800">{quoteToConfirmDelete.client}</span>
                            <br />
                            Version: <span className="font-semibold text-gray-800">V{quoteToConfirmDelete.version}</span>
                        </div>
                    ) : null}
                    <DialogFooter>
                        <Button
                            variant="secondary"
                            onClick={() => setQuoteToConfirmDelete(null)}
                            disabled={Boolean(deletingQuoteId)}
                        >
                            Cancelar
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={() => void handleDeleteQuote()}
                            disabled={Boolean(deletingQuoteId)}
                        >
                            {deletingQuoteId ? <Loader2 size={14} className="animate-spin mr-2" /> : null}
                            Confirmar
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
