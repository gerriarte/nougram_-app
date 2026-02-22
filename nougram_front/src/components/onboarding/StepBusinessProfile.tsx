import React from 'react';
import { motion } from 'framer-motion';
import { User, Building2, Briefcase, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { BENCHMARKS } from '@/services/onboardingService';

interface StepBusinessProfileProps {
    onNext: (type: 'freelance' | 'company' | 'agency') => void;
    onBack: () => void;
    initialType?: 'freelance' | 'company' | 'agency';
}

const profiles = [
    {
        id: 'freelance',
        title: 'Freelance',
        icon: User,
        description: BENCHMARKS.freelance.description,
        color: 'bg-blue-500',
        benchmarks: BENCHMARKS.freelance
    },
    {
        id: 'company',
        title: 'Empresa',
        icon: Building2,
        description: BENCHMARKS.company.description,
        color: 'bg-purple-500',
        benchmarks: BENCHMARKS.company
    },
    {
        id: 'agency',
        title: 'Agencia',
        icon: Briefcase,
        description: BENCHMARKS.agency.description,
        color: 'bg-orange-500',
        benchmarks: BENCHMARKS.agency
    }
] as const;

export function StepBusinessProfile({ onNext, onBack, initialType }: StepBusinessProfileProps) {
    const [selected, setSelected] = React.useState<typeof profiles[number]['id'] | null>(initialType || null);

    const handleContinue = () => {
        if (selected) {
            onNext(selected);
        }
    };

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="text-center space-y-3">
                <motion.h1
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-3xl font-bold text-[#1d1d1f] tracking-tight"
                >
                    ¿Cómo trabajas?
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="text-[#86868b] text-base"
                >
                    Selecciona tu perfil para cargar benchmarks de la industria.
                </motion.p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {profiles.map((profile, index) => {
                    const Icon = profile.icon;
                    const isSelected = selected === profile.id;

                    return (
                        <motion.div
                            key={profile.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 + (index * 0.1) }}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => setSelected(profile.id)}
                            className={cn(
                                "cursor-pointer rounded-2xl p-6 border transition-all duration-300 relative overflow-hidden",
                                isSelected
                                    ? "bg-white border-blue-500 shadow-xl shadow-blue-500/10 ring-2 ring-blue-500/20"
                                    : "bg-white/60 border-white/40 hover:bg-white/80 hover:shadow-lg"
                            )}
                        >
                            <div className={cn(
                                "w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-colors",
                                isSelected ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-500"
                            )}>
                                <Icon strokeWidth={2} className="w-6 h-6" />
                            </div>

                            <h3 className="text-xl font-bold text-[#1d1d1f] mb-2">{profile.title}</h3>
                            <p className="text-sm text-[#86868b] leading-relaxed mb-4">
                                {profile.description}
                            </p>

                            {/* Benchmarks Preview */}
                            <div className="space-y-2 pt-4 border-t border-gray-100">
                                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Promedios</p>
                                <div className="text-xs space-y-1 text-gray-600">
                                    <div className="flex justify-between">
                                        <span>Margen:</span>
                                        <span className="font-medium text-[#1d1d1f]">{profile.benchmarks.avgMargin}%</span>
                                    </div>
                                    {'avgMonthlyIncome' in profile.benchmarks && (
                                        <div className="flex justify-between">
                                            <span>Ingreso:</span>
                                            <span className="font-medium text-[#1d1d1f]">${profile.benchmarks.avgMonthlyIncome}</span>
                                        </div>
                                    )}
                                    {'avgTeamSize' in profile.benchmarks && (
                                        <div className="flex justify-between">
                                            <span>Equipo:</span>
                                            <span className="font-medium text-[#1d1d1f]">{profile.benchmarks.avgTeamSize} personas</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {isSelected && (
                                <div className="absolute top-4 right-4 text-blue-500">
                                    <div className="bg-blue-50 rounded-full p-1">
                                        <Check className="w-4 h-4" />
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    );
                })}
            </div>

            <div className="flex justify-between items-center pt-8">
                <button
                    onClick={onBack}
                    className="text-[#86868b] hover:text-[#1d1d1f] font-medium transition-colors px-4 py-2"
                >
                    Atrás
                </button>
                <div className="flex-1"></div>
                <button
                    onClick={handleContinue}
                    disabled={!selected}
                    className={cn(
                        "px-8 py-3 rounded-xl font-medium transition-all duration-300",
                        selected
                            ? "bg-[#007aff] text-white hover:bg-[#0071e3] shadow-lg shadow-blue-500/25 transform hover:-translate-y-0.5"
                            : "bg-gray-200 text-gray-400 cursor-not-allowed"
                    )}
                >
                    Continuar
                </button>
            </div>
        </div>
    );
}
