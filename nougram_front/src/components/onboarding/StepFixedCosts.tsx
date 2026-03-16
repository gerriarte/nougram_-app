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

const isAmortizableCategory = (category: FixedCostTemplate['category']): boolean => category === 'Tools';

const monthlyImpact = (item: FixedCostTemplate): number => {
    const quantity = Math.max(1, item.quantity || 1);
    const isAmortizable = Boolean(item.amortizable || isAmortizableCategory(item.category));
    if (!isAmortizable) {
        const amount = Math.max(0, item.amount || 0);
        const monthlyAmount = item.paymentType === 'annual' ? amount / 12 : amount;
        return monthlyAmount * quantity;
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
            const isAmortizable = Boolean(item.amortizable || isAmortizableCategory(item.category));
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
                paymentType: isAmortizable ? undefined : (item.paymentType || 'monthly'),
            };
        })
    );
    const [searchTerm, setSearchTerm] = useState('');
    const [customName, setCustomName] = useState('');
    const [customCategory, setCustomCategory] = useState<FixedCostTemplate['category']>('Overhead');

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
        const isAmortizable = Boolean(template.amortizable || isAmortizableCategory(template.category));
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
            paymentType: isAmortizable ? undefined : (template.paymentType || 'monthly'),
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

    const updateCustomCategory = (id: string, category: FixedCostTemplate['category']) => {
        setSelectedCosts((prev) => prev.map((item) => {
            if (item.id !== id || !item.isCustom) return item;
            const becomesAmortizable = isAmortizableCategory(category);
            return {
                ...item,
                category,
                amortizable: becomesAmortizable,
                costType: becomesAmortizable ? 'amortization' : 'operational',
                purchasePrice: becomesAmortizable ? Math.max(0, item.purchasePrice ?? item.amount ?? 0) : undefined,
                usefulLifeMonths: becomesAmortizable ? Math.max(1, item.usefulLifeMonths || getDefaultUsefulLife({ ...item, category })) : undefined,
                salvageValue: becomesAmortizable ? Math.max(0, item.salvageValue || 0) : undefined,
                depreciationMethod: becomesAmortizable ? (item.depreciationMethod || 'straight_line') : undefined,
                paymentType: becomesAmortizable ? undefined : (item.paymentType || 'monthly'),
            };
        }));
        setAvailableTemplates((prev) => prev.map((item) => {
            if (item.id !== id || !item.isCustom) return item;
            const becomesAmortizable = isAmortizableCategory(category);
            return {
                ...item,
                category,
                amortizable: becomesAmortizable,
                costType: becomesAmortizable ? 'amortization' : 'operational',
                paymentType: becomesAmortizable ? undefined : (item.paymentType || 'monthly'),
            };
        }));
    };

    const addCustomItem = () => {
        const trimmedName = customName.trim();
        if (!trimmedName) return;
        const id = `custom-${Date.now()}`;
        const amortizable = isAmortizableCategory(customCategory);
        const customTemplate: FixedCostTemplate = {
            id,
            name: trimmedName,
            amount: 0,
            currency: primaryCurrency,
            quantity: 1,
            category: customCategory,
            amortizable,
            costType: amortizable ? 'amortization' : 'operational',
            purchasePrice: amortizable ? 0 : undefined,
            usefulLifeMonths: amortizable ? getDefaultUsefulLife({ category: customCategory } as FixedCostTemplate) : undefined,
            salvageValue: amortizable ? 0 : undefined,
            depreciationMethod: amortizable ? 'straight_line' : undefined,
            paymentType: amortizable ? undefined : 'monthly',
            icon: '🧩',
            isCustom: true,
        };
        setAvailableTemplates((prev) => [customTemplate, ...prev]);
        setSelectedCosts((prev) => [customTemplate, ...prev]);
        setCustomName('');
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

            <Card className="border-dashed border-gray-300">
                <CardContent className="pt-4">
                    <p className="text-sm font-medium text-gray-700 mb-3">Agregar elemento personalizado</p>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                        <div className="md:col-span-2">
                            <label className="text-xs text-gray-500">Nombre del ítem</label>
                            <Input
                                placeholder="Ej: Mantenimiento de servidores"
                                value={customName}
                                onChange={(e) => setCustomName(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="text-xs text-gray-500">Categoría</label>
                            <select
                                value={customCategory}
                                onChange={(e) => setCustomCategory(e.target.value as FixedCostTemplate['category'])}
                                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm"
                            >
                                {CATEGORY_ORDER.map((category) => (
                                    <option key={category} value={category}>
                                        {CATEGORY_LABELS[category]}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <Button type="button" onClick={addCustomItem}>
                            Agregar ítem
                        </Button>
                    </div>
                </CardContent>
            </Card>

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
                                        {group.category === 'Tools' ? (
                                            <>
                                                <th className="py-2 pr-2">Vida util (meses)</th>
                                                <th className="py-2">Salvamento</th>
                                            </>
                                        ) : (
                                            <th className="py-2" colSpan={2}>Tipo de pago</th>
                                        )}
                                    </tr>
                                </thead>
                                <tbody>
                                    {group.templates.map((template) => {
                                        const selected = selectedCosts.find((item) => item.id === template.id);
                                        const isSelected = Boolean(selected);
                                        const isAmortizable = Boolean((selected?.amortizable ?? template.amortizable) || isAmortizableCategory(template.category));
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
                                                        {isAmortizable ? 'Amortizable' : 'Operativo'}
                                                    </span>
                                                    {selected?.isCustom && isSelected && (
                                                        <div className="mt-2">
                                                            <select
                                                                value={selected.category}
                                                                onChange={(e) => updateCustomCategory(selected.id, e.target.value as FixedCostTemplate['category'])}
                                                                className="h-9 rounded-md border border-gray-300 bg-white px-2 text-xs"
                                                            >
                                                                {CATEGORY_ORDER.map((category) => (
                                                                    <option key={category} value={category}>
                                                                        {CATEGORY_LABELS[category]}
                                                                    </option>
                                                                ))}
                                                            </select>
                                                        </div>
                                                    )}
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
                                                {group.category === 'Tools' ? (
                                                    <>
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
                                                    </>
                                                ) : (
                                                    <td className="py-2 align-top min-w-[180px]" colSpan={2}>
                                                        <select
                                                            disabled={!isSelected}
                                                            value={selected?.paymentType || 'monthly'}
                                                            onChange={(e) => updateSelectedCost(template.id, { paymentType: e.target.value as 'monthly' | 'annual' })}
                                                            className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm disabled:bg-gray-100"
                                                        >
                                                            <option value="monthly">Mensual</option>
                                                            <option value="annual">Anual</option>
                                                        </select>
                                                    </td>
                                                )}
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
