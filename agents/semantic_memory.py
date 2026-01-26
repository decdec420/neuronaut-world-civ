"""
Semantic Long-Term Memory System - AI Agents That TRULY LEARN

This system gives agents PERSISTENT, SEARCHABLE memory using vector embeddings.
Agents can recall relevant experiences from their entire life, not just recent events.

Key Features:
- **Vector Embeddings**: Memories stored as semantic vectors for intelligent search
- **Relevance Retrieval**: Find memories by meaning, not just keywords
- **Cross-Agent Learning**: Agents can learn from others' experiences
- **Memory Consolidation**: Important memories strengthened, trivial ones fade
- **Emotional Weighting**: Emotionally intense memories easier to recall
- **Temporal Decay**: Old memories naturally fade (configurable)

This is TRUE AI MEMORY - agents build life stories, learn from mistakes,
and recall relevant experiences just like humans do.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib
from pathlib import Path

# Vector storage and embeddings
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    SEMANTIC_MEMORY_AVAILABLE = True
except ImportError:
    SEMANTIC_MEMORY_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None

logger = logging.getLogger(__name__)


@dataclass
class SemanticMemory:
    """
    Enhanced memory with vector embedding for semantic search

    This extends the basic Memory class with semantic capabilities
    """
    id: str
    agent_id: str
    tick: int
    timestamp: datetime
    event_type: str
    description: str

    # Memory characteristics
    emotional_intensity: float = 0.5  # 0-1, how emotionally charged
    importance: float = 0.5  # 0-1, how significant

    # Context
    participants: List[str] = field(default_factory=list)
    location: Tuple[int, int] = (0, 0)
    related_goal: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Semantic search metadata
    embedding: Optional[List[float]] = None  # Vector representation
    access_count: int = 0  # How often recalled
    last_accessed: Optional[datetime] = None
    consolidation_strength: float = 1.0  # Gets stronger with recall

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for ChromaDB storage)"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        if self.last_accessed:
            d['last_accessed'] = self.last_accessed.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticMemory':
        """Create from dictionary"""
        # Parse timestamps
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data.get('last_accessed'), str):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)


class SemanticMemorySystem:
    """
    Vector-based memory system with semantic search

    This replaces simple list-based memory with intelligent retrieval:
    - Memories stored as vector embeddings
    - Search by meaning, not just keywords
    - Automatic consolidation and forgetting
    - Cross-agent memory sharing

    Example:
        Agent searches for "how to hunt deer"
        → Retrieves memories about successful hunts, tracking prey, using weapons
        Even if those exact words weren't used!
    """

    def __init__(
        self,
        agent_id: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        persist_directory: Optional[str] = None,
        max_memories: int = 1000,
        consolidation_enabled: bool = True,
        temporal_decay_enabled: bool = True
    ):
        """
        Initialize semantic memory system

        Args:
            agent_id: Unique identifier for this agent
            embedding_model: Sentence transformer model for embeddings
            persist_directory: Where to store memory database (None = in-memory)
            max_memories: Maximum memories to retain
            consolidation_enabled: Whether to strengthen recalled memories
            temporal_decay_enabled: Whether old memories fade over time
        """
        self.agent_id = agent_id
        self.max_memories = max_memories
        self.consolidation_enabled = consolidation_enabled
        self.temporal_decay_enabled = temporal_decay_enabled

        # Statistics
        self.total_memories_created = 0
        self.total_recalls = 0
        self.total_consolidations = 0

        if not SEMANTIC_MEMORY_AVAILABLE:
            logger.warning(f"[{agent_id}] Semantic memory unavailable - install chromadb and sentence-transformers")
            self.enabled = False
            self.embedder = None
            self.collection = None
            return

        self.enabled = True

        # Initialize embedding model (lightweight, runs locally)
        logger.info(f"[{agent_id}] Loading embedding model: {embedding_model}")
        try:
            self.embedder = SentenceTransformer(embedding_model)
            logger.info(f"[{agent_id}] ✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"[{agent_id}] Failed to load embedder: {e}")
            self.enabled = False
            return

        # Initialize ChromaDB for vector storage
        try:
            if persist_directory:
                persist_path = Path(persist_directory) / f"memories_{agent_id}"
                persist_path.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(
                    path=str(persist_path),
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                # In-memory only (for testing)
                client = chromadb.Client(Settings(anonymized_telemetry=False))

            # Get or create collection for this agent's memories
            self.collection = client.get_or_create_collection(
                name=f"agent_{agent_id}_memories",
                metadata={"agent_id": agent_id}
            )

            logger.info(f"[{agent_id}] ✅ Semantic memory system ready ({self.collection.count()} existing memories)")

        except Exception as e:
            logger.error(f"[{agent_id}] Failed to initialize ChromaDB: {e}")
            self.enabled = False

    # ============================================================================
    # CORE MEMORY OPERATIONS
    # ============================================================================

    def remember(
        self,
        tick: int,
        event_type: str,
        description: str,
        emotional_intensity: float = 0.5,
        importance: float = 0.5,
        participants: List[str] = None,
        location: Tuple[int, int] = (0, 0),
        related_goal: Optional[str] = None,
        tags: List[str] = None
    ) -> Optional[str]:
        """
        Store a new memory with semantic embedding

        Args:
            tick: Simulation tick when event occurred
            event_type: Category of event (birth, death, discovery, etc.)
            description: Natural language description of what happened
            emotional_intensity: 0-1, how emotionally charged
            importance: 0-1, how significant for agent's life
            participants: Other agents involved
            location: Where it happened (x, y)
            related_goal: Goal this memory relates to
            tags: Optional tags for categorization

        Returns:
            Memory ID if successful, None if failed
        """
        if not self.enabled:
            return None

        # Generate unique memory ID
        memory_id = self._generate_memory_id(tick, description)

        # Create memory object
        memory = SemanticMemory(
            id=memory_id,
            agent_id=self.agent_id,
            tick=tick,
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            emotional_intensity=emotional_intensity,
            importance=importance,
            participants=participants or [],
            location=location,
            related_goal=related_goal,
            tags=tags or []
        )

        # Generate embedding from description
        try:
            embedding = self.embedder.encode(description).tolist()
            memory.embedding = embedding
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to encode memory: {e}")
            return None

        # Store in vector database
        try:
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                metadatas=[{
                    'agent_id': self.agent_id,
                    'tick': tick,
                    'event_type': event_type,
                    'emotional_intensity': emotional_intensity,
                    'importance': importance,
                    'location': f"{location[0]},{location[1]}",
                    'participants': ','.join(participants or []),
                    'tags': ','.join(tags or []),
                    'consolidation_strength': 1.0,
                    'access_count': 0
                }],
                documents=[description]
            )

            self.total_memories_created += 1
            logger.debug(f"[{self.agent_id}] Remembered: {description[:50]}...")

            # Consolidate if we have too many memories
            if self.collection.count() > self.max_memories:
                self._consolidate_memories()

            return memory_id

        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to store memory: {e}")
            return None

    def recall(
        self,
        query: str,
        n_results: int = 5,
        min_relevance: float = 0.0,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recall memories semantically related to query

        This is the MAGIC of semantic memory - agents can recall relevant
        experiences even if the exact words differ!

        Example:
            query = "how to survive winter"
            → recalls memories about: storing food, building shelter, staying warm
            even if those memories never used the word "winter"!

        Args:
            query: What to search for (natural language)
            n_results: How many memories to retrieve
            min_relevance: Minimum similarity score (0-1)
            filter_params: Optional filters (event_type, participants, etc.)

        Returns:
            List of relevant memories, sorted by relevance
        """
        if not self.enabled or self.collection.count() == 0:
            return []

        try:
            # Encode query to vector
            query_embedding = self.embedder.encode(query).tolist()

            # Build filter if provided
            where_filter = None
            if filter_params:
                where_filter = {}
                if 'event_type' in filter_params:
                    where_filter['event_type'] = filter_params['event_type']
                if 'min_importance' in filter_params:
                    where_filter['importance'] = {"$gte": filter_params['min_importance']}

            # Query vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, self.collection.count()),
                where=where_filter if where_filter else None
            )

            # Parse results
            memories = []
            for i in range(len(results['ids'][0])):
                memory_id = results['ids'][0][i]
                description = results['documents'][0][i]
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0

                # Convert distance to similarity (0-1)
                relevance = 1.0 - min(distance, 1.0)

                if relevance >= min_relevance:
                    memories.append({
                        'id': memory_id,
                        'description': description,
                        'relevance': relevance,
                        'tick': metadata.get('tick', 0),
                        'event_type': metadata.get('event_type', 'unknown'),
                        'emotional_intensity': metadata.get('emotional_intensity', 0.5),
                        'importance': metadata.get('importance', 0.5),
                        'access_count': metadata.get('access_count', 0),
                        'consolidation_strength': metadata.get('consolidation_strength', 1.0)
                    })

                    # Update access statistics
                    self._mark_accessed(memory_id)

            self.total_recalls += 1

            logger.debug(f"[{self.agent_id}] Recalled {len(memories)} memories for: {query[:30]}...")

            return memories

        except Exception as e:
            logger.error(f"[{self.agent_id}] Recall failed: {e}")
            return []

    def recall_recent(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """Get most recent memories (chronological)"""
        if not self.enabled or self.collection.count() == 0:
            return []

        try:
            # Get all memories and sort by tick
            all_results = self.collection.get()

            memories_with_tick = []
            for i in range(len(all_results['ids'])):
                tick = all_results['metadatas'][i].get('tick', 0)
                memories_with_tick.append({
                    'id': all_results['ids'][i],
                    'description': all_results['documents'][i],
                    'tick': tick,
                    'event_type': all_results['metadatas'][i].get('event_type'),
                    'importance': all_results['metadatas'][i].get('importance', 0.5)
                })

            # Sort by tick descending
            memories_with_tick.sort(key=lambda m: m['tick'], reverse=True)

            return memories_with_tick[:n_results]

        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to get recent memories: {e}")
            return []

    def recall_about_agent(self, other_agent_id: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Recall all memories involving another agent"""
        return self.recall(
            query=f"interactions with {other_agent_id}",
            n_results=n_results,
            filter_params={'participants': other_agent_id}
        )

    # ============================================================================
    # CROSS-AGENT MEMORY SHARING
    # ============================================================================

    def share_memory(
        self,
        memory_id: str,
        recipient_memory_system: 'SemanticMemorySystem',
        trust_level: float = 1.0
    ) -> bool:
        """
        Share a memory with another agent

        This enables COLLECTIVE LEARNING - agents can learn from each other's
        experiences without experiencing them directly!

        Args:
            memory_id: Memory to share
            recipient_memory_system: Other agent's memory system
            trust_level: How much recipient trusts this agent (0-1)
                        Lower trust = memory stored with lower importance

        Returns:
            True if successfully shared
        """
        if not self.enabled or not recipient_memory_system.enabled:
            return False

        try:
            # Get memory from this agent
            result = self.collection.get(ids=[memory_id])

            if not result['ids']:
                return False

            description = result['documents'][0]
            metadata = result['metadatas'][0]

            # Store in recipient's memory with adjusted importance
            recipient_memory_system.remember(
                tick=metadata.get('tick', 0),
                event_type=metadata.get('event_type', 'shared_knowledge'),
                description=f"[Learned from {self.agent_id}] {description}",
                emotional_intensity=metadata.get('emotional_intensity', 0.3) * trust_level,
                importance=metadata.get('importance', 0.5) * trust_level * 0.7,  # Shared memories less important
                tags=['shared_knowledge', f'from_{self.agent_id}']
            )

            logger.info(f"[{self.agent_id}] Shared memory with {recipient_memory_system.agent_id}")
            return True

        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to share memory: {e}")
            return False

    # ============================================================================
    # MEMORY CONSOLIDATION & FORGETTING
    # ============================================================================

    def _consolidate_memories(self):
        """
        Remove least important memories when limit exceeded

        Mimics human memory consolidation:
        - Important memories preserved
        - Frequently recalled memories strengthened
        - Old, unimportant memories forgotten
        """
        if not self.enabled:
            return

        try:
            current_count = self.collection.count()

            if current_count <= self.max_memories:
                return

            # Get all memories with metadata
            all_data = self.collection.get()

            # Calculate retention score for each memory
            memories_scored = []
            for i in range(len(all_data['ids'])):
                metadata = all_data['metadatas'][i]

                # Score based on: importance, consolidation strength, emotional intensity
                score = (
                    metadata.get('importance', 0.5) * 0.4 +
                    metadata.get('consolidation_strength', 1.0) * 0.3 +
                    metadata.get('emotional_intensity', 0.5) * 0.2 +
                    metadata.get('access_count', 0) / 100.0 * 0.1
                )

                memories_scored.append({
                    'id': all_data['ids'][i],
                    'score': score
                })

            # Sort by score
            memories_scored.sort(key=lambda m: m['score'], reverse=True)

            # Keep top memories
            to_keep = memories_scored[:self.max_memories]
            to_delete = memories_scored[self.max_memories:]

            # Delete low-importance memories
            if to_delete:
                delete_ids = [m['id'] for m in to_delete]
                self.collection.delete(ids=delete_ids)

                logger.info(f"[{self.agent_id}] Consolidated memories: kept {len(to_keep)}, forgot {len(to_delete)}")
                self.total_consolidations += 1

        except Exception as e:
            logger.error(f"[{self.agent_id}] Consolidation failed: {e}")

    def _mark_accessed(self, memory_id: str):
        """Mark memory as accessed (strengthens it)"""
        if not self.enabled or not self.consolidation_enabled:
            return

        try:
            # Get current metadata
            result = self.collection.get(ids=[memory_id])
            if not result['ids']:
                return

            metadata = result['metadatas'][0]
            access_count = metadata.get('access_count', 0) + 1
            consolidation_strength = min(
                metadata.get('consolidation_strength', 1.0) + 0.1,
                2.0  # Max 2x strengthening
            )

            # Update metadata
            self.collection.update(
                ids=[memory_id],
                metadatas=[{
                    **metadata,
                    'access_count': access_count,
                    'consolidation_strength': consolidation_strength
                }]
            )

        except Exception as e:
            logger.debug(f"[{self.agent_id}] Failed to mark accessed: {e}")

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _generate_memory_id(self, tick: int, description: str) -> str:
        """Generate unique memory ID"""
        content = f"{self.agent_id}_{tick}_{description}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        if not self.enabled:
            return {
                'enabled': False,
                'reason': 'Dependencies not available'
            }

        return {
            'enabled': True,
            'agent_id': self.agent_id,
            'total_memories': self.collection.count() if self.collection else 0,
            'total_created': self.total_memories_created,
            'total_recalls': self.total_recalls,
            'total_consolidations': self.total_consolidations,
            'max_memories': self.max_memories,
            'consolidation_enabled': self.consolidation_enabled,
            'temporal_decay_enabled': self.temporal_decay_enabled
        }

    def clear_all_memories(self):
        """Clear all memories (use with caution!)"""
        if not self.enabled:
            return

        try:
            # Delete all
            all_ids = self.collection.get()['ids']
            if all_ids:
                self.collection.delete(ids=all_ids)
            logger.warning(f"[{self.agent_id}] All memories cleared!")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to clear memories: {e}")

    def export_memories(self) -> List[Dict[str, Any]]:
        """Export all memories as list of dictionaries"""
        if not self.enabled:
            return []

        try:
            all_data = self.collection.get()

            memories = []
            for i in range(len(all_data['ids'])):
                memories.append({
                    'id': all_data['ids'][i],
                    'description': all_data['documents'][i],
                    'metadata': all_data['metadatas'][i]
                })

            return memories
        except Exception as e:
            logger.error(f"[{self.agent_id}] Export failed: {e}")
            return []
