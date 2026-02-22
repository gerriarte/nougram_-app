
// Types for Quotes & Dashboard

export type QuoteStatus = 'Draft' | 'Sent' | 'Viewed' | 'Accepted' | 'Rejected' | 'Expired';

export interface Quote {
    id: string;
    projectName: string;
    clientName: string;
    version: number;
    amount: number;
    currency: string;
    marginPercentage: number; // 0-100

    status: QuoteStatus;

    // Dates
    createdAt: string; // ISO
    sentAt?: string;
    expiresAt?: string;
    lastViewedAt?: string;

    // Tracking
    viewCount: number;
    downloadCount: number;

    // Alerts
    requiresAttention?: boolean;
    alertMessage?: string;
}

export interface DashboardMetrics {
    totalQuoted: number;     // Total value of all quotes
    pipelineValue: number;   // Value of active quotes (Sent/Viewed)
    winRate: number;         // Percentage
    avgMargin: number;       // Percentage

    // Granular Reports
    sentCount: number;
    sentValue: number;
    wonCount: number;
    wonValue: number;
    lostCount: number;

    // Financials
    netIncome: number;       // Profit from Won deals
}
