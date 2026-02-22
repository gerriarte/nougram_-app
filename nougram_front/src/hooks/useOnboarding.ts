
import { useState, useEffect, useCallback } from 'react';
import { onboardingService, ALL_TEMPLATES, CurrencyRate } from '@/services/onboardingService';
import { OnboardingData, FixedCostTemplate } from '@/types/onboarding';

// Initial Mock Data
const INITIAL_DATA: OnboardingData = {
    identity: {
        organizationName: '',
        primaryCurrency: 'COP',
        country: 'Colombia'
    },
    fixedCosts: {
        selectedTemplates: [],
        totalMonthly: 0
    },
    team: {
        name: '',
        role: '',
        level: '',
        salary: 0,
        totalHours: 40,
        billableHours: 28,
        vacationDays: 20,
        applySocialCharges: true,
        yearlyBillableHours: 0,
        hourlyCost: 0
    },
    status: 'in_progress',
    lastStep: 1
};

export function useOnboarding() {
    const [data, setData] = useState<OnboardingData>(INITIAL_DATA);
    const [availableTemplates, setAvailableTemplates] = useState<FixedCostTemplate[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Load data from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem('nougram_onboarding_data');
        if (saved) {
            try {
                setData(JSON.parse(saved));
            } catch (e) {
                console.error("Failed to parse onboarding data", e);
            }
        }

        // Load Templates
        const loadTemplates = async () => {
            const temps = await onboardingService.getTemplates();
            setAvailableTemplates(temps);
        };
        loadTemplates();
    }, []);

    // Save to localStorage on change
    useEffect(() => {
        localStorage.setItem('nougram_onboarding_data', JSON.stringify(data));
    }, [data]);

    const updateIdentity = (identity: Partial<OnboardingData['identity']>) => {
        setData((prev: OnboardingData) => ({
            ...prev,
            identity: { ...prev.identity, ...identity }
        }));
    };

    const updateFixedCosts = (fixedCosts: Partial<OnboardingData['fixedCosts']>) => {
        setData((prev: OnboardingData) => ({
            ...prev,
            fixedCosts: { ...prev.fixedCosts, ...fixedCosts }
        }));
    };

    const updateTeam = (team: Partial<OnboardingData['team']>) => {
        // Auto-calculate True Hourly Cost whenever team data changes
        const fullTeam = { ...data.team, ...team };

        const analysis = onboardingService.calculateTrueHourlyCost(
            fullTeam.applySocialCharges ? fullTeam.salary * 1.52852 : fullTeam.salary, // Approx social charges
            fullTeam.billableHours,
            fullTeam.vacationDays
        );

        setData((prev: OnboardingData) => ({
            ...prev,
            team: {
                ...fullTeam,
                hourlyCost: analysis.hourlyCost,
                yearlyBillableHours: analysis.annualBillableHours
            }
        }));
    };

    const convertCurrency = (amount: number, from: string, to: string) => {
        return onboardingService.convertCurrency(amount, from, to);
    };

    return {
        data,
        availableTemplates,
        updateIdentity,
        updateFixedCosts,
        updateTeam,
        convertCurrency,
        isLoading
    };
}
