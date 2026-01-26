/**
 * View Modes & Display Settings
 *
 * Controls what information is visible on the world canvas.
 */

export type ViewMode =
  | 'normal'      // Balanced view with moderate detail
  | 'agents'      // Focus on agents, minimize building details
  | 'buildings'   // Focus on buildings and construction
  | 'resources'   // Highlight resource nodes and gathering
  | 'technology'  // Color-code by tech level
  | 'economy';    // Size by wealth, show trade

export type DetailLevel = 'minimal' | 'medium' | 'full';

export interface ViewSettings {
  mode: ViewMode;
  detailLevel: DetailLevel;
  showAgentNames: boolean;
  showAgentActivities: boolean;
  showAgentHealth: boolean;
  showBuildingOwners: boolean;
  showBuildingProgress: boolean;
  showResourceNodes: boolean;
  showResourceQuantities: boolean;
  hoverOnly: boolean; // Only show labels on hover
}

export const DEFAULT_VIEW_SETTINGS: ViewSettings = {
  mode: 'normal',
  detailLevel: 'medium',
  showAgentNames: false, // Changed to false for cleaner look
  showAgentActivities: true,
  showAgentHealth: true,
  showBuildingOwners: false, // Changed to false
  showBuildingProgress: true,
  showResourceNodes: true,
  showResourceQuantities: false,
  hoverOnly: true, // Enable hover-based labels
};

export const VIEW_MODE_PRESETS: Record<ViewMode, Partial<ViewSettings>> = {
  normal: {
    showAgentNames: false,
    showAgentActivities: true,
    showAgentHealth: true,
    showBuildingOwners: false,
    showBuildingProgress: true,
    showResourceNodes: true,
    hoverOnly: true,
  },
  agents: {
    showAgentNames: true,
    showAgentActivities: true,
    showAgentHealth: true,
    showBuildingOwners: false,
    showBuildingProgress: false,
    showResourceNodes: false,
    hoverOnly: false,
  },
  buildings: {
    showAgentNames: false,
    showAgentActivities: false,
    showAgentHealth: false,
    showBuildingOwners: true,
    showBuildingProgress: true,
    showResourceNodes: false,
    hoverOnly: true,
  },
  resources: {
    showAgentNames: false,
    showAgentActivities: false,
    showAgentHealth: false,
    showBuildingOwners: false,
    showBuildingProgress: false,
    showResourceNodes: true,
    showResourceQuantities: true,
    hoverOnly: true,
  },
  technology: {
    showAgentNames: true,
    showAgentActivities: false,
    showAgentHealth: false,
    showBuildingOwners: false,
    showBuildingProgress: false,
    showResourceNodes: false,
    hoverOnly: false,
  },
  economy: {
    showAgentNames: false,
    showAgentActivities: false,
    showAgentHealth: false,
    showBuildingOwners: true,
    showBuildingProgress: false,
    showResourceNodes: false,
    hoverOnly: true,
  },
};

export function getViewSettings(mode: ViewMode): ViewSettings {
  return {
    ...DEFAULT_VIEW_SETTINGS,
    ...VIEW_MODE_PRESETS[mode],
    mode,
  };
}

export function getDetailLevelFromZoom(zoom: number): DetailLevel {
  if (zoom < 0.5) return 'minimal';
  if (zoom > 1.5) return 'full';
  return 'medium';
}
