'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Trash2, UserPlus } from 'lucide-react';
import { api } from '@/lib/api';

interface DeliveryDriver {
  id: string;
  name: string;
  phone: string;
  is_active: boolean;
  total_deliveries: number;
}

export function DeliveryDriversList() {
  const [drivers, setDrivers] = useState<DeliveryDriver[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', phone: '' });

  const fetchDrivers = async () => {
    try {
      const data = await api.get('/api/v1/delivery-drivers');
      setDrivers(data);
    } catch (error) {
      console.error('Erro ao buscar motoboys:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrivers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/v1/delivery-drivers', formData);
      fetchDrivers();
      setModalOpen(false);
      setFormData({ name: '', phone: '' });
    } catch (error: any) {
      alert('Erro ao criar motoboy: ' + error.message);
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await api.patch(`/api/v1/delivery-drivers/${id}/toggle`);
      fetchDrivers();
    } catch (error) {
      alert('Erro ao alterar status');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir este motoboy?')) return;
    try {
      await api.delete(`/api/v1/delivery-drivers/${id}`);
      fetchDrivers();
    } catch (error) {
      alert('Erro ao excluir motoboy');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Carregando...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Motoboys</CardTitle>
              <p className="text-sm text-muted-foreground">
                Gerencie sua equipe de entregadores
              </p>
            </div>
            <Button onClick={() => setModalOpen(true)}>
              <UserPlus className="mr-2 h-4 w-4" />
              Adicionar Motoboy
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {drivers.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-4">
                Nenhum motoboy cadastrado
              </p>
              <Button onClick={() => setModalOpen(true)}>
                Adicionar Primeiro Motoboy
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-4">Nome</th>
                    <th className="text-left p-4">Telefone</th>
                    <th className="text-center p-4">Entregas</th>
                    <th className="text-center p-4">Status</th>
                    <th className="text-right p-4">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {drivers.map((driver) => (
                    <tr key={driver.id} className="border-b hover:bg-gray-50">
                      <td className="p-4 font-medium">{driver.name}</td>
                      <td className="p-4">{driver.phone}</td>
                      <td className="p-4 text-center">{driver.total_deliveries}</td>
                      <td className="p-4 text-center">
                        <Badge
                          variant={driver.is_active ? 'default' : 'secondary'}
                          className={driver.is_active ? 'bg-green-100 text-green-800' : ''}
                        >
                          {driver.is_active ? 'Ativo' : 'Inativo'}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggle(driver.id)}
                          >
                            {driver.is_active ? 'Desativar' : 'Ativar'}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(driver.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Adicionar */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Adicionar Motoboy</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <Label htmlFor="name">Nome Completo</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="João Silva"
                required
                minLength={3}
              />
            </div>

            <div>
              <Label htmlFor="phone">Telefone WhatsApp</Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="11999999999"
                required
                minLength={10}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit">Cadastrar</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
