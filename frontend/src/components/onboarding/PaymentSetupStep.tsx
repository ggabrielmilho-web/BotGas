'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { tenantApi } from '@/lib/api'

interface PaymentSetupStepProps {
  onComplete: () => void
}

export default function PaymentSetupStep({ onComplete }: PaymentSetupStepProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    payment_methods: ['Dinheiro'],
    pix_enabled: false,
    pix_key: '',
    pix_name: '',
    payment_instructions: '',
  })

  const togglePaymentMethod = (method: string) => {
    const methods = formData.payment_methods.includes(method)
      ? formData.payment_methods.filter((m) => m !== method)
      : [...formData.payment_methods, method]

    setFormData({ ...formData, payment_methods: methods })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await tenantApi.update({
        payment_methods: formData.payment_methods,
        pix_enabled: formData.pix_enabled,
        pix_key: formData.pix_key || undefined,
        pix_name: formData.pix_name || undefined,
        payment_instructions: formData.payment_instructions || undefined,
      })

      onComplete()
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar configuração')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="font-medium text-blue-900 mb-2">Pagamento Simplificado</h4>
        <p className="text-sm text-blue-800">
          O bot apenas informará as formas de pagamento disponíveis. Não há validação automática de pagamento.
        </p>
      </div>

      <div>
        <Label className="mb-3 block">Formas de Pagamento Aceitas</Label>
        <div className="space-y-2">
          {['Dinheiro', 'Cartão', 'PIX'].map((method) => (
            <button
              key={method}
              type="button"
              onClick={() => togglePaymentMethod(method)}
              className={`
                w-full p-4 border-2 rounded-lg flex items-center justify-between transition-all
                ${
                  formData.payment_methods.includes(method)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <div className="flex items-center">
                <div
                  className={`
                    w-5 h-5 rounded border-2 flex items-center justify-center mr-3
                    ${
                      formData.payment_methods.includes(method)
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    }
                  `}
                >
                  {formData.payment_methods.includes(method) && (
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <span className="font-medium">{method}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Configuração PIX */}
      {formData.payment_methods.includes('PIX') && (
        <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
          <div className="flex items-center justify-between">
            <Label>Habilitar PIX</Label>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, pix_enabled: !formData.pix_enabled })}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${formData.pix_enabled ? 'bg-blue-600' : 'bg-gray-300'}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${formData.pix_enabled ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
          </div>

          {formData.pix_enabled && (
            <>
              <div>
                <Label htmlFor="pix_key">Chave PIX</Label>
                <Input
                  id="pix_key"
                  type="text"
                  placeholder="CPF, CNPJ, E-mail, Celular ou Aleatória"
                  value={formData.pix_key}
                  onChange={(e) => setFormData({ ...formData, pix_key: e.target.value })}
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="pix_name">Nome do Beneficiário</Label>
                <Input
                  id="pix_name"
                  type="text"
                  placeholder="Nome que aparece no PIX"
                  value={formData.pix_name}
                  onChange={(e) => setFormData({ ...formData, pix_name: e.target.value })}
                  className="mt-1"
                />
              </div>
            </>
          )}
        </div>
      )}

      {/* Instruções de Pagamento */}
      <div>
        <Label htmlFor="payment_instructions">
          Instruções Adicionais (opcional)
        </Label>
        <textarea
          id="payment_instructions"
          rows={3}
          placeholder="Ex: Troco para quanto? Envie comprovante do PIX..."
          value={formData.payment_instructions}
          onChange={(e) =>
            setFormData({ ...formData, payment_instructions: e.target.value })
          }
          className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        />
        <p className="text-xs text-gray-500 mt-1">
          Estas instruções serão mostradas ao cliente após confirmar o pedido
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <div className="bg-green-50 border border-green-200 rounded-md p-4">
        <h4 className="font-medium text-green-900 mb-2">
          Pronto para começar! 🎉
        </h4>
        <p className="text-sm text-green-800">
          Após salvar, você será redirecionado para o dashboard onde poderá gerenciar
          pedidos, ver conversas e ajustar configurações.
        </p>
      </div>

      <Button
        type="submit"
        disabled={loading || formData.payment_methods.length === 0}
        className="w-full"
        size="lg"
      >
        {loading ? 'Finalizando...' : 'Finalizar Configuração'}
      </Button>
    </form>
  )
}
