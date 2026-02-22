
'use client';

import { QuotePipeline } from '@/components/dashboard/QuotePipeline';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';

export default function QuotesDashboardPage() {
    return (
        <AdminLayout>
            <QuotePipeline />
        </AdminLayout>
    );
}
