'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AudioMessage } from './AudioMessage';
import { DateRangeFilter } from './DateRangeFilter';
import { api } from '@/lib/api';

interface Message {
  role: string;
  content: string;
  timestamp: string;
  message_type?: string;
  audio_transcription?: string;
  audio_data?: string;
  audio_duration?: number;
}

interface Conversation {
  id: string;
  customer_id: string;
  session_id: string;
  messages: Message[];
  status: string;
  human_intervention: boolean;
  started_at: string;
  ended_at?: string;
}

interface ConversationDetails {
  conversation_id: string;
  customer_id: string;
  messages: Message[];
  context: any;
  human_intervention: boolean;
  started_at: string;
}

export function ChatHistory() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<ConversationDetails | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);
  const [dateFilter, setDateFilter] = useState<{ from: string | null; to: string | null }>({
    from: null,
    to: null,
  });

  const fetchConversations = async () => {
    console.log('[ChatHistory] Buscando conversas...', new Date().toLocaleTimeString());
    try {
      // Construir URL com query parameters
      let url = '/api/v1/dashboard/conversations';
      const params = new URLSearchParams();

      if (filter === 'intervention') {
        params.append('intervention_only', 'true');
      } else if (filter === 'active') {
        params.append('status', 'active');
      }

      if (dateFilter.from) params.append('date_from', dateFilter.from);
      if (dateFilter.to) params.append('date_to', dateFilter.to);

      // Adicionar query string à URL se houver parâmetros
      if (params.toString()) {
        url += '?' + params.toString();
      }

      console.log('[ChatHistory] URL da requisição:', url);
      const data = await api.get<Conversation[]>(url);
      console.log('[ChatHistory] Conversas recebidas:', data.length, data);
      setConversations(data);
    } catch (error) {
      console.error('Erro ao buscar conversas:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConversationDetails = async (conversationId: string) => {
    try {
      const data = await api.get<ConversationDetails>(`/api/v1/dashboard/conversations/${conversationId}/messages`);
      setSelectedConversation(data);
    } catch (error) {
      console.error('Erro ao buscar detalhes da conversa:', error);
    }
  };

  useEffect(() => {
    console.log('[ChatHistory] Iniciando auto-refresh a cada 3 segundos');
    fetchConversations();

    // Atualizar a cada 3 segundos (para desenvolvimento)
    const interval = setInterval(() => {
      console.log('[ChatHistory] Executando refresh automático...');
      fetchConversations();
    }, 3000);

    return () => {
      console.log('[ChatHistory] Limpando interval');
      clearInterval(interval);
    };
  }, [filter, dateFilter]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const handleDateFilterChange = (from: string | null, to: string | null) => {
    setDateFilter({ from, to });
  };

  return (
    <div className="grid md:grid-cols-3 gap-4">
      {/* Lista de Conversas */}
      <div className="md:col-span-1 space-y-4">
        {/* Filtro de Data */}
        <DateRangeFilter onFilterChange={handleDateFilterChange} />

        {/* Filtros de Status */}
        <div className="flex flex-col gap-2">
          <Button
            variant={filter === null ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(null)}
          >
            Todas
          </Button>
          <Button
            variant={filter === 'active' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('active')}
          >
            Ativas
          </Button>
          <Button
            variant={filter === 'intervention' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('intervention')}
          >
            Com Intervenção
          </Button>
        </div>

        {/* Lista */}
        <div className="space-y-2">
          {conversations.length === 0 ? (
            <Card>
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground text-center">
                  Nenhuma conversa encontrada
                </p>
              </CardContent>
            </Card>
          ) : (
            conversations.map((conv) => (
              <Card
                key={conv.id}
                className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                  selectedConversation?.conversation_id === conv.id ? 'border-primary' : ''
                }`}
                onClick={() => fetchConversationDetails(conv.id)}
              >
                <CardHeader className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardDescription className="text-xs">
                        {new Date(conv.started_at).toLocaleString('pt-BR')}
                      </CardDescription>
                      <p className="text-sm font-medium mt-1">
                        {conv.messages.length} mensagens
                      </p>
                    </div>
                    <div className="flex flex-col gap-1">
                      <Badge
                        variant={conv.status === 'active' ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {conv.status === 'active' ? 'Ativa' : 'Encerrada'}
                      </Badge>
                      {conv.human_intervention && (
                        <Badge variant="destructive" className="text-xs">
                          Intervenção
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
              </Card>
            ))
          )}
        </div>
      </div>

      {/* Detalhes da Conversa */}
      <div className="md:col-span-2">
        {selectedConversation ? (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Conversa</CardTitle>
                  <CardDescription>
                    Iniciada em{' '}
                    {new Date(selectedConversation.started_at).toLocaleString('pt-BR')}
                  </CardDescription>
                </div>
                {selectedConversation.human_intervention && (
                  <Badge variant="destructive">Intervenção Ativa</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4 max-h-[600px] overflow-y-auto">
              {selectedConversation.messages.map((message, index) => (
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
                        : 'bg-muted'
                    } rounded-lg p-3 space-y-2`}
                  >
                    {/* Áudio */}
                    {message.message_type === 'audio' ? (
                      <AudioMessage
                        audioData={message.audio_data}
                        transcription={message.audio_transcription}
                        duration={message.audio_duration}
                      />
                    ) : (
                      /* Texto */
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}

                    {/* Timestamp */}
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
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="flex items-center justify-center p-12">
              <p className="text-muted-foreground">
                Selecione uma conversa para ver os detalhes
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
