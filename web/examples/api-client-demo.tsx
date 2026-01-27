'use client';

/**
 * API Client Demo Component
 *
 * Demonstrates usage of all 45 API endpoints through React Query hooks.
 * This is a reference implementation showing best practices.
 */

import { useState } from 'react';
import {
  // Core World State
  useServerStatus,
  useWorld,
  useStats,
  useAgents,
  useAgent,
  // Agent Details
  useAgentProfile,
  useAgentInventory,
  useAgentFunStats,
  // Events & Stories
  useEvents,
  useStories,
  useAchievements,
  // Buildings & Structures
  useBuildings,
  // Science & Discovery
  useExperiments,
  useInnovations,
  // Society & Governance
  useConflicts,
  useGovernments,
  // Knowledge & Education
  useKnowledge,
  useLibraries,
  useTeachingSessions,
  // Emergent Roles
  useRoles,
  // Economy & Resources
  useEconomy,
  useMaterials,
  useRecipes,
  // Fun & Culture
  useFunStats,
  useCelebrations,
  useGames,
  useArt,
  // Consequences
  useConsequences,
  // Simulation Control
  useSimulationStatus,
  useSaves,
  // Mutations
  useCreateCharacter,
  usePauseSimulation,
  useSetSimulationSpeed,
  useTriggerDisaster,
  useCreateSave,
  useLoadSave,
  useDeleteSave,
  useResetWorld,
} from '@/hooks/use-api-client';

