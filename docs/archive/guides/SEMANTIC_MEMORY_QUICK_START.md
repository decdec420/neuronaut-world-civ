# Semantic Memory - Quick Start Guide

## 30-Second Setup

```bash
# 1. Enable semantic memory
echo "ENABLE_SEMANTIC_MEMORY=true" >> .env

# 2. Pre-download embedding model (one-time, ~80MB)
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# 3. Run tests
python3 tests/test_semantic_memory.py

# 4. Start simulation
python3 main.py
```

## What You Get

🧠 **Agents now have TRUE MEMORY:**
- Remember entire life history
- Search memories by meaning (not keywords!)
- Learn from other agents
- Important memories never forgotten

## Example Usage

### Store a Memory
```python
from agents.semantic_memory import SemanticMemorySystem

memory = SemanticMemorySystem(agent_id="hunter_1")

memory.remember(
    tick=100,
    event_type='discovery',
    description='Found berry bush near river with ripe red berries',
    importance=0.7,
    emotional_intensity=0.6
)
```

### Semantic Search
```python
# Search by meaning, not exact words!
results = memory.recall(
    query="where to find food",
    n_results=5
)

# Returns memories about:
# - Berry bushes
# - Hunting deer
# - Fishing spots
# Even if they don't contain the word "food"!
```

### Share Knowledge
```python
# Experienced hunter teaches novice
hunter1.memory.share_memory(
    memory_id="best_hunting_spot",
    recipient_memory_system=novice.memory,
    trust_level=0.8
)
# Novice can now recall this memory!
```

### Get Statistics
```python
stats = memory.get_statistics()
# {
#   'total_memories': 147,
#   'total_recalls': 23,
#   'total_consolidations': 3
# }
```

## Configuration (Optional)

Edit `.env`:
```bash
MAX_MEMORIES_PER_AGENT=1000     # How many to remember
MEMORY_PERSIST_DIR=./data/memories  # Where to save
MEMORY_CONSOLIDATION_ENABLED=true   # Strengthen recalled memories
```

## Real-World Examples

### Scenario 1: Learning to Hunt
```python
# Agent remembers failed hunt
memory.remember(
    description="Tried to hunt deer but it heard me and ran away",
    importance=0.6,
    tags=['hunting', 'failure']
)

# Later, before hunting again, agent recalls
results = memory.recall("hunting deer successfully")
# → Learns: need stealth, approach from downwind
```

### Scenario 2: Building Tribal Knowledge
```python
# Elder shares wisdom with tribe
for member in tribe:
    elder.memory.share_memory(
        memory_id="winter_survival_techniques",
        recipient_memory_system=member.memory,
        trust_level=1.0
    )
# Entire tribe now knows how to survive winter!
```

### Scenario 3: Memory Consolidation
```python
# Agent frequently recalls important memory
memory.recall("how to make fire")  # Access: 1
memory.recall("starting fire")     # Access: 2
memory.recall("fire creation")     # Access: 3

# Memory strengthened, will never be forgotten!
# consolidation_strength: 1.3 → 2.0
```

## Troubleshooting

**"Model download failed"**
→ Pre-download: `python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`

**"Memory not persisting"**
→ Check `MEMORY_PERSIST_DIR` exists and is writable

**"Searches too slow"**
→ Reduce `MAX_MEMORIES_PER_AGENT` to 500

**"Out of disk space"**
→ Each agent uses ~2-5MB for 1000 memories
→ Use in-memory mode or reduce max memories

## Next Steps

- Read `PHASE_1_2_COMPLETE.md` for full documentation
- Check `tests/test_semantic_memory.py` for examples
- See `agents/semantic_memory.py` for API reference

---

**READY!** 🚀 Agents can now learn, remember, and recall their entire lives!
