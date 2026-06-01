/**
 * DEPRECATED — pricing math has moved to the backend (single source of truth).
 *
 * The frontend must NEVER calculate prices, costs or margins. Use
 * `quoteService.calculate(...)` which calls `POST /quotes/calculate` and returns
 * the authoritative numbers. This module is kept only to fail loudly if any old
 * code path tries to compute pricing on the client.
 */

const DEPRECATED_MESSAGE =
    'pricingService is deprecated: the backend is the single source of truth. ' +
    'Use quoteService.calculate() instead of calculating on the client.';

export const pricingService = {
    calculateItem(): never {
        throw new Error(DEPRECATED_MESSAGE);
    },
    calculateQuoteTotals(): never {
        throw new Error(DEPRECATED_MESSAGE);
    },
};
