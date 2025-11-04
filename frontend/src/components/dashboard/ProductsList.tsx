'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { productsApi, type Product } from '@/lib/api';
import { AddProductModal } from './AddProductModal';
import { EditProductModal } from './EditProductModal';
import { Pencil, Trash2, Plus, Package } from 'lucide-react';

export function ProductsList() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data = await productsApi.list();
      setProducts(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar produtos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleProductAdded = (product: Product) => {
    setProducts([...products, product]);
  };

  const handleProductUpdated = (updatedProduct: Product) => {
    setProducts(products.map((p) => (p.id === updatedProduct.id ? updatedProduct : p)));
  };

  const handleToggleAvailability = async (product: Product) => {
    try {
      const updatedProduct = await productsApi.update(product.id, {
        is_available: !product.is_available,
      });
      setProducts(products.map((p) => (p.id === updatedProduct.id ? updatedProduct : p)));
    } catch (err: any) {
      alert('Erro ao atualizar disponibilidade: ' + err.message);
    }
  };

  const handleDelete = async (productId: string) => {
    if (!confirm('Tem certeza que deseja excluir este produto?')) {
      return;
    }

    try {
      setDeletingId(productId);
      await productsApi.delete(productId);
      setProducts(products.filter((p) => p.id !== productId));
    } catch (err: any) {
      alert('Erro ao excluir produto: ' + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleEdit = (product: Product) => {
    setSelectedProduct(product);
    setEditModalOpen(true);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="mt-4 text-muted-foreground">Carregando produtos...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center">
            <p className="text-red-600">{error}</p>
            <Button onClick={fetchProducts} variant="outline" className="mt-4">
              Tentar Novamente
            </Button>
          </div>
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
              <CardTitle>Produtos</CardTitle>
              <CardDescription>
                Gerencie seu catálogo de produtos
              </CardDescription>
            </div>
            <Button onClick={() => setAddModalOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Adicionar Produto
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {products.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Package className="h-16 w-16 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Nenhum produto cadastrado
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Comece adicionando seu primeiro produto ao catálogo
              </p>
              <Button onClick={() => setAddModalOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Adicionar Primeiro Produto
              </Button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {products.map((product) => (
                <Card key={product.id} className="overflow-hidden">
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      {/* Header com nome e badge */}
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">{product.name}</h3>
                          {product.category && (
                            <p className="text-xs text-gray-500">{product.category}</p>
                          )}
                        </div>
                        <Badge
                          variant={product.is_available ? 'default' : 'secondary'}
                          className={
                            product.is_available
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }
                        >
                          {product.is_available ? 'Disponível' : 'Indisponível'}
                        </Badge>
                      </div>

                      {/* Descrição */}
                      {product.description && (
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {product.description}
                        </p>
                      )}

                      {/* Preço */}
                      <div className="pt-2 border-t">
                        <p className="text-2xl font-bold text-gray-900">
                          {formatCurrency(product.price)}
                        </p>
                      </div>

                      {/* Ações */}
                      <div className="flex items-center gap-2 pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(product)}
                          className="flex-1"
                        >
                          <Pencil className="mr-2 h-3 w-3" />
                          Editar
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleToggleAvailability(product)}
                          className="flex-1"
                        >
                          {product.is_available ? 'Desativar' : 'Ativar'}
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(product.id)}
                          disabled={deletingId === product.id}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      <AddProductModal
        open={addModalOpen}
        onOpenChange={setAddModalOpen}
        onProductAdded={handleProductAdded}
      />

      <EditProductModal
        open={editModalOpen}
        onOpenChange={setEditModalOpen}
        product={selectedProduct}
        onProductUpdated={handleProductUpdated}
      />
    </>
  );
}
