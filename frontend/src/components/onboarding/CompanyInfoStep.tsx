'use client'

import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { tenantApi } from '@/lib/api'
import { formatPhone, formatCNPJ } from '@/lib/utils'

interface CompanyInfoStepProps {
  onComplete: () => void
}

export default function CompanyInfoStep({ onComplete }: CompanyInfoStepProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    company_name: '',
    phone: '',
    cnpj: '',
  })

  // Carregar dados existentes
  useEffect(() => {
    async function loadTenantData() {
      try {
        const tenant = await tenantApi.get()
        setFormData({
          company_name: tenant.company_name || '',
          phone: tenant.phone || '',
          cnpj: tenant.cnpj || '',
        })
      } catch (err) {
        console.error('Erro ao carregar dados:', err)
      }
    }
    loadTenantData()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await tenantApi.update({
        company_name: formData.company_name,
        phone: formData.phone.replace(/\D/g, ''),
      })

      onComplete()
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar dados')
    } finally {
      setLoading(false)
    }
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhone(e.target.value)
    setFormData({ ...formData, phone: formatted })
  }

  const handleCNPJChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCNPJ(e.target.value)
    setFormData({ ...formData, cnpj: formatted })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div>
          <Label htmlFor="company_name">
            Nome da Empresa <span className="text-red-500">*</span>
          </Label>
          <Input
            id="company_name"
            type="text"
            placeholder="Distribuidora Exemplo Ltda"
            value={formData.company_name}
            onChange={(e) =>
              setFormData({ ...formData, company_name: e.target.value })
            }
            required
            className="mt-1"
          />
          <p className="text-xs text-gray-500 mt-1">
            Nome que aparecerá para seus clientes
          </p>
        </div>

        <div>
          <Label htmlFor="phone">
            Telefone/WhatsApp <span className="text-red-500">*</span>
          </Label>
          <Input
            id="phone"
            type="tel"
            placeholder="(11) 99999-9999"
            value={formData.phone}
            onChange={handlePhoneChange}
            required
            className="mt-1"
          />
          <p className="text-xs text-gray-500 mt-1">
            Número principal de contato
          </p>
        </div>

        <div>
          <Label htmlFor="cnpj">CNPJ (opcional)</Label>
          <Input
            id="cnpj"
            type="text"
            placeholder="00.000.000/0000-00"
            value={formData.cnpj}
            onChange={handleCNPJChange}
            className="mt-1"
          />
          <p className="text-xs text-gray-500 mt-1">
            Para emissão de notas fiscais (opcional)
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="font-medium text-blue-900 mb-2">Por que precisamos disso?</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Nome da empresa aparece nas mensagens do bot</li>
          <li>• Telefone é usado para suporte e notificações</li>
          <li>• CNPJ é opcional, apenas para emissão de NF</li>
        </ul>
      </div>

      <Button
        type="submit"
        disabled={loading || !formData.company_name || !formData.phone}
        className="w-full"
      >
        {loading ? 'Salvando...' : 'Salvar e Continuar'}
      </Button>
    </form>
  )
}
