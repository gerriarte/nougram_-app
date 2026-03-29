
import { Quote } from '@/components/dashboard/QuoteCard';
import { QuoteBuilderState, CalculationSummary, Service, QuoteItem, TaxConfig } from '@/types/quote-builder';
import { apiRequest } from '@/lib/api-client';
import { CreditsRequiredError } from '@/lib/errors';

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
    is_active?: boolean;
    deletion_requested_at?: string | null;
    deletion_requested_by_id?: number | null;
    deletion_request_reason?: string | null;
    notes?: string;
    total_internal_cost?: string | number;
    total_client_price?: string | number;
    total_with_taxes?: string | number;
    total_taxes?: string | number;
    margin_percentage?: string | number;
    target_margin_percentage?: string | number;
    margin?: {
        gross_margin_ratio?: string | number;
        net_margin_ratio?: string | number;
        target_margin_ratio?: string | number;
        tax_burden_ratio?: string | number;
        scale?: string;
    };
    contingency_description?: string | null;
    contingency_type?: 'fixed' | 'percentage' | string | null;
    contingency_value?: string | number | null;
    items?: Array<{
        id?: number;
        service_id: number;
        service_name?: string;
        custom_service_name?: string;
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
        cell_assignment?: {
            id?: number;
            cell_id: number;
            cell_version_id: number;
            occupancy_percentage: string | number;
            duration_months: number;
        } | null;
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
        code?: string;
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
    proposalId?: number;
    proposalMessage?: string;
};

type QuoteEmailApiResponse = {
    success: boolean;
    message: string;
};

type QuoteDeletionApiResponse = {
    success: boolean;
    action: 'deleted' | 'deactivated' | 'already_inactive';
    message: string;
};

/** Parse "Available: X, Required: Y" from backend 402 message for PaywallModal. */
function parseCreditsFromMessage(message?: string): { availableCredits?: number; requiredCredits?: number } {
    const out: { availableCredits?: number; requiredCredits?: number } = {};
    if (!message || typeof message !== 'string') return out;
    const availMatch = message.match(/Available:\s*(\d+)/i);
    const reqMatch = message.match(/Required:\s*(\d+)/i);
    if (availMatch) out.availableCredits = parseInt(availMatch[1], 10);
    if (reqMatch) out.requiredCredits = parseInt(reqMatch[1], 10);
    return out;
}

function toPercent(value?: string | number): number {
    const num = Number(value || 0);
    if (!Number.isFinite(num)) return 0;
    return num <= 1 ? num * 100 : num;
}

function toMarginRatio(value?: string | number): number {
    const num = Number(value ?? 0.35);
    if (!Number.isFinite(num) || num <= 0) return 0.35;
    if (num > 1 && num <= 100) return num / 100;
    if (num > 100) return 0.35;
    return num;
}

function resolveTargetMarginRatio(quote?: ProjectQuoteResponse | null): number {
    const canonical = quote?.margin?.target_margin_ratio;
    if (canonical !== undefined && canonical !== null && canonical !== "") {
        return toMarginRatio(canonical);
    }
    return toMarginRatio(quote?.target_margin_percentage);
}

function toSafeNumber(value?: string | number): number {
    const num = Number(value ?? 0);
    return Number.isFinite(num) ? num : 0;
}

function sumTaxRate(taxes?: Array<{ percentage: string | number }>): number {
    return (taxes || []).reduce((acc, tax) => acc + (Number(tax.percentage) || 0), 0);
}

function resolveProjectTaxes(
    projectDetail?: { taxes?: Array<{ percentage: string | number }> },
    projectListItem?: { taxes?: Array<{ percentage: string | number }> }
): Array<{ percentage: string | number }> {
    return projectDetail?.taxes || projectListItem?.taxes || [];
}

function toRealMarginPercent(
    basePrice: number,
    internalCost: number,
    totalTaxes: number
): number {
    if (!Number.isFinite(basePrice) || basePrice <= 0) return 0;
    const realIncome = basePrice - totalTaxes;
    if (realIncome <= 0) return 0;
    return ((realIncome - internalCost) / realIncome) * 100;
}

