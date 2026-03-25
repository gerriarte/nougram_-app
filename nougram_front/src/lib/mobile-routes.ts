/**
 * Canonical client routes for commercial flows (avoid /projects/new vs /dashboard/quotes/* drift).
 */
export const CANONICAL_NEW_QUOTE_PATH = "/dashboard/quotes/create" as const;
