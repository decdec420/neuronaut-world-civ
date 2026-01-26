'use client';

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';

// ============================================================================
// CONFIGURATION
// ============================================================================

const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  return 'http://localhost:8000';
};

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

// Core Types
export interface Location {
  x: number;
  y: number;
}

export interface Agent {
  id: string;
  name: string;
  age: number;
  gender: string;
  location: Location;
  health: number;
  wealth: number;
  status: number;
  mood: number;
  life_satisfaction: number;
  is_player: boolean;
  alive: boolean;
}

export interface AgentProfile {
  id: string;
  name: string;
  age: number;
  gender: string;
  personality: Record<string, number>;
  relationships: any[];
  memories: any[];
  skills: Record<string, number>;
  traits: string[];
  current_activity: string;
  goals: any[];
  inventory: Record<string, number>;
}

export interface Event {
  id: string;
  category: string;
  importance: number;
  title: string;
  description: string;
  tick: number;
  agent_ids: string[];
  timestamp: string;
}

export interface Building {
  id: string;
  name: string;
  category: string;
  purposes: string[];
  location: Location;
  builders: string[];
  materials_used: Record<string, number>;
  built_date: string | null;
  is_complete: boolean;
  construction_progress: number;
  collapsed: boolean;
}

export interface Material {
  id: string;
  name: string;
  description: string;
  hardness: number;
  weight: number;
  durability: number;
  flammable: boolean;
  edible: boolean;
  liquid: boolean;
  stackable: boolean;
  tags: string[];
  discovered_by?: string;
  discovery_method?: string;
}

export interface Recipe {
  id: string;
  name: string;
  description: string;
  output_item: string;
  output_quantity: number;
  inputs: Record<string, number>;
  requires_fire: boolean;
  requires_water: boolean;
  requires_tool: string | null;
  required_skill: string | null;
  min_skill_level: number;
  is_basic: boolean;
  difficulty: number;
  times_crafted: number;
}

export interface Discovery {
  id: string;
  name: string;
  discovered_by_id: string;
  discovered_by_name: string;
  discovery_date: string;
  material_name: string | null;
  properties: string[];
  recipe: any;
  effectiveness: number;
  category: string;
  description: string;
  discovery_context: string;
  known_by_count: number;
  known_by_ids: string[];
  times_used: number;
  success_rate: number;
  intent: any;
}

export interface Experiment {
  agent_id: string;
  agent_name: string;
  inputs: string[];
  method: string;
  category: string;
  reason: string;
  date: string;
  lesson_learned?: string;
  consequences?: Record<string, any>;
  intent?: any;
}

export interface Innovation {
  id: string;
  name: string;
  discovered_by: string;
  discovery_date: string;
  category: string;
  effects: Record<string, any>;
}

export interface Conflict {
  id: string;
  type: string;
  reason: string;
  side_a_size: number;
  side_b_size: number;
  turns_elapsed: number;
}

export interface Government {
  id: string;
  name: string;
  type: string;
  citizens: number;
  approval: number;
  leader: string;
}

export interface Knowledge {
  id: string;
  name: string;
  type: string;
  content: string;
  author: string;
  transmission_method: string;
  accuracy: number;
  known_by_count: number;
  times_taught: number;
  mutation_count: number;
  has_mutated: boolean;
}

export interface Library {
  id: string;
  name: string;
  location: Location;
  founder: string;
  founded_date: string;
  documents_count: number;
  total_knowledge: number;
  visitors_count: number;
  times_visited: number;
  is_famous: boolean;
  librarian: string | null;
}

export interface TeachingSession {
  id: string;
  teacher: string;
  students_count: number;
  knowledge_count: number;
  date: string;
  teacher_skill: number;
  method: string;
}

export interface Role {
  role_id: string;
  agent_id: string;
  agent_name: string;
  custom_role_name: string;
  role_name_language: string;
  pattern_type: string;
  dominant_actions: string[];
  pattern_strength: number;
  emergence_date: string;
  emergence_context: string;
  recognized_by_count: number;
  recognition_strength: number;
  name_adopters_count: number;
  times_acted_in_role: number;
  role_effectiveness: number;
  previous_names: string[];
}

