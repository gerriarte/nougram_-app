
import { Quote } from '@/components/dashboard/QuoteCard';
import { QuoteBuilderState, CalculationSummary, Service, QuoteItem } from '@/types/quote-builder';
import { apiRequest } from '@/lib/api-client';

type ProjectListItem = {
    id: number;
    name: string;
    client_id?: number | null;
    client_name: string;
    status: 'Draft' | 'Sent' | 'Won' | 'Lost';
    currency?: string;
    taxes?: Array<{
        id: number;
        name: string;
        percentage: string | number;
    }>;
};

type ProjectListResponse = {
    items: ProjectListItem[];
    total: number;
};

type ProjectQuoteResponse = {
    id: number;
    version?: number;
    notes?: string;
    total_internal_cost?: string | number;
    total_client_price?: number;
    margin_percentage?: number;
    items?: Array<{
        id?: number;
        service_id: number;
        service_name?: string;
        estimated_hours?: number;
        pricing_type?: string;
        fixed_price?: string | number;
        quantity?: string | number;
        recurring_price?: string | number;
        billing_frequency?: 'monthly' | 'annual' | string;
        project_value?: string | number;
        allocations?: Array<{
            id?: number;
            team_member_id: number;
            hours: string | number;
            role?: string;
            start_date?: string;
            end_date?: string;
        }>;
        internal_cost?: string | number;
        client_price?: string | number;
        margin_percentage?: string | number;
    }>;
};

type ProjectResponse = {
    id: number;
    name: string;
    client_id?: number | null;
    client_name: string;
    client_email?: string;
    currency?: string;
    status?: string;
    taxes?: Array<{
        id: number;
        name: string;
        percentage: string | number;
    }>;
};

type ServiceListResponse = {
    items: Array<{
        id: number;
        name: string;
        description?: string;
        default_margin_target?: string | number;
        pricing_type?: string;
        is_active?: boolean;
    }>;
    total: number;
};

type SendEmailPayload = {
    to?: string;
    subject?: string;
    message?: string;
    includePdf?: boolean;
};

function toPercent(value?: string | number): number {
    const num = Number(value || 0);
    if (!Number.isFinite(num)) return 0;
    return num <= 1 ? num * 100 : num;
}

function sumTaxRate(taxes?: Array<{ percentage: string | number }>): number {
    return (taxes || []).reduce((acc, tax) => acc + (Number(tax.percentage) || 0), 0);
}

function toInvoiceAmount(basePrice?: string | number, taxes?: Array<{ percentage: string | number }>): number {
    const price = Number(basePrice || 0);
    if (!Number.isFinite(price) || price <= 0) return 0;
    const taxRate = sumTaxRate(taxes);
    return price * (1 + taxRate / 100);
}

function toRealMarginPercent(
    basePrice?: string | number,
    internalCost?: string | number,
    taxes?: Array<{ percentage: string | number }>
): number {
    const price = Number(basePrice || 0);
    const cost = Number(internalCost || 0);
    if (!Number.isFinite(price) || price <= 0) return 0;
    const taxRate = sumTaxRate(taxes);
    const taxesAmount = price * (taxRate / 100);
    const realIncome = price - taxesAmount;
    if (realIncome <= 0) return 0;
    return ((realIncome - cost) / realIncome) * 100;
}

function getAllocatedHours(item: QuoteItem): number {
    return (item.allocations || []).reduce((sum, alloc) => sum + (Number(alloc.hours) || 0), 0);
}

function resolveEstimatedHours(item: QuoteItem): number {
    const allocated = getAllocatedHours(item);
    if (allocated > 0) {
        if (item.pricingType === 'recurring') {
            const duration = Math.max(1, Number(item.durationMonths || item.quantity || 1));
            return allocated * duration;
        }
        return allocated;
    }
    return Number(item.estimatedHours || 0);
}

function resolveQuantity(item: QuoteItem): number {
    if (item.pricingType === 'recurring') {
        return Math.max(1, Number(item.durationMonths || item.quantity || 1));
    }
    return Math.max(1, Number(item.quantity || 1));
}

