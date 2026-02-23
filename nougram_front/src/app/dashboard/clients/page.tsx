'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { UserCircle2, Plus, Pencil, Building2, Mail, User } from 'lucide-react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/Dialog';
import { apiRequest } from '@/lib/api-client';

type ClientItem = {
  id: number;
  organization_id: number;
  display_name: string;
  requester_name?: string | null;
  email?: string | null;
  status: string;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

type ClientListResponse = {
  items: ClientItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export default function ClientsPage() {
  const [loading, setLoading] = useState(true);
  const [clients, setClients] = useState<ClientItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [error, setError] = useState<string | null>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [formDisplayName, setFormDisplayName] = useState('');
  const [formRequesterName, setFormRequesterName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formStatus, setFormStatus] = useState('active');
  const [formNotes, setFormNotes] = useState('');

  const loadClients = useCallback(async () => {
    setLoading(true);
    setError(null);
    const response = await apiRequest<ClientListResponse>(
      `/clients/?page=${page}&page_size=${pageSize}`
    );
    if (response.error || !response.data) {
      setError(response.error || 'No se pudieron cargar los clientes');
      setClients([]);
      setTotal(0);
    } else {
      setClients(response.data.items);
      setTotal(response.data.total);
    }
    setLoading(false);
  }, [page, pageSize]);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  const openCreate = () => {
    setEditingId(null);
    setFormDisplayName('');
    setFormRequesterName('');
    setFormEmail('');
    setFormStatus('active');
    setFormNotes('');
    setDialogOpen(true);
  };

  const openEdit = (c: ClientItem) => {
    setEditingId(c.id);
    setFormDisplayName(c.display_name);
    setFormRequesterName(c.requester_name || '');
    setFormEmail(c.email || '');
    setFormStatus(c.status || 'active');
    setFormNotes(c.notes || '');
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formDisplayName.trim()) {
      setError('El nombre / razón social es obligatorio');
      return;
    }
    setSaving(true);
    setError(null);

    if (editingId) {
      const response = await apiRequest<ClientItem>(`/clients/${editingId}`, {
        method: 'PUT',
        body: JSON.stringify({
          display_name: formDisplayName.trim(),
          requester_name: formRequesterName.trim() || undefined,
          email: formEmail.trim() || undefined,
          status: formStatus,
          notes: formNotes.trim() || undefined,
        }),
      });
      if (response.error) {
        setError(response.error);
        setSaving(false);
        return;
      }
    } else {
      const response = await apiRequest<ClientItem>('/clients/', {
        method: 'POST',
        body: JSON.stringify({
          display_name: formDisplayName.trim(),
          requester_name: formRequesterName.trim() || undefined,
          email: formEmail.trim() || undefined,
          status: formStatus,
          notes: formNotes.trim() || undefined,
        }),
      });
      if (response.error || !response.data) {
        setError(response.error || 'No se pudo crear el cliente');
        setSaving(false);
        return;
      }
    }

    setDialogOpen(false);
    setSaving(false);
    loadClients();
  };

  return (
    <AdminLayout hideRightPanel>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-[1000px] mx-auto space-y-8"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <UserCircle2 size={20} strokeWidth={1.8} />
            </div>
            <span className="text-[10px] font-black text-blue-600 uppercase tracking-[0.2em] bg-blue-50 px-3 py-1 rounded-full border border-blue-100">
              Catálogo maestro
            </span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Gestión de Clientes</h1>
              <p className="text-system-gray font-medium text-lg mt-1">
                Listado y edición de clientes para cotizaciones y pipeline.
              </p>
            </div>
            <Button
              onClick={openCreate}
              className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20 flex items-center gap-2"
            >
              <Plus size={18} />
              Nuevo cliente
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-800 text-sm font-medium">
            {error}
          </div>
        )}

        <Card>
          {loading ? (
            <div className="p-10 flex justify-center">
              <div className="w-8 h-8 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
            </div>
          ) : clients.length === 0 ? (
            <div className="p-12 text-center">
              <UserCircle2 className="mx-auto h-12 w-12 text-gray-300" />
              <p className="mt-4 text-gray-600 font-medium">No hay clientes</p>
              <p className="text-sm text-gray-500 mt-1">Crea el primero para usarlo en cotizaciones.</p>
              <Button
                onClick={openCreate}
                variant="secondary"
                className="mt-4"
              >
                Crear cliente
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Empresa</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Contacto</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider w-20" />
                  </tr>
                </thead>
                <tbody>
                  {clients.map((c) => (
                    <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Building2 size={16} className="text-gray-400" />
                          <span className="font-medium text-gray-900">{c.display_name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-600">{c.requester_name || '—'}</td>
                      <td className="px-6 py-4 text-gray-600">
                        {c.email ? (
                          <a href={`mailto:${c.email}`} className="flex items-center gap-1 text-blue-600 hover:underline">
                            <Mail size={14} /> {c.email}
                          </a>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            c.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {c.status === 'active' ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEdit(c)}
                          className="text-gray-600 hover:text-blue-600"
                        >
                          <Pencil size={16} />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {total > pageSize && (
            <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
              <span>
                Mostrando {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} de {total}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Anterior
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page * pageSize >= total}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          )}
        </Card>
      </motion.div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>{editingId ? 'Editar cliente' : 'Nuevo cliente'}</DialogTitle>
            <DialogDescription>
              {editingId
                ? 'Actualiza los datos del cliente en el catálogo.'
                : 'Agrega un cliente al catálogo para usarlo en cotizaciones.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="display_name">Razón social / Empresa *</Label>
              <div className="relative">
                <Building2 className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  id="display_name"
                  className="pl-9"
                  placeholder="Ej: Acme Corp S.A.S"
                  value={formDisplayName}
                  onChange={(e) => setFormDisplayName(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="requester_name">Solicitante / Contacto</Label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  id="requester_name"
                  className="pl-9"
                  placeholder="Ej: Juan Pérez"
                  value={formRequesterName}
                  onChange={(e) => setFormRequesterName(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  className="pl-9"
                  placeholder="contacto@empresa.com"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                />
              </div>
            </div>
            {editingId && (
              <div className="space-y-2">
                <Label htmlFor="status">Estado</Label>
                <select
                  id="status"
                  className="w-full h-10 px-3 rounded-lg border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  value={formStatus}
                  onChange={(e) => setFormStatus(e.target.value)}
                >
                  <option value="active">Activo</option>
                  <option value="inactive">Inactivo</option>
                </select>
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="notes">Notas</Label>
              <textarea
                id="notes"
                className="w-full min-h-[80px] px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-y"
                placeholder="Notas internas (opcional)"
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || !formDisplayName.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {saving ? 'Guardando...' : editingId ? 'Guardar cambios' : 'Crear cliente'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminLayout>
  );
}
