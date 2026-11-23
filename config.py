"""
Configuration Loader for Neuronaut World

Loads API keys and settings from .env file
"""

import os
from pathlib import Path
from typing import Dict, Optional

# Try to load python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using environment variables only.")
    print("   Install with: pip install python-dotenv")


def _api_key(name: str) -> str:
    """An API key from the environment, or '' if unset or still the
    .env.example placeholder ("your_groq_api_key_here"). Copying the example
    used to leave four fake keys, so every AI decision first tried four cloud
    providers that could only fail before reaching the local model."""
    value = os.getenv(name, '').strip()
    lowered = value.lower()
    if lowered.startswith('your_') or lowered.endswith('_here'):
        return ''
    return value


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    """An integer setting, or the default (with a warning) if it isn't one."""
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        print(f"⚠️  Invalid {name}={raw!r}, using default {default}")
        return default
    if value < minimum:
        print(f"⚠️  {name} must be >= {minimum}, using default {default}")
        return default
    return value


REPO_DIR = Path(__file__).resolve().parent


class Config:
    """Configuration for Neuronaut World"""

    def __init__(self):
        # Server (main.py, api/server.py). HOST defaults to this machine only;
        # set HOST=0.0.0.0 to serve others (the Docker image does), and then
        # set NEURONAUT_ADMIN_TOKEN so only you can change the world.
        self.host = os.getenv('HOST', '127.0.0.1').strip() or '127.0.0.1'
        self.port = _int_env('PORT', 8000)
        self.num_agents = _int_env('NUM_AGENTS', 12)
        level = os.getenv('LOG_LEVEL', 'INFO').strip().upper()
        if level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            print(f"⚠️  Invalid LOG_LEVEL={level!r}, using INFO")
            level = 'INFO'
        self.log_level = level
        # Where saves go; relative paths are taken from the repository, not
        # from wherever the server was started
        save_dir = Path(os.getenv('SAVE_DIR', 'save_states'))
        self.save_dir = save_dir if save_dir.is_absolute() else REPO_DIR / save_dir

        # LLM API Keys (the .env.example placeholders count as no key)
        self.groq_api_key = _api_key('GROQ_API_KEY')
        self.gemini_api_key = _api_key('GEMINI_API_KEY')
        self.huggingface_api_key = _api_key('HUGGINGFACE_API_KEY')
        self.together_api_key = _api_key('TOGETHER_API_KEY')

        # Ollama settings (a local model; no API key). OLLAMA_BASE_URL is the
        # documented name; OLLAMA_HOST still works.
        self.ollama_host = os.getenv('OLLAMA_BASE_URL') or os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        # Small instruct model that runs on CPU (e.g. an Intel Mac): ~2 GB to
        # download, ~4 GB of free RAM while loaded
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
        try:
            # Context window in tokens. A decision prompt is ~2,000 tokens; some
            # Ollama versions default to 2,048 and silently cut the prompt.
            self.ollama_num_ctx = int(os.getenv('OLLAMA_NUM_CTX', '4096'))
            self.llm_timeout = float(os.getenv('LLM_TIMEOUT', '60'))  # seconds per model call
            # Room for optional context (laws, buildings, discoveries...) in a
            # decision prompt, in characters; the agent's own state always goes in
            self.llm_context_chars = int(os.getenv('LLM_CONTEXT_CHARS', '1800'))
        except ValueError:
            print("⚠️  Invalid OLLAMA_NUM_CTX, LLM_TIMEOUT or LLM_CONTEXT_CHARS, using 4096, 60 and 1800")
            self.ollama_num_ctx, self.llm_timeout, self.llm_context_chars = 4096, 60.0, 1800
        try:
            # Thinking in parallel (agents/thinking.py): model calls in flight at
            # once, ticks between an agent's thoughts, and seconds a tick waits
            # for answers before agents use the rule-based brain
            self.llm_workers = max(1, int(os.getenv('LLM_WORKERS', '2')))
            self.llm_think_every = max(1, int(os.getenv('LLM_THINK_EVERY', '6')))
            self.llm_tick_budget = max(0.0, float(os.getenv('LLM_TICK_BUDGET', '2')))
        except ValueError:
            print("⚠️  Invalid LLM_WORKERS, LLM_THINK_EVERY or LLM_TICK_BUDGET, using 2, 6 and 2")
            self.llm_workers, self.llm_think_every, self.llm_tick_budget = 2, 6, 2.0

        # Feature flags with validation
        self.use_llm_decisions = os.getenv('USE_LLM_DECISIONS', 'true').lower() == 'true'

        # Life: how many ticks make one year of an agent's life (life/aging.py).
        # 144 ticks is one sim day, so a lifetime is ~80 days of sim time.
        try:
            self.ticks_per_life_year = int(os.getenv('TICKS_PER_LIFE_YEAR', '144'))
            if self.ticks_per_life_year < 1:
                print("⚠️  TICKS_PER_LIFE_YEAR must be >= 1, using default 144")
                self.ticks_per_life_year = 144
        except ValueError:
            print("⚠️  Invalid TICKS_PER_LIFE_YEAR value, using default 144")
            self.ticks_per_life_year = 144

        # Auto-save a summary snapshot every N ticks (0 = off); the newest 10 are kept
        try:
            self.autosave_every = max(0, int(os.getenv('AUTOSAVE_EVERY', '1000')))
        except ValueError:
            print("⚠️  Invalid AUTOSAVE_EVERY value, using default 1000")
            self.autosave_every = 1000

        # Population cap: a technical limit for performance (each agent costs
        # tick time, and AI-brain calls when those are on), not a design rule.
        # At the cap no new pregnancy starts; nothing else changes.
        try:
            self.max_population = int(os.getenv('MAX_POPULATION', '60'))
            if self.max_population < 1:
                print("⚠️  MAX_POPULATION must be >= 1, using default 60")
                self.max_population = 60
        except ValueError:
            print("⚠️  Invalid MAX_POPULATION value, using default 60")
            self.max_population = 60

        # Validate and parse integer environment variables
        try:
            self.long_term_planning_interval = int(os.getenv('LONG_TERM_PLANNING_INTERVAL', '100'))
            if self.long_term_planning_interval < 1:
                print("⚠️  LONG_TERM_PLANNING_INTERVAL must be >= 1, using default 100")
                self.long_term_planning_interval = 100
        except ValueError:
            print("⚠️  Invalid LONG_TERM_PLANNING_INTERVAL value, using default 100")
            self.long_term_planning_interval = 100

        try:
            self.reflection_interval = int(os.getenv('REFLECTION_INTERVAL', '500'))
            if self.reflection_interval < 1:
                print("⚠️  REFLECTION_INTERVAL must be >= 1, using default 500")
                self.reflection_interval = 500
        except ValueError:
            print("⚠️  Invalid REFLECTION_INTERVAL value, using default 500")
            self.reflection_interval = 500

        # Swarm Intelligence Settings
        self.enable_swarm_intelligence = os.getenv('ENABLE_SWARM_INTELLIGENCE', 'true').lower() == 'true'
        self.enable_parallel_llm = os.getenv('ENABLE_PARALLEL_LLM', 'true').lower() == 'true'

        try:
            self.max_swarm_size = int(os.getenv('MAX_SWARM_SIZE', '10'))
            if self.max_swarm_size < 2:
                print("⚠️  MAX_SWARM_SIZE must be >= 2, using default 10")
                self.max_swarm_size = 10
        except ValueError:
            print("⚠️  Invalid MAX_SWARM_SIZE value, using default 10")
            self.max_swarm_size = 10

        try:
            self.consensus_threshold = float(os.getenv('CONSENSUS_THRESHOLD', '0.6'))
            if not 0.0 <= self.consensus_threshold <= 1.0:
                print("⚠️  CONSENSUS_THRESHOLD must be between 0.0 and 1.0, using default 0.6")
                self.consensus_threshold = 0.6
        except ValueError:
            print("⚠️  Invalid CONSENSUS_THRESHOLD value, using default 0.6")
            self.consensus_threshold = 0.6

        try:
            self.coordination_radius = float(os.getenv('COORDINATION_RADIUS', '5.0'))
            if self.coordination_radius < 0:
                print("⚠️  COORDINATION_RADIUS must be >= 0, using default 5.0")
                self.coordination_radius = 5.0
        except ValueError:
            print("⚠️  Invalid COORDINATION_RADIUS value, using default 5.0")
            self.coordination_radius = 5.0

        # Semantic Long-Term Memory Settings
        self.enable_semantic_memory = os.getenv('ENABLE_SEMANTIC_MEMORY', 'true').lower() == 'true'
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.memory_persist_dir = os.getenv('MEMORY_PERSIST_DIR', './data/memories')

        try:
            self.max_memories_per_agent = int(os.getenv('MAX_MEMORIES_PER_AGENT', '1000'))
            if self.max_memories_per_agent < 100:
                print("⚠️  MAX_MEMORIES_PER_AGENT must be >= 100, using default 1000")
                self.max_memories_per_agent = 1000
        except ValueError:
            print("⚠️  Invalid MAX_MEMORIES_PER_AGENT value, using default 1000")
            self.max_memories_per_agent = 1000

        self.memory_consolidation_enabled = os.getenv('MEMORY_CONSOLIDATION_ENABLED', 'true').lower() == 'true'
        self.memory_temporal_decay = os.getenv('MEMORY_TEMPORAL_DECAY', 'true').lower() == 'true'

    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys as a dictionary for LLMBrain"""
        keys = {}

        if self.groq_api_key:
            keys['groq'] = self.groq_api_key
        if self.gemini_api_key:
            keys['gemini'] = self.gemini_api_key
        if self.huggingface_api_key:
            keys['huggingface'] = self.huggingface_api_key
        if self.together_api_key:
            keys['together'] = self.together_api_key

        return keys

    def has_any_api_keys(self) -> bool:
        """Check if any API keys are configured"""
        return bool(self.get_api_keys())

    def get_available_providers(self) -> list:
        """Get list of available LLM providers"""
        providers = ['ollama']  # Always available

        if self.groq_api_key:
            providers.append('groq')
        if self.gemini_api_key:
            providers.append('gemini')
        if self.huggingface_api_key:
            providers.append('huggingface')
        if self.together_api_key:
            providers.append('together')

        return providers

    def get_swarm_config(self) -> Dict[str, any]:
        """Get swarm intelligence configuration"""
        return {
            'enabled': self.enable_swarm_intelligence,
            'max_swarm_size': self.max_swarm_size,
            'consensus_threshold': self.consensus_threshold,
            'coordination_radius': self.coordination_radius,
            'enable_parallel_llm': self.enable_parallel_llm
        }

    def get_memory_config(self) -> Dict[str, any]:
        """Get semantic memory configuration"""
        return {
            'enabled': self.enable_semantic_memory,
            'embedding_model': self.embedding_model,
            'persist_directory': self.memory_persist_dir,
            'max_memories': self.max_memories_per_agent,
            'consolidation_enabled': self.memory_consolidation_enabled,
            'temporal_decay_enabled': self.memory_temporal_decay
        }

    def print_status(self):
        """Print configuration status"""
        print("\n🔧 NEURONAUT WORLD CONFIGURATION")
        print("=" * 50)
        print(f"LLM Decisions: {'✅ ENABLED' if self.use_llm_decisions else '❌ DISABLED (rule-based only)'}")
        print(f"\nAvailable LLM Providers:")

        if self.groq_api_key:
            print("  ✅ Groq (30/min, 14,400/day)")
        else:
            print("  ❌ Groq (no API key)")

        if self.gemini_api_key:
            print("  ✅ Google Gemini Flash (15/min, 1,500/day)")
        else:
            print("  ❌ Google Gemini (no API key)")

        if self.huggingface_api_key:
            print("  ✅ Hugging Face (30,000/month)")
        else:
            print("  ❌ Hugging Face (no API key)")

        if self.together_api_key:
            print("  ✅ Together AI (60/min)")
        else:
            print("  ❌ Together AI (no API key)")

        print(f"  ✅ Ollama (unlimited, local) - {self.ollama_model}")

        if not self.has_any_api_keys():
            print("\n⚠️  No cloud API keys configured!")
            print("   Only Ollama (local) will be used.")
            print("   To add API keys, copy .env.example to .env and add your keys.")

        print(f"\nAutonomy Settings:")
        print(f"  Long-term Planning: Every {self.long_term_planning_interval} ticks")
        print(f"  Self-Reflection: Every {self.reflection_interval} ticks")

        print(f"\nSwarm Intelligence:")
        if self.enable_swarm_intelligence:
            print(f"  ✅ ENABLED - Agents coordinate and form alliances")
            print(f"  Max Swarm Size: {self.max_swarm_size} agents")
            print(f"  Consensus Threshold: {self.consensus_threshold * 100:.0f}%")
            print(f"  Coordination Radius: {self.coordination_radius} tiles")
            print(f"  Parallel LLM: {'✅ Enabled' if self.enable_parallel_llm else '❌ Disabled'}")
        else:
            print(f"  ❌ DISABLED - Agents act independently")

        print(f"\nSemantic Long-Term Memory:")
        if self.enable_semantic_memory:
            print(f"  ✅ ENABLED - Agents learn and recall experiences semantically")
            print(f"  Embedding Model: {self.embedding_model}")
            print(f"  Max Memories/Agent: {self.max_memories_per_agent}")
            print(f"  Memory Consolidation: {'✅ Enabled' if self.memory_consolidation_enabled else '❌ Disabled'}")
            print(f"  Temporal Decay: {'✅ Enabled' if self.memory_temporal_decay else '❌ Disabled'}")
            print(f"  Persist Directory: {self.memory_persist_dir}")
        else:
            print(f"  ❌ DISABLED - Basic memory only")

        print("=" * 50)
        print()


# Private module-level config instance (not exported)
_config_instance: Optional[Config] = None


def load_config() -> Config:
    """
    Load and return configuration (singleton pattern).

    This creates a single Config instance on first call and returns
    the same instance on subsequent calls, avoiding global mutable state
    while still providing convenient access.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config() -> None:
    """Reset configuration instance (useful for testing)"""
    global _config_instance
    _config_instance = None
