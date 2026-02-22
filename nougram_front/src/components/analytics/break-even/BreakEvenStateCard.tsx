import React from 'react';
import { BreakEvenAnalysisResponse } from '@/types/break-even';
import { AlertCircle, CheckCircle2, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

interface BreakEvenStateCardProps {
    data: BreakEvenAnalysisResponse;
}

export function BreakEvenStateCard({ data }: BreakEvenStateCardProps) {
    const isBelow = data.status === 'below_break_even';
    const isAbove = data.status === 'above_break_even';
    const isAt = data.status === 'at_break_even';

    return (
        <div className={`rounded-[24px] p-6 border ${isBelow ? 'bg-yellow-50/50 border-yellow-200' :
                isAbove ? 'bg-green-50/50 border-green-200' :
                    'bg-blue-50/50 border-blue-200'
            }`}>
            <div className="flex justify-between items-start">
                <div className="space-y-4">
                    <div>
                        <h2 className="text-gray-500 font-medium text-sm mb-1">Estado Actual</h2>
                        <div className="flex items-center gap-2">
                            {isBelow && <AlertCircle className="text-yellow-600" />}
                            {isAbove && <CheckCircle2 className="text-green-600" />}
                            {isAt && <TrendingUp className="text-blue-600" />}

                            <span className={`text-xl font-bold ${isBelow ? 'text-yellow-700' :
                                    isAbove ? 'text-green-700' :
                                        'text-blue-700'
                                }`}>
                                {isBelow ? 'Por debajo del equilibrio' :
                                    isAbove ? 'Por encima del equilibrio' :
                                        'En punto de equilibrio'}
                            </span>
                        </div>
                    </div>

                    <p className="text-gray-700 text-lg max-w-2xl font-medium">
                        {data.status_message}
                    </p>

                    {/* Quick Stats Context */}
                    <div className="flex gap-6 text-sm">
                        <div>
                            <span className="text-gray-500 block">Proyección</span>
                            <span className="font-semibold text-gray-900">
                                {data.projected_break_even_date
                                    ? `Equilibrio estimado: ${new Date(data.projected_break_even_date).toLocaleDateString()}`
                                    : 'N/A'
                                }
                            </span>
                        </div>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <Link href="/analytics/break-even/projection">
                            <Button variant="secondary" className="bg-white hover:bg-gray-50 text-gray-700 border border-gray-200">
                                Ver Proyección
                            </Button>
                        </Link>
                        <Link href="/analytics/break-even/scenarios">
                            <Button className="bg-[black] text-white hover:bg-gray-800">
                                Simular Escenarios
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
