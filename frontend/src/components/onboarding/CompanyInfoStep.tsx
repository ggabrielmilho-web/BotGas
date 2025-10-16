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
    city: '',
    state: 'SP',
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
          city: tenant.address?.city || '',
          state: tenant.address?.state || 'SP',
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
        address: {
          city: formData.city,
          state: formData.state,
        },
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

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="city">
              Cidade <span className="text-red-500">*</span>
            </Label>
            <Input
              id="city"
              type="text"
              placeholder="São Paulo"
              value={formData.city}
              onChange={(e) =>
                setFormData({ ...formData, city: e.target.value })
              }
              required
              className="mt-1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Cidade da sua distribuidora
            </p>
          </div>

          <div>
            <Label htmlFor="state">
              Estado <span className="text-red-500">*</span>
            </Label>
            <select
              id="state"
              value={formData.state}
              onChange={(e) =>
                setFormData({ ...formData, state: e.target.value })
              }
              required
              className="mt-1 w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="AC">AC</option>
              <option value="AL">AL</option>
              <option value="AP">AP</option>
              <option value="AM">AM</option>
              <option value="BA">BA</option>
              <option value="CE">CE</option>
              <option value="DF">DF</option>
              <option value="ES">ES</option>
              <option value="GO">GO</option>
              <option value="MA">MA</option>
              <option value="MT">MT</option>
              <option value="MS">MS</option>
              <option value="MG">MG</option>
              <option value="PA">PA</option>
              <option value="PB">PB</option>
              <option value="PR">PR</option>
              <option value="PE">PE</option>
              <option value="PI">PI</option>
              <option value="RJ">RJ</option>
              <option value="RN">RN</option>
              <option value="RS">RS</option>
              <option value="RO">RO</option>
              <option value="RR">RR</option>
              <option value="SC">SC</option>
              <option value="SP">SP</option>
              <option value="SE">SE</option>
              <option value="TO">TO</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Estado da sua distribuidora
            </p>
          </div>
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
          <li>• Cidade/Estado são usados para validar entregas nos bairros cadastrados</li>
          <li>• CNPJ é opcional, apenas para emissão de NF</li>
        </ul>
      </div>

      <Button
        type="submit"
        disabled={loading || !formData.company_name || !formData.phone || !formData.city}
        className="w-full"
      >
        {loading ? 'Salvando...' : 'Salvar e Continuar'}
      </Button>
    </form>
  )
}
