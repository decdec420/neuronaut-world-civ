'use client';

import { Play, Pause, FastForward } from 'lucide-react';
import { usePauseSimulation, useSetSimulationSpeed, useSimulationStatus } from '@/hooks/use-api-client';
import { useEffect } from 'react';

interface TimeControlsProps {
  isPaused: boolean;
  playbackSpeed: 1 | 2 | 4 | 8;
  onPlayPause: () => void;
  onSpeedChange: (speed: 1 | 2 | 4 | 8) => void;
}

export default function TimeControls({
  isPaused,
  playbackSpeed,
  onPlayPause,
  onSpeedChange,
}: TimeControlsProps) {
  const speeds: Array<1 | 2 | 4 | 8> = [1, 2, 4, 8];

  // API integration
  const pauseMutation = usePauseSimulation();
  const speedMutation = useSetSimulationSpeed();
  const { data: status } = useSimulationStatus();

  // Map frontend speed to backend speed names
  const getBackendSpeed = (speed: number): 'paused' | 'slow' | 'normal' | 'fast' | 'ultra' => {
    if (isPaused) return 'paused';
    switch(speed) {
      case 1: return 'slow';
      case 2: return 'normal';
      case 4: return 'fast';
      case 8: return 'ultra';
      default: return 'normal';
    }
  };

  const handlePlayPause = () => {
    // Call backend API
    pauseMutation.mutate(!isPaused);
    // Update local state
    onPlayPause();
  };

  const handleSpeedChange = (speed: 1 | 2 | 4 | 8) => {
    // Call backend API
    const backendSpeed = getBackendSpeed(speed);
    speedMutation.mutate(backendSpeed);
    // Update local state
    onSpeedChange(speed);
  };

  return (
    <div className="glass-panel flex items-center justify-center gap-6">
      {/* Play/Pause Button */}
      <button
        onClick={handlePlayPause}
        className="p-4 rounded-full glass-hover bg-accent/20 hover:bg-accent/30 transition-all disabled:opacity-50"
        aria-label={isPaused ? 'Play' : 'Pause'}
        disabled={pauseMutation.isPending}
      >
        {isPaused ? <Play className="w-6 h-6 text-accent" /> : <Pause className="w-6 h-6 text-accent" />}
      </button>

      {/* Speed Controls */}
      <div className="flex items-center gap-2">
        <FastForward className="w-5 h-5 text-text-muted" />
        <div className="flex gap-2">
          {speeds.map((speed) => (
            <button
              key={speed}
              onClick={() => handleSpeedChange(speed)}
              disabled={speedMutation.isPending || isPaused}
              className={`px-4 py-2 rounded-lg transition-all disabled:opacity-50 ${
                playbackSpeed === speed
                  ? 'bg-accent text-white font-bold'
                  : 'glass-hover text-text-muted'
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Status */}
      <div className="text-text-muted">
        {isPaused ? '⏸️ Paused' : `▶️ Running at ${playbackSpeed}x`}
        {status && (
          <span className="ml-2 text-xs opacity-70">
            (Backend: {status.paused ? 'Paused' : 'Running'})
          </span>
        )}
      </div>
    </div>
  );
}
