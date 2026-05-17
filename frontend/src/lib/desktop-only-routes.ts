/**
 * Paths that require a desktop viewport (costs, finance, admin).
 * Matched with exact path or prefix `${p}/`.
 */
export const DESKTOP_ONLY_PATH_PREFIXES: readonly string[] = [
  "/admin",
  "/analytics",
  "/billing",
  "/dashboard/operational-costs",
  "/dashboard/overhead-costs",
  "/dashboard/payroll-costs",
  "/dashboard/tax-costs",
  "/dashboard/cash-flow",
  "/dashboard/cash-flow-budget",
  "/dashboard/invoices",
  "/dashboard/super-admin",
  "/dashboard/resources/availability",
  "/dashboard/users",
  "/dashboard/organization",
];

export function isDesktopOnlyPath(pathname: string | null): boolean {
  if (!pathname) return false;
  return DESKTOP_ONLY_PATH_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}