export interface Celebration {
  id: string;
  type: string;
  name: string;
  organizer_id: string;
  participants: string[];
  participant_count: number;
  location: Location;
  trigger_event: string;
  duration_remaining?: number;
  mood_boost?: number;
}

export interface Game {
  id: string;
  type: string;
  players: string[];
  player_count: number;
  stakes?: any;
  spectators?: string[];
  completed: boolean;
  winner?: string;
  scores?: Record<string, number>;
}

export interface ArtPiece {
  id: string;
  type: string;
  title: string;
  creator_id: string;
  creator_name: string;
  quality: number;
  fame_generated: number;
  cultural_value: number;
  created_at: string;
  viewer_count: number;
  reactions: Record<string, number>;
}

export interface Consequence {
  id: string;
  type: string;
  severity: number;
  description: string;
  caused_by: string;
  affected_agents: string[];
  timestamp: string;
  secondary_effects: any[];
}

export interface Story {
  id: string;
  title: string;
  narrative: string;
  category: string;
  importance: number;
  characters: string[];
  timestamp: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  type: string;
  unlocked_by: string;
  unlocked_date: string;
  rarity: string;
}

export interface SaveInfo {
  id: string;
  name: string;
  created_at: string;
  tick: number;
  population: number;
}

// Response Types
export interface ServerStatusResponse {
  name: string;
  version: string;
  status: string;
  agents: number;
}

export interface WorldResponse {
  agents: Agent[];
  tick: number;
  era: string;
  population: number;
  alive: number;
  time: {
    day: number;
    season: string;
    year: number;
  };
}

export interface AgentsResponse {
  agents: Agent[];
  total: number;
}

export interface AgentDetailResponse {
  profile: AgentProfile;
  agent: Agent;
}

export interface EventsResponse {
  events: Event[];
  total: number;
}

export interface StoriesResponse {
  stories: Story[];
  total: number;
}

export interface AchievementsResponse {
  agent_achievements: Achievement[];
  civilization_achievements: Achievement[];
  total: number;
}

export interface ConsequencesResponse {
  consequences: Consequence[];
  statistics: Record<string, any>;
}

export interface BuildingsResponse {
  buildings: Building[];
  total: number;
}

export interface ExperimentsResponse {
  discoveries: Discovery[];
  failures: Experiment[];
  materials: Material[];
  total_discoveries: number;
  total_failures: number;
  success_rate: number;
}

export interface InnovationsResponse {
  innovations: Innovation[];
  total: number;
}

export interface ConflictsResponse {
  active_conflicts: number;
  conflicts: Conflict[];
}

export interface GovernmentsResponse {
  governments: Government[];
  total: number;
}

export interface KnowledgeResponse {
  knowledge: Knowledge[];
  total: number;
}

export interface LibrariesResponse {
  libraries: Library[];
  total: number;
}

export interface TeachingResponse {
  sessions: TeachingSession[];
  total: number;
}

export interface RolesResponse {
  roles: Role[];
  total_roles: number;
  agents_with_roles: number;
  unique_role_names: number;
  role_vocabulary: any[];
  statistics: Record<string, any>;
}

export interface EconomyResponse {
  wealth_stats: Record<string, any>;
  market_stats: Record<string, any>;
}

export interface MaterialsResponse {
  categories: Record<string, {
    name: string;
    count: number;
    materials: Material[];
  }>;
  total_materials: number;
}

export interface RecipesResponse {
  recipes: Recipe[];
  total: number;
}

export interface InventoryResponse {
  agent_id: string;
  agent_name: string;
  inventory_by_category: Record<string, {
    name: string;
    items: Array<Material & { quantity: number }>;
  }>;
  total_items: number;
  capacity: number;
}

export interface FunStatsResponse {
  celebrations: {
    total: number;
    active: number;
    traditions_count: number;
    most_popular_tradition?: string;
  };
  games: {
    total: number;
    active: number;
  };
  art: {
    total_created: number;
  };
}

export interface CelebrationsResponse {
  active: Celebration[];
  recent: Celebration[];
  traditions: Record<string, any>;
}

export interface GamesResponse {
  active: Game[];
  recent: Game[];
}

export interface ArtResponse {
  art_pieces: ArtPiece[];
  total_art: number;
  by_type: Record<string, number>;
}