function resolveRecurringPrice(item: QuoteItem): number | undefined {
    if (item.pricingType !== 'recurring') return item.recurringPrice;
    if (typeof item.recurringPrice === 'number' && item.recurringPrice > 0) return item.recurringPrice;

    const duration = Math.max(1, Number(item.durationMonths || item.quantity || 1));
    const total = (typeof item.manualPrice === 'number' && item.manualPrice > 0)
        ? item.manualPrice
        : item.clientPrice;
    if (typeof total !== 'number' || total <= 0) return undefined;
    return Number((total / duration).toFixed(2));
}

function mapQuoteItemToApi(item: QuoteItem) {
    return {
        service_id: item.serviceId,
        estimated_hours: resolveEstimatedHours(item),
        pricing_type: item.pricingType,
        fixed_price: item.fixedPrice,
        quantity: resolveQuantity(item),
        recurring_price: resolveRecurringPrice(item),
        billing_frequency: item.billingFrequency,
        project_value: item.projectValue,
        allocations: (item.allocations || []).map((alloc) => ({
            team_member_id: alloc.teamMemberId,
            hours: alloc.hours,
            role: alloc.role,
            start_date: alloc.startDate,
            end_date: alloc.endDate,
        })),
    };
}

const DEFAULT_SERVICE_SEEDS = [
    { name: 'Desarrollo Frontend', pricing_type: 'hourly', default_margin_target: 0.4 },
    { name: 'Setup Inicial', pricing_type: 'fixed', default_margin_target: 0.35, fixed_price: 1000000 },
    { name: 'Mantenimiento Mensual', pricing_type: 'recurring', default_margin_target: 0.4, recurring_price: 500000, billing_frequency: 'monthly' },
];

let serviceSeedInFlight: Promise<Service[]> | null = null;
let servicesCache: Service[] | null = null;
let servicesFetchInFlight: Promise<Service[]> | null = null;

// Mock Data
const MOCK_QUOTES: Quote[] = [
    { id: '1', project: 'App E-commerce', client: 'TechCorp', amount: 25000, currency: 'USD', margin: 42, version: 2, history: [{ version: 1, amount: 22000, date: 'Hace 5d' }], status: 'sent', sentAt: 'Hace 2d', viewedCount: 0, downloadCount: 0, publicToken: 'demo-proposal', tokenExpiresAt: new Date(Date.now() + 86400000 * 30).toISOString() },
    { id: '2', project: 'Landing Page', client: 'StartupX', amount: 8000, currency: 'USD', margin: 22, version: 1, status: 'viewed', sentAt: 'Hace 1d', viewedCount: 5, downloadCount: 2 },
    { id: '3', project: 'Branding', client: 'DesignCo', amount: 12000, currency: 'USD', margin: 35, version: 1, status: 'accepted', sentAt: 'Hace 3d', viewedCount: 3, downloadCount: 1 },
    { id: '4', project: 'SEO Audit', client: 'MarketFit', amount: 4500, currency: 'USD', margin: 8, version: 1, status: 'draft', viewedCount: 0, downloadCount: 0 },
    { id: '5', project: 'Web Redesign', client: 'OldSchool', amount: 15000, currency: 'USD', margin: 28, version: 3, history: [{ version: 1, amount: 12000, date: 'Hace 1w' }, { version: 2, amount: 14000, date: 'Hace 2d' }], status: 'viewed', sentAt: 'Hace 5h', viewedCount: 12, downloadCount: 4 },
];

function mapProjectStatusToQuoteStatus(status?: string): Quote['status'] {
    switch (status) {
        case 'Sent':
            return 'sent';
        case 'Won':
            return 'accepted';
        case 'Lost':
            return 'rejected';
        case 'Draft':
        default:
            return 'draft';
    }
}

function buildQuoteCardFromProject(
    project: Pick<ProjectResponse, 'id' | 'name' | 'client_id' | 'client_name' | 'currency' | 'status'> & {
        taxes?: Array<{ percentage: string | number }>;
    },
    latestQuote: ProjectQuoteResponse | null
): Quote {
    const amount = Number(toInvoiceAmount(latestQuote?.total_client_price || 0, project.taxes || []));
    const margin = Number(
        toRealMarginPercent(
            latestQuote?.total_client_price || 0,
            latestQuote?.total_internal_cost || 0,
            project.taxes || []
        ).toFixed(2)
    );
    return {
        id: String(project.id),
        project: project.name,
        client: project.client_name,
        clientId: project.client_id ?? undefined,
        amount,
        currency: project.currency || 'USD',
        margin,
        version: Number(latestQuote?.version || 1),
        status: mapProjectStatusToQuoteStatus(project.status),
        viewedCount: 0,
        downloadCount: 0,
    };
}

