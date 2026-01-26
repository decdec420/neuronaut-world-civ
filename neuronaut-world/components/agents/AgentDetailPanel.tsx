'use client';

import {
  X, Heart, Coins, Calendar, Activity, Brain, Zap, TrendingUp,
  Target, MapPin, Users, Star, Award, Flame, Sparkles, Trophy,
  Footprints, Clock, BarChart3, PieChart, LineChart
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  position: { x: number; y: number };
  wealth: number;
  health: number;
  age: number;
  alive: boolean;
}

interface AgentDetailPanelProps {
  agent: Agent;
  onClose: () => void;
}

// Helper functions for derived stats
const getWealthTier = (wealth: number): { tier: string; color: string; icon: string } => {
  if (wealth >= 200) return { tier: 'Elite', color: '#fbbf24', icon: '👑' };
  if (wealth >= 150) return { tier: 'Rich', color: '#f59e0b', icon: '💎' };
  if (wealth >= 100) return { tier: 'Prosperous', color: '#eab308', icon: '💰' };
  if (wealth >= 50) return { tier: 'Comfortable', color: '#84cc16', icon: '🏠' };
  if (wealth >= 25) return { tier: 'Modest', color: '#22c55e', icon: '🌾' };
  return { tier: 'Poor', color: '#64748b', icon: '🥔' };
};

const getHealthStatus = (health: number): { status: string; color: string; icon: string } => {
  if (health >= 90) return { status: 'Excellent', color: '#10b981', icon: '💪' };
  if (health >= 70) return { status: 'Good', color: '#22c55e', icon: '✅' };
  if (health >= 50) return { status: 'Fair', color: '#f59e0b', icon: '⚠️' };
  if (health >= 30) return { status: 'Poor', color: '#ef4444', icon: '🩹' };
  return { status: 'Critical', color: '#dc2626', icon: '☠️' };
};

const getAgeCategory = (age: number): { category: string; color: string; icon: string } => {
  if (age >= 60) return { category: 'Elder', color: '#a78bfa', icon: '🧓' };
  if (age >= 40) return { category: 'Middle Age', color: '#60a5fa', icon: '🧑' };
  if (age >= 18) return { category: 'Adult', color: '#22d3ee', icon: '👨' };
  if (age >= 13) return { category: 'Teen', color: '#4ade80', icon: '🧒' };
  return { category: 'Child', color: '#fbbf24', icon: '👶' };
};

