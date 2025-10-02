/**
 * Hook para gerenciar conexão WebSocket do dashboard
 * Recebe atualizações em tempo real de novos pedidos, mensagens, etc.
 */
import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface UseWebSocketOptions {
  tenantId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
}

export function useWebSocket({
  tenantId,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectInterval = 5000,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    try {
      // URL do WebSocket - usar wss:// em produção
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/api/v1/conversations/ws/${tenantId}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket conectado');
        setIsConnected(true);
        onConnect?.();

        // Enviar ping a cada 30 segundos para manter conexão
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);

        // Limpar interval ao fechar
        ws.addEventListener('close', () => {
          clearInterval(pingInterval);
        });
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Erro ao parsear mensagem WebSocket:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('Erro no WebSocket:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('WebSocket desconectado');
        setIsConnected(false);
        onDisconnect?.();

        // Tentar reconectar
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Tentando reconectar...');
          connect();
        }, reconnectInterval);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Erro ao criar WebSocket:', error);
    }
  }, [tenantId, onMessage, onConnect, onDisconnect, onError, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}
