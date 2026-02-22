import { useState, useEffect } from 'react';
import { Quote } from '@/components/dashboard/QuoteCard';
import { quoteService } from '../services/quoteService';
import { apiRequest } from '@/lib/api-client';


export interface QuoteFilters {
    status: Quote['status'][];
    dateRange: {
        start: Date | null;
        end: Date | null;
    };
    minAmount: number | '';
    maxAmount: number | '';
    client: string;
}

export interface PipelineMetrics {
    totalQuoted: number;
    pipelineValue: number;
    winRate: number;
    avgMargin: number;
    sentCount: number;
    wonCount: number;
    lostCount: number;
}

export function useQuotePipeline() {
    const [quotes, setQuotes] = useState<Quote[]>([]);
    const [search, setSearch] = useState('');
    const [viewMode, setViewMode] = useState<'board' | 'list'>('list');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [metrics, setMetrics] = useState<PipelineMetrics>({
        totalQuoted: 0,
        pipelineValue: 0,
        winRate: 0,
        avgMargin: 0,
        sentCount: 0,
        wonCount: 0,
        lostCount: 0,
    });

    // Advanced Filters State
    const [filters, setFilters] = useState<QuoteFilters>({
        status: [],
        dateRange: { start: null, end: null },
        minAmount: '',
        maxAmount: '',
        client: ''
    });

    useEffect(() => {
        const loadQuotes = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await quoteService.getAll();
                setQuotes(data);

                const dashboardResponse = await apiRequest<{
                    total_revenue: number;
                    average_margin: number;
                    conversion_rate: number;
                    projects_by_status: Record<string, number>;
                }>('/insights/dashboard');

                // Fallback metrics are always derived from loaded quotes.
                const fallbackTotal = data.reduce((sum, q) => sum + q.amount, 0);
                const fallbackPipeline = data
                    .filter((q) => q.status === 'sent' || q.status === 'viewed')
                    .reduce((sum, q) => sum + q.amount, 0);
                const fallbackClosed = data.filter((q) => q.status === 'accepted' || q.status === 'rejected').length;
                const fallbackWon = data.filter((q) => q.status === 'accepted').length;
                const fallbackWinRate = fallbackClosed > 0 ? (fallbackWon / fallbackClosed) * 100 : 0;
                const fallbackAvgMargin = data.length > 0
                    ? data.reduce((sum, q) => sum + q.margin, 0) / data.length
                    : 0;
                const fallbackSent = data.filter((q) => q.status === 'sent' || q.status === 'viewed').length;
                const fallbackLost = data.filter((q) => q.status === 'rejected').length;

                if (dashboardResponse.error || !dashboardResponse.data) {
                    setMetrics({
                        totalQuoted: fallbackTotal,
                        pipelineValue: fallbackPipeline,
                        winRate: fallbackWinRate,
                        avgMargin: fallbackAvgMargin,
                        sentCount: fallbackSent,
                        wonCount: fallbackWon,
                        lostCount: fallbackLost,
                    });
                    return;
                }

                const byStatus = dashboardResponse.data.projects_by_status || {};
                const avgMarginRaw = Number(dashboardResponse.data.average_margin || fallbackAvgMargin);
                const avgMargin = avgMarginRaw <= 1 ? avgMarginRaw * 100 : avgMarginRaw;
                const sentCount = Number(byStatus.Sent || 0);
                const wonCount = Number(byStatus.Won || 0);
                const lostCount = Number(byStatus.Lost || 0);
                const draftCount = Number(byStatus.Draft || 0);

                setMetrics({
                    totalQuoted: Number(dashboardResponse.data.total_revenue || fallbackTotal),
                    pipelineValue: fallbackPipeline,
                    winRate: Number(dashboardResponse.data.conversion_rate || fallbackWinRate),
                    avgMargin,
                    sentCount: sentCount + draftCount,
                    wonCount,
                    lostCount,
                });
            } catch (error) {
                console.error("Failed to load quotes", error);
                setQuotes([]);
                setError(error instanceof Error ? error.message : "No se pudo cargar el pipeline");
            } finally {
                setLoading(false);
            }
        };
        loadQuotes();
    }, []);

    const handleStatusChange = async (id: string, newStatus: Quote['status']) => {
        // Optimistic update
        setQuotes(prevQuotes => prevQuotes.map(quote =>
            quote.id === id ? { ...quote, status: newStatus } : quote
        ));

        try {
            await quoteService.updateStatus(id, newStatus);
        } catch (error) {
            console.error("Failed to update status", error);
            // Revert on failure could be implemented here
        }
    };

    const updateFilter = (key: keyof QuoteFilters, value: any) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const clearFilters = () => {
        setFilters({
            status: [],
            dateRange: { start: null, end: null },
            minAmount: '',
            maxAmount: '',
            client: ''
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

        // 3. Client Filter
        if (filters.client && q.client !== filters.client) {
            return false;
        }

        // 4. Amount Range
        if (filters.minAmount !== '' && q.amount < filters.minAmount) return false;
        if (filters.maxAmount !== '' && q.amount > filters.maxAmount) return false;

        // 5. Date Filter (Mock: assuming 'sentAt' is a parseable date or we use created_at)
        // For this mock simplified version, we'll skip complex date parsing unless 'sentAt' format is standardized.
        // Assuming 'sentAt' is "Hace 2d", this is hard to filter without real dates.
        // TODO: Implement Date Filter when backend provides ISO dates.

        return true;
    });

    const columns = [
        { id: 'draft', title: 'Borradores', color: 'bg-gray-100' },
        { id: 'sent', title: 'Enviadas', color: 'bg-blue-50' },
        { id: 'viewed', title: 'Vistas (Hot)', color: 'bg-yellow-50' },
        { id: 'accepted', title: 'Cerradas', color: 'bg-green-50' },
    ];

    return {
        quotes: filteredQuotes, // Return filtered directly or raw depending on need. Usually UI wants filtered.
        allQuotes: quotes,
        error,
        search,
        setSearch,
        viewMode,
        setViewMode,
        handleStatusChange,
        columns,
        loading,
        metrics,
        filters,
        updateFilter,
        clearFilters
    };
}
