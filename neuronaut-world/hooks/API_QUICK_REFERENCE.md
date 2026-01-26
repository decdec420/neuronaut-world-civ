# API Client Quick Reference

Quick copy-paste examples for common use cases.

## Setup

```tsx
// .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Import

```tsx
import {
  // Queries
  useWorld,
  useAgents,
  useAgent,
  useBuildings,
  useEvents,
  // Mutations
  useCreateCharacter,
  usePauseSimulation,
  // Types
  type Agent,
  type Building,
  type Event,
} from '@/hooks/use-api-client';
```

## Common Patterns

### 1. Display World State
```tsx
function WorldDisplay() {
  const { data: world, isLoading } = useWorld();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <p>Day: {world?.time.day}</p>
      <p>Population: {world?.population}</p>
      <p>Era: {world?.era}</p>
    </div>
  );
}
```

### 2. List Agents
```tsx
function AgentList() {
  const { data: agents } = useAgents();

  return (
    <ul>
      {agents?.agents.map((agent) => (
        <li key={agent.id}>
          {agent.name} - Age {agent.age}
        </li>
      ))}
    </ul>
  );
}
```

### 3. Agent Details
```tsx
function AgentCard({ agentId }: { agentId: string }) {
  const { data: agent } = useAgent(agentId);
  const { data: inventory } = useAgentInventory(agentId);

  return (
    <div>
      <h2>{agent?.profile.name}</h2>
      <p>Health: {agent?.agent.health}</p>
      <p>Items: {inventory?.total_items}</p>
    </div>
  );
}
```

### 4. Events Feed
```tsx
function EventsFeed() {
  const { data: events } = useEvents(20, 2); // 20 events, min importance 2

  return (
    <div>
      {events?.events.map((event) => (
        <div key={event.id}>
          <h3>{event.title}</h3>
          <p>{event.description}</p>
        </div>
      ))}
    </div>
  );
}
```

### 5. Create Character
```tsx
function CreateCharacterButton() {
  const create = useCreateCharacter({
    onSuccess: (data) => {
      alert(`Created: ${data.agent.name}`);
    },
  });

  return (
    <button
      onClick={() =>
        create.mutate({
          name: 'Alice',
          age: 25,
          gender: 'female',
        })
      }
      disabled={create.isPending}
    >
      {create.isPending ? 'Creating...' : 'Create Character'}
    </button>
  );
}
```

### 6. Simulation Controls
```tsx
function SimControls() {
  const pause = usePauseSimulation();
  const setSpeed = useSetSimulationSpeed();

  return (
    <div>
      <button onClick={() => pause.mutate()}>
        Pause/Resume
      </button>
      <button onClick={() => setSpeed.mutate({ speed: 'fast' })}>
        Fast
      </button>
      <button onClick={() => setSpeed.mutate({ speed: 'normal' })}>
        Normal
      </button>
    </div>
  );
}
```

### 7. Buildings Display
```tsx
function BuildingsList() {
  const { data: buildings } = useBuildings();

  return (
    <div>
      <h2>Buildings ({buildings?.total})</h2>
      {buildings?.buildings.map((b) => (
        <div key={b.id}>
          <h3>{b.name}</h3>
          <p>Category: {b.category}</p>
          <p>Progress: {b.construction_progress}%</p>
        </div>
      ))}
    </div>
  );
}
```

### 8. Science Panel
```tsx
function SciencePanel() {
  const { data: experiments } = useExperiments();
  const { data: innovations } = useInnovations();

  return (
    <div>
      <h2>Discoveries: {experiments?.total_discoveries}</h2>
      <h2>Innovations: {innovations?.total}</h2>
      <p>Success Rate: {(experiments?.success_rate * 100).toFixed(1)}%</p>
    </div>
  );
}
```

### 9. Save Management
```tsx
function SaveManager() {
  const { data: saves } = useSaves();
  const createSave = useCreateSave();
  const loadSave = useLoadSave();

  return (
    <div>
      <button onClick={() => createSave.mutate({ name: 'My World' })}>
        Save World
      </button>
      {saves?.saves.map((save) => (
        <div key={save.id}>
          <span>{save.name}</span>
          <button onClick={() => loadSave.mutate(save.id)}>Load</button>
        </div>
      ))}
    </div>
  );
}
```

### 10. Error Handling
```tsx
function SafeComponent() {
  const { data, isLoading, error } = useAgents();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return <div>No data</div>;

  return <div>{data.total} agents</div>;
}
```

### 11. Custom Refetch
```tsx
function ManualRefresh() {
  const { data, refetch, isRefetching } = useWorld({
    enabled: false, // Don't auto-fetch
  });

  return (
    <button onClick={() => refetch()} disabled={isRefetching}>
      {isRefetching ? 'Refreshing...' : 'Refresh'}
    </button>
  );
}
```

### 12. Conditional Query
```tsx
function ConditionalData({ agentId }: { agentId: string | null }) {
  const { data } = useAgent(agentId || '', {
    enabled: !!agentId, // Only fetch if agentId exists
  });

  if (!agentId) return <div>Select an agent</div>;

  return <div>{data?.agent.name}</div>;
}
```

### 13. Statistics Dashboard
```tsx
function StatsDashboard() {
  const { data: stats } = useStats();

  return (
    <div>
      <h2>World Statistics</h2>
      <p>Total Agents: {stats?.agents.total}</p>
      <p>Buildings: {stats?.buildings.total_buildings}</p>
      <p>Innovations: {stats?.innovations.total_innovations}</p>
    </div>
  );
}
```

### 14. Knowledge System
```tsx
function KnowledgePanel() {
  const { data: knowledge } = useKnowledge();
  const { data: libraries } = useLibraries();

  return (
    <div>
      <h2>Knowledge: {knowledge?.total}</h2>
      <h2>Libraries: {libraries?.total}</h2>
    </div>
  );
}
```

### 15. Culture & Fun
```tsx
function CulturePanel() {
  const { data: celebrations } = useCelebrations();
  const { data: games } = useGames();
  const { data: art } = useArt();

  return (
    <div>
      <h2>Active Celebrations: {celebrations?.active.length}</h2>
      <h2>Active Games: {games?.active.length}</h2>
      <h2>Art Pieces: {art?.total_art}</h2>
    </div>
  );
}
```

## All Available Hooks

### Query Hooks (GET)
```tsx
// Core
useServerStatus()
useWorld()
useStats()
useAgents()
useAgent(id)

