'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import AgentDetailPanel from '@/components/agents/AgentDetailPanel';
import TimeControls from '@/components/simulation/TimeControls';
import SimulationStats from '@/components/simulation/SimulationStats';
import TechTreePanel from '@/components/technology/TechTreePanel';
import ViewModeSelector from '@/components/ui/ViewModeSelector';
import MiniMap from '@/components/ui/MiniMap';
import NotificationSystem, { useNotifications } from '@/components/ui/NotificationSystem';
import FilterControlsPanel from '@/components/ui/FilterControlsPanel';
import type { Building } from '@/types/structures';
import type { AgentKnowledge } from '@/types/technology';
import type { ViewMode, ViewSettings } from '@/types/view-modes';
import { getViewSettings } from '@/types/view-modes';

// Load WorldCanvasSimple (HTML/CSS based - no WebGL issues)
const WorldCanvas = dynamic(() => import('@/components/world/WorldCanvasSimple'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-accent text-lg">Loading World Canvas...</div>
    </div>
  ),
});

// Mock data for now - will be replaced with WebSocket data
const mockAgents = [
  {
    id: '1',
    name: 'Alice',
    position: { x: 30, y: 40 },
    wealth: 100,
    health: 85,
    age: 25,
    alive: true,
  },
  {
    id: '2',
    name: 'Bob',
    position: { x: 45, y: 50 },
    wealth: 150,
    health: 95,
    age: 30,
    alive: true,
  },
  {
    id: '3',
    name: 'Charlie',
    position: { x: 60, y: 35 },
    wealth: 75,
    health: 65,
    age: 40,
    alive: true,
  },
  {
    id: '4',
    name: 'Diana',
    position: { x: 25, y: 55 },
    wealth: 200,
    health: 90,
    age: 28,
    alive: true,
  },
  {
    id: '5',
    name: 'Eve',
    position: { x: 70, y: 45 },
    wealth: 50,
    health: 45,
    age: 35,
    alive: true,
  },
];

// Mock buildings - Demonstrating construction progression
const mockBuildings: Building[] = [
  // Completed buildings
  {
    id: 'b1',
    type: 'campfire',
    position: { x: 35, y: 42 },
    ownerId: '1',
    stage: 'completed',
    progress: 100,
    health: 100,
    built: 0,
    completed: 50,
  },
  {
    id: 'b2',
    type: 'shelter',
    position: { x: 48, y: 52 },
    ownerId: '2',
    stage: 'completed',
    progress: 100,
    health: 100,
    built: 100,
    completed: 300,
  },
  {
    id: 'b3',
    type: 'workshop',
    position: { x: 63, y: 38 },
    ownerId: '3',
    stage: 'completed',
    progress: 100,
    health: 95,
    built: 200,
    completed: 600,
  },

  // Buildings under construction - Different stages
  {
    id: 'b4',
    type: 'farm',
    position: { x: 28, y: 58 },
    ownerId: '4',
    stage: 'finishing',
    progress: 85,
    health: 100,
    built: 700,
  },
  {
    id: 'b5',
    type: 'house',
    position: { x: 73, y: 48 },
    ownerId: '5',
    stage: 'framing',
    progress: 55,
    health: 100,
    built: 750,
  },
  {
    id: 'b6',
    type: 'storage',
    position: { x: 40, y: 32 },
    ownerId: '1',
    stage: 'foundation',
    progress: 25,
    health: 100,
    built: 800,
  },
  {
    id: 'b7',
    type: 'tent',
    position: { x: 55, y: 60 },
    ownerId: '2',
    stage: 'planning',
    progress: 8,
    health: 100,
    built: 850,
  },
];