export interface AgentFunStatsResponse {
  celebrations_attended: number;
  celebrations_organized: number;
  games_played: number;
  games_won: number;
  art_created: number;
  art_viewed: number;
  favorite_game_type?: string;
  favorite_celebration_type?: string;
}

export interface StatsResponse {
  world: Record<string, any>;
  events: Record<string, any>;
  economy: Record<string, any>;
  agents: {
    total: number;
    alive: number;
    player_characters: number;
  };
  buildings: Record<string, any>;
  innovations: Record<string, any>;
  warfare: Record<string, any>;
  governance: Record<string, any>;
  production: Record<string, any>;
  strategy: Record<string, any>;
  experimentation: Record<string, any>;
  dynamic_buildings: Record<string, any>;
  knowledge: Record<string, any>;
  consequences: Record<string, any>;
  roles: Record<string, any>;
  tech_progression: Record<string, any>;
  civilization: Record<string, any>;
  stories: Record<string, any>;
  achievements: Record<string, any>;
  meta_progression: Record<string, any>;
  population: Record<string, any>;
  weather: Record<string, any>;
  disasters: Record<string, any>;
}

export interface SimulationStatusResponse {
  running: boolean;
  paused: boolean;
  speed: 'paused' | 'slow' | 'normal' | 'fast' | 'ultra' | 'stopped';
  tick_rate: number;
  current_day: number;
}

export interface SavesResponse {
  saves: SaveInfo[];
}

// Request Types
export interface CreateCharacterRequest {
  name: string;
  age?: number;
  gender?: string;
  personality?: Record<string, number>;
}

export interface CreateCharacterResponse {
  success: boolean;
  agent: Agent;
}

export interface SetSpeedRequest {
  speed: 'paused' | 'slow' | 'normal' | 'fast' | 'ultra';
}

export interface SetSpeedResponse {
  success: boolean;
  speed: string;
  tick_rate: number;
  paused: boolean;
}

export interface TriggerDisasterRequest {
  type: 'earthquake' | 'flood' | 'drought' | 'plague' | 'wildfire' | 'meteor';
  severity: 'minor' | 'moderate' | 'major' | 'catastrophic';
}

export interface TriggerDisasterResponse {
  success: boolean;
  message: string;
  disaster_type: string;
  severity: string;
}

export interface CreateSaveRequest {
  name?: string;
}

export interface CreateSaveResponse {
  success: boolean;
  message: string;
}

export interface LoadSaveResponse {
  success: boolean;
  message: string;
}

export interface DeleteSaveResponse {
  success: boolean;
  message: string;
}

export interface ResetWorldResponse {
  success: boolean;
  message: string;
}

export interface PauseResponse {
  success: boolean;
  paused: boolean;
  message: string;
}

