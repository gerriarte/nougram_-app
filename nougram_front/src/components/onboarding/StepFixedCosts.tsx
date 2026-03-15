import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { onboardingService } from '@/services/onboardingService';
import { FixedCostTemplate } from '@/types/onboarding';
import { formatCurrency } from '@/lib/utils';

interface StepFixedCostsProps {
    onNext: (data: { selectedTemplates: FixedCostTemplate[]; totalMonthly: number }) => void;
    onBack: () => void;
    initialData?: { selectedTemplates: FixedCostTemplate[] };
    primaryCurrency: string;
}

const INDUSTRIES = [
    { id: 'marketing', label: 'Agencia de Marketing', icon: '📢' },
    { id: 'dev', label: 'Desarrollo Web', icon: '💻' },
    { id: 'design', label: 'Diseno', icon: '🎨' },
    { id: 'consulting', label: 'Consultoria', icon: '🤝' },
];

const CATEGORY_ORDER: Array<FixedCostTemplate['category']> = ['Tools', 'Software', 'Overhead', 'Other'];
const CATEGORY_LABELS: Record<FixedCostTemplate['category'], string> = {
    Tools: 'Herramientas y Equipos',
    Software: 'Software y Licencias',
    Overhead: 'Gastos Operativos',
    Other: 'Otros',
};

const getDefaultUsefulLife = (item: FixedCostTemplate): number => (
    item.category === 'Software' ? 24 : 36
);

const priceFormatter = new Intl.NumberFormat('es-CO', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
});

const formatPriceInput = (value: number | null | undefined): string => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed <= 0) return '0';
    return priceFormatter.format(parsed);
};

const parsePriceInput = (raw: string): number => {
    const normalized = (raw || '')
        .trim()
        .replace(/\./g, '')
        .replace(',', '.')
        .replace(/[^\d.]/g, '');
    if (!normalized) return 0;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
};

const monthlyImpact = (item: FixedCostTemplate): number => {
    const quantity = Math.max(1, item.quantity || 1);
    const isAmortizable = Boolean(item.amortizable || item.category === 'Tools');
    if (!isAmortizable) {
        return Math.max(0, item.amount || 0) * quantity;
    }
    const purchasePrice = Math.max(0, item.purchasePrice ?? item.amount ?? 0);
    const usefulLife = Math.max(1, item.usefulLifeMonths || getDefaultUsefulLife(item));
    const salvage = Math.max(0, item.salvageValue || 0);
    return Math.max(0, (purchasePrice - salvage) / usefulLife) * quantity;
};

const asSafeTemplateArray = (value: unknown): FixedCostTemplate[] => {
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is FixedCostTemplate => (
        Boolean(item) && typeof item === 'object'
    ));
};

