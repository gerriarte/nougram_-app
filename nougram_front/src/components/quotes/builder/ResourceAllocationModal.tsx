
import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { AlertCircle, Activity, User, Calendar, FileText, Info, CheckCircle2 } from 'lucide-react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { ResourceAllocation } from '@/types/quote-builder';

interface ResourceAllocationModalProps {
    isOpen: boolean;
    onClose: () => void;
    allocationToEdit?: ResourceAllocation | null;
    onSave: (allocation: ResourceAllocation) => void;
}

export function ResourceAllocationModal({ isOpen, onClose, allocationToEdit, onSave }: ResourceAllocationModalProps) {
    const { teamMembers, getMemberUtilization } = useQuoteBuilder();

    // Form State
    const [teamMemberId, setTeamMemberId] = useState<number>(0);
    const [hours, setHours] = useState<number>(0);
    const [role, setRole] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [notes, setNotes] = useState('');
    const [validationError, setValidationError] = useState<string | null>(null);

    // Initialize/Reset
    useEffect(() => {
        if (isOpen) {
            if (allocationToEdit) {
                setTeamMemberId(allocationToEdit.teamMemberId);
                setHours(allocationToEdit.hours);
                setRole(allocationToEdit.role || '');
                setStartDate(allocationToEdit.startDate || '');
                setEndDate(allocationToEdit.endDate || '');
                setNotes(allocationToEdit.notes || '');
            } else {
                setTeamMemberId(0);
                setHours(0);
                setRole('');
                setStartDate('');
                setEndDate('');
                setNotes('');
            }
            setValidationError(null);
        }
    }, [isOpen, allocationToEdit]);

    // Validation Logic
    const validate = () => {
        if (!teamMemberId) return "Selecciona un miembro del equipo.";
        if (hours <= 0) return "Las horas asignadas deben ser mayores a 0.";

        // Utilization Check
        const member = teamMembers.find(m => m.id === teamMemberId);
        if (member) {
            const currentUtil = getMemberUtilization(member.id);
            // If editing, subtract current allocation from "used" to forecast accurately
            const editingHours = allocationToEdit?.teamMemberId === teamMemberId ? allocationToEdit.hours : 0;
            const projectedUsed = (currentUtil.used - editingHours) + hours;
            const projectedPercent = (projectedUsed / member.availableHours) * 100;

            if (projectedPercent > 100) {
                return `Capacidad excedida: ${member.name} quedaría al ${projectedPercent.toFixed(1)}% de utilización.`;
            }
        }
        return null;
    };

    const handleSave = () => {
        const error = validate();
        if (error) {
            setValidationError(error);
            return;
        }

        onSave({
            id: allocationToEdit?.id || crypto.randomUUID(),
            teamMemberId,
            hours,
            role,
            startDate,
            endDate,
            notes
        });
        onClose();
    };

    // Calculate Visualization
    const selectedMember = teamMembers.find(m => m.id === teamMemberId);
    let utilizationInfo = null;

    if (selectedMember) {
        const currentUtil = getMemberUtilization(selectedMember.id);
        const editingHours = allocationToEdit?.teamMemberId === teamMemberId ? allocationToEdit.hours : 0;
        const projectedUsed = (currentUtil.used - editingHours) + (hours || 0);
        const projectedPercent = selectedMember.availableHours > 0 ? (projectedUsed / selectedMember.availableHours) * 100 : 0;

        let statusColor = 'bg-green-500';
        let statusText = 'text-green-600';
        let statusBg = 'bg-green-50';

        if (projectedPercent > 90 && projectedPercent <= 100) {
            statusColor = 'bg-yellow-500';
            statusText = 'text-yellow-600';
            statusBg = 'bg-yellow-50';
        } else if (projectedPercent > 100) {
            statusColor = 'bg-red-500';
            statusText = 'text-red-600';
            statusBg = 'bg-red-50';
        }

        utilizationInfo = (
            <div className={`mt-4 p-4 rounded-xl border transition-all duration-300 ${statusBg} border-opacity-50`}>
                <div className="flex justify-between items-end mb-2">
                    <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Carga Proyectada</span>
                        <span className={`text-xl font-black ${statusText}`}>{projectedPercent.toFixed(1)}%</span>
                    </div>
                    <span className="text-[10px] font-bold text-gray-500">{projectedUsed}h / {selectedMember.availableHours}h total</span>
                </div>
                <div className="w-full bg-gray-200/50 rounded-full h-2 overflow-hidden">
                    <div
                        className={`h-full transition-all duration-700 ease-out shadow-sm ${statusColor}`}
                        style={{ width: `${Math.min(projectedPercent, 100)}%` }}
                    />
                </div>
            </div>
        );
    }

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[480px] p-0 overflow-hidden border-none shadow-2xl ring-1 ring-black/5">
                <div className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 w-full" />

                <div className="p-8">
                    <DialogHeader className="mb-6">
                        <div className="flex items-center gap-3 mb-1">
                            <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
                                <User size={20} />
                            </div>
                            <DialogTitle className="text-2xl font-black text-gray-900 tracking-tight">
                                {allocationToEdit ? 'Editar Asignación' : 'Nueva Asignación'}
                            </DialogTitle>
                        </div>
                        <p className="text-sm text-gray-500">Configura los detalles del recurso para el proyecto.</p>
                    </DialogHeader>

                    <div className="space-y-6">
                        {/* Member & Hours Selection */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-xs font-black text-gray-400 uppercase ml-1">Miembro *</Label>
                                <div className="relative">
                                    <select
                                        className="appearance-none flex h-11 w-full rounded-xl border border-gray-100 bg-gray-50/50 px-4 py-2 text-sm font-bold transition-all focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:bg-white focus:border-purple-200"
                                        value={teamMemberId}
                                        onChange={(e) => setTeamMemberId(Number(e.target.value))}
                                    >
                                        <option value={0}>Seleccionar...</option>
                                        {teamMembers.map(m => (
                                            <option key={m.id} value={m.id}>{m.name}</option>
                                        ))}
                                    </select>
                                    <div className="absolute right-3 top-3.5 pointer-events-none text-gray-400">
                                        <Activity size={14} />
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label className="text-xs font-black text-gray-400 uppercase ml-1">Horas *</Label>
                                <Input
                                    type="number"
                                    value={hours || ''}
                                    onChange={(e) => setHours(parseFloat(e.target.value))}
                                    placeholder="Ej: 40"
                                    className="h-11 rounded-xl bg-gray-50/50 border-gray-100 font-bold focus:bg-white"
                                />
                            </div>
                        </div>

                        {/* Utilization Visualization */}
                        {utilizationInfo}

                        {/* Role Selection */}
                        <div className="space-y-2">
                            <Label className="text-xs font-black text-gray-400 uppercase ml-1">Rol en el Proyecto</Label>
                            <div className="relative">
                                <Input
                                    value={role}
                                    onChange={(e) => setRole(e.target.value)}
                                    placeholder="Ej: UI Designer"
                                    className="h-11 pl-10 rounded-xl bg-gray-50/50 border-gray-100 focus:bg-white"
                                />
                                <div className="absolute left-3.5 top-3.5 text-gray-400">
                                    <Activity size={14} />
                                </div>
                            </div>
                        </div>

                        {/* Dates Row */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-xs font-black text-gray-400 uppercase ml-1">Inicio</Label>
                                <div className="relative">
                                    <Input
                                        type="date"
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        className="h-11 pl-10 rounded-xl bg-gray-50/50 border-gray-100 focus:bg-white text-xs font-bold"
                                    />
                                    <div className="absolute left-3.5 top-3.5 text-gray-400">
                                        <Calendar size={14} />
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label className="text-xs font-black text-gray-400 uppercase ml-1">Fin</Label>
                                <div className="relative">
                                    <Input
                                        type="date"
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        className="h-11 pl-10 rounded-xl bg-gray-50/50 border-gray-100 focus:bg-white text-xs font-bold"
                                    />
                                    <div className="absolute left-3.5 top-3.5 text-gray-400">
                                        <Calendar size={14} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Notes */}
                        <div className="space-y-2">
                            <Label className="text-xs font-black text-gray-400 uppercase ml-1">Notas Internas</Label>
                            <div className="relative">
                                <Input
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    placeholder="Instrucciones o detalles de la asignación..."
                                    className="h-11 pl-10 rounded-xl bg-gray-50/50 border-gray-100 focus:bg-white"
                                />
                                <div className="absolute left-3.5 top-3.5 text-gray-400">
                                    <FileText size={14} />
                                </div>
                            </div>
                        </div>

                        {/* Validation & Messages */}
                        {validationError && (
                            <div className="bg-red-50 text-red-600 text-[11px] font-bold p-3 rounded-xl border border-red-100 flex items-start gap-2 animate-in slide-in-from-left-2 duration-200">
                                <AlertCircle size={14} className="mt-0.5 shrink-0" />
                                <span>{validationError}</span>
                            </div>
                        )}

                        {!validationError && selectedMember && (
                            (() => {
                                const currentUtil = getMemberUtilization(selectedMember.id);
                                const editingHours = allocationToEdit?.teamMemberId === selectedMember.id ? allocationToEdit.hours : 0;
                                const projectedUsed = (currentUtil.used - editingHours) + (hours || 0);
                                const projectedPercent = selectedMember.availableHours > 0 ? (projectedUsed / selectedMember.availableHours) * 100 : 0;

                                if (projectedPercent > 90 && projectedPercent <= 100) {
                                    return (
                                        <div className="bg-yellow-50 text-yellow-700 text-[11px] font-bold p-3 rounded-xl border border-yellow-100 flex items-start gap-2 animate-in fade-in duration-300">
                                            <Info size={14} className="mt-0.5 shrink-0" />
                                            <span>Capacidad de {selectedMember.name} está cerca del límite.</span>
                                        </div>
                                    );
                                } else if (projectedPercent <= 90 && teamMemberId !== 0) {
                                    return (
                                        <div className="bg-green-50 text-green-700 text-[11px] font-bold p-3 rounded-xl border border-green-100 flex items-start gap-2 animate-in fade-in duration-300">
                                            <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                                            <span>Capacidad ideal para {selectedMember.name}.</span>
                                        </div>
                                    );
                                }
                                return null;
                            })()
                        )}
                    </div>

                    <DialogFooter className="mt-8 gap-3 border-t border-gray-50 pt-8">
                        <Button
                            variant="ghost"
                            onClick={onClose}
                            className="text-gray-400 font-bold hover:bg-gray-100 rounded-xl px-6"
                        >
                            Cerrar
                        </Button>
                        <Button
                            onClick={handleSave}
                            className="bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl px-10 shadow-lg shadow-purple-100 transition-all hover:scale-105 active:scale-95"
                        >
                            Confirmar Asignación
                        </Button>
                    </DialogFooter>
                </div>
            </DialogContent>
        </Dialog>
    );
}
