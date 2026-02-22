
import React from 'react';
import { Card, CardContent, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface QuickSelect {
    id: string;
    name: string;
    description: string;
    icon: string;
    isSystem: boolean;
    isActive: boolean;
    templateCount: number;
    color?: string;
}

interface QuickSelectCardProps {
    item: QuickSelect;
    onEdit: (id: string) => void;
    onToggleStatus: (id: string) => void;
    onDelete?: (id: string) => void;
}

export function QuickSelectCard({ item, onEdit, onToggleStatus, onDelete }: QuickSelectCardProps) {
    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardContent className="p-4 flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                <div className="flex items-start gap-3">
                    <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl flex-shrink-0"
                        style={{ backgroundColor: item.color || '#E5E7EB', color: item.color ? 'white' : 'inherit' }}
                    >
                        {item.icon}
                    </div>
                    <div>
                        <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-gray-900">{item.name}</h3>
                            <Badge variant={item.isSystem ? 'default' : 'info'}>
                                {item.isSystem ? 'Sistema' : 'Personalizado'}
                            </Badge>
                            {!item.isActive && (
                                <Badge variant="default">Inactivo</Badge>
                            )}
                        </div>
                        <CardDescription className="line-clamp-1 mt-1">
                            {item.description}
                        </CardDescription>
                        <p className="text-xs text-gray-500 mt-1">
                            {item.templateCount} templates pre-seleccionados
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2 w-full md:w-auto mt-2 md:mt-0">
                    {!item.isSystem && (
                        <Button variant="secondary" size="sm" onClick={() => onEdit(item.id)}>
                            Editar
                        </Button>
                    )}

                    <Button
                        variant={item.isActive ? 'secondary' : 'primary'}
                        size="sm"
                        onClick={() => onToggleStatus(item.id)}
                        className={!item.isActive ? 'bg-green-600 hover:bg-green-700' : ''}
                    >
                        {item.isActive ? 'Desactivar' : 'Activar'}
                    </Button>

                    {!item.isSystem && onDelete && (
                        <Button variant="destructive" size="sm" onClick={() => onDelete(item.id)}>
                            🗑️
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
