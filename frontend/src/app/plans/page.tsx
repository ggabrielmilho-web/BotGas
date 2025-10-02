'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { Check } from 'lucide-react';

interface Plan {
  id: string;
  name: string;
  price: number;
  features: string[];
  popular?: boolean;
}

interface TrialStatus {
  status: string;
  days_remaining: number | null;
  is_blocked: boolean;
}

export default function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [trialStatus, setTrialStatus] = useState<TrialStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [plansResponse, trialResponse] = await Promise.all([
        api.get('/trial/plans'),
        api.get('/trial/status'),
      ]);

      setPlans(plansResponse.data.plans);
      setTrialStatus(trialResponse.data);
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleActivatePlan = async (planId: string) => {
    setActivating(planId);

    try {
      await api.post('/trial/activate', { plan: planId });

      alert('Plano ativado com sucesso! 🎉');
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Erro ao ativar plano:', error);
      alert('Erro ao ativar plano. Tente novamente.');
    } finally {
      setActivating(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold">Escolha seu Plano</h1>
        <p className="text-xl text-muted-foreground">
          Automatize seu atendimento e aumente suas vendas
        </p>
        {trialStatus && trialStatus.status === 'active' && (
          <p className="text-sm text-muted-foreground">
            Você tem {trialStatus.days_remaining} dias restantes de trial
          </p>
        )}
      </div>

      {/* Trial Banner */}
      {trialStatus?.is_blocked && (
        <Card className="border-red-500 bg-red-50">
          <CardContent className="p-4">
            <p className="text-center font-semibold text-red-700">
              ⚠️ Seu trial expirou. Escolha um plano para continuar usando o GasBot.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Planos */}
      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        {plans.map((plan) => (
          <Card
            key={plan.id}
            className={`relative ${
              plan.popular ? 'border-primary shadow-lg scale-105' : ''
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <Badge className="bg-primary text-white px-4 py-1">Mais Popular</Badge>
              </div>
            )}

            <CardHeader className="text-center pb-4">
              <CardTitle className="text-2xl">{plan.name}</CardTitle>
              <div className="mt-4">
                <span className="text-4xl font-bold">R$ {plan.price.toFixed(2)}</span>
                <span className="text-muted-foreground">/mês</span>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Features */}
              <ul className="space-y-3">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Button
                className="w-full"
                size="lg"
                variant={plan.popular ? 'default' : 'outline'}
                onClick={() => handleActivatePlan(plan.id)}
                disabled={activating !== null}
              >
                {activating === plan.id ? 'Ativando...' : 'Escolher Plano'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Garantia */}
      <Card className="max-w-2xl mx-auto bg-muted">
        <CardContent className="p-6 text-center space-y-2">
          <h3 className="font-semibold text-lg">🔒 Garantia de 7 dias</h3>
          <p className="text-sm text-muted-foreground">
            Não gostou? Devolvemos seu dinheiro sem perguntas.
          </p>
        </CardContent>
      </Card>

      {/* FAQ */}
      <div className="max-w-2xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold text-center">Perguntas Frequentes</h2>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Posso cancelar quando quiser?</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Sim! Você pode cancelar sua assinatura a qualquer momento, sem multas ou taxas.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Como funciona o pagamento?</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              O pagamento é mensal via PIX ou cartão de crédito. Você receberá uma fatura todo
              mês.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Posso mudar de plano depois?</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Sim! Você pode fazer upgrade ou downgrade a qualquer momento. A diferença será
              cobrada ou creditada proporcionalmente.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