// ============================================================================
// API CLIENT
// ============================================================================

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getApiUrl();
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unknown error occurred');
    }
  }

  // Core World State Endpoints
  async getServerStatus(): Promise<ServerStatusResponse> {
    return this.fetch('/');
  }

  async getWorld(): Promise<WorldResponse> {
    return this.fetch('/world');
  }

  async getStats(): Promise<StatsResponse> {
    return this.fetch('/stats');
  }

  async getAgents(): Promise<AgentsResponse> {
    return this.fetch('/agents');
  }

  async getAgent(id: string): Promise<AgentDetailResponse> {
    return this.fetch(`/agents/${id}`);
  }

  // Advanced Systems Endpoints
  async getAgentProfile(id: string): Promise<AgentProfile> {
    return this.fetch(`/agents/${id}/profile`);
  }

  async getAgentInventory(id: string): Promise<InventoryResponse> {
    return this.fetch(`/agents/${id}/inventory`);
  }

  async getAgentFunStats(id: string): Promise<AgentFunStatsResponse> {
    return this.fetch(`/agents/${id}/fun`);
  }

  async getEvents(limit = 50, minImportance = 1): Promise<EventsResponse> {
    return this.fetch(`/events?limit=${limit}&min_importance=${minImportance}`);
  }

  async getStories(): Promise<StoriesResponse> {
    return this.fetch('/stories');
  }

  async getAchievements(): Promise<AchievementsResponse> {
    return this.fetch('/achievements');
  }

  async getConsequences(): Promise<ConsequencesResponse> {
    return this.fetch('/consequences');
  }

  async getBuildings(): Promise<BuildingsResponse> {
    return this.fetch('/buildings');
  }

  async getExperiments(): Promise<ExperimentsResponse> {
    return this.fetch('/experiments');
  }

  async getInnovations(): Promise<InnovationsResponse> {
    return this.fetch('/innovations');
  }

  async getConflicts(): Promise<ConflictsResponse> {
    return this.fetch('/conflicts');
  }

  async getGovernments(): Promise<GovernmentsResponse> {
    return this.fetch('/governments');
  }

  async getKnowledge(): Promise<KnowledgeResponse> {
    return this.fetch('/knowledge');
  }

  async getLibraries(): Promise<LibrariesResponse> {
    return this.fetch('/knowledge/libraries');
  }

  async getTeachingSessions(): Promise<TeachingResponse> {
    return this.fetch('/knowledge/teaching');
  }

  async getRoles(): Promise<RolesResponse> {
    return this.fetch('/roles');
  }

  async getEconomy(): Promise<EconomyResponse> {
    return this.fetch('/economy');
  }

  async getMaterials(): Promise<MaterialsResponse> {
    return this.fetch('/materials');
  }

  async getRecipes(): Promise<RecipesResponse> {
    return this.fetch('/recipes');
  }

  async getFunStats(): Promise<FunStatsResponse> {
    return this.fetch('/fun/stats');
  }

  async getCelebrations(): Promise<CelebrationsResponse> {
    return this.fetch('/fun/celebrations');
  }

  async getGames(): Promise<GamesResponse> {
    return this.fetch('/fun/games');
  }

  async getArt(): Promise<ArtResponse> {
    return this.fetch('/fun/art');
  }

  // Simulation Control Endpoints
  async createCharacter(data: CreateCharacterRequest): Promise<CreateCharacterResponse> {
    return this.fetch('/characters', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async pauseSimulation(): Promise<PauseResponse> {
    return this.fetch('/simulation/pause', {
      method: 'POST',
    });
  }

  async setSimulationSpeed(data: SetSpeedRequest): Promise<SetSpeedResponse> {
    return this.fetch('/simulation/speed', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSimulationStatus(): Promise<SimulationStatusResponse> {
    return this.fetch('/simulation/status');
  }

  async triggerDisaster(data: TriggerDisasterRequest): Promise<TriggerDisasterResponse> {
    return this.fetch('/disasters/trigger', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Save System Endpoints
  async getSaves(): Promise<SavesResponse> {
    return this.fetch('/saves');
  }

  async createSave(data: CreateSaveRequest): Promise<CreateSaveResponse> {
    return this.fetch('/saves', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async loadSave(id: string): Promise<LoadSaveResponse> {
    return this.fetch(`/saves/${id}/load`, {
      method: 'POST',
    });
  }

  async deleteSave(id: string): Promise<DeleteSaveResponse> {
    return this.fetch(`/saves/${id}`, {
      method: 'DELETE',
    });
  }

  async resetWorld(): Promise<ResetWorldResponse> {
    return this.fetch('/reset', {
      method: 'POST',
    });
  }
}

// Singleton instance
const apiClient = new ApiClient();

// ============================================================================
// REACT QUERY HOOKS
// ============================================================================

// Query Keys
export const queryKeys = {
  serverStatus: ['serverStatus'] as const,
  world: ['world'] as const,
  stats: ['stats'] as const,
  agents: ['agents'] as const,
  agent: (id: string) => ['agent', id] as const,
  agentProfile: (id: string) => ['agentProfile', id] as const,
  agentInventory: (id: string) => ['agentInventory', id] as const,
  agentFunStats: (id: string) => ['agentFunStats', id] as const,
  events: (limit?: number, minImportance?: number) => ['events', limit, minImportance] as const,
  stories: ['stories'] as const,
  achievements: ['achievements'] as const,
  consequences: ['consequences'] as const,
  buildings: ['buildings'] as const,
  experiments: ['experiments'] as const,
  innovations: ['innovations'] as const,
  conflicts: ['conflicts'] as const,
  governments: ['governments'] as const,
  knowledge: ['knowledge'] as const,
  libraries: ['libraries'] as const,
  teachingSessions: ['teachingSessions'] as const,
  roles: ['roles'] as const,
  economy: ['economy'] as const,
  materials: ['materials'] as const,
  recipes: ['recipes'] as const,
  funStats: ['funStats'] as const,
  celebrations: ['celebrations'] as const,
  games: ['games'] as const,
  art: ['art'] as const,
  simulationStatus: ['simulationStatus'] as const,
  saves: ['saves'] as const,
};

// Core World State Hooks
export function useServerStatus(options?: Omit<UseQueryOptions<ServerStatusResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.serverStatus,
    queryFn: () => apiClient.getServerStatus(),
    refetchInterval: 5000, // Refresh every 5 seconds
    ...options,
  });
}

export function useWorld(options?: Omit<UseQueryOptions<WorldResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.world,
    queryFn: () => apiClient.getWorld(),
    refetchInterval: 2000, // Refresh every 2 seconds
    ...options,
  });
}

export function useStats(options?: Omit<UseQueryOptions<StatsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: () => apiClient.getStats(),
    refetchInterval: 5000,
    ...options,
  });
}

export function useAgents(options?: Omit<UseQueryOptions<AgentsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: () => apiClient.getAgents(),
    refetchInterval: 3000,
    ...options,
  });
}

