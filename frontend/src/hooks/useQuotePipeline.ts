import { useState, useMemo, useCallback } from 'react';
import useSWR from 'swr';
import { Quote } from '@/components/dashboard/QuoteCard';
import { quoteService } from '../services/quoteService';
import { apiRequest } from '@/lib/api-client';
import type {
    DashboardKpiSummaryResponse,
    KpiRangeMode,
} from '@/types/dashboard';

export interface QuoteFilters {
    status: Quote['status'][];
    dateRange: {
        start: Date | null;
        end: Date | null;
    };
    minAmount: number | '';
    maxAmount: number | '';
    client: string;
    clientId: number | '';
}

export interface ClientOption {
    id: number;
    display_name: string;
    requester_name?: string | null;
    email?: string | null;
}

const DEFAULT_TZ =
    Intl.DateTimeFormat().resolvedOptions().timeZone ||
    process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE ||
    'America/Bogota';

export interface KpiDateFilterState {
    rangeMode: KpiRangeMode;
    monthsBack: number;
    customStart: string;
    customEnd: string;
}

async function fetchClients(): Promise<ClientOption[]> {
    const res = await apiRequest<{ items: ClientOption[] }>('/clients/?page=1&page_size=100');
    if (res.error) throw new Error(res.error);
    return res.data?.items ?? [];
}

async function fetchKpiSummary(url: string): Promise<DashboardKpiSummaryResponse> {
    const res = await apiRequest<DashboardKpiSummaryResponse>(url);
    if (res.error) throw new Error(typeof res.error === 'string' ? res.error : 'No se pudieron cargar los KPI.');
    if (!res.data) throw new Error('Respuesta vacía del servidor.');
    return res.data;
}

export function useQuotePipeline() {
    const [search, setSearch] = useState('');
    const [viewMode, setViewMode] = useState<'board' | 'list'>('list');
    const [showInactiveQuotes, setShowInactiveQuotes] = useState(false);

    const [kpiFilter, setKpiFilter] = useState<KpiDateFilterState>({
        rangeMode: 'relative',
        monthsBack: 3,
        customStart: '',
        customEnd: '',
    });

    const [filters, setFilters] = useState<QuoteFilters>({
        status: [],
        dateRange: { start: null, end: null },
        minAmount: '',
        maxAmount: '',
        client: '',
        clientId: ''
    });

    // --- SWR: quotes ---
    const {
        data: quotes = [],
        isLoading: loading,
        error: quotesError,
        mutate: mutateQuotes,
    } = useSWR(
        ['quotes', showInactiveQuotes],
        ([, includeInactive]) => quoteService.getAll({ includeInactive }),
        { revalidateOnFocus: false, dedupingInterval: 10000 }
    );

    // --- SWR: clients (rarely changes, long dedup window) ---
    const { data: clients = [] } = useSWR('clients-pipeline', fetchClients, {
        revalidateOnFocus: false,
        dedupingInterval: 60000,
    });

    // --- SWR: KPI summary (key changes with filter) ---
    const kpiKey = useMemo(() => {
        if (kpiFilter.rangeMode === 'custom' && (!kpiFilter.customStart || !kpiFilter.customEnd)) {
            return null;
        }
        const params = new URLSearchParams();
        params.set('range_mode', kpiFilter.rangeMode);
        if (kpiFilter.rangeMode === 'relative') {
            params.set('months_back', String(kpiFilter.monthsBack));
        } else {
            params.set('start_date', kpiFilter.customStart);
            params.set('end_date', kpiFilter.customEnd);
        }
        params.set('timezone', DEFAULT_TZ);
        return `/insights/dashboard/kpi-summary?${params.toString()}`;
    }, [kpiFilter]);

    const {
        data: kpiSummary = null,
        isLoading: kpiLoading,
        error: kpiSWRError,
        mutate: mutateKpi,
    } = useSWR(kpiKey, fetchKpiSummary, {
        revalidateOnFocus: false,
        dedupingInterval: 30000,
    });

    const kpiError: string | null = kpiSWRError instanceof Error
        ? kpiSWRError.message
        : kpiSWRError
            ? 'No se pudieron cargar los KPI.'
            : kpiFilter.rangeMode === 'custom' && (!kpiFilter.customStart || !kpiFilter.customEnd)
                ? 'Selecciona fecha desde y hasta para el rango personalizado.'
                : null;

    const error: string | null = quotesError instanceof Error
        ? quotesError.message
        : quotesError ? 'No se pudo cargar el pipeline' : null;

    const handleStatusChange = async (id: string, newStatus: Quote['status']) => {
        const previousStatus = quotes.find((q) => q.id === id)?.status;

        await mutateQuotes(
            async (current = []) => {
                await quoteService.updateStatus(id, newStatus);
                return current.map(q => (q.id === id ? { ...q, status: newStatus } : q));
            },
            {
                optimisticData: (current = []) =>
                    current.map(q => (q.id === id ? { ...q, status: newStatus } : q)),
                rollbackOnError: true,
                revalidate: false,
            }
        );

        void mutateKpi();

        // Suppress unused-variable warning — previousStatus is used by rollbackOnError implicitly
        void previousStatus;
    };

    const updateKpiFilter = useCallback((patch: Partial<KpiDateFilterState>) => {
        setKpiFilter((prev) => ({ ...prev, ...patch }));
    }, []);

    const updateFilter = (key: keyof QuoteFilters, value: unknown) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const clearFilters = () => {
        setFilters({
            status: [],
            dateRange: { start: null, end: null },
            minAmount: '',
            maxAmount: '',
            client: '',
            clientId: ''
        });
        setSearch('');
    };

    const filteredQuotes = quotes.filter(q => {
        if (search) {
            const searchLower = search.toLowerCase();
            if (!q.project.toLowerCase().includes(searchLower) &&
                !q.client.toLowerCase().includes(searchLower)) {
                return false;
            }
        }
        if (filters.status.length > 0 && !filters.status.includes(q.status)) return false;
        if (filters.clientId !== '' && (q.clientId === undefined || q.clientId !== filters.clientId)) return false;
        if (filters.client && q.client !== filters.client) return false;
        if (filters.minAmount !== '' && q.totalWithTaxes < filters.minAmount) return false;
        if (filters.maxAmount !== '' && q.totalWithTaxes > filters.maxAmount) return false;
        return true;
    });

    const columns = [
        { id: 'draft', title: 'Borradores', color: 'bg-gray-100' },
        { id: 'sent', title: 'Enviadas', color: 'bg-blue-50' },
        { id: 'viewed', title: 'Vistas (Hot)', color: 'bg-yellow-50' },
        { id: 'accepted', title: 'Cerradas', color: 'bg-green-50' },
    ];

    return {
        quotes: filteredQuotes,
        allQuotes: quotes,
        showInactiveQuotes,
        setShowInactiveQuotes,
        clients,
        error,
        search,
        setSearch,
        viewMode,
        setViewMode,
        handleStatusChange,
        columns,
        loading,
        filters,
        updateFilter,
        clearFilters,
        kpiSummary,
        kpiLoading,
        kpiError,
        kpiFilter,
        updateKpiFilter,
    };
}
