import { useState, useEffect, useCallback } from 'react';
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

export function useQuotePipeline() {
    const [quotes, setQuotes] = useState<Quote[]>([]);
    const [clients, setClients] = useState<ClientOption[]>([]);
    const [search, setSearch] = useState('');
    const [viewMode, setViewMode] = useState<'board' | 'list'>('list');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [kpiFilter, setKpiFilter] = useState<KpiDateFilterState>({
        rangeMode: 'relative',
        monthsBack: 3,
        customStart: '',
        customEnd: '',
    });
    const [kpiSummary, setKpiSummary] = useState<DashboardKpiSummaryResponse | null>(null);
    const [kpiLoading, setKpiLoading] = useState(true);
    const [kpiError, setKpiError] = useState<string | null>(null);
    const [showInactiveQuotes, setShowInactiveQuotes] = useState(false);

    // Advanced Filters State
    const [filters, setFilters] = useState<QuoteFilters>({
        status: [],
        dateRange: { start: null, end: null },
        minAmount: '',
        maxAmount: '',
        client: '',
        clientId: ''
    });

    useEffect(() => {
        const loadClients = async () => {
            const res = await apiRequest<{ items: ClientOption[] }>('/clients/?page=1&page_size=100');
            if (res.data?.items) setClients(res.data.items);
        };
        loadClients();
    }, []);

    const loadKpiSummary = useCallback(async () => {
        setKpiLoading(true);
        setKpiError(null);
        try {
            const params = new URLSearchParams();
            params.set('range_mode', kpiFilter.rangeMode);
            if (kpiFilter.rangeMode === 'relative') {
                params.set('months_back', String(kpiFilter.monthsBack));
            } else {
                if (!kpiFilter.customStart || !kpiFilter.customEnd) {
                    setKpiSummary(null);
                    setKpiError('Selecciona fecha desde y hasta para el rango personalizado.');
                    return;
                }
                params.set('start_date', kpiFilter.customStart);
                params.set('end_date', kpiFilter.customEnd);
            }
            params.set('timezone', DEFAULT_TZ);

            const res = await apiRequest<DashboardKpiSummaryResponse>(
                `/insights/dashboard/kpi-summary?${params.toString()}`
            );
            if (res.error) {
                setKpiSummary(null);
                setKpiError(typeof res.error === 'string' ? res.error : 'No se pudieron cargar los KPI.');
                return;
            }
            if (!res.data) {
                setKpiSummary(null);
                setKpiError('Respuesta vacía del servidor.');
                return;
            }
            setKpiSummary(res.data);
        } catch (e) {
            setKpiSummary(null);
            setKpiError(e instanceof Error ? e.message : 'No se pudieron cargar los KPI.');
        } finally {
            setKpiLoading(false);
        }
    }, [kpiFilter]);

    useEffect(() => {
        void loadKpiSummary();
    }, [loadKpiSummary]);

    useEffect(() => {
        const loadQuotes = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await quoteService.getAll({ includeInactive: showInactiveQuotes });
                setQuotes(data);
            } catch (err) {
                console.error("Failed to load quotes", err);
                setQuotes([]);
                setError(err instanceof Error ? err.message : "No se pudo cargar el pipeline");
            } finally {
                setLoading(false);
            }
        };
        loadQuotes();
    }, [showInactiveQuotes]);

    const updateKpiFilter = useCallback((patch: Partial<KpiDateFilterState>) => {
        setKpiFilter((prev) => ({ ...prev, ...patch }));
    }, []);

    const isCountedForDashboard = (status: Quote['status']): boolean => status !== 'draft';
    const isWonForDashboard = (status: Quote['status']): boolean => status === 'accepted';

    const handleStatusChange = async (id: string, newStatus: Quote['status']) => {
        const previousQuote = quotes.find((q) => q.id === id);
        const previousStatus = previousQuote?.status;
        const previousKpi = kpiSummary;

        // Optimistic update
        setQuotes(prevQuotes => prevQuotes.map(quote =>
            quote.id === id ? { ...quote, status: newStatus } : quote
        ));

        // Optimistic KPI update so widgets react immediately.
        if (previousQuote && previousKpi && previousStatus && previousStatus !== newStatus) {
            const fromCounted = isCountedForDashboard(previousStatus);
            const toCounted = isCountedForDashboard(newStatus);
            const fromWon = isWonForDashboard(previousStatus);
            const toWon = isWonForDashboard(newStatus);

            const billed = Number(previousQuote.totalWithTaxes || 0);
            const operationalCost = Number(previousQuote.internalCost || 0);
            const netMargin = billed - operationalCost;

            setKpiSummary((prev) => {
                if (!prev) return prev;

                const deltaCount = toCounted ? (fromCounted ? 0 : 1) : (fromCounted ? -1 : 0);
                const deltaWon = toWon ? (fromWon ? 0 : 1) : (fromWon ? -1 : 0);
                const deltaFactor = toCounted ? (fromCounted ? 0 : 1) : (fromCounted ? -1 : 0);

                return {
                    ...prev,
                    kpis: {
                        ...prev.kpis,
                        totalCotizadoConImpuestos: prev.kpis.totalCotizadoConImpuestos + (billed * deltaFactor),
                        costoTotalOperacional: prev.kpis.costoTotalOperacional + (operationalCost * deltaFactor),
                        margenNetoTotal: prev.kpis.margenNetoTotal + (netMargin * deltaFactor),
                        numeroPropuestasRealizadas: Math.max(0, prev.kpis.numeroPropuestasRealizadas + deltaCount),
                        numeroPropuestasGanadas: Math.max(0, prev.kpis.numeroPropuestasGanadas + deltaWon),
                    },
                };
            });
        }

        try {
            await quoteService.updateStatus(id, newStatus);
            // Reconcile with backend source-of-truth after optimistic paint.
            void loadKpiSummary();
        } catch (err) {
            console.error("Failed to update status", err);
            // Revert optimistic changes on failure.
            if (previousStatus) {
                setQuotes(prevQuotes => prevQuotes.map(quote =>
                    quote.id === id ? { ...quote, status: previousStatus } : quote
                ));
            }
            if (previousKpi) {
                setKpiSummary(previousKpi);
            }
        }
    };

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
        // 1. Text Search
        if (search) {
            const searchLower = search.toLowerCase();
            const matchesProject = q.project.toLowerCase().includes(searchLower);
            const matchesClient = q.client.toLowerCase().includes(searchLower);
            if (!matchesProject && !matchesClient) return false;
        }

        // 2. Status Filter
        if (filters.status.length > 0 && !filters.status.includes(q.status)) {
            return false;
        }

        // 3. Client Filter (by master client_id)
        if (filters.clientId !== '' && (q.clientId === undefined || q.clientId !== filters.clientId)) {
            return false;
        }
        if (filters.client && q.client !== filters.client) {
            return false;
        }

        // 4. Amount Range
        if (filters.minAmount !== '' && q.totalWithTaxes < filters.minAmount) return false;
        if (filters.maxAmount !== '' && q.totalWithTaxes > filters.maxAmount) return false;

        // 5. Date Filter
        // TODO: Implement when pipeline cards receive ISO dates from backend.

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
