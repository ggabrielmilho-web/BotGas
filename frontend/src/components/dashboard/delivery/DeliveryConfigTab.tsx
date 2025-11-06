'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DeliveryStats } from './DeliveryStats';
import { DeliveryModeSelector } from './DeliveryModeSelector';
import { NeighborhoodManager } from './NeighborhoodManager';
import { RadiusManager } from './RadiusManager';
import { HybridManager } from './HybridManager';
import { api, type DeliveryConfig } from '@/lib/api';

export function DeliveryConfigTab() {
  const [config, setConfig] = useState<DeliveryConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await api.delivery.getConfig();
      setConfig(data);
    } catch (error: any) {
      console.error('Erro ao carregar configuração:', error);
      setError(error.message || 'Erro ao carregar configuração de entrega');
    } finally {
      setLoading(false);
    }
  };

  const handleModeChanged = () => {
    // Recarregar configuração após trocar modo
    setLoading(true);
    loadConfig();
  };

  const getModeInfo = (mode: string) => {
    const modes = {
      neighborhood: {
        name: 'Por Bairros',
        description: 'Validação manual por bairros cadastrados',
        color: 'bg-blue-100 text-blue-800 border-blue-300',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
      },
      radius: {
        name: 'Por Raio/KM',
        description: 'Validação automática por distância (Google Maps)',
        color: 'bg-green-100 text-green-800 border-green-300',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        ),
      },
      hybrid: {
        name: 'Híbrido',
        description: 'Combina bairros + raio (recomendado)',
        color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        ),
      },
    };

    return modes[mode as keyof typeof modes] || modes.neighborhood;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Carregando configuração de entrega...</p>
        </div>
      </div>
    );
  }

  if (error || !config) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Erro ao Carregar Configuração</CardTitle>
            <CardDescription>{error || 'Configuração de entrega não encontrada'}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Não foi possível carregar a configuração de entrega. Isso pode acontecer se você ainda
              não configurou o sistema de entrega no onboarding.
            </p>
            <p className="text-sm text-muted-foreground">
              Tente recarregar a página ou entre em contato com o suporte.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const modeInfo = getModeInfo(config.delivery_mode);

  return (
    <div className="space-y-6">
      {/* Header com info do modo atual */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${modeInfo.color}`}>
                {modeInfo.icon}
              </div>
              <div>
                <CardTitle className="text-2xl">Configuração de Entrega</CardTitle>
                <CardDescription className="mt-1">
                  Gerencie como os endereços dos clientes são validados
                </CardDescription>
              </div>
            </div>
            <DeliveryModeSelector
              currentMode={config.delivery_mode as 'neighborhood' | 'radius' | 'hybrid'}
              onModeChanged={handleModeChanged}
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Modo ativo:</span>
            <Badge variant="outline" className={modeInfo.color}>
              {modeInfo.name}
            </Badge>
            <span className="text-sm text-muted-foreground">• {modeInfo.description}</span>
          </div>

          {/* Entrega grátis */}
          {config.free_delivery_minimum && (
            <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm font-medium text-green-900">
                  Entrega grátis para pedidos acima de R$ {config.free_delivery_minimum.toFixed(2)}
                </span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Estatísticas */}
      <DeliveryStats />

      {/* Conteúdo dinâmico baseado no modo */}
      <Card>
        <CardHeader>
          <CardTitle>Gerenciar Configurações</CardTitle>
          <CardDescription>
            {config.delivery_mode === 'neighborhood' && 'Configure os bairros que você atende'}
            {config.delivery_mode === 'radius' && 'Configure as faixas de distância e taxas'}
            {config.delivery_mode === 'hybrid' && 'Configure bairros principais e faixas de raio'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {config.delivery_mode === 'neighborhood' && <NeighborhoodManager />}
          {config.delivery_mode === 'radius' && <RadiusManager />}
          {config.delivery_mode === 'hybrid' && <HybridManager />}
        </CardContent>
      </Card>

      {/* Dicas gerais */}
      <Card>
        <CardHeader>
          <CardTitle>💡 Dicas de Otimização</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-muted-foreground">
                <strong>Cache automático:</strong> Endereços validados são salvos por 30 dias,
                economizando até 80% em chamadas de API externa.
              </p>
            </div>

            {config.delivery_mode === 'neighborhood' && (
              <div className="flex items-start gap-2">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-muted-foreground">
                  Modo por bairros é mais simples mas requer cadastro manual. Considere o modo híbrido
                  para ter validação automática em áreas não cadastradas.
                </p>
              </div>
            )}

            {config.delivery_mode === 'radius' && (
              <div className="flex items-start gap-2">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-muted-foreground">
                  Cada validação de endereço usa a API do Google Maps. O cache ajuda, mas considere
                  o modo híbrido para economia ainda maior.
                </p>
              </div>
            )}

            {config.delivery_mode === 'hybrid' && (
              <div className="flex items-start gap-2">
                <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <p className="text-muted-foreground">
                  <strong>Modo recomendado!</strong> Bairros principais são validados instantaneamente,
                  e outros endereços usam GPS automaticamente. Melhor custo-benefício.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
