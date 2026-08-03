import { test, expect } from '@playwright/test';
import {
    computeQuoteBuilderValidation,
    computeMemberUtilization,
    markItemAsCreatedInSession,
    isItemCreatedInSession,
    PRICE_BELOW_COST_ERROR,
} from '@/context/QuoteBuilderContext';
import type {
    QuoteBuilderState,
    QuoteItem,
    TeamMemberMock,
} from '@/types/quote-builder';

/**
 * Tests unitarios (sin navegador) de la validación del builder de cotizaciones.
 * Cubren H14 (alcance obligatorio solo en ítems nuevos) y H13 (sobreasignación
 * como advertencia, no como bloqueo del guardado).
 */

function makeItem(overrides: Partial<QuoteItem> = {}): QuoteItem {
    return {
        id: 'item-1',
        serviceId: 7,
        serviceName: 'Rediseño web',
        pricingType: 'fixed',
        quantity: 1,
        fixedPrice: 1_000_000,
        allocations: [],
        internalCost: 600_000,
        clientPrice: 1_000_000,
        marginPercentage: 0.4,
        ...overrides,
    };
}

function makeState(overrides: Partial<QuoteBuilderState> = {}): QuoteBuilderState {
    return {
        step: 'editor',
        projectName: 'Proyecto Demo',
        clientName: 'Cliente Demo',
        clientCompany: '',
        clientRequester: '',
        clientEmail: '',
        projectType: '',
        projectDescription: '',
        currency: 'COP',
        items: [],
        expenses: [],
        selectedTaxIds: [],
        targetMargin: 0.35,
        allowLowMargin: false,
        showResourceAllocation: false,
        resourceAllocations: [],
        ...overrides,
    };
}

const HEALTHY_SUMMARY = { totalClientPrice: 1_000_000, totalInternalCost: 600_000 };

/** Diseñador Gráfico Senior del repro de H13: 32 h/semana × 4.33 = 138.56 h/mes. */
const DESIGNER: TeamMemberMock = {
    id: 12,
    name: 'Diseñador Gráfico Senior',
    role: 'Diseño',
    availableHours: 138.56,
};

test.describe('H14 — el alcance solo es obligatorio en ítems nuevos', () => {
    test('un ítem cargado desde una cotización existente sin descripción no bloquea el guardado', () => {
        // Así llegan los ítems de loadQuote: sin marca de sesión y sin description,
        // porque la columna quote_items.description es nueva y nunca se pobló.
        const state = makeState({ items: [makeItem({ description: undefined })] });

        const { errors } = computeQuoteBuilderValidation({
            state,
            summary: HEALTHY_SUMMARY,
            teamMembers: [],
        });

        expect(errors).toEqual([]);
    });

    test('un ítem creado en esta sesión sin descripción sí bloquea el guardado', () => {
        const state = makeState({
            items: [markItemAsCreatedInSession(makeItem({ description: undefined }))],
        });

        const { errors } = computeQuoteBuilderValidation({
            state,
            summary: HEALTHY_SUMMARY,
            teamMembers: [],
        });

        expect(errors).toContain('Un ítem nuevo sin descripción del alcance');
    });

    test('un ítem creado en esta sesión con descripción no bloquea', () => {
        const state = makeState({
            items: [markItemAsCreatedInSession(makeItem({ description: 'Wireframes + UI de 8 pantallas' }))],
        });

        const { errors } = computeQuoteBuilderValidation({
            state,
            summary: HEALTHY_SUMMARY,
            teamMembers: [],
        });

        expect(errors).toEqual([]);
    });

    test('la marca no se infiere de la forma del id: un id numérico recién creado también exige alcance', () => {
        const numericIdOld = makeItem({ id: '42', description: undefined });
        const numericIdNew = markItemAsCreatedInSession(makeItem({ id: '42', description: undefined }));

        expect(isItemCreatedInSession(numericIdOld)).toBe(false);
        expect(isItemCreatedInSession(numericIdNew)).toBe(true);

        const uuidOld = makeItem({ id: '0f5f5e1a-2f4b-4a5e-9f3a-1c2d3e4f5a6b', description: undefined });
        expect(isItemCreatedInSession(uuidOld)).toBe(false);
        expect(
            computeQuoteBuilderValidation({
                state: makeState({ items: [uuidOld] }),
                summary: HEALTHY_SUMMARY,
                teamMembers: [],
            }).errors
        ).toEqual([]);
    });

    test('el título sigue siendo obligatorio para cualquier ítem', () => {
        const state = makeState({ items: [makeItem({ serviceName: '   ', description: 'algo' })] });

        const { errors } = computeQuoteBuilderValidation({
            state,
            summary: HEALTHY_SUMMARY,
            teamMembers: [],
        });

        expect(errors).toContain('Un ítem sin título');
    });

    test('varios ítems nuevos sin alcance se reportan en plural', () => {
        const state = makeState({
            items: [
                markItemAsCreatedInSession(makeItem({ id: 'a' })),
                markItemAsCreatedInSession(makeItem({ id: 'b' })),
                makeItem({ id: 'c' }),
            ],
        });

        const { errors } = computeQuoteBuilderValidation({
            state,
            summary: HEALTHY_SUMMARY,
            teamMembers: [],
        });

        expect(errors).toContain('2 ítems nuevos sin descripción del alcance');
    });
});

