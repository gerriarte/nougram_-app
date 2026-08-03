/**
 * Capacidad mensual de un miembro del equipo — IMPLEMENTACIÓN ÚNICA del frontend.
 *
 * Espejo de backend/app/core/capacity.py. Si cambia una, cambia la otra.
 *
 * Decisión de producto (2026-07-27)
 * ---------------------------------
 * `billableHoursPerWeek` YA representa horas facturables: así lo rotula la propia UI
 * ("Horas Facturables / Semana"). Antes, varios lugares volvían a multiplicar por
 * `(1 - nonBillablePercentage)`, descontando dos veces — una implícita en el dato que
 * carga el usuario y otra explícita en el cálculo. El efecto era inflar el BCR
 * (menos horas en el denominador) y subestimar la capacidad del equipo.
 *
 * `nonBillablePercentage` sigue siendo un dato informativo del miembro (se muestra como
 * "% Admin"), pero NO participa del cálculo de capacidad.
 */

/** Promedio de semanas por mes (52 / 12). */
export const WEEKS_PER_MONTH = 4.33;

/**
 * Horas facturables al mes.
 *
 * Devuelve 0 ante datos ausentes o inválidos: una capacidad de 0 es la lectura
 * conservadora (no se le puede asignar trabajo) y evita propagar NaN a la UI.
 */
export function monthlyBillableHours(billableHoursPerWeek: unknown): number {
    const weekly = Number(billableHoursPerWeek);
    if (!Number.isFinite(weekly) || weekly <= 0) return 0;
    return weekly * WEEKS_PER_MONTH;
}

/** Convierte horas mensuales a semanales (operación inversa, usada por el onboarding). */
export function weeklyFromMonthlyHours(billableHoursPerMonth: unknown): number {
    const monthly = Number(billableHoursPerMonth);
    if (!Number.isFinite(monthly) || monthly <= 0) return 0;
    return monthly / WEEKS_PER_MONTH;
}
