# Swarm Intelligence - Quick Start Guide

## 30-Second Setup

```bash
# 1. Enable swarm intelligence
echo "ENABLE_SWARM_INTELLIGENCE=true" >> .env

# 2. Run tests to verify
python3 tests/test_swarm_intelligence.py

# 3. Start simulation
python3 main.py
```

## What You Get

🐝 **Agents now coordinate autonomously:**
- Form alliances with friends
- Compete with rivals
- Make collective decisions
- Share strategies

## Configuration (Optional)

Edit `.env`:
```bash
MAX_SWARM_SIZE=10              # How many agents coordinate (5-15)
CONSENSUS_THRESHOLD=0.6        # 60% agreement for consensus
COORDINATION_RADIUS=5.0        # Distance for coordination
ENABLE_PARALLEL_LLM=true       # Faster (uses more API)
```

## API Usage

### Social Decision
```python
# Agent decides what to do considering nearby agents
decision, reasoning = await swarm.social_network_decision(
    agent=my_agent,
    action_type="gather_food",
    nearby_agents=nearby_agents
)
```

### Collective Decision
```python
# Group decides strategy
consensus = await swarm.emergent_consensus(
    agents=tribe,
    decision_topic="Where to build?",
    options=["river", "hill", "forest"]
)
```

### Track Relationships
```python
# Update relationships based on interactions
swarm.update_relationships(
    agent1_id="alice",
    agent2_id="bob",
    interaction_type="cooperate",  # or "attack", "trade"
    success=True
)

# Check relationships
allies = swarm.get_agent_allies("alice")
rivals = swarm.get_agent_rivals("alice")
```

## Monitor Performance

```python
# Get statistics
stats = swarm.get_statistics()
print(f"Swarm decisions: {stats['total_swarm_decisions']}")
print(f"Alliances formed: {stats['emergent_alliances']}")
print(f"Active intentions: {stats['active_intentions']}")
```

## Troubleshooting

**"Swarm requires LLM decisions"**
→ Set `USE_LLM_DECISIONS=true` in .env

**"No LLM available"**
→ Start Ollama: `ollama serve && ollama pull llama3.2:3b`

**"Too slow"**
→ Reduce `MAX_SWARM_SIZE` to 5-8

## Examples of Emergent Behavior

With swarm intelligence enabled, watch for:

1. **Hunting Parties** - Agents coordinate to surround prey
2. **Trading Posts** - Merchants cluster and negotiate
3. **War Bands** - Warriors form tactical groups
4. **Research Teams** - Scientists collaborate on discoveries
5. **Building Crews** - Builders divide labor on large projects

## Next Steps

- Read `SWARM_INTELLIGENCE_IMPLEMENTATION.md` for full docs
- See `PHASE_1_1_COMPLETE.md` for implementation details
- Check `tests/test_swarm_intelligence.py` for examples

---

**READY TO GO!** 🚀 Just enable it and watch agents coordinate autonomously!
