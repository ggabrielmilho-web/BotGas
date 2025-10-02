'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { AudioMessage } from './AudioMessage';
import { api } from '@/lib/api';

interface ActiveIntervention {
  intervention_id: string;
  conversation_id: string;
  customer_name: string;
  customer_phone: string;
  started_at: string;
  reason: string;
  messages_count: number;
}

interface ConversationMessage {
  role: string;
  content: string;
  timestamp: string;
  message_type?: string;
  audio_transcription?: string;
  audio_data?: string;
}

interface ConversationDetails {
  conversation_id: string;
  customer_id: string;
  messages: ConversationMessage[];
  context: any;
  human_intervention: boolean;
  started_at: string;
}

export function InterventionPanel() {
  const [interventions, setInterventions] = useState<ActiveIntervention[]>([]);
  const [selectedIntervention, setSelectedIntervention] = useState<ActiveIntervention | null>(
    null
  );
  const [conversationDetails, setConversationDetails] = useState<ConversationDetails | null>(
    null
  );
  const [messageText, setMessageText] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchInterventions = async () => {
    try {
      const response = await api.get('/dashboard/interventions');
      setInterventions(response.data);
    } catch (error) {
      console.error('Erro ao buscar intervenções:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConversationDetails = async (conversationId: string) => {
    try {
      const response = await api.get(`/dashboard/conversations/${conversationId}/messages`);
      setConversationDetails(response.data);
    } catch (error) {
      console.error('Erro ao buscar detalhes:', error);
    }
  };

  const startIntervention = async (conversationId: string, reason?: string) => {
    try {
      await api.post(`/conversations/${conversationId}/intervene`, { reason });
      fetchInterventions();
    } catch (error) {
      console.error('Erro ao iniciar intervenção:', error);
    }
  };

  const resumeBot = async (conversationId: string, notes?: string) => {
    try {
      await api.post(`/conversations/${conversationId}/resume`, { operator_notes: notes });
      setSelectedIntervention(null);
      setConversationDetails(null);
      fetchInterventions();
    } catch (error) {
      console.error('Erro ao retomar bot:', error);
    }
  };

  const sendManualMessage = async () => {
    if (!messageText.trim() || !selectedIntervention) return;

    setSending(true);
    try {
      await api.post(`/conversations/${selectedIntervention.conversation_id}/send`, {
        message: messageText,
      });

      // Atualizar detalhes da conversa
      await fetchConversationDetails(selectedIntervention.conversation_id);

      setMessageText('');
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    fetchInterventions();

    // Atualizar a cada 5 segundos
    const interval = setInterval(fetchInterventions, 5000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedIntervention) {
      fetchConversationDetails(selectedIntervention.conversation_id);

      // Atualizar mensagens a cada 3 segundos durante intervenção
      const interval = setInterval(() => {
        fetchConversationDetails(selectedIntervention.conversation_id);
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [selectedIntervention]);

  // Auto-scroll para última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationDetails?.messages]);

  const calculateTimeRemaining = (startedAt: string) => {
    const started = new Date(startedAt);
    const now = new Date();
    const elapsed = (now.getTime() - started.getTime()) / 1000 / 60; // minutos
    const remaining = Math.max(0, 5 - elapsed);
    return Math.ceil(remaining);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-3 gap-4">
      {/* Lista de Intervenções Ativas */}
      <div className="md:col-span-1 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Intervenções Ativas</CardTitle>
            <CardDescription>
              {interventions.length} conversa{interventions.length !== 1 ? 's' : ''} com
              intervenção humana
            </CardDescription>
          </CardHeader>
        </Card>

        {interventions.length === 0 ? (
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground text-center">
                Nenhuma intervenção ativa no momento
              </p>
            </CardContent>
          </Card>
        ) : (
          interventions.map((intervention) => (
            <Card
              key={intervention.intervention_id}
              className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                selectedIntervention?.intervention_id === intervention.intervention_id
                  ? 'border-primary'
                  : ''
              }`}
              onClick={() => setSelectedIntervention(intervention)}
            >
              <CardHeader className="p-4">
                <div className="space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-sm">
                        {intervention.customer_name || 'Cliente'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {intervention.customer_phone}
                      </p>
                    </div>
                    <Badge variant="destructive" className="text-xs">
                      {calculateTimeRemaining(intervention.started_at)} min
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground">{intervention.reason}</p>

                  <p className="text-xs">
                    {intervention.messages_count} mensagem
                    {intervention.messages_count !== 1 ? 's' : ''}
                  </p>
                </div>
              </CardHeader>
            </Card>
          ))
        )}
      </div>

      {/* Painel de Intervenção */}
      <div className="md:col-span-2">
        {selectedIntervention && conversationDetails ? (
          <Card className="h-[700px] flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>
                    Conversando com {selectedIntervention.customer_name || 'Cliente'}
                  </CardTitle>
                  <CardDescription>{selectedIntervention.customer_phone}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Badge variant="destructive">
                    {calculateTimeRemaining(selectedIntervention.started_at)} min restantes
                  </Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      resumeBot(selectedIntervention.conversation_id, 'Intervenção finalizada')
                    }
                  >
                    Retomar Bot
                  </Button>
                </div>
              </div>
            </CardHeader>

            {/* Mensagens */}
            <CardContent className="flex-1 overflow-y-auto space-y-4 pb-4">
              {conversationDetails.messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : message.role === 'system'
                        ? 'bg-yellow-100 text-yellow-900'
                        : 'bg-muted'
                    } rounded-lg p-3 space-y-2`}
                  >
                    {message.message_type === 'audio' ? (
                      <AudioMessage
                        audioData={message.audio_data}
                        transcription={message.audio_transcription}
                      />
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}

                    <p
                      className={`text-xs ${
                        message.role === 'user'
                          ? 'text-primary-foreground/70'
                          : 'text-muted-foreground'
                      }`}
                    >
                      {new Date(message.timestamp).toLocaleTimeString('pt-BR')}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </CardContent>

            {/* Input de Mensagem */}
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Digite sua mensagem..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendManualMessage();
                    }
                  }}
                  disabled={sending}
                />
                <Button onClick={sendManualMessage} disabled={sending || !messageText.trim()}>
                  {sending ? 'Enviando...' : 'Enviar'}
                </Button>
              </div>
            </div>
          </Card>
        ) : (
          <Card>
            <CardContent className="flex items-center justify-center p-12">
              <p className="text-muted-foreground">
                Selecione uma intervenção para começar a conversar
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