export function useAgent(id: string, options?: Omit<UseQueryOptions<AgentDetailResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.agent(id),
    queryFn: () => apiClient.getAgent(id),
    enabled: !!id,
    refetchInterval: 3000,
    ...options,
  });
}

// Advanced Systems Hooks
export function useAgentProfile(id: string, options?: Omit<UseQueryOptions<AgentProfile>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.agentProfile(id),
    queryFn: () => apiClient.getAgentProfile(id),
    enabled: !!id,
    refetchInterval: 5000,
    ...options,
  });
}

export function useAgentInventory(id: string, options?: Omit<UseQueryOptions<InventoryResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.agentInventory(id),
    queryFn: () => apiClient.getAgentInventory(id),
    enabled: !!id,
    refetchInterval: 5000,
    ...options,
  });
}

export function useAgentFunStats(id: string, options?: Omit<UseQueryOptions<AgentFunStatsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.agentFunStats(id),
    queryFn: () => apiClient.getAgentFunStats(id),
    enabled: !!id,
    refetchInterval: 10000,
    ...options,
  });
}

export function useEvents(limit = 50, minImportance = 1, options?: Omit<UseQueryOptions<EventsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: ['events', limit, minImportance] as const,
    queryFn: () => apiClient.getEvents(limit, minImportance),
    refetchInterval: 5000,
    ...options,
  });
}

export function useStories(options?: Omit<UseQueryOptions<StoriesResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.stories,
    queryFn: () => apiClient.getStories(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useAchievements(options?: Omit<UseQueryOptions<AchievementsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.achievements,
    queryFn: () => apiClient.getAchievements(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useConsequences(options?: Omit<UseQueryOptions<ConsequencesResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.consequences,
    queryFn: () => apiClient.getConsequences(),
    refetchInterval: 5000,
    ...options,
  });
}

export function useBuildings(options?: Omit<UseQueryOptions<BuildingsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.buildings,
    queryFn: () => apiClient.getBuildings(),
    refetchInterval: 5000,
    ...options,
  });
}

