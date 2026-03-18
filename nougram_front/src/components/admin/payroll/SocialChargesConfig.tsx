
'use client';

import React from 'react';
import { useAdmin } from '@/context/AdminContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Button } from '@/components/ui/Button';
import { useNougram } from '@/context/NougramCoreContext';
import {
    buildSocialChargesConfigFromCountry,
    getSocialChargesPresetMeta,
    listSocialChargesPresetMeta,
} from '@/lib/social-charges-presets';

// Mock Switch if not available
function SimpleSwitch({ checked, onCheckedChange }: { checked: boolean; onCheckedChange: (c: boolean) => void }) {
    return (
        <button
            type="button"
            className={`w-11 h-6 bg-gray-200 rounded-full relative transition-colors ${checked ? 'bg-blue-600' : ''}`}
            onClick={() => onCheckedChange(!checked)}
        >
            <span className={`block w-5 h-5 bg-white rounded-full shadow transform transition-transform absolute top-0.5 left-0.5 ${checked ? 'translate-x-5' : ''}`} />
        </button>
    );
}

export function SocialChargesConfig() {
    const { socialCharges, updateSocialCharges } = useAdmin();
    const { state } = useNougram();
    const [isEditing, setIsEditing] = React.useState(false);
    const [formData, setFormData] = React.useState(socialCharges);
    const [countryCode, setCountryCode] = React.useState(socialCharges.country_code || 'CO');
    const currentCurrency = state.identity.primaryCurrency || 'COP';
    const presetMeta = getSocialChargesPresetMeta(currentCurrency);
    const availablePresets = listSocialChargesPresetMeta();

    const handleSave = () => {
        // Calculate total
        const total =
            formData.health_percentage +
            formData.pension_percentage +
            formData.arl_percentage +
            formData.parafiscales_percentage +
            formData.prima_services_percentage +
            formData.cesantias_percentage +
            formData.int_cesantias_percentage +
            formData.vacations_percentage;

        updateSocialCharges({
            ...formData,
            total_percentage: total,
            country_code: countryCode,
            preset_key: countryCode,
            version: (socialCharges.version || 0) + 1,
            updated_at: new Date().toISOString(),
        });
        setIsEditing(false);
    };

    const applyCountryPreset = () => {
        const preset = buildSocialChargesConfigFromCountry(
            countryCode,
            socialCharges.enable_social_charges
        );
        updateSocialCharges({
            ...preset,
            version: (socialCharges.version || 0) + 1,
            updated_at: new Date().toISOString(),
        });
        setFormData((prev) => ({
            ...prev,
            ...preset,
        }));
    };

    const handleChange = (key: keyof typeof formData, value: string) => {
        setFormData(prev => ({ ...prev, [key]: parseFloat(value) || 0 }));
    };

    // Reset form when entering edit mode
    React.useEffect(() => {
        if (isEditing) {
            setFormData(socialCharges);
            setCountryCode(socialCharges.country_code || presetMeta.countryCode);
        }
    }, [isEditing, socialCharges]);

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div>
                    <CardTitle>Cargas Sociales & Prestaciones</CardTitle>
                    <p className="text-sm text-gray-500">
                        Configuracion por pais (base: {presetMeta.countryLabel}, moneda {currentCurrency}). Desactivado por defecto para cuentas nuevas.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">Estado:</span>
                    <SimpleSwitch
                        checked={socialCharges.enable_social_charges}
                        onCheckedChange={(checked) => updateSocialCharges({ ...socialCharges, enable_social_charges: checked })}
                    />
                    <span className={`text-sm ${socialCharges.enable_social_charges ? 'text-green-600 font-bold' : 'text-gray-500'}`}>
                        {socialCharges.enable_social_charges ? 'ACTIVO' : 'INACTIVO'}
                    </span>
                </div>
            </CardHeader>
            <CardContent>
                <div className="mb-5 rounded-lg border border-gray-200 p-3 bg-gray-50/60">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                        <div className="space-y-1">
                            <Label>Pais de referencia</Label>
                            <select
                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-white"
                                value={countryCode}
                                onChange={(e) => setCountryCode(e.target.value)}
                            >
                                {availablePresets.map((preset) => (
                                    <option key={preset.countryCode} value={preset.countryCode}>
                                        {preset.countryLabel} ({preset.countryCode})
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="text-xs text-gray-500 md:col-span-2">
                            Se guardara en base de datos como configuracion editable de tu organizacion con versionado.
                        </div>
                    </div>
                    <div className="mt-3">
                        <Button type="button" variant="secondary" size="sm" onClick={applyCountryPreset}>
                            Aplicar preset del pais seleccionado
                        </Button>
                    </div>
                </div>

                {/* View Mode */}
                {!isEditing && (
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
                            <div><p className="text-xs text-gray-500">Salud</p><p className="font-medium">{socialCharges.health_percentage}%</p></div>
                            <div><p className="text-xs text-gray-500">Pensión</p><p className="font-medium">{socialCharges.pension_percentage}%</p></div>
                            <div><p className="text-xs text-gray-500">ARL</p><p className="font-medium">{socialCharges.arl_percentage}%</p></div>
                            <div><p className="text-xs text-gray-500">Parafiscales</p><p className="font-medium">{socialCharges.parafiscales_percentage}%</p></div>
                            <div><p className="text-xs text-gray-500">Prima</p><p className="font-medium">{socialCharges.prima_services_percentage}%</p></div>
                            <div><p className="text-xs text-gray-500">Cesantías</p><p className="font-medium">{socialCharges.cesantias_percentage}%</p></div>
                            <div><p className="text-xs text-gray-500">Int. Cesantías</p><p className="font-medium">{socialCharges.int_cesantias_percentage}%</p></div>
                            <div><p className="text-xs text-gray-500">Vacaciones</p><p className="font-medium">{socialCharges.vacations_percentage}%</p></div>
                        </div>
                        <div className="flex justify-between items-center pt-2 border-t">
                            <div>
                                <p className="text-lg font-bold text-gray-900">Total Carga: {socialCharges.total_percentage?.toFixed(3)}%</p>
                                <p className="text-xs text-gray-500">Multiplicador: {(1 + (socialCharges.total_percentage || 0) / 100).toFixed(5)}x</p>
                            </div>
                            <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)}>Editar Porcentajes</Button>
                        </div>
                    </div>
                )}

                {/* Edit Mode */}
                {isEditing && (
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(formData).map(([key, val]) => {
                                if (key === 'enable_social_charges' || key === 'total_percentage') return null;
                                return (
                                    <div key={key} className="space-y-1">
                                        <Label className="capitalize">{key.replace(/_/g, ' ').replace('percentage', '').trim()}</Label>
                                        <div className="relative">
                                            <Input
                                                type="number"
                                                step="0.01"
                                                value={val as number}
                                                onChange={e => handleChange(key as any, e.target.value)}
                                            />
                                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs">%</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        <div className="flex justify-end gap-2 pt-4">
                            <Button variant="ghost" onClick={() => setIsEditing(false)}>Cancelar</Button>
                            <Button onClick={handleSave}>Guardar Cambios</Button>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
