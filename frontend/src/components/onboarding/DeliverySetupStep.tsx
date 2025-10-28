'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { deliveryApi } from '@/lib/api'

interface DeliverySetupStepProps {
  onComplete: () => void
}

type DeliveryMode = 'neighborhood' | 'radius' | 'hybrid'

export default function DeliverySetupStep({ onComplete }: DeliverySetupStepProps) {
  const [selectedMode, setSelectedMode] = useState<DeliveryMode | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState<'select' | 'configure'>('select')

  // Estados para modo Bairros
  const [neighborhoods, setNeighborhoods] = useState<
    Array<{ name: string; fee: number; time: number }>
  >([])
  const [newNeighborhood, setNewNeighborhood] = useState({
    name: '',
    fee: '',
    time: '60',
  })

  // Estados para modo Raio
  const [centerAddress, setCenterAddress] = useState('')
  const [radiusTiers, setRadiusTiers] = useState<
    Array<{ start: number; end: number; fee: number; time: number }>
  >([
    { start: 0, end: 5, fee: 0, time: 30 },
    { start: 5, end: 10, fee: 10, time: 45 },
    { start: 10, end: 20, fee: 20, time: 60 },
  ])
  const [newRadiusTier, setNewRadiusTier] = useState({
    start: '',
    end: '',
    fee: '',
    time: '60',
  })

  // Estados para modo Híbrido
  const [hybridNeighborhoods, setHybridNeighborhoods] = useState<
    Array<{ name: string; fee: number; time: number; delivery_type: string }>
  >([])
  const [hybridCenter, setHybridCenter] = useState('')
  const [hybridTiers, setHybridTiers] = useState<
    Array<{ start: number; end: number; fee: number; time: number }>
  >([
    { start: 0, end: 15, fee: 15, time: 60 },
    { start: 15, end: 25, fee: 25, time: 90 },
  ])

  const handleModeSelect = (mode: DeliveryMode) => {
    setSelectedMode(mode)
    setStep('configure')
  }

  const handleAddNeighborhood = () => {
    if (!newNeighborhood.name) return

    setNeighborhoods([
      ...neighborhoods,
      {
        name: newNeighborhood.name,
        fee: parseFloat(newNeighborhood.fee) || 0,
        time: parseInt(newNeighborhood.time) || 60,
      },
    ])
    setNewNeighborhood({ name: '', fee: '', time: '60' })
  }

  const handleAddRadiusTier = () => {
    const start = parseFloat(newRadiusTier.start)
    const end = parseFloat(newRadiusTier.end)
    const fee = parseFloat(newRadiusTier.fee)
    const time = parseInt(newRadiusTier.time) || 60

    // Validação
    if (isNaN(start) || isNaN(end) || isNaN(fee)) {
      setError('Preencha todos os campos da faixa de raio')
      return
    }

    if (start >= end) {
      setError('O KM inicial deve ser menor que o KM final')
      return
    }

    if (start < 0 || end < 0) {
      setError('Os valores de KM devem ser positivos')
      return
    }

    // Verificar sobreposição com faixas existentes
    const hasOverlap = radiusTiers.some((tier) => {
      return (start < tier.end && end > tier.start)
    })

    if (hasOverlap) {
      setError('Esta faixa se sobrepõe a uma faixa existente. Por favor, ajuste os valores.')
      return
    }

    // Adicionar nova faixa
    const newTiers = [...radiusTiers, { start, end, fee, time }]
    // Ordenar por km inicial
    newTiers.sort((a, b) => a.start - b.start)
    setRadiusTiers(newTiers)
    setNewRadiusTier({ start: '', end: '', fee: '', time: '60' })
    setError('')
  }

  const handleSaveNeighborhoodMode = async () => {
    if (neighborhoods.length === 0) {
      setError('Adicione pelo menos 1 bairro')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Atualizar modo
      await deliveryApi.updateMode('neighborhood')

      // Criar bairros
      await deliveryApi.bulkCreateNeighborhoods(neighborhoods)

      onComplete()
    } catch (err: any) {
      setError(err.message || 'Erro ao configurar entrega')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveRadiusMode = async () => {
    if (!centerAddress) {
      setError('Informe o endereço central')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Atualizar modo
      await deliveryApi.updateMode('radius')

      // Criar configs de raio
      await deliveryApi.bulkCreateRadiusConfigs(centerAddress, radiusTiers)

      onComplete()
    } catch (err: any) {
      setError(err.message || 'Erro ao configurar entrega')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveHybridMode = async () => {
    if (hybridNeighborhoods.length === 0 || !hybridCenter) {
      setError('Configure pelo menos 1 bairro e o endereço central')
      return
    }

    setLoading(true)
    setError('')

    try {
      await deliveryApi.setupHybrid({
        center_address: hybridCenter,
        main_neighborhoods: hybridNeighborhoods,
        radius_tiers: hybridTiers,
      })

      onComplete()
    } catch (err: any) {
      setError(err.message || 'Erro ao configurar entrega')
    } finally {
      setLoading(false)
    }
  }

  if (step === 'select') {
    return (
      <div className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h4 className="font-medium text-blue-900 mb-2">Escolha o modo de entrega</h4>
          <p className="text-sm text-blue-800">
            Você pode trocar o modo depois no dashboard. Escolha o que melhor se adequa ao seu negócio.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Modo Bairros */}
          <Card
            className="cursor-pointer hover:border-blue-500 transition-all"
            onClick={() => handleModeSelect('neighborhood')}
          >
            <CardContent className="p-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-lg mb-2">Por Bairros</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Configure manualmente os bairros que você atende
                </p>
                <ul className="text-xs text-gray-500 text-left space-y-1">
                  <li>✓ Simples de configurar</li>
                  <li>✓ Sem custos de API</li>
                  <li>✓ Taxa por bairro</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Modo Raio */}
          <Card
            className="cursor-pointer hover:border-blue-500 transition-all"
            onClick={() => handleModeSelect('radius')}
          >
            <CardContent className="p-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                </div>
                <h3 className="font-semibold text-lg mb-2">Por Raio/KM</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Entrega automática baseada em distância
                </p>
                <ul className="text-xs text-gray-500 text-left space-y-1">
                  <li>✓ Cobertura total</li>
                  <li>✓ GPS preciso</li>
                  <li>✓ Usa Google Maps</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Modo Híbrido */}
          <Card
            className="cursor-pointer hover:border-blue-500 transition-all border-2 border-yellow-400"
            onClick={() => handleModeSelect('hybrid')}
          >
            <CardContent className="p-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-lg mb-2">Híbrido</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Combina bairros + raio (recomendado)
                </p>
                <ul className="text-xs text-gray-500 text-left space-y-1">
                  <li>✓ Melhor dos 2 mundos</li>
                  <li>✓ Economia de API</li>
                  <li>✓ Máxima cobertura</li>
                </ul>
                <span className="inline-block mt-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                  Recomendado
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Configuração de Bairros
  if (selectedMode === 'neighborhood') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Configuração por Bairros</h3>
          <Button variant="ghost" size="sm" onClick={() => setStep('select')}>
            Trocar Modo
          </Button>
        </div>

        {/* Lista de Bairros */}
        {neighborhoods.length > 0 && (
          <div className="space-y-2">
            <Label>Bairros Cadastrados ({neighborhoods.length})</Label>
            <div className="space-y-2">
              {neighborhoods.map((n, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div>
                    <p className="font-medium">{n.name}</p>
                    <p className="text-sm text-gray-600">
                      Taxa: R$ {n.fee.toFixed(2)} • Tempo: {n.time}min
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setNeighborhoods(neighborhoods.filter((_, i) => i !== index))}
                  >
                    Remover
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Formulário Novo Bairro */}
        <div className="space-y-4 border rounded-md p-4">
          <Label>Adicionar Bairro</Label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Input
                placeholder="Nome do bairro"
                value={newNeighborhood.name}
                onChange={(e) =>
                  setNewNeighborhood({ ...newNeighborhood, name: e.target.value })
                }
              />
            </div>
            <div>
              <Input
                type="number"
                step="0.01"
                placeholder="Taxa (R$)"
                value={newNeighborhood.fee}
                onChange={(e) =>
                  setNewNeighborhood({ ...newNeighborhood, fee: e.target.value })
                }
              />
            </div>
            <div>
              <Input
                type="number"
                placeholder="Tempo (min)"
                value={newNeighborhood.time}
                onChange={(e) =>
                  setNewNeighborhood({ ...newNeighborhood, time: e.target.value })
                }
              />
            </div>
          </div>
          <Button onClick={handleAddNeighborhood} variant="outline" className="w-full">
            + Adicionar Bairro
          </Button>
        </div>

        {/* Bairros Exemplo */}
        {neighborhoods.length === 0 && (
          <div className="bg-gray-50 border rounded-md p-4">
            <Label className="mb-3 block">Exemplos (clique para adicionar):</Label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {[
                { name: 'Centro', fee: 0, time: 30 },
                { name: 'Jardins', fee: 10, time: 45 },
                { name: 'Paulista', fee: 10, time: 45 },
                { name: 'Vila Mariana', fee: 15, time: 60 },
              ].map((ex) => (
                <button
                  key={ex.name}
                  type="button"
                  onClick={() =>
                    setNeighborhoods([...neighborhoods, ex])
                  }
                  className="text-left p-2 border rounded hover:bg-white text-sm"
                >
                  {ex.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Button
          onClick={handleSaveNeighborhoodMode}
          disabled={loading || neighborhoods.length === 0}
          className="w-full"
        >
          {loading ? 'Salvando...' : 'Salvar Configuração'}
        </Button>
      </div>
    )
  }

  // Configuração de Raio
  if (selectedMode === 'radius') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Configuração por Raio/KM</h3>
          <Button variant="ghost" size="sm" onClick={() => setStep('select')}>
            Trocar Modo
          </Button>
        </div>

        <div>
          <Label>Endereço Central (sua loja/depósito)</Label>
          <Input
            placeholder="Ex: Rua Exemplo, 100, Centro, São Paulo"
            value={centerAddress}
            onChange={(e) => setCenterAddress(e.target.value)}
            className="mt-1"
          />
          <p className="text-xs text-gray-500 mt-1">
            A distância será calculada a partir deste endereço
          </p>
        </div>

        <div>
          <Label className="mb-3 block">Faixas de Raio ({radiusTiers.length})</Label>
          <div className="space-y-2">
            {radiusTiers.map((tier, index) => (
              <div key={index} className="grid grid-cols-4 gap-2 items-center p-3 bg-gray-50 rounded-md">
                <div className="text-sm">
                  <span className="font-medium">{tier.start}-{tier.end}km</span>
                </div>
                <div className="text-sm">R$ {tier.fee.toFixed(2)}</div>
                <div className="text-sm">{tier.time}min</div>
                <div className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setRadiusTiers(radiusTiers.filter((_, i) => i !== index))}
                  >
                    Remover
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Formulário Nova Faixa de Raio */}
        <div className="space-y-4 border rounded-md p-4">
          <Label>Adicionar Nova Faixa de KM</Label>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div>
              <Input
                type="number"
                step="0.1"
                min="0"
                placeholder="KM inicial"
                value={newRadiusTier.start}
                onChange={(e) =>
                  setNewRadiusTier({ ...newRadiusTier, start: e.target.value })
                }
              />
              <p className="text-xs text-gray-500 mt-1">Ex: 0, 5, 12</p>
            </div>
            <div>
              <Input
                type="number"
                step="0.1"
                min="0"
                placeholder="KM final"
                value={newRadiusTier.end}
                onChange={(e) =>
                  setNewRadiusTier({ ...newRadiusTier, end: e.target.value })
                }
              />
              <p className="text-xs text-gray-500 mt-1">Ex: 5, 12, 20</p>
            </div>
            <div>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="Taxa (R$)"
                value={newRadiusTier.fee}
                onChange={(e) =>
                  setNewRadiusTier({ ...newRadiusTier, fee: e.target.value })
                }
              />
              <p className="text-xs text-gray-500 mt-1">Ex: 10.00</p>
            </div>
            <div>
              <Input
                type="number"
                min="0"
                placeholder="Tempo (min)"
                value={newRadiusTier.time}
                onChange={(e) =>
                  setNewRadiusTier({ ...newRadiusTier, time: e.target.value })
                }
              />
              <p className="text-xs text-gray-500 mt-1">Ex: 45</p>
            </div>
          </div>
          <Button onClick={handleAddRadiusTier} variant="outline" className="w-full">
            + Adicionar Faixa
          </Button>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Button
          onClick={handleSaveRadiusMode}
          disabled={loading || !centerAddress}
          className="w-full"
        >
          {loading ? 'Salvando...' : 'Salvar Configuração'}
        </Button>
      </div>
    )
  }

  // Configuração Híbrida (simplificada)
  if (selectedMode === 'hybrid') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Configuração Híbrida</h3>
          <Button variant="ghost" size="sm" onClick={() => setStep('select')}>
            Trocar Modo
          </Button>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <p className="text-sm text-yellow-800">
            Modo híbrido combina bairros principais (rápido) + raio para outros endereços (preciso).
            Economiza até 80% em chamadas de API!
          </p>
        </div>

        <div>
          <Label>Endereço Central</Label>
          <Input
            placeholder="Ex: Rua Exemplo, 100, Centro, São Paulo"
            value={hybridCenter}
            onChange={(e) => setHybridCenter(e.target.value)}
            className="mt-1"
          />
        </div>

        <div>
          <Label>Bairros Principais (opcional - clique para adicionar)</Label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
            {['Centro', 'Paulista', 'Jardins', 'Pinheiros', 'Itaim', 'Vila Mariana'].map((name) => (
              <button
                key={name}
                type="button"
                onClick={() => {
                  if (!hybridNeighborhoods.find(n => n.name === name)) {
                    setHybridNeighborhoods([
                      ...hybridNeighborhoods,
                      { name, fee: 10, time: 45, delivery_type: 'paid' },
                    ])
                  }
                }}
                className={`p-2 border rounded text-sm ${
                  hybridNeighborhoods.find(n => n.name === name)
                    ? 'bg-blue-100 border-blue-500'
                    : 'hover:bg-gray-50'
                }`}
              >
                {name}
              </button>
            ))}
          </div>
          {hybridNeighborhoods.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              {hybridNeighborhoods.length} bairro(s) selecionado(s)
            </p>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Button
          onClick={handleSaveHybridMode}
          disabled={loading || !hybridCenter}
          className="w-full"
        >
          {loading ? 'Salvando...' : 'Salvar Configuração Híbrida'}
        </Button>
      </div>
    )
  }

  return null
}
