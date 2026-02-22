
'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/Dialog';
import { Plus, Search, User, Mail, Building2, UserCircle } from 'lucide-react';

interface Client {
    id: number;
    name: string; // Display Name (usually Company)
    company?: string;
    requester?: string;
    email?: string;
    projectType?: string;
}

const MOCK_CLIENTS: Client[] = [
    { id: 1, name: 'TechCorp', company: 'TechCorp Inc.', requester: 'John Doe', email: 'billing@techcorp.com' },
    { id: 2, name: 'StartupX', company: 'StartupX LLC', requester: 'Jane Smith', email: 'founders@startupx.io' },
    { id: 3, name: 'DesignCo', company: 'DesignCo Agency', requester: 'Alex Art', email: 'hello@designco.agency' },
    { id: 4, name: 'Acme Inc', company: 'Acme Corporation', requester: 'Wile E. Coyote', email: 'contact@acme.com' },
];

interface ClientSelectorProps {
    value: string;
    onChange: (name: string, email?: string, company?: string, requester?: string) => void;
}

export function ClientSelector({ value, onChange }: ClientSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [isCreateOpen, setIsCreateOpen] = useState(false);

    // Mock "Local" Clients state to allow addition
    const [clients, setClients] = useState<Client[]>(MOCK_CLIENTS);

    // New Client Form
    const [newClientCompany, setNewClientCompany] = useState('');
    const [newClientRequester, setNewClientRequester] = useState('');
    const [newClientEmail, setNewClientEmail] = useState('');

    const filteredClients = clients.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c.company && c.company.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const handleSelect = (client: Client) => {
        onChange(client.name, client.email, client.company, client.requester);
        setIsOpen(false);
    };

    const handleCreate = () => {
        if (!newClientCompany || !newClientRequester) return;

        const newClient: Client = {
            id: Date.now(),
            name: newClientCompany, // Default display name is Company
            company: newClientCompany,
            requester: newClientRequester,
            email: newClientEmail
        };

        setClients([...clients, newClient]);
        onChange(newClient.name, newClient.email, newClient.company, newClient.requester);
        setIsCreateOpen(false);
        setIsOpen(false);

        // Reset form
        setNewClientCompany('');
        setNewClientRequester('');
        setNewClientEmail('');
    };

    return (
        <div className="relative group">
            {/* Trigger Input (Fake Select) */}
            <div
                className="relative cursor-pointer"
                onClick={() => setIsOpen(true)}
            >
                <div className={`
                    flex items-center justify-between
                    w-full px-3 py-2 
                    bg-white/50 backdrop-blur-sm 
                    border border-gray-200 rounded-lg 
                    text-sm text-gray-900 
                    transition-all duration-200
                    hover:bg-white hover:border-gray-300 hover:shadow-sm
                    focus:outline-none focus:ring-2 focus:ring-blue-500/20
                    ${value ? 'bg-white' : ''}
                `}>
                    <span className={`block truncate ${!value ? 'text-gray-400' : ''}`}>
                        {value || "Seleccionar o crear cliente..."}
                    </span>
                    <Search className="w-4 h-4 text-gray-400" />
                </div>
            </div>

            {/* Dropdown / Modal for Selection */}
            {isOpen && (
                <>
                    {/* Backdrop to close */}
                    <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />

                    <div className="absolute z-20 top-full left-0 w-full mt-2 bg-white/80 backdrop-blur-xl border border-gray-100/50 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 origin-top">
                        <div className="p-2 border-b border-gray-100">
                            <Input
                                autoFocus
                                placeholder="Buscar empresa o contacto..."
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                                className="h-9 text-sm bg-gray-50/50 border-transparent focus:bg-white transition-colors"
                            />
                        </div>

                        <div className="max-h-60 overflow-y-auto">
                            {filteredClients.length === 0 && (
                                <div className="p-8 text-center">
                                    <p className="text-sm text-gray-500">No se encontraron clientes.</p>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setIsCreateOpen(true)}
                                        className="mt-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                    >
                                        Crear nuevo ahora
                                    </Button>
                                </div>
                            )}

                            {filteredClients.map(client => (
                                <button
                                    key={client.id}
                                    className="w-full text-left px-4 py-3 hover:bg-blue-50/50 transition-colors border-b border-gray-50 last:border-0 group"
                                    onClick={() => handleSelect(client)}
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="font-medium text-gray-900 group-hover:text-blue-700">
                                                {client.company || client.name}
                                            </div>
                                            <div className="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                                                {client.requester && (
                                                    <span className="flex items-center gap-1">
                                                        <UserCircle size={10} /> {client.requester}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        {client.email && (
                                            <div className="text-xs text-gray-400 group-hover:text-blue-500">
                                                {client.email}
                                            </div>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>

                        <div className="p-2 border-t border-gray-100 bg-gray-50/50 backdrop-blur-sm">
                            <Button
                                size="sm"
                                variant="ghost"
                                className="w-full justify-start text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                onClick={() => setIsCreateOpen(true)}
                            >
                                <Plus size={16} className="mr-2" />
                                Crear Nuevo Cliente
                            </Button>
                        </div>
                    </div>
                </>
            )}

            {/* Create Client Modal */}
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>Nuevo Cliente</DialogTitle>
                        <DialogDescription>
                            Ingresa los datos del cliente para la cotización.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="grid gap-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="company">Razón Social / Empresa <span className="text-red-500">*</span></Label>
                            <div className="relative">
                                <Building2 className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                                <Input
                                    id="company"
                                    className="pl-9"
                                    placeholder="Ej: Acme Corp S.A.S"
                                    value={newClientCompany}
                                    onChange={e => setNewClientCompany(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="requester">Solicitante <span className="text-red-500">*</span></Label>
                            <div className="relative">
                                <User className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                                <Input
                                    id="requester"
                                    className="pl-9"
                                    placeholder="Ej: Juan Pérez"
                                    value={newClientRequester}
                                    onChange={e => setNewClientRequester(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="email">Correo Electrónico</Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                                <Input
                                    id="email"
                                    className="pl-9"
                                    placeholder="contacto@empresa.com"
                                    value={newClientEmail}
                                    onChange={e => setNewClientEmail(e.target.value)}
                                />
                            </div>
                            <p className="text-xs text-gray-500">Usado para notificaciones automáticas.</p>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>Cancelar</Button>
                        <Button onClick={handleCreate} disabled={!newClientCompany || !newClientRequester} className="bg-blue-600 hover:bg-blue-700">
                            Guardar Cliente
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
