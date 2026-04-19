import * as React from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    isCurrency?: boolean;
    // When true, all dots/commas are treated as thousands separators (no decimal allowed).
    // Use for salary and other integer-only monetary fields.
    isInteger?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, isCurrency, isInteger, onChange, value, defaultValue, ...props }, ref) => {
        const isFormattedNumeric = Boolean(isCurrency || type === "number");

        const parseToCanonicalNumberString = React.useCallback((rawValue: string): string => {
            if (!rawValue) return "";

            const cleaned = rawValue.replace(/[^\d,.\-]/g, "");
            const isNegative = cleaned.startsWith("-");
            const unsigned = cleaned.replace(/-/g, "");

            const dotCount = (unsigned.match(/\./g) || []).length;
            const commaCount = (unsigned.match(/,/g) || []).length;

            let integerPart: string;
            let normalizedDecimal = "";

            if (isInteger) {
                // Integer mode: ALL separators are thousands separators, no decimal
                integerPart = unsigned.replace(/[.,]/g, "");
            } else if (commaCount === 1 && dotCount >= 1) {
                // es-CO format: dots=thousands, comma=decimal  e.g. "1.000.000,50"
                const commaIdx = unsigned.lastIndexOf(",");
                integerPart = unsigned.slice(0, commaIdx).replace(/\./g, "");
                normalizedDecimal = unsigned.slice(commaIdx + 1).replace(/[^\d]/g, "");
            } else if (dotCount > 1) {
                // Multiple dots → all are thousands separators  e.g. "1.000.000"
                integerPart = unsigned.replace(/\./g, "");
            } else if (commaCount > 1) {
                // Multiple commas → all are thousands separators  e.g. "1,000,000"
                integerPart = unsigned.replace(/,/g, "");
            } else {
                // Single separator or none
                const lastComma = unsigned.lastIndexOf(",");
                const lastDot = unsigned.lastIndexOf(".");
                const decimalIndex = Math.max(lastComma, lastDot);

                if (decimalIndex >= 0) {
                    const afterSep = unsigned.slice(decimalIndex + 1).replace(/[^\d]/g, "");
                    // In es-CO convention a dot followed by 3+ digits is a thousands separator.
                    // e.g. "1.000" → 1000, "1.0000" (user extended "1.000") → 10000
                    // Dots with 1-2 following digits are decimal: "0.20" → 0.20
                    if (decimalIndex === lastDot && afterSep.length >= 3) {
                        integerPart = unsigned.replace(/\./g, "");
                        normalizedDecimal = "";
                    } else {
                        integerPart = unsigned.slice(0, decimalIndex).replace(/[.,]/g, "");
                        normalizedDecimal = afterSep;
                    }
                } else {
                    integerPart = unsigned;
                }
            }

            const normalizedInteger = integerPart.replace(/^0+(?=\d)/, "") || "0";

            const canonical = normalizedDecimal.length > 0
                ? `${normalizedInteger}.${normalizedDecimal}`
                : normalizedInteger;

            return isNegative ? `-${canonical}` : canonical;
        }, [isInteger]);

        const formatNumberWithDotThousands = React.useCallback((canonicalValue: string): string => {
            if (!canonicalValue) return "";

            const isNegative = canonicalValue.startsWith("-");
            const unsigned = isNegative ? canonicalValue.slice(1) : canonicalValue;
            const [integerPartRaw, decimalPartRaw] = unsigned.split(".");
            const integerPart = integerPartRaw || "0";
            const groupedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
            const formatted = decimalPartRaw !== undefined && decimalPartRaw.length > 0
                ? `${groupedInteger},${decimalPartRaw}`
                : groupedInteger;

            return isNegative ? `-${formatted}` : formatted;
        }, []);

        const resolveRawValue = React.useCallback((): string => {
            if (value !== undefined && value !== null) return String(value);
            if (defaultValue !== undefined && defaultValue !== null) return String(defaultValue);
            return "";
        }, [value, defaultValue]);

        const [displayValue, setDisplayValue] = React.useState<string>(() => {
            if (!isFormattedNumeric) return resolveRawValue();
            const canonical = parseToCanonicalNumberString(resolveRawValue());
            return formatNumberWithDotThousands(canonical);
        });

        React.useEffect(() => {
            if (!isFormattedNumeric) return;
            const canonical = parseToCanonicalNumberString(resolveRawValue());
            setDisplayValue(formatNumberWithDotThousands(canonical));
        }, [isFormattedNumeric, resolveRawValue, parseToCanonicalNumberString, formatNumberWithDotThousands]);

        const emitNormalizedChange = (normalizedValue: string, event: React.ChangeEvent<HTMLInputElement>) => {
            if (!onChange) return;
            const syntheticEvent = {
                ...event,
                target: { ...event.target, value: normalizedValue },
                currentTarget: { ...event.currentTarget, value: normalizedValue },
            } as React.ChangeEvent<HTMLInputElement>;
            onChange(syntheticEvent);
        };

        const baseStyles = "flex h-12 w-full rounded-xl border border-transparent bg-gray-200/50 px-4 py-2 text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400/30 focus:bg-white transition-all disabled:cursor-not-allowed disabled:opacity-50";

        const handleNumericChange = (event: React.ChangeEvent<HTMLInputElement>) => {
            const normalized = parseToCanonicalNumberString(event.target.value);
            setDisplayValue(formatNumberWithDotThousands(normalized));
            emitNormalizedChange(normalized, event);
        };

        if (isCurrency) {
            return (
                <div className="relative group">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold pointer-events-none group-focus-within:text-primary transition-colors">
                        $
                    </span>
                    <input
                        {...props}
                        type="text"
                        inputMode="decimal"
                        ref={ref}
                        value={displayValue}
                        onChange={handleNumericChange}
                        className={cn(baseStyles, "pl-8 pr-12 text-right tabular-nums", className)}
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-[10px] font-black tracking-widest pointer-events-none">
                        COP
                    </span>
                </div>
            );
        }

        if (type === "number") {
            return (
                <input
                    {...props}
                    type="text"
                    inputMode={isInteger ? "numeric" : "decimal"}
                    className={cn(baseStyles, className)}
                    ref={ref}
                    value={displayValue}
                    onChange={handleNumericChange}
                />
            );
        }

        return (
            <input
                type={type}
                className={cn(baseStyles, className)}
                ref={ref}
                value={value}
                defaultValue={defaultValue}
                onChange={onChange}
                {...props}
            />
        );
    }
);
Input.displayName = "Input";
