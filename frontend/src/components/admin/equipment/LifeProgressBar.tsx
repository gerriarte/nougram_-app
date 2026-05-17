
'use client';

import React from 'react';

/**
 * Visual indicator for asset life
 * Green (0-50%) -> Yellow (50-80%) -> Red (80-100%)
 */
export function LifeProgressBar({ percentage }: { percentage: number }) {
    let color = 'bg-green-500';
    if (percentage > 80) color = 'bg-red-500';
    else if (percentage > 50) color = 'bg-yellow-500';

    return (
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
                className={`h-full ${color} transition-all duration-1000 ease-out`}
                style={{ width: `${Math.min(100, percentage)}%` }}
            />
        </div>
    );
}
