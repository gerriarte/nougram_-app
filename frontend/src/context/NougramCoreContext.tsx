
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Equipment } from '@/types/equipment';
import { calculateDepreciation } from '@/lib/depreciation';
import { FixedCostTemplate } from '@/types/onboarding';
import { apiRequest } from '@/lib/api-client';
import { isAuthenticated } from '@/lib/auth';
import { equipmentService } from '@/services/equipmentService';
import { financialSummaryService } from '@/services/financialSummaryService';
import { estimateOnboardingBcrPreview } from '@/lib/onboarding-bcr-preview';

// --- Types ---

import { UserRole } from '@/types/user';
export type Currency = 'COP' | 'USD' | 'EUR' | 'ARS' | 'PEN' | 'MXN';

export interface AgencyIdentity {
    name: string;
    logo?: string;
    primaryCurrency: Currency;
    country?: string;
}

/**
 * De dónde salió el BCR que hay en memoria.
 *  - 'backend': valor autoritativo de /admin/financial-summary. Normaliza monedas
 *    a la moneda primaria de la org, aplica las cargas sociales configuradas e
 *    incluye la amortización de equipos. Es el único válido para cotizar.
 *  - 'onboarding-estimate': previsualización del wizard, antes de que exista nada
 *    persistido (ver lib/onboarding-bcr-preview.ts). Preliminar por definición.
 *  - 'unavailable': se intentó consultar al backend y no contestó.
 *  - 'none': todavía no se resolvió.
 */
export type BcrSource = 'backend' | 'onboarding-estimate' | 'unavailable' | 'none';

export interface FinancialState {
    baseMonthlyCost: number; // Payroll + Overhead (backend, o estimado en onboarding)
    billableHours: number;   // Total capacity
    equipmentAmortization: number; // Calculated from active equipment (solo display)
    bcr: number; // Costo/hora. Ver bcrSource para saber si es autoritativo.
    bcrSource: BcrSource;
    exchangeRateCOP: number;
}

export interface NougramState {
    identity: AgencyIdentity;
    financials: FinancialState;
    equipment: Equipment[]; // Inventory
    features: {
        teamCellsEnabled: boolean;
        resourceOccupancyEnabled: boolean;
        resourcePlanningMode: 'simple' | 'advanced';
        quoteAgentEnabled: boolean;
    };
    user: {
        role: UserRole;
        credits: number;
    };
    isHydrated: boolean;
}

// --- Context ---
interface NougramCoreContextType {
    state: NougramState;

    // Actions
    updateIdentity: (identity: Partial<AgencyIdentity>) => void;
    // updateBCR is now implicit via component updates, but we keep override for base params
    updateFinancialBasics: (baseCost: number, hours: number) => void;

    // Equipment Actions
    addEquipment: (item: Equipment) => void;
    updateEquipment: (id: string, updates: Partial<Equipment>) => void;
    removeEquipment: (id: string) => void;

    updateCredits: (newCredits: number) => void;
    switchRole: (role: UserRole) => void;
    hydrateFromOnboarding: (data: any) => void;
}

const DEFAULT_STATE: NougramState = {
    identity: { name: 'Mi Agencia', primaryCurrency: 'COP', country: 'CO' },
    financials: {
        baseMonthlyCost: 0,
        billableHours: 160,
        equipmentAmortization: 0,
        bcr: 0,
        bcrSource: 'none',
        exchangeRateCOP: 4200
    },
    equipment: [],
    features: {
        teamCellsEnabled: false,
        resourceOccupancyEnabled: true,
        resourcePlanningMode: 'simple',
        quoteAgentEnabled: false,
    },
    user: { role: 'owner', credits: 100 },
    isHydrated: false
};

/**
 * Cuánto se espera al backend antes de dar la hidratación por perdida.
 * `fetch` no tiene timeout propio: si el backend acepta la conexión y no contesta
 * nunca, ningún request settlea. Sin este techo, `bcrSource` se queda en 'none' y
 * `isHydrated` en false para siempre, y la ruta '/' no decide nunca (H18).
 */
