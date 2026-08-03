/**
 * ESTIMACIÓN PREVIA DE ONBOARDING — NO es el BCR real de la organización.
 *
 * El BCR real lo calcula el backend (`/admin/financial-summary` →
 * `blendedCostRate`): normaliza todas las monedas a la moneda primaria de la
 * organización, aplica el config de cargas sociales persistido e incluye la
 * amortización de equipos. Ese es el único número que puede usarse para cotizar.
 *
 * Durante el wizard de onboarding todavía no hay nada persistido, así que no hay
 * backend del cual leer: lo único posible es previsualizar. Este módulo existe
 * para que esa previsualización sea EXPLÍCITA y esté AISLADA, en vez de vivir
 * mezclada con el estado financiero real. Sus supuestos:
 *
 *   - un único tipo de cambio implícito: se asume que todos los importes ya
 *     vienen en la misma moneda (el wizard fuerza moneda única);
 *   - cargas sociales por preset de país (curadas en social-charges-presets.ts),
 *     no por el config real de la organización;
 *   - sin amortización de equipos más allá de lo que el wizard ya modeló.
 *
 * Cualquier valor producido acá debe quedar marcado como `bcrSource:
 * 'onboarding-estimate'` y ser reemplazado por el del backend en cuanto exista.
 */

import { getSocialChargesMultiplierByCountry } from '@/lib/social-charges-presets';

export type OnboardingBcrPreviewInput = {
    /** Sueldo bruto mensual modelado en el wizard. */
    salary: number;
    /** Si el wizard pidió aplicar cargas sociales sobre ese sueldo. */
    applySocialCharges: boolean;
    /** País declarado en el wizard (ISO-2 o ISO-3; se resuelven alias). */
    countryCode?: string;
    /** Costos fijos mensuales no amortizables ya modelados. */
    nonAmortizableCosts: number;
    /** Capacidad mensual estimada en horas. */
    monthlyHours: number;
};

export type OnboardingBcrPreview = {
    /** Costo mensual base estimado (nómina con cargas + costos fijos). */
    baseMonthlyCost: number;
    /** Horas mensuales usadas en la estimación. */
    billableHours: number;
    /** Costo/hora estimado. Preliminar: no cotizar con esto. */
    bcr: number;
    /** Multiplicador de cargas aplicado, para poder mostrarlo/auditarlo en UI. */
    socialChargesMultiplier: number;
};

/** Estimación preliminar del BCR mientras el onboarding no persistió nada. */
export function estimateOnboardingBcrPreview(
    input: OnboardingBcrPreviewInput
): OnboardingBcrPreview {
    const multiplier = input.applySocialCharges
        ? getSocialChargesMultiplierByCountry(input.countryCode)
        : 1;

    const salary = Number(input.salary) || 0;
    const fixedCosts = Number(input.nonAmortizableCosts) || 0;
    const hours = Number(input.monthlyHours) || 0;

    const baseMonthlyCost = salary * multiplier + fixedCosts;

    return {
        baseMonthlyCost,
        billableHours: hours,
        bcr: hours > 0 ? baseMonthlyCost / hours : 0,
        socialChargesMultiplier: multiplier,
    };
}
