import { useState, useEffect } from 'react';
import { templateService, Template } from '../services/templateService';

export interface QuickSelectData {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    templateIds: string[];
}

const INITIAL_STATE: QuickSelectData = {
    id: '',
    name: '',
    description: '',
    icon: '💼',
    color: '#3B82F6',
    templateIds: []
};

export function useQuickSelect(initialData?: QuickSelectData | null, onSave?: (data: QuickSelectData) => void, onOpenChange?: (open: boolean) => void) {
    const [formData, setFormData] = useState<QuickSelectData>(INITIAL_STATE);
    const [searchTerm, setSearchTerm] = useState('');
    const [availableTemplates, setAvailableTemplates] = useState<Template[]>([]);
    const [filteredTemplates, setFilteredTemplates] = useState<Template[]>([]);

    // Reset or Initialize Form Data
    useEffect(() => {
        if (initialData) {
            setFormData(initialData);
        } else {
            setFormData(INITIAL_STATE);
        }
    }, [initialData]);

    // Load Templates
    useEffect(() => {
        const loadTemplates = async () => {
            const templates = await templateService.getAll();
            setAvailableTemplates(templates);
            setFilteredTemplates(templates);
        };
        loadTemplates();
    }, []);

    // Filter Templates
    useEffect(() => {
        const filtered = availableTemplates.filter(t =>
            t.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setFilteredTemplates(filtered);
    }, [searchTerm, availableTemplates]);

    const handleTemplateToggle = (templateId: string) => {
        setFormData(prev => {
            const newIds = prev.templateIds.includes(templateId)
                ? prev.templateIds.filter(id => id !== templateId)
                : [...prev.templateIds, templateId];
            return { ...prev, templateIds: newIds };
        });
    };

    const updateField = (field: keyof QuickSelectData, value: any) => {
        setFormData(prev => {
            // Special handling for ID generation from name if ID is empty/auto
            if (field === 'id') {
                return { ...prev, id: value.toLowerCase().replace(/\s+/g, '_') };
            }
            return { ...prev, [field]: value };
        });
    };

    const save = () => {
        if (!formData.id || !formData.name || formData.templateIds.length === 0) {
            alert('Por favor completa los campos requeridos y selecciona al menos un template.');
            return;
        }
        if (onSave) onSave(formData);
        if (onOpenChange) onOpenChange(false);
    };

    return {
        formData,
        searchTerm,
        filteredTemplates,
        setSearchTerm,
        updateField,
        handleTemplateToggle,
        save
    };
}
