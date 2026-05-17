
'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { QuickSelectCard } from './QuickSelectCard';
import { QuickSelectDialog } from './QuickSelectDialog';

// Mock Initial Data
const INITIAL_DATA = [
    { id: 'marketing_agency', name: 'Agencia de Marketing', description: 'Herramientas para marketing digital', icon: '📢', isSystem: true, isActive: true, templateCount: 4, color: '#3B82F6', templateIds: ['adobe', 'chatgpt'] },
    { id: 'web_development', name: 'Desarrollo Web', description: 'Stack típico de dev', icon: '💻', isSystem: true, isActive: true, templateCount: 5, color: '#10B981', templateIds: ['hosting', 'chatgpt'] },
    { id: 'design_agency', name: 'Agencia de Diseño', description: 'Software creativo', icon: '🎨', isSystem: true, isActive: true, templateCount: 4, color: '#EC4899', templateIds: ['adobe'] },
    { id: 'consulting', name: 'Consultoría', description: 'Gestión y comunicación', icon: '🤝', isSystem: true, isActive: true, templateCount: 4, color: '#F59E0B', templateIds: ['notion'] },
];

export function QuickSelectList() {
    const [quickSelects, setQuickSelects] = useState(INITIAL_DATA);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<any>(null);

    const handleCreate = () => {
        setEditingItem(null);
        setIsDialogOpen(true);
    };

    const handleEdit = (id: string) => {
        const item = quickSelects.find(q => q.id === id);
        if (item) {
            setEditingItem(item);
            setIsDialogOpen(true);
        }
    };

    const handleSave = (data: any) => {
        if (editingItem) {
            // Update
            setQuickSelects(prev => prev.map(item => item.id === editingItem.id ? { ...item, ...data, templateCount: data.templateIds.length } : item));
        } else {
            // Create
            setQuickSelects(prev => [...prev, { ...data, isSystem: false, isActive: true, templateCount: data.templateIds.length }]);
        }
    };

    const handleToggleStatus = (id: string) => {
        setQuickSelects(prev => prev.map(item => item.id === id ? { ...item, isActive: !item.isActive } : item));
    };

    const handleDelete = (id: string) => {
        if (confirm('¿Estás seguro de eliminar este Quick Select?')) {
            setQuickSelects(prev => prev.filter(item => item.id !== id));
        }
    };

    const activeItems = quickSelects.filter(i => i.isActive);
    const inactiveItems = quickSelects.filter(i => !i.isActive);

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-lg font-semibold text-gray-700">Quick Selects Activos</h2>
                    <p className="text-sm text-gray-500">Estos aparecerán en el paso 2 del onboarding.</p>
                </div>
                <Button onClick={handleCreate}>
                    + Crear Nuevo
                </Button>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {activeItems.map(item => (
                    <QuickSelectCard
                        key={item.id}
                        item={item}
                        onEdit={handleEdit}
                        onToggleStatus={handleToggleStatus}
                        onDelete={handleDelete}
                    />
                ))}
                {activeItems.length === 0 && <p className="text-gray-500 italic">No hay Quick Selects activos.</p>}
            </div>

            {inactiveItems.length > 0 && (
                <div className="pt-8 border-t">
                    <h2 className="text-lg font-semibold text-gray-700 mb-4">Inactivos</h2>
                    <div className="grid grid-cols-1 gap-4 bg-gray-50 p-4 rounded-lg">
                        {inactiveItems.map(item => (
                            <QuickSelectCard
                                key={item.id}
                                item={item}
                                onEdit={handleEdit}
                                onToggleStatus={handleToggleStatus}
                                onDelete={handleDelete}
                            />
                        ))}
                    </div>
                </div>
            )}

            <QuickSelectDialog
                open={isDialogOpen}
                onOpenChange={setIsDialogOpen}
                initialData={editingItem}
                onSave={handleSave}
            />
        </div>
    );
}
