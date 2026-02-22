
import React, { useState } from 'react';
import { PricingTable } from './PricingTable';
import { CreditTracker } from './CreditTracker';
import { SubscriptionStatus } from './SubscriptionStatus';
import { TransactionHistory } from './TransactionHistory';
import { Plan, Subscription, CreditUsage } from '@/types/billing';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'; // Assuming standard Shadcn-like tabs
import { Wallet, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

// --- MOCK DATA ---
const MOCK_CURRENT_PLAN: Plan = {
    id: 'starter',
    name: 'Starter',
    description: 'Ideal para equipos pequeños',
    priceMonthly: 29.99,
    priceYearly: 299.99,
    currency: 'USD',
    features: {
        creditsPerMonth: 100,
        maxUsers: 5,
        maxProjects: 25,
        maxServices: 50,
        maxTeamMembers: 10,
        supportLevel: 'email'
    }
};

const MOCK_SUBSCRIPTION: Subscription = {
    id: 'sub_123',
    planId: 'starter',
    status: 'active',
    interval: 'monthly',
    currentPeriodStart: '2026-01-15',
    currentPeriodEnd: '2026-02-15',
    cancelAtPeriodEnd: false,
    paymentMethod: {
        id: 'pm_123',
        type: 'card',
        brand: 'visa',
        last4: '4242',
        expiryMonth: 12,
        expiryYear: 2025
    }
};

const MOCK_USAGE: CreditUsage = {
    available: 20,
    usedThisMonth: 80,
    usedTotal: 450,
    limitMonthly: 100,
    nextResetDate: '2026-02-15'
};

export function BillingDashboard() {
    const [activeTab, setActiveTab] = useState('overview');

    const handleUpgrade = () => {
        setActiveTab('plans');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div className="min-h-screen bg-[#F5F5F7] text-[#1D1D1F]">
            {/* Apple-style Blur Header */}
            <div className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard/quotes" className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-black">
                            <ArrowLeft size={20} />
                        </Link>
                        <h1 className="text-xl font-semibold -tracking-[0.01em] flex items-center gap-3">
                            <div className="h-8 w-8 rounded-full bg-black text-white flex items-center justify-center shadow-lg shadow-black/10">
                                <Wallet size={16} strokeWidth={2.5} />
                            </div>
                            <span className="opacity-90">Facturación y Créditos</span>
                        </h1>
                    </div>
                </div>
            </div>

            <div className="max-w-5xl mx-auto px-6 py-12">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-10">

                    {/* IOS Segmented Control Style Tabs */}
                    <div className="flex justify-center mb-8">
                        <TabsList className="bg-gray-200/50 p-1 rounded-full inline-flex relative shadow-inner">
                            {['overview', 'plans', 'invoices'].map((tab) => (
                                <TabsTrigger
                                    key={tab}
                                    value={tab}
                                    className="rounded-full px-8 py-2 text-sm font-medium transition-all duration-300 data-[state=active]:bg-white data-[state=active]:text-black data-[state=active]:shadow-sm text-gray-500 hover:text-gray-900 capitalize"
                                >
                                    {tab === 'overview' ? 'Resumen' : tab === 'plans' ? 'Planes' : 'Facturas'}
                                </TabsTrigger>
                            ))}
                        </TabsList>
                    </div>

                    <TabsContent value="overview" className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out">
                        {/* 1. Credit Tracker */}
                        <CreditTracker
                            usage={MOCK_USAGE}
                            onUpgrade={handleUpgrade}
                            onTopUp={() => alert('Top-up coming soon!')}
                        />

                        {/* 2. Subscription Details */}
                        <SubscriptionStatus
                            subscription={MOCK_SUBSCRIPTION}
                            currentPlan={MOCK_CURRENT_PLAN}
                            onChangePlan={handleUpgrade}
                        />
                    </TabsContent>

                    <TabsContent value="plans" className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <PricingTable
                            currentPlanId={MOCK_CURRENT_PLAN.id}
                            onSelectPlan={(id) => alert(`Selected plan: ${id}`)}
                        />
                    </TabsContent>

                    <TabsContent value="invoices" className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <TransactionHistory />
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
}
