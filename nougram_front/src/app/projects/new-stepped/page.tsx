'use client';

import React, { useState } from 'react';
import { QuoteBuilderProvider, useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { Step1ProjectInfo } from '@/components/quotes/steps/Step1ProjectInfo';
import { Step2ServiceSelection } from '@/components/quotes/steps/Step2ServiceSelection';
import { Step3ResourceConfiguration } from '@/components/quotes/steps/Step3ResourceConfiguration';
import { Step4Summary } from '@/components/quotes/steps/Step4Summary';
import { Button } from '@/components/ui/Button';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { formatCurrency } from '@/lib/utils';
import { QuoteFlowStepper } from '@/components/quotes/QuoteFlowStepper';

const STEPS = [
    { id: 1, title: 'Información del proyecto', component: Step1ProjectInfo },
    { id: 2, title: 'Servicios y alcance', component: Step2ServiceSelection },
    { id: 3, title: 'Estimación operativa', component: Step3ResourceConfiguration },
    { id: 4, title: 'Validación final', component: Step4Summary },
];

function QuoteWizardContent() {
    const { state, summary, saveQuote, isValid } = useQuoteBuilder();
    const router = useRouter();
    const [currentStepId, setCurrentStepId] = useState(1);
    const [isSaving, setIsSaving] = useState(false);

    const handleNext = () => {
        if (currentStepId < STEPS.length) {
            setCurrentStepId(prev => prev + 1);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            handleComplete();
        }
    };

    const handleBack = () => {
        if (currentStepId > 1) {
            setCurrentStepId(prev => prev - 1);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            router.back();
        }
    };

    const handleComplete = async () => {
        setIsSaving(true);
        try {
            const projectId = await saveQuote('Draft');
            if (projectId) {
                router.push(`/dashboard/quotes/${projectId}/next-step`);
            } else {
                router.push('/dashboard');
            }
        } catch (error) {
            console.error("Error saving quote", error);
            alert("Error al guardar la cotización");
        } finally {
            setIsSaving(false);
        }
    };

    const CurrentStepComponent = STEPS[currentStepId - 1]?.component || Step1ProjectInfo;
    const progress = (currentStepId / STEPS.length) * 100;

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
                    <QuoteFlowStepper
                        className="hidden lg:block min-w-[520px]"
                        gridClassName="grid grid-cols-4 gap-2"
                        steps={STEPS.map((s) => ({ id: s.id, title: s.title }))}
                        currentStepId={currentStepId}
                    />

                    <div className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full whitespace-nowrap">
                        Total: {formatCurrency(summary.totalClientPrice, state.currency)}
                    </div>
                </div>

                {/* Progress Bar (Mobile) */}
                <QuoteFlowStepper
                    className="px-4 md:hidden"
                    gridClassName="hidden"
                    steps={STEPS.map((s) => ({ id: s.id, title: s.title }))}
                    currentStepId={currentStepId}
                    showMobileProgress
                    mobileProgressPercent={progress}
                />
            </header>

            <main className={`mx-auto px-4 py-8 transition-all duration-300 ${currentStepId === 4 ? 'max-w-[95vw]' : 'max-w-5xl'}`}>
                <div className="mb-4 rounded-xl border border-gray-200 bg-white px-4 py-2 text-xs text-gray-600">
                    Paso {currentStepId} de {STEPS.length}: {STEPS[currentStepId - 1]?.title}
                </div>
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStepId}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2 }}
                    >
                        <CurrentStepComponent />
                    </motion.div>
                </AnimatePresence>
            </main>

            <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-xl border-t border-gray-200 p-4 z-40">
                <div className="max-w-5xl mx-auto flex justify-between items-center gap-3">
                    <Button
                        variant="secondary"
                        onClick={handleBack}
                        className="glass-card hover:bg-white"
                        disabled={isSaving}
                    >
                        {currentStepId === 1 ? 'Cancelar' : 'Anterior'}
                    </Button>

                    {currentStepId < STEPS.length ? (
                        <Button
                            onClick={handleNext}
                            disabled={isSaving}
                            className={`text-white rounded-xl px-8 shadow-lg transition-colors bg-black hover:bg-gray-800 shadow-black/20`}
                        >
                            Continuar
                            <ArrowRight className="w-4 h-4 ml-2" />
                        </Button>
                    ) : (
                        <Button
                            onClick={handleComplete}
                            disabled={isSaving || !isValid}
                            className="text-white rounded-xl px-8 shadow-lg transition-colors bg-blue-600 hover:bg-blue-700 shadow-blue-500/20"
                        >
                            {isSaving ? 'Guardando...' : 'Guardar y pasar a propuesta'}
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function NewQuoteSteppedPage() {
    return (
        <QuoteBuilderProvider>
            <QuoteWizardContent />
        </QuoteBuilderProvider>
    );
}
