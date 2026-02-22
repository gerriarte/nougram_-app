
export type PlanTier = 'free' | 'starter' | 'professional' | 'enterprise';
export type BillingInterval = 'monthly' | 'yearly';
export type SubscriptionStatus = 'active' | 'trialing' | 'past_due' | 'canceled' | 'incomplete' | 'incomplete_expired';
export type InvoiceStatus = 'paid' | 'pending' | 'failed' | 'void';

export interface Plan {
    id: PlanTier;
    name: string;
    description: string;
    priceMonthly: number;
    priceYearly: number;
    currency: string;
    features: {
        creditsPerMonth: number | 'unlimited';
        maxUsers: number | 'unlimited';
        maxProjects: number | 'unlimited';
        maxServices: number | 'unlimited';
        maxTeamMembers: number | 'unlimited';
        supportLevel: 'community' | 'email' | 'priority' | 'dedicated';
    };
    isPopular?: boolean;
}

export interface CreditUsage {
    available: number;
    usedThisMonth: number;
    usedTotal: number;
    limitMonthly: number | null; // null for unlimited
    nextResetDate: string; // ISO Date
}

export interface PaymentMethod {
    id: string;
    type: 'card';
    brand: 'visa' | 'mastercard' | 'amex' | 'discover' | 'unknown';
    last4: string;
    expiryMonth: number;
    expiryYear: number;
}

export interface Subscription {
    id: string;
    planId: PlanTier;
    status: SubscriptionStatus;
    interval: BillingInterval;
    currentPeriodStart: string; // ISO Date
    currentPeriodEnd: string; // ISO Date
    cancelAtPeriodEnd: boolean;
    paymentMethod?: PaymentMethod;
    trialEndsAt?: string | null;
}

export interface Transaction {
    id: string;
    invoiceNumber: string;
    amount: number;
    currency: string;
    status: InvoiceStatus;
    date: string; // Payment or creation date
    dueDate?: string;
    pdfUrl?: string;
    planName: string;
    periodStart: string;
    periodEnd: string;
}

export interface CreditTransaction {
    id: string;
    action: string;
    credits: number;
    timestamp: string;
}
