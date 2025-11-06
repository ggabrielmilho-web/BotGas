'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { NeighborhoodManager } from './NeighborhoodManager';
import { RadiusManager } from './RadiusManager';

export function HybridManager() {
  return (
    <div className="space-y-6">
      {/* Info sobre modo híbrido */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg
            className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <div>
            <h4 className="font-medium text-yellow-900 mb-1">Modo Híbrido Ativo</h4>
            <p className="text-sm text-yellow-800">
              Este modo combina validação por bairros (rápido, sem custo de API) com validação por raio
              (preciso, usa Google Maps). Quando um cliente informa um endereço:
            </p>
            <ol className="text-sm text-yellow-800 mt-2 ml-4 space-y-1 list-decimal">
              <li>Primeiro verifica se o bairro está cadastrado (economia de API)</li>
              <li>Se não encontrar, calcula distância por GPS (Google Maps)</li>
              <li>Resultado: Economia de até 80% em chamadas de API!</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Tabs para gerenciar bairros e raio */}
      <Tabs defaultValue="neighborhoods" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="neighborhoods">
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            Bairros Principais
          </TabsTrigger>
          <TabsTrigger value="radius">
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              />
            </svg>
            Faixas de Raio (Fallback)
          </TabsTrigger>
        </TabsList>

        <TabsContent value="neighborhoods" className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-sm text-blue-800">
              <strong>Bairros principais:</strong> Configure os bairros mais comuns onde você entrega.
              Quando um cliente informar um desses bairros, a validação será instantânea (sem usar API do Google Maps).
            </p>
          </div>
          <NeighborhoodManager />
        </TabsContent>

        <TabsContent value="radius" className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-md p-3">
            <p className="text-sm text-green-800">
              <strong>Faixas de raio (fallback):</strong> Configure faixas de distância para endereços fora
              dos bairros cadastrados. A distância será calculada automaticamente usando Google Maps.
            </p>
          </div>
          <RadiusManager />
        </TabsContent>
      </Tabs>

      {/* Dicas de Uso */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">💡 Dicas para otimizar o modo híbrido:</h4>
        <ul className="text-sm text-gray-700 space-y-1 ml-4 list-disc">
          <li>Cadastre os bairros onde você mais recebe pedidos para economizar API</li>
          <li>Configure faixas de raio amplas para cobrir áreas não cadastradas</li>
          <li>Revise periodicamente os bairros mais solicitados e adicione à lista</li>
          <li>Use o cache de endereços para evitar validações repetidas</li>
        </ul>
      </div>
    </div>
  );
}
