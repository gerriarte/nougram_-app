
import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { useQuickSelect, QuickSelectData } from '@/hooks/useQuickSelect';

interface QuickSelectDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    initialData?: QuickSelectData | null;
    onSave: (data: QuickSelectData) => void;
}

export function QuickSelectDialog({ open, onOpenChange, initialData, onSave }: QuickSelectDialogProps) {
    const {
        formData,
        searchTerm,
        filteredTemplates,
        setSearchTerm,
        updateField,
        handleTemplateToggle,
        save
    } = useQuickSelect(initialData, onSave, onOpenChange);

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>
                        {initialData ? 'Editar Quick Select' : 'Crear Quick Select Personalizado'}
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-6 py-4">
                    {/* Basic Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="qs-id">Clave Única (ID) *</Label>
                            <Input
                                id="qs-id"
                                value={formData.id}
                                onChange={e => {
                                    // Manually handle logic that was inside the component before, now delegated to hook or kept simple here if UI specific
                                    // The hook handles the transformation logic if we pass the raw value? 
                                    // Actually, let's keep the UI logic simple and generic updateField
                                    // But wait, the hook has specific logic for ID. Let's use the hook's updateField carefully.
                                    updateField('id', e.target.value);
                                }}
                                placeholder="ej: arquitectos"
                                disabled={!!initialData} // ID not editable after creation usually
                            />
                            <p className="text-xs text-gray-500">Identificador único del sistema.</p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="qs-name">Nombre para Mostrar *</Label>
                            <Input
                                id="qs-name"
                                value={formData.name}
                                onChange={e => updateField('name', e.target.value)}
                                placeholder="ej: Arquitectos"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="qs-desc">Descripción</Label>
                        <Input
                            id="qs-desc"
                            value={formData.description}
                            onChange={e => updateField('description', e.target.value)}
                            placeholder="Descripción breve..."
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="qs-icon">Icono (Emoji)</Label>
                            <Input
                                id="qs-icon"
                                value={formData.icon}
                                onChange={e => updateField('icon', e.target.value)}
                                className="text-center text-2xl"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="qs-color">Color</Label>
                            <div className="flex gap-2">
                                <Input
                                    id="qs-color"
                                    type="color"
                                    value={formData.color}
                                    onChange={e => updateField('color', e.target.value)}
                                    className="w-12 h-10 p-1"
                                />
                                <Input
                                    value={formData.color}
                                    onChange={e => updateField('color', e.target.value)}
                                />
                            </div>
                        </div>
                    </div>

                    <hr />

                    {/* Template Selection */}
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <Label>Templates a Pre-seleccionar * ({formData.templateIds.length})</Label>
                            <Input
                                placeholder="Buscar template..."
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                                className="max-w-xs h-8"
                            />
                        </div>

                        <div className="border rounded-md max-h-60 overflow-y-auto bg-gray-50 p-2 grid grid-cols-1 gap-2">
                            {filteredTemplates.map(template => (
                                <div
                                    key={template.id}
                                    className={`flex items-center p-2 rounded-md border cursor-pointer transition-colors ${formData.templateIds.includes(template.id)
                                        ? 'bg-blue-50 border-blue-500'
                                        : 'bg-white border-gray-200 hover:bg-gray-100'
                                        }`}
                                    onClick={() => handleTemplateToggle(template.id)}
                                >
                                    <input
                                        type="checkbox"
                                        checked={formData.templateIds.includes(template.id)}
                                        onChange={() => { }} // Handled by div click
                                        className="mr-3 h-4 w-4 text-blue-600 rounded"
                                    />
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-900">{template.name}</p>
                                        <p className="text-xs text-gray-500">${template.amount} {template.currency}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="secondary" onClick={() => onOpenChange(false)}>Cancelar</Button>
                    <Button onClick={save}>Guardar Quick Select</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
