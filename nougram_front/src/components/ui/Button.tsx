import * as React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "destructive" | "ghost" | "outline";
    size?: "default" | "sm" | "lg" | "icon";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className = "", variant = "primary", size = "default", ...props }, ref) => {

        const baseStyles = "inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";

        const variants = {
            primary: "bg-primary text-white hover:bg-blue-600 focus:ring-blue-500",
            secondary: "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-blue-500",
            destructive: "bg-red-500 text-white hover:bg-red-700 focus:ring-red-500",
            ghost: "bg-transparent text-gray-700 hover:bg-gray-100 hover:text-gray-900 focus:ring-gray-500",
            outline: "bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500",
        };

        const sizes = {
            default: "px-4 py-2 text-sm",
            sm: "px-3 py-1.5 text-xs",
            lg: "px-6 py-3 text-base",
            icon: "h-9 w-9",
        };

        const combinedClassName = `${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`;

        return (
            <button
                ref={ref}
                className={combinedClassName}
                {...props}
            />
        );
    }
);
Button.displayName = "Button";
