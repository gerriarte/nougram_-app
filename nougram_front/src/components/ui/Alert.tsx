import * as React from "react";
import { cn } from "@/lib/utils";
import { AlertTriangle, CheckCircle, Info, XCircle } from "lucide-react";

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: "critical" | "warning" | "info" | "success";
}

export function Alert({ className, variant = "info", children, ...props }: AlertProps) {

    const variantStyles = {
        critical: "bg-red-50 border-red-200 text-red-900",
        warning: "bg-amber-50 border-amber-200 text-amber-900",
        info: "bg-blue-50 border-blue-200 text-blue-900",
        success: "bg-green-50 border-green-200 text-green-900",
    };

    const icons = {
        critical: <XCircle className="h-5 w-5 text-red-600" />,
        warning: <AlertTriangle className="h-5 w-5 text-amber-600" />,
        info: <Info className="h-5 w-5 text-blue-600" />,
        success: <CheckCircle className="h-5 w-5 text-green-600" />,
    };

    return (
        <div
            role="alert"
            className={cn(
                "relative w-full rounded-lg border p-4 flex gap-3 items-start",
                variantStyles[variant],
                className
            )}
            {...props}
        >
            <div className="flex-shrink-0 mt-0.5">
                {icons[variant]}
            </div>
            <div className="text-sm [&>p]:leading-relaxed">
                {children}
            </div>
        </div>
    );
}

export function AlertTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
    return (
        <h5 className={cn("mb-1 font-semibold leading-none tracking-tight", className)} {...props}>
            {children}
        </h5>
    );
}

export function AlertDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
    return (
        <div className={cn("text-sm opacity-90", className)} {...props}>
            {children}
        </div>
    );
}
