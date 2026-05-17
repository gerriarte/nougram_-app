'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Calculator, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';

export function BreakEvenNav() {
    const pathname = usePathname();

    const tabs = [
        {
            name: 'Dashboard',
            href: '/analytics/break-even',
            icon: LayoutDashboard
        },
        {
            name: 'Simulador',
            href: '/analytics/break-even/scenarios',
            icon: Calculator
        },
        {
            name: 'Proyección',
            href: '/analytics/break-even/projection',
            icon: TrendingUp
        }
    ];

    return (
        <div className="flex justify-center mb-8">
            <div className="bg-gray-100/50 p-1 rounded-full inline-flex border border-gray-200">
                {tabs.map((tab) => {
                    const isActive = pathname === tab.href;

                    return (
                        <Link
                            key={tab.href}
                            href={tab.href}
                            className={`relative px-6 py-2 rounded-full text-sm font-medium transition-colors ${isActive ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            {isActive && (
                                <motion.div
                                    layoutId="break-even-nav-pill"
                                    className="absolute inset-0 bg-white rounded-full shadow-sm border border-gray-200/50"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                />
                            )}
                            <div className="relative flex items-center gap-2 z-10">
                                <tab.icon size={16} />
                                {tab.name}
                            </div>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
}
