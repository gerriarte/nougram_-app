'use client';

import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    X,
    FileText,
    DollarSign,
    Users,
    Package,
    Calculator,
    Landmark,
    Wrench,
    Store,
    UserCheck,
    Send,
    Activity,
    LayoutDashboard,
    PlusCircle,
} from 'lucide-react';

type HelpItem = {
    icon: React.ReactNode;
    title: string;
    description: string;
};

type HelpSection = {
    id: string;
    label: string;
    color: string;
    bg: string;
    items: HelpItem[];
};

const SECTIONS: HelpSection[] = [
    {
        id: 'quotes',
        label: 'Cotizaciones y Proyectos',
        color: 'text-orange-600',
        bg: 'bg-orange-50',
        items: [
            {
                icon: <PlusCircle size={16} />,
                title: 'Nueva cotización',
                description:
                    'Creá una cotización desde cero eligiendo el cliente, moneda y los ítems de servicio. Cada ítem tiene su tipo de precio (fijo, por hora o recurrente).',
            },
            {
                icon: <Calculator size={16} />,
                title: 'Builder de ítems',
                description:
                    'El builder calcula automáticamente el costo real de cada ítem usando tu nómina y overhead, y te muestra el margen de ganancia en tiempo real.',
            },
            {
                icon: <Send size={16} />,
                title: 'Propuesta al cliente',
                description:
                    'Generá un link único para que tu cliente vea la propuesta en un portal profesional, sin necesidad de que tenga una cuenta.',
            },
            {
                icon: <Activity size={16} />,
                title: 'Estados y seguimiento',
                description:
                    'Cada cotización pasa por estados: Borrador → Enviada → Aprobada → En curso → Completada. El dashboard refleja el pipeline en tiempo real.',
            },
        ],
    },
    {
        id: 'costs',
        label: 'Costos Operativos',
        color: 'text-blue-600',
        bg: 'bg-blue-50',
        items: [
            {
                icon: <Users size={16} />,
                title: 'Nómina',
                description:
                    'Registrá los sueldos brutos de tu equipo. El sistema distribuye ese costo en cada cotización proporcionalmente a las horas asignadas.',
            },
            {
                icon: <LayoutDashboard size={16} />,
                title: 'Overhead',
                description:
                    'Gastos fijos de la agencia: alquiler, suscripciones, servicios, etc. Se distribuyen mensualmente entre todos los proyectos activos.',
            },
            {
                icon: <Landmark size={16} />,
                title: 'Impuestos',
                description:
                    'Configurá los impuestos que aplican a tus servicios (IVA, retenciones, etc.). Se aplican automáticamente al calcular el precio final al cliente.',
            },
            {
                icon: <Wrench size={16} />,
                title: 'Equipos',
                description:
                    'Registrá los activos físicos de la agencia (computadoras, cámaras, etc.) y su amortización mensual para incluirlos en el costo real.',
            },
            {
                icon: <Store size={16} />,
                title: 'Proveedores',
                description:
                    'Servicios externos que subcontratás (freelancers, plataformas, licencias). Podés agregarlos como ítem de costo en cualquier cotización.',
            },
        ],
    },
    {
        id: 'clients',
        label: 'Clientes y Propuestas',
        color: 'text-emerald-600',
        bg: 'bg-emerald-50',
        items: [
            {
                icon: <UserCheck size={16} />,
                title: 'Gestión de clientes',
                description:
                    'La base de clientes de tu agencia. Cada cliente agrupa todas sus cotizaciones y proyectos, y acumula el historial de facturación.',
            },
            {
                icon: <FileText size={16} />,
                title: 'Portal de propuesta',
                description:
                    'Tu cliente recibe un link único con una vista profesional de la propuesta: ítems, totales, condiciones y opción de aprobación online.',
            },
            {
                icon: <Package size={16} />,
                title: 'Versiones de cotización',
                description:
                    'Si el cliente pide cambios, podés crear una nueva versión de la cotización sin perder la original. Cada versión tiene su propio estado.',
            },
            {
                icon: <DollarSign size={16} />,
                title: 'Rentabilidad por cliente',
                description:
                    'Desde el perfil del cliente podés ver el margen acumulado, las horas trabajadas y comparar lo cotizado vs. lo real ejecutado.',
            },
        ],
    },
];

type HelpPanelProps = {
    open: boolean;
    onClose: () => void;
};

export function HelpPanel({ open, onClose }: HelpPanelProps) {
    useEffect(() => {
        if (!open) return;
        const prev = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = prev;
        };
    }, [open]);

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [onClose]);

    if (typeof document === 'undefined') return null;

    return createPortal(
        <AnimatePresence>
            {open && (
                <div className="fixed inset-0 z-[200] flex justify-end" role="dialog" aria-modal="true" aria-label="Guía de uso">
                    {/* Backdrop */}
                    <motion.div
                        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />

                    {/* Panel */}
                    <motion.div
                        className="relative w-full max-w-lg bg-white shadow-2xl flex flex-col overflow-hidden"
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 28, stiffness: 300 }}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-primary/5 to-secondary/5 shrink-0">
                            <div>
                                <p className="text-[10px] font-black text-system-gray uppercase tracking-[0.2em]">Nougram</p>
                                <h2 className="text-xl font-black text-gray-900 tracking-tight mt-0.5">Guía de uso</h2>
                            </div>
                            <button
                                type="button"
                                onClick={onClose}
                                className="h-10 w-10 rounded-2xl border border-gray-200 bg-white flex items-center justify-center text-gray-500 hover:bg-gray-50 hover:text-gray-900 transition-all"
                                aria-label="Cerrar guía"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        {/* Intro */}
                        <div className="px-6 py-4 bg-gray-50/60 border-b border-gray-100 shrink-0">
                            <p className="text-sm text-gray-600 leading-relaxed">
                                Nougram centraliza la gestión de rentabilidad de tu agencia: calculá el costo real de tus proyectos,
                                armá propuestas profesionales y monitoreá tus márgenes en tiempo real.
                            </p>
                        </div>

                        {/* Sections */}
                        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">
                            {SECTIONS.map((section) => (
                                <div key={section.id}>
                                    <div className="flex items-center gap-2 mb-4">
                                        <div className={`w-1.5 h-5 rounded-full ${section.bg.replace('bg-', 'bg-').replace('-50', '-400')}`} />
                                        <h3 className={`text-sm font-black uppercase tracking-widest ${section.color}`}>
                                            {section.label}
                                        </h3>
                                    </div>

                                    <div className="space-y-3">
                                        {section.items.map((item) => (
                                            <div
                                                key={item.title}
                                                className="flex gap-4 p-4 rounded-2xl border border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm transition-all"
                                            >
                                                <div className={`w-8 h-8 rounded-xl ${section.bg} ${section.color} flex items-center justify-center shrink-0 mt-0.5`}>
                                                    {item.icon}
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="text-sm font-bold text-gray-900 leading-none mb-1.5">{item.title}</p>
                                                    <p className="text-xs text-gray-500 leading-relaxed">{item.description}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Footer */}
                        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/60 shrink-0">
                            <p className="text-xs text-gray-400 text-center">
                                ¿Necesitás ayuda adicional? Contactanos en{' '}
                                <span className="font-bold text-gray-600">soporte@nougram.co</span>
                            </p>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>,
        document.body
    );
}