function buildFinancialBreakdown(
    quote: Pick<ProjectQuoteResponse, 'total_client_price' | 'total_internal_cost' | 'total_with_taxes' | 'total_taxes'> | null | undefined,
    taxes: Array<{ percentage: string | number }>
) {
    const baseAmount = toSafeNumber(quote?.total_client_price);
    const internalCost = toSafeNumber(quote?.total_internal_cost);
    const taxAmountFromQuote = toSafeNumber(quote?.total_taxes);
    const billedFromQuote = toSafeNumber(quote?.total_with_taxes);
    const taxRateFromProject = sumTaxRate(taxes);
    const taxAmountFromRates = baseAmount > 0 && taxRateFromProject > 0
        ? (baseAmount * taxRateFromProject) / 100
        : 0;
    const hasExplicitTaxFromQuote = taxAmountFromQuote > 0;
    const hasBilledDeltaFromQuote = billedFromQuote > 0 && Math.abs(billedFromQuote - baseAmount) > 0.01;
    const taxAmount = hasExplicitTaxFromQuote
        ? taxAmountFromQuote
        : hasBilledDeltaFromQuote
            ? Math.max(0, billedFromQuote - baseAmount)
            : taxAmountFromRates;
    // If quote totals come without tax breakdown but project taxes exist, derive billed from base + rates.
    const billedAmount = (billedFromQuote > 0 && (hasExplicitTaxFromQuote || hasBilledDeltaFromQuote))
        ? billedFromQuote
        : baseAmount + taxAmount;
    const taxRate = baseAmount > 0 ? (taxAmount / baseAmount) * 100 : taxRateFromProject;
    const realIncome = Math.max(0, baseAmount - taxAmount);
    const profitAmount = realIncome - internalCost;
    const margin = Number(toRealMarginPercent(baseAmount, internalCost, taxAmount).toFixed(2));

    return {
        baseAmount,
        internalCost,
        taxRate,
        taxAmount,
        billedAmount,
        realIncome,
        profitAmount,
        margin,
    };
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
    const customServiceName = typeof item.serviceName === 'string' ? item.serviceName.trim() : '';
    const assignment = item.teamAssignment;
    return {
        service_id: item.serviceId,
        custom_service_name: customServiceName || undefined,
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
        cell_assignment: assignment
            ? {
                cell_id: assignment.cellId,
                cell_version_id: assignment.cellVersionId,
                occupancy_percentage: assignment.occupancyPercentage,
                duration_months: assignment.durationMonths || 1,
            }
            : undefined,
    };
}

function buildProjectUpdatePayload(data: Partial<QuoteBuilderState>) {
    const payload: Record<string, unknown> = {};

    if (typeof data.projectName === 'string' && data.projectName.trim().length > 0) {
        payload.name = data.projectName.trim();
    }
    if (typeof data.clientName === 'string' && data.clientName.trim().length > 0) {
        payload.client_name = data.clientName.trim();
    }
    if (typeof data.clientEmail === 'string') {
        payload.client_email = data.clientEmail.trim() || null;
    }
    if (data.clientId !== undefined) {
        payload.client_id = data.clientId === null ? null : data.clientId;
    }
    if (typeof data.currency === 'string' && data.currency.length > 0) {
        payload.currency = data.currency;
    }
    if (Array.isArray(data.selectedTaxIds)) {
        payload.tax_ids = data.selectedTaxIds;
    }

    return payload;
}

const DEFAULT_SERVICE_SEEDS = [
    { name: 'Desarrollo Frontend', pricing_type: 'hourly', default_margin_target: 0.4 },
    { name: 'Setup Inicial', pricing_type: 'fixed', default_margin_target: 0.35, fixed_price: 1000000 },
    { name: 'Mantenimiento Mensual', pricing_type: 'recurring', default_margin_target: 0.4, recurring_price: 500000, billing_frequency: 'monthly' },
];

