import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Format currency for Colombia
export const formatCurrency = (value: number | string) => {
    const numberValue = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(numberValue)) return "";

    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(numberValue);
};
