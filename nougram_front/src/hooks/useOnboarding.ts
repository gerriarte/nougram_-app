
import { useState, useEffect } from 'react';
import { onboardingService } from '@/services/onboardingService';
import { OnboardingData, FixedCostTemplate } from '@/types/onboarding';
import { normalizeCountryCode, normalizeCurrencyCode } from '@/lib/onboarding-geo';

// Initial onboarding state
const INITIAL_DATA: OnboardingData = {
    identity: {
        organizationName: '',
        primaryCurrency: 'COP',
        country: 'COL'
    },
    fixedCosts: {
        selectedTemplates: [],
        totalMonthly: 0
    },
    team: {
        payrollHeadcount: 1,
        name: '',
        role: '',
        level: '',
        salary: 0,
        totalHours: 40,
        billableHours: 28,
        vacationDays: 20,
        applySocialCharges: true,
        yearlyBillableHours: 0,
        hourlyCost: 0,
        teamMembers: []
    },
    status: 'in_progress',
    lastStep: 1
};

export function useOnboarding() {
    const [data, setData] = useState<OnboardingData>(INITIAL_DATA);
    const [availableTemplates, setAvailableTemplates] = useState<FixedCostTemplate[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isHydrated, setIsHydrated] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);

    useEffect(() => {
        const loadInitialState = async () => {
            setIsLoading(true);
            const temps = await onboardingService.getTemplates();
            setAvailableTemplates(temps);
            const draft = await onboardingService.getDraft<OnboardingData>();
            if (draft) {
                const normalizedCurrency = normalizeCurrencyCode(draft.identity?.primaryCurrency) || INITIAL_DATA.identity.primaryCurrency;
                const normalizedCountry = normalizeCountryCode(draft.identity?.country) || INITIAL_DATA.identity.country;
                setData({
                    ...INITIAL_DATA,
                    ...draft,
                    identity: {
                        ...INITIAL_DATA.identity,
                        ...(draft.identity || {}),
                        primaryCurrency: normalizedCurrency,
                        country: normalizedCountry,
                    },
                    fixedCosts: { ...INITIAL_DATA.fixedCosts, ...(draft.fixedCosts || {}) },
                    team: { ...INITIAL_DATA.team, ...(draft.team || {}) },
                });
            }
            setIsHydrated(true);
            setIsLoading(false);
        };
        void loadInitialState();
    }, []);

    useEffect(() => {
        if (!isHydrated) return;
        const timer = setTimeout(() => {
            void (async () => {
                setIsSaving(true);
                setSaveError(null);
                const ok = await onboardingService.saveDraft(data as unknown as Record<string, unknown>);
                setIsSaving(false);
                if (!ok) {
                    setSaveError('No se pudo guardar el borrador');
                    return;
                }
                setLastSavedAt(new Date());
            })();
        }, 700);
        return () => clearTimeout(timer);
    }, [data, isHydrated]);

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

    const updateProgress = (lastStep: number, status?: OnboardingData['status']) => {
        setData((prev: OnboardingData) => ({
            ...prev,
            lastStep: Math.max(1, lastStep),
            status: status || prev.status
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
        updateProgress,
        convertCurrency,
        isLoading,
        isSaving,
        saveError,
        lastSavedAt
    };
}
