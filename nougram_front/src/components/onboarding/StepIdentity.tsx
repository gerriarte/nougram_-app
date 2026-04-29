
import React, { useState } from 'react';
import { OnboardingStickyActions } from '@/components/onboarding/OnboardingStickyActions';
import { OnboardingStepHero } from '@/components/onboarding/OnboardingStepHero';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { SUPPORTED_COUNTRIES, SUPPORTED_CURRENCIES, normalizeCountryCode, normalizeCurrencyCode } from '@/lib/onboarding-geo';
import type { OnboardingData } from '@/types/onboarding';

type IdentityData = OnboardingData['identity'] & {
    currency?: string;
};

interface StepIdentityProps {
    onNext: (data: OnboardingData['identity']) => void;
    initialData?: IdentityData;
}

export function StepIdentity({ onNext, initialData }: StepIdentityProps) {
    const [organizationName, setOrganizationName] = useState(initialData?.organizationName || '');
    const [currency, setCurrency] = useState(
        normalizeCurrencyCode(initialData?.primaryCurrency || initialData?.currency) || ''
    );
    const [country, setCountry] = useState(
        normalizeCountryCode(initialData?.country) || ''
    );
    const [errors, setErrors] = useState<Partial<Record<'organizationName' | 'currency' | 'country', string>>>({});

    const validate = () => {
        const newErrors: Partial<Record<'organizationName' | 'currency' | 'country', string>> = {};
        if (!organizationName.trim()) newErrors.organizationName = 'El nombre de la organización es requerido';
        if (!currency) newErrors.currency = 'La moneda es requerida';
        if (!country) newErrors.country = 'El país es requerido';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validate()) {
            onNext({ organizationName, primaryCurrency: currency, country });
        }
    };

    return (
        <div className="space-y-6 max-w-2xl mx-auto pb-24 md:pb-6">
            <OnboardingStepHero
                eyebrow="Paso 1 de 4"
                title="Empecemos con la identidad de tu operación"
                description="Estos datos definen la moneda base, el país y el nombre que Nougram usará para calcular costos y preparar tus cotizaciones."
                callout="Tus datos financieros se usan solo para modelar márgenes, costos reales y recomendaciones dentro de tu workspace."
            />

            <Card className="overflow-hidden border-gray-200 shadow-sm">
                <div className="border-b border-gray-100 bg-gradient-to-r from-primary-soft to-white px-6 py-4">
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Datos base</p>
                    <p className="mt-1 text-sm text-gray-600">Completa los campos obligatorios para continuar.</p>
                </div>
                <CardContent className="space-y-4 pt-6">
                    <div className="space-y-2">
                        <Label htmlFor="orgName">Nombre de tu organización *</Label>
                        <Input
                            id="orgName"
                            placeholder="Ej: Mi Agencia Creativa"
                            value={organizationName}
                            onChange={(e) => setOrganizationName(e.target.value)}
                            className={errors.organizationName ? 'border-red-500' : ''}
                        />
                        {errors.organizationName && <p className="text-red-500 text-sm">{errors.organizationName}</p>}
                        <p className="text-xs text-gray-500">ℹ️ Este nombre aparecerá en tus cotizaciones.</p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="currency">Moneda Primaria *</Label>
                        <select
                            id="currency"
                            className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${errors.currency ? 'border-red-500' : ''}`}
                            value={currency}
                            onChange={(e) => setCurrency(e.target.value)}
                        >
                            <option value="">Seleccionar moneda...</option>
                            {SUPPORTED_CURRENCIES.map((item) => (
                                <option key={item.code} value={item.code}>
                                    {item.label}
                                </option>
                            ))}
                        </select>
                        {errors.currency && <p className="text-red-500 text-sm">{errors.currency}</p>}
                        <p className="text-xs text-gray-500">ℹ️ Todos los cálculos se harán en esta moneda.</p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="country">País</Label>
                        <select
                            id="country"
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            value={country}
                            onChange={(e) => setCountry(e.target.value)}
                        >
                            <option value="">Seleccionar país...</option>
                            {SUPPORTED_COUNTRIES.map((item) => (
                                <option key={item.code} value={item.code}>
                                    {item.label}
                                </option>
                            ))}
                        </select>
                        {errors.country && <p className="text-red-500 text-sm">{errors.country}</p>}
                        <p className="text-xs text-gray-500">ℹ️ Esto nos ayuda a sugerirte impuestos y cargas sociales correctas.</p>
                    </div>
                </CardContent>
            </Card>

            <OnboardingStickyActions>
                <div className="flex justify-stretch md:justify-end">
                    <Button onClick={handleNext} className="w-full h-12 rounded-2xl text-base font-bold md:w-auto md:h-10">
                        Siguiente →
                    </Button>
                </div>
            </OnboardingStickyActions>
        </div>
    );
}
