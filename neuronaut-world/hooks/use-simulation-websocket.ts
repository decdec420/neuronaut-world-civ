'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

export interface SimulationUpdate {
  type: 'state_update' | 'event' | 'agent_update';
  data: any;
  tick: number;
}

interface UseSimulationWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  onMessage?: (update: SimulationUpdate) => void;
  onError?: (error: Event) => void;
  reconnectDelay?: number;
}

export function useSimulationWebSocket({
  url = 'ws://localhost:8000/ws',
  autoConnect = true,
  onMessage,
  onError,
  reconnectDelay = 3000,
}: UseSimulationWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<SimulationUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    try {
      console.log('[WebSocket] Connecting to:', url);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const update: SimulationUpdate = JSON.parse(event.data);
          setLastUpdate(update);
          if (onMessage) onMessage(update);
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        setError('WebSocket connection error');
        if (onError) onError(event);
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Auto-reconnect if enabled
        if (shouldReconnectRef.current && autoConnect) {
          console.log(`[WebSocket] Reconnecting in ${reconnectDelay}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[WebSocket] Connection failed:', err);
      setError('Failed to connect to simulation server');
    }
  }, [url, autoConnect, onMessage, onError, reconnectDelay]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('[WebSocket] Cannot send - not connected');
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoConnect, connect]);

  return {
    isConnected,
    lastUpdate,
    error,
    connect,
    disconnect,
    send,
  };
}