export const BCR_HYDRATION_TIMEOUT_MS = 10_000;

/** Estado observable por la pantalla raíz para decidir a dónde mandar al usuario. */
export interface RootRouteInput {
    /** `loading` de useAuth: depende de GET /auth/me, que puede no settlear nunca. */
    authLoading: boolean;
    /** `isAuthenticated` de useAuth: solo es confiable cuando authLoading es false. */
    isAuthenticated: boolean;
    /** Token persistido (lectura sincrónica de localStorage, sin fetch de por medio). */
    hasStoredSession: boolean;
    /** `state.isHydrated`: depende de GET /settings/equipment, que puede no settlear. */
    isHydrated: boolean;
    bcr: number;
    bcrSource: BcrSource;
    /** true cuando venció el techo de espera de la pantalla raíz. */
    bailedOut: boolean;
}

export type RootRouteDecision = '/login' | '/onboarding' | '/dashboard' | null;

/**
 * Decide el destino de la ruta '/'. `null` significa "seguir esperando".
 *
 * Vive acá y no en la página para poder testearla sin navegador, y porque las dos
 * banderas que la gobiernan (`isHydrated`, `bcrSource`) las produce este contexto.
 *
 * H18: mientras `bailedOut` es false se espera a que la sesión y la hidratación
 * resuelvan, que es el camino feliz. Pero esas banderas cuelgan de fetches sin
 * timeout, así que una vez vencido el techo la decisión NO puede volver a mirarlas:
 * se cae a `hasStoredSession`, que es sincrónico y no depende de ninguna red.
 */
export function decideRootRoute(input: RootRouteInput): RootRouteDecision {
    const {
        authLoading,
        isAuthenticated: authenticated,
        hasStoredSession,
        isHydrated,
        bcr,
        bcrSource,
        bailedOut,
    } = input;

    if (!bailedOut) {
        if (authLoading || !isHydrated) return null;
        if (!authenticated) return '/login';
        // Decidir con 'none' mandaría a onboarding a cualquier organización ya
        // configurada, solo por llegar antes que el resumen financiero.
        if (bcrSource === 'none') return null;
        return bcr === 0 ? '/onboarding' : '/dashboard';
    }

    // Venció el techo: decidir con lo que haya, sin esperar a ningún request.
    // Si la sesión nunca resolvió, el token persistido es el único dato disponible.
    const sessionLooksValid = authLoading ? hasStoredSession : authenticated;
    if (!sessionLooksValid) return '/login';

    // 'none' = el resumen financiero nunca llegó. Mandar a onboarding a una org que
    // quizá ya está configurada es peor que dejarla en el dashboard, que sabe
    // mostrar sus propios errores y tiene navegación.
    if (bcrSource === 'none') return '/dashboard';
    return bcr === 0 ? '/onboarding' : '/dashboard';
}

const NougramCoreContext = createContext<NougramCoreContextType | undefined>(undefined);

