'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { DateRangeFilter } from './DateRangeFilter';
import { api } from '@/lib/api';

interface Order {
  id: string;
  order_number: number;
  status: string;
  items: Array<{
    product_name: string;
    quantity: number;
    price: number;
    subtotal: number;
  }>;
  subtotal: number;
  delivery_fee: number;
  total: number;
  delivery_address: {
    address: string;
    neighborhood?: string;
  };
  payment_method: string;
  created_at: string;
  customer_id: string;
  driver_name?: string;
}

const statusColors: Record<string, string> = {
  new: 'bg-blue-500',
  confirmed: 'bg-yellow-500',
  preparing: 'bg-orange-500',
  delivering: 'bg-purple-500',
  delivered: 'bg-green-500',
  cancelled: 'bg-red-500',
};

const statusLabels: Record<string, string> = {
  new: 'Novo',
  confirmed: 'Confirmado',
  preparing: 'Preparando',
  delivering: 'Entregando',
  delivered: 'Entregue',
  cancelled: 'Cancelado',
};

// Componente interno para selecionar motoboy
function SendToDriverButton({ orderId, onSent }: { orderId: string; onSent: () => void }) {
  const [open, setOpen] = useState(false);
  const [drivers, setDrivers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (open) {
      setLoading(true);
      api.get('/api/v1/delivery-drivers/active')
        .then(setDrivers)
        .finally(() => setLoading(false));
    }
  }, [open]);

  const handleSend = async (driverId: string) => {
    setSending(true);
    try {
      await api.post(`/api/v1/dashboard/orders/${orderId}/send-to-driver`, {
        driver_id: driverId
      });
      alert('Ticket enviado ao motoboy!');
      onSent();
      setOpen(false);
    } catch (error: any) {
      alert('Erro: ' + error.message);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>
        Enviar para Motoboy
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Selecionar Motoboy</DialogTitle>
          </DialogHeader>

          {loading ? (
            <div className="py-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            </div>
          ) : drivers.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <p>Nenhum motoboy ativo.</p>
              <p className="text-sm mt-2">Cadastre um na aba Motoboys.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {drivers.map((driver) => (
                <div
                  key={driver.id}
                  className="flex items-center justify-between p-3 border rounded hover:bg-gray-50"
                >
                  <div>
                    <p className="font-medium">{driver.name}</p>
                    <p className="text-sm text-gray-500">{driver.phone}</p>
                    <p className="text-xs text-gray-400">
                      {driver.total_deliveries} entregas realizadas
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleSend(driver.id)}
                    disabled={sending}
                  >
                    {sending ? 'Enviando...' : 'Selecionar'}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

export function OrdersList() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);
  const [dateFilter, setDateFilter] = useState<{ from: string | null; to: string | null }>({
    from: null,
    to: null,
  });

  const fetchOrders = async () => {
    try {
      // Construir URL com query parameters
      let url = '/api/v1/dashboard/orders';
      const params = new URLSearchParams();

      if (filter) params.append('status', filter);
      if (dateFilter.from) params.append('date_from', dateFilter.from);
      if (dateFilter.to) params.append('date_to', dateFilter.to);

      if (params.toString()) url += '?' + params.toString();

      console.log('🔍 Buscando pedidos em:', url);
      const response = await api.get(url);
      console.log('✅ Resposta recebida:', response);
      setOrders(Array.isArray(response) ? response : []);
    } catch (error) {
      console.error('❌ Erro ao buscar pedidos:', error);
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();

    // Atualizar a cada 10 segundos
    const interval = setInterval(fetchOrders, 10000);

    return () => clearInterval(interval);
  }, [filter, dateFilter]);

  const updateOrderStatus = async (orderId: string, newStatus: string) => {
    try {
      console.log('🔄 Atualizando pedido', orderId, 'para status:', newStatus);
      await api.put(`/api/v1/dashboard/orders/${orderId}/status?status=${newStatus}`);
      console.log('✅ Status atualizado com sucesso');
      fetchOrders(); // Atualizar lista
    } catch (error) {
      console.error('❌ Erro ao atualizar status:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="ml-2">Carregando pedidos...</p>
      </div>
    );
  }

  console.log('🎯 OrdersList renderizado com', orders.length, 'pedidos');

  const handleDateFilterChange = (from: string | null, to: string | null) => {
    setDateFilter({ from, to });
  };

  return (
    <div className="space-y-4">
      {/* Filtro de Data */}
      <DateRangeFilter onFilterChange={handleDateFilterChange} />

      {/* Filtros de Status */}
      <div className="flex gap-2">
        <Button
          variant={filter === null ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter(null)}
        >
          Todos
        </Button>
        <Button
          variant={filter === 'new' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('new')}
        >
          Novos
        </Button>
        <Button
          variant={filter === 'confirmed' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('confirmed')}
        >
          Confirmados
        </Button>
        <Button
          variant={filter === 'delivering' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('delivering')}
        >
          Em Entrega
        </Button>
      </div>

      {/* Lista de Pedidos */}
      {orders.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center p-8">
            <p className="text-muted-foreground">Nenhum pedido encontrado</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {orders.map((order) => (
            <Card key={order.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">
                      Pedido #{order.order_number}
                    </CardTitle>
                    <CardDescription>
                      {new Date(order.created_at).toLocaleString('pt-BR')}
                    </CardDescription>
                  </div>
                  <Badge className={statusColors[order.status]}>
                    {statusLabels[order.status]}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Itens do Pedido */}
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Itens:</h4>
                  {order.items.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>
                        {item.quantity}x {item.product_name}
                      </span>
                      <span>R$ {item.subtotal.toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                {/* Endereço */}
                <div>
                  <h4 className="font-semibold text-sm">Endereço:</h4>
                  <p className="text-sm text-muted-foreground">
                    {order.delivery_address.normalized_address || order.delivery_address.address || 'Endereço não informado'}
                  </p>
                </div>

                {/* Totais */}
                <div className="border-t pt-2 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Subtotal:</span>
                    <span>R$ {Number(order.subtotal).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Taxa de Entrega:</span>
                    <span>R$ {Number(order.delivery_fee).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between font-bold">
                    <span>Total:</span>
                    <span>R$ {Number(order.total).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Pagamento:</span>
                    <span>{order.payment_method}</span>
                  </div>
                </div>

                {/* Ações */}
                <div className="flex gap-2 pt-2">
                  {order.status === 'new' && (
                    <>
                      <SendToDriverButton orderId={order.id} onSent={fetchOrders} />
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => updateOrderStatus(order.id, 'cancelled')}
                      >
                        Cancelar
                      </Button>
                    </>
                  )}

                  {order.status === 'confirmed' && (
                    <>
                      <Badge className="bg-yellow-600">
                        🚚 Em entrega
                        {order.driver_name && ` - ${order.driver_name}`}
                      </Badge>
                      <Button
                        size="sm"
                        onClick={() => updateOrderStatus(order.id, 'delivered')}
                      >
                        Confirmar Entrega
                      </Button>
                    </>
                  )}

                  {order.status === 'delivered' && (
                    <Badge className="bg-green-600">✅ Entregue</Badge>
                  )}

                  {order.status === 'cancelled' && (
                    <Badge className="bg-red-600">❌ Cancelado</Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

