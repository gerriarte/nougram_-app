'use client';

import React, { useState } from 'react';
import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { formatCurrency } from '@/lib/utils';
import type { QuoteAgentEstimate } from '@/lib/quote-agent';

export function QuoteEstimatePanel({
  estimate,
  currency,
  confirming,
  onConfirm,
}: {
  estimate: QuoteAgentEstimate | null;
  currency: string;
  confirming: boolean;
  onConfirm: (clientName: string) => void;
}) {
  const [clientName, setClientName] = useState('');

  const marginPct = estimate ? Math.round(estimate.margin_percentage * 100) : 0;
  const belowMinimum = Boolean(estimate?.below_minimum_margin);

  return (
    <div className="flex flex-col h-full rounded-2xl border border-gray-200 bg-white overflow-hidden">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-[14px] font-bold text-gray-900">Estimación en vivo</h2>
        <p className="text-[12px] text-gray-500">
          Precios calculados por el motor determinista de Nougram.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!estimate || estimate.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 gap-2 py-16">
            <Sparkles size={28} />
            <p className="text-[13px] max-w-[240px]">
              Conversá con el agente para generar una estimación de servicios y horas.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-[12px]">
                <thead>
                  <tr className="text-left text-gray-400 uppercase tracking-wider text-[10px]">
                    <th className="pb-2 font-bold">Servicio</th>
                    <th className="pb-2 font-bold text-right">Horas/Cant.</th>
                    <th className="pb-2 font-bold text-right">Precio</th>
                    <th className="pb-2 font-bold text-right">Margen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {estimate.items.map((item) => (
                    <tr key={item.service_id}>
                      <td className="py-2 font-medium text-gray-800">
                        {item.service_name || `Servicio ${item.service_id}`}
                      </td>
                      <td className="py-2 text-right text-gray-600">
                        {item.estimated_hours != null
                          ? `${item.estimated_hours}h`
                          : item.quantity != null
                            ? `×${item.quantity}`
                            : '—'}
                      </td>
                      <td className="py-2 text-right text-gray-800">
                        {formatCurrency(item.client_price, currency)}
                      </td>
                      <td className="py-2 text-right text-gray-500">
                        {Math.round(item.margin_percentage * 100)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="rounded-xl bg-gray-50 border border-gray-200 p-4 space-y-2">
              <div className="flex items-center justify-between text-[12px] text-gray-500">
                <span>Costo interno</span>
                <span>{formatCurrency(estimate.total_internal_cost, currency)}</span>
              </div>
              <div className="flex items-center justify-between text-[15px] font-bold text-gray-900">
                <span>Precio al cliente</span>
                <span>{formatCurrency(estimate.total_client_price, currency)}</span>
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-[12px] text-gray-500">Margen</span>
                <Badge variant={belowMinimum ? 'warning' : 'success'}>{marginPct}%</Badge>
              </div>
            </div>

            {belowMinimum && (
              <Alert variant="warning">
                <p>
                  El margen ({marginPct}%) está por debajo del mínimo recomendado. Podés crear el
                  borrador igual y ajustarlo en el builder.
                </p>
              </Alert>
            )}
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 p-4 space-y-3 bg-white">
        <input
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
          placeholder="Nombre del cliente"
          className="w-full rounded-xl border border-gray-200 px-3 py-2 text-[13px] focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <Button
          className="w-full"
          disabled={!estimate || estimate.items.length === 0 || !clientName.trim() || confirming}
          onClick={() => onConfirm(clientName.trim())}
        >
          {confirming ? 'Creando borrador…' : 'Crear borrador'}
        </Button>
      </div>
    </div>
  );
}
