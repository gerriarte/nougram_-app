
import React, { useMemo, useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { onboardingService, ALL_TEMPLATES } from '@/services/onboardingService';
import { FixedCostTemplate } from '@/types/onboarding';

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

export function StepFixedCosts({ onNext, onBack, initialData, primaryCurrency }: StepFixedCostsProps) {
    type LogicalCategory = 'amortization' | 'operational' | 'tools';
    const [selectedCosts, setSelectedCosts] = useState<FixedCostTemplate[]>(
        (initialData?.selectedTemplates || [])
            .filter((item: any) => item && typeof item.name === 'string')
            .map((item: any) => ({
                ...item,
                amount: Number(item?.amount || 0),
                costType: item?.costType || 'operational'
            }))
    );
    const [activeIndustry, setActiveIndustry] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [showCustomModal, setShowCustomModal] = useState(false);
    const [editingCostId, setEditingCostId] = useState<string | null>(null);

    // Custom Cost State
    const [customCost, setCustomCost] = useState({
        name: '',
        amount: '',
        currency: primaryCurrency,
        logicalCategory: 'operational' as LogicalCategory
    });
    const [editCost, setEditCost] = useState<{
        id: string;
        name: string;
        amount: string;
        logicalCategory: LogicalCategory;
    } | null>(null);

    const getLogicalCategory = (cost: FixedCostTemplate): LogicalCategory => {
        if (cost.costType === 'amortization') return 'amortization';
        if (cost.category === 'Tools' || cost.category === 'Software') return 'tools';
        return 'operational';
    };

    const logicalCategoryLabel = (value: LogicalCategory): string => {
        if (value === 'amortization') return 'Amortización';
        if (value === 'tools') return 'Herramientas';
        return 'Costos operacionales';
    };

    const getCategoryFields = (cost: FixedCostTemplate, logicalCategory: LogicalCategory): Pick<FixedCostTemplate, 'category' | 'costType'> => {
        if (logicalCategory === 'tools') {
            return { category: 'Tools', costType: 'operational' };
        }
        if (logicalCategory === 'amortization') {
            return { category: cost.category, costType: 'amortization' };
        }
        return { category: cost.category, costType: 'operational' };
    };

    const toPrimaryCurrency = (template: FixedCostTemplate): FixedCostTemplate => {
        const convertedAmount = onboardingService.convertCurrency(template.amount, template.currency, primaryCurrency);
        return {
            ...template,
            amount: Number(convertedAmount.toFixed(2)),
            currency: primaryCurrency
        };
    };

    const handleIndustrySelect = (industryId: string) => {
        setActiveIndustry(industryId);
        // Pre-select templates
        const industryTemplates = ALL_TEMPLATES.filter(t => t.preSelectedFor?.includes(industryId));

        // Merge with existing selection (avoid duplicates by ID)
        const combined = [...selectedCosts];
        industryTemplates.forEach(t => {
            if (!combined.find(existing => existing.id === t.id)) {
                combined.push(toPrimaryCurrency(t));
            }
        });
        setSelectedCosts(combined);
    };

    const toggleCost = (template: FixedCostTemplate) => {
        const exists = selectedCosts.find(t => t.id === template.id);
        if (exists) {
            setSelectedCosts(selectedCosts.filter(t => t.id !== template.id));
        } else {
            setSelectedCosts([...selectedCosts, toPrimaryCurrency(template)]);
        }
    };

    const handleAddCustom = () => {
        if (!customCost.name || !customCost.amount) return;

        const newCost: FixedCostTemplate = {
            id: `custom-${Date.now()}`,
            name: customCost.name,
            amount: parseFloat(customCost.amount),
            currency: primaryCurrency,
            category: 'Other',
            costType: 'operational',
            icon: '✨',
            isCustom: true
        };

        setSelectedCosts([...selectedCosts, { ...newCost, ...getCategoryFields(newCost, customCost.logicalCategory) }]);
        setCustomCost({ name: '', amount: '', currency: primaryCurrency, logicalCategory: 'operational' });
        setShowCustomModal(false);
    };

    const startEditCost = (cost: FixedCostTemplate) => {
        setEditingCostId(cost.id);
        setEditCost({
            id: cost.id,
            name: cost.name,
            amount: String(cost.amount),
            logicalCategory: getLogicalCategory(cost)
        });
    };

    const saveEditedCost = () => {
        if (!editCost || !editCost.name.trim() || !editCost.amount) return;
        const parsedAmount = parseFloat(editCost.amount);
        if (Number.isNaN(parsedAmount) || parsedAmount <= 0) return;

        setSelectedCosts((prev) =>
            prev.map((cost) =>
                cost.id === editCost.id
                    ? {
                        ...cost,
                        name: editCost.name.trim(),
                        amount: parsedAmount,
                        currency: primaryCurrency,
                        ...getCategoryFields(cost, editCost.logicalCategory)
                    }
                    : cost
            )
        );
        setEditingCostId(null);
        setEditCost(null);
    };

    const calculateTotal = () => {
        return selectedCosts.reduce((acc, curr) => {
            return acc + curr.amount;
        }, 0);
    };

    const selectedTemplateIds = useMemo(
        () => new Set(selectedCosts.map((cost) => cost.id)),
        [selectedCosts]
    );

    const filteredTemplates = ALL_TEMPLATES.filter((t) =>
        t.name.toLowerCase().includes(searchTerm.toLowerCase()) && !selectedTemplateIds.has(t.id)
    );

    const handleNext = () => {
        onNext({ selectedTemplates: selectedCosts, totalMonthly: calculateTotal() });
    };

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold text-gray-900">¿Qué herramientas y servicios usas?</h1>
                <p className="text-gray-600">Selecciona los costos fijos que ya tienes. Puedes agregar costos personalizados.</p>
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

            {/* Templates Grid */}
            <div className="space-y-4">
                <Input
                    placeholder="Buscar herramienta..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="max-w-md"
                />

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Selected costs (editable) */}
                    {selectedCosts.map(cost => (
                        <div
                            key={cost.id}
                            className="relative p-4 rounded-lg border border-blue-500 bg-blue-50/50 cursor-pointer"
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl">{cost.icon}</span>
                                    <span className="font-semibold text-gray-900">{cost.name}</span>
                                </div>
                                <button
                                    onClick={(e) => { e.stopPropagation(); toggleCost(cost); }}
                                    className="text-red-500 hover:text-red-700 text-xs"
                                >
                                    Eliminar
                                </button>
                            </div>
                            <p className="font-medium text-gray-900">
                                ${Number(cost.amount || 0).toLocaleString()} {primaryCurrency} <span className="text-xs text-gray-500">/mes</span>
                            </p>
                            <div className="mt-2 flex items-center justify-between gap-2">
                                <span className={`text-xs px-2 py-1 rounded ${getLogicalCategory(cost) === 'amortization' ? 'bg-purple-100 text-purple-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                    {logicalCategoryLabel(getLogicalCategory(cost))}
                                </span>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        startEditCost(cost);
                                    }}
                                    className="text-xs text-blue-600 hover:text-blue-800"
                                >
                                    Editar
                                </button>
                            </div>
                        </div>
                    ))}

                    {filteredTemplates.map(template => {
                        const isSelected = selectedTemplateIds.has(template.id);
                        const convertedAmount = onboardingService.convertCurrency(template.amount, template.currency, primaryCurrency);

                        return (
                            <div
                                key={template.id}
                                onClick={() => toggleCost(template)}
                                className={`relative p-4 rounded-lg border cursor-pointer transition-all hover:shadow-sm ${isSelected ? 'border-blue-500 bg-blue-50/50' : 'border-gray-200 bg-white'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className="text-2xl">{template.icon}</span>
                                        <span className="font-semibold text-gray-900">{template.name}</span>
                                    </div>
                                    <div className={`w-5 h-5 rounded border flex items-center justify-center ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-300 bg-white'
                                        }`}>
                                        {isSelected && <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <p className="font-medium text-gray-900">
                                        ${convertedAmount.toLocaleString()} {primaryCurrency} <span className="text-xs text-gray-500">/mes</span>
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {logicalCategoryLabel(getLogicalCategory(template))}
                                    </p>
                                </div>
                            </div>
                        );
                    })}
                </div>
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
                                    <label className="text-sm font-medium">Categoría</label>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                        value={customCost.logicalCategory}
                                        onChange={e => setCustomCost({ ...customCost, logicalCategory: e.target.value as LogicalCategory })}
                                    >
                                        <option value="amortization">Amortización</option>
                                        <option value="operational">Costos operacionales</option>
                                        <option value="tools">Herramientas (operacional)</option>
                                    </select>
                                </div>
                            </div>
                            <p className="text-xs text-gray-500">Moneda aplicada: {primaryCurrency}</p>
                            <div className="flex gap-2 justify-end pt-2">
                                <Button variant="secondary" onClick={() => setShowCustomModal(false)}>Cancelar</Button>
                                <Button onClick={handleAddCustom}>Agregar</Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Edit Cost Modal */}
            {editingCostId && editCost && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <Card className="max-w-md w-full">
                        <CardContent className="space-y-4 pt-6">
                            <h3 className="text-lg font-bold">Editar costo</h3>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Nombre</label>
                                <Input
                                    value={editCost.name}
                                    onChange={e => setEditCost({ ...editCost, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Monto ({primaryCurrency})</label>
                                <Input
                                    type="number"
                                    value={editCost.amount}
                                    onChange={e => setEditCost({ ...editCost, amount: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Tipo de costo</label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={editCost.logicalCategory}
                                    onChange={e => setEditCost({ ...editCost, logicalCategory: e.target.value as LogicalCategory })}
                                >
                                    <option value="amortization">Amortización</option>
                                    <option value="operational">Costos operacionales</option>
                                    <option value="tools">Herramientas (operacional)</option>
                                </select>
                            </div>
                            <div className="flex gap-2 justify-end pt-2">
                                <Button variant="secondary" onClick={() => { setEditingCostId(null); setEditCost(null); }}>
                                    Cancelar
                                </Button>
                                <Button onClick={saveEditedCost}>Guardar cambios</Button>
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
                            ${calculateTotal().toLocaleString()} {primaryCurrency}
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
