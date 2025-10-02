'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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

export function OrdersList() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);

  const fetchOrders = async () => {
    try {
      const params = filter ? { status: filter } : {};
      const response = await api.get('/dashboard/orders', { params });
      setOrders(response.data);
    } catch (error) {
      console.error('Erro ao buscar pedidos:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();

    // Atualizar a cada 10 segundos
    const interval = setInterval(fetchOrders, 10000);

    return () => clearInterval(interval);
  }, [filter]);

  const updateOrderStatus = async (orderId: string, newStatus: string) => {
    try {
      await api.put(`/dashboard/orders/${orderId}/status`, null, {
        params: { status: newStatus },
      });
      fetchOrders(); // Atualizar lista
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filtros */}
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
                    {order.delivery_address.address}
                    {order.delivery_address.neighborhood &&
                      ` - ${order.delivery_address.neighborhood}`}
                  </p>
                </div>

                {/* Totais */}
                <div className="border-t pt-2 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Subtotal:</span>
                    <span>R$ {order.subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Taxa de Entrega:</span>
                    <span>R$ {order.delivery_fee.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between font-bold">
                    <span>Total:</span>
                    <span>R$ {order.total.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Pagamento:</span>
                    <span>{order.payment_method}</span>
                  </div>
                </div>

                {/* Ações */}
                <div className="flex gap-2 pt-2">
                  {order.status === 'new' && (
                    <Button
                      size="sm"
                      onClick={() => updateOrderStatus(order.id, 'confirmed')}
                    >
                      Confirmar
                    </Button>
                  )}
                  {order.status === 'confirmed' && (
                    <Button
                      size="sm"
                      onClick={() => updateOrderStatus(order.id, 'preparing')}
                    >
                      Iniciar Preparo
                    </Button>
                  )}
                  {order.status === 'preparing' && (
                    <Button
                      size="sm"
                      onClick={() => updateOrderStatus(order.id, 'delivering')}
                    >
                      Saiu para Entrega
                    </Button>
                  )}
                  {order.status === 'delivering' && (
                    <Button
                      size="sm"
                      onClick={() => updateOrderStatus(order.id, 'delivered')}
                    >
                      Marcar como Entregue
                    </Button>
                  )}
                  {['new', 'confirmed'].includes(order.status) && (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => updateOrderStatus(order.id, 'cancelled')}
                    >
                      Cancelar
                    </Button>
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
