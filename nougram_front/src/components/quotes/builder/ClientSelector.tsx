'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/Dialog';
import { Plus, Search, User, Mail, Building2, UserCircle } from 'lucide-react';
import { clientService, type Client } from '@/services/clientService';

interface ClientSelectorProps {
  value: string;
  clientId?: number | null;
  onChange: (clientId: number | null, name: string, email?: string, company?: string, requester?: string) => void;
}

const SEARCH_DEBOUNCE_MS = 300;

export function ClientSelector({ value, clientId, onChange }: ClientSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchClients = useCallback(async (q: string) => {
    if (!q || q.trim().length < 2) {
      setClients([]);
      return;
    }
    setLoading(true);
    try {
      const results = await clientService.searchClients(q);
      setClients(results);
    } catch {
      setClients([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => fetchClients(searchTerm), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [searchTerm, fetchClients]);

  const handleSelect = (client: Client) => {
    onChange(client.id, client.name, client.email, client.company, client.requester);
    setIsOpen(false);
  };

  const handleCreate = async () => {
    if (!newClientCompany.trim() || !newClientRequester.trim()) return;

    const created = await clientService.createClient({
      display_name: newClientCompany.trim(),
      requester_name: newClientRequester.trim(),
      email: newClientEmail.trim() || undefined,
    });
    if (created) {
      setClients((prev) => [created, ...prev]);
      onChange(created.id, created.name, created.email, created.company, created.requester);
    }
    setIsCreateOpen(false);
    setIsOpen(false);
    setNewClientCompany('');
    setNewClientRequester('');
    setNewClientEmail('');
  };

  const [newClientCompany, setNewClientCompany] = useState('');
  const [newClientRequester, setNewClientRequester] = useState('');
  const [newClientEmail, setNewClientEmail] = useState('');

  const displayValue = value || 'Seleccionar o crear cliente...';

  return (
    <div className="relative group">
      <div
        className="relative cursor-pointer"
        onClick={() => setIsOpen(true)}
      >
        <div
          className={`
            flex items-center justify-between
            w-full px-3 py-2 
            bg-white/50 backdrop-blur-sm 
            border border-gray-200 rounded-lg 
            text-sm text-gray-900 
            transition-all duration-200
            hover:bg-white hover:border-gray-300 hover:shadow-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500/20
            ${value ? 'bg-white' : ''}
          `}
        >
          <span className={`block truncate ${!value ? 'text-gray-400' : ''}`}>
            {displayValue}
          </span>
          <Search className="w-4 h-4 text-gray-400" />
        </div>
      </div>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute z-20 top-full left-0 w-full mt-2 bg-white/80 backdrop-blur-xl border border-gray-100/50 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 origin-top">
            <div className="p-2 border-b border-gray-100">
              <Input
                autoFocus
                placeholder="Buscar empresa o contacto..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="h-9 text-sm bg-gray-50/50 border-transparent focus:bg-white transition-colors"
              />
            </div>
            <div className="max-h-60 overflow-y-auto">
              {loading && (
                <div className="p-4 text-center text-sm text-gray-500">Buscando...</div>
              )}
              {!loading && clients.length === 0 && searchTerm.trim().length >= 2 && (
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
              {!loading && searchTerm.trim().length < 2 && (
                <div className="p-6 text-center text-sm text-gray-500">
                  Escribe al menos 2 caracteres para buscar.
                </div>
              )}
              {!loading &&
                clients.map((client) => (
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
                  onChange={(e) => setNewClientCompany(e.target.value)}
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
                  onChange={(e) => setNewClientRequester(e.target.value)}
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
                  onChange={(e) => setNewClientEmail(e.target.value)}
                />
              </div>
              <p className="text-xs text-gray-500">Usado para notificaciones automáticas.</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>Cancelar</Button>
            <Button
              onClick={handleCreate}
              disabled={!newClientCompany.trim() || !newClientRequester.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Guardar Cliente
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