export function NougramCoreProvider({ children }: { children: React.ReactNode }) {
    const [state, setState] = useState<NougramState>(DEFAULT_STATE);
    const [backendHydrationKey, setBackendHydrationKey] = useState(0);

    useEffect(() => {
        const onSessionRestored = () => setBackendHydrationKey((k) => k + 1);
        if (typeof window !== 'undefined') {
            window.addEventListener('nougram:session-restored', onSessionRestored);
        }
        return () => {
            if (typeof window !== 'undefined') {
                window.removeEventListener('nougram:session-restored', onSessionRestored);
            }
        };
    }, []);

    type OrganizationMeResponse = {
        id: number;
        name: string;
        settings?: {
            currency?: Currency;
            primary_currency?: Currency;
            country?: string;
        } | null;
    };
    type CurrencySettingsResponse = {
        primary_currency?: Currency;
    };
    type FeatureFlagsResponse = {
        team_cells_enabled?: boolean;
        resource_occupancy_enabled?: boolean;
        resource_planning_mode?: 'simple' | 'advanced';
        quote_agent_enabled?: boolean;
    };

    // Initial hydration from backend-only sources (skip when logged out to avoid 401 storms).
    useEffect(() => {
        if (!isAuthenticated()) {
            setState((prev) => ({ ...prev, isHydrated: true }));
            return;
        }
        // Igual que el resumen financiero: `equipmentService.getAll()` sale por
        // `fetch`, que no tiene timeout. Si el backend acepta la conexión y no
        // responde, este await no settlea nunca e `isHydrated` se queda en false —
        // la segunda bandera que congelaba la ruta '/' en el spinner (H18).
        const markHydrated = () =>
            setState(prev => (prev.isHydrated ? prev : { ...prev, isHydrated: true }));
        const timeoutId = setTimeout(markHydrated, BCR_HYDRATION_TIMEOUT_MS);
        const hydrateFromBackend = async () => {
            const equipment = await equipmentService.getAll();
            clearTimeout(timeoutId);
            // Si el equipo llega tarde igual se aplica: solo se perdió la espera.
            setState(prev => ({ ...prev, equipment, isHydrated: true }));
        };
        void hydrateFromBackend().catch(() => {
            clearTimeout(timeoutId);
            markHydrated();
        });
        return () => clearTimeout(timeoutId);
    }, [backendHydrationKey]);

    // El front ya no deriva el BCR: el backend es la fuente de verdad porque es el
    // único que normaliza a la moneda primaria de la organización y aplica su config
    // de cargas sociales. Si el resumen no llega, se marca 'unavailable' y se conserva
    // lo que hubiera (p. ej. la estimación preliminar del onboarding) sin blanquearlo.
    const applyBackendFinancials = (
        summary: Awaited<ReturnType<typeof financialSummaryService.get>>
    ) => {
        setState((prev) => ({
            ...prev,
            financials: summary
                ? {
                    ...prev.financials,
                    baseMonthlyCost:
                        (Number(summary.monthlyFixedCosts) || 0) +
                        (Number(summary.monthlyPayroll) || 0),
                    billableHours:
                        Number(summary.totalBillableHours) > 0
                            ? Number(summary.totalBillableHours)
                            : prev.financials.billableHours,
                    bcr: Number(summary.blendedCostRate) || 0,
                    bcrSource: 'backend',
                }
                : { ...prev.financials, bcrSource: 'unavailable' },
        }));
    };

    useEffect(() => {
        if (!isAuthenticated()) {
            return;
        }
        // `fetch` no tiene timeout propio: si el backend acepta la conexión y no
        // contesta nunca, este Promise.all no settlea jamás y bcrSource se queda en
        // 'none', que es lo que deja la pantalla raíz girando en el spinner (H18).
        // Pasado el plazo se degrada a 'unavailable' — el mismo estado que ya se usa
        // cuando el backend contesta con error — para que la app siga decidiendo.
        let resolved = false;
        const degradeToUnavailable = () => {
            if (resolved) return;
            resolved = true;
            applyBackendFinancials(null);
        };
        const timeoutId = setTimeout(degradeToUnavailable, BCR_HYDRATION_TIMEOUT_MS);
        const hydrateOrganizationName = async () => {
            const [organizationResponse, currencyResponse, featuresResponse, financialSummary] = await Promise.all([
                apiRequest<OrganizationMeResponse>('/organizations/me'),
                apiRequest<CurrencySettingsResponse>('/settings/currency'),
                apiRequest<FeatureFlagsResponse>('/settings/features'),
                // BCR autoritativo: el backend ya normaliza monedas y cargas sociales.
                financialSummaryService.get(),
            ]);
            // El BCR se aplica aunque /organizations/me falle: la pantalla raíz
            // decide onboarding vs dashboard mirando bcrSource, y dejarla en 'none'
            // la colgaría en el spinner. Si la respuesta llega tarde (después del
            // timeout) igual se aplica: pisa el 'unavailable' con el dato real.
            resolved = true;
            clearTimeout(timeoutId);
            applyBackendFinancials(financialSummary);
            if (organizationResponse.error || !organizationResponse.data) return;
            const backendCountry = organizationResponse.data.settings?.country;
            const backendCurrency =
                currencyResponse.data?.primary_currency ||
                organizationResponse.data.settings?.primary_currency ||
                organizationResponse.data.settings?.currency;
            const backendFeatures = featuresResponse.data;
            setState((prev) => ({
                ...prev,
                identity: {
                    ...prev.identity,
                    name: organizationResponse.data?.name || prev.identity.name,
                    primaryCurrency: backendCurrency || prev.identity.primaryCurrency,
                    country: backendCountry || prev.identity.country,
                },
                features: {
                    teamCellsEnabled: Boolean(backendFeatures?.team_cells_enabled),
                    resourceOccupancyEnabled: backendFeatures?.resource_occupancy_enabled !== false,
                    resourcePlanningMode: backendFeatures?.resource_planning_mode === 'advanced' ? 'advanced' : 'simple',
                    quoteAgentEnabled: Boolean(backendFeatures?.quote_agent_enabled),
                },
            }));
        };
        // A diferencia del otro efecto de hidratación, este no tenía `.catch`: una
        // excepción inesperada dejaba bcrSource en 'none' para siempre.
        void hydrateOrganizationName().catch(degradeToUnavailable);
        return () => clearTimeout(timeoutId);
    }, [backendHydrationKey]);

    // Amortización de equipos + BCR de respaldo.
    //
    // La amortización se sigue agregando acá porque varias vistas la muestran
    // desglosada. El BCR, en cambio, YA NO se deriva cuando el backend contestó:
    // el backend normaliza a la moneda primaria de la organización y este cálculo
    // no, así que derivarlo en paralelo producía dos números divergentes (hasta
    // ~3472x cuando la org tiene todo en COP y el front lo trataba como USD).
    // Solo se calcula localmente mientras no hay valor autoritativo, es decir
    // durante la previsualización del wizard de onboarding.
    useEffect(() => {
        const { baseMonthlyCost, billableHours, bcr, bcrSource, equipmentAmortization } = state.financials;

        // Sum active equipment depreciation
        let totalAmortization = 0;
        state.equipment.forEach(eq => {
            if (eq.isActive) {
                const { monthlyDepreciation } = calculateDepreciation(eq);
                totalAmortization += monthlyDepreciation;
            }
        });

        const backendIsAuthoritative = bcrSource === 'backend';
        // El BCR del backend ya incluye la amortización: recalcularlo acá la duplicaría.
        const newBCR = backendIsAuthoritative
            ? bcr
            : (billableHours > 0 ? (baseMonthlyCost + totalAmortization) / billableHours : 0);

        // Avoid infinite loop: only update if changed
        if (bcr !== newBCR || equipmentAmortization !== totalAmortization) {
            setState(prev => ({
                ...prev,
                financials: {
                    ...prev.financials,
                    equipmentAmortization: totalAmortization,
                    bcr: newBCR
                }
            }));
        }

    }, [
        state.financials.baseMonthlyCost,
        state.financials.billableHours,
        state.financials.bcr,
        state.financials.bcrSource,
        state.financials.equipmentAmortization,
        state.equipment,
    ]);


    const updateIdentity = (id: Partial<AgencyIdentity>) =>
        setState(prev => ({ ...prev, identity: { ...prev.identity, ...id } }));

    const updateFinancialBasics = (baseCost: number, hours: number) =>
        setState(prev => ({ ...prev, financials: { ...prev.financials, baseMonthlyCost: baseCost, billableHours: hours } }));

    // Equipment Actions
    const addEquipment = (item: Equipment) =>
        setState(prev => ({ ...prev, equipment: [...prev.equipment, item] }));

    const updateEquipment = (id: string, updates: Partial<Equipment>) =>
        setState(prev => ({ ...prev, equipment: prev.equipment.map(e => e.id === id ? { ...e, ...updates } : e) }));

    const removeEquipment = (id: string) =>
        setState(prev => ({ ...prev, equipment: prev.equipment.filter(e => e.id !== id) }));


    const updateCredits = (newCredits: number) =>
        setState(prev => ({ ...prev, user: { ...prev.user, credits: newCredits } }));

    const switchRole = (role: UserRole) =>
        setState(prev => ({ ...prev, user: { ...prev.user, role } }));

    const hydrateFromOnboarding = (data: any) => {
        const name = data.identity?.organizationName || data.identity?.name || 'Agencia';
        const currency = (data.identity?.primaryCurrency || data.identity?.currency || 'COP') as Currency;
        const country = data.identity?.country || 'CO';
        const selectedTemplates: FixedCostTemplate[] = Array.isArray(data.fixedCosts?.selectedTemplates)
            ? data.fixedCosts.selectedTemplates
            : [];

        const onboardingHours = Number(data.team?.billableHours);
        const hours = Number.isFinite(onboardingHours) && onboardingHours > 0 ? onboardingHours * 4.33 : 160;

        const nonAmortizableCosts = selectedTemplates
            .filter((template) => !(template.amortizable || template.category === 'Tools'))
            .reduce((sum, template) => {
                // Onboarding inventory amounts are normalized to primary currency before persistence.
                return sum + (Number(template.amount) || 0);
            }, 0);

        // ESTIMACIÓN PRELIMINAR: en el wizard todavía no hay nada persistido, así que
        // no existe BCR del backend al cual acudir. Se calcula con el preset de cargas
        // del país (no con el config real de la org) y queda marcado como tal; el
        // primer hidratado desde el backend lo reemplaza.
        const preview = estimateOnboardingBcrPreview({
            salary: Number(data.team?.salary) || 0,
            applySocialCharges: Boolean(data.team?.applySocialCharges),
            countryCode: country,
            nonAmortizableCosts,
            monthlyHours: hours,
        });

        const equipmentFromOnboarding: Equipment[] = selectedTemplates
            .filter((template) => template.amortizable || template.category === 'Tools')
            .map((template) => {
                const purchasePrice = Number(template.amount) || 0;
                return {
                    id: `onboarding-${template.id}`,
                    name: template.name,
                    description: 'Generado desde onboarding (costo amortizable)',
                    category: 'Hardware',
                    purchasePrice: Number(purchasePrice.toFixed(2)),
                    purchaseDate: new Date().toISOString().slice(0, 10),
                    currency,
                    usefulLifeMonths: 36,
                    salvageValue: 0,
                    depreciationMethod: 'straight_line',
                    isActive: true,
                    createdAt: new Date().toISOString(),
                };
            });
        setState(prev => ({
            ...prev,
            identity: { ...prev.identity, name, primaryCurrency: currency, country },
            financials: {
                ...prev.financials,
                baseMonthlyCost: preview.baseMonthlyCost,
                billableHours: preview.billableHours,
                bcr: preview.bcr,
                bcrSource: 'onboarding-estimate'
            },
            equipment: equipmentFromOnboarding,
            isHydrated: true
        }));
    };

    return (
        <NougramCoreContext.Provider value={{
            state,
            updateIdentity,
            updateFinancialBasics,
            addEquipment,
            updateEquipment,
            removeEquipment,
            updateCredits,
            switchRole,
            hydrateFromOnboarding
        }}>
            {children}
        </NougramCoreContext.Provider>
    );
}

export const useNougram = () => {
    const context = useContext(NougramCoreContext);
    if (!context) throw new Error('useNougram must be used within NougramCoreProvider');
    return context;
};
