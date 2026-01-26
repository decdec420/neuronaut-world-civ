import Link from 'next/link';
import { Play, Users, Brain, TrendingUp } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-background via-background to-purple-950/20 flex flex-col items-center justify-center p-8">
      {/* Hero Section */}
      <div className="max-w-5xl mx-auto text-center space-y-8">
        <h1 className="text-7xl font-bold bg-gradient-to-r from-accent-light via-purple-400 to-pink-400 bg-clip-text text-transparent animate-pulse-slow">
          Neuronaut World
        </h1>

        <p className="text-2xl text-text-muted max-w-2xl mx-auto">
          Watch autonomous AI civilizations evolve, trade, fight, and build their own societies
        </p>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
          <div className="glass-panel glass-hover">
            <Brain className="w-12 h-12 text-accent mb-4 mx-auto" />
            <h3 className="text-lg font-semibold mb-2">AI Autonomy</h3>
            <p className="text-sm text-text-muted">
              Agents make their own decisions based on personality and needs
            </p>
          </div>

          <div className="glass-panel glass-hover">
            <Users className="w-12 h-12 text-system-life mb-4 mx-auto" />
            <h3 className="text-lg font-semibold mb-2">Living Civilizations</h3>
            <p className="text-sm text-text-muted">
              Societies emerge organically from agent interactions
            </p>
          </div>

          <div className="glass-panel glass-hover">
            <TrendingUp className="w-12 h-12 text-system-economy mb-4 mx-auto" />
            <h3 className="text-lg font-semibold mb-2">Complex Economics</h3>
            <p className="text-sm text-text-muted">
              From barter to banking, watch economies evolve
            </p>
          </div>

          <div className="glass-panel glass-hover">
            <Play className="w-12 h-12 text-system-fun mb-4 mx-auto" />
            <h3 className="text-lg font-semibold mb-2">Emergent Drama</h3>
            <p className="text-sm text-text-muted">
              Tax revolts, religious conflicts, and unexpected events
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-12">
          <Link href="/simulation">
            <button className="glass-hover px-12 py-4 rounded-full text-xl font-bold bg-gradient-to-r from-accent to-purple-600 hover:scale-105 transition-transform duration-300 shadow-2xl">
              Enter the World
            </button>
          </Link>
        </div>

        {/* Stats Preview */}
        <div className="mt-16 glass-panel max-w-3xl mx-auto">
          <h3 className="text-lg font-semibold mb-4 text-accent">
            10 Integrated Systems
          </h3>
          <div className="flex flex-wrap gap-3 justify-center">
            {[
              { name: 'Agriculture', color: 'system-agriculture' },
              { name: 'Health', color: 'system-health' },
              { name: 'Religion', color: 'system-religion' },
              { name: 'Territory', color: 'system-territory' },
              { name: 'Chemistry', color: 'system-chemistry' },
              { name: 'Energy', color: 'system-energy' },
              { name: 'Materials', color: 'system-materials' },
              { name: 'Economy', color: 'system-economy' },
              { name: 'Life', color: 'system-life' },
              { name: 'Fun', color: 'system-fun' },
            ].map((system) => (
              <span
                key={system.name}
                className={`px-4 py-2 rounded-full text-sm font-medium bg-${system.color}/20 text-${system.color} border border-${system.color}/40`}
              >
                {system.name}
              </span>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
