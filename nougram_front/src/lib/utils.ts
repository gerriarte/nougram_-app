import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Format currency for Colombia
export const formatCurrency = (value: number | string, currency: string = "COP") => {
    const numberValue = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(numberValue)) return "";
    const normalizedCurrency = (currency || "COP").toUpperCase();

    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: normalizedCurrency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    }).format(numberValue);
};

// Keep monetary displays visually consistent across quote editor and pipeline.
export const formatMoneyAmount = (value: number | string) => {
    const numberValue = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(numberValue)) return "0";

    return new Intl.NumberFormat("es-CO", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    }).format(numberValue);
};

const ZERO_DECIMAL_CURRENCIES = new Set(["COP", "CLP", "JPY", "KRW"]);

const currencyUsesZeroDecimals = (currencyCode?: string) => {
    if (!currencyCode) return false;
    return ZERO_DECIMAL_CURRENCIES.has(String(currencyCode).toUpperCase());
};

export const parseLocalizedNumberInput = (
    raw: string,
    options?: { allowDecimal?: boolean }
): number => {
    const allowDecimal = options?.allowDecimal ?? true;
    const normalized = String(raw ?? "")
        .trim()
        .replace(/\s/g, "")
        .replace(/\./g, "")
        .replace(",", ".")
        .replace(allowDecimal ? /[^\d.-]/g : /[^\d-]/g, "");

    if (!normalized || normalized === "-" || normalized === "." || normalized === "-.") {
        return 0;
    }

    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
};

export const formatLocalizedNumberInput = (
    value: number | string | null | undefined,
    options?: {
        minimumFractionDigits?: number;
        maximumFractionDigits?: number;
        currencyCode?: string;
    }
) => {
    if (value === null || value === undefined || value === "") return "";
    const numericValue = typeof value === "number" ? value : parseLocalizedNumberInput(value);
    if (!Number.isFinite(numericValue)) return "";
    const forceInteger = currencyUsesZeroDecimals(options?.currencyCode);

    return new Intl.NumberFormat("es-CO", {
        minimumFractionDigits: forceInteger ? 0 : (options?.minimumFractionDigits ?? 0),
        maximumFractionDigits: forceInteger ? 0 : (options?.maximumFractionDigits ?? 2),
    }).format(numericValue);
};
