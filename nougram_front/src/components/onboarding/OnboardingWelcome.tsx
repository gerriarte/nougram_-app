import React from 'react';
import { ArrowRight, Building2, Calculator, CheckCircle2, Sparkles, Users } from 'lucide-react';
import { Button } from '@/components/ui/Button';

type OnboardingWelcomeProps = {
    onStart: () => void;
};

const PREVIEW_STEPS = [
    {
        n: 1,
        icon: Building2,
        title: 'Identidad',
        desc: 'Cuéntanos sobre tu empresa',
        time: '~1 min',
        items: ['Nombre y sector', 'País y moneda', 'Tipo de operación'],
    },
    {
        n: 2,
        icon: Calculator,
        title: 'Inventario',
        desc: 'Tus gastos operativos',
        time: '~3 min',
        items: ['Gastos fijos', 'Amortizables', 'Software'],
    },
    {
        n: 3,
        icon: Users,
        title: 'Equipo',
        desc: 'Nómina y horas',
        time: '~2 min',
        items: ['Miembros', 'Salarios', 'Horas facturables'],
    },
];

export function OnboardingWelcome({ onStart }: OnboardingWelcomeProps) {
    return (
        <div className="mx-auto flex min-h-[calc(100vh-180px)] w-full max-w-4xl items-center px-4 py-12">
            <div className="w-full">
                <div className="mb-10 text-center">
                    <div className="mb-5 inline-flex rounded-full bg-primary-soft px-4 py-1.5 text-[11px] font-black uppercase tracking-[0.16em] text-primary">
                        Configuración inicial · ~5 min
                    </div>
                    <h1 className="text-4xl font-black tracking-tight text-gray-950 sm:text-5xl">
                        Bienvenido a Nougram.
                        <br />
                        <span className="text-primary">Hagamos los números primero.</span>
                    </h1>
                    <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-gray-600">
                        En tres pasos vamos a calcular tu <strong className="text-gray-900">costo real por hora (BCR)</strong>, el número mínimo que necesitas cobrar para no perder dinero.
                    </p>
                </div>

                <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
                    {PREVIEW_STEPS.map((step) => {
                        const Icon = step.icon;
                        return (
                            <div key={step.n} className="relative overflow-hidden rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                                <div className="absolute right-4 top-4 text-[10px] font-bold text-gray-400">{step.time}</div>
                                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-primary-soft text-primary">
                                    <Icon size={18} />
                                </div>
                                <div className="mb-1 flex items-baseline gap-2">
                                    <span className="font-mono text-[11px] font-black text-gray-400">0{step.n}</span>
                                    <h2 className="text-base font-black text-gray-900">{step.title}</h2>
                                </div>
                                <p className="mb-3 text-[12.5px] text-gray-500">{step.desc}</p>
                                <div className="space-y-1">
                                    {step.items.map((item) => (
                                        <div key={item} className="flex items-center gap-2 text-[11.5px] text-gray-400">
                                            <span className="h-1 w-1 rounded-full bg-gray-300" />
                                            {item}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="mb-8 flex items-start gap-4 rounded-2xl border border-dashed border-gray-200 bg-white p-4 shadow-sm">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
                        <Sparkles size={17} />
                    </div>
                    <div>
                        <div className="flex items-center gap-2 text-sm font-black text-gray-900">
                            <CheckCircle2 size={15} className="text-success" />
                            Tu progreso se guarda automáticamente
                        </div>
                        <p className="mt-1 text-sm leading-6 text-gray-500">
                            Puedes salir y volver cuando quieras. Si prefieres, importa todo desde Excel desde el menú de opciones.
                        </p>
                    </div>
                </div>

                <div className="text-center">
                    <Button onClick={onStart} className="h-12 rounded-2xl px-8 text-base font-black">
                        Empezar configuración <ArrowRight size={16} className="ml-2" />
                    </Button>
                    <p className="mt-3 text-[12px] text-gray-400">
                        ¿Ya tienes los datos en Excel? Usa la plantilla disponible en el menú superior.
                    </p>
                </div>
            </div>
        </div>
    );
}
