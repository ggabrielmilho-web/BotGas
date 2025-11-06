'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { api } from '@/lib/api';

type DeliveryMode = 'neighborhood' | 'radius' | 'hybrid';

interface DeliveryModeSelectorProps {
  currentMode: DeliveryMode;
  onModeChanged: () => void;
}

export function DeliveryModeSelector({ currentMode, onModeChanged }: DeliveryModeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedMode, setSelectedMode] = useState<DeliveryMode | null>(null);
  const [loading, setLoading] = useState(false);

  const modes = [
    {
      id: 'neighborhood' as DeliveryMode,
      name: 'Por Bairros',
      description: 'Configure manualmente os bairros que você atende',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      color: 'blue',
      features: ['Simples de configurar', 'Sem custos de API', 'Taxa por bairro'],
    },
    {
      id: 'radius' as DeliveryMode,
      name: 'Por Raio/KM',
      description: 'Entrega automática baseada em distância',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      ),
      color: 'green',
      features: ['Cobertura total', 'GPS preciso', 'Usa Google Maps'],
    },
    {
      id: 'hybrid' as DeliveryMode,
      name: 'Híbrido',
      description: 'Combina bairros + raio (recomendado)',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'yellow',
      features: ['Melhor dos 2 mundos', 'Economia de API', 'Máxima cobertura'],
      recommended: true,
    },
  ];

  const handleConfirmChange = async () => {
    if (!selectedMode || selectedMode === currentMode) return;

    setLoading(true);
    try {
      await api.delivery.updateMode(selectedMode);
      setIsOpen(false);
      onModeChanged();
    } catch (error) {
      console.error('Erro ao trocar modo:', error);
      alert('Erro ao trocar modo de entrega');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button variant="outline" onClick={() => setIsOpen(true)}>
        Trocar Modo de Entrega
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Trocar Modo de Entrega</DialogTitle>
            <DialogDescription>
              Escolha o modo de entrega que melhor se adequa ao seu negócio.
              Esta mudança afetará como os endereços são validados.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Aviso */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <div className="flex">
                <svg className="h-5 w-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-yellow-800">Atenção</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    Ao trocar o modo, você precisará configurar as novas regras de entrega.
                    Suas configurações anteriores serão mantidas caso queira voltar ao modo anterior.
                  </p>
                </div>
              </div>
            </div>

            {/* Modo Atual */}
            <div className="text-sm text-muted-foreground">
              Modo atual: <span className="font-semibold">{modes.find(m => m.id === currentMode)?.name}</span>
            </div>

            {/* Grid de Modos */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {modes.map((mode) => (
                <Card
                  key={mode.id}
                  className={`cursor-pointer transition-all ${
                    selectedMode === mode.id
                      ? 'border-2 border-primary shadow-md'
                      : 'hover:border-gray-400'
                  } ${
                    mode.id === currentMode
                      ? 'bg-gray-50 opacity-60'
                      : ''
                  } ${
                    mode.recommended
                      ? 'border-2 border-yellow-400'
                      : ''
                  }`}
                  onClick={() => {
                    if (mode.id !== currentMode) {
                      setSelectedMode(mode.id);
                    }
                  }}
                >
                  <CardContent className="p-6">
                    <div className="text-center">
                      <div className={`w-12 h-12 bg-${mode.color}-100 rounded-full flex items-center justify-center mx-auto mb-3 text-${mode.color}-600`}>
                        {mode.icon}
                      </div>
                      <h3 className="font-semibold text-lg mb-2">
                        {mode.name}
                        {mode.id === currentMode && (
                          <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                            Atual
                          </span>
                        )}
                      </h3>
                      <p className="text-sm text-gray-600 mb-3">{mode.description}</p>
                      <ul className="text-xs text-gray-500 text-left space-y-1">
                        {mode.features.map((feature, index) => (
                          <li key={index}>✓ {feature}</li>
                        ))}
                      </ul>
                      {mode.recommended && (
                        <span className="inline-block mt-3 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                          Recomendado
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleConfirmChange}
              disabled={!selectedMode || selectedMode === currentMode || loading}
            >
              {loading ? 'Alterando...' : 'Confirmar Mudança'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