let serviceSeedInFlight: Promise<Service[]> | null = null;
let servicesCache: Service[] | null = null;
let servicesFetchInFlight: Promise<Service[]> | null = null;

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
    const breakdown = buildFinancialBreakdown(latestQuote, project.taxes || []);
    return {
        id: String(project.id),
        project: project.name,
        client: project.client_name,
        clientId: project.client_id ?? undefined,
        totalWithTaxes: breakdown.billedAmount,
        totalClientPrice: breakdown.baseAmount,
        totalTaxes: breakdown.taxAmount,
        taxRate: breakdown.taxRate,
        internalCost: breakdown.internalCost,
        profitAmount: breakdown.profitAmount,
        currency: project.currency || 'USD',
        margin: breakdown.margin,
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
                if (!latestQuote) {
                    return null;
                }
                const detailedQuote = await getQuoteDetailForProject(project.id, latestQuote?.id);
                const baseQuote = detailedQuote || latestQuote;
                const projectTaxes = resolveProjectTaxes(projectDetail, project);
                const breakdown = buildFinancialBreakdown(baseQuote, projectTaxes);
                const version = Number(latestQuote?.version || 1);

                return {
                    id: String(project.id),
                    project: projectDetail.name || project.name,
                    client: projectDetail.client_name || project.client_name,
                    clientId: projectDetail.client_id ?? project.client_id ?? undefined,
                    totalWithTaxes: breakdown.billedAmount,
                    totalClientPrice: breakdown.baseAmount,
                    totalTaxes: breakdown.taxAmount,
                    taxRate: breakdown.taxRate,
                    internalCost: breakdown.internalCost,
                    profitAmount: breakdown.profitAmount,
                    currency: projectDetail.currency || project.currency || 'USD',
                    margin: breakdown.margin,
                    quoteId: latestQuote?.id,
                    version,
                    status: statusMap[project.status] || 'draft',
                    viewedCount: 0,
                    downloadCount: 0,
                } satisfies Quote;
            })
        );

        return mapped.filter((item): item is Quote => item !== null);
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
        const quote = buildQuoteCardFromProject(projectResponse.data, detailedQuote || latestQuote);
        return {
            ...quote,
            quoteId: latestQuote?.id,
        };
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
                target_margin_percentage: typeof data.targetMargin === 'number' ? toMarginRatio(data.targetMargin) : undefined,
                contingency_description: data.contingency ? (data.contingency.description || '') : null,
                contingency_type: data.contingency ? data.contingency.type : null,
                contingency_value: data.contingency ? (data.contingency.value ?? 0) : null,
                revisions_included: 2,
                allow_low_margin: Boolean(data.allowLowMargin),
            }),
        });

        if (response.error || !response.data?.project_id) {
            if (response.statusCode === 402) {
                const errorMessage = response.error || 'Creditos insuficientes para crear la cotizacion';
                const { availableCredits, requiredCredits } = parseCreditsFromMessage(response.error);
                throw new CreditsRequiredError(
                    errorMessage,
                    availableCredits,
                    requiredCredits ?? 1
                );
            }
            throw new Error(response.error || 'No se pudo crear el proyecto/cotización');
        }

        return String(response.data.project_id);
    },

    update: async (id: string, data: Partial<QuoteBuilderState> & { amount?: number, marginPercentage?: number }): Promise<void> => {
        const latestQuote = await quoteService.getLatestQuoteForProject(id);
        if (!latestQuote) {
            throw new Error('No existe una cotización para actualizar');
        }

        const projectUpdatePayload = buildProjectUpdatePayload(data);
        if (Object.keys(projectUpdatePayload).length > 0) {
            const projectUpdateResponse = await apiRequest(`/projects/${id}`, {
                method: 'PUT',
                body: JSON.stringify(projectUpdatePayload),
            });
            if (projectUpdateResponse.error) {
                throw new Error(projectUpdateResponse.error);
            }
        }

        const payloadItems = (data.items || []).map((item: QuoteItem) => mapQuoteItemToApi(item));

        const response = await apiRequest(
            `/projects/${id}/quotes/${latestQuote.id}`,
            {
                method: 'PUT',
                body: JSON.stringify({
                    items: payloadItems,
                    target_margin_percentage: typeof data.targetMargin === 'number' ? toMarginRatio(data.targetMargin) : undefined,
                    contingency_description: data.contingency ? (data.contingency.description || '') : null,
                    contingency_type: data.contingency ? data.contingency.type : null,
                    contingency_value: data.contingency ? (data.contingency.value ?? 0) : null,
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

        const projectUpdatePayload = buildProjectUpdatePayload(data);
        if (Object.keys(projectUpdatePayload).length > 0) {
            const projectUpdateResponse = await apiRequest(`/projects/${id}`, {
                method: 'PUT',
                body: JSON.stringify(projectUpdatePayload),
            });
            if (projectUpdateResponse.error) {
                throw new Error(projectUpdateResponse.error);
            }
        }

        const payloadItems = (data.items || []).map((item: QuoteItem) => mapQuoteItemToApi(item));

        const response = await apiRequest<{ id: number; project_id: number; version: number }>(
            `/projects/${id}/quotes/${latestQuote.id}/new-version`,
            {
                method: 'POST',
                body: JSON.stringify({
                    items: payloadItems,
                    target_margin_percentage: typeof data.targetMargin === 'number' ? toMarginRatio(data.targetMargin) : undefined,
                    contingency_description: data.contingency ? (data.contingency.description || '') : null,
                    contingency_type: data.contingency ? data.contingency.type : null,
                    contingency_value: data.contingency ? (data.contingency.value ?? 0) : null,
                    allow_low_margin: Boolean(data.allowLowMargin),
                }),
            }
        );

        if (response.error) {
            if (response.statusCode === 402) {
                const { availableCredits, requiredCredits } = parseCreditsFromMessage(response.error);
                throw new CreditsRequiredError(
                    response.error,
                    availableCredits,
                    requiredCredits ?? 1
                );
            }
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

    sendEmail: async (id: string, data: SendEmailPayload, quoteId?: number): Promise<QuoteEmailApiResponse> => {
        let targetQuoteId = quoteId;
        if (!targetQuoteId) {
            const quotesResponse = await apiRequest<ProjectQuoteResponse[]>(`/projects/${id}/quotes`);
            if (quotesResponse.error) {
                throw new Error(quotesResponse.error);
            }
            const quotes = quotesResponse.data || [];
            const latestQuote = quotes.sort((a, b) => (b.version || 0) - (a.version || 0))[0];
            if (!latestQuote) {
                throw new Error('No existe una cotización para enviar');
            }
            targetQuoteId = latestQuote.id;
        }

        const response = await apiRequest<QuoteEmailApiResponse>(`/projects/${id}/quotes/${targetQuoteId}/send-email`, {
            method: 'POST',
            body: JSON.stringify({
                to_email: data?.to || '',
                subject: data?.subject,
                message: data?.message,
                proposal_id: data?.proposalId,
                proposal_message: data?.proposalMessage,
                include_pdf: Boolean(data?.includePdf ?? true),
                include_docx: false,
                cc: [],
                bcc: [],
            }),
        });

        if (response.error) {
            throw new Error(response.error);
        }
        if (!response.data?.success) {
            throw new Error(response.data?.message || 'No se pudo enviar la cotización');
        }
        return response.data;
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
    deleteOrRequestQuoteDeletion: async (projectId: string, quoteId: number): Promise<QuoteDeletionApiResponse> => {
        const response = await apiRequest<QuoteDeletionApiResponse>(`/projects/${projectId}/quotes/${quoteId}`, {
            method: 'DELETE',
        });
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo procesar la eliminacion de la cotizacion');
        }
        return response.data;
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
        targetMargin: number;
        selectedTaxIds: number[];
        selectedTaxes: TaxConfig[];
        contingency?: QuoteBuilderState['contingency'];
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
                serviceName: item.custom_service_name || item.service_name || service?.name || `Servicio ${item.service_id}`,
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
                teamAssignment: item.cell_assignment
                    ? {
                        id: item.cell_assignment.id,
                        cellId: Number(item.cell_assignment.cell_id),
                        cellVersionId: Number(item.cell_assignment.cell_version_id),
                        occupancyPercentage: Number(item.cell_assignment.occupancy_percentage || 0),
                        durationMonths: Number(item.cell_assignment.duration_months || 1),
                    }
                    : undefined,
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
            targetMargin: resolveTargetMarginRatio(detail),
            selectedTaxIds: (projectResponse.data.taxes || []).map((tax) => Number(tax.id)).filter((id) => Number.isFinite(id)),
            selectedTaxes: (projectResponse.data.taxes || []).map((tax) => ({
                id: Number(tax.id),
                name: tax.name,
                percentage: Number(tax.percentage || 0),
                code: tax.code,
                isActive: true,
            })),
            contingency: (detail?.contingency_type && detail?.contingency_value !== null && detail?.contingency_value !== undefined)
                ? {
                    description: String(detail.contingency_description || ''),
                    type: detail.contingency_type === 'fixed' ? 'fixed' : 'percentage',
                    value: Number(detail.contingency_value || 0),
                }
                : undefined,
            items,
        };
    },
    // Public Proposal System
    generatePublicLink: async (id: string, daysValid: number = 30): Promise<string> => {
        void id;
        void daysValid;
        throw new Error('Generación de enlaces públicos requiere endpoint backend aún no disponible.');
    },

    getQuoteByToken: async (token: string): Promise<Quote | null> => {
        void token;
        return null;
    },

    acceptQuote: async (token: string): Promise<boolean> => {
        void token;
        throw new Error('Aceptación de propuesta pública requiere endpoint backend aún no disponible.');
    },

    rejectQuote: async (token: string, reason?: string): Promise<boolean> => {
        void token;
        void reason;
        throw new Error('Rechazo de propuesta pública requiere endpoint backend aún no disponible.');
    }
};
