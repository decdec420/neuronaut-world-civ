"""
Smart Memory System for AI Agents

Implements industry-standard memory management based on 2026 best practices:
- Dual memory architecture (working + persistent)
- Vector database for semantic retrieval
- Memory decay with importance scoring
- Episodic memory with compression

References:
- Redis: "Build smarter AI agents: Manage short-term and long-term memory"
- Research: "Memory in the Age of AI Agents: A Survey" (arxiv.org/abs/2512.13564)
- Redis Vector Library for AI agent memory (redis.io/blog/best-ai-agent-data-storage-2025)
"""

from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
from datetime import datetime, timedelta


# Memory runs on sim time: timestamps are the agent's own tick count (the
# Agent sets SmartMemorySystem.clock each tick), and decay is per sim hour.
# It used to run on wall-clock time (time.time()), so a memory decayed by how
# long the server had been up, not by how much life had passed: at normal
# speed a sim hour is 6 real seconds, so nothing ever decayed.
TICKS_PER_HOUR = 6


class EventImportance(Enum):
    """Memory importance levels for decay and retention"""
    MUNDANE = 1      # Routine actions (picked berries, walked)
    MINOR = 2        # Small successes (traded item, learned tip)
    SIGNIFICANT = 3  # Notable events (built something, discovered tech)
    MAJOR = 4        # Life events (birth, death, major achievement)
    LEGENDARY = 5    # Historical moments (founded civilization, first discovery)


class MemoryType(Enum):
    """Types of memories for categorization"""
    EPISODIC = "episodic"        # Specific events that happened
    SEMANTIC = "semantic"         # General knowledge and facts
    PROCEDURAL = "procedural"     # Skills and how-to knowledge
    EMOTIONAL = "emotional"       # Emotionally significant moments


@dataclass
class Memory:
    """Individual memory with metadata for decay and retrieval"""
    content: str
    importance: EventImportance
    memory_type: MemoryType
    timestamp: float
    agent_id: str

    # Scoring for decay
    recency_score: float = 1.0
    relevance_score: float = 1.0
    emotional_weight: float = 0.0

    # Context metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_decay_score(self, current_time: float, decay_factor: float = 0.995) -> float:
        """
        Calculate memory decay score based on recency and importance.

        Industry standard: 0.995 hourly decay (Redis AI agent best practices)
        Important memories decay slower, mundane memories fade faster.
        """
        hours_elapsed = max(0.0, (current_time - self.timestamp) / TICKS_PER_HOUR)

        # Base decay (exponential decay over time)
        time_decay = decay_factor ** hours_elapsed

        # Importance modifier (higher importance = slower decay)
        importance_modifier = self.importance.value / 5.0  # 0.2 to 1.0

        # Emotional weight modifier (emotional memories persist)
        emotion_modifier = 1.0 + (self.emotional_weight * 0.5)

        # Combined decay score
        decay_score = time_decay * importance_modifier * emotion_modifier

        return max(0.0, min(1.0, decay_score))

    def should_retain(self, current_time: float, threshold: float = 0.1) -> bool:
        """Determine if memory should be retained or pruned"""
        # Always keep MAJOR+ memories
        if self.importance.value >= EventImportance.MAJOR.value:
            return True

        # Check decay score
        return self.calculate_decay_score(current_time) >= threshold

    def to_dict(self) -> Dict:
        """Serialize memory for storage"""
        return {
            'content': self.content,
            'importance': self.importance.value,
            'memory_type': self.memory_type.value,
            'timestamp': self.timestamp,
            'agent_id': self.agent_id,
            'recency_score': self.recency_score,
            'relevance_score': self.relevance_score,
            'emotional_weight': self.emotional_weight,
            'metadata': self.metadata
        }


