'use client';

import { useState, useEffect } from 'react';
import { useSimulationWebSocket, SimulationUpdate } from './use-simulation-websocket';

export interface Agent {
  id: string;
  name: string;
  position: { x: number; y: number };
  wealth: number;
  health: number;
  age: number;
  alive: boolean;
}

export interface SimulationState {
  agents: Agent[];
  tick: number;
  era: string;
  population: number;
  alive: number;
}

export function useSimulationData() {
  const [state, setState] = useState<SimulationState>({
    agents: [],
    tick: 0,
    era: 'Stone Age',
    population: 0,
    alive: 0,
  });

  const handleMessage = (update: SimulationUpdate) => {
    // Handle standardized message format from backend
    if (update.type === 'simulation_update') {
      setState((prev) => ({
        ...prev,
        ...update.data,
        tick: update.tick,
      }));
    } else if (update.type === 'state_update') {
      setState((prev) => ({
        ...prev,
        ...update.data,
        tick: update.tick,
      }));
    } else if (update.type === 'agent_update') {
      setState((prev) => {
        const updatedAgents = [...prev.agents];
        const index = updatedAgents.findIndex((a) => a.id === update.data.id);
        if (index >= 0) {
          updatedAgents[index] = { ...updatedAgents[index], ...update.data };
        } else {
          updatedAgents.push(update.data);
        }
        return {
          ...prev,
          agents: updatedAgents,
          tick: update.tick,
        };
      });
    }
  };

  const { isConnected, error, connect, disconnect, send } = useSimulationWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    autoConnect: true,
    onMessage: handleMessage,
  });

  // Fetch initial state on mount
  useEffect(() => {
    const fetchInitialState = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/world`);
        if (response.ok) {
          const data = await response.json();
          setState(data);
        }
      } catch (err) {
        console.error('Failed to fetch initial state:', err);
      }
    };

    fetchInitialState();
  }, []);

  return {
    state,
    isConnected,
    error,
    connect,
    disconnect,
    sendCommand: send,
  };
}
