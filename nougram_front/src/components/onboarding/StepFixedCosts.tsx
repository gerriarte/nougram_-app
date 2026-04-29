import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { OnboardingStepHero } from '@/components/onboarding/OnboardingStepHero';
import { onboardingService } from '@/services/onboardingService';
import { FixedCostTemplate } from '@/types/onboarding';
import { formatCurrency, formatLocalizedNumberInput, parseLocalizedNumberInput } from '@/lib/utils';

interface StepFixedCostsProps {
    onNext: (data: { selectedTemplates: FixedCostTemplate[]; totalMonthly: number }) => void;
    onBack: () => void;
    initialData?: { selectedTemplates: FixedCostTemplate[] };
    primaryCurrency: string;
    onOpenImport?: () => void;
}

const CATEGORY_ORDER: Array<FixedCostTemplate['category']> = ['Tools', 'Software', 'Overhead', 'Other'];
const CATEGORY_LABELS: Record<FixedCostTemplate['category'], string> = {
    Tools: 'Herramientas y Equipos',
    Software: 'Software y Licencias',
    Overhead: 'Gastos Operativos',
    Other: 'Otros',
};
const CATEGORY_META: Record<FixedCostTemplate['category'], { sub: string; desc: string; color: string; tint: string }> = {
    Tools: {
        sub: 'Compras grandes que se distribuyen',
        desc: 'Equipos, mobiliario o activos que se amortizan durante su vida útil.',
        color: '#7B3B99',
        tint: 'bg-purple-50 border-purple-100',
    },
    Software: {
        sub: 'Suscripciones de tu stack',
        desc: 'Licencias mensuales o anuales: Figma, Adobe, Notion, Slack y similares.',
        color: '#2E5A3E',
        tint: 'bg-emerald-50 border-emerald-100',
    },
    Overhead: {
        sub: 'Pagos recurrentes mensuales',
        desc: 'Costos que pagas todos los meses: oficina, internet, contabilidad o servicios.',
        color: '#D97757',
        tint: 'bg-orange-50 border-orange-100',
    },
    Other: {
        sub: 'Otros costos operativos',
        desc: 'Cualquier gasto que no encaje en las categorías anteriores.',
        color: '#475569',
        tint: 'bg-slate-50 border-slate-100',
    },
};

const getDefaultUsefulLife = (item: FixedCostTemplate): number => (
    item.category === 'Software' ? 24 : 36
);

const formatPriceInput = (value: number | null | undefined, currencyCode: string): string => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed <= 0) return '0';
    return formatLocalizedNumberInput(parsed, { currencyCode });
};

