
import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
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
    { id: 'design', label: 'Diseño', icon: '🎨' },
    { id: 'consulting', label: 'Consultoría', icon: '🤝' },
];

const CATEGORY_ORDER: Array<FixedCostTemplate['category']> = ['Tools', 'Software', 'Overhead', 'Other'];
const CATEGORY_LABELS: Record<FixedCostTemplate['category'], string> = {
    Tools: 'Herramientas y Equipos',
    Software: 'Software y Licencias',
    Overhead: 'Gastos Operativos',
    Other: 'Otros',
};

export function StepFixedCosts({ onNext, onBack, initialData, primaryCurrency }: StepFixedCostsProps) {
    const [availableTemplates, setAvailableTemplates] = useState<FixedCostTemplate[]>([]);
    const [exchangeRates, setExchangeRates] = useState<Record<string, { rate: number; lastUpdated: string }>>({});

    const normalizeTemplateToPrimary = (template: FixedCostTemplate): FixedCostTemplate => {
        const normalizedAmount = onboardingService.convertCurrency(
            template.amount || 0,
            template.currency || primaryCurrency,
            primaryCurrency,
            exchangeRates
        );
        return {
            ...template,
            amount: Number(normalizedAmount.toFixed(2)),
            currency: primaryCurrency,
            quantity: template.quantity && template.quantity > 0 ? template.quantity : 1,
        };
    };

    const [selectedCosts, setSelectedCosts] = useState<FixedCostTemplate[]>(
        (initialData?.selectedTemplates || []).map((item) => normalizeTemplateToPrimary(item))
    );
    const [activeIndustry, setActiveIndustry] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [showCustomModal, setShowCustomModal] = useState(false);

    // Custom Cost State (always in primary currency)
    const [customCost, setCustomCost] = useState({ name: '', amount: '' });

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

    const handleIndustrySelect = (industryId: string) => {
        setActiveIndustry(industryId);
        // Pre-select templates
        const industryTemplates = availableTemplates.filter(t => t.preSelectedFor?.includes(industryId));

        // Merge with existing selection (avoid duplicates by ID)
        const combined = [...selectedCosts];
        industryTemplates.forEach(t => {
            if (!combined.find(existing => existing.id === t.id)) {
                combined.push(normalizeTemplateToPrimary(t));
            }
        });
        setSelectedCosts(combined);
    };

    const toggleCost = (template: FixedCostTemplate) => {
        const exists = selectedCosts.find(t => t.id === template.id);
        if (exists) {
            setSelectedCosts(selectedCosts.filter(t => t.id !== template.id));
        } else {
            setSelectedCosts([...selectedCosts, normalizeTemplateToPrimary(template)]);
        }
    };

    const updateSelectedCost = (id: string, updates: Partial<FixedCostTemplate>) => {
        setSelectedCosts((prev) => prev.map((item) => (item.id === id ? { ...item, ...updates } : item)));
    };

    const handleAddCustom = () => {
        if (!customCost.name || !customCost.amount) return;

        const newCost: FixedCostTemplate = {
            id: `custom-${Date.now()}`,
            name: customCost.name,
            amount: parseFloat(customCost.amount),
            currency: primaryCurrency,
            quantity: 1,
            category: 'Other',
            icon: '✨',
            isCustom: true
        };

        setSelectedCosts([...selectedCosts, newCost]);
        setCustomCost({ name: '', amount: '' });
        setShowCustomModal(false);
    };

    const calculateTotal = () => {
        return selectedCosts.reduce((acc, curr) => {
            return acc + onboardingService.convertCurrency(curr.amount, curr.currency, primaryCurrency, exchangeRates);
        }, 0);
    };

    const filteredTemplates = availableTemplates.filter(t =>
        t.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const groupedTemplates = CATEGORY_ORDER.map((category) => ({
        category,
        templates: filteredTemplates.filter((template) => template.category === category),
    })).filter((group) => group.templates.length > 0);

    const handleNext = () => {
        onNext({ selectedTemplates: selectedCosts, totalMonthly: calculateTotal() });
    };

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold text-gray-900">Define tu inventario operativo</h1>
                <p className="text-gray-600">
                    Entre mas detallado sea tu inventario, mejor sera tu proyeccion financiera: computadores, monitores,
                    mobiliario, software, servicios y cualquier activo relevante.
                </p>
                <p className="text-xs text-gray-500">
                    Importante: el monto ingresado en cada item representa el total acumulado de la cantidad indicada.
                </p>
                <p className="text-xs text-blue-600">
                    Todos los valores de este paso se muestran y editan en {primaryCurrency}.
                </p>
            </div>

            {/* Quick Select & Actions */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div className="space-y-3 flex-1">
                    <p className="text-sm font-medium text-gray-700">💡 Quick Select: Elige tu industria</p>
                    <div className="flex flex-wrap gap-2">
                        {INDUSTRIES.map(ind => (
                            <button
                                key={ind.id}
                                onClick={() => handleIndustrySelect(ind.id)}
                                className={`px-4 py-2 rounded-full border text-sm font-medium transition-colors ${activeIndustry === ind.id
                                    ? 'bg-blue-100 border-blue-500 text-blue-700'
                                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                                    }`}
                            >
                                {ind.icon} {ind.label}
                            </button>
                        ))}
                    </div>
                </div>

                <Button onClick={() => setShowCustomModal(true)} variant="secondary" className="whitespace-nowrap">
                    + Agregar Costo
                </Button>
            </div>

            {/* Categorized Manual List */}
            <div className="space-y-4">
                <Input
                    placeholder="Buscar herramienta..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="max-w-md"
                />

                {groupedTemplates.map((group) => (
                    <Card key={group.category} className="border-gray-200">
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-sm font-semibold text-gray-800">{CATEGORY_LABELS[group.category]}</h3>
                                <span className="text-xs text-gray-500">{group.templates.length} ítems</span>
                            </div>
                            <div className="space-y-2">
                                {group.templates.map((template) => {
                                    const isSelected = selectedCosts.some((t) => t.id === template.id);
                                    const selectedTemplate = selectedCosts.find((c) => c.id === template.id);
                                    const displayedAmount = selectedTemplate
                                        ? selectedTemplate.amount
                                        : onboardingService.convertCurrency(template.amount, template.currency, primaryCurrency, exchangeRates);

                                    return (
                                        <div
                                            key={template.id}
                                            className={`rounded-lg border p-3 ${isSelected ? 'border-blue-400 bg-blue-50/50' : 'border-gray-200 bg-white'}`}
                                        >
                                            <div className="flex items-center justify-between gap-3">
                                                <button
                                                    type="button"
                                                    onClick={() => toggleCost(template)}
                                                    className="flex items-center gap-2 text-left"
                                                >
                                                    <span className="text-xl">{template.icon}</span>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">{template.name}</p>
                                                        <p className="text-xs text-gray-500">
                                                            {formatCurrency(displayedAmount, primaryCurrency)} /mes
                                                        </p>
                                                    </div>
                                                </button>
                                                <div className={`w-5 h-5 rounded border flex items-center justify-center ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-300 bg-white'}`}>
                                                    {isSelected && (
                                                        <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    )}
                                                </div>
                                            </div>
                                            {isSelected && (
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                                                    <div>
                                                        <p className="text-[11px] text-gray-500 mb-1">Cantidad</p>
                                                        <Input
                                                            type="number"
                                                            min={1}
                                                            value={selectedTemplate?.quantity ?? 1}
                                                            onChange={(e) =>
                                                                updateSelectedCost(template.id, {
                                                                    quantity: Math.max(1, Number(e.target.value) || 1),
                                                                })
                                                            }
                                                        />
                                                    </div>
                                                    <div>
                                                        <p className="text-[11px] text-gray-500 mb-1">Monto total ({primaryCurrency})</p>
                                                        <Input
                                                            type="number"
                                                            min={0}
                                                            value={selectedTemplate?.amount ?? displayedAmount}
                                                            onChange={(e) =>
                                                                updateSelectedCost(template.id, {
                                                                    amount: Math.max(0, Number(e.target.value) || 0),
                                                                    currency: primaryCurrency,
                                                                })
                                                            }
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>
                ))}

                {selectedCosts.filter((c) => c.isCustom).length > 0 && (
                    <Card className="border-gray-200">
                        <CardContent className="pt-4 space-y-2">
                            <h3 className="text-sm font-semibold text-gray-800">Costos Personalizados</h3>
                            {selectedCosts.filter((c) => c.isCustom).map((cost) => (
                                <div key={cost.id} className="rounded-lg border border-blue-400 bg-blue-50/50 p-3">
                                    <div className="flex items-center justify-between gap-2">
                                        <p className="text-sm font-medium text-gray-900">{cost.icon} {cost.name}</p>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                toggleCost(cost);
                                            }}
                                            className="text-xs text-red-600 hover:text-red-700"
                                        >
                                            Eliminar
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                                        <div>
                                            <p className="text-[11px] text-gray-500 mb-1">Cantidad</p>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={cost.quantity ?? 1}
                                                onChange={(e) =>
                                                    updateSelectedCost(cost.id, {
                                                        quantity: Math.max(1, Number(e.target.value) || 1),
                                                    })
                                                }
                                            />
                                        </div>
                                        <div>
                                            <p className="text-[11px] text-gray-500 mb-1">Monto total ({primaryCurrency})</p>
                                            <Input
                                                type="number"
                                                min={0}
                                                value={cost.amount}
                                                onChange={(e) =>
                                                    updateSelectedCost(cost.id, {
                                                        amount: Math.max(0, Number(e.target.value) || 0),
                                                        currency: primaryCurrency,
                                                    })
                                                }
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                )}
            </div>

            {/* Custom Cost Modal */}
            {showCustomModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <Card className="max-w-md w-full">
                        <CardContent className="space-y-4 pt-6">
                            <h3 className="text-lg font-bold">Agregar Costo Personalizado</h3>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Nombre</label>
                                <Input
                                    value={customCost.name}
                                    onChange={e => setCustomCost({ ...customCost, name: e.target.value })}
                                    placeholder="Ej: Licencia Software X"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Monto</label>
                                    <Input
                                        type="number"
                                        value={customCost.amount}
                                        onChange={e => setCustomCost({ ...customCost, amount: e.target.value })}
                                        placeholder="0"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Moneda</label>
                                    <Input value={primaryCurrency} disabled />
                                </div>
                            </div>
                            <div className="flex gap-2 justify-end pt-2">
                                <Button variant="secondary" onClick={() => setShowCustomModal(false)}>Cancelar</Button>
                                <Button onClick={handleAddCustom}>Agregar</Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Summary Footer */}
            <Card className="bg-gray-50 sticky bottom-4 shadow-lg border-t border-gray-200">
                <CardContent className="flex flex-col sm:flex-row items-center justify-between p-4">
                    <div>
                        <p className="text-sm text-gray-500">Total Mensual Estimado</p>
                        <p className="text-2xl font-bold text-gray-900">
                            {formatCurrency(calculateTotal(), primaryCurrency)}
                        </p>
                        <p className="text-xs text-gray-400">{selectedCosts.length} items seleccionados</p>
                    </div>
                    <div className="flex gap-3 mt-4 sm:mt-0 w-full sm:w-auto">
                        <Button variant="secondary" onClick={onBack} className="flex-1 sm:flex-none">
                            ← Atrás
                        </Button>
                        <Button onClick={handleNext} className="flex-1 sm:flex-none">
                            Siguiente →
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