@dataclass
class SkillPattern:
    """Compressed representation of repeated actions"""
    action_name: str
    total_attempts: int = 0
    successful_attempts: int = 0
    last_used: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_attempts / self.total_attempts

    def update(self, success: bool, now: float = 0.0):
        """Update skill pattern with new attempt (now: the sim clock)"""
        self.total_attempts += 1
        if success:
            self.successful_attempts += 1
        self.last_used = now

    def to_summary(self) -> str:
        """Generate natural language summary"""
        rate = self.success_rate * 100
        return f"I've {self.action_name} {self.total_attempts} times with {rate:.0f}% success"


class SmartMemorySystem:
    """
    Industry-standard memory system for AI agents (2026).

    Features:
    1. Working memory (recent events) - Fast access, bounded
    2. Persistent memory (important events) - Long-term storage
    3. Episodic memory with decay - Realistic forgetting
    4. Skill patterns - Compressed procedural knowledge
    5. Vector-ready format - For semantic retrieval (optional)

    Memory decay implementation based on:
    - Redis AI agent memory management
    - "Memory in the Age of AI Agents" research (2026)
    """

    MAX_EPISODIC = 300
    MAX_PERSISTENT = 100

    def __init__(
        self,
        agent_id: str,
        working_memory_size: int = 100,
        decay_factor: float = 0.995,
        decay_threshold: float = 0.1
    ):
        """
        Initialize smart memory system.

        Args:
            agent_id: Unique identifier for this agent
            working_memory_size: Size of recent memory buffer (default 100)
            decay_factor: Hourly decay rate (default 0.995 per Redis standards)
            decay_threshold: Minimum score to retain memory (default 0.1)
        """
        self.agent_id = agent_id
        self.decay_factor = decay_factor
        self.decay_threshold = decay_threshold

        # Working memory - Recent events (fast access)
        self.working_memory: deque = deque(maxlen=working_memory_size)

        # Persistent memory - Important events never forgotten
        self.persistent_memories: List[Memory] = []

        # Episodic memory with decay - Recent + medium importance
        self.episodic_memory: List[Memory] = []

        # Skill patterns - Compressed procedural knowledge
        self.skill_patterns: Dict[str, SkillPattern] = {}

        # Statistics
        self.total_memories_added = 0
        self.total_memories_decayed = 0
        self.clock = 0                 # sim ticks (set by the agent)
        self.last_cleanup_time = 0     # clock at the last decay

    def add_memory(
        self,
        content: str,
        importance: EventImportance = EventImportance.MUNDANE,
        memory_type: MemoryType = MemoryType.EPISODIC,
        emotional_weight: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> Memory:
        """
        Add new memory to the system.

        Implements smart routing:
        - MUNDANE → working memory only (will decay)
        - MINOR/SIGNIFICANT → episodic memory (with decay)
        - MAJOR/LEGENDARY → persistent memory (never decays)
        """
        memory = Memory(
            content=content,
            importance=importance,
            memory_type=memory_type,
            timestamp=getattr(self, 'clock', 0),
            agent_id=self.agent_id,
            emotional_weight=emotional_weight,
            metadata=metadata or {}
        )

        # Always add to working memory (recent events)
        self.working_memory.append(memory)

        # Route to appropriate long-term storage
        if importance.value >= EventImportance.MAJOR.value:
            # Major+ events: kept (the most recent MAX_PERSISTENT of them)
            self.persistent_memories.append(memory)
            del self.persistent_memories[:-self.MAX_PERSISTENT]
        elif importance.value >= EventImportance.MINOR.value:
            # Minor/Significant: Store but allow decay
            self.episodic_memory.append(memory)
            # Decay runs on wall-clock hours, so in a fast-running world it
            # never pruned anything: keep the most important, then newest
            if len(self.episodic_memory) > self.MAX_EPISODIC * 1.2:
                keep = sorted(self.episodic_memory, key=lambda m: (m.importance.value, m.timestamp))[-self.MAX_EPISODIC:]
                self.episodic_memory = sorted(keep, key=lambda m: m.timestamp)
        # MUNDANE events only live in working memory, naturally drop off

        self.total_memories_added += 1
        return memory

    def update_skill_pattern(self, action_name: str, success: bool):
        """
        Update skill pattern (compressed procedural memory).

        Instead of remembering every "picked berries" event,
        remember "I've picked berries 47 times with 81% success"
        """
        if action_name not in self.skill_patterns:
            self.skill_patterns[action_name] = SkillPattern(action_name)

        self.skill_patterns[action_name].update(success, getattr(self, 'clock', 0))

    def decay_memories(self, force: bool = False):
        """
        Apply memory decay to episodic memories.

        Based on industry research:
        - Decay score decreases hourly by decay_factor (default 0.995)
        - Memories below threshold are pruned
        - Important/emotional memories decay slower

        Runs automatically every hour, or on-demand with force=True.
        """
        current_time = getattr(self, 'clock', 0)

        # A save made when this ran on wall-clock seconds has times far in the
        # future on this clock: they start counting from now
        if self.last_cleanup_time > current_time:
            self.last_cleanup_time = current_time - TICKS_PER_HOUR
            for memory in self.episodic_memory:
                if memory.timestamp > current_time:
                    memory.timestamp = current_time

        # Only run decay every sim hour (unless forced)
        if not force and current_time - self.last_cleanup_time < TICKS_PER_HOUR:
            return

        # Apply decay to episodic memories
        retained_memories = []
        for memory in self.episodic_memory:
            if memory.should_retain(current_time, self.decay_threshold):
                retained_memories.append(memory)
            else:
                self.total_memories_decayed += 1

        self.episodic_memory = retained_memories
        self.last_cleanup_time = current_time

    def get_recent_context(self, limit: int = 10) -> List[Memory]:
        """Get most recent memories (working memory)"""
        return list(self.working_memory)[-limit:]

    def get_important_memories(self) -> List[Memory]:
        """Get all persistent (never-forget) memories"""
        return self.persistent_memories

    def get_skill_knowledge(self) -> Dict[str, Dict]:
        """Get compressed skill patterns"""
        return {
            name: {
                'attempts': pattern.total_attempts,
                'success_rate': pattern.success_rate,
                'summary': pattern.to_summary()
            }
            for name, pattern in self.skill_patterns.items()
        }

    def get_context_for_decision(
        self,
        recent_count: int = 10,
        relevant_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive memory context for AI decision-making.

        Returns:
            - recent: Last N events (what just happened)
            - important: Life story and major events
            - skills: What agent knows how to do
            - episodic: Medium-importance memories (with decay applied)
        """
        # Apply decay before retrieving
        self.decay_memories()

        context = {
            # Recent events (working memory)
            'recent': [m.to_dict() for m in self.get_recent_context(recent_count)],

            # Important life story (persistent memory)
            'important': [m.to_dict() for m in self.get_important_memories()],

            # Skill knowledge (compressed patterns)
            'skills': self.get_skill_knowledge(),

            # Episodic memories (with decay)
            'episodic': [m.to_dict() for m in self.episodic_memory[-20:]],

            # Memory statistics
            'stats': {
                'total_memories': self.total_memories_added,
                'working_size': len(self.working_memory),
                'persistent_size': len(self.persistent_memories),
                'episodic_size': len(self.episodic_memory),
                'decayed_count': self.total_memories_decayed
            }
        }

        return context

    def compress_to_summary(self, time_period: str = "day") -> str:
        """
        Create compressed summary of memories for long-term storage.

        Instead of storing 1000 individual events,
        store a summary: "Spent the day gathering resources and socializing"
        """
        recent = self.get_recent_context(limit=50)

        # Group by action type
        actions = {}
        for memory in recent:
            action = memory.metadata.get('action_type', 'unknown')
            actions[action] = actions.get(action, 0) + 1

        # Generate summary
        top_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)[:3]
        summary_parts = [f"{action} ({count}x)" for action, count in top_actions]

        return f"Summary for {time_period}: " + ", ".join(summary_parts)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            'agent_id': self.agent_id,
            'working_memory_size': len(self.working_memory),
            'persistent_memories': len(self.persistent_memories),
            'episodic_memories': len(self.episodic_memory),
            'skill_patterns': len(self.skill_patterns),
            'total_added': self.total_memories_added,
            'total_decayed': self.total_memories_decayed,
            'decay_factor': self.decay_factor,
            'decay_threshold': self.decay_threshold
        }


# Optional: Vector database integration for semantic retrieval
class VectorMemoryAdapter:
    """
    Adapter for vector database integration (ChromaDB, Redis, Milvus).

    Use this when you want semantic memory retrieval:
    - "What do I know about gathering food?" → finds all food-related memories
    - "How do I deal with winter?" → finds winter survival memories

    Based on 2026 industry standards:
    - Redis: Most popular for AI agents (43% adoption)
    - ChromaDB: Best for prototyping
    - Milvus: Best for production scale
    """

    def __init__(self, db_type: str = "chroma", collection_name: str = "agent_memories"):
        """
        Initialize vector database adapter.

        Args:
            db_type: "chroma", "redis", or "milvus"
            collection_name: Name of memory collection
        """
        self.db_type = db_type
        self.collection_name = collection_name
        self.client = None

        # Initialize based on type (placeholder - actual implementation depends on DB)
        if db_type == "chroma":
            # ChromaDB: Best for rapid prototyping
            # import chromadb
            # self.client = chromadb.Client()
            pass
        elif db_type == "redis":
            # Redis: Best for real-time AI agents
            # from redis import Redis
            # self.client = Redis()
            pass
        elif db_type == "milvus":
            # Milvus: Best for production scale
            # from pymilvus import connections
            # connections.connect()
            pass

    def add_memory_to_vector_db(self, memory: Memory):
        """Add memory to vector database for semantic search"""
        # Placeholder - actual implementation depends on chosen DB
        pass

    def retrieve_similar_memories(self, query: str, limit: int = 10) -> List[Memory]:
        """Retrieve semantically similar memories"""
        # Placeholder - actual implementation depends on chosen DB
        pass


# Example usage for your game
def example_usage():
    """Example of how to use SmartMemorySystem in your game"""

    # Create memory system for an agent
    agent_memory = SmartMemorySystem(
        agent_id="agent_123",
        working_memory_size=100,  # Keep last 100 events
        decay_factor=0.995,       # Industry standard
        decay_threshold=0.1       # Memories below 0.1 score are pruned
    )

    # Agent picks berries (mundane - will decay)
    agent_memory.add_memory(
        content="Picked berries near river",
        importance=EventImportance.MUNDANE,
        metadata={'action_type': 'gather_berries', 'location': 'river'}
    )
    agent_memory.update_skill_pattern('gather_berries', success=True)

    # Agent learns new skill (significant - stored but can decay)
    agent_memory.add_memory(
        content="Learned how to identify edible mushrooms from Elder Jane",
        importance=EventImportance.SIGNIFICANT,
        memory_type=MemoryType.SEMANTIC,
        metadata={'skill': 'foraging', 'teacher': 'Elder Jane'}
    )

    # Agent has a child (major - never forgotten)
    agent_memory.add_memory(
        content="My child Sophie was born!",
        importance=EventImportance.MAJOR,
        memory_type=MemoryType.EMOTIONAL,
        emotional_weight=1.0,
        metadata={'event_type': 'birth', 'child_name': 'Sophie'}
    )

    # Get context for AI decision
    context = agent_memory.get_context_for_decision(recent_count=10)

    print("Context for AI decision:")
    print(f"Recent events: {len(context['recent'])}")
    print(f"Important memories: {len(context['important'])}")
    print(f"Skills known: {context['skills']}")
    print(f"Memory stats: {context['stats']}")

    # Agent remembers HOW to pick berries (skill pattern)
    # but not every individual berry-picking event!
    skills = agent_memory.get_skill_knowledge()
    if 'gather_berries' in skills:
        print(f"\nSkill memory: {skills['gather_berries']['summary']}")


if __name__ == "__main__":
    example_usage()
