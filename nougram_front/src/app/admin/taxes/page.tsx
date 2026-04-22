'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { taxService } from '@/services/taxService';
import { TaxConfig } from '@/types/quote-builder';
import { SocialChargesConfig } from '@/components/admin/payroll/SocialChargesConfig';
import { formatDisplayNumber } from '@/lib/utils';

type TaxFormState = {
    name: string;
    code: string;
    percentage: string;
    country: string;
    description: string;
    isActive: boolean;
};

const INITIAL_FORM: TaxFormState = {
    name: '',
    code: '',
    percentage: '',
    country: '',
    description: '',
    isActive: true,
};

export default function TaxesAdminPage() {
    const [taxes, setTaxes] = useState<TaxConfig[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [filterCountry, setFilterCountry] = useState('');
    const [editingId, setEditingId] = useState<number | null>(null);
    const [form, setForm] = useState<TaxFormState>(INITIAL_FORM);

    const loadTaxes = async () => {
        setLoading(true);
        setError(null);
        try {
            const all = await taxService.getAll({ activeOnly: false });
            setTaxes(all);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'No se pudieron cargar los impuestos');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void loadTaxes();
    }, []);

    const filteredTaxes = useMemo(() => {
        const country = filterCountry.trim().toUpperCase();
        if (!country) return taxes;
        return taxes.filter((tax) => (tax.country || '').toUpperCase() === country);
    }, [taxes, filterCountry]);

    const resetForm = () => {
        setEditingId(null);
        setForm(INITIAL_FORM);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        const percentage = Number(form.percentage);
        if (!form.name.trim() || !form.code.trim() || !Number.isFinite(percentage) || percentage < 0) {
            setError('Completa nombre, código y porcentaje válido (>= 0).');
            return;
        }

        setSaving(true);
        try {
            const payload = {
                name: form.name.trim(),
                code: form.code.trim().toUpperCase(),
                percentage,
                country: form.country.trim().toUpperCase() || undefined,
                description: form.description.trim() || undefined,
                is_active: form.isActive,
            };

            if (editingId) {
                await taxService.update(editingId, payload);
            } else {
                await taxService.create(payload);
            }
            resetForm();
            await loadTaxes();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'No se pudo guardar el impuesto');
        } finally {
            setSaving(false);
        }
    };

    const handleEdit = (tax: TaxConfig) => {
        setEditingId(tax.id);
        setForm({
            name: tax.name || '',
            code: tax.code || '',
            percentage: String(tax.percentage ?? ''),
            country: tax.country || '',
            description: tax.description || '',
            isActive: Boolean(tax.isActive ?? true),
        });
    };

    const handleDelete = async (taxId: number) => {
        setError(null);
        try {
            await taxService.remove(taxId);
            if (editingId === taxId) resetForm();
            await loadTaxes();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'No se pudo eliminar el impuesto');
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-[20px] font-bold text-gray-900">Impuestos</h1>
                <p className="text-[13px] text-gray-500 mt-0.5">
                    Configura impuestos por país. Se aplican como porcentaje sobre la base de la cotización.
                </p>
            </div>

            <SocialChargesConfig />

            <form onSubmit={handleSubmit} className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Nombre</label>
                        <Input
                            value={form.name}
                            onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                            placeholder="Ej: IVA"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Código</label>
                        <Input
                            value={form.code}
                            onChange={(e) => setForm((prev) => ({ ...prev, code: e.target.value.toUpperCase() }))}
                            placeholder="Ej: VAT"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Porcentaje</label>
                        <Input
                            type="number"
                            step="0.01"
                            min="0"
                            value={form.percentage}
                            onChange={(e) => setForm((prev) => ({ ...prev, percentage: e.target.value }))}
                            placeholder="Ej: 19"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-gray-600">País (ISO, opcional)</label>
                        <Input
                            value={form.country}
                            onChange={(e) => setForm((prev) => ({ ...prev, country: e.target.value.toUpperCase() }))}
                            placeholder="Ej: CO, MX, US"
                            maxLength={3}
                        />
                    </div>
                    <div className="md:col-span-2">
                        <label className="text-xs font-semibold text-gray-600">Descripción (opcional)</label>
                        <Input
                            value={form.description}
                            onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                            placeholder="Ej: Impuesto al valor agregado"
                        />
                    </div>
                </div>

                <label className="inline-flex items-center gap-2 text-sm text-gray-700">
                    <input
                        type="checkbox"
                        checked={form.isActive}
                        onChange={(e) => setForm((prev) => ({ ...prev, isActive: e.target.checked }))}
                    />
                    Impuesto activo
                </label>

                <div className="flex items-center gap-3">
                    <Button type="submit" disabled={saving}>
                        {saving ? 'Guardando...' : editingId ? 'Actualizar impuesto' : 'Crear impuesto'}
                    </Button>
                    {editingId && (
                        <Button type="button" variant="secondary" onClick={resetForm}>
                            Cancelar edición
                        </Button>
                    )}
                </div>
            </form>

            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <h2 className="text-[14px] font-semibold text-gray-900">Impuestos configurados</h2>
                    <Input
                        value={filterCountry}
                        onChange={(e) => setFilterCountry(e.target.value)}
                        placeholder="Filtrar por país (CO, MX, US...)"
                        className="md:w-72"
                    />
                </div>

                {error && (
                    <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
                )}

                {loading ? (
                    <p className="text-sm text-gray-500">Cargando impuestos...</p>
                ) : filteredTaxes.length === 0 ? (
                    <p className="text-sm text-gray-500">No hay impuestos para el filtro actual.</p>
                ) : (
                    <div className="overflow-auto">
                        <table className="w-full text-sm">
                            <thead className="text-left text-gray-500">
                                <tr>
                                    <th className="py-2">Nombre</th>
                                    <th className="py-2">Código</th>
                                    <th className="py-2">País</th>
                                    <th className="py-2">%</th>
                                    <th className="py-2">Estado</th>
                                    <th className="py-2 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredTaxes.map((tax) => (
                                    <tr key={tax.id} className="border-t border-gray-100">
                                        <td className="py-2 font-medium text-gray-900">{tax.name}</td>
                                        <td className="py-2">{tax.code || '-'}</td>
                                        <td className="py-2">{tax.country || 'Global'}</td>
                                        <td className="py-2">{formatDisplayNumber(Number(tax.percentage || 0), { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%</td>
                                        <td className="py-2">{tax.isActive ? 'Activo' : 'Inactivo'}</td>
                                        <td className="py-2 text-right space-x-2">
                                            <Button type="button" variant="secondary" size="sm" onClick={() => handleEdit(tax)}>
                                                Editar
                                            </Button>
                                            <Button type="button" variant="ghost" size="sm" onClick={() => handleDelete(tax.id)}>
                                                Eliminar
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