// Agent Details
useAgentProfile(id)
useAgentInventory(id)
useAgentFunStats(id)

// Events & Stories
useEvents(limit?, minImportance?)
useStories()
useAchievements()
useConsequences()

// Buildings & Science
useBuildings()
useExperiments()
useInnovations()

// Society
useConflicts()
useGovernments()
useRoles()

// Knowledge
useKnowledge()
useLibraries()
useTeachingSessions()

// Economy
useEconomy()
useMaterials()
useRecipes()

// Culture
useFunStats()
useCelebrations()
useGames()
useArt()

// Control
useSimulationStatus()
useSaves()
```

### Mutation Hooks (POST/DELETE)
```tsx
useCreateCharacter()
usePauseSimulation()
useSetSimulationSpeed()
useTriggerDisaster()
useCreateSave()
useLoadSave()
useDeleteSave()
useResetWorld()
```

## Common Types

```tsx
import type {
  Agent,
  Building,
  Event,
  Discovery,
  Material,
  Recipe,
  Knowledge,
  Role,
  Celebration,
  Game,
  ArtPiece,
} from '@/hooks/use-api-client';
```

## Direct API Access

```tsx
import { apiClient } from '@/hooks/use-api-client';

// In async function
const world = await apiClient.getWorld();
const agents = await apiClient.getAgents();
```

## Performance Tips

```tsx
// Slow refetch for static data
const { data } = useMaterials({
  refetchInterval: 60000, // 1 minute
});

// Disable auto-fetch
const { data } = useAgents({
  enabled: false,
});

// Increase stale time
const { data } = useRecipes({
  staleTime: 300000, // 5 minutes
});
```

## Complete Example

```tsx
'use client';

import {
  useWorld,
  useAgents,
  useBuildings,
  useCreateCharacter,
  usePauseSimulation,
} from '@/hooks/use-api-client';

export default function Dashboard() {
  const { data: world, isLoading } = useWorld();
  const { data: agents } = useAgents();
  const { data: buildings } = useBuildings();

  const create = useCreateCharacter();
  const pause = usePauseSimulation();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="p-6">
      <h1>Neuronaut World</h1>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <h2>Day {world?.time.day}</h2>
          <p>{world?.time.season}</p>
        </div>
        <div>
          <h2>{world?.population} Population</h2>
          <p>{world?.alive} alive</p>
        </div>
        <div>
          <h2>{world?.era}</h2>
        </div>
      </div>

      <section>
        <h2>Agents ({agents?.total})</h2>
        {agents?.agents.slice(0, 5).map((agent) => (
          <div key={agent.id}>
            {agent.name} - Age {agent.age}
          </div>
        ))}
      </section>

      <section>
        <h2>Buildings ({buildings?.total})</h2>
        {buildings?.buildings.map((b) => (
          <div key={b.id}>{b.name}</div>
        ))}
      </section>

      <section>
        <button onClick={() => pause.mutate()}>Pause</button>
        <button onClick={() => create.mutate({ name: 'Alice' })}>
          Create Character
        </button>
      </section>
    </div>
  );
}
```

## Troubleshooting

**No data showing?**
```tsx
// Check if backend is running
const { data, error } = useServerStatus();
console.log(error); // Check for connection errors
```

**Stale data?**
```tsx
// Force refetch
const { refetch } = useWorld();
refetch();

// Or reduce refetch interval
const { data } = useWorld({
  refetchInterval: 1000, // 1 second
});
```

**Type errors?**
```tsx
// Import types explicitly
import type { Agent } from '@/hooks/use-api-client';

const agent: Agent = {...};
```

## More Examples

See full documentation: `/hooks/API_CLIENT_README.md`
See demo component: `/components/api-client-demo.tsx`
