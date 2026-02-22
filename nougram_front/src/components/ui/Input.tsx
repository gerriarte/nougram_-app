import * as React from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    // If true, behaves as a controlled currency input
    isCurrency?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, isCurrency, ...props }, ref) => {

        // Base input styles
        const baseStyles = "flex h-12 w-full rounded-xl border border-transparent bg-gray-200/50 px-4 py-2 text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:bg-white transition-all disabled:cursor-not-allowed disabled:opacity-50";

        // If currency, we need a wrapper for the prefix/suffix
        if (isCurrency) {
            return (
                <div className="relative group">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-system-gray font-bold pointer-events-none group-focus-within:text-blue-500 transition-colors">
                        $
                    </span>
                    <input
                        {...props}
                        type="text" // Always text for formatted currency inputs internally
                        ref={ref}
                        className={cn(baseStyles, "pl-8 pr-12 text-right tabular-nums", className)}
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-system-gray text-[10px] font-black tracking-widest pointer-events-none">
                        COP
                    </span>
                </div>
            );
        }

        return (
            <input
                type={type}
                className={cn(baseStyles, className)}
                ref={ref}
                {...props}
            />
        );
    }
);
Input.displayName = "Input";
