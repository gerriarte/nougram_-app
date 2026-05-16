
import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { PlanTier } from '@/types/billing';
import { AlertCircle, Zap, Users, Layout, Lock } from 'lucide-react';

export type PaywallReason = 'limits_project' | 'limits_user' | 'credits_insufficient' | 'feature_locked';

interface PaywallModalProps {
    isOpen: boolean;
    onClose: () => void;
    reason: PaywallReason;
    data?: {
        currentCount?: number;
        limit?: number;
        requiredCredits?: number;
        availableCredits?: number;
    };
    onUpgrade: () => void;
}

export function PaywallModal({ isOpen, onClose, reason, data, onUpgrade }: PaywallModalProps) {

    const getContent = () => {
        switch (reason) {
            case 'limits_project':
                return {
                    icon: Layout,
                    title: 'Límite de Proyectos Alcanzado',
                    description: `Has creado ${data?.currentCount} de ${data?.limit} proyectos permitidos en tu plan actual.`,
                    action: 'Actualizar para crear más',
                    color: 'text-blue-600',
                    bg: 'bg-blue-50'
                };
            case 'limits_user':
                return {
                    icon: Users,
                    title: 'Límite de Miembros del Equipo',
                    description: `Has alcanzado el límite de ${data?.limit} miembros del equipo.`,
                    action: 'Actualizar para colaborar más',
                    color: 'text-purple-600',
                    bg: 'bg-purple-50'
                };
            case 'credits_insufficient':
                return {
                    icon: Zap,
                    title: 'Créditos Insuficientes',
                    description: `Esta acción requiere ${data?.requiredCredits} créditos, pero solo tienes ${data?.availableCredits} disponibles.`,
                    action: 'Obtener más créditos',
                    color: 'text-yellow-600',
                    bg: 'bg-yellow-50'
                };
            case 'feature_locked':
                return {
                    icon: Lock,
                    title: 'Función Premium',
                    description: 'Esta función está disponible exclusivamente en planes superiores.',
                    action: 'Desbloquear función',
                    color: 'text-indigo-600',
                    bg: 'bg-indigo-50'
                };
            default:
                return {
                    icon: AlertCircle,
                    title: 'Acceso Restringido',
                    description: 'Actualiza tu plan para continuar.',
                    action: 'Ver Planes',
                    color: 'text-gray-600',
                    bg: 'bg-gray-50'
                };
        }
    };

    const content = getContent();
    const Icon = content.icon;

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[440px] p-0 overflow-hidden border-0 shadow-2xl">
                {/* Visual Header */}
                <div className={`h-32 w-full ${content.bg} flex items-center justify-center relative overflow-hidden`}>
                    <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-black to-transparent" />
                    <div className={`p-4 rounded-full bg-white shadow-sm ring-4 ring-white/50 ${content.color}`}>
                        <Icon size={40} />
                    </div>
                </div>

                <div className="p-6 text-center">
                    <DialogTitle className="text-xl font-black text-gray-900 mb-2">
                        {content.title}
                    </DialogTitle>
                    <DialogDescription className="text-gray-500 mb-8">
                        {content.description}
                    </DialogDescription>

                    <div className="space-y-3">
                        <Button
                            onClick={onUpgrade}
                            className="w-full h-12 text-base shadow-lg shadow-blue-500/20 bg-blue-600 hover:bg-blue-700"
                        >
                            {content.action}
                        </Button>
                        <Button
                            variant="ghost"
                            onClick={onClose}
                            className="w-full text-gray-400 hover:text-gray-600"
                        >
                            Cerrar
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
