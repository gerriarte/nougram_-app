import * as React from "react";
import { Button } from "@/components/ui/Button";
import { Calculator, Users, Building, Settings, Home } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface AdminLayoutProps {
    children: React.ReactNode;
    activeTab: "payroll" | "overhead" | "config";
    onTabChange: (tab: "payroll" | "overhead" | "config") => void;
}

export function AdminLayout({ children, activeTab, onTabChange }: AdminLayoutProps) {

    const NavItem = ({ id, label, icon: Icon }: { id: "payroll" | "overhead" | "config", label: string, icon: any }) => (
        <button
            onClick={() => onTabChange(id)}
            className={cn(
                "flex items-center gap-3 w-full px-4 py-2.5 text-sm font-medium rounded-lg transition-colors",
                activeTab === id
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            )}
        >
            <Icon className="h-4 w-4" />
            {label}
        </button>
    );

    return (
        <div className="min-h-screen bg-gray-50 font-sans">
            {/* Top Navigation */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
                <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-blue-600 p-1.5 rounded-md text-white">
                            <Calculator className="h-5 w-5" />
                        </div>
                        <h1 className="text-xl font-bold text-gray-900">Nougram Admin</h1>
                    </div>

                    <Link href="/">
                        <Button variant="ghost" size="sm" className="gap-2">
                            <Home className="h-4 w-4" /> Ir al Cotizador
                        </Button>
                    </Link>
                </div>
            </header>

            <div className="container mx-auto px-4 py-8">
                <div className="grid lg:grid-cols-12 gap-8">

                    {/* Sidebar Navigation */}
                    <aside className="lg:col-span-3 space-y-6">
                        <nav className="space-y-1">
                            <NavItem id="payroll" label="Nómina" icon={Users} />
                            <NavItem id="overhead" label="Overhead & Tools" icon={Building} />
                            <NavItem id="config" label="Configuración Global" icon={Settings} />
                        </nav>

                        <div className="pt-6 border-t border-gray-200">
                            {/* Placeholder for BCR Card injection */}
                            <div id="bcr-card-portal"></div>
                        </div>
                    </aside>

                    {/* Main Content Area */}
                    <main className="lg:col-span-9">
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm min-h-[600px]">
                            {children}
                        </div>
                    </main>

                </div>
            </div>
        </div>
    );
}
