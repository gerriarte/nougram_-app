
'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { QuotePipeline } from '@/components/dashboard/QuotePipeline';
import { Button } from '@/components/ui/Button';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { Plus } from 'lucide-react';
import { CANONICAL_NEW_QUOTE_PATH } from '@/lib/mobile-routes';
import { motion } from 'framer-motion';

export default function DashboardPage() {
    const router = useRouter();

    return (
        <AdminLayout>
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-10"
            >
                <div className="flex flex-col md:flex-row justify-between items-stretch md:items-end gap-6">
                    <div className="min-w-0">
                        <h1 className="text-2xl sm:text-4xl font-bold text-gray-900 tracking-tight">Dashboard Comercial</h1>
                        <p className="text-system-gray font-medium text-base sm:text-lg mt-2">Vista general de tus oportunidades de negocio.</p>
                    </div>
                    <Button
                        className="bg-blue-600 hover:bg-blue-700 text-white rounded-2xl h-12 px-6 font-bold shadow-lg shadow-blue-200 active:scale-95 transition-all flex items-center justify-center gap-2 w-full md:w-auto shrink-0"
                        onClick={() => router.push(CANONICAL_NEW_QUOTE_PATH)}
                    >
                        <Plus size={20} strokeWidth={2.5} />
                        Nueva Cotización
                    </Button>
                </div>

                <QuotePipeline />
            </motion.div>
        </AdminLayout>
    );
}
