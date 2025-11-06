'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { api, type Neighborhood } from '@/lib/api';

export function NeighborhoodManager() {
  const [neighborhoods, setNeighborhoods] = useState<Neighborhood[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingNeighborhood, setEditingNeighborhood] = useState<Neighborhood | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    neighborhood_name: '',
    delivery_type: 'paid' as 'free' | 'paid' | 'not_available',
    delivery_fee: '10.00',
    delivery_time_minutes: '60',
  });

  useEffect(() => {
    loadNeighborhoods();
  }, []);

  const loadNeighborhoods = async () => {
    try {
      const data = await api.delivery.listNeighborhoods();
      setNeighborhoods(data);
    } catch (error) {
      console.error('Erro ao carregar bairros:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      await api.delivery.createNeighborhood({
        neighborhood_name: formData.neighborhood_name,
        delivery_type: formData.delivery_type,
        delivery_fee: parseFloat(formData.delivery_fee),
        delivery_time_minutes: parseInt(formData.delivery_time_minutes),
      });

      setShowAddForm(false);
      setFormData({
        neighborhood_name: '',
        delivery_type: 'paid',
        delivery_fee: '10.00',
        delivery_time_minutes: '60',
      });
      loadNeighborhoods();
    } catch (error) {
      console.error('Erro ao adicionar bairro:', error);
      alert('Erro ao adicionar bairro');
    }
  };

  const handleEdit = async () => {
    if (!editingNeighborhood) return;

    try {
      await api.delivery.updateNeighborhood(editingNeighborhood.id, {
        neighborhood_name: formData.neighborhood_name,
        delivery_type: formData.delivery_type,
        delivery_fee: parseFloat(formData.delivery_fee),
        delivery_time_minutes: parseInt(formData.delivery_time_minutes),
      });

      setEditingNeighborhood(null);
      loadNeighborhoods();
    } catch (error) {
      console.error('Erro ao editar bairro:', error);
      alert('Erro ao editar bairro');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delivery.deleteNeighborhood(id);
      setDeletingId(null);
      loadNeighborhoods();
    } catch (error) {
      console.error('Erro ao excluir bairro:', error);
      alert('Erro ao excluir bairro');
    }
  };

  const openEditDialog = (neighborhood: Neighborhood) => {
    setFormData({
      neighborhood_name: neighborhood.neighborhood_name,
      delivery_type: neighborhood.delivery_type,
      delivery_fee: neighborhood.delivery_fee.toString(),
      delivery_time_minutes: neighborhood.delivery_time_minutes.toString(),
    });
    setEditingNeighborhood(neighborhood);
  };

  const getDeliveryTypeBadge = (type: string) => {
    const variants = {
      free: { label: 'Grátis', color: 'bg-green-100 text-green-800 border-green-300' },
      paid: { label: 'Pago', color: 'bg-blue-100 text-blue-800 border-blue-300' },
      not_available: { label: 'Indisponível', color: 'bg-gray-100 text-gray-800 border-gray-300' },
    };

    const variant = variants[type as keyof typeof variants] || variants.paid;

    return (
      <Badge variant="outline" className={variant.color}>
        {variant.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Bairros Cadastrados</h3>
          <p className="text-sm text-muted-foreground">
            {neighborhoods.length} bairro(s) configurado(s)
          </p>
        </div>
        <Button onClick={() => setShowAddForm(true)}>
          + Adicionar Bairro
        </Button>
      </div>

      {/* Lista de Bairros */}
      {neighborhoods.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum bairro cadastrado</h3>
          <p className="mt-1 text-sm text-gray-500">
            Comece adicionando os bairros que você atende.
          </p>
          <div className="mt-6">
            <Button onClick={() => setShowAddForm(true)}>
              + Adicionar Primeiro Bairro
            </Button>
          </div>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bairro
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cidade/Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Taxa
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tempo
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {neighborhoods.map((neighborhood) => (
                <tr key={neighborhood.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {neighborhood.neighborhood_name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {neighborhood.city}/{neighborhood.state}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getDeliveryTypeBadge(neighborhood.delivery_type)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      R$ {neighborhood.delivery_fee.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {neighborhood.delivery_time_minutes} min
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openEditDialog(neighborhood)}
                    >
                      Editar
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => setDeletingId(neighborhood.id)}
                    >
                      Excluir
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Dialog Adicionar */}
      <Dialog open={showAddForm} onOpenChange={setShowAddForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Adicionar Bairro</DialogTitle>
            <DialogDescription>
              Configure as informações de entrega para um novo bairro.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="neighborhood_name">Nome do Bairro</Label>
              <Input
                id="neighborhood_name"
                value={formData.neighborhood_name}
                onChange={(e) => setFormData({ ...formData, neighborhood_name: e.target.value })}
                placeholder="Ex: Centro, Paulista, Jardins"
              />
            </div>

            <div>
              <Label htmlFor="delivery_type">Tipo de Entrega</Label>
              <select
                id="delivery_type"
                className="w-full border rounded-md px-3 py-2"
                value={formData.delivery_type}
                onChange={(e) => setFormData({ ...formData, delivery_type: e.target.value as any })}
              >
                <option value="paid">Pago</option>
                <option value="free">Grátis</option>
                <option value="not_available">Não Atendemos</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="delivery_fee">Taxa (R$)</Label>
                <Input
                  id="delivery_fee"
                  type="number"
                  step="0.01"
                  value={formData.delivery_fee}
                  onChange={(e) => setFormData({ ...formData, delivery_fee: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="delivery_time">Tempo (minutos)</Label>
                <Input
                  id="delivery_time"
                  type="number"
                  value={formData.delivery_time_minutes}
                  onChange={(e) => setFormData({ ...formData, delivery_time_minutes: e.target.value })}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddForm(false)}>
              Cancelar
            </Button>
            <Button onClick={handleAdd} disabled={!formData.neighborhood_name}>
              Adicionar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Editar */}
      <Dialog open={!!editingNeighborhood} onOpenChange={() => setEditingNeighborhood(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Bairro</DialogTitle>
            <DialogDescription>
              Atualize as informações de entrega para este bairro.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="edit_neighborhood_name">Nome do Bairro</Label>
              <Input
                id="edit_neighborhood_name"
                value={formData.neighborhood_name}
                onChange={(e) => setFormData({ ...formData, neighborhood_name: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="edit_delivery_type">Tipo de Entrega</Label>
              <select
                id="edit_delivery_type"
                className="w-full border rounded-md px-3 py-2"
                value={formData.delivery_type}
                onChange={(e) => setFormData({ ...formData, delivery_type: e.target.value as any })}
              >
                <option value="paid">Pago</option>
                <option value="free">Grátis</option>
                <option value="not_available">Não Atendemos</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_delivery_fee">Taxa (R$)</Label>
                <Input
                  id="edit_delivery_fee"
                  type="number"
                  step="0.01"
                  value={formData.delivery_fee}
                  onChange={(e) => setFormData({ ...formData, delivery_fee: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="edit_delivery_time">Tempo (minutos)</Label>
                <Input
                  id="edit_delivery_time"
                  type="number"
                  value={formData.delivery_time_minutes}
                  onChange={(e) => setFormData({ ...formData, delivery_time_minutes: e.target.value })}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingNeighborhood(null)}>
              Cancelar
            </Button>
            <Button onClick={handleEdit}>
              Salvar Alterações
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Excluir */}
      <Dialog open={!!deletingId} onOpenChange={() => setDeletingId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir este bairro? Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletingId(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => deletingId && handleDelete(deletingId)}
            >
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
