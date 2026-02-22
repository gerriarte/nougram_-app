
import * as React from "react"

const TabsContext = React.createContext<{
    value: string;
    onValueChange: (value: string) => void;
} | null>(null);

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
    value?: string;
    defaultValue?: string;
    onValueChange?: (value: string) => void;
}

export function Tabs({ value, defaultValue, onValueChange, children, className, ...props }: TabsProps) {
    const [internalValue, setInternalValue] = React.useState(defaultValue || "");
    const currentValue = value !== undefined ? value : internalValue;

    const handleValueChange = React.useCallback((newValue: string) => {
        setInternalValue(newValue);
        onValueChange?.(newValue);
    }, [onValueChange]);

    return (
        <TabsContext.Provider value={{ value: currentValue, onValueChange: handleValueChange }}>
            <div className={className} {...props}>
                {children}
            </div>
        </TabsContext.Provider>
    );
}

export const TabsList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    ({ className, ...props }, ref) => (
        <div
            ref={ref}
            className={`inline-flex items-center justify-center rounded-lg bg-gray-100 p-1 text-gray-500 ${className || ''}`}
            {...props}
        />
    )
)
TabsList.displayName = "TabsList"

export interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    value: string;
}

export const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
    ({ className, value, ...props }, ref) => {
        const context = React.useContext(TabsContext);
        const isActive = context?.value === value;

        return (
            <button
                ref={ref}
                type="button"
                onClick={() => context?.onValueChange(value)}
                data-state={isActive ? "active" : "inactive"}
                className={`inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-white data-[state=active]:text-gray-950 data-[state=active]:shadow-sm ${className || ''}`}
                {...props}
            />
        )
    }
)
TabsTrigger.displayName = "TabsTrigger"

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
    value: string;
}

export const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
    ({ className, value, ...props }, ref) => {
        const context = React.useContext(TabsContext);
        if (context?.value !== value) return null;

        return (
            <div
                ref={ref}
                className={`mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 focus-visible:ring-offset-2 ${className || ''}`}
                {...props}
            />
        )
    }
)
TabsContent.displayName = "TabsContent"
