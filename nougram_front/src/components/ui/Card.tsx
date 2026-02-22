import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({ className = "", children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={cn(
                "bg-white/70 backdrop-blur-xl border border-white/20 rounded-2xl shadow-[0_8px_32px_0_rgba(0,0,0,0.05)] overflow-hidden",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardHeader({ className = "", children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={cn("px-8 py-6 border-b border-gray-100/50", className)} {...props}>
            {children}
        </div>
    );
}

export function CardTitle({ className = "", children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
    return (
        <h3 className={cn("text-xl font-bold text-gray-900 tracking-tight", className)} {...props}>
            {children}
        </h3>
    );
}

export function CardContent({ className = "", children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={cn("p-8", className)} {...props}>
            {children}
        </div>
    );
}

export function CardFooter({ className = "", children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={cn("px-8 py-5 bg-gray-50/30 border-t border-gray-100/50", className)} {...props}>
            {children}
        </div>
    );
}

export function CardDescription({ className = "", children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
    return (
        <p className={cn("text-sm text-system-gray font-medium", className)} {...props}>
            {children}
        </p>
    );
}
