# Neuronaut World v2.0 - Quick Reference Card

## 🚀 What's New in v2.0

**5 Major AI Autonomy Systems:**
1. 🐝 **Swarm Intelligence** - Agents coordinate and form alliances
2. 🧠 **Semantic Memory** - Agents remember entire lives
3. 🎭 **Personality Evolution** - Agents develop through experience
4. 📖 **Civilization Narrator** - GPT-4 generates epic stories
5. 🌍 **Multi-Civilization** - Multiple societies compete

**Total**: 112,000+ bytes of AI autonomy code

---

## ⚡ Quick Start (30 Seconds)

```bash
# 1. Enable v2.0 features
echo "ENABLE_SWARM_INTELLIGENCE=true" >> .env
echo "ENABLE_SEMANTIC_MEMORY=true" >> .env
echo "ENABLE_PERSONALITY_EVOLUTION=true" >> .env
echo "ENABLE_NARRATION=true" >> .env

# 2. Download embedding model (one-time)
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# 3. Run!
python3 main.py
```

---

## 📋 Key Configuration

```bash
# Swarm Intelligence
MAX_SWARM_SIZE=10
CONSENSUS_THRESHOLD=0.6
ENABLE_PARALLEL_LLM=true

# Semantic Memory
MAX_MEMORIES_PER_AGENT=1000
MEMORY_PERSIST_DIR=./data/memories

# Personality Evolution
EVOLUTION_RATE=0.01
ROLE_THRESHOLD=0.6

# Narrator
MIN_MAGNITUDE_TO_NARRATE=MODERATE

# Multi-Civilization
MAX_CIVILIZATIONS=10
MIN_SPAWN_DISTANCE=20
```

---

## 🔧 API Quick Reference

### Swarm Intelligence
```python
from agents.swarm_intelligence import SwarmIntelligence

# Social decision
decision, reasoning = await swarm.social_network_decision(
    agent, action_type, nearby_agents
)

# Group consensus
consensus = await swarm.emergent_consensus(
    agents, topic, options
)

# Track relationships
swarm.update_relationships(id1, id2, "cooperate", success=True)
```

### Semantic Memory
```python
from agents.semantic_memory import SemanticMemorySystem

# Store memory
memory.remember(
    tick=100,
    event_type='discovery',
    description='Found berry bush',
    importance=0.7
)

# Semantic search
results = memory.recall("where to find food", n_results=5)

# Share knowledge
memory.share_memory(mem_id, other_agent.memory, trust=0.8)
```

### Personality Evolution
```python
from agents.personality_evolution import PersonalityEvolutionSystem

# Record experience
evolution.record_experience(
    agent_id, "hunt", success=True, intensity=0.8
)

# Track swarm participation
evolution.record_swarm_participation(
    agent_id, was_leader=True
)

# Major life event
evolution.record_major_event(
    agent_id, "first_kill", {'aggression': 0.1}
)
```

### Civilization Narrator
```python
from narrative.civilization_narrator import CivilizationNarrator

# Name civilization
name, demonym = await narrator.generate_civilization_name(
    civ_id, cultural_context
)

# Narrate event
await narrator.record_event(
    event_type='first_fire',
    description='Elder Kara discovered fire',
    tick=500,
    civilization_id='civ_0',
    is_first_of_kind=True
)

# Get stories
stories = narrator.get_recent_stories(count=10)
legendary = narrator.get_legendary_moments()
```

### Multi-Civilization
```python
from world.multi_civilization import CivilizationManager

# Spawn civilization
civ = manager.spawn_civilization(
    world_size=(100, 100),
    culture_type=CultureType.AGRARIAN
)

# Detect contact
contacted = manager.detect_contact(
    civ_id, agent_location, tick
)

# Update relations
manager.update_diplomatic_relation(
    civ1, civ2, DiplomaticRelation.WAR
)

# Transfer knowledge
manager.transfer_knowledge(
    from_civ, to_civ, "metalworking"
)
```

---

## 🎯 What You Can Observe

### Individual Level
- ✅ Agents remember entire lives
- ✅ Personalities evolve (hunters become more aggressive, builders more patient)
- ✅ Specialists emerge (14 role types)

### Group Level
- ✅ Swarms coordinate hunts
- ✅ Alliances and rivalries
- ✅ Collective decisions through debate

### Civilization Level
- ✅ Multiple civs compete
- ✅ Wars and peace treaties
- ✅ Cultural diffusion
- ✅ Epic GPT-4 generated stories

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Embedder failed to load" | Pre-download model (see Quick Start) |
| "Swarm requires LLM" | Set `USE_LLM_DECISIONS=true` |
| "Searches slow" | Reduce `MAX_MEMORIES_PER_AGENT=500` |
| "Out of space" | Use in-memory: `MEMORY_PERSIST_DIR=` |

---

## 📊 Performance

```
100 agents:     ✅ Smooth
1,000 agents:   ✅ Good (with tuning)
10,000 agents:  ⚠️  Requires optimization
Multiple civs:  ✅ 10 civs optimal
```

---

## 📚 Full Documentation

- **AI_AUTONOMY_V2_FINAL_REPORT.md** - Complete guide
- **SWARM_INTELLIGENCE_IMPLEMENTATION.md** - Swarm details
- **PHASE_1_2_COMPLETE.md** - Memory details
- **GAMEPLAN_V2_AI_SANDBOX.md** - Original vision

---

## 🎮 Example Workflow

```python
# 1. Spawn civilizations
riverfolk = multi_civ.spawn_civilization(
    world_size=(100, 100),
    culture_type=CultureType.AGRARIAN
)

mountain_clans = multi_civ.spawn_civilization(
    world_size=(100, 100),
    culture_type=CultureType.MILITARISTIC
)

# 2. Name them
await narrator.generate_civilization_name(
    riverfolk.civilization_id,
    {'dominant_terrain': 'river', 'specialization': 'farming'}
)

# 3. Run simulation...
# Agents hunt, build, socialize, remember, evolve

# 4. Watch emergent behavior
# - Riverfolk become peaceful farmers
# - Mountain Clans become fierce warriors
# - They make contact
# - Relations evolve (trade → dispute → war)
# - GPT-4 narrates the epic saga

# 5. Get the story
stories = narrator.get_recent_stories()
for story in stories:
    print(f"{story.title}:\n{story.narrative}\n")
```

---

## ✅ Verification Commands

```bash
# Check imports
python3 -c "from agents.swarm_intelligence import SwarmIntelligence; from agents.semantic_memory import SemanticMemorySystem; from agents.personality_evolution import PersonalityEvolutionSystem; from narrative.civilization_narrator import CivilizationNarrator; from world.multi_civilization import CivilizationManager; print('✅ All systems ready')"

# Run tests
python3 tests/test_swarm_intelligence.py
python3 tests/test_semantic_memory.py

# Check config
python3 -c "from config import load_config; c = load_config(); c.print_status()"
```

---

## 🚀 IT'S READY!

**112KB of AI autonomy deployed!**

Let the AI civilizations discover, compete, cooperate, and surprise you! 🌍🤖✨

---

*Neuronaut World v2.0 - AI Autonomy Complete*
*January 25, 2026*