export default function AgentDetailPanel({ agent, onClose }: AgentDetailPanelProps) {
  const wealthTier = getWealthTier(agent.wealth);
  const healthStatus = getHealthStatus(agent.health);
  const ageCategory = getAgeCategory(agent.age);

  // Derived stats
  const totalLifespan = 80; // years
  const lifeProgress = (agent.age / totalLifespan) * 100;
  const healthScore = Math.floor((agent.health / 100) * 10);
  const wealthRank = Math.floor((agent.wealth / 250) * 100);

  return (
    <div className="h-full flex flex-col overflow-hidden" style={{
      background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      border: '1px solid rgba(100, 116, 139, 0.3)',
    }}>
      {/* Animated Header */}
      <div className="relative p-6 pb-4 border-b" style={{ borderColor: 'rgba(100, 116, 139, 0.3)' }}>
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-5" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.5) 1px, transparent 0)`,
          backgroundSize: '32px 32px',
        }} />

        <div className="relative flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-3xl font-bold" style={{
                background: 'linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                {agent.name}
              </h2>
              <div className="flex gap-1">
                {agent.wealth > 120 && <span className="text-2xl animate-pulse">👑</span>}
                {agent.health > 90 && <span className="text-2xl">💪</span>}
                {agent.age > 50 && <span className="text-2xl">🧓</span>}
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm" style={{ color: 'rgba(203, 213, 225, 0.7)' }}>
              <span className="font-mono">ID: {agent.id}</span>
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                ({agent.position.x.toFixed(1)}, {agent.position.y.toFixed(1)})
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-all hover:scale-110"
            style={{
              background: 'rgba(100, 116, 139, 0.2)',
              border: '1px solid rgba(100, 116, 139, 0.3)',
            }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Primary Stats with Progress Bars */}
        <div className="space-y-3">
          <StatWithBar
            icon={<Heart className="w-5 h-5" />}
            label="Health"
            value={agent.health}
            max={100}
            color={healthStatus.color}
            suffix={`${healthStatus.icon} ${healthStatus.status}`}
          />
          <StatWithBar
            icon={<Coins className="w-5 h-5" />}
            label="Wealth"
            value={agent.wealth}
            max={250}
            color={wealthTier.color}
            suffix={`${wealthTier.icon} ${wealthTier.tier}`}
          />
          <StatWithBar
            icon={<Calendar className="w-5 h-5" />}
            label="Age"
            value={agent.age}
            max={totalLifespan}
            color={ageCategory.color}
            suffix={`${ageCategory.icon} ${ageCategory.category}`}
          />
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-3 gap-3">
          <QuickStat icon={<Star className="w-4 h-4" />} label="Score" value={healthScore.toString()} color="#fbbf24" />
          <QuickStat icon={<TrendingUp className="w-4 h-4" />} label="Rank" value={`${wealthRank}%`} color="#22d3ee" />
          <QuickStat icon={<Activity className="w-4 h-4" />} label="Status" value={agent.alive ? '🟢 Live' : '🔴 Dead'} color={agent.alive ? '#22c55e' : '#ef4444'} />
        </div>

        {/* Attributes Section */}
        <InfoSection title="🧬 Attributes" icon={<Brain className="w-5 h-5" />}>
          <div className="grid grid-cols-2 gap-3">
            <AttributeBar label="Strength" value={Math.floor(agent.health * 0.8)} color="#ef4444" />
            <AttributeBar label="Intelligence" value={Math.floor(65 + (agent.age * 0.5))} color="#3b82f6" />
            <AttributeBar label="Charisma" value={Math.floor(50 + (agent.wealth * 0.2))} color="#a78bfa" />
            <AttributeBar label="Luck" value={Math.floor(40 + Math.random() * 30)} color="#22c55e" />
          </div>
        </InfoSection>

        {/* Needs & Resources */}
        <InfoSection title="📊 Needs & Resources" icon={<BarChart3 className="w-5 h-5" />}>
          <div className="space-y-2">
            <NeedBar label="🍖 Food" value={75} urgent={false} />
            <NeedBar label="💧 Water" value={85} urgent={false} />
            <NeedBar label="😊 Happiness" value={60} urgent={false} />
            <NeedBar label="⚡ Energy" value={45} urgent={true} />
          </div>
        </InfoSection>

        {/* Current Activity */}
        <InfoSection title="🎯 Current Activity" icon={<Target className="w-5 h-5" />} highlight>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: 'rgba(167, 139, 250, 0.1)', border: '1px solid rgba(167, 139, 250, 0.3)' }}>
              <div className="text-3xl animate-bounce">🚶</div>
              <div className="flex-1">
                <div className="font-semibold" style={{ color: '#a78bfa' }}>Wandering</div>
                <div className="text-xs" style={{ color: 'rgba(203, 213, 225, 0.7)' }}>Exploring the world, looking for resources</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2 p-2 rounded" style={{ background: 'rgba(100, 116, 139, 0.2)' }}>
                <Footprints className="w-4 h-4" style={{ color: '#60a5fa' }} />
                <span style={{ color: 'rgba(203, 213, 225, 0.9)' }}>Distance: 42m</span>
              </div>
              <div className="flex items-center gap-2 p-2 rounded" style={{ background: 'rgba(100, 116, 139, 0.2)' }}>
                <Clock className="w-4 h-4" style={{ color: '#22d3ee' }} />
                <span style={{ color: 'rgba(203, 213, 225, 0.9)' }}>Duration: 2m</span>
              </div>
            </div>
          </div>
        </InfoSection>

        {/* Recent Actions Log */}
        <InfoSection title="📜 Recent Actions" icon={<Activity className="w-5 h-5" />}>
          <div className="space-y-2">
            <ActionLog action="Gathered 5 berries" time="2m ago" icon="🫐" color="#22c55e" />
            <ActionLog action="Moved to new location" time="5m ago" icon="🗺️" color="#3b82f6" />
            <ActionLog action="Rested to recover health" time="8m ago" icon="😴" color="#a78bfa" />
            <ActionLog action="Found 12 coins" time="12m ago" icon="💰" color="#fbbf24" />
          </div>
        </InfoSection>

        {/* Relationships */}
        <InfoSection title="👥 Relationships" icon={<Users className="w-5 h-5" />}>
          <div className="space-y-2">
            <RelationshipCard name="Bob" status="Friend" sentiment={85} />
            <RelationshipCard name="Diana" status="Acquaintance" sentiment={45} />
            <RelationshipCard name="Eve" status="Rival" sentiment={-30} />
          </div>
        </InfoSection>

        {/* Achievements */}
        <InfoSection title="🏆 Achievements" icon={<Trophy className="w-5 h-5" />}>
          <div className="grid grid-cols-2 gap-2">
            <Achievement icon="🌟" label="First Steps" unlocked />
            <Achievement icon="💎" label="Wealthy" unlocked={agent.wealth > 100} />
            <Achievement icon="🧓" label="Elder" unlocked={agent.age > 50} />
            <Achievement icon="❤️" label="Survivor" unlocked={agent.health > 90} />
          </div>
        </InfoSection>

        {/* AI Thoughts (Simulated) */}
        <InfoSection title="🧠 AI Thoughts" icon={<Brain className="w-5 h-5" />} highlight>
          <div className="p-4 rounded-lg space-y-3" style={{
            background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.1) 0%, rgba(96, 165, 250, 0.1) 100%)',
            border: '1px solid rgba(167, 139, 250, 0.3)',
          }}>
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 mt-1 text-purple-400 animate-pulse" />
              <div className="flex-1 text-sm" style={{ color: 'rgba(203, 213, 225, 0.9)', lineHeight: '1.6' }}>
                <em>"I should focus on gathering more resources. My energy is running low, and I noticed Bob found some good spots earlier. Maybe I should explore the forest biome to the east..."</em>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap text-xs">
              <Tag label="⚡ Low Energy" color="#f59e0b" />
              <Tag label="🎯 Resource Seeking" color="#22d3ee" />
              <Tag label="🤔 Strategic" color="#a78bfa" />
            </div>
          </div>
        </InfoSection>

        {/* Performance Metrics */}
        <InfoSection title="📈 Performance Metrics" icon={<LineChart className="w-5 h-5" />}>
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="Survival" value="12 days" icon="⏱️" />
            <MetricCard label="Resources" value="247 total" icon="📦" />
            <MetricCard label="Distance" value="1.2 km" icon="🗺️" />
            <MetricCard label="Interactions" value="34 times" icon="💬" />
          </div>
        </InfoSection>
      </div>
    </div>
  );
}