export function useExperiments(options?: Omit<UseQueryOptions<ExperimentsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.experiments,
    queryFn: () => apiClient.getExperiments(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useInnovations(options?: Omit<UseQueryOptions<InnovationsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.innovations,
    queryFn: () => apiClient.getInnovations(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useConflicts(options?: Omit<UseQueryOptions<ConflictsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.conflicts,
    queryFn: () => apiClient.getConflicts(),
    refetchInterval: 5000,
    ...options,
  });
}

export function useGovernments(options?: Omit<UseQueryOptions<GovernmentsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.governments,
    queryFn: () => apiClient.getGovernments(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useKnowledge(options?: Omit<UseQueryOptions<KnowledgeResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.knowledge,
    queryFn: () => apiClient.getKnowledge(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useLibraries(options?: Omit<UseQueryOptions<LibrariesResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.libraries,
    queryFn: () => apiClient.getLibraries(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useTeachingSessions(options?: Omit<UseQueryOptions<TeachingResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.teachingSessions,
    queryFn: () => apiClient.getTeachingSessions(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useRoles(options?: Omit<UseQueryOptions<RolesResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.roles,
    queryFn: () => apiClient.getRoles(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useEconomy(options?: Omit<UseQueryOptions<EconomyResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.economy,
    queryFn: () => apiClient.getEconomy(),
    refetchInterval: 5000,
    ...options,
  });
}

export function useMaterials(options?: Omit<UseQueryOptions<MaterialsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.materials,
    queryFn: () => apiClient.getMaterials(),
    staleTime: 60000, // Materials don't change often
    ...options,
  });
}

export function useRecipes(options?: Omit<UseQueryOptions<RecipesResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.recipes,
    queryFn: () => apiClient.getRecipes(),
    staleTime: 60000,
    ...options,
  });
}

export function useFunStats(options?: Omit<UseQueryOptions<FunStatsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.funStats,
    queryFn: () => apiClient.getFunStats(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useCelebrations(options?: Omit<UseQueryOptions<CelebrationsResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.celebrations,
    queryFn: () => apiClient.getCelebrations(),
    refetchInterval: 5000,
    ...options,
  });
}

export function useGames(options?: Omit<UseQueryOptions<GamesResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.games,
    queryFn: () => apiClient.getGames(),
    refetchInterval: 5000,
    ...options,
  });
}

export function useArt(options?: Omit<UseQueryOptions<ArtResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.art,
    queryFn: () => apiClient.getArt(),
    refetchInterval: 10000,
    ...options,
  });
}

export function useSimulationStatus(options?: Omit<UseQueryOptions<SimulationStatusResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.simulationStatus,
    queryFn: () => apiClient.getSimulationStatus(),
    refetchInterval: 2000,
    ...options,
  });
}

export function useSaves(options?: Omit<UseQueryOptions<SavesResponse>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.saves,
    queryFn: () => apiClient.getSaves(),
    ...options,
  });
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export function useCreateCharacter(options?: UseMutationOptions<CreateCharacterResponse, Error, CreateCharacterRequest>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCharacterRequest) => apiClient.createCharacter(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents });
      queryClient.invalidateQueries({ queryKey: queryKeys.world });
      queryClient.invalidateQueries({ queryKey: queryKeys.stats });
    },
    ...options,
  });
}

export function usePauseSimulation(options?: UseMutationOptions<PauseResponse, Error, void>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.pauseSimulation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.simulationStatus });
    },
    ...options,
  });
}

export function useSetSimulationSpeed(options?: UseMutationOptions<SetSpeedResponse, Error, SetSpeedRequest>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SetSpeedRequest) => apiClient.setSimulationSpeed(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.simulationStatus });
    },
    ...options,
  });
}

export function useTriggerDisaster(options?: UseMutationOptions<TriggerDisasterResponse, Error, TriggerDisasterRequest>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TriggerDisasterRequest) => apiClient.triggerDisaster(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.world });
      queryClient.invalidateQueries({ queryKey: queryKeys.events });
      queryClient.invalidateQueries({ queryKey: queryKeys.stats });
    },
    ...options,
  });
}

export function useCreateSave(options?: UseMutationOptions<CreateSaveResponse, Error, CreateSaveRequest>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSaveRequest) => apiClient.createSave(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.saves });
    },
    ...options,
  });
}

export function useLoadSave(options?: UseMutationOptions<LoadSaveResponse, Error, string>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.loadSave(id),
    onSuccess: () => {
      // Invalidate all queries since world state changed
      queryClient.invalidateQueries();
    },
    ...options,
  });
}

export function useDeleteSave(options?: UseMutationOptions<DeleteSaveResponse, Error, string>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteSave(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.saves });
    },
    ...options,
  });
}

export function useResetWorld(options?: UseMutationOptions<ResetWorldResponse, Error, void>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.resetWorld(),
    onSuccess: () => {
      // Invalidate all queries since world was reset
      queryClient.invalidateQueries();
    },
    ...options,
  });
}

// ============================================================================
// EXPORTS
// ============================================================================

export { apiClient };
export default apiClient;
