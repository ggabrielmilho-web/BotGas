'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { productsApi, type Product } from '@/lib/api';

interface EditProductModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product | null;
  onProductUpdated: (product: Product) => void;
}

export function EditProductModal({ open, onOpenChange, product, onProductUpdated }: EditProductModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    is_available: true,
  });

  // Populate form when product changes
  useEffect(() => {
    if (product) {
      setFormData({
        name: product.name,
        description: product.description || '',
        price: product.price.toString(),
        category: product.category || '',
        is_available: product.is_available,
      });
    }
  }, [product]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!product) return;

    if (!formData.name || !formData.price) {
      setError('Nome e preço são obrigatórios');
      return;
    }

    const priceValue = parseFloat(formData.price);
    if (isNaN(priceValue) || priceValue <= 0) {
      setError('Preço deve ser um número maior que zero');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const updatedProduct = await productsApi.update(product.id, {
        name: formData.name,
        description: formData.description || undefined,
        price: priceValue,
        category: formData.category || undefined,
        is_available: formData.is_available,
      });

      onProductUpdated(updatedProduct);
      onOpenChange(false);
    } catch (err: any) {
      setError(err.message || 'Erro ao atualizar produto');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError('');
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Editar Produto</DialogTitle>
          <DialogDescription>
            Atualize as informações do produto
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-name">Nome do Produto *</Label>
            <Input
              id="edit-name"
              placeholder="Ex: Botijão P13"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={loading}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-price" className="text-base font-semibold">
              Preço (R$) *
            </Label>
            <Input
              id="edit-price"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="Ex: 95.00"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              disabled={loading}
              required
              className="text-lg font-medium"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-description">Descrição</Label>
            <Input
              id="edit-description"
              placeholder="Ex: Botijão de gás 13kg"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-category">Categoria</Label>
            <Input
              id="edit-category"
              placeholder="Ex: Gás, Água, Acessórios"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              disabled={loading}
            />
          </div>

          <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-md">
            <input
              type="checkbox"
              id="edit-is_available"
              checked={formData.is_available}
              onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
              disabled={loading}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <Label htmlFor="edit-is_available" className="cursor-pointer font-medium">
              Produto disponível para venda
            </Label>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
