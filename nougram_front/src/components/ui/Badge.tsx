import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: "success" | "warning" | "critical" | "info" | "default";
}

export function Badge({ className = "", variant = "default", children, ...props }: BadgeProps) {

    const variants = {
        default: "bg-gray-100 text-gray-700",
        success: "bg-green-100 text-green-900 border-none",
        warning: "bg-orange-100 text-orange-900 border-none",
        critical: "bg-red-100 text-red-900 border-none",
        info: "bg-blue-100 text-blue-900 border-none",
    };

    return (
        <span
            className={cn(
                "inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider",
                variants[variant],
                className
            )}
            {...props}
        >
            {children}
        </span>
    );
}
