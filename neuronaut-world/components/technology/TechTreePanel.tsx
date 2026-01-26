/**
 * Technology Tree Panel
 *
 * Displays the technology tree with visual progression.
 * Shows unlocked, available, and locked technologies.
 */

'use client';

import React from 'react';
import type { TechnologyId, TechnologyEra, TechnologyCategory, AgentKnowledge } from '@/types/technology';
import { getTechnology, getTechnologiesByEra, TECHNOLOGY_TREE } from '@/types/technology';

interface TechTreePanelProps {
  agentKnowledge: AgentKnowledge | null;
  onClose: () => void;
  onResearchTech?: (techId: TechnologyId) => void;
}

export default function TechTreePanel({ agentKnowledge, onClose, onResearchTech }: TechTreePanelProps) {
  if (!agentKnowledge) return null;

  const eras: TechnologyEra[] = ['stone_age', 'early_civilization', 'bronze_age', 'iron_age', 'classical_era'];

  const eraNames: Record<TechnologyEra, string> = {
    stone_age: 'Stone Age',
    early_civilization: 'Early Civilization',
    bronze_age: 'Bronze Age',
    iron_age: 'Iron Age',
    classical_era: 'Classical Era',
  };

  const eraColors: Record<TechnologyEra, string> = {
    stone_age: '#a78bfa',
    early_civilization: '#60a5fa',
    bronze_age: '#fbbf24',
    iron_age: '#f59e0b',
    classical_era: '#ec4899',
  };

  const categoryIcons: Record<TechnologyCategory, string> = {
    survival: '🔥',
    construction: '🏗️',
    production: '⚙️',
    military: '⚔️',
    science: '🔬',
  };

  const getTechStatus = (techId: TechnologyId) => {
    // Discovered
    if (agentKnowledge.discoveredTechnologies.has(techId)) {
      return 'discovered';
    }

    // Currently researching
    if (agentKnowledge.researchingTechnology === techId) {
      return 'researching';
    }

    // Available (prerequisites met)
    const tech = getTechnology(techId);
    const hasPrereqs = tech.prerequisites.every(prereq =>
      agentKnowledge.discoveredTechnologies.has(prereq)
    );

    if (hasPrereqs) {
      return 'available';
    }

    // Locked
    return 'locked';
  };

  return (
    <div
      className="h-full flex flex-col overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
        backdropFilter: 'blur(20px)',
      }}
    >
      {/* Header */}
      <div
        className="flex-shrink-0 p-6 relative"
        style={{
          background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.2) 0%, rgba(96, 165, 250, 0.2) 100%)',
          borderBottom: '1px solid rgba(100, 116, 139, 0.3)',
        }}
      >
        {/* Background pattern */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `radial-gradient(circle at 20% 50%, rgba(167, 139, 250, 0.3) 0%, transparent 50%),
                            radial-gradient(circle at 80% 50%, rgba(96, 165, 250, 0.3) 0%, transparent 50%)`,
          }}
        />

        <div className="relative flex items-center justify-between">
          <div>
            <h2
              className="text-2xl font-bold"
              style={{
                background: 'linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              🔬 Technology Tree
            </h2>
            <p className="text-sm mt-1" style={{ color: 'rgba(203, 213, 225, 0.8)' }}>
              Agent {agentKnowledge.agentId} • {agentKnowledge.discoveredTechnologies.size} / {Object.keys(TECHNOLOGY_TREE).length} Discovered
            </p>
          </div>

          <button
            onClick={onClose}
            className="hover:scale-110 transition-transform"
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.5)',
              color: '#ef4444',
              fontSize: '18px',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        {/* Currently Researching Banner */}
        {agentKnowledge.researchingTechnology && (
          <div
            className="mt-4 p-3 rounded-lg"
            style={{
              background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(147, 51, 234, 0.3) 100%)',
              border: '1px solid rgba(168, 85, 247, 0.5)',
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold" style={{ color: '#a855f7' }}>
                  🔬 Currently Researching
                </div>
                <div className="text-xs mt-1" style={{ color: 'rgba(203, 213, 225, 0.9)' }}>
                  {getTechnology(agentKnowledge.researchingTechnology).name}
                </div>
              </div>
              <div className="text-lg font-bold" style={{ color: '#a855f7' }}>
                {Math.floor(agentKnowledge.researchProgress)}%
              </div>
            </div>
            <div
              className="mt-2 w-full h-2 rounded-full"
              style={{ background: 'rgba(100, 116, 139, 0.3)' }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${agentKnowledge.researchProgress}%`,
                  background: 'linear-gradient(90deg, #a855f7 0%, #9333ea 100%)',
                  boxShadow: '0 0 8px rgba(168, 85, 247, 0.6)',
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Tech Tree Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {eras.map(era => {
          const techs = getTechnologiesByEra(era);
          const discoveredInEra = techs.filter(tech =>
            agentKnowledge.discoveredTechnologies.has(tech.id)
          ).length;

          return (
            <div key={era} className="space-y-3">
              {/* Era Header */}
              <div
                className="flex items-center justify-between p-3 rounded-lg"
                style={{
                  background: `linear-gradient(135deg, ${eraColors[era]}20 0%, ${eraColors[era]}10 100%)`,
                  border: `1px solid ${eraColors[era]}40`,
                }}
              >
                <div className="font-bold" style={{ color: eraColors[era] }}>
                  {eraNames[era]}
                </div>
                <div className="text-sm" style={{ color: eraColors[era] }}>
                  {discoveredInEra} / {techs.length}
                </div>
              </div>

              {/* Technologies in Era */}
              <div className="grid grid-cols-2 gap-3">
                {techs.map(tech => {
                  const status = getTechStatus(tech.id);

                  const statusStyles = {
                    discovered: {
                      bg: 'linear-gradient(135deg, rgba(34, 197, 94, 0.3) 0%, rgba(22, 163, 74, 0.3) 100%)',
                      border: '2px solid rgba(34, 197, 94, 0.6)',
                      opacity: 1,
                      cursor: 'default',
                    },
                    researching: {
                      bg: 'linear-gradient(135deg, rgba(168, 85, 247, 0.4) 0%, rgba(147, 51, 234, 0.4) 100%)',
                      border: '2px solid rgba(168, 85, 247, 0.8)',
                      opacity: 1,
                      cursor: 'default',
                    },
                    available: {
                      bg: 'linear-gradient(135deg, rgba(96, 165, 250, 0.3) 0%, rgba(59, 130, 246, 0.3) 100%)',
                      border: '2px solid rgba(96, 165, 250, 0.6)',
                      opacity: 1,
                      cursor: 'pointer',
                    },
                    locked: {
                      bg: 'linear-gradient(135deg, rgba(71, 85, 105, 0.2) 0%, rgba(51, 65, 85, 0.2) 100%)',
                      border: '1px solid rgba(100, 116, 139, 0.3)',
                      opacity: 0.5,
                      cursor: 'not-allowed',
                    },
                  };

                  const style = statusStyles[status];

                  return (
                    <div
                      key={tech.id}
                      className="p-3 rounded-lg transition-all hover:scale-105"
                      style={{
                        background: style.bg,
                        border: style.border,
                        opacity: style.opacity,
                        cursor: style.cursor,
                      }}
                      onClick={() => {
                        if (status === 'available' && onResearchTech) {
                          onResearchTech(tech.id);
                        }
                      }}
                      title={tech.description}
                    >
                      <div className="flex items-start justify-between">
                        <div className="text-2xl">{tech.icon}</div>
                        <div className="text-xs" style={{ color: 'rgba(203, 213, 225, 0.7)' }}>
                          {categoryIcons[tech.category]}
                        </div>
                      </div>
                      <div className="mt-2 text-sm font-semibold" style={{ color: '#ffffff' }}>
                        {tech.name}
                      </div>
                      <div className="mt-1 text-xs" style={{ color: 'rgba(203, 213, 225, 0.8)' }}>
                        {tech.description.substring(0, 50)}...
                      </div>

                      {/* Status Badge */}
                      <div className="mt-2">
                        {status === 'discovered' && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-full"
                            style={{
                              background: 'rgba(34, 197, 94, 0.3)',
                              color: '#22c55e',
                              border: '1px solid rgba(34, 197, 94, 0.5)',
                            }}
                          >
                            ✓ Discovered
                          </span>
                        )}
                        {status === 'researching' && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-full animate-pulse"
                            style={{
                              background: 'rgba(168, 85, 247, 0.3)',
                              color: '#a855f7',
                              border: '1px solid rgba(168, 85, 247, 0.5)',
                            }}
                          >
                            🔬 Researching
                          </span>
                        )}
                        {status === 'available' && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-full"
                            style={{
                              background: 'rgba(96, 165, 250, 0.3)',
                              color: '#60a5fa',
                              border: '1px solid rgba(96, 165, 250, 0.5)',
                            }}
                          >
                            🔓 Available
                          </span>
                        )}
                        {status === 'locked' && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-full"
                            style={{
                              background: 'rgba(100, 116, 139, 0.2)',
                              color: '#64748b',
                              border: '1px solid rgba(100, 116, 139, 0.3)',
                            }}
                          >
                            🔒 Locked
                          </span>
                        )}
                      </div>

                      {/* Cost Preview (for available techs) */}
                      {status === 'available' && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {Object.entries(tech.researchCost).map(([resource, cost]) => (
                            <span
                              key={resource}
                              className="text-xs px-1.5 py-0.5 rounded"
                              style={{
                                background: 'rgba(0, 0, 0, 0.3)',
                                color: 'rgba(255, 255, 255, 0.9)',
                              }}
                            >
                              {cost} {resource}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend Footer */}
      <div
        className="flex-shrink-0 p-4 flex gap-4 text-xs"
        style={{
          borderTop: '1px solid rgba(100, 116, 139, 0.3)',
          background: 'rgba(15, 23, 42, 0.5)',
          color: 'rgba(203, 213, 225, 0.7)',
        }}
      >
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ background: '#22c55e' }} />
          <span>Discovered</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ background: '#a855f7' }} />
          <span>Researching</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ background: '#60a5fa' }} />
          <span>Available</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ background: '#64748b' }} />
          <span>Locked</span>
        </div>
      </div>
    </div>
  );
}
