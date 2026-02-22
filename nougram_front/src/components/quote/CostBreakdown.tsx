import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { QuoteCalculationResponse } from "@/types/quote";
import { formatCurrency } from "@/lib/utils";

interface CostBreakdownProps {
    calculation: QuoteCalculationResponse;
}

export function CostBreakdown({ calculation }: CostBreakdownProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Desglose de Costos</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {/* Main Totals */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="text-gray-600">Costo Interno Total</div>
                        <div className="text-right font-medium">{formatCurrency(calculation.total_internal_cost)}</div>

                        <div className="text-gray-600">Precio Base (Servicios)</div>
                        <div className="text-right font-medium">{formatCurrency(calculation.total_client_price)}</div>

                        <div className="text-gray-600">Gastos de Terceros</div>
                        <div className="text-right font-medium">{formatCurrency(calculation.total_expenses_client_price)}</div>
                    </div>

                    <div className="border-t border-gray-100 my-2"></div>

                    <div className="grid grid-cols-2 gap-4 text-base font-semibold">
                        <div>Subtotal</div>
                        <div className="text-right">{formatCurrency(parseFloat(calculation.total_client_price) + parseFloat(calculation.total_expenses_client_price))}</div>
                    </div>

                    <div className="border-t border-gray-100 my-2"></div>

                    {/* Taxes */}
                    <div className="space-y-2">
                        <h4 className="text-sm font-semibold text-gray-900 mb-2">Impuestos</h4>
                        {calculation.taxes.map((tax) => (
                            <div key={tax.id} className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                                <div>{tax.name} ({parseFloat(tax.percentage).toFixed(2)}%)</div>
                                <div className="text-right">{formatCurrency(tax.amount)}</div>
                            </div>
                        ))}
                        <div className="grid grid-cols-2 gap-4 text-sm font-medium text-gray-900 mt-2 pt-2 border-t border-dashed border-gray-200">
                            <div>Total Impuestos</div>
                            <div className="text-right">{formatCurrency(calculation.total_taxes)}</div>
                        </div>
                    </div>

                    <div className="border-t border-gray-200 my-4"></div>

                    <div className="grid grid-cols-2 gap-4 text-lg font-bold text-blue-600 bg-blue-50 p-3 rounded-lg">
                        <div>TOTAL CON IMPUESTOS</div>
                        <div className="text-right">{formatCurrency(calculation.total_with_taxes)}</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
