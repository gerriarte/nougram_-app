import { test, expect } from '@playwright/test';
import { decideRootRoute, type RootRouteInput } from '@/context/NougramCoreContext';

/**
 * Tests unitarios (sin navegador) de la decisión de la ruta raíz '/'.
 * Cubren H18: la pantalla no puede quedarse en el spinner "Cargando Nougram OS..."
 * cuando el backend acepta la conexión y no contesta nunca.
 *
 * Escenario del bloqueante: `fetch` no tiene timeout, así que con el backend
 * colgado a nivel TCP ni GET /auth/me (que apaga `authLoading`) ni
 * GET /settings/equipment (que enciende `isHydrated`) settlean jamás, y
 * GET /admin/financial-summary deja `bcrSource` en 'none'. La decisión, entonces,
 * no puede estar detrás de ninguna de esas tres banderas.
 */

/** Backend colgado a nivel TCP: nada resolvió, nada va a resolver. */
const NOTHING_RESOLVED: RootRouteInput = {
    authLoading: true,
    isAuthenticated: false,
    hasStoredSession: true,
    isHydrated: false,
    bcr: 0,
    bcrSource: 'none',
    bailedOut: false,
};

function input(overrides: Partial<RootRouteInput> = {}): RootRouteInput {
    return { ...NOTHING_RESOLVED, ...overrides };
}

/**
 * Lógica ANTERIOR de page.tsx, transcrita para dejar la regresión documentada:
 * la guarda de espera cortaba antes de que la red de seguridad pudiera evaluarse.
 */
function decideRootRouteLegacy(i: RootRouteInput): RootRouteDecisionLike {
    if (i.authLoading || !i.isHydrated) return null; // ← cortaba acá, siempre
    if (!i.isAuthenticated) return '/login';
    if (i.bcrSource === 'none' && !i.bailedOut) return null;
    return i.bcr === 0 ? '/onboarding' : '/dashboard';
}
type RootRouteDecisionLike = '/login' | '/onboarding' | '/dashboard' | null;

test.describe('H18 — la ruta raíz siempre decide, aunque ningún request settlee', () => {
    test('con el backend colgado y el techo vencido, decide en vez de girar', () => {
        const hungBackend = input({ bailedOut: true });

        // Con el código viejo la pantalla giraba para siempre incluso con el techo
        // vencido, porque `authLoading` e `isHydrated` nunca cambiaban.
        expect(decideRootRouteLegacy(hungBackend)).toBeNull();

        expect(decideRootRoute(hungBackend)).toBe('/dashboard');
    });

    test('antes del techo sigue esperando (no decide con datos a medias)', () => {
        expect(decideRootRoute(input())).toBeNull();
    });

    test('el techo vencido no depende de isHydrated', () => {
        // isHydrated cuelga de GET /settings/equipment, que puede no settlear nunca.
        expect(decideRootRoute(input({ isHydrated: false, bailedOut: true }))).not.toBeNull();
    });

    test('el techo vencido no depende de authLoading', () => {
        // authLoading cuelga de GET /auth/me, que puede no settlear nunca.
        expect(decideRootRoute(input({ authLoading: true, bailedOut: true }))).not.toBeNull();
    });

    test('el techo vencido no depende de bcrSource', () => {
        // bcrSource cuelga de GET /admin/financial-summary.
        expect(decideRootRoute(input({ bcrSource: 'none', bailedOut: true }))).not.toBeNull();
    });

    test('sin sesión resuelta ni token persistido, el techo manda a /login', () => {
        expect(
            decideRootRoute(input({ authLoading: true, hasStoredSession: false, bailedOut: true }))
        ).toBe('/login');
    });

    test('bcr=0 y bcrSource="none" no manda a onboarding: no se sabe si está configurada', () => {
        // Con el resumen financiero perdido, bcr=0 es "no sé", no "falta onboarding".
        // Mandar a onboarding a una org ya configurada era la regresión original.
        expect(decideRootRoute(input({ bcr: 0, bcrSource: 'none', bailedOut: true }))).toBe(
            '/dashboard'
        );
    });

    test('si el BCR sí se resolvió, el techo no cambia el destino', () => {
        // 'backend' y 'unavailable' significan "hubo respuesta": bcr=0 es un dato,
        // no una incógnita, y sigue mandando a onboarding como siempre.
        expect(
            decideRootRoute(
                input({ authLoading: false, isAuthenticated: true, bcr: 0, bcrSource: 'backend', bailedOut: true })
            )
        ).toBe('/onboarding');

        expect(
            decideRootRoute(
                input({ authLoading: false, isAuthenticated: true, bcr: 52_000, bcrSource: 'backend', bailedOut: true })
            )
        ).toBe('/dashboard');
    });

    test('con sesión resuelta como anónima, el token viejo no la resucita', () => {
        expect(
            decideRootRoute(
                input({ authLoading: false, isAuthenticated: false, hasStoredSession: true, bailedOut: true })
            )
        ).toBe('/login');
    });
});

test.describe('camino feliz — el techo no cambia la decisión normal', () => {
    const resolved = (overrides: Partial<RootRouteInput> = {}): RootRouteInput =>
        input({
            authLoading: false,
            isAuthenticated: true,
            isHydrated: true,
            bcrSource: 'backend',
            ...overrides,
        });

    test('org configurada va al dashboard', () => {
        expect(decideRootRoute(resolved({ bcr: 52_000 }))).toBe('/dashboard');
    });

    test('org sin BCR va a onboarding', () => {
        expect(decideRootRoute(resolved({ bcr: 0 }))).toBe('/onboarding');
    });

    test('usuario anónimo va a login sin esperar la hidratación del BCR', () => {
        expect(
            decideRootRoute(
                resolved({ isAuthenticated: false, hasStoredSession: false, bcrSource: 'none' })
            )
        ).toBe('/login');
    });

    test('con el BCR aún sin resolver espera, pero solo hasta el techo', () => {
        const waiting = resolved({ bcrSource: 'none' });
        expect(decideRootRoute(waiting)).toBeNull();
        expect(decideRootRoute({ ...waiting, bailedOut: true })).toBe('/dashboard');
    });

    test('el backend respondió "no disponible": se decide igual, no se espera', () => {
        expect(decideRootRoute(resolved({ bcrSource: 'unavailable', bcr: 0 }))).toBe('/onboarding');
    });
});
