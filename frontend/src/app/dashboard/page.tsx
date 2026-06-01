
'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { QuotePipeline } from '@/components/dashboard/QuotePipeline';
import { BusinessHealthSection } from '@/components/dashboard/BusinessHealthSection';
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
                        <h1 className="text-[22px] sm:text-[28px] font-bold text-gray-900 tracking-tight">Dashboard comercial</h1>
                        <p className="text-[13.5px] text-gray-500 mt-1">Vista general de tus oportunidades de negocio.</p>
                    </div>
                    <Button
                        className="bg-gray-900 hover:bg-gray-700 text-white rounded-xl h-11 px-5 font-semibold active:scale-95 transition-all flex items-center justify-center gap-2 w-full md:w-auto shrink-0"
                        onClick={() => router.push(CANONICAL_NEW_QUOTE_PATH)}
                    >
                        <Plus size={17} strokeWidth={2.5} />
                        Nueva cotización
                    </Button>
                </div>

                <BusinessHealthSection />

                <QuotePipeline />
            </motion.div>
        </AdminLayout>
    );
}