export default function SimulationPage() {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<1 | 2 | 4 | 8>(1);
  const [showTechTree, setShowTechTree] = useState(false);
  const [agentKnowledge, setAgentKnowledge] = useState<AgentKnowledge[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('normal');
  const [currentView, setCurrentView] = useState({ x: 50, y: 50, zoom: 1 });
  const [viewSettings, setViewSettings] = useState<ViewSettings>(getViewSettings('normal'));
  const [filterPanelExpanded, setFilterPanelExpanded] = useState(false);

  const { notifications, addNotification, dismissNotification } = useNotifications();

  // Update view settings when view mode changes
  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    setViewSettings(getViewSettings(mode));
  };

  // Update individual view settings
  const handleSettingsChange = (partialSettings: Partial<ViewSettings>) => {
    setViewSettings((prev) => ({ ...prev, ...partialSettings }));
  };

  const selectedAgent = mockAgents.find((a) => a.id === selectedAgentId) || null;
  const selectedAgentKnowledge = agentKnowledge.find((k) => k.agentId === selectedAgentId) || null;

  return (
    <div className="h-screen w-screen flex flex-col bg-background overflow-hidden">
      {/* Top Bar - Stats with better spacing */}
      <div className="flex-shrink-0 px-6 py-4 flex items-center justify-between border-b border-border/50 backdrop-blur-sm bg-background/80">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-accent-light to-purple-400 bg-clip-text text-transparent tracking-tight">
            Neuronaut World
          </h1>

          {/* View Mode Selector */}
          <ViewModeSelector currentMode={viewMode} onModeChange={handleViewModeChange} />

          {/* Tech Tree Button */}
          <button
            onClick={() => {
              // Select first agent if none selected
              if (!selectedAgentId && mockAgents.length > 0) {
                setSelectedAgentId(mockAgents[0].id);
              }
              setShowTechTree(!showTechTree);
            }}
            className="px-4 py-2 rounded-lg font-semibold text-sm transition-all hover:scale-105"
            style={{
              background: showTechTree
                ? 'linear-gradient(135deg, rgba(34, 211, 238, 0.3) 0%, rgba(6, 182, 212, 0.3) 100%)'
                : 'linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%)',
              border: '1px solid rgba(34, 211, 238, 0.5)',
              color: '#22d3ee',
            }}
          >
            🔬 Tech Tree
          </button>
        </div>

        <SimulationStats
          population={mockAgents.length}
          alive={mockAgents.filter((a) => a.alive).length}
          currentTick={1234}
          currentEra="Stone Age"
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex gap-0 min-h-0">
        {/* World Canvas - Center */}
        <div className="flex-1 relative overflow-hidden">
          <WorldCanvas
            width={1200}
            height={800}
            worldWidth={100}
            worldHeight={100}
            agents={mockAgents}
            buildings={mockBuildings}
            viewMode={viewMode}
            viewSettings={viewSettings}
            selectedAgentId={selectedAgentId}
            onAgentClick={(agent) => setSelectedAgentId(agent.id)}
            onBuildingClick={(building) => {
              console.log('Building clicked:', building);
              // TODO: Add building detail panel similar to agent panel
            }}
            onAgentKnowledgeUpdate={(knowledge) => setAgentKnowledge(knowledge)}
            onViewChange={(view) => setCurrentView(view)}
          />

          {/* Mini-Map Overlay */}
          <MiniMap
            agents={mockAgents}
            buildings={mockBuildings}
            worldWidth={100}
            worldHeight={100}
            currentView={currentView}
            onLocationClick={(x, y) => {
              console.log(`Jump to location: ${x}, ${y}`);
              // TODO: Implement camera pan to location
            }}
          />

          {/* Notification System */}
          <NotificationSystem
            notifications={notifications}
            onNotificationClick={(notification) => {
              console.log('Notification clicked:', notification);
              if (notification.location) {
                console.log(`Jump to: ${notification.location.x}, ${notification.location.y}`);
              }
            }}
            onDismiss={dismissNotification}
          />

          {/* Filter Controls Panel */}
          <FilterControlsPanel
            settings={viewSettings}
            onSettingsChange={handleSettingsChange}
            isExpanded={filterPanelExpanded}
            onToggleExpanded={() => setFilterPanelExpanded(!filterPanelExpanded)}
          />
        </div>

        {/* Right Panel - Agent Detail or Tech Tree */}
        <div
          className={`transition-all duration-300 ease-out border-l border-border/50 ${
            (selectedAgent && !showTechTree) || (showTechTree && selectedAgentKnowledge) ? 'w-96' : 'w-0'
          }`}
          style={{ flexShrink: 0 }}
        >
          {showTechTree && selectedAgentKnowledge ? (
            <TechTreePanel
              agentKnowledge={selectedAgentKnowledge}
              onClose={() => setShowTechTree(false)}
              onResearchTech={(techId) => {
                console.log(`Start researching ${techId}`);
                // TODO: Trigger research in simulator
              }}
            />
          ) : selectedAgent ? (
            <AgentDetailPanel
              agent={selectedAgent}
              onClose={() => setSelectedAgentId(null)}
            />
          ) : null}
        </div>
      </div>

      {/* Bottom Bar - Time Controls with better styling */}
      <div className="flex-shrink-0 px-6 py-3 border-t border-border/50 backdrop-blur-sm bg-background/80">
        <TimeControls
          isPaused={isPaused}
          playbackSpeed={playbackSpeed}
          onPlayPause={() => setIsPaused(!isPaused)}
          onSpeedChange={setPlaybackSpeed}
        />
      </div>
    </div>
  );
}
