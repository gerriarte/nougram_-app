
'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';
import { History, GitBranch, Plus } from 'lucide-react';

interface QuoteVersion {
    version: number;
    createdAt: string;
    totalAmount: number;
    isCurrent: boolean;
}

interface VersionSelectorProps {
    currentVersion: string; // 'v1', 'v2'
    onSelectVersion?: (version: string) => void;
    onCreateNewVersion?: () => void;
}

const MOCK_VERSIONS: QuoteVersion[] = [
    { version: 1, createdAt: 'Hace 2 días', totalAmount: 15000000, isCurrent: false },
    { version: 2, createdAt: 'Hace 1 hora', totalAmount: 16500000, isCurrent: true },
];

export function VersionSelector({ currentVersion, onSelectVersion, onCreateNewVersion }: VersionSelectorProps) {
    // In a real implementation, we would fetch versions based on the project ID from context

    return (
        <div className="flex items-center gap-2 bg-white p-1 rounded-lg border border-gray-200">
            <div className="flex items-center gap-2 px-2 text-xs font-medium text-gray-500 border-r border-gray-100 pr-3">
                <History size={14} />
                <span>Versiones</span>
            </div>

            <div className="flex items-center gap-1">
                {MOCK_VERSIONS.map((v) => (
                    <button
                        key={v.version}
                        onClick={() => onSelectVersion?.(`v${v.version}`)}
                        className={`
                            px-2 py-1 rounded text-xs font-bold transition-all
                            ${currentVersion === `v${v.version}`
                                ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-100'
                                : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'}
                        `}
                    >
                        v{v.version}
                    </button>
                ))}
            </div>

            <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 ml-1 text-gray-400 hover:text-blue-600"
                title="Crear nueva versión"
                onClick={onCreateNewVersion}
            >
                <Plus size={14} />
            </Button>
        </div>
    );
}
