'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { X } from 'lucide-react';

interface TrialStatus {
  status: 'active' | 'expired' | 'subscribed';
  days_remaining: number | null;
  trial_ends_at: string | null;
  is_blocked: boolean;
  message: string;
}

export function TrialBanner() {
  const [trialStatus, setTrialStatus] = useState<TrialStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrialStatus();
  }, []);

  const fetchTrialStatus = async () => {
    try {
      const response = await api.get('/trial/status');
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Erro ao buscar status do trial:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !trialStatus) {
    return null;
  }

  // Não mostrar se já tem assinatura
  if (trialStatus.status === 'subscribed') {
    return null;
  }

  // Não mostrar se foi dismissed (exceto se expirado)
  if (dismissed && trialStatus.status !== 'expired') {
    return null;
  }

  // Banner vermelho quando expirado
  if (trialStatus.status === 'expired') {
    return (
      <div className="fixed top-0 left-0 right-0 z-50 bg-red-600 text-white">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <div>
                <p className="font-semibold">Trial Expirado!</p>
                <p className="text-sm">
                  Seu período de teste terminou. Assine um plano para continuar usando o GasBot.
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="bg-white text-red-600 hover:bg-gray-100"
              onClick={() => (window.location.href = '/plans')}
            >
              Ver Planos
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Banner amarelo nos últimos 3 dias
  const daysRemaining = trialStatus.days_remaining || 0;
  const isUrgent = daysRemaining <= 3;

  if (!isUrgent && dismissed) {
    return null;
  }

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 ${
        isUrgent ? 'bg-yellow-500' : 'bg-blue-500'
      } text-white`}
    >
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <p className="font-semibold">
                {isUrgent ? '⚠️ Trial Expirando!' : 'Trial Ativo'}
              </p>
              <p className="text-sm">
                {daysRemaining === 1
                  ? 'Último dia do seu trial gratuito!'
                  : `${daysRemaining} dias restantes do seu trial gratuito.`}
                {isUrgent && ' Assine agora para não perder acesso!'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="bg-white text-black hover:bg-gray-100"
              onClick={() => (window.location.href = '/plans')}
            >
              Ver Planos
            </Button>
            {!isUrgent && (
              <button
                onClick={() => setDismissed(true)}
                className="p-1 hover:bg-white/20 rounded"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function TrialStatusCard() {
  const [trialStatus, setTrialStatus] = useState<TrialStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrialStatus();
  }, []);

  const fetchTrialStatus = async () => {
    try {
      const response = await api.get('/trial/status');
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Erro ao buscar status do trial:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !trialStatus) {
    return null;
  }

  // Não mostrar se já tem assinatura
  if (trialStatus.status === 'subscribed') {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            <p className="text-sm font-medium">Assinatura Ativa</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const daysRemaining = trialStatus.days_remaining || 0;
  const isExpired = trialStatus.status === 'expired';
  const isUrgent = daysRemaining <= 3 && !isExpired;

  return (
    <Card
      className={
        isExpired
          ? 'border-red-500 bg-red-50'
          : isUrgent
          ? 'border-yellow-500 bg-yellow-50'
          : 'border-blue-500 bg-blue-50'
      }
    >
      <CardContent className="p-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div
                className={`h-2 w-2 rounded-full ${
                  isExpired ? 'bg-red-500' : isUrgent ? 'bg-yellow-500' : 'bg-blue-500'
                }`}
              />
              <p className="text-sm font-medium">
                {isExpired ? 'Trial Expirado' : 'Trial Ativo'}
              </p>
            </div>
            {!isExpired && (
              <span className="text-2xl font-bold">{daysRemaining} dias</span>
            )}
          </div>

          <p className="text-sm text-muted-foreground">{trialStatus.message}</p>

          <Button
            size="sm"
            className="w-full"
            variant={isExpired ? 'destructive' : 'default'}
            onClick={() => (window.location.href = '/plans')}
          >
            {isExpired ? 'Assinar Agora' : 'Ver Planos'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
