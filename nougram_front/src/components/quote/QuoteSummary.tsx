import * as React from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { QuoteCalculationResponse } from "@/types/quote";
import { formatCurrency } from "@/lib/utils";
import { Alert } from "@/components/ui/Alert";

interface QuoteSummaryProps {
    calculation: QuoteCalculationResponse;
}

export function QuoteSummary({ calculation }: QuoteSummaryProps) {

    // Logic to determine badge color based on margin
    const margin = parseFloat(calculation.margin_percentage);
    let badgeVariant: "success" | "warning" | "critical" | "default" = "default";
    let marginLabel = "Neutro";

    if (margin >= 0.30) {
        badgeVariant = "success"; // Green
        marginLabel = "Saludable";
    } else if (margin >= 0.20) {
        badgeVariant = "warning"; // Amber
        marginLabel = "Bajo";
    } else {
        badgeVariant = "critical"; // Red
        marginLabel = "Crítico";
    }

    return (
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
                {/* Price Card */}
                <Card className="bg-blue-50 border-blue-100">
                    <CardContent className="p-6">
                        <h2 className="text-xl font-semibold text-blue-900 mb-2">Precio Final</h2>
                        <div className="text-4xl font-bold text-blue-600">
                            {formatCurrency(calculation.total_with_taxes)}
                        </div>
                        <p className="text-sm text-blue-700 mt-1 font-medium">
                            (con impuestos incluidos)
                        </p>
                    </CardContent>
                </Card>

                {/* Margin Card */}
                <Card>
                    <CardContent className="p-6">
                        <h2 className="text-lg font-semibold text-gray-700 mb-4">Margen Neto</h2>
                        <div className="flex items-center gap-4">
                            <span className="text-3xl font-bold text-gray-900">
                                {(margin * 100).toFixed(1)}%
                            </span>
                            <Badge variant={badgeVariant} className="text-sm px-3 py-1">
                                {marginLabel}
                            </Badge>
                        </div>
                        <p className="text-sm text-gray-500 mt-2">
                            Objetivo: {calculation.target_margin_percentage ? `${(parseFloat(calculation.target_margin_percentage) * 100).toFixed(0)}%` : "N/A"}
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Alerts Section (Mocked logic for UI) */}
            {margin < 0.20 && (
                <Alert variant="warning">
                    <strong>Margen Bajo:</strong> El margen está por debajo del recomendado (20%).
                </Alert>
            )}
        </div>
    );
}
