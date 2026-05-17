'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { vendorService } from '@/services/vendorService';
import { Vendor } from '@/types/quote-builder';

const CATEGORIES = ['Software', 'Freelance', 'Infraestructura', 'Materiales', 'Licencias', 'Otro'];

type FormState = {
    name: string;
    description: string;
    category: string;
    defaultCost: string;
    defaultMarkupPercentage: string;
    isActive: boolean;
};

const INITIAL_FORM: FormState = {
    name: '',
    description: '',
    category: '',
    defaultCost: '',
    defaultMarkupPercentage: '',
    isActive: true,
};

export default function VendorsAdminPage() {
    const [vendors, setVendors] = useState<Vendor[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [form, setForm] = useState<FormState>(INITIAL_FORM);
    const [search, setSearch] = useState('');

    const load = async () => {
        setLoading(true);
        setError(null);
        try {
            setVendors(await vendorService.getAll());
        } catch (e) {
            setError(e instanceof Error ? e.message : 'No se pudieron cargar los proveedores');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { void load(); }, []);

    const reset = () => { setEditingId(null); setForm(INITIAL_FORM); };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        if (!form.name.trim()) { setError('El nombre es requerido.'); return; }

        setSaving(true);
        try {
            const payload = {
                name: form.name.trim(),
                description: form.description.trim() || undefined,
                category: form.category || undefined,
                default_cost: form.defaultCost ? Number(form.defaultCost) : undefined,
                default_markup_percentage: form.defaultMarkupPercentage
                    ? Number(form.defaultMarkupPercentage) / 100
                    : undefined,
                is_active: form.isActive,
            };
            if (editingId) {
                await vendorService.update(editingId, payload);
            } else {
                await vendorService.create(payload);
            }
            reset();
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'No se pudo guardar el proveedor');
        } finally {
            setSaving(false);
        }
    };

    const handleEdit = (v: Vendor) => {
        setEditingId(v.id);
        setForm({
            name: v.name,
            description: v.description || '',
            category: v.category || '',
            defaultCost: v.defaultCost != null ? String(v.defaultCost) : '',
            defaultMarkupPercentage: v.defaultMarkupPercentage != null
                ? String(Math.round(v.defaultMarkupPercentage * 100))
                : '',
            isActive: v.isActive,
        });
    };

    const handleDelete = async (id: number) => {
        setError(null);
        try {
            await vendorService.remove(id);
            if (editingId === id) reset();
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'No se pudo eliminar el proveedor');
        }
    };

    const filtered = vendors.filter(v =>
        !search || v.name.toLowerCase().includes(search.toLowerCase()) ||
        (v.category || '').toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-[20px] font-bold text-gray-900">Catálogo de Proveedores</h1>
                <p className="text-[13px] text-gray-500 mt-0.5">
                    Registra proveedores recurrentes. Al agregar un gasto en el builder puedes seleccionarlos
                    y se pre-llenan costo y margen automáticamente.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                <h2 className="text-[14px] font-semibold text-gray-900">
                    {editingId ? 'Editar proveedor' : 'Agregar proveedor'}
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Nombre *</label>
                        <Input
                            value={form.name}
                            onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                            placeholder="Ej: AWS, Adobe, Fiverr"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Categoría</label>
                        <select
                            value={form.category}
                            onChange={e => setForm(p => ({ ...p, category: e.target.value }))}
                            className="mt-1 w-full h-9 rounded-lg border border-gray-200 bg-white px-3 text-[13px] text-gray-700 focus:border-primary focus:outline-none"
                        >
                            <option value="">Sin categoría</option>
                            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Descripción</label>
                        <Input
                            value={form.description}
                            onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                            placeholder="Opcional"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Costo por defecto</label>
                        <Input
                            type="number"
                            min="0"
                            step="0.01"
                            value={form.defaultCost}
                            onChange={e => setForm(p => ({ ...p, defaultCost: e.target.value }))}
                            placeholder="Ej: 500000"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-gray-600">Margen por defecto (%)</label>
                        <Input
                            type="number"
                            min="0"
                            max="500"
                            step="1"
                            value={form.defaultMarkupPercentage}
                            onChange={e => setForm(p => ({ ...p, defaultMarkupPercentage: e.target.value }))}
                            placeholder="Ej: 20"
                        />
                    </div>
                </div>

                <label className="inline-flex items-center gap-2 text-sm text-gray-700">
                    <input
                        type="checkbox"
                        checked={form.isActive}
                        onChange={e => setForm(p => ({ ...p, isActive: e.target.checked }))}
                    />
                    Proveedor activo
                </label>

                {error && (
                    <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
                )}

                <div className="flex items-center gap-3">
                    <Button type="submit" disabled={saving}>
                        {saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Agregar proveedor'}
                    </Button>
                    {editingId && (
                        <Button type="button" variant="secondary" onClick={reset}>
                            Cancelar
                        </Button>
                    )}
                </div>
            </form>

            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <h2 className="text-[14px] font-semibold text-gray-900">
                        Proveedores registrados <span className="text-gray-400 font-normal">({vendors.length})</span>
                    </h2>
                    <Input
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        placeholder="Buscar por nombre o categoría..."
                        className="md:w-72"
                    />
                </div>

                {loading ? (
                    <p className="text-sm text-gray-500">Cargando...</p>
                ) : filtered.length === 0 ? (
                    <p className="text-sm text-gray-500">
                        {vendors.length === 0
                            ? 'No hay proveedores registrados aún.'
                            : 'No hay resultados para la búsqueda.'}
                    </p>
                ) : (
                    <div className="overflow-auto">
                        <table className="w-full text-sm">
                            <thead className="text-left text-gray-500">
                                <tr>
                                    <th className="py-2 pr-4">Nombre</th>
                                    <th className="py-2 pr-4">Categoría</th>
                                    <th className="py-2 pr-4">Costo def.</th>
                                    <th className="py-2 pr-4">Margen def.</th>
                                    <th className="py-2 pr-4">Estado</th>
                                    <th className="py-2 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map(v => (
                                    <tr key={v.id} className="border-t border-gray-100">
                                        <td className="py-2 pr-4 font-medium text-gray-900">{v.name}</td>
                                        <td className="py-2 pr-4 text-gray-500">{v.category || '—'}</td>
                                        <td className="py-2 pr-4 tabular-nums">
                                            {v.defaultCost != null ? `$${v.defaultCost.toLocaleString()}` : '—'}
                                        </td>
                                        <td className="py-2 pr-4 tabular-nums">
                                            {v.defaultMarkupPercentage != null
                                                ? `${Math.round(v.defaultMarkupPercentage * 100)}%`
                                                : '—'}
                                        </td>
                                        <td className="py-2 pr-4">
                                            <span className={`text-xs font-semibold ${v.isActive ? 'text-green-600' : 'text-gray-400'}`}>
                                                {v.isActive ? 'Activo' : 'Inactivo'}
                                            </span>
                                        </td>
                                        <td className="py-2 text-right space-x-2">
                                            <Button type="button" variant="secondary" size="sm" onClick={() => handleEdit(v)}>
                                                Editar
                                            </Button>
                                            <Button type="button" variant="ghost" size="sm" onClick={() => handleDelete(v.id)}>
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
