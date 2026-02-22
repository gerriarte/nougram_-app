
import React, { useState } from 'react';
import { Check, Star, Zap, Shield, HelpCircle, ArrowRight } from 'lucide-react';
import { Plan, PlanTier, BillingInterval } from '@/types/billing';
import { Button } from '@/components/ui/Button';

// Mock Plans Data based on requirements
const PLANS: Plan[] = [
    {
        id: 'free',
        name: 'Free',
        description: 'Ideal para probar Nougram.',
        priceMonthly: 0,
        priceYearly: 0,
        currency: 'USD',
        features: {
            creditsPerMonth: 10,
            maxUsers: 1,
            maxProjects: 5,
            maxServices: 10,
            maxTeamMembers: 3,
            supportLevel: 'community'
        }
    },
    {
        id: 'starter',
        name: 'Starter',
        description: 'Todo lo necesario para equipos pequeños.',
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
    },
    {
        id: 'professional',
        name: 'Professional',
        description: 'Potencia real para agencias en crecimiento.',
        priceMonthly: 99.99,
        priceYearly: 999.99,
        currency: 'USD',
        isPopular: true,
        features: {
            creditsPerMonth: 500,
            maxUsers: 20,
            maxProjects: 100,
            maxServices: 200,
            maxTeamMembers: 50,
            supportLevel: 'priority'
        }
    },
    {
        id: 'enterprise',
        name: 'Enterprise',
        description: 'Soluciones a medida para grandes organizaciones.',
        priceMonthly: 0,
        priceYearly: 0,
        currency: 'USD',
        features: {
            creditsPerMonth: 'unlimited',
            maxUsers: 'unlimited',
            maxProjects: 'unlimited',
            maxServices: 'unlimited',
            maxTeamMembers: 'unlimited',
            supportLevel: 'dedicated'
        }
    }
];

interface PricingTableProps {
    currentPlanId?: PlanTier;
    onSelectPlan?: (planId: PlanTier, interval: BillingInterval) => void;
}