const parsePriceInput = (raw: string, currencyCode: string): number => {
    const isCopCurrency = String(currencyCode || '').toUpperCase() === 'COP';
    return parseLocalizedNumberInput(raw, { allowDecimal: !isCopCurrency });
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

export function StepFixedCosts({ onNext, onBack, initialData, primaryCurrency, onOpenImport }: StepFixedCostsProps) {
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
    const [openCategories, setOpenCategories] = useState<Record<FixedCostTemplate['category'], boolean>>({
        Tools: true,
        Software: true,
        Overhead: true,
        Other: true,
    });

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

    const addCustomItem = () => {
        const trimmedName = customName.trim();
        if (!trimmedName) return;
        addCategoryItem(customCategory, trimmedName);
        setCustomName('');
    };

    const addCategoryItem = (category: FixedCostTemplate['category'], name = '') => {
        const id = `custom-${Date.now()}`;
        const amortizable = isAmortizableCategory(category);
        const customTemplate: FixedCostTemplate = {
            id,
            name: name || '',
            amount: 0,
            currency: primaryCurrency,
            quantity: 1,
            category,
            amortizable,
            costType: amortizable ? 'amortization' : 'operational',
            purchasePrice: amortizable ? 0 : undefined,
            usefulLifeMonths: amortizable ? getDefaultUsefulLife({ category } as FixedCostTemplate) : undefined,
            salvageValue: amortizable ? 0 : undefined,
            depreciationMethod: amortizable ? 'straight_line' : undefined,
            paymentType: amortizable ? undefined : 'monthly',
            icon: '•',
            isCustom: true,
        };
        setAvailableTemplates((prev) => [customTemplate, ...prev]);
        setSelectedCosts((prev) => [customTemplate, ...prev]);
    };

    const calculateTotal = () => selectedCosts.reduce((acc, item) => acc + monthlyImpact(item), 0);
    const categoryTotal = (category: FixedCostTemplate['category']) => (
        selectedCosts
            .filter((item) => item.category === category)
            .reduce((sum, item) => sum + monthlyImpact(item), 0)
    );

    const filteredTemplateSuggestions = useMemo(
        () => availableTemplates
            .filter((template) => template.name.toLowerCase().includes(searchTerm.toLowerCase()))
            .filter((template) => !selectedCosts.some((item) => item.id === template.id)),
        [availableTemplates, searchTerm, selectedCosts]
    );

    const groupedSelectedCosts = useMemo(
        () => CATEGORY_ORDER
            .map((category) => ({ category, items: selectedCosts.filter((item) => item.category === category) })),
        [selectedCosts]
    );

    return (
        <div className="space-y-6 max-w-5xl mx-auto pb-32 md:pb-0">
            <OnboardingStepHero
                eyebrow="Paso 2 de 4"
                title="Define tu inventario operativo"
                description="Registra gastos fijos, software y herramientas para que Nougram entienda el costo mensual real de mantener tu empresa funcionando."
                callout={`Todos los valores se muestran y editan en ${primaryCurrency}. Los activos amortizables se calculan por vida útil, no como gasto mensual directo.`}
            />

            {onOpenImport && (
                <div className="flex justify-center">
                    <Button type="button" variant="secondary" onClick={onOpenImport} className="rounded-xl">
                        Importar inventario desde Excel
                    </Button>
                </div>
            )}

            <Card className="overflow-hidden border-dashed border-gray-300 shadow-sm">
                <div className="border-b border-gray-100 bg-gradient-to-r from-primary-soft to-white px-5 py-4">
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Carga manual</p>
                    <p className="mt-1 text-sm text-gray-600">Agrega cualquier gasto que no aparezca en las sugerencias.</p>
                </div>
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

            <div className="rounded-2xl border border-primary/10 bg-white p-4 shadow-sm">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Sugerencias rápidas</p>
                        <p className="mt-1 text-sm text-gray-600">Busca una plantilla y agrégala a la categoría correspondiente.</p>
                    </div>
                    <Input
                        placeholder="Buscar sugerencia..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="md:max-w-xs"
                    />
                </div>
                {filteredTemplateSuggestions.length > 0 && (
                    <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
                        {filteredTemplateSuggestions.slice(0, 12).map((template) => (
                            <button
                                key={template.id}
                                type="button"
                                onClick={() => toggleCost(template)}
                                className="shrink-0 rounded-full border border-gray-200 bg-surface-2 px-3 py-1.5 text-[12px] font-semibold text-gray-600 hover:border-primary/30 hover:bg-primary-soft hover:text-primary"
                            >
                                {template.icon} {template.name}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="space-y-4">
                {groupedSelectedCosts.map((group) => {
                    const meta = CATEGORY_META[group.category];
                    const open = openCategories[group.category];
                    const isTools = group.category === 'Tools';
                    const moneyInputMode: 'numeric' | 'decimal' = String(primaryCurrency || '').toUpperCase() === 'COP' ? 'numeric' : 'decimal';

                    return (
                        <Card key={group.category} className="overflow-hidden border-gray-200 shadow-sm">
                            <button
                                type="button"
                                onClick={() => setOpenCategories((prev) => ({ ...prev, [group.category]: !prev[group.category] }))}
                                className={`flex w-full items-center gap-4 border-b px-5 py-4 text-left ${meta.tint}`}
                            >
                                <div
                                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-black text-white"
                                    style={{ backgroundColor: meta.color }}
                                >
                                    {group.items.length}
                                </div>
                                <div className="min-w-0 flex-1">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <h3 className="text-[15px] font-black tracking-tight text-gray-900">{CATEGORY_LABELS[group.category]}</h3>
                                        <span className="rounded-full bg-white/70 px-2 py-0.5 text-[10.5px] font-semibold text-gray-500">
                                            {meta.sub}
                                        </span>
                                    </div>
                                    <p className="mt-1 text-[12px] text-gray-500">{meta.desc}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-[10px] font-black uppercase tracking-[0.14em] text-gray-400">Subtotal mensual</p>
                                    <p className="tabular-nums text-[16px] font-black" style={{ color: meta.color }}>
                                        {formatCurrency(categoryTotal(group.category), primaryCurrency)}
                                    </p>
                                </div>
                                <span className="text-xl text-gray-400">{open ? '−' : '+'}</span>
                            </button>

                            {open && (
                                <CardContent className="p-0">
                                    {group.items.length === 0 ? (
                                        <div className="px-5 py-8 text-center">
                                            <p className="text-sm font-semibold text-gray-700">Aún no hay conceptos registrados</p>
                                            <p className="mt-1 text-xs text-gray-400">Agrega el primero y luego ajusta montos, cantidad y frecuencia.</p>
                                            <Button type="button" onClick={() => addCategoryItem(group.category, `Nuevo ${CATEGORY_LABELS[group.category].toLowerCase()}`)} className="mt-4">
                                                Agregar primer concepto
                                            </Button>
                                        </div>
                                    ) : (
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b bg-surface-2 text-left text-[10.5px] font-black uppercase tracking-[0.12em] text-gray-400">
                                                        <th className="min-w-[220px] px-4 py-3">Concepto</th>
                                                        <th className="min-w-[140px] px-4 py-3">{isTools ? 'Costo total' : 'Costo'}</th>
                                                        <th className="min-w-[90px] px-4 py-3">Cantidad</th>
                                                        {isTools ? (
                                                            <>
                                                                <th className="min-w-[120px] px-4 py-3">Vida útil</th>
                                                                <th className="min-w-[140px] px-4 py-3">Salvamento</th>
                                                                <th className="min-w-[140px] px-4 py-3">Mensualizado</th>
                                                            </>
                                                        ) : (
                                                            <th className="min-w-[150px] px-4 py-3">Facturación</th>
                                                        )}
                                                        <th className="w-10 px-4 py-3" />
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {group.items.map((item) => {
                                                        const isAmortizable = Boolean(item.amortizable || isAmortizableCategory(item.category));
                                                        const currentPrice = isAmortizable ? (item.purchasePrice ?? item.amount ?? 0) : (item.amount ?? 0);

                                                        return (
                                                            <tr key={item.id} className="border-b last:border-b-0">
                                                                <td className="px-4 py-3 align-top">
                                                                    <Input
                                                                        value={item.name}
                                                                        onChange={(e) => updateSelectedCost(item.id, { name: e.target.value })}
                                                                        placeholder="Nombre del concepto"
                                                                    />
                                                                </td>
                                                                <td className="px-4 py-3 align-top">
                                                                    <Input
                                                                        type="text"
                                                                        inputMode={moneyInputMode}
                                                                        value={formatPriceInput(currentPrice, primaryCurrency)}
                                                                        onChange={(e) => updateSelectedCost(item.id, isAmortizable
                                                                            ? { purchasePrice: Math.max(0, parsePriceInput(e.target.value, primaryCurrency)), currency: primaryCurrency }
                                                                            : { amount: Math.max(0, parsePriceInput(e.target.value, primaryCurrency)), currency: primaryCurrency })}
                                                                    />
                                                                </td>
                                                                <td className="px-4 py-3 align-top">
                                                                    <Input
                                                                        type="number"
                                                                        min={1}
                                                                        value={item.quantity ?? 1}
                                                                        onChange={(e) => updateSelectedCost(item.id, { quantity: Math.max(1, Number(e.target.value) || 1) })}
                                                                    />
                                                                </td>
                                                                {isTools ? (
                                                                    <>
                                                                        <td className="px-4 py-3 align-top">
                                                                            <Input
                                                                                type="number"
                                                                                min={1}
                                                                                value={item.usefulLifeMonths ?? getDefaultUsefulLife(item)}
                                                                                onChange={(e) => updateSelectedCost(item.id, { usefulLifeMonths: Math.max(1, Number(e.target.value) || getDefaultUsefulLife(item)) })}
                                                                            />
                                                                        </td>
                                                                        <td className="px-4 py-3 align-top">
                                                                            <Input
                                                                                type="text"
                                                                                inputMode={moneyInputMode}
                                                                                value={formatPriceInput(item.salvageValue ?? 0, primaryCurrency)}
                                                                                onChange={(e) => updateSelectedCost(item.id, { salvageValue: Math.max(0, parsePriceInput(e.target.value, primaryCurrency)) })}
                                                                            />
                                                                        </td>
                                                                        <td className="px-4 py-3 align-top">
                                                                            <div className="rounded-lg bg-surface-2 px-3 py-2 text-[12px] font-bold tabular-nums text-gray-700">
                                                                                {formatCurrency(monthlyImpact(item), primaryCurrency)}
                                                                            </div>
                                                                        </td>
                                                                    </>
                                                                ) : (
                                                                    <td className="px-4 py-3 align-top">
                                                                        <select
                                                                            value={item.paymentType || 'monthly'}
                                                                            onChange={(e) => updateSelectedCost(item.id, { paymentType: e.target.value as 'monthly' | 'annual' })}
                                                                            className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                                                                        >
                                                                            <option value="monthly">Mensual</option>
                                                                            <option value="annual">Anual</option>
                                                                        </select>
                                                                    </td>
                                                                )}
                                                                <td className="px-4 py-3 align-top">
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setSelectedCosts((prev) => prev.filter((selected) => selected.id !== item.id))}
                                                                        className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-600"
                                                                        aria-label="Eliminar concepto"
                                                                    >
                                                                        ×
                                                                    </button>
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                            <div className="border-t bg-white px-5 py-3">
                                                <Button type="button" variant="secondary" onClick={() => addCategoryItem(group.category, `Nuevo ${CATEGORY_LABELS[group.category].toLowerCase()}`)}>
                                                    Agregar concepto
                                                </Button>
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            )}
                        </Card>
                    );
                })}
            </div>

            <Card className="bg-gray-50 border-t border-gray-200 shadow-[0_-8px_28px_rgba(15,23,42,0.08)] rounded-t-2xl md:rounded-xl fixed inset-x-0 bottom-0 z-40 md:static md:inset-auto md:shadow-lg md:sticky md:bottom-4 pb-[max(0.5rem,env(safe-area-inset-bottom))] md:pb-0">
                <CardContent className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between p-4 gap-4">
                    <div className="min-w-0 text-center sm:text-left">
                        <p className="text-xs sm:text-sm text-gray-500">Impacto mensual estimado (incluye amortizacion)</p>
                        <p className="text-xl sm:text-2xl font-bold text-gray-900">{formatCurrency(calculateTotal(), primaryCurrency)}</p>
                        <p className="text-xs text-gray-400">{selectedCosts.length} items seleccionados</p>
                    </div>
                    <div className="flex gap-3 w-full sm:w-auto">
                        <Button variant="secondary" onClick={onBack} className="flex-1 sm:flex-none h-12 rounded-2xl font-bold md:h-10 md:rounded-md">
                            ← Atras
                        </Button>
                        <Button onClick={() => onNext({ selectedTemplates: selectedCosts, totalMonthly: calculateTotal() })} className="flex-1 sm:flex-none h-12 rounded-2xl font-bold md:h-10 md:rounded-md">
                            Siguiente →
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
