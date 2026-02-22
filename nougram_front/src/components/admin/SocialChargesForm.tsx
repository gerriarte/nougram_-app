import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Button } from "@/components/ui/Button";
import { SocialChargesConfig } from "@/types/admin";
import { calculateSocialChargesMult } from "@/lib/admin-logic";
import { ChevronDown, ChevronUp } from "lucide-react";

interface SocialChargesFormProps {
    config: SocialChargesConfig;
    onChange: (config: SocialChargesConfig) => void;
}

export function SocialChargesForm({ config, onChange }: SocialChargesFormProps) {
    const [isOpen, setIsOpen] = React.useState(false);

    const handleChange = (field: keyof SocialChargesConfig, value: number) => {
        const newConfig = { ...config, [field]: value };
        onChange(newConfig);
    };

    const toggleEnable = () => {
        onChange({ ...config, enable_social_charges: !config.enable_social_charges });
    };

    const multiplier = calculateSocialChargesMult(config);
    const totalPercentage = (multiplier - 1) * 100;

    return (
        <Card className={`transition-all duration-300 ${!config.enable_social_charges ? "opacity-75" : ""}`}>
            <CardHeader className="flex flex-row items-center justify-between py-4 cursor-pointer hover:bg-gray-50 bg-gray-50/50" onClick={() => setIsOpen(!isOpen)}>
                <div className="flex flex-col">
                    <CardTitle className="text-base">Configuración de Cargas Sociales</CardTitle>
                    <span className="text-sm text-gray-500 font-normal">
                        {config.enable_social_charges ? `Activo (${totalPercentage.toFixed(3)}%)` : "Inactivo"}
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <Button
                        type="button"
                        variant={config.enable_social_charges ? "primary" : "secondary"}
                        size="sm"
                        onClick={(e) => { e.stopPropagation(); toggleEnable(); }}
                    >
                        {config.enable_social_charges ? "Habilitado" : "Deshabilitado"}
                    </Button>
                    {isOpen ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
                </div>
            </CardHeader>

            {isOpen && (
                <CardContent className="pt-6 animate-in slide-in-from-top-2">
                    {!config.enable_social_charges && (
                        <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-md text-sm text-amber-800">
                            ⚠️ Las cargas sociales están deshabilitadas. Los salarios se calcularán sin costos adicionales.
                        </div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div className="space-y-2">
                            <Label>Salud (Patrono)</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.01"
                                    value={config.health_percentage}
                                    onChange={e => handleChange("health_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Pensión (Patrono)</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.01"
                                    value={config.pension_percentage}
                                    onChange={e => handleChange("pension_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>ARL</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.001"
                                    value={config.arl_percentage}
                                    onChange={e => handleChange("arl_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Parafiscales</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.01"
                                    value={config.parafiscales_percentage}
                                    onChange={e => handleChange("parafiscales_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Prima Servicios</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.01"
                                    value={config.prima_services_percentage}
                                    onChange={e => handleChange("prima_services_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Cesantías</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.01"
                                    value={config.cesantias_percentage}
                                    onChange={e => handleChange("cesantias_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Int. Cesantías</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.01"
                                    value={config.int_cesantias_percentage}
                                    onChange={e => handleChange("int_cesantias_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Vacaciones</Label>
                            <div className="relative">
                                <Input
                                    type="number" step="0.01"
                                    value={config.vacations_percentage}
                                    onChange={e => handleChange("vacations_percentage", parseFloat(e.target.value))}
                                    disabled={!config.enable_social_charges}
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">%</span>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-100 flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-500">Total Factor Prestacional (Multiplicador)</span>
                        <div className="text-2xl font-bold text-gray-900">
                            x{multiplier.toFixed(5)}
                            <span className="text-sm font-normal text-gray-400 ml-2">({totalPercentage.toFixed(3)}%)</span>
                        </div>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
