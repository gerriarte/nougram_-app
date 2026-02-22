
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useNougram } from '@/context/NougramCoreContext';
import { Users, LogOut, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function AdminHeader() {
    const { state } = useNougram();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleLogout = () => {
        window.location.href = '/login';
    };

    return (
        <header className="bg-white/60 backdrop-blur-md border-b border-white/20 h-20 px-10 flex items-center justify-between sticky top-0 z-30">
            {/* Left: Context */}
            <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                <h2 className="text-system-gray text-xs font-black uppercase tracking-[0.2em]">{state.identity.name} Workspace</h2>
            </div>

            {/* Right: User Menu */}
            <div className="relative" ref={menuRef}>
                <button
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className="flex items-center gap-4 hover:bg-white/50 p-2 pl-4 rounded-2xl transition-all focus:outline-none group"
                >
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-bold text-gray-900 tracking-tight leading-none">Usuario Demo</p>
                        <p className="text-[10px] font-black text-system-gray uppercase tracking-widest mt-1.5">{state.user.role}</p>
                    </div>
                    <div className="relative">
                        <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-lg shadow-blue-500/20 border border-white/20">
                            U
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-100">
                            <ChevronDown size={10} className={state.user.role === 'owner' ? "rotate-180" : ""} />
                        </div>
                    </div>
                </button>

                {/* Dropdown */}
                <AnimatePresence>
                    {isMenuOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className="absolute right-0 mt-4 w-64 bg-white/80 backdrop-blur-2xl rounded-3xl shadow-[0_20px_40px_rgba(0,0,0,0.1)] border border-white/20 py-3 z-50 origin-top-right overflow-hidden"
                        >
                            <div className="px-6 py-4 border-b border-gray-100/50 mb-2">
                                <p className="text-[10px] font-black text-system-gray uppercase tracking-widest mb-1">Sesión Actual</p>
                                <p className="text-sm font-bold text-gray-900 truncate">usuario@nougram.com</p>
                            </div>

                            <div className="px-2 space-y-1">
                                {state.user.role === 'owner' && (
                                    <a href="/dashboard/users" className="flex items-center gap-3 px-4 py-3 text-sm font-bold text-gray-600 hover:bg-white hover:text-blue-600 hover:shadow-sm rounded-2xl transition-all group">
                                        <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center group-hover:bg-blue-50 transition-colors">
                                            <Users size={16} strokeWidth={2} />
                                        </div>
                                        Usuarios (Equipo)
                                    </a>
                                )}
                            </div>

                            <div className="mt-2 px-2 pt-2 border-t border-gray-100/50">
                                <button
                                    onClick={handleLogout}
                                    className="flex items-center gap-3 w-full px-4 py-3 text-sm font-bold text-red-500 hover:bg-red-50 hover:shadow-sm rounded-2xl transition-all group"
                                >
                                    <div className="w-8 h-8 rounded-xl bg-red-50 flex items-center justify-center group-hover:bg-white transition-colors">
                                        <LogOut size={16} strokeWidth={2} />
                                    </div>
                                    Cerrar Sesión
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </header>
    );
}
