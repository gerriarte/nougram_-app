
import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Eye, Clock, CheckCircle2, XCircle, MoreHorizontal, ArrowUpRight, Copy, Send } from 'lucide-react';

export interface Quote {
    id: string;
    project: string;
    client: string;
    amount: number;
    currency: string;
    margin: number;
    version: number;
    history?: { version: number; amount: number; date: string }[];
    status: 'draft' | 'sent' | 'viewed' | 'accepted' | 'rejected' | 'expired';
    sentAt?: string;
    expiresAt?: string;
    viewedCount: number;
    downloadCount: number;

    // Public Proposal
    publicToken?: string;
    tokenExpiresAt?: string;
    lastViewedAt?: string;
}

interface QuoteCardProps extends React.HTMLAttributes<HTMLDivElement> {
    quote: Quote;
    onStatusChange?: (id: string, status: Quote['status']) => void;
}

export function QuoteCard({ quote, onStatusChange, ...props }: QuoteCardProps) {
    const router = useRouter();

    // Status Logic
    const getStatusStyle = (status: string) => {
        switch (status) {
            case 'draft': return { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Borrador', icon: Clock };
            case 'sent': return { bg: 'bg-blue-50', text: 'text-blue-600', label: 'Enviada', icon: Send };
            case 'viewed': return { bg: 'bg-yellow-50', text: 'text-yellow-600', label: 'Visto', icon: Eye };
            case 'accepted': return { bg: 'bg-[#E8F8F0]', text: 'text-[#1D9D5D]', label: 'Aceptada', icon: CheckCircle2 };
            case 'rejected': return { bg: 'bg-red-50', text: 'text-red-500', label: 'Rechazada', icon: XCircle };
            case 'expired': return { bg: 'bg-gray-100', text: 'text-gray-500', label: 'Vencida', icon: Clock };
            default: return { bg: 'bg-gray-50', text: 'text-gray-500', label: status, icon: Clock };
        }
    };

    const statusStyle = getStatusStyle(quote.status);
    const StatusIcon = statusStyle.icon;

    // Margin Color
    const getMarginColor = (margin: number) => {
        if (margin >= 30) return 'text-[#34C759]'; // Green
        if (margin >= 15) return 'text-[#FF9500]'; // Orange
        return 'text-[#FF3B30]'; // Red
    };

    return (
        <div {...props} className={`group relative flex flex-col rounded-[24px] bg-white p-6 shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300 ${props.className || ''}`}>

            {/* Header */}
            <div className="flex justify-between items-start mb-4">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide ${statusStyle.bg} ${statusStyle.text}`}>
                    <StatusIcon size={12} strokeWidth={2.5} /> {statusStyle.label}
                </span>
                <button className="text-gray-400 hover:text-gray-900 transition-colors">
                    <MoreHorizontal size={20} />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 mb-6">
                <h3 className="text-[17px] font-semibold text-[#1D1D1F] leading-tight">{quote.project}</h3>
                <p className="text-[13px] text-[#86868B] font-medium mt-1">{quote.client}</p>

                <div className="mt-4 flex items-baseline gap-2">
                    <span className="text-2xl font-semibold text-[#1D1D1F] tracking-tight">
                        ${quote.amount.toLocaleString()} <span className="text-sm font-medium text-[#86868B]">{quote.currency}</span>
                    </span>
                </div>

                <div className="flex items-center gap-2 mt-1">
                    <div className={`h-2 w-2 rounded-full ${getMarginColor(quote.margin).replace('text', 'bg')}`} />
                    <span className={`text-xs font-medium ${getMarginColor(quote.margin)}`}>
                        {quote.margin.toFixed(2)}% Margen
                    </span>
                    <span className="text-xs text-gray-300 mx-1">•</span>
                    <span className="text-[11px] font-medium text-[#86868B] bg-gray-100 px-2 py-0.5 rounded-full">
                        V{quote.version}
                    </span>
                </div>
            </div>

            {/* Metrics / Footer */}
            <div className="mt-auto pt-4 border-t border-gray-50 flex items-center justify-between">
                <div className="flex gap-3 text-xs font-medium text-[#86868B]">
                    {quote.viewedCount > 0 && (
                        <span className="flex items-center gap-1 text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded-full">
                            <Eye size={12} /> {quote.viewedCount}
                        </span>
                    )}
                    {quote.sentAt && (
                        <span className="flex items-center gap-1">
                            <Clock size={12} /> {quote.sentAt}
                        </span>
                    )}
                </div>


                {/* Logical Next Step Action */}
                <div className="flex gap-2">
                    {quote.status === 'draft' && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                router.push(`/dashboard/quotes/${quote.id}/send`);
                            }}
                            className="text-[11px] font-semibold bg-black text-white px-3 py-1.5 rounded-full hover:bg-gray-800 transition-colors flex items-center gap-1"
                        >
                            <Send size={11} /> Enviar
                        </button>
                    )}
                    {quote.status === 'sent' && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                router.push(`/dashboard/quotes/${quote.id}/send`);
                            }}
                            className="text-[11px] font-semibold bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full hover:bg-gray-200 transition-colors flex items-center gap-1"
                        >
                            Reenviar
                        </button>
                    )}
                    {quote.status === 'viewed' && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onStatusChange?.(quote.id, 'accepted');
                            }}
                            className="text-[11px] font-semibold bg-[#34C759] text-white px-3 py-1.5 rounded-full hover:bg-green-600 transition-colors flex items-center gap-1 shadow-sm shadow-green-200"
                        >
                            <CheckCircle2 size={11} /> Aceptar
                        </button>
                    )}
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/dashboard/quotes/${quote.id}/tracking`);
                        }}
                        className="p-1.5 hover:bg-gray-100 rounded-full text-gray-500 transition-colors"
                        title="Ver Detalle"
                    >
                        <ArrowUpRight size={16} />
                    </button>
                </div>
            </div>

            {/* Contextual Alert for High Attention */}
            {quote.viewedCount > 4 && quote.status !== 'accepted' && (
                <div className="absolute -top-2 -right-2 bg-[#FF3B30] text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-lg animate-bounce">
                    🔥 Hot Lead
                </div>
            )}
        </div>
    );
}
