# API Client Documentation

Comprehensive React Query-based API client for the Neuronaut World simulation backend.

## Overview

This API client provides type-safe access to all 45 backend endpoints with:
- **React Query integration** for automatic caching and refetching
- **TypeScript types** for all requests and responses
- **Error handling** with meaningful error messages
- **Automatic invalidation** of related queries on mutations
- **Configurable refetch intervals** optimized per endpoint

## Installation

The client uses `@tanstack/react-query` which is already in your dependencies.

## Configuration

Set your API URL in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Usage

### Setup

Wrap your app with `QueryClientProvider`:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000,
      retry: 1,
    },
  },
});

export default function App({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### Query Hooks (GET Endpoints)

All query hooks return `{ data, isLoading, error, refetch }`.

#### Core World State (5 endpoints)

```tsx
import {
  useServerStatus,
  useWorld,
  useStats,
  useAgents,
  useAgent
} from '@/hooks/use-api-client';

function MyComponent() {
  // Server status - refreshes every 5s
  const { data: status } = useServerStatus();

  // Current world state - refreshes every 2s
  const { data: world } = useWorld();

  // Comprehensive statistics - refreshes every 5s
  const { data: stats } = useStats();

  // All agents - refreshes every 3s
  const { data: agents } = useAgents();

  // Specific agent with full profile - refreshes every 3s
  const { data: agent } = useAgent('agent-id-123');

  return (
    <div>
      <h1>{status?.name} - {status?.status}</h1>
      <p>Population: {world?.population}</p>
      <p>Day: {world?.time.day} - {world?.time.season}</p>
    </div>
  );
}
```

#### Agent Details (3 endpoints)

```tsx
import {
  useAgentProfile,
  useAgentInventory,
  useAgentFunStats
} from '@/hooks/use-api-client';

function AgentDetails({ agentId }: { agentId: string }) {
  // Full agent profile with personality, skills, relationships
  const { data: profile } = useAgentProfile(agentId);

  // Agent's inventory organized by category
  const { data: inventory } = useAgentInventory(agentId);

  // Fun statistics (celebrations, games, art)
  const { data: funStats } = useAgentFunStats(agentId);

  return (
    <div>
      <h2>{profile?.name}</h2>
      <p>Skills: {JSON.stringify(profile?.skills)}</p>
      <p>Items: {inventory?.total_items}/{inventory?.capacity}</p>
      <p>Games Won: {funStats?.games_won}</p>
    </div>
  );
}
```

#### Events & Stories (3 endpoints)

```tsx
import {
  useEvents,
  useStories,
  useAchievements
} from '@/hooks/use-api-client';

function EventsFeed() {
  // Get events with filtering
  const { data: events } = useEvents(50, 2); // limit=50, minImportance=2

  // Epic narratives
  const { data: stories } = useStories();

  // Achievements
  const { data: achievements } = useAchievements();

  return (
    <div>
      {events?.events.map(event => (
        <div key={event.id}>
          <h3>{event.title}</h3>
          <p>{event.description}</p>
        </div>
      ))}
    </div>
  );
}
```

#### Buildings & Structures (1 endpoint)

```tsx
import { useBuildings } from '@/hooks/use-api-client';

function BuildingsView() {
  const { data: buildings, isLoading } = useBuildings();

  if (isLoading) return <div>Loading buildings...</div>;

  return (
    <div>
      <h2>Buildings ({buildings?.total})</h2>
      {buildings?.buildings.map(building => (
        <div key={building.id}>
          <h3>{building.name}</h3>
          <p>Category: {building.category}</p>
          <p>Progress: {building.construction_progress}%</p>
        </div>
      ))}
    </div>
  );
}
```

#### Science & Discovery (2 endpoints)

```tsx
import {
  useExperiments,
  useInnovations
} from '@/hooks/use-api-client';

function SciencePanel() {
  // Discoveries and failed experiments
  const { data: experiments } = useExperiments();

  // Innovations unlocked
  const { data: innovations } = useInnovations();

  return (
    <div>
      <h2>Discoveries ({experiments?.total_discoveries})</h2>
      <p>Success Rate: {(experiments?.success_rate * 100).toFixed(1)}%</p>

      {experiments?.discoveries.map(discovery => (
        <div key={discovery.id}>
          <h3>{discovery.name}</h3>
          <p>Discovered by: {discovery.discovered_by_name}</p>
          <p>Effectiveness: {discovery.effectiveness}</p>
        </div>
      ))}
    </div>
  );
}
```

#### Society & Governance (2 endpoints)

```tsx
import {
  useConflicts,
  useGovernments
} from '@/hooks/use-api-client';

function SocietyPanel() {
  const { data: conflicts } = useConflicts();
  const { data: governments } = useGovernments();

  return (
    <div>
      <h2>Active Conflicts: {conflicts?.active_conflicts}</h2>
      <h2>Governments ({governments?.total})</h2>

      {governments?.governments.map(gov => (
        <div key={gov.id}>
          <h3>{gov.name}</h3>
          <p>Type: {gov.type}</p>
          <p>Citizens: {gov.citizens}</p>
          <p>Approval: {(gov.approval * 100).toFixed(0)}%</p>
        </div>
      ))}
    </div>
  );
}
```

#### Knowledge & Education (3 endpoints)

```tsx
import {
  useKnowledge,
  useLibraries,
  useTeachingSessions
} from '@/hooks/use-api-client';

function KnowledgeSystem() {
  const { data: knowledge } = useKnowledge();
  const { data: libraries } = useLibraries();
  const { data: sessions } = useTeachingSessions();

  return (
    <div>
      <h2>Knowledge Records: {knowledge?.total}</h2>
      <h2>Libraries: {libraries?.total}</h2>
      <h2>Recent Teaching Sessions: {sessions?.total}</h2>
    </div>
  );
}
```

#### Emergent Roles (1 endpoint)

```tsx
import { useRoles } from '@/hooks/use-api-client';

function RolesPanel() {
  const { data: roles } = useRoles();

  return (
    <div>
      <h2>Emergent Roles ({roles?.total_roles})</h2>
      <p>Agents with Roles: {roles?.agents_with_roles}</p>
      <p>Unique Role Names: {roles?.unique_role_names}</p>

      {roles?.roles.map(role => (
        <div key={role.role_id}>
          <h3>{role.custom_role_name}</h3>
          <p>Agent: {role.agent_name}</p>
          <p>Pattern: {role.pattern_type}</p>
          <p>Recognition: {role.recognition_strength}</p>
        </div>
      ))}
    </div>
  );
}
```

#### Economy & Resources (3 endpoints)

```tsx
import {
  useEconomy,
  useMaterials,
  useRecipes
} from '@/hooks/use-api-client';

function EconomyPanel() {
  const { data: economy } = useEconomy();
  const { data: materials } = useMaterials();
  const { data: recipes } = useRecipes();

  return (
    <div>
      <h2>Economy</h2>
      <pre>{JSON.stringify(economy?.wealth_stats, null, 2)}</pre>

      <h2>Materials ({materials?.total_materials})</h2>
      {Object.entries(materials?.categories || {}).map(([cat, data]) => (
        <div key={cat}>
          <h3>{data.name} ({data.count})</h3>
        </div>
      ))}

      <h2>Recipes ({recipes?.total})</h2>
    </div>
  );
}
```

#### Fun & Culture (4 endpoints)

```tsx
import {
  useFunStats,
  useCelebrations,
  useGames,
  useArt
} from '@/hooks/use-api-client';

function CulturePanel() {
  const { data: funStats } = useFunStats();
  const { data: celebrations } = useCelebrations();
  const { data: games } = useGames();
  const { data: art } = useArt();

  return (
    <div>
      <h2>Fun Statistics</h2>
      <p>Total Celebrations: {funStats?.celebrations.total}</p>
      <p>Active Games: {funStats?.games.active}</p>
      <p>Art Created: {funStats?.art.total_created}</p>

      <h2>Active Celebrations ({celebrations?.active.length})</h2>
      <h2>Games ({games?.active.length} active)</h2>
      <h2>Art Gallery ({art?.total_art} pieces)</h2>
    </div>
  );
}
```

#### Consequences (1 endpoint)

```tsx
import { useConsequences } from '@/hooks/use-api-client';

function ConsequencesPanel() {
  const { data: consequences } = useConsequences();

  return (
    <div>
      {consequences?.consequences.map(c => (
        <div key={c.id}>
          <h3>{c.type} (Severity: {c.severity})</h3>
          <p>{c.description}</p>
          <p>Affected: {c.affected_agents.length} agents</p>
        </div>
      ))}
    </div>
  );
}
```

#### Simulation Control (1 endpoint)

```tsx
import { useSimulationStatus } from '@/hooks/use-api-client';

function SimulationControls() {
  const { data: status } = useSimulationStatus();

  return (
    <div>
      <p>Status: {status?.running ? 'Running' : 'Stopped'}</p>
      <p>Speed: {status?.speed}</p>
      <p>Day: {status?.current_day}</p>
    </div>
  );
}
```

#### Save System (1 endpoint)

```tsx
import { useSaves } from '@/hooks/use-api-client';

function SaveManager() {
  const { data: saves } = useSaves();

  return (
    <div>
      <h2>Saved Worlds</h2>
      {saves?.saves.map(save => (
        <div key={save.id}>
          <h3>{save.name}</h3>
          <p>Day {save.tick} - Population: {save.population}</p>
        </div>
      ))}
    </div>
  );
}
```

### Mutation Hooks (POST/DELETE Endpoints)

All mutation hooks return `{ mutate, mutateAsync, isLoading, error }`.

#### Create Character

```tsx
import { useCreateCharacter } from '@/hooks/use-api-client';

function CharacterCreator() {
  const createChar = useCreateCharacter({
    onSuccess: (data) => {
      console.log('Character created:', data.agent);
    },
    onError: (error) => {
      console.error('Failed to create:', error.message);
    },
  });

  const handleCreate = () => {
    createChar.mutate({
      name: 'Alice',
      age: 25,
      gender: 'female',
      personality: {
        openness: 0.8,
        conscientiousness: 0.6,
        extraversion: 0.7,
        agreeableness: 0.9,
        neuroticism: 0.3,
      },
    });
  };

  return (
    <button onClick={handleCreate} disabled={createChar.isLoading}>
      {createChar.isLoading ? 'Creating...' : 'Create Character'}
    </button>
  );
}
```

#### Simulation Controls

```tsx
import {
  usePauseSimulation,
  useSetSimulationSpeed
} from '@/hooks/use-api-client';

function SimulationControls() {
  const pause = usePauseSimulation();
  const setSpeed = useSetSimulationSpeed();

  return (
    <div>
      <button onClick={() => pause.mutate()}>
        Pause/Resume
      </button>

      <button onClick={() => setSpeed.mutate({ speed: 'fast' })}>
        Fast Forward
      </button>

      <button onClick={() => setSpeed.mutate({ speed: 'normal' })}>
        Normal Speed
      </button>
    </div>
  );
}
```

#### Trigger Disaster

```tsx
import { useTriggerDisaster } from '@/hooks/use-api-client';

function DisasterControls() {
  const trigger = useTriggerDisaster({
    onSuccess: (data) => {
      alert(data.message);
    },
  });

  return (
    <button
      onClick={() => trigger.mutate({
        type: 'earthquake',
        severity: 'major'
      })}
    >
      Trigger Earthquake
    </button>
  );
}
```

#### Save Management

```tsx
import {
  useCreateSave,
  useLoadSave,
  useDeleteSave
} from '@/hooks/use-api-client';

function SaveControls() {
  const createSave = useCreateSave();
  const loadSave = useLoadSave();
  const deleteSave = useDeleteSave();

  return (
    <div>
      <button onClick={() => createSave.mutate({ name: 'My World' })}>
        Save World
      </button>

      <button onClick={() => loadSave.mutate('save-id-123')}>
        Load Save
      </button>

      <button onClick={() => deleteSave.mutate('save-id-123')}>
        Delete Save
      </button>
    </div>
  );
}
```

#### Reset World

```tsx
import { useResetWorld } from '@/hooks/use-api-client';

function ResetButton() {
  const reset = useResetWorld({
    onSuccess: () => {
      alert('World reset successful!');
    },
  });

  return (
    <button
      onClick={() => {
        if (confirm('Reset world? This cannot be undone!')) {
          reset.mutate();
        }
      }}
    >
      Reset World
    </button>
  );
}
```

## Advanced Usage

### Custom Options

Override default query options:

```tsx
const { data } = useAgents({
  refetchInterval: 10000, // Override default 3s with 10s
  enabled: false, // Don't auto-fetch
  staleTime: 5000, // Data fresh for 5s
});
```

### Manual Refetch

```tsx
const { data, refetch } = useWorld();

// Manually refetch
<button onClick={() => refetch()}>Refresh</button>
```

### Error Handling

```tsx
const { data, error, isLoading } = useAgents();

if (isLoading) return <div>Loading...</div>;
if (error) return <div>Error: {error.message}</div>;

return <div>{data.total} agents</div>;
```

### Optimistic Updates

```tsx
const createChar = useCreateCharacter({
  onMutate: async (newChar) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: queryKeys.agents });

    // Snapshot previous value
    const previous = queryClient.getQueryData(queryKeys.agents);

    // Optimistically update
    queryClient.setQueryData(queryKeys.agents, (old: any) => ({
      ...old,
      agents: [...old.agents, newChar],
      total: old.total + 1,
    }));

    return { previous };
  },
  onError: (err, newChar, context) => {
    // Rollback on error
    queryClient.setQueryData(queryKeys.agents, context?.previous);
  },
});
```

### Direct API Access

Use the client directly without React Query:

```tsx
import { apiClient } from '@/hooks/use-api-client';

async function fetchData() {
  try {
    const world = await apiClient.getWorld();
    const agents = await apiClient.getAgents();
    return { world, agents };
  } catch (error) {
    console.error('Failed:', error);
  }
}
```

## Complete Endpoint Reference

### Query Hooks (32 endpoints)

| Hook | Endpoint | Refetch Interval | Description |
|------|----------|------------------|-------------|
| `useServerStatus()` | `GET /` | 5s | Server status |
| `useWorld()` | `GET /world` | 2s | World snapshot |
| `useStats()` | `GET /stats` | 5s | All statistics |
| `useAgents()` | `GET /agents` | 3s | All agents |
| `useAgent(id)` | `GET /agents/{id}` | 3s | Agent details |
| `useAgentProfile(id)` | `GET /agents/{id}/profile` | 5s | Full profile |
| `useAgentInventory(id)` | `GET /agents/{id}/inventory` | 5s | Inventory |
| `useAgentFunStats(id)` | `GET /agents/{id}/fun` | 10s | Fun stats |
| `useEvents(limit, minImportance)` | `GET /events` | 5s | Events feed |
| `useStories()` | `GET /stories` | 10s | Epic stories |
| `useAchievements()` | `GET /achievements` | 10s | Achievements |
| `useConsequences()` | `GET /consequences` | 5s | Consequences |
| `useBuildings()` | `GET /buildings` | 5s | Buildings |
| `useExperiments()` | `GET /experiments` | 10s | Discoveries |
| `useInnovations()` | `GET /innovations` | 10s | Innovations |
| `useConflicts()` | `GET /conflicts` | 5s | Conflicts |
| `useGovernments()` | `GET /governments` | 10s | Governments |
| `useKnowledge()` | `GET /knowledge` | 10s | Knowledge |
| `useLibraries()` | `GET /knowledge/libraries` | 10s | Libraries |
| `useTeachingSessions()` | `GET /knowledge/teaching` | 10s | Teaching |
| `useRoles()` | `GET /roles` | 10s | Emergent roles |
| `useEconomy()` | `GET /economy` | 5s | Economy |
| `useMaterials()` | `GET /materials` | 60s (stale) | Materials |
| `useRecipes()` | `GET /recipes` | 60s (stale) | Recipes |
| `useFunStats()` | `GET /fun/stats` | 10s | Fun stats |
| `useCelebrations()` | `GET /fun/celebrations` | 5s | Celebrations |
| `useGames()` | `GET /fun/games` | 5s | Games |
| `useArt()` | `GET /fun/art` | 10s | Art pieces |
| `useSimulationStatus()` | `GET /simulation/status` | 2s | Sim status |
| `useSaves()` | `GET /saves` | On-demand | Save list |

### Mutation Hooks (8 endpoints)

| Hook | Endpoint | Invalidates | Description |
|------|----------|-------------|-------------|
| `useCreateCharacter()` | `POST /characters` | agents, world, stats | Create character |
| `usePauseSimulation()` | `POST /simulation/pause` | simulationStatus | Pause/resume |
| `useSetSimulationSpeed()` | `POST /simulation/speed` | simulationStatus | Set speed |
| `useTriggerDisaster()` | `POST /disasters/trigger` | world, events, stats | Trigger disaster |
| `useCreateSave()` | `POST /saves` | saves | Create save |
| `useLoadSave()` | `POST /saves/{id}/load` | ALL | Load save |
| `useDeleteSave()` | `DELETE /saves/{id}` | saves | Delete save |
| `useResetWorld()` | `POST /reset` | ALL | Reset world |

## TypeScript Types

All types are exported from the hook file:

```tsx
import type {
  Agent,
  Building,
  Event,
  Discovery,
  Material,
  Recipe,
  // ... 40+ types
} from '@/hooks/use-api-client';
```

## Best Practices

1. **Use the hooks** - They handle caching, refetching, and state management automatically
2. **Enable/disable queries** - Use `enabled` option to conditionally fetch
3. **Handle loading states** - Always check `isLoading` and `error`
4. **Optimize refetch intervals** - Adjust based on data change frequency
5. **Use mutations for side effects** - They auto-invalidate related queries
6. **Type everything** - Take advantage of full TypeScript support

## Performance Tips

1. **Stale time** - Set higher `staleTime` for static data (materials, recipes)
2. **Disable unused queries** - Use `enabled: false` when data not needed
3. **Debounce mutations** - Prevent rapid-fire mutations
4. **Pagination** - Use limit parameters for large datasets (events)
5. **Selective invalidation** - Only invalidate queries that need updating

## Error Handling

All errors include meaningful messages from the backend:

```tsx
const { error } = useAgents();

if (error) {
  // Error messages are from backend API
  console.log(error.message); // "Simulation not running" or "Agent not found"
}
```

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Complete Example

```tsx
'use client';

import {
  useWorld,
  useAgents,
  useEvents,
  useBuildings,
  useCreateCharacter,
  usePauseSimulation,
} from '@/hooks/use-api-client';

export default function Dashboard() {
  const { data: world, isLoading: worldLoading } = useWorld();
  const { data: agents } = useAgents();
  const { data: events } = useEvents(10, 2);
  const { data: buildings } = useBuildings();

  const createChar = useCreateCharacter();
  const pause = usePauseSimulation();

  if (worldLoading) return <div>Loading world...</div>;

  return (
    <div>
      <h1>Neuronaut World</h1>

      <section>
        <h2>World Status</h2>
        <p>Day {world?.time.day} - {world?.time.season}</p>
        <p>Population: {world?.population} ({world?.alive} alive)</p>
      </section>

      <section>
        <h2>Agents ({agents?.total})</h2>
        {agents?.agents.slice(0, 5).map(agent => (
          <div key={agent.id}>{agent.name} - Age {agent.age}</div>
        ))}
      </section>

      <section>
        <h2>Recent Events</h2>
        {events?.events.map(event => (
          <div key={event.id}>{event.title}</div>
        ))}
      </section>

      <section>
        <h2>Buildings ({buildings?.total})</h2>
        {buildings?.buildings.map(b => (
          <div key={b.id}>{b.name} - {b.category}</div>
        ))}
      </section>

      <section>
        <h2>Controls</h2>
        <button onClick={() => pause.mutate()}>
          Pause/Resume
        </button>
        <button onClick={() => createChar.mutate({ name: 'Alice' })}>
          Create Character
        </button>
      </section>
    </div>
  );
}
```

## Support

For issues or questions, check:
- Backend API docs: `http://localhost:8000/docs`
- Server.py source: `/api/server.py`
- Types reference: This file's type definitions
