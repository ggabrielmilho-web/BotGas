'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { productsApi, type Product } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface ProductsSetupStepProps {
  onComplete: () => void
}

export default function ProductsSetupStep({ onComplete }: ProductsSetupStepProps) {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [newProduct, setNewProduct] = useState({
    name: '',
    price: '',
    description: '',
  })

  const handleAddProduct = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProduct.name || !newProduct.price) return

    setLoading(true)
    setError('')

    try {
      const product = await productsApi.create({
        name: newProduct.name,
        price: parseFloat(newProduct.price),
        description: newProduct.description,
        is_available: true,
      })

      setProducts([...products, product])
      setNewProduct({ name: '', price: '', description: '' })
    } catch (err: any) {
      setError(err.message || 'Erro ao adicionar produto')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveProduct = async (id: string) => {
    try {
      await productsApi.delete(id)
      setProducts(products.filter(p => p.id !== id))
    } catch (err: any) {
      setError(err.message || 'Erro ao remover produto')
    }
  }

  const handleContinue = () => {
    if (products.length > 0) {
      onComplete()
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="font-medium text-blue-900 mb-2">Dica!</h4>
        <p className="text-sm text-blue-800">
          Cadastre seus produtos principais agora. Você poderá adicionar mais produtos depois no dashboard.
        </p>
      </div>

      {/* Lista de Produtos */}
      {products.length > 0 && (
        <div className="space-y-2">
          <Label>Produtos Cadastrados ({products.length})</Label>
          <div className="space-y-2">
            {products.map((product) => (
              <div
                key={product.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
              >
                <div>
                  <p className="font-medium">{product.name}</p>
                  <p className="text-sm text-gray-600">
                    {formatCurrency(product.price)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveProduct(product.id)}
                >
                  Remover
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Formulário Novo Produto */}
      <form onSubmit={handleAddProduct} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="product_name">Nome do Produto *</Label>
            <Input
              id="product_name"
              type="text"
              placeholder="Ex: Botijão P13"
              value={newProduct.name}
              onChange={(e) =>
                setNewProduct({ ...newProduct, name: e.target.value })
              }
              required
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="product_price">Preço (R$) *</Label>
            <Input
              id="product_price"
              type="number"
              step="0.01"
              placeholder="Ex: 95.00"
              value={newProduct.price}
              onChange={(e) =>
                setNewProduct({ ...newProduct, price: e.target.value })
              }
              required
              className="mt-1"
            />
          </div>
        </div>

        <div>
          <Label htmlFor="product_description">Descrição (opcional)</Label>
          <Input
            id="product_description"
            type="text"
            placeholder="Ex: Botijão de gás 13kg"
            value={newProduct.description}
            onChange={(e) =>
              setNewProduct({ ...newProduct, description: e.target.value })
            }
            className="mt-1"
          />
        </div>

        <Button type="submit" disabled={loading} variant="outline" className="w-full">
          {loading ? 'Adicionando...' : '+ Adicionar Produto'}
        </Button>
      </form>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Produtos de Exemplo */}
      {products.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <h4 className="font-medium text-gray-900 mb-3">Produtos Comuns:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[
              { name: 'Botijão P13', price: 95 },
              { name: 'Botijão P45', price: 280 },
              { name: 'Galão 20L Água', price: 15 },
              { name: 'Galão 10L Água', price: 8 },
            ].map((example) => (
              <button
                key={example.name}
                type="button"
                onClick={() =>
                  setNewProduct({
                    name: example.name,
                    price: example.price.toString(),
                    description: '',
                  })
                }
                className="text-left p-2 border border-gray-300 rounded hover:bg-white transition-colors"
              >
                <p className="text-sm font-medium">{example.name}</p>
                <p className="text-xs text-gray-600">{formatCurrency(example.price)}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      <Button
        onClick={handleContinue}
        disabled={products.length === 0}
        className="w-full"
      >
        {products.length === 0
          ? 'Adicione pelo menos 1 produto'
          : `Continuar com ${products.length} produto(s)`}
      </Button>
    </div>
  )
}
