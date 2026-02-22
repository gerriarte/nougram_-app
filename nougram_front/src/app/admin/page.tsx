"use client";

import * as React from "react";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { TeamMemberList } from "@/components/admin/TeamMemberList";
import { TeamMemberForm } from "@/components/admin/TeamMemberForm";
import { SocialChargesForm } from "@/components/admin/SocialChargesForm";
import { FixedCostList } from "@/components/admin/FixedCostList";
import { FixedCostForm } from "@/components/admin/FixedCostForm";
import { GlobalConfigForm } from "@/components/admin/GlobalConfigForm";
import { BCRSummaryCard } from "@/components/admin/BCRSummaryCard";
import { calculatePayroll, calculateOverhead, calculateBCR } from "@/lib/admin-logic";
import { createPortal } from "react-dom";
import { useAdminData } from "@/hooks/useAdminData";
import {
    TeamMemberInput,
    TeamMemberDisplay,
    FixedCostInput,
    FixedCostDisplay,
    GlobalConfig,
    SocialChargesConfig,
    BCRSummary,
    PayrollSummary,
    OverheadSummary
} from "@/types/admin";
import { Loader2 } from "lucide-react";

export default function AdminPage() {
    const [activeTab, setActiveTab] = React.useState<"payroll" | "overhead" | "config">("payroll");
    const [isClient, setIsClient] = React.useState(false);

    // HOOK STATE
    const {
        isLoading,
        members,
        fixedCosts,
        socialConfig,
        globalConfig,
        actions
    } = useAdminData();

    // UI STATE - FORMS
    const [editingMember, setEditingMember] = React.useState<TeamMemberInput | null>(null);
    const [isMemberFormOpen, setIsMemberFormOpen] = React.useState(false);

    const [editingCost, setEditingCost] = React.useState<FixedCostInput | null>(null);
    const [isCostFormOpen, setIsCostFormOpen] = React.useState(false);

    // CALCULATED STATE
    const [payrollResult, setPayrollResult] = React.useState<{ members: TeamMemberDisplay[], summary: PayrollSummary } | null>(null);
    const [overheadResult, setOverheadResult] = React.useState<OverheadSummary | null>(null);
    const [bcrResult, setBcrResult] = React.useState<BCRSummary | null>(null);

    React.useEffect(() => {
        setIsClient(true);
    }, []);

    // RECALCULATE EFFECT
    React.useEffect(() => {
        if (isLoading) return;

        const pResult = calculatePayroll(members, socialConfig);
        const oResult = calculateOverhead(fixedCosts);
        const bResult = calculateBCR(pResult.summary, oResult, globalConfig);

        setPayrollResult(pResult);
        setOverheadResult(oResult);
        setBcrResult(bResult);
    }, [members, socialConfig, fixedCosts, globalConfig, isLoading]);

    // --- HANDLERS ---

    // Members
    const handleAddMember = (m: TeamMemberInput) => {
        actions.addMember(m);
        setIsMemberFormOpen(false);
    };

    const handleUpdateMember = (m: TeamMemberInput) => {
        actions.editMember(m);
        setEditingMember(null);
    };

    const handleDeleteMember = (id: number) => {
        if (confirm("¿Estás seguro de eliminar este miembro?")) {
            actions.deleteMember(id);
        }
    };

    // Costs
    const handleAddCost = (c: FixedCostInput) => {
        actions.addCost(c);
        setIsCostFormOpen(false);
    };

    const handleUpdateCost = (c: FixedCostInput) => {
        actions.editCost(c);
        setEditingCost(null);
    };

    const handleDeleteCost = (id: number) => {
        if (confirm("¿Estás seguro de eliminar este gasto?")) {
            actions.deleteCost(id);
        }
    };

    if (isLoading) {
        return (
            <AdminLayout activeTab={activeTab} onTabChange={setActiveTab}>
                <div className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
                    <span className="ml-2 text-gray-500">Cargando configuración...</span>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout activeTab={activeTab} onTabChange={setActiveTab}>

            {/* Portal BCR Card to Sidebar */}
            {isClient && document.getElementById("bcr-card-portal") && createPortal(
                <BCRSummaryCard summary={bcrResult} />,
                document.getElementById("bcr-card-portal")!
            )}

            <div className="p-6">
                {activeTab === "payroll" && payrollResult && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-right-4">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="bg-blue-50 p-4 rounded-lg">
                                <div className="text-sm text-blue-600 font-medium">Salario total Mensual</div>
                                <div className="text-xl font-bold text-blue-900">{payrollResult.summary.total_salary_with_charges}</div>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="text-sm text-gray-500 font-medium">Miembros Activos</div>
                                <div className="text-xl font-bold text-gray-900">{payrollResult.summary.total_members}</div>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="text-sm text-gray-500 font-medium">Costo Promedio / Hora</div>
                                <div className="text-xl font-bold text-gray-900">{payrollResult.summary.average_cost_per_hour}</div>
                            </div>
                        </div>

                        <SocialChargesForm config={socialConfig} onChange={actions.updateSocialConfig} />

                        <TeamMemberList
                            members={payrollResult.members}
                            onAdd={() => { setEditingMember(null); setIsMemberFormOpen(true); }}
                            onEdit={(m) => { setEditingMember(m); setIsMemberFormOpen(true); }}
                            onDelete={handleDeleteMember}
                        />
                    </div>
                )}

                {activeTab === "overhead" && overheadResult && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-right-4">
                        <div className="grid grid-cols-3 gap-4 mb-6">
                            <div className="bg-orange-50 p-4 rounded-lg">
                                <div className="text-sm text-orange-600 font-medium">Total Gastos Fijos</div>
                                <div className="text-xl font-bold text-orange-900">{overheadResult.total_fixed_costs}</div>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="text-sm text-gray-500 font-medium">Overhead Operacional</div>
                                <div className="text-xl font-bold text-gray-900">{overheadResult.total_overhead_costs}</div>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="text-sm text-gray-500 font-medium">Tools & SaaS</div>
                                <div className="text-xl font-bold text-gray-900">{overheadResult.total_tools_costs}</div>
                            </div>
                        </div>

                        <FixedCostList
                            costs={fixedCosts.map((c, i) => ({ ...c, id: c.id!, amount_monthly_normalized: c.amount_monthly, created_at: "" }))} // Simple mapping for display
                            onAdd={() => { setEditingCost(null); setIsCostFormOpen(true); }}
                            onEdit={(c) => { setEditingCost(c); setIsCostFormOpen(true); }}
                            onDelete={handleDeleteCost}
                        />
                    </div>
                )}

                {activeTab === "config" && (
                    <GlobalConfigForm config={globalConfig} onChange={actions.updateGlobalConfig} />
                )}
            </div>

            {/* Modals */}
            {(isMemberFormOpen || editingMember) && (
                <TeamMemberForm
                    initialData={editingMember || undefined}
                    onSubmit={editingMember ? handleUpdateMember : handleAddMember}
                    onCancel={() => { setIsMemberFormOpen(false); setEditingMember(null); }}
                />
            )}

            {(isCostFormOpen || editingCost) && (
                <FixedCostForm
                    initialData={editingCost || undefined}
                    onSubmit={editingCost ? handleUpdateCost : handleAddCost}
                    onCancel={() => { setIsCostFormOpen(false); setEditingCost(null); }}
                />
            )}

        </AdminLayout>
    );
}