export function StepFixedCosts({ onNext, onBack, initialData, primaryCurrency }: StepFixedCostsProps) {
    const [availableTemplates, setAvailableTemplates] = useState<FixedCostTemplate[]>([]);
    const [exchangeRates, setExchangeRates] = useState<Record<string, { rate: number; lastUpdated: string }>>({});
    const [selectedCosts, setSelectedCosts] = useState<FixedCostTemplate[]>(() =>
        asSafeTemplateArray(initialData?.selectedTemplates).map((item) => {
            const isAmortizable = Boolean(item.amortizable || item.category === 'Tools');
            return {
                ...item,
                currency: primaryCurrency,
                amortizable: isAmortizable,
                costType: isAmortizable ? 'amortization' : 'operational',
                quantity: Math.max(1, item.quantity || 1),
                purchasePrice: isAmortizable ? Math.max(0, item.purchasePrice ?? item.amount ?? 0) : undefined,
                usefulLifeMonths: isAmortizable ? Math.max(1, item.usefulLifeMonths || getDefaultUsefulLife(item)) : undefined,
                salvageValue: isAmortizable ? Math.max(0, item.salvageValue || 0) : undefined,
                depreciationMethod: isAmortizable ? (item.depreciationMethod || 'straight_line') : undefined,
            };
        })
    );
    const [activeIndustry, setActiveIndustry] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        const loadOnboardingCatalog = async () => {
            const [templates, rates] = await Promise.all([
                onboardingService.getTemplates(),
                onboardingService.getExchangeRates(),
            ]);
            setAvailableTemplates(templates);
            setExchangeRates(rates);
        };
        void loadOnboardingCatalog();
    }, []);

    const normalizeTemplateToPrimary = (template: FixedCostTemplate): FixedCostTemplate => {
        const converted = onboardingService.convertCurrency(
            template.amount || 0,
            template.currency || primaryCurrency,
            primaryCurrency,
            exchangeRates
        );
        const isAmortizable = Boolean(template.amortizable || template.category === 'Tools');
        return {
            ...template,
            amount: Number(converted.toFixed(2)),
            currency: primaryCurrency,
            quantity: Math.max(1, template.quantity || 1),
            amortizable: isAmortizable,
            costType: isAmortizable ? 'amortization' : 'operational',
            purchasePrice: isAmortizable ? Number(converted.toFixed(2)) : undefined,
            usefulLifeMonths: isAmortizable ? getDefaultUsefulLife(template) : undefined,
            salvageValue: isAmortizable ? 0 : undefined,
            depreciationMethod: isAmortizable ? 'straight_line' : undefined,
            purchaseDate: template.purchaseDate,
        };
    };

    const toggleCost = (template: FixedCostTemplate) => {
        setSelectedCosts((prev) => {
            const exists = prev.some((item) => item.id === template.id);
            if (exists) return prev.filter((item) => item.id !== template.id);
            return [...prev, normalizeTemplateToPrimary(template)];
        });
    };

    const updateSelectedCost = (id: string, updates: Partial<FixedCostTemplate>) => {
        setSelectedCosts((prev) => prev.map((item) => (item.id === id ? { ...item, ...updates } : item)));
    };

    const handleIndustrySelect = (industryId: string) => {
        setActiveIndustry(industryId);
        const industryTemplates = availableTemplates.filter((t) => t.preSelectedFor?.includes(industryId));
        setSelectedCosts((prev) => {
            const next = [...prev];
            industryTemplates.forEach((template) => {
                if (!next.some((item) => item.id === template.id)) {
                    next.push(normalizeTemplateToPrimary(template));
                }
            });
            return next;
        });
    };

    const calculateTotal = () => selectedCosts.reduce((acc, item) => acc + monthlyImpact(item), 0);

    const filteredTemplates = useMemo(
        () => availableTemplates.filter((t) => t.name.toLowerCase().includes(searchTerm.toLowerCase())),
        [availableTemplates, searchTerm]
    );

    const groupedTemplates = useMemo(
        () => CATEGORY_ORDER
            .map((category) => ({ category, templates: filteredTemplates.filter((template) => template.category === category) }))
            .filter((group) => group.templates.length > 0),
        [filteredTemplates]
    );

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold text-gray-900">Define tu inventario operativo</h1>
                <p className="text-gray-600">Selecciona items y completa los datos. Los costos amortizables se configuran con datos de amortizacion, no con valor mensual.</p>
                <p className="text-xs text-blue-600">Todos los valores se muestran y editan en {primaryCurrency}.</p>
            </div>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div className="space-y-3 flex-1">
                    <p className="text-sm font-medium text-gray-700">Quick Select por industria</p>
                    <div className="flex flex-wrap gap-2">
                        {INDUSTRIES.map((industry) => (
                            <button
                                key={industry.id}
                                type="button"
                                onClick={() => handleIndustrySelect(industry.id)}
                                className={`px-4 py-2 rounded-full border text-sm font-medium transition-colors ${activeIndustry === industry.id ? 'bg-blue-100 border-blue-500 text-blue-700' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}`}
                            >
                                {industry.icon} {industry.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <Input
                placeholder="Buscar item..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-md"
            />

            {groupedTemplates.map((group) => (
                <Card key={group.category} className="border-gray-200">
                    <CardContent className="pt-4">
                        <div className="flex items-center justify-between mb-3">
                            <h3 className="text-sm font-semibold text-gray-800">{CATEGORY_LABELS[group.category]}</h3>
                            <span className="text-xs text-gray-500">{group.templates.length} items</span>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-left text-xs text-gray-500 border-b">
                                        <th className="py-2 pr-2">Elegir</th>
                                        <th className="py-2 pr-2">Tipo de costo</th>
                                        <th className="py-2 pr-2">Clase</th>
                                        <th className="py-2 pr-2">Precio ({primaryCurrency})</th>
                                        <th className="py-2 pr-2">Cantidad</th>
                                        <th className="py-2 pr-2">Vida util (meses)</th>
                                        <th className="py-2">Salvamento</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {group.templates.map((template) => {
                                        const selected = selectedCosts.find((item) => item.id === template.id);
                                        const isSelected = Boolean(selected);
                                        const isAmortizable = Boolean((selected?.amortizable ?? template.amortizable) || template.category === 'Tools');
                                        const defaultValue = onboardingService.convertCurrency(
                                            template.amount || 0,
                                            template.currency || primaryCurrency,
                                            primaryCurrency,
                                            exchangeRates
                                        );
                                        const currentPrice = isAmortizable
                                            ? (selected?.purchasePrice ?? Number(defaultValue.toFixed(2)))
                                            : (selected?.amount ?? Number(defaultValue.toFixed(2)));

                                        return (
                                            <tr key={template.id} className={`border-b last:border-b-0 ${isSelected ? 'bg-blue-50/40' : ''}`}>
                                                <td className="py-2 pr-2 align-top">
                                                    <input
                                                        type="checkbox"
                                                        checked={isSelected}
                                                        onChange={() => toggleCost(template)}
                                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                    />
                                                </td>
                                                <td className="py-2 pr-2 align-top">
                                                    <p className="font-medium text-gray-900">{template.icon} {template.name}</p>
                                                </td>
                                                <td className="py-2 pr-2 align-top">
                                                    <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ${isAmortizable ? 'bg-indigo-100 text-indigo-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                                        {isAmortizable ? 'Amortizable' : 'Operativo mensual'}
                                                    </span>
                                                </td>
                                                <td className="py-2 pr-2 align-top min-w-[140px]">
                                                    <Input
                                                        type="text"
                                                        inputMode="decimal"
                                                        disabled={!isSelected}
                                                        value={formatPriceInput(currentPrice)}
                                                        onChange={(e) => updateSelectedCost(template.id, isAmortizable
                                                            ? { purchasePrice: Math.max(0, parsePriceInput(e.target.value)), currency: primaryCurrency }
                                                            : { amount: Math.max(0, parsePriceInput(e.target.value)), currency: primaryCurrency })}
                                                    />
                                                </td>
                                                <td className="py-2 pr-2 align-top min-w-[100px]">
                                                    <Input
                                                        type="number"
                                                        min={1}
                                                        disabled={!isSelected}
                                                        value={selected?.quantity ?? 1}
                                                        onChange={(e) => updateSelectedCost(template.id, { quantity: Math.max(1, Number(e.target.value) || 1) })}
                                                    />
                                                </td>
                                                <td className="py-2 pr-2 align-top min-w-[120px]">
                                                    <Input
                                                        type="number"
                                                        min={1}
                                                        disabled={!isSelected || !isAmortizable}
                                                        value={selected?.usefulLifeMonths ?? getDefaultUsefulLife(template)}
                                                        onChange={(e) => updateSelectedCost(template.id, { usefulLifeMonths: Math.max(1, Number(e.target.value) || getDefaultUsefulLife(template)) })}
                                                    />
                                                </td>
                                                <td className="py-2 align-top min-w-[130px]">
                                                    <Input
                                                        type="number"
                                                        min={0}
                                                        disabled={!isSelected || !isAmortizable}
                                                        value={selected?.salvageValue ?? 0}
                                                        onChange={(e) => updateSelectedCost(template.id, { salvageValue: Math.max(0, Number(e.target.value) || 0) })}
                                                    />
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            ))}

            <Card className="bg-gray-50 sticky bottom-4 shadow-lg border-t border-gray-200">
                <CardContent className="flex flex-col sm:flex-row items-center justify-between p-4">
                    <div>
                        <p className="text-sm text-gray-500">Impacto mensual estimado (incluye amortizacion)</p>
                        <p className="text-2xl font-bold text-gray-900">{formatCurrency(calculateTotal(), primaryCurrency)}</p>
                        <p className="text-xs text-gray-400">{selectedCosts.length} items seleccionados</p>
                    </div>
                    <div className="flex gap-3 mt-4 sm:mt-0 w-full sm:w-auto">
                        <Button variant="secondary" onClick={onBack} className="flex-1 sm:flex-none">
                            ← Atras
                        </Button>
                        <Button onClick={() => onNext({ selectedTemplates: selectedCosts, totalMonthly: calculateTotal() })} className="flex-1 sm:flex-none">
                            Siguiente →
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