export function PricingTable({ currentPlanId = 'free', onSelectPlan }: PricingTableProps) {
    const [interval, setInterval] = useState<BillingInterval>('monthly');

    const handleSelect = (planId: PlanTier) => {
        if (onSelectPlan) {
            onSelectPlan(planId, interval);
        }
    };

    return (
        <div className="w-full max-w-[1200px] mx-auto py-12 px-6">
            <div className="text-center mb-20 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <h2 className="text-5xl font-semibold tracking-tight text-[#1D1D1F]">
                    Elige el plan perfecto.
                </h2>
                <p className="mt-4 text-xl text-[#86868B] max-w-2xl mx-auto font-light">
                    Desbloquea todo el potencial de tu agencia con IA.
                </p>

                {/* Modern Apple-style Toggle */}
                <div className="mt-10 flex justify-center items-center gap-6">
                    <span className={`text-[17px] font-medium transition-colors duration-200 ${interval === 'monthly' ? 'text-black' : 'text-[#86868B]'}`}>Mensual</span>
                    <button
                        onClick={() => setInterval(prev => prev === 'monthly' ? 'yearly' : 'monthly')}
                        className={`relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-300 ease-in-out focus:outline-none ${interval === 'yearly' ? 'bg-[#2997FF]' : 'bg-[#E5E5EA]'}`}
                    >
                        <span
                            aria-hidden="true"
                            className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow-sm ring-0 transition duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1.0)] ${interval === 'yearly' ? 'translate-x-6' : 'translate-x-0'}`}
                        />
                    </button>
                    <span className={`text-[17px] font-medium transition-colors duration-200 ${interval === 'yearly' ? 'text-black' : 'text-[#86868B]'}`}>
                        Anual <span className="text-[#2997FF] text-xs font-semibold ml-1 tracking-wide uppercase">Ahorra 17%</span>
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4 lg:gap-6">
                {PLANS.map((plan) => {
                    const isCurrent = currentPlanId === plan.id;
                    const price = interval === 'monthly' ? plan.priceMonthly : plan.priceYearly;
                    const isEnterprise = plan.id === 'enterprise';

                    // Apple Card Styles
                    const cardBase = "relative flex flex-col rounded-[28px] transition-all duration-300 bg-white";
                    const cardShadow = plan.isPopular
                        ? "shadow-[0_20px_40px_-10px_rgba(41,151,255,0.3)] ring-[1.5px] ring-[#2997FF] scale-[1.02] z-10"
                        : "shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] hover:-translate-y-1";

                    return (
                        <div
                            key={plan.id}
                            className={`${cardBase} ${cardShadow}`}
                        >
                            {plan.isPopular && (
                                <div className="absolute -top-3 left-0 right-0 flex justify-center">
                                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#2997FF] px-4 py-1 text-[11px] font-bold uppercase tracking-wider text-white shadow-lg shadow-blue-500/30">
                                        <Star size={10} fill="currentColor" strokeWidth={3} /> Popular
                                    </span>
                                </div>
                            )}

                            <div className="p-8 pb-0 flex-1 flex flex-col items-center text-center">
                                <h3 className="text-[19px] font-semibold text-[#1D1D1F]">{plan.name}</h3>
                                <p className="mt-3 text-[13px] leading-relaxed text-[#86868B] min-h-[40px] px-2">{plan.description}</p>

                                <div className="mt-6 flex items-baseline text-[#1D1D1F]">
                                    {isEnterprise ? (
                                        <span className="text-3xl font-semibold tracking-tight">Contactar</span>
                                    ) : (
                                        <>
                                            <span className="text-4xl font-semibold tracking-tight">${price}</span>
                                            <span className="ml-1 text-base text-[#86868B] font-medium">/{interval === 'monthly' ? 'mes' : 'año'}</span>
                                        </>
                                    )}
                                </div>

                                {!isEnterprise && (
                                    <p className="mt-1 text-[11px] font-medium text-[#86868B]">
                                        ≈ ${(price * 4000).toLocaleString()} COP
                                    </p>
                                )}

                                <div className="mt-8 w-full">
                                    <Button
                                        onClick={() => handleSelect(plan.id)}
                                        disabled={isCurrent}
                                        className={`w-full rounded-full text-[14px] font-medium h-11 transition-all active:scale-95 border-0 ${plan.isPopular
                                                ? 'bg-[#2997FF] hover:bg-[#0071E3] text-white shadow-lg shadow-blue-500/25'
                                                : isCurrent
                                                    ? 'bg-[#F5F5F7] text-[#86868B] cursor-not-allowed'
                                                    : 'bg-[#1D1D1F] hover:bg-black text-white'
                                            }`}
                                    >
                                        {isCurrent ? 'Plan Actual' : (isEnterprise ? 'Contactar' : (currentPlanId !== 'free' ? 'Actualizar' : 'Elegir Plan'))}
                                    </Button>
                                </div>
                            </div>

                            <div className="p-8 pt-8 w-full">
                                <div className="w-full h-px bg-gray-100 mb-6" />
                                <ul className="space-y-4 text-left">
                                    {[
                                        { label: `${plan.features.creditsPerMonth === 'unlimited' ? 'Ilimitados' : plan.features.creditsPerMonth} créditos IA/mes`, icon: Zap },
                                        { label: `${plan.features.maxUsers === 'unlimited' ? 'Ilimitados' : plan.features.maxUsers} usuarios`, icon: Check },
                                        { label: `${plan.features.maxProjects === 'unlimited' ? 'Ilimitados' : plan.features.maxProjects} proyectos`, icon: Check },
                                        { label: `Soporte ${plan.features.supportLevel}`, icon: HelpCircle },
                                    ].map((feature, idx) => (
                                        <li key={idx} className="flex items-start">
                                            <div className="flex-shrink-0">
                                                <feature.icon size={16} className={`mt-0.5 ${plan.isPopular ? 'text-[#2997FF]' : 'text-[#86868B]'}`} strokeWidth={2.5} />
                                            </div>
                                            <p className="ml-3 text-[13px] font-medium text-[#424245]">{feature.label}</p>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="mt-16 text-center space-y-3 opacity-70">
                <p className="text-xs text-[#86868B] flex items-center justify-center gap-2">
                    <Shield size={12} /> Pagos seguros via Stripe. Encriptación de 256-bit.
                </p>
            </div>
        </div>
    );
}
