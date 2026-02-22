import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils'; // Assuming exist

interface MarginIndicatorProps {
    margin: number; // 0-100
    className?: string;
}

export function MarginIndicator({ margin, className }: MarginIndicatorProps) {
    let colorClass = "text-red-500";
    let bgClass = "bg-red-500";
    let text = "Bajo";

    if (margin >= 40) {
        colorClass = "text-green-500";
        bgClass = "bg-green-500";
        text = "Excelente";
    } else if (margin >= 25) {
        colorClass = "text-blue-500";
        bgClass = "bg-blue-500";
        text = "Saludable";
    } else if (margin >= 15) {
        colorClass = "text-yellow-500";
        bgClass = "bg-yellow-500";
        text = "Aceptable";
    }

    return (
        <div className={cn("flex flex-col gap-1", className)}>
            <div className="flex justify-between items-end">
                <span className="text-sm font-medium text-gray-500">Margen</span>
                <div className="text-right">
                    <span className={cn("text-2xl font-bold", colorClass)}>{margin}%</span>
                    <span className="text-xs text-gray-400 ml-2">({text})</span>
                </div>
            </div>

            <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(margin, 100)}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className={cn("h-full rounded-full", bgClass)}
                />
            </div>
        </div>
    );
}
