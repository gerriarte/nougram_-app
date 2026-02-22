import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, Check } from 'lucide-react';
import { clientService, Client } from '@/services/clientService';
import { Input } from '@/components/ui/Input'; // Assuming exist
import { cn } from '@/lib/utils'; // Assuming exist

interface ClientAutocompleteProps {
    value: string;
    onChange: (name: string) => void;
    onSelect: (client: Client) => void;
    className?: string;
}

export function ClientAutocomplete({ value, onChange, onSelect, className }: ClientAutocompleteProps) {
    const [query, setQuery] = useState(value);
    const [results, setResults] = useState<Client[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Debounce
    useEffect(() => {
        const timer = setTimeout(async () => {
            if (query.length >= 2) {
                setIsLoading(true);
                try {
                    const data = await clientService.searchClients(query);
                    setResults(data);
                    setIsOpen(true);
                } finally {
                    setIsLoading(false);
                }
            } else {
                setResults([]);
                setIsOpen(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);

    // Handle outside click to close
    const wrapperRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (client: Client) => {
        setQuery(client.name);
        onChange(client.name);
        onSelect(client);
        setIsOpen(false);
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setQuery(e.target.value);
        onChange(e.target.value);
    };

    return (
        <div ref={wrapperRef} className={cn("relative", className)}>
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                    value={query}
                    onChange={handleChange}
                    onFocus={() => query.length >= 2 && setIsOpen(true)}
                    placeholder="Buscar cliente..."
                    className="pl-9 glass-input"
                />
                {isLoading && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-blue-500" />
                )}
            </div>

            <AnimatePresence>
                {isOpen && results.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="absolute z-50 w-full mt-2 bg-white/80 backdrop-blur-xl border border-white/40 rounded-xl shadow-xl overflow-hidden"
                    >
                        <ul className="max-h-60 overflow-y-auto custom-scrollbar">
                            {results.map((client) => (
                                <li
                                    key={client.id}
                                    onClick={() => handleSelect(client)}
                                    className="px-4 py-3 hover:bg-white/60 cursor-pointer flex items-center justify-between group transition-colors"
                                >
                                    <div>
                                        <p className="font-medium text-gray-900">{client.name}</p>
                                        <p className="text-xs text-gray-500">{client.email}</p>
                                    </div>
                                    {client.sector && (
                                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                            {client.sector}
                                        </span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