test.describe('H13 — la sobreasignación advierte pero no bloquea', () => {
    const overAllocatedState = makeState({
        items: [
            makeItem({
                description: 'Rediseño completo',
                allocations: [
                    { id: 'alloc-1', teamMemberId: DESIGNER.id, hours: 300 },
                ],
            }),
        ],
    });

    test('300 h sobre 138.56 h/mes no apagan isValid', () => {
        const { errors } = computeQuoteBuilderValidation({
            state: overAllocatedState,
            summary: HEALTHY_SUMMARY,
            teamMembers: [DESIGNER],
        });

        expect(errors).toEqual([]);
    });

    test('la sobreasignación se reporta como advertencia con el porcentaje real', () => {
        const { warnings } = computeQuoteBuilderValidation({
            state: overAllocatedState,
            summary: HEALTHY_SUMMARY,
            teamMembers: [DESIGNER],
        });

        expect(warnings).toHaveLength(1);
        expect(warnings[0]).toContain('Diseñador Gráfico Senior');
        expect(warnings[0]).toContain('216,5%');
    });

    test('sin sobreasignación no hay advertencias', () => {
        const state = makeState({
            items: [
                makeItem({
                    allocations: [{ id: 'alloc-1', teamMemberId: DESIGNER.id, hours: 100 }],
                }),
            ],
        });

        const { errors, warnings } = computeQuoteBuilderValidation({
            state,
            summary: HEALTHY_SUMMARY,
            teamMembers: [DESIGNER],
        });

        expect(errors).toEqual([]);
        expect(warnings).toEqual([]);
    });

    test('un miembro sin capacidad conocida no genera advertencia', () => {
        const state = makeState({
            items: [
                makeItem({
                    allocations: [{ id: 'alloc-1', teamMemberId: 99, hours: 500 }],
                }),
            ],
        });

        const { warnings } = computeQuoteBuilderValidation({
            state,
            summary: HEALTHY_SUMMARY,
            teamMembers: [{ id: 99, name: 'Sin capacidad', role: 'X', availableHours: 0 }],
        });

        expect(warnings).toEqual([]);
    });

    test('computeMemberUtilization suma las asignaciones por ítem y las legacy', () => {
        const state = makeState({
            resourceAllocations: [{ id: 'legacy-1', teamMemberId: DESIGNER.id, hours: 20 }],
            items: [
                makeItem({ allocations: [{ id: 'alloc-1', teamMemberId: DESIGNER.id, hours: 30 }] }),
            ],
        });

        const util = computeMemberUtilization(DESIGNER.id, state, [DESIGNER]);

        expect(util.used).toBe(50);
        expect(util.capacity).toBe(138.56);
    });

    test('los errores que sí deben bloquear siguen bloqueando', () => {
        const { errors } = computeQuoteBuilderValidation({
            state: makeState({ projectName: '', clientName: '', items: [] }),
            summary: HEALTHY_SUMMARY,
            teamMembers: [],
        });

        expect(errors).toContain('Nombre del proyecto requerido');
        expect(errors).toContain('Cliente requerido');
        expect(errors).toContain('Al menos un ítem de servicio requerido (gastos de proveedor no bastan)');
    });

    test('precio por debajo del costo sigue bloqueando', () => {
        const { errors } = computeQuoteBuilderValidation({
            state: makeState({ items: [makeItem()] }),
            summary: { totalClientPrice: 100, totalInternalCost: 500 },
            teamMembers: [],
        });

        expect(errors).toContain(PRICE_BELOW_COST_ERROR);
    });

    test('allowLowMargin es la vía de escape del precio bajo costo', () => {
        // Sin esto el usuario queda en un callejón sin salida: el error apaga isValid y
        // no hay forma de crear la propuesta aunque vender bajo costo sea intencional.
        const { errors } = computeQuoteBuilderValidation({
            state: makeState({ items: [makeItem()], allowLowMargin: true }),
            summary: { totalClientPrice: 100, totalInternalCost: 500 },
            teamMembers: [],
        });

        expect(errors).not.toContain(PRICE_BELOW_COST_ERROR);
    });
});
