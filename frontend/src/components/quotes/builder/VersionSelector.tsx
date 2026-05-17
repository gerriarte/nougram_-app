
'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';
import { History, Plus } from 'lucide-react';

interface QuoteVersion {
    version: number;
}

interface VersionSelectorProps {
    currentVersion: string; // 'v1', 'v2'
    versions?: QuoteVersion[];
    onSelectVersion?: (version: string) => void;
    onCreateNewVersion?: () => void;
}

function parseVersionLabel(versionLabel: string): number {
    const numeric = Number(versionLabel.replace(/[^0-9]/g, ''));
    return Number.isFinite(numeric) && numeric > 0 ? numeric : 1;
}

export function VersionSelector({ currentVersion, versions, onSelectVersion, onCreateNewVersion }: VersionSelectorProps) {
    const currentNumeric = parseVersionLabel(currentVersion);
    const availableVersions = (versions && versions.length > 0)
        ? versions
        : [{ version: currentNumeric }];

    return (
        <div className="flex items-center gap-2 bg-white p-1 rounded-lg border border-gray-200">
            <div className="flex items-center gap-2 px-2 text-xs font-medium text-gray-500 border-r border-gray-100 pr-3">
                <History size={14} />
                <span>Versiones</span>
            </div>

            <div className="flex items-center gap-1">
                {availableVersions.map((v) => (
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

            {onCreateNewVersion && (
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 ml-1 text-gray-400 hover:text-blue-600"
                    title="Crear nueva versión"
                    onClick={onCreateNewVersion}
                >
                    <Plus size={14} />
                </Button>
            )}
        </div>
    );
}