export function ApiClientDemo() {
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [selectedTab, setSelectedTab] = useState<string>('overview');

  // Core World State Hooks
  const { data: serverStatus } = useServerStatus();
  const { data: world } = useWorld();
  const { data: stats } = useStats();
  const { data: agents } = useAgents();
  const { data: agent } = useAgent(selectedAgentId);

  // Agent Details Hooks
  const { data: agentProfile } = useAgentProfile(selectedAgentId);
  const { data: agentInventory } = useAgentInventory(selectedAgentId);
  const { data: agentFunStats } = useAgentFunStats(selectedAgentId);

  // Events & Stories Hooks
  const { data: events } = useEvents(20, 2);
  const { data: stories } = useStories();
  const { data: achievements } = useAchievements();

  // Buildings & Structures Hooks
  const { data: buildings } = useBuildings();

  // Science & Discovery Hooks
  const { data: experiments } = useExperiments();
  const { data: innovations } = useInnovations();

  // Society & Governance Hooks
  const { data: conflicts } = useConflicts();
  const { data: governments } = useGovernments();

  // Knowledge & Education Hooks
  const { data: knowledge } = useKnowledge();
  const { data: libraries } = useLibraries();
  const { data: teachingSessions } = useTeachingSessions();

  // Emergent Roles Hooks
  const { data: roles } = useRoles();

  // Economy & Resources Hooks
  const { data: economy } = useEconomy();
  const { data: materials } = useMaterials();
  const { data: recipes } = useRecipes();

  // Fun & Culture Hooks
  const { data: funStats } = useFunStats();
  const { data: celebrations } = useCelebrations();
  const { data: games } = useGames();
  const { data: art } = useArt();

  // Consequences Hooks
  const { data: consequences } = useConsequences();

  // Simulation Control Hooks
  const { data: simulationStatus } = useSimulationStatus();
  const { data: saves } = useSaves();

  // Mutation Hooks
  const createCharacter = useCreateCharacter({
    onSuccess: (data) => {
      alert(`Character created: ${data.agent.name}`);
    },
  });

  const pauseSimulation = usePauseSimulation({
    onSuccess: (data) => {
      alert(data.message);
    },
  });

  const setSpeed = useSetSimulationSpeed({
    onSuccess: (data) => {
      alert(`Speed set to: ${data.speed}`);
    },
  });

  const triggerDisaster = useTriggerDisaster({
    onSuccess: (data) => {
      alert(data.message);
    },
  });

  const createSave = useCreateSave({
    onSuccess: (data) => {
      alert(data.message);
    },
  });

  const loadSave = useLoadSave({
    onSuccess: (data) => {
      alert(data.message);
    },
  });

  const deleteSave = useDeleteSave({
    onSuccess: (data) => {
      alert(data.message);
    },
  });

  const resetWorld = useResetWorld({
    onSuccess: (data) => {
      if (confirm('Reset world? This cannot be undone!')) {
        alert(data.message);
      }
    },
  });

  const tabs = [
    { id: 'overview', name: 'Overview' },
    { id: 'agents', name: 'Agents' },
    { id: 'buildings', name: 'Buildings' },
    { id: 'science', name: 'Science' },
    { id: 'society', name: 'Society' },
    { id: 'knowledge', name: 'Knowledge' },
    { id: 'economy', name: 'Economy' },
    { id: 'culture', name: 'Culture' },
    { id: 'controls', name: 'Controls' },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">API Client Demo</h1>
        <p className="text-gray-600">
          Demonstrating all 45 endpoints with React Query hooks
        </p>
      </div>

      {/* Server Status */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h2 className="text-xl font-semibold mb-2">Server Status</h2>
        <div className="grid grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Name</p>
            <p className="font-semibold">{serverStatus?.name}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className="font-semibold">{serverStatus?.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Agents</p>
            <p className="font-semibold">{serverStatus?.agents}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Version</p>
            <p className="font-semibold">{serverStatus?.version}</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {selectedTab === 'overview' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">World Overview</h2>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Day</p>
                <p className="text-2xl font-bold">{world?.time.day}</p>
                <p className="text-xs text-gray-500">{world?.time.season}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Population</p>
                <p className="text-2xl font-bold">{world?.population}</p>
                <p className="text-xs text-gray-500">{world?.alive} alive</p>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Era</p>
                <p className="text-2xl font-bold">{world?.era}</p>
              </div>
            </div>

            {/* Statistics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 border rounded">
                <p className="text-sm text-gray-600">Buildings</p>
                <p className="text-xl font-bold">{buildings?.total || 0}</p>
              </div>
              <div className="p-4 border rounded">
                <p className="text-sm text-gray-600">Discoveries</p>
                <p className="text-xl font-bold">{experiments?.total_discoveries || 0}</p>
              </div>
              <div className="p-4 border rounded">
                <p className="text-sm text-gray-600">Innovations</p>
                <p className="text-xl font-bold">{innovations?.total || 0}</p>
              </div>
              <div className="p-4 border rounded">
                <p className="text-sm text-gray-600">Knowledge</p>
                <p className="text-xl font-bold">{knowledge?.total || 0}</p>
              </div>
            </div>

            {/* Recent Events */}
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3">Recent Events</h3>
              <div className="space-y-2">
                {events?.events.slice(0, 5).map((event) => (
                  <div key={event.id} className="p-3 bg-gray-50 rounded">
                    <p className="font-medium">{event.title}</p>
                    <p className="text-sm text-gray-600">{event.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'agents' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Agents ({agents?.total})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {agents?.agents.slice(0, 10).map((a) => (
                <div
                  key={a.id}
                  onClick={() => setSelectedAgentId(a.id)}
                  className={`p-4 border rounded cursor-pointer transition-colors ${
                    selectedAgentId === a.id ? 'border-blue-600 bg-blue-50' : 'hover:border-gray-400'
                  }`}
                >
                  <p className="font-bold">{a.name}</p>
                  <p className="text-sm text-gray-600">
                    Age {a.age} • {a.gender} • {a.alive ? 'Alive' : 'Deceased'}
                  </p>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                    <div>Health: {a.health.toFixed(1)}</div>
                    <div>Wealth: {a.wealth.toFixed(1)}</div>
                    <div>Mood: {a.mood.toFixed(1)}</div>
                    <div>Status: {a.status.toFixed(1)}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Selected Agent Details */}
            {selectedAgentId && agentProfile && (
              <div className="mt-6 p-4 border-t">
                <h3 className="text-xl font-bold mb-4">
                  {agentProfile.name} - Detailed Profile
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold mb-2">Skills</h4>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
                      {JSON.stringify(agentProfile.skills, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Inventory ({agentInventory?.total_items})</h4>
                    <div className="text-sm space-y-1">
                      {Object.entries(agentInventory?.inventory_by_category || {}).map(([cat, data]) => (
                        <div key={cat}>
                          <span className="font-medium">{data.name}:</span> {data.items.length} items
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-4">
                  <h4 className="font-semibold mb-2">Fun Stats</h4>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>Celebrations: {agentFunStats?.celebrations_attended || 0}</div>
                    <div>Games: {agentFunStats?.games_played || 0}</div>
                    <div>Art: {agentFunStats?.art_created || 0}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'buildings' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Buildings ({buildings?.total})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {buildings?.buildings.map((building) => (
                <div key={building.id} className="p-4 border rounded">
                  <p className="font-bold">{building.name}</p>
                  <p className="text-sm text-gray-600">{building.category}</p>
                  <p className="text-xs mt-2">Progress: {building.construction_progress}%</p>
                  <p className="text-xs">
                    {building.is_complete ? '✅ Complete' : '🚧 Building'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'science' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Science & Discovery</h2>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-green-50 rounded">
                <p className="text-sm text-gray-600">Discoveries</p>
                <p className="text-2xl font-bold">{experiments?.total_discoveries}</p>
              </div>
              <div className="p-4 bg-red-50 rounded">
                <p className="text-sm text-gray-600">Failures</p>
                <p className="text-2xl font-bold">{experiments?.total_failures}</p>
              </div>
              <div className="p-4 bg-blue-50 rounded">
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold">
                  {((experiments?.success_rate || 0) * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            <h3 className="text-lg font-semibold mb-3">Recent Discoveries</h3>
            <div className="space-y-2">
              {experiments?.discoveries.slice(0, 5).map((discovery) => (
                <div key={discovery.id} className="p-3 bg-gray-50 rounded">
                  <p className="font-bold">{discovery.name}</p>
                  <p className="text-sm text-gray-600">
                    Discovered by {discovery.discovered_by_name}
                  </p>
                  <p className="text-xs mt-1">{discovery.description}</p>
                </div>
              ))}
            </div>

            <h3 className="text-lg font-semibold mb-3 mt-6">Innovations ({innovations?.total})</h3>
            <div className="grid grid-cols-2 gap-2">
              {innovations?.innovations.slice(0, 6).map((innovation) => (
                <div key={innovation.id} className="p-2 border rounded text-sm">
                  {innovation.name}
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'society' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Society & Governance</h2>

            <h3 className="text-lg font-semibold mb-3">Governments ({governments?.total})</h3>
            <div className="space-y-2 mb-6">
              {governments?.governments.map((gov) => (
                <div key={gov.id} className="p-3 border rounded">
                  <p className="font-bold">{gov.name}</p>
                  <p className="text-sm text-gray-600">
                    {gov.type} • {gov.citizens} citizens • {(gov.approval * 100).toFixed(0)}% approval
                  </p>
                </div>
              ))}
            </div>

            <h3 className="text-lg font-semibold mb-3">
              Conflicts ({conflicts?.active_conflicts} active)
            </h3>
            <div className="space-y-2">
              {conflicts?.conflicts.map((conflict, idx) => (
                <div key={idx} className="p-3 bg-red-50 border border-red-200 rounded">
                  <p className="font-bold">{conflict.type}</p>
                  <p className="text-sm">
                    {conflict.side_a_size} vs {conflict.side_b_size} • {conflict.turns_elapsed} turns
                  </p>
                </div>
              ))}
            </div>

            <h3 className="text-lg font-semibold mb-3 mt-6">
              Emergent Roles ({roles?.total_roles})
            </h3>
            <div className="space-y-2">
              {roles?.roles.slice(0, 5).map((role) => (
                <div key={role.role_id} className="p-3 bg-purple-50 rounded">
                  <p className="font-bold">{role.custom_role_name}</p>
                  <p className="text-sm text-gray-600">
                    {role.agent_name} • Pattern: {role.pattern_type}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'knowledge' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Knowledge & Education</h2>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-blue-50 rounded">
                <p className="text-sm text-gray-600">Knowledge Records</p>
                <p className="text-2xl font-bold">{knowledge?.total}</p>
              </div>
              <div className="p-4 bg-green-50 rounded">
                <p className="text-sm text-gray-600">Libraries</p>
                <p className="text-2xl font-bold">{libraries?.total}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded">
                <p className="text-sm text-gray-600">Teaching Sessions</p>
                <p className="text-2xl font-bold">{teachingSessions?.total}</p>
              </div>
            </div>

            <h3 className="text-lg font-semibold mb-3">Libraries</h3>
            <div className="space-y-2">
              {libraries?.libraries.map((lib) => (
                <div key={lib.id} className="p-3 border rounded">
                  <p className="font-bold">{lib.name}</p>
                  <p className="text-sm text-gray-600">
                    {lib.documents_count} documents • {lib.visitors_count} visitors
                    {lib.is_famous && ' • ⭐ Famous'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'economy' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Economy & Resources</h2>

            <h3 className="text-lg font-semibold mb-3">
              Materials ({materials?.total_materials})
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-6">
              {Object.entries(materials?.categories || {}).map(([cat, data]) => (
                <div key={cat} className="p-3 border rounded">
                  <p className="font-medium">{data.name}</p>
                  <p className="text-sm text-gray-600">{data.count} materials</p>
                </div>
              ))}
            </div>

            <h3 className="text-lg font-semibold mb-3">Recipes ({recipes?.total})</h3>
            <div className="grid grid-cols-2 gap-2">
              {recipes?.recipes.slice(0, 8).map((recipe) => (
                <div key={recipe.id} className="p-2 border rounded text-sm">
                  <p className="font-medium">{recipe.name}</p>
                  <p className="text-xs text-gray-600">
                    Crafted {recipe.times_crafted} times
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'culture' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Culture & Fun</h2>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-yellow-50 rounded">
                <p className="text-sm text-gray-600">Celebrations</p>
                <p className="text-2xl font-bold">{funStats?.celebrations.total}</p>
                <p className="text-xs text-gray-500">{funStats?.celebrations.active} active</p>
              </div>
              <div className="p-4 bg-green-50 rounded">
                <p className="text-sm text-gray-600">Games</p>
                <p className="text-2xl font-bold">{funStats?.games.total}</p>
                <p className="text-xs text-gray-500">{funStats?.games.active} active</p>
              </div>
              <div className="p-4 bg-purple-50 rounded">
                <p className="text-sm text-gray-600">Art Pieces</p>
                <p className="text-2xl font-bold">{funStats?.art.total_created}</p>
              </div>
            </div>

            <h3 className="text-lg font-semibold mb-3">
              Active Celebrations ({celebrations?.active.length})
            </h3>
            <div className="space-y-2 mb-6">
              {celebrations?.active.map((cel) => (
                <div key={cel.id} className="p-3 bg-yellow-50 rounded">
                  <p className="font-bold">{cel.name}</p>
                  <p className="text-sm">{cel.participant_count} participants</p>
                </div>
              ))}
            </div>

            <h3 className="text-lg font-semibold mb-3">Art Gallery ({art?.total_art})</h3>
            <div className="grid grid-cols-2 gap-2">
              {art?.art_pieces.slice(0, 6).map((piece) => (
                <div key={piece.id} className="p-3 border rounded">
                  <p className="font-bold">{piece.title}</p>
                  <p className="text-sm text-gray-600">
                    by {piece.creator_name} • Quality: {piece.quality.toFixed(1)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'controls' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Simulation Controls</h2>

            {/* Simulation Status */}
            <div className="mb-6 p-4 bg-gray-50 rounded">
              <h3 className="font-semibold mb-2">Current Status</h3>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Running</p>
                  <p className="font-bold">{simulationStatus?.running ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Paused</p>
                  <p className="font-bold">{simulationStatus?.paused ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Speed</p>
                  <p className="font-bold">{simulationStatus?.speed}</p>
                </div>
                <div>
                  <p className="text-gray-600">Day</p>
                  <p className="font-bold">{simulationStatus?.current_day}</p>
                </div>
              </div>
            </div>

            {/* Speed Controls */}
            <div className="mb-6">
              <h3 className="font-semibold mb-3">Speed Controls</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => pauseSimulation.mutate()}
                  className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                >
                  {simulationStatus?.paused ? 'Resume' : 'Pause'}
                </button>
                <button
                  onClick={() => setSpeed.mutate({ speed: 'slow' })}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Slow
                </button>
                <button
                  onClick={() => setSpeed.mutate({ speed: 'normal' })}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Normal
                </button>
                <button
                  onClick={() => setSpeed.mutate({ speed: 'fast' })}
                  className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
                >
                  Fast
                </button>
              </div>
            </div>

            {/* Character Creation */}
            <div className="mb-6">
              <h3 className="font-semibold mb-3">Create Character</h3>
              <button
                onClick={() =>
                  createCharacter.mutate({
                    name: `Agent-${Date.now()}`,
                    age: 20,
                    gender: 'female',
                  })
                }
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                disabled={createCharacter.isPending}
              >
                {createCharacter.isPending ? 'Creating...' : 'Create Random Character'}
              </button>
            </div>

            {/* Disasters */}
            <div className="mb-6">
              <h3 className="font-semibold mb-3">Trigger Disaster</h3>
              <div className="flex gap-2">
                <button
                  onClick={() =>
                    triggerDisaster.mutate({ type: 'earthquake', severity: 'moderate' })
                  }
                  className="px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                >
                  Earthquake
                </button>
                <button
                  onClick={() =>
                    triggerDisaster.mutate({ type: 'flood', severity: 'moderate' })
                  }
                  className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                >
                  Flood
                </button>
                <button
                  onClick={() =>
                    triggerDisaster.mutate({ type: 'plague', severity: 'moderate' })
                  }
                  className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                >
                  Plague
                </button>
              </div>
            </div>

            {/* Save Management */}
            <div className="mb-6">
              <h3 className="font-semibold mb-3">Save Management</h3>
              <div className="flex gap-2 mb-3">
                <button
                  onClick={() => createSave.mutate({ name: `World-${Date.now()}` })}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  disabled={createSave.isPending}
                >
                  {createSave.isPending ? 'Saving...' : 'Create Save'}
                </button>
              </div>
              <div className="space-y-2">
                {saves?.saves.slice(0, 5).map((save) => (
                  <div key={save.id} className="p-3 border rounded flex justify-between items-center">
                    <div>
                      <p className="font-medium">{save.name}</p>
                      <p className="text-sm text-gray-600">
                        Day {save.tick} • Pop: {save.population}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => loadSave.mutate(save.id)}
                        className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => deleteSave.mutate(save.id)}
                        className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Reset World */}
            <div>
              <h3 className="font-semibold mb-3 text-red-600">Danger Zone</h3>
              <button
                onClick={() => {
                  if (confirm('Reset world? This will delete all progress!')) {
                    resetWorld.mutate();
                  }
                }}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                disabled={resetWorld.isPending}
              >
                {resetWorld.isPending ? 'Resetting...' : 'Reset World'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ApiClientDemo;
