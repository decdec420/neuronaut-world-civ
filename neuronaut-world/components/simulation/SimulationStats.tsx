'use client';

import { Users, Activity, Clock, Landmark } from 'lucide-react';

interface SimulationStatsProps {
  population: number;
  alive: number;
  currentTick: number;
  currentEra: string;
}

export default function SimulationStats({
  population,
  alive,
  currentTick,
  currentEra,
}: SimulationStatsProps) {
  return (
    <div className="glass-panel flex items-center gap-6">
      <StatItem icon={<Users />} label="Population" value={population.toString()} />
      <StatItem icon={<Activity />} label="Alive" value={alive.toString()} color="system-health" />
      <StatItem icon={<Clock />} label="Tick" value={currentTick.toString()} />
      <StatItem icon={<Landmark />} label="Era" value={currentEra} color="accent" />
    </div>
  );
}

function StatItem({
  icon,
  label,
  value,
  color = 'text',
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <div className={`text-${color}-muted`}>{icon}</div>
      <div>
        <div className="text-xs text-text-muted">{label}</div>
        <div className={`text-lg font-bold text-${color}`}>{value}</div>
      </div>
    </div>
  );
}
