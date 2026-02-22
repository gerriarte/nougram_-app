import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Button } from "@/components/ui/Button";
import { GlobalConfig } from "@/types/admin";
import { Globe, Clock, Percent, AlertCircle } from "lucide-react";

interface GlobalConfigFormProps {
    config: GlobalConfig;
    onChange: (config: GlobalConfig) => void;
}

export function GlobalConfigForm({ config, onChange }: GlobalConfigFormProps) {

    const handleChange = (field: keyof GlobalConfig, value: any) => {
        onChange({ ...config, [field]: value });
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Globe className="h-5 w-5 text-gray-500" />
                        <CardTitle>Configuración Regional</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4 max-w-md">
                        <div className="space-y-2">
                            <Label>Moneda Primaria</Label>
                            <select
                                className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={config.primary_currency}
                                onChange={e => handleChange("primary_currency", e.target.value)}
                            >
                                <option value="COP">Peso Colombiano (COP)</option>
                                <option value="USD">Dólar Estadounidense (USD)</option>
                                <option value="EUR">Euro (EUR)</option>
                            </select>
                            <p className="text-xs text-gray-500">
                                Esta es la moneda base para todos los cálculos del BCR. Los costos en otras monedas se convertirán automáticamente.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-gray-500" />
                        <CardTitle>Horas Base por Defecto</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <Label>Horas Facturables / Semana</Label>
                            <Input
                                type="number"
                                min="0" max="80"
                                value={config.default_billable_hours_per_week}
                                onChange={e => handleChange("default_billable_hours_per_week", parseFloat(e.target.value))}
                            />
                            <p className="text-xs text-gray-500">
                                Valor sugerido al agregar nuevos equipos. Estándar: 32 a 40 horas.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label>% No Facturable</Label>
                            <Input
                                type="number"
                                step="0.01" min="0" max="1"
                                value={config.default_non_billable_percentage}
                                onChange={e => handleChange("default_non_billable_percentage", e.target.value)}
                            />
                            <p className="text-xs text-gray-500">
                                1.0 = 100%. Ejemplo: 0.20 reserva el 20% del tiempo para tareas internas.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Percent className="h-5 w-5 text-gray-500" />
                        <CardTitle>Márgenes</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2 max-w-md">
                        <Label>Margen Objetivo por Defecto</Label>
                        <Input
                            type="number"
                            step="0.01" min="0" max="1"
                            value={config.default_margin_target}
                            onChange={e => handleChange("default_margin_target", e.target.value)}
                        />
                        <p className="text-xs text-gray-500">
                            Margen neto deseado para nuevos proyectos.
                        </p>
                    </div>
                </CardContent>
            </Card>

            <div className="flex items-center gap-2 p-4 bg-blue-50 text-blue-800 rounded-lg text-sm border border-blue-100">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <p>
                    Los cambios en la configuración global afectan los valores por defecto para nuevos registros, pero no modifican los registros existentes automáticamente.
                </p>
            </div>
        </div>
    );
}
