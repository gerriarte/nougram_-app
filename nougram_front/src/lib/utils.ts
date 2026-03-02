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
        maximumFractionDigits: 0,
    }).format(numberValue);
};
