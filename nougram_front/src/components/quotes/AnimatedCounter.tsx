import React, { useEffect, useRef, useState } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

interface AnimatedCounterProps {
    value: number;
    currency?: string;
    className?: string;
}

export function AnimatedCounter({ value, currency, className }: AnimatedCounterProps) {
    const spring = useSpring(0, { stiffness: 60, damping: 15 });
    const display = useTransform(spring, (current) => Math.round(current));
    const [displayValue, setDisplayValue] = useState(0);

    useEffect(() => {
        spring.set(value);
    }, [spring, value]);

    useEffect(() => {
        return display.on("change", (latest) => {
            setDisplayValue(latest);
        });
    }, [display]);

    return (
        <span className={className}>
            {currency && <span className="mr-1">{currency}</span>}
            {displayValue.toLocaleString()}
        </span>
    );
}
