'use client';

import React from 'react';
import { QuoteCreationProvider, useQuoteCreation } from '@/context/QuoteCreationContext';
import { Step1ProjectInfo } from '@/components/quotes/steps/Step1ProjectInfo';
import { Step2ServiceSelection } from '@/components/quotes/steps/Step2ServiceSelection';
import { Step3ResourceConfiguration } from '@/components/quotes/steps/Step3ResourceConfiguration';
import { Step4Summary } from '@/components/quotes/steps/Step4Summary';
import { Button } from '@/components/ui/Button'; // Assuming exist
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight, Save, FileText } from 'lucide-react';
import { useRouter } from 'next/navigation';
// import { useToast } from '@/hooks/use-toast'; // Assuming exist

const STEPS = [
    { id: 1, title: "Proyecto", component: Step1ProjectInfo },
    { id: 2, title: "Servicios", component: Step2ServiceSelection },
    { id: 3, title: "Recursos", component: Step3ResourceConfiguration },
    { id: 4, title: "Resumen", component: Step4Summary },
];

function QuoteWizardContent() {
    const { step, setStep, projectInfo, services, totalAmount, reset } = useQuoteCreation();
    const router = useRouter();
    // const { toast } = useToast();

    const handleNext = () => {
        if (step < STEPS.length) {
            setStep(step + 1);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            handleComplete();
        }
    };

    const handleBack = () => {
        if (step > 1) {
            setStep(step - 1);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            router.back();
        }
    };

    const handleComplete = async () => {
        // Here you would call the API to create the project/quote
        console.log("Creating Quote...", { projectInfo, services, totalAmount });
        // toast({ title: "Cotización Creada", description: "El proyecto se ha guardado exitosamente." });

        // Simulate API call
        setTimeout(() => {
            reset();
            router.push('/dashboard');
        }, 1000);
    };

    const CurrentStepComponent = STEPS[step - 1]?.component || Step1ProjectInfo;
    const progress = (step / STEPS.length) * 100;

    return (
        <div className="min-h-screen bg-[#F5F5F7] pb-20 font-sans">
            {/* Header / Nav */}
            <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" onClick={() => router.back()}>
                            <ArrowLeft className="w-4 h-4 mr-1" />
                            Cancelar
                        </Button>
                        <span className="font-bold text-lg text-[#1d1d1f] ml-2">Nueva Cotización</span>
                    </div>

                    {/* Progress Steps (Desktop) */}
                    <div className="hidden md:flex items-center gap-1">
                        {STEPS.map((s) => (
                            <div key={s.id} className="flex items-center">
                                <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm transition-colors ${step === s.id ? 'bg-black text-white' : step > s.id ? 'text-black font-medium' : 'text-gray-400'}`}>
                                    <span className={`w-5 h-5 flex items-center justify-center rounded-full text-xs ${step === s.id ? 'bg-white text-black' : step > s.id ? 'bg-black text-white' : 'border border-gray-300'}`}>
                                        {step > s.id ? '✓' : s.id}
                                    </span>
                                    <span>{s.title}</span>
                                </div>
                                {s.id < STEPS.length && <div className="w-4 h-[1px] bg-gray-300 mx-1" />}
                            </div>
                        ))}
                    </div>

                    <div className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                        Total: {projectInfo.currency} {totalAmount.toLocaleString()}
                    </div>
                </div>

                {/* Progress Bar (Mobile) */}
                <div className="h-1 bg-gray-200 w-full md:hidden">
                    <div
                        className="h-full bg-blue-600 transition-all duration-300"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-4 py-8">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={step}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2 }}
                    >
                        <CurrentStepComponent />
                    </motion.div>
                </AnimatePresence>
            </main>

            {/* Footer Actions */}
            <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-xl border-t border-gray-200 p-4 z-40">
                <div className="max-w-5xl mx-auto flex justify-between items-center">
                    <Button
                        variant="secondary"
                        onClick={handleBack}
                        className="glass-card hover:bg-white"
                    >
                        {step === 1 ? 'Cancelar' : 'Atrás'}
                    </Button>

                    <Button
                        onClick={handleNext}
                        className="bg-black text-white hover:bg-gray-800 rounded-xl px-8 shadow-lg shadow-black/20"
                    >
                        {step === STEPS.length ? (
                            <>
                                <Save className="w-4 h-4 mr-2" />
                                Finalizar
                            </>
                        ) : (
                            <>
                                Siguiente
                                <ArrowRight className="w-4 h-4 ml-2" />
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}

export default function NewQuoteSteppedPage() {
    return (
        <QuoteCreationProvider>
            <QuoteWizardContent />
        </QuoteCreationProvider>
    );
}