async function getQuoteDetailForProject(projectId: number, quoteId?: number): Promise<ProjectQuoteResponse | null> {
    if (!quoteId) return null;
    const detailResponse = await apiRequest<ProjectQuoteResponse>(`/projects/${projectId}/quotes/${quoteId}`);
    if (detailResponse.error || !detailResponse.data) return null;
    return detailResponse.data;
}

export const quoteService = {
    getAll: async (): Promise<Quote[]> => {
        const projectResponse = await apiRequest<ProjectListResponse>('/projects/');
        if (projectResponse.error) {
            throw new Error(projectResponse.error);
        }
        if (!projectResponse.data?.items) {
            return [];
        }

        const statusMap: Record<ProjectListItem['status'], Quote['status']> = {
            Draft: 'draft',
            Sent: 'sent',
            Won: 'accepted',
            Lost: 'rejected',
        };

        const mapped = await Promise.all(
            projectResponse.data.items.map(async (project) => {
                const projectDetailResponse = await apiRequest<ProjectResponse>(`/projects/${project.id}`);
                const projectDetail = projectDetailResponse.data || project;
                const quotesResponse = await apiRequest<ProjectQuoteResponse[]>(
                    `/projects/${project.id}/quotes`
                );
                if (quotesResponse.error) {
                    throw new Error(quotesResponse.error);
                }
                const quotes = quotesResponse.data || [];
                const latestQuote =
                    quotes.sort((a, b) => (b.version || 0) - (a.version || 0))[0] || null;
                const detailedQuote = await getQuoteDetailForProject(project.id, latestQuote?.id);
                const baseQuote = detailedQuote || latestQuote;

                const amount = Number(toInvoiceAmount(baseQuote?.total_client_price || 0, projectDetail.taxes || []));
                const margin = Number(
                    toRealMarginPercent(
                        baseQuote?.total_client_price || 0,
                        baseQuote?.total_internal_cost || 0,
                        projectDetail.taxes || []
                    ).toFixed(2)
                );
                const version = Number(latestQuote?.version || 1);

                return {
                    id: String(project.id),
                    project: projectDetail.name || project.name,
                    client: projectDetail.client_name || project.client_name,
                    clientId: projectDetail.client_id ?? project.client_id ?? undefined,
                    amount,
                    currency: projectDetail.currency || project.currency || 'USD',
                    margin,
                    version,
                    status: statusMap[project.status] || 'draft',
                    viewedCount: 0,
                    downloadCount: 0,
                } satisfies Quote;
            })
        );

        return mapped;
    },

    getById: async (id: string): Promise<Quote | null> => {
        const byProjectId = await quoteService.getByProjectId(id);
        if (byProjectId) return byProjectId;

        const quotes = await quoteService.getAll();
        const quote = quotes.find((q) => q.id === id);
        return quote || null;
    },
    getByProjectId: async (projectId: string): Promise<Quote | null> => {
        const projectResponse = await apiRequest<ProjectResponse>(`/projects/${projectId}`);
        if (projectResponse.error) {
            throw new Error(projectResponse.error);
        }
        if (!projectResponse.data) return null;
        const latestQuote = await quoteService.getLatestQuoteForProject(projectId);
        const detailedQuote = await getQuoteDetailForProject(Number(projectId), latestQuote?.id);
        return buildQuoteCardFromProject(projectResponse.data, detailedQuote || latestQuote);
    },
    getProjectClientEmail: async (projectId: string): Promise<string> => {
        const projectResponse = await apiRequest<ProjectResponse>(`/projects/${projectId}`);
        if (projectResponse.error || !projectResponse.data) return '';
        return projectResponse.data.client_email || '';
    },

    create: async (data: Partial<QuoteBuilderState> & { amount: number, marginPercentage: number }): Promise<string> => {
        const quoteItems = (data.items || []).map((item: QuoteItem) => mapQuoteItemToApi(item));

        const response = await apiRequest<{
            id: number;
            project_id: number;
            version: number;
        }>('/projects/', {
            method: 'POST',
            body: JSON.stringify({
                name: data.projectName || 'Proyecto sin nombre',
                client_id: data.clientId ?? undefined,
                client_name: data.clientName || 'Cliente',
                client_email: data.clientEmail || undefined,
                currency: data.currency || 'COP',
                tax_ids: data.selectedTaxIds || [],
                quote_items: quoteItems,
                target_margin_percentage: typeof data.targetMargin === 'number' ? data.targetMargin : undefined,
                revisions_included: 2,
                allow_low_margin: Boolean(data.allowLowMargin),
            }),
        });

        if (response.error || !response.data?.project_id) {
            throw new Error(response.error || 'No se pudo crear el proyecto/cotización');
        }

        return String(response.data.project_id);
    },

    update: async (id: string, data: Partial<QuoteBuilderState> & { amount?: number, marginPercentage?: number }): Promise<void> => {
        const latestQuote = await quoteService.getLatestQuoteForProject(id);
        if (!latestQuote) {
            throw new Error('No existe una cotización para actualizar');
        }

        const payloadItems = (data.items || []).map((item: QuoteItem) => mapQuoteItemToApi(item));

        const response = await apiRequest(
            `/projects/${id}/quotes/${latestQuote.id}`,
            {
                method: 'PUT',
                body: JSON.stringify({
                    items: payloadItems,
                    target_margin_percentage: typeof data.targetMargin === 'number' ? data.targetMargin : undefined,
                    allow_low_margin: Boolean(data.allowLowMargin),
                }),
            }
        );

        if (response.error) {
            throw new Error(response.error);
        }
    },

    createVersion: async (id: string, data: Partial<QuoteBuilderState> & { amount: number, marginPercentage: number }): Promise<void> => {
        const latestQuote = await quoteService.getLatestQuoteForProject(id);
        if (!latestQuote) {
            throw new Error('No existe una cotización para versionar');
        }

        const payloadItems = (data.items || []).map((item: QuoteItem) => mapQuoteItemToApi(item));

        const response = await apiRequest(
            `/projects/${id}/quotes/${latestQuote.id}/new-version`,
            {
                method: 'POST',
                body: JSON.stringify({
                    items: payloadItems,
                    target_margin_percentage: typeof data.targetMargin === 'number' ? data.targetMargin : undefined,
                    allow_low_margin: Boolean(data.allowLowMargin),
                }),
            }
        );

        if (response.error) {
            throw new Error(response.error);
        }
    },

    updateStatus: async (id: string, newStatus: Quote['status']): Promise<void> => {
        const backendStatusMap: Record<Quote['status'], ProjectListItem['status']> = {
            draft: 'Draft',
            sent: 'Sent',
            viewed: 'Sent',
            accepted: 'Won',
            rejected: 'Lost',
            expired: 'Lost',
        };

        const response = await apiRequest(`/projects/${id}`, {
            method: 'PUT',
            body: JSON.stringify({
                status: backendStatusMap[newStatus],
            }),
        });

        if (response.error) {
            throw new Error(response.error);
        }
    },

    // Server-side calculation simulation
    calculate: async (): Promise<CalculationSummary> => {
        // This returns the same structure as the context calculates, useful for server-side verification
        // For now we assume client-side context does the heavy lifting for "Real-time"
        return {} as CalculationSummary;
    },

    sendEmail: async (id: string, data: SendEmailPayload): Promise<void> => {
        const quotesResponse = await apiRequest<ProjectQuoteResponse[]>(`/projects/${id}/quotes`);
        if (quotesResponse.error) {
            throw new Error(quotesResponse.error);
        }
        const quotes = quotesResponse.data || [];
        const latestQuote = quotes.sort((a, b) => (b.version || 0) - (a.version || 0))[0];

        if (!latestQuote) {
            throw new Error('No existe una cotización para enviar');
        }

        const response = await apiRequest(`/projects/${id}/quotes/${latestQuote.id}/send-email`, {
            method: 'POST',
            body: JSON.stringify({
                to_email: data?.to || '',
                subject: data?.subject,
                message: data?.message,
                include_pdf: Boolean(data?.includePdf ?? true),
                include_docx: false,
                cc: [],
                bcc: [],
            }),
        });

        if (response.error) {
            throw new Error(response.error);
        }
    },
    setProjectStatus: async (projectId: string, status: 'Draft' | 'Sent' | 'Won' | 'Lost'): Promise<void> => {
        const response = await apiRequest(`/projects/${projectId}`, {
            method: 'PUT',
            body: JSON.stringify({ status }),
        });
        if (response.error) {
            throw new Error(response.error);
        }
    },
    getLatestQuoteForProject: async (projectId: string): Promise<ProjectQuoteResponse | null> => {
        const quotesResponse = await apiRequest<ProjectQuoteResponse[]>(`/projects/${projectId}/quotes`);
        const quotes = quotesResponse.data || [];
        if (!quotes.length) return null;
        return quotes.sort((a, b) => (b.version || 0) - (a.version || 0))[0];
    },
    getAvailableServices: async (forceRefresh = false): Promise<Service[]> => {
        if (!forceRefresh && servicesCache && servicesCache.length > 0) {
            return servicesCache;
        }

        if (!forceRefresh && servicesFetchInFlight) {
            return servicesFetchInFlight;
        }

        const mapServices = (items: ServiceListResponse['items']) =>
            items
                .filter((service) => service.is_active !== false)
                .map((service) => ({
                    id: service.id,
                    name: service.name,
                    description: service.description,
                    pricingType: (service.pricing_type as Service['pricingType']) || 'hourly',
                    defaultMarginTarget: Number(service.default_margin_target || 0.4),
                    isActive: Boolean(service.is_active ?? true),
                }));
        servicesFetchInFlight = (async () => {
            const response = await apiRequest<ServiceListResponse>('/services/');
            if (response.error) {
                throw new Error(response.error);
            }

            const currentItems = response.data?.items || [];
            if (currentItems.length > 0) {
                const mapped = mapServices(currentItems);
                servicesCache = mapped;
                return mapped;
            }

            if (!serviceSeedInFlight) {
                serviceSeedInFlight = (async () => {
                    // Auto-seed base services for brand-new organizations.
                    for (const seed of DEFAULT_SERVICE_SEEDS) {
                        await apiRequest('/services/', {
                            method: 'POST',
                            body: JSON.stringify(seed),
                        });
                    }

                    const refreshed = await apiRequest<ServiceListResponse>('/services/');
                    if (refreshed.error || !refreshed.data?.items?.length) {
                        throw new Error(refreshed.error || 'No hay servicios disponibles para cotizar');
                    }
                    const mapped = mapServices(refreshed.data.items);
                    servicesCache = mapped;
                    return mapped;
                })().finally(() => {
                    serviceSeedInFlight = null;
                });
            }

            return serviceSeedInFlight;
        })().finally(() => {
            servicesFetchInFlight = null;
        });

        return servicesFetchInFlight;
    },
    getBuilderData: async (projectId: string): Promise<{
        id: string;
        version: number;
        projectName: string;
        clientId?: number | null;
        clientName: string;
        clientEmail: string;
        clientCompany?: string;
        clientRequester?: string;
        currency: 'COP' | 'USD';
        items: QuoteItem[];
    } | null> => {
        const projectResponse = await apiRequest<ProjectResponse>(`/projects/${projectId}`);
        if (projectResponse.error || !projectResponse.data) return null;

        const latestQuote = await quoteService.getLatestQuoteForProject(projectId);
        if (!latestQuote) return null;

        const detailResponse = await apiRequest<ProjectQuoteResponse>(
            `/projects/${projectId}/quotes/${latestQuote.id}`
        );
        const detail = detailResponse.data;
        const services = await quoteService.getAvailableServices();
        const serviceMap = new Map(services.map((s) => [s.id, s]));
        const items: QuoteItem[] = (detail?.items || []).map((item) => {
            const service = serviceMap.get(item.service_id);
            const resolvedPricingType = (item.pricing_type || service?.pricingType || 'hourly') as QuoteItem['pricingType'];
            const fixedPrice = Number(item.fixed_price || 0);
            const quantity = Number(item.quantity || 1);
            const recurringPrice = Number(item.recurring_price || 0);
            const projectValue = Number(item.project_value || 0);
            return {
                id: String(item.id),
                serviceId: item.service_id,
                serviceName: item.service_name || service?.name || `Servicio ${item.service_id}`,
                pricingType: resolvedPricingType,
                estimatedHours: Number(item.estimated_hours || 0),
                fixedPrice: resolvedPricingType === 'fixed' ? fixedPrice : undefined,
                quantity,
                recurringPrice: resolvedPricingType === 'recurring' ? recurringPrice : undefined,
                billingFrequency: item.billing_frequency as QuoteItem['billingFrequency'],
                durationMonths: resolvedPricingType === 'recurring' ? quantity : undefined,
                projectValue: resolvedPricingType === 'project_value' ? projectValue : undefined,
                allocations: (item.allocations || []).map((alloc) => ({
                    id: String(alloc.id || crypto.randomUUID()),
                    teamMemberId: Number(alloc.team_member_id),
                    hours: Number(alloc.hours || 0),
                    role: alloc.role,
                    startDate: alloc.start_date,
                    endDate: alloc.end_date,
                })).filter((alloc) => Number.isFinite(alloc.teamMemberId) && Number.isFinite(alloc.hours) && alloc.hours > 0),
                internalCost: Number(item.internal_cost || 0),
                clientPrice: Number(item.client_price || 0),
                marginPercentage: toPercent(item.margin_percentage || 0),
            };
        });

        return {
            id: String(projectResponse.data.id),
            version: Number(detail?.version || latestQuote.version || 1),
            projectName: projectResponse.data.name,
            clientId: projectResponse.data.client_id ?? undefined,
            clientName: projectResponse.data.client_name,
            clientEmail: projectResponse.data.client_email || '',
            clientCompany: projectResponse.data.client_name,
            clientRequester: '',
            currency: (projectResponse.data.currency as 'COP' | 'USD') || 'COP',
            items,
        };
    },
    // Public Proposal System
    generatePublicLink: async (id: string, daysValid: number = 30): Promise<string> => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const idx = MOCK_QUOTES.findIndex(q => q.id === id);
                if (idx !== -1) {
                    const token = crypto.randomUUID();
                    const expiresAt = new Date();
                    expiresAt.setDate(expiresAt.getDate() + daysValid);

                    MOCK_QUOTES[idx] = {
                        ...MOCK_QUOTES[idx],
                        publicToken: token,
                        tokenExpiresAt: expiresAt.toISOString()
                    };
                    resolve(token);
                } else {
                    resolve('');
                }
            }, 300);
        });
    },

    getQuoteByToken: async (token: string): Promise<Quote | null> => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const quote = MOCK_QUOTES.find(q => q.publicToken === token);
                if (!quote) {
                    resolve(null);
                    return;
                }

                // Check expiration
                if (quote.tokenExpiresAt && new Date(quote.tokenExpiresAt) < new Date()) {
                    resolve(null); // Or throw error 'expired'
                    return;
                }

                // Increment view count
                quote.viewedCount += 1;
                quote.lastViewedAt = new Date().toISOString();
                if (quote.status === 'sent') {
                    quote.status = 'viewed';
                }

                resolve(quote);
            }, 400);
        });
    },

    acceptQuote: async (token: string): Promise<boolean> => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const idx = MOCK_QUOTES.findIndex(q => q.publicToken === token);
                if (idx !== -1) {
                    MOCK_QUOTES[idx].status = 'accepted';
                    // In a real app, trigger email notification to Admin
                    console.log(`Quote ${MOCK_QUOTES[idx].id} ACCEPTED by client`);
                    resolve(true);
                } else {
                    resolve(false);
                }
            }, 500);
        });
    },

    rejectQuote: async (token: string, reason?: string): Promise<boolean> => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const idx = MOCK_QUOTES.findIndex(q => q.publicToken === token);
                if (idx !== -1) {
                    MOCK_QUOTES[idx].status = 'rejected';
                    console.log(`Quote ${MOCK_QUOTES[idx].id} REJECTED by client. Reason: ${reason}`);
                    resolve(true);
                } else {
                    resolve(false);
                }
            }, 500);
        });
    }
};