// Component: Stat with Progress Bar
function StatWithBar({ icon, label, value, max, color, suffix }: {
  icon: React.ReactNode;
  label: string;
  value: number;
  max: number;
  color: string;
  suffix: string;
}) {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className="p-4 rounded-lg" style={{
      background: 'rgba(100, 116, 139, 0.15)',
      border: '1px solid rgba(100, 116, 139, 0.3)',
    }}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span style={{ color }}>{icon}</span>
          <span className="text-sm font-semibold" style={{ color: 'rgba(203, 213, 225, 0.9)' }}>{label}</span>
        </div>
        <span className="text-sm font-mono font-bold" style={{ color }}>{value}/{max}</span>
      </div>
      <div className="relative w-full h-2 rounded-full mb-2" style={{ background: 'rgba(100, 116, 139, 0.3)' }}>
        <div
          className="absolute top-0 left-0 h-full rounded-full transition-all duration-500"
          style={{
            width: `${percentage}%`,
            background: `linear-gradient(90deg, ${color}dd 0%, ${color} 100%)`,
            boxShadow: `0 0 8px ${color}66`,
          }}
        />
      </div>
      <div className="text-xs" style={{ color: 'rgba(148, 163, 184, 0.8)' }}>{suffix}</div>
    </div>
  );
}

// Component: Quick Stat Card
function QuickStat({ icon, label, value, color }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="p-3 rounded-lg text-center" style={{
      background: `${color}15`,
      border: `1px solid ${color}40`,
    }}>
      <div className="flex justify-center mb-1" style={{ color }}>{icon}</div>
      <div className="text-xs" style={{ color: 'rgba(148, 163, 184, 0.8)' }}>{label}</div>
      <div className="text-sm font-bold mt-1" style={{ color }}>{value}</div>
    </div>
  );
}

// Component: Info Section
function InfoSection({ title, icon, children, highlight = false }: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-lg p-4" style={{
      background: highlight
        ? 'linear-gradient(135deg, rgba(167, 139, 250, 0.08) 0%, rgba(96, 165, 250, 0.08) 100%)'
        : 'rgba(100, 116, 139, 0.1)',
      border: highlight
        ? '1px solid rgba(167, 139, 250, 0.3)'
        : '1px solid rgba(100, 116, 139, 0.2)',
    }}>
      <div className="flex items-center gap-2 mb-3">
        <span style={{ color: highlight ? '#a78bfa' : '#60a5fa' }}>{icon}</span>
        <h3 className="text-sm font-bold" style={{
          color: highlight ? '#a78bfa' : 'rgba(203, 213, 225, 0.9)',
        }}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

