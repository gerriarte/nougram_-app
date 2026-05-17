
import React, { useState } from 'react';
import { OnboardingStickyActions } from '@/components/onboarding/OnboardingStickyActions';
import { OnboardingStepHero } from '@/components/onboarding/OnboardingStepHero';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { SUPPORTED_COUNTRIES, SUPPORTED_CURRENCIES, normalizeCountryCode, normalizeCurrencyCode } from '@/lib/onboarding-geo';
import type { OnboardingData } from '@/types/onboarding';
import { cn } from '@/lib/utils';

type IdentityData = OnboardingData['identity'] & {
    currency?: string;
};

interface StepIdentityProps {
    onNext: (data: OnboardingData['identity']) => void;
    initialData?: IdentityData;
}

const INDUSTRIES = [
    'Agencia de diseño / branding',
    'Desarrollo de software',
    'Estudio creativo / producción',
    'Consultoría',
    'Marketing digital',
    'Agencia de publicidad',
    'Arquitectura / interiorismo',
    'Otro',
];

const COMPANY_TYPES: Array<{ id: NonNullable<OnboardingData['identity']['companyType']>; label: string; desc: string }> = [
    { id: 'agency', label: 'Agencia', desc: 'Equipo establecido, varios clientes' },
    { id: 'studio', label: 'Estudio', desc: 'Pequeño grupo creativo o técnico' },
    { id: 'freelance', label: 'Freelance', desc: 'Trabajas independiente' },
    { id: 'consult', label: 'Consultoría', desc: 'Servicios especializados por proyecto' },
];

export function StepIdentity({ onNext, initialData }: StepIdentityProps) {
    const [organizationName, setOrganizationName] = useState(initialData?.organizationName || '');
    const [taxId, setTaxId] = useState(initialData?.taxId || '');
    const [industry, setIndustry] = useState(initialData?.industry || '');
    const [companyType, setCompanyType] = useState<OnboardingData['identity']['companyType']>(initialData?.companyType || '');
    const [logo, setLogo] = useState<OnboardingData['identity']['logo']>(initialData?.logo || null);
    const [currency, setCurrency] = useState(
        normalizeCurrencyCode(initialData?.primaryCurrency || initialData?.currency) || ''
    );
    const [country, setCountry] = useState(
        normalizeCountryCode(initialData?.country) || ''
    );
    const [errors, setErrors] = useState<Partial<Record<'organizationName' | 'currency' | 'country' | 'industry' | 'companyType', string>>>({});

    const validate = () => {
        const newErrors: Partial<Record<'organizationName' | 'currency' | 'country' | 'industry' | 'companyType', string>> = {};
        if (!organizationName.trim()) newErrors.organizationName = 'El nombre de la organización es requerido';
        if (!currency) newErrors.currency = 'La moneda es requerida';
        if (!country) newErrors.country = 'El país es requerido';
        if (!industry) newErrors.industry = 'El sector es requerido';
        if (!companyType) newErrors.companyType = 'El tipo de empresa es requerido';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validate()) {
            onNext({ organizationName, primaryCurrency: currency, country, taxId, industry, companyType, logo });
        }
    };
    const handleLogo = (file?: File | null) => {
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            if (typeof reader.result === 'string') {
                setLogo({ src: reader.result, name: file.name });
            }
        };
        reader.readAsDataURL(file);
    };

    return (
        <div className="space-y-6 max-w-3xl mx-auto pb-24 md:pb-6">
            <OnboardingStepHero
                eyebrow="Paso 1 de 4"
                title="Cuéntanos sobre tu empresa"
                description="Esto nos ayuda a personalizar Nougram con datos relevantes para tu sector, país y forma de operar."
                callout="Tus datos financieros se usan solo para modelar márgenes, costos reales y recomendaciones dentro de tu workspace."
            />

            <Card className="overflow-hidden border-gray-200 shadow-sm">
                <div className="border-b border-gray-100 bg-gradient-to-r from-primary-soft to-white px-6 py-4">
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Identidad comercial</p>
                    <p className="mt-1 text-sm text-gray-600">Completa los datos que se usarán en cotizaciones y cálculos.</p>
                </div>
                <CardContent className="space-y-6 pt-6">
                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-[104px_1fr]">
                        <div>
                            <Label>Logo</Label>
                            <label className="mt-2 grid h-[92px] w-[92px] cursor-pointer place-items-center overflow-hidden rounded-2xl border-2 border-dashed border-gray-200 bg-surface-2 hover:border-primary/40">
                                {logo?.src ? (
                                    // eslint-disable-next-line @next/next/no-img-element -- local data URL preview
                                    <img src={logo.src} alt="Logo" className="h-full w-full object-contain p-2" />
                                ) : (
                                    <div className="text-center text-xs font-semibold text-gray-400">
                                        Subir
                                    </div>
                                )}
                                <input type="file" accept="image/*" className="hidden" onChange={(event) => handleLogo(event.target.files?.[0])} />
                            </label>
                            <p className="mt-1 max-w-[92px] text-center text-[10.5px] text-gray-400">PNG/SVG · Opcional</p>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="orgName">Nombre de la empresa *</Label>
                                <Input
                                    id="orgName"
                                    placeholder="Ej: Acme Studio"
                                    value={organizationName}
                                    onChange={(e) => setOrganizationName(e.target.value)}
                                    className={errors.organizationName ? 'border-red-500' : ''}
                                />
                                {errors.organizationName && <p className="text-red-500 text-sm">{errors.organizationName}</p>}
                                <p className="text-xs text-gray-500">Como se mostrará en cotizaciones y en tu cuenta.</p>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="taxId">NIT / Identificación fiscal <span className="font-normal text-gray-400">· Opcional</span></Label>
                                <Input
                                    id="taxId"
                                    placeholder="Ej: 901.234.567-8"
                                    value={taxId}
                                    onChange={(e) => setTaxId(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Tipo de empresa *</Label>
                        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                            {COMPANY_TYPES.map((type) => (
                                <button
                                    key={type.id}
                                    type="button"
                                    onClick={() => setCompanyType(type.id)}
                                    className={cn(
                                        'rounded-xl border p-4 text-left transition-colors',
                                        companyType === type.id
                                            ? 'border-primary bg-primary-soft text-primary'
                                            : 'border-gray-200 bg-white text-gray-700 hover:bg-surface-2'
                                    )}
                                >
                                    <div className="text-sm font-black">{type.label}</div>
                                    <div className="mt-1 text-xs text-gray-500">{type.desc}</div>
                                </button>
                            ))}
                        </div>
                        {errors.companyType && <p className="text-red-500 text-sm">{errors.companyType}</p>}
                    </div>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                        <div className="space-y-2">
                            <Label htmlFor="industry">Sector *</Label>
                            <select
                                id="industry"
                                className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ${errors.industry ? 'border-red-500' : ''}`}
                                value={industry}
                                onChange={(e) => setIndustry(e.target.value)}
                            >
                                <option value="">Seleccionar sector...</option>
                                {INDUSTRIES.map((item) => (
                                    <option key={item} value={item}>{item}</option>
                                ))}
                            </select>
                            {errors.industry && <p className="text-red-500 text-sm">{errors.industry}</p>}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="country">País *</Label>
                            <select
                                id="country"
                                className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ${errors.country ? 'border-red-500' : ''}`}
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
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="currency">Moneda primaria *</Label>
                            <select
                                id="currency"
                                className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ${errors.currency ? 'border-red-500' : ''}`}
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
                        </div>
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
