
import React from 'react';
import { Transaction } from '@/types/billing';
import { Button } from '@/components/ui/Button';
import { Download, ExternalLink, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

const MOCK_TRANSACTIONS: Transaction[] = [
    {
        id: '1',
        invoiceNumber: 'INV-2026-001',
        amount: 99.99,
        currency: 'USD',
        status: 'paid',
        date: '2026-01-15',
        planName: 'Professional',
        periodStart: '2026-01-15',
        periodEnd: '2026-02-15',
        pdfUrl: '#'
    },
    {
        id: '2',
        invoiceNumber: 'INV-2025-012',
        amount: 29.99,
        currency: 'USD',
        status: 'paid',
        date: '2025-12-15',
        planName: 'Starter',
        periodStart: '2025-12-15',
        periodEnd: '2026-01-15',
        pdfUrl: '#'
    }
];

interface TransactionHistoryProps {
    transactions?: Transaction[];
}

export function TransactionHistory({ transactions = MOCK_TRANSACTIONS }: TransactionHistoryProps) {

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'paid':
                return (
                    <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-[#E8F8F0] text-[#1D9D5D]">
                        Pagada
                    </span>
                );
            case 'pending':
                return (
                    <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-blue-50 text-[#0071E3]">
                        Pendiente
                    </span>
                );
            case 'failed':
                return (
                    <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-red-50 text-[#FF3B30]">
                        Fallida
                    </span>
                );
            default:
                return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-gray-100 text-gray-500">{status}</span>;
        }
    };

    return (
        <div className="bg-white rounded-[24px] shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 overflow-hidden">
            <div className="px-8 py-6 border-b border-gray-100 flex items-center justify-between">
                <h2 className="text-[19px] font-semibold text-[#1D1D1F]">Historial de Facturación</h2>
                <Button variant="ghost" className="text-[#0071E3] font-medium text-[13px]">Descargar todo</Button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-[#FAFAFA] border-b border-gray-100">
                        <tr>
                            <th className="px-8 py-4 text-[11px] font-bold text-[#86868B] uppercase tracking-wider">Factura</th>
                            <th className="px-6 py-4 text-[11px] font-bold text-[#86868B] uppercase tracking-wider">Fecha</th>
                            <th className="px-6 py-4 text-[11px] font-bold text-[#86868B] uppercase tracking-wider">Monto</th>
                            <th className="px-6 py-4 text-[11px] font-bold text-[#86868B] uppercase tracking-wider">Plan</th>
                            <th className="px-6 py-4 text-[11px] font-bold text-[#86868B] uppercase tracking-wider">Estado</th>
                            <th className="px-8 py-4 text-right text-[11px] font-bold text-[#86868B] uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {transactions.map((tx) => (
                            <tr key={tx.id} className="group hover:bg-[#F5F5F7] transition-colors duration-200">
                                <td className="px-8 py-5 font-semibold text-[#1D1D1F] text-[14px]">{tx.invoiceNumber}</td>
                                <td className="px-6 py-5 text-[#86868B] text-[13px]">{new Date(tx.date).toLocaleDateString()}</td>
                                <td className="px-6 py-5 font-semibold text-[#1D1D1F] text-[14px]">
                                    ${tx.amount.toFixed(2)} {tx.currency}
                                </td>
                                <td className="px-6 py-5 text-[#424245] text-[13px]">
                                    {tx.planName}
                                    <span className="block text-[11px] text-[#86868B] mt-0.5 font-normal">
                                        {new Date(tx.periodStart).toLocaleDateString()} - {new Date(tx.periodEnd).toLocaleDateString()}
                                    </span>
                                </td>
                                <td className="px-6 py-5">
                                    {getStatusBadge(tx.status)}
                                </td>
                                <td className="px-8 py-5 text-right">
                                    <div className="flex justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button className="text-[#86868B] hover:text-[#0071E3] transition-colors p-2 rounded-full hover:bg-white" title="Ver Detalles">
                                            <ExternalLink size={16} />
                                        </button>
                                        <button className="text-[#86868B] hover:text-[#0071E3] transition-colors p-2 rounded-full hover:bg-white" title="Descargar PDF">
                                            <Download size={16} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {transactions.length === 0 && (
                <div className="p-12 text-center text-[#86868B]">
                    No hay facturas disponibles.
                </div>
            )}
        </div>
    );
}
