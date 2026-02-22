import React from 'react';
import { motion } from 'framer-motion';
import { Input } from '@/components/ui/Input'; // Assuming exist
import { Label } from '@/components/ui/Label'; // Assuming exist

interface ResourceSliderProps {
    label: string;
    value: number;
    onChange: (value: number) => void;
    min?: number;
    max?: number;
    unit?: string;
}

export function ResourceSlider({ label, value, onChange, min = 0, max = 200, unit = "h" }: ResourceSliderProps) {
    return (
        <div className="space-y-3">
            <div className="flex justify-between">
                <Label className="text-gray-700 font-medium">{label}</Label>
                <div className="flex items-center gap-2">
                    <Input
                        type="number"
                        value={value}
                        onChange={(e) => onChange(Number(e.target.value))}
                        className="w-16 h-8 text-right p-1"
                    />
                    <span className="text-sm text-gray-500">{unit}</span>
                </div>
            </div>

            <div className="relative group">
                <input
                    type="range"
                    min={min}
                    max={max}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
            </div>
        </div>
    );
}
