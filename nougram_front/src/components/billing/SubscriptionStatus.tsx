
import React from 'react';
import { Plan, Subscription } from '@/types/billing';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, AlertTriangle, CreditCard, Calendar, RefreshCw, ChevronRight } from 'lucide-react';

interface SubscriptionStatusProps {
    subscription: Subscription;
    currentPlan: Plan;
    onChangePlan?: () => void;
    onUpdatePayment?: () => void;
    onCancel?: () => void;
}

export function SubscriptionStatus({
    subscription,
    currentPlan,
    onChangePlan,
    onUpdatePayment,
    onCancel
}: SubscriptionStatusProps) {

    // Status Badge Logic
    const getStatusBadge = () => {
        const baseClass = "inline-flex items-center px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide";
        switch (subscription.status) {
            case 'active':
                return <span className={`${baseClass} bg-[#E8F8F0] text-[#1D9D5D]`}>Activa</span>;
            case 'trialing':
                return <span className={`${baseClass} bg-blue-50 text-[#0071E3]`}>Prueba</span>;
            case 'past_due':
                return <span className={`${baseClass} bg-yellow-50 text-[#FF9500]`}>Pago Pendiente</span>;
            case 'canceled':
                return <span className={`${baseClass} bg-gray-100 text-gray-500`}>Cancelada</span>;
            default:
                return <span className={`${baseClass} bg-red-50 text-[#FF3B30]`}>Error</span>;
        }
    };

    const isPastDue = subscription.status === 'past_due';

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">

            {/* Main Alert for Past Due - Colombian Specific */}
            {isPastDue && (
                <div className="bg-[#FFF4E5] border border-[#FFE0B2] p-6 rounded-[24px] shadow-sm flex items-start gap-4">
                    <div className="p-3 bg-[#FF9500] text-white rounded-full shadow-lg shadow-orange-200">
                        <AlertTriangle size={24} />
                    </div>
                    <div>
                        <h3 className="text-[17px] font-semibold text-[#663C00]">
                            Tu último pago falló
                        </h3>
                        <p className="mt-1 text-[14px] text-[#995A00] leading-relaxed max-w-2xl">
                            Tu banco rechazó el pago. Esto es común en Colombia con tarjetas internacionales. Contacta a tu banco o intenta con otra tarjeta dentro de los próximos 3 días.
                        </p>
                        <div className="mt-4">
                            <Button
                                onClick={onUpdatePayment}
                                className="bg-[#FF9500] hover:bg-[#E08200] text-white border-none rounded-full px-6 h-9 text-[13px] font-bold shadow-md shadow-orange-200"
                            >
                                Actualizar Método de Pago
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                {/* 1. Plan Details Card */}
                <div className="flex flex-col bg-white rounded-[28px] p-8 shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-8 opacity-5">
                        <Check size={120} />
                    </div>

                    <div className="flex justify-between items-start mb-6 z-10">
                        <div>
                            <p className="text-[11px] font-bold text-[#86868B] uppercase tracking-widest mb-2">Tu Plan Actual</p>
                            <h2 className="text-3xl font-semibold text-[#1D1D1F]">{currentPlan.name}</h2>
                        </div>
                        {getStatusBadge()}
                    </div>

                    <div className="flex items-baseline gap-1 mb-8 z-10">
                        <span className="text-4xl font-bold tracking-tight text-[#1D1D1F]">
                            ${subscription.interval === 'monthly' ? currentPlan.priceMonthly : currentPlan.priceYearly}
                        </span>
                        <span className="text-gray-400 font-medium">/{subscription.interval === 'monthly' ? 'mes' : 'año'}</span>
                    </div>

                    <div className="bg-[#F5F5F7] rounded-[20px] p-6 mb-6 z-10">
                        <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-200/50">
                            <span className="text-[13px] text-[#86868B] font-medium">Próxima renovación</span>
                            <span className="text-[13px] text-[#1D1D1F] font-semibold">{new Date(subscription.currentPeriodEnd).toLocaleDateString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-[13px] text-[#86868B] font-medium">Miembros incluidos</span>
                            <span className="text-[13px] text-[#1D1D1F] font-semibold">{currentPlan.features.maxUsers} usuarios</span>
                        </div>
                    </div>

                    <Button
                        onClick={onChangePlan}
                        className="w-full bg-[#1D1D1F] hover:bg-black text-white rounded-full h-12 font-medium z-10"
                    >
                        Cambiar Plan
                    </Button>
                </div>

                {/* 2. Payment Method Card (Apple Wallet Style) */}
                <div className="flex flex-col bg-white rounded-[28px] p-8 shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100">
                    <div className="flex justify-between items-center mb-8">
                        <p className="text-[11px] font-bold text-[#86868B] uppercase tracking-widest">Método de Pago</p>
                        <Button variant="ghost" size="sm" onClick={onUpdatePayment} className="text-[#0071E3] hover:bg-transparent p-0 text-[13px] font-medium h-auto hover:underline">
                            Editar
                        </Button>
                    </div>

                    <div className="flex-1 flex flex-col justify-center items-center py-2">
                        {subscription.paymentMethod ? (
                            <div className="relative w-full aspect-[1.586] rounded-[24px] bg-gradient-to-br from-[#1c1c1e] to-[#2c2c2e] p-6 text-white shadow-2xl flex flex-col justify-between overflow-hidden group hover:scale-[1.02] transition-transform duration-500">
                                {/* Gloss effect */}
                                <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full blur-3xl -mr-16 -mt-16" />

                                <div className="flex justify-between items-start z-10">
                                    <CreditCard size={28} strokeWidth={1.5} className="opacity-80" />
                                    <span className="text-[14px] font-medium opacity-60 italic">{subscription.paymentMethod.type.toUpperCase()}</span>
                                </div>

                                <div className="z-10">
                                    <p className="text-[22px] font-mono tracking-widest opacity-90">•••• •••• •••• {subscription.paymentMethod.last4}</p>
                                </div>

                                <div className="flex justify-between items-end z-10">
                                    <div>
                                        <p className="text-[9px] font-bold uppercase opacity-50 tracking-wider">Titular</p>
                                        <p className="text-[13px] font-medium tracking-wide">Nougram User</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[9px] font-bold uppercase opacity-50 tracking-wider">Expira</p>
                                        <p className="text-[13px] font-medium tracking-wide">{subscription.paymentMethod.expiryMonth}/{subscription.paymentMethod.expiryYear}</p>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-10">
                                <p>No payment method</p>
                            </div>
                        )}
                    </div>

                    <div className="mt-8 pt-6 border-t border-gray-100">
                        <Button
                            variant="ghost"
                            onClick={onCancel}
                            className="w-full text-[#FF3B30] hover:text-[#D70015] hover:bg-red-50 rounded-xl text-[13px] font-medium h-10"
                        >
                            Cancelar Suscripción
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
