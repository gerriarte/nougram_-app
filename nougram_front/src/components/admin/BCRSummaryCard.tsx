import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { BCRSummary } from "@/types/admin";
import { formatCurrency } from "@/lib/utils";
import { AlertCircle, ChevronDown, ChevronUp } from "lucide-react";

interface BCRSummaryCardProps {
    summary: BCRSummary | null;
    isLoading?: boolean;
}

export function BCRSummaryCard({ summary, isLoading }: BCRSummaryCardProps) {
    const [isExpanded, setIsExpanded] = React.useState(false);

    if (isLoading) {
        return (
            <Card className="animate-pulse">
                <CardHeader>
                    <div className="h-6 w-32 bg-gray-200 rounded"></div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="h-10 w-48 bg-gray-200 rounded"></div>
                    <div className="h-4 w-full bg-gray-200 rounded"></div>
                    <div className="h-4 w-3/4 bg-gray-200 rounded"></div>
                </CardContent>
            </Card>
        );
    }

    if (!summary || summary.active_team_members === 0) {
        return (
            <Card className="bg-amber-50 border-amber-200">
                <CardContent className="p-6">
                    <div className="flex items-center gap-2 text-amber-800 mb-2">
                        <AlertCircle className="h-5 w-5" />
                        <h3 className="font-semibold">Sin Cálculo de BCR</h3>
                    </div>
                    <p className="text-sm text-amber-700 mb-4">
                        Configura al menos un miembro del equipo para calcular el Costo Hora Real.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="sticky top-6 shadow-lg border-blue-100 bg-white overflow-hidden">
            <div className="bg-blue-50/50 p-6 border-b border-blue-100">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">
                    Costo Hora Real (BCR)
                </h3>
                <div className="text-3xl font-bold text-blue-600">
                    {formatCurrency(summary.blended_cost_rate)}
                    <span className="text-sm font-medium text-gray-500 ml-1">/{summary.primary_currency.toLowerCase()}</span>
                </div>
            </div>

            <CardContent className="p-0">
                <div className="px-6 py-4 space-y-3">
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Total Mensual</span>
                        <span className="font-medium">{formatCurrency(summary.total_monthly_costs)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Horas Facturables</span>
                        <span className="font-medium">{summary.total_monthly_hours.toFixed(1)} hrs</span>
                    </div>
                </div>

                {isExpanded && (
                    <div className="px-6 pb-4 pt-0 space-y-3 border-t border-gray-100 bg-gray-50/30 animate-in slide-in-from-top-2">
                        <div className="pt-3 text-xs font-semibold text-gray-400 uppercase">Desglose Mensual</div>

                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Salarios (con cargas)</span>
                            <span className="font-medium">{formatCurrency(summary.total_salaries)}</span>
                        </div>

                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Overhead Fijo</span>
                            <span className="font-medium">{formatCurrency(summary.total_fixed_overhead)}</span>
                        </div>

                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Herramientas / SaaS</span>
                            <span className="font-medium">{formatCurrency(summary.total_tools_costs)}</span>
                        </div>

                        <div className="pt-2 border-t border-dashed border-gray-200 flex justify-between text-sm text-gray-500">
                            <span>Miembros Activos</span>
                            <span>{summary.active_team_members}</span>
                        </div>
                    </div>
                )}

                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full py-3 px-6 text-xs font-medium text-gray-500 hover:text-blue-600 hover:bg-gray-50 transition-colors flex items-center justify-center gap-1 border-t border-gray-100"
                >
                    {isExpanded ? (
                        <>Ocultar Detalles <ChevronUp className="h-3 w-3" /></>
                    ) : (
                        <>Ver Detalles Completos <ChevronDown className="h-3 w-3" /></>
                    )}
                </button>
            </CardContent>
        </Card>
    );
}
