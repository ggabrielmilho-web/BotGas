'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { api, type RadiusConfig } from '@/lib/api';

export function RadiusManager() {
  const [radiusConfigs, setRadiusConfigs] = useState<RadiusConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingConfig, setEditingConfig] = useState<RadiusConfig | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    center_address: '',
    radius_km_start: '',
    radius_km_end: '',
    delivery_fee: '10.00',
    delivery_time_minutes: '60',
  });

  const [error, setError] = useState('');

  useEffect(() => {
    loadRadiusConfigs();
  }, []);

  const loadRadiusConfigs = async () => {
    try {
      const data = await api.delivery.listRadiusConfigs();
      setRadiusConfigs(data);

      // Se houver configurações, pegar o endereço central da primeira
      if (data.length > 0 && !formData.center_address) {
        setFormData(prev => ({ ...prev, center_address: data[0].center_address }));
      }
    } catch (error) {
      console.error('Erro ao carregar configurações de raio:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const start = parseFloat(formData.radius_km_start);
    const end = parseFloat(formData.radius_km_end);

    if (isNaN(start) || isNaN(end)) {
      setError('KM inicial e final devem ser números válidos');
      return false;
    }

    if (start >= end) {
      setError('KM inicial deve ser menor que o KM final');
      return false;
    }

    if (start < 0 || end < 0) {
      setError('Valores de KM devem ser positivos');
      return false;
    }

    // Verificar sobreposição (apenas ao adicionar novo)
    if (!editingConfig) {
      const hasOverlap = radiusConfigs.some((config) => {
        return (start < config.radius_km_end && end > config.radius_km_start);
      });

      if (hasOverlap) {
        setError('Esta faixa se sobrepõe a uma faixa existente');
        return false;
      }
    }

    setError('');
    return true;
  };

  const handleAdd = async () => {
    if (!validateForm()) return;

    try {
      await api.delivery.createRadiusConfig({
        center_address: formData.center_address,
        radius_km_start: parseFloat(formData.radius_km_start),
        radius_km_end: parseFloat(formData.radius_km_end),
        delivery_fee: parseFloat(formData.delivery_fee),
        delivery_time_minutes: parseInt(formData.delivery_time_minutes),
      });

      setShowAddForm(false);
      setFormData({
        ...formData,
        radius_km_start: '',
        radius_km_end: '',
        delivery_fee: '10.00',
        delivery_time_minutes: '60',
      });
      setError('');
      loadRadiusConfigs();
    } catch (error: any) {
      console.error('Erro ao adicionar configuração:', error);
      setError(error.message || 'Erro ao adicionar configuração');
    }
  };

  const handleEdit = async () => {
    if (!editingConfig || !validateForm()) return;

    try {
      await api.delivery.updateRadiusConfig(editingConfig.id, {
        center_address: formData.center_address,
        radius_km_start: parseFloat(formData.radius_km_start),
        radius_km_end: parseFloat(formData.radius_km_end),
        delivery_fee: parseFloat(formData.delivery_fee),
        delivery_time_minutes: parseInt(formData.delivery_time_minutes),
      });

      setEditingConfig(null);
      setError('');
      loadRadiusConfigs();
    } catch (error: any) {
      console.error('Erro ao editar configuração:', error);
      setError(error.message || 'Erro ao editar configuração');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delivery.deleteRadiusConfig(id);
      setDeletingId(null);
      loadRadiusConfigs();
    } catch (error) {
      console.error('Erro ao excluir configuração:', error);
      alert('Erro ao excluir configuração');
    }
  };

  const openEditDialog = (config: RadiusConfig) => {
    setFormData({
      center_address: config.center_address,
      radius_km_start: config.radius_km_start.toString(),
      radius_km_end: config.radius_km_end.toString(),
      delivery_fee: config.delivery_fee.toString(),
      delivery_time_minutes: config.delivery_time_minutes.toString(),
    });
    setEditingConfig(config);
    setError('');
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
      {/* Endereço Central */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-blue-900">Endereço Central</h4>
            <p className="text-sm text-blue-800 mt-1">
              {radiusConfigs.length > 0 ? radiusConfigs[0].center_address : 'Não configurado'}
            </p>
            {radiusConfigs.length > 0 && radiusConfigs[0].center_lat && (
              <p className="text-xs text-blue-700 mt-1">
                GPS: {radiusConfigs[0].center_lat.toFixed(6)}, {radiusConfigs[0].center_lng?.toFixed(6)}
              </p>
            )}
          </div>
          {radiusConfigs.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => openEditDialog(radiusConfigs[0])}
            >
              Editar
            </Button>
          )}
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Faixas de Raio</h3>
          <p className="text-sm text-muted-foreground">
            {radiusConfigs.length} faixa(s) configurada(s)
          </p>
        </div>
        <Button onClick={() => setShowAddForm(true)}>
          + Adicionar Faixa
        </Button>
      </div>

      {/* Lista de Faixas */}
      {radiusConfigs.length === 0 ? (
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
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma faixa configurada</h3>
          <p className="mt-1 text-sm text-gray-500">
            Comece adicionando faixas de raio/KM com suas respectivas taxas.
          </p>
          <div className="mt-6">
            <Button onClick={() => setShowAddForm(true)}>
              + Adicionar Primeira Faixa
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {radiusConfigs.map((config, index) => (
            <div
              key={config.id}
              className="flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-4">
                {/* Indicador visual */}
                <div className={`w-3 h-16 rounded-full bg-gradient-to-b ${
                  index === 0 ? 'from-green-400 to-green-600' :
                  index === 1 ? 'from-blue-400 to-blue-600' :
                  index === 2 ? 'from-yellow-400 to-yellow-600' :
                  'from-red-400 to-red-600'
                }`} />

                <div>
                  <div className="font-semibold text-lg">
                    {config.radius_km_start} - {config.radius_km_end} km
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <div>Taxa: R$ {config.delivery_fee.toFixed(2)}</div>
                    <div>Tempo estimado: {config.delivery_time_minutes} min</div>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openEditDialog(config)}
                >
                  Editar
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700"
                  onClick={() => setDeletingId(config.id)}
                >
                  Excluir
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dialog Adicionar */}
      <Dialog open={showAddForm} onOpenChange={setShowAddForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Adicionar Faixa de Raio</DialogTitle>
            <DialogDescription>
              Configure uma nova faixa de distância com sua respectiva taxa de entrega.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {radiusConfigs.length === 0 && (
              <div>
                <Label htmlFor="center_address">Endereço Central</Label>
                <Input
                  id="center_address"
                  value={formData.center_address}
                  onChange={(e) => setFormData({ ...formData, center_address: e.target.value })}
                  placeholder="Ex: Rua Exemplo, 100, Centro, São Paulo"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  A distância será calculada a partir deste endereço
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="radius_start">KM Inicial</Label>
                <Input
                  id="radius_start"
                  type="number"
                  step="0.1"
                  value={formData.radius_km_start}
                  onChange={(e) => setFormData({ ...formData, radius_km_start: e.target.value })}
                  placeholder="Ex: 0, 5, 10"
                />
              </div>

              <div>
                <Label htmlFor="radius_end">KM Final</Label>
                <Input
                  id="radius_end"
                  type="number"
                  step="0.1"
                  value={formData.radius_km_end}
                  onChange={(e) => setFormData({ ...formData, radius_km_end: e.target.value })}
                  placeholder="Ex: 5, 10, 20"
                />
              </div>
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

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowAddForm(false); setError(''); }}>
              Cancelar
            </Button>
            <Button onClick={handleAdd} disabled={!formData.center_address && radiusConfigs.length === 0}>
              Adicionar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Editar */}
      <Dialog open={!!editingConfig} onOpenChange={() => { setEditingConfig(null); setError(''); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Faixa de Raio</DialogTitle>
            <DialogDescription>
              Atualize as informações desta faixa de distância.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="edit_center_address">Endereço Central</Label>
              <Input
                id="edit_center_address"
                value={formData.center_address}
                onChange={(e) => setFormData({ ...formData, center_address: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_radius_start">KM Inicial</Label>
                <Input
                  id="edit_radius_start"
                  type="number"
                  step="0.1"
                  value={formData.radius_km_start}
                  onChange={(e) => setFormData({ ...formData, radius_km_start: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="edit_radius_end">KM Final</Label>
                <Input
                  id="edit_radius_end"
                  type="number"
                  step="0.1"
                  value={formData.radius_km_end}
                  onChange={(e) => setFormData({ ...formData, radius_km_end: e.target.value })}
                />
              </div>
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

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setEditingConfig(null); setError(''); }}>
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
              Tem certeza que deseja excluir esta faixa de raio? Esta ação não pode ser desfeita.
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