// Component: Attribute Bar
function AttributeBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span style={{ color: 'rgba(203, 213, 225, 0.9)' }}>{label}</span>
        <span style={{ color }}>{value}</span>
      </div>
      <div className="w-full h-1.5 rounded-full" style={{ background: 'rgba(100, 116, 139, 0.3)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${value}%`,
            background: color,
            boxShadow: `0 0 6px ${color}66`,
          }}
        />
      </div>
    </div>
  );
}

// Component: Need Bar
function NeedBar({ label, value, urgent }: { label: string; value: number; urgent: boolean }) {
  const color = urgent ? '#ef4444' : value > 70 ? '#22c55e' : value > 40 ? '#f59e0b' : '#ef4444';

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm w-24">{label}</span>
      <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(100, 116, 139, 0.3)' }}>
        <div
          className={`h-full rounded-full transition-all duration-300 ${urgent ? 'animate-pulse' : ''}`}
          style={{
            width: `${value}%`,
            background: color,
            boxShadow: urgent ? `0 0 8px ${color}` : 'none',
          }}
        />
      </div>
      <span className="text-xs font-mono w-10 text-right" style={{ color }}>{value}%</span>
    </div>
  );
}

// Component: Action Log
function ActionLog({ action, time, icon, color }: {
  action: string;
  time: string;
  icon: string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3 p-2 rounded" style={{ background: 'rgba(100, 116, 139, 0.15)' }}>
      <span className="text-xl">{icon}</span>
      <div className="flex-1">
        <div className="text-sm" style={{ color: 'rgba(203, 213, 225, 0.9)' }}>{action}</div>
        <div className="text-xs" style={{ color: 'rgba(148, 163, 184, 0.7)' }}>{time}</div>
      </div>
      <div className="w-1 h-8 rounded-full" style={{ background: color }} />
    </div>
  );
}

// Component: Relationship Card
function RelationshipCard({ name, status, sentiment }: {
  name: string;
  status: string;
  sentiment: number;
}) {
  const color = sentiment > 50 ? '#22c55e' : sentiment > 0 ? '#f59e0b' : '#ef4444';
  const icon = sentiment > 50 ? '❤️' : sentiment > 0 ? '👋' : '⚔️';

  return (
    <div className="flex items-center justify-between p-3 rounded-lg" style={{
      background: 'rgba(100, 116, 139, 0.15)',
      border: `1px solid ${color}40`,
    }}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="text-sm font-semibold" style={{ color: 'rgba(203, 213, 225, 0.9)' }}>{name}</div>
          <div className="text-xs" style={{ color: 'rgba(148, 163, 184, 0.7)' }}>{status}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-xs font-mono font-bold" style={{ color }}>{sentiment > 0 ? '+' : ''}{sentiment}</div>
        <div className="w-16 h-1 rounded-full mt-1" style={{ background: 'rgba(100, 116, 139, 0.3)' }}>
          <div
            className="h-full rounded-full"
            style={{
              width: `${Math.abs(sentiment)}%`,
              background: color,
            }}
          />
        </div>
      </div>
    </div>
  );
}

// Component: Achievement
function Achievement({ icon, label, unlocked }: { icon: string; label: string; unlocked: boolean }) {
  return (
    <div
      className="flex items-center gap-2 p-2 rounded-lg transition-all"
      style={{
        background: unlocked ? 'rgba(167, 139, 250, 0.15)' : 'rgba(100, 116, 139, 0.1)',
        border: unlocked ? '1px solid rgba(167, 139, 250, 0.4)' : '1px solid rgba(100, 116, 139, 0.2)',
        opacity: unlocked ? 1 : 0.5,
      }}
    >
      <span className="text-xl" style={{ filter: unlocked ? 'none' : 'grayscale(100%)' }}>{icon}</span>
      <span className="text-xs" style={{ color: unlocked ? '#a78bfa' : 'rgba(148, 163, 184, 0.7)' }}>{label}</span>
    </div>
  );
}

// Component: Tag
function Tag({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="px-2 py-1 rounded-full text-xs font-semibold"
      style={{
        background: `${color}20`,
        color,
        border: `1px solid ${color}40`,
      }}
    >
      {label}
    </span>
  );
}

// Component: Metric Card
function MetricCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="p-3 rounded-lg" style={{
      background: 'rgba(100, 116, 139, 0.15)',
      border: '1px solid rgba(100, 116, 139, 0.25)',
    }}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs" style={{ color: 'rgba(148, 163, 184, 0.8)' }}>{label}</span>
        <span className="text-lg">{icon}</span>
      </div>
      <div className="text-lg font-bold" style={{ color: '#60a5fa' }}>{value}</div>
    </div>
  );
}
