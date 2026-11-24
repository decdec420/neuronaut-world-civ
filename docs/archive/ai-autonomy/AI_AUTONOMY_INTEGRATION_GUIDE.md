# 🧠 AI AUTONOMY INTEGRATION GUIDE

## 🎯 Overview

Your agents now have **TRUE AUTONOMY** powered by multiple free LLM providers!

**New Capabilities:**
- ✅ **Unlimited AI-powered thinking** (rotates between free LLM APIs)
- ✅ **Long-term goal planning** (agents set their own life goals)
- ✅ **Persistent memory** (agents remember their experiences)
- ✅ **Self-reflection** (agents learn and grow from their past)
- ✅ **Creative decision-making** (AI reasoning beyond rules)

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd /Users/hackerman/neuronaut-world

# Install LLM client libraries (optional - only for cloud APIs)
pip install groq google-genai python-dotenv

# OR just use local Ollama (100% free, no API keys needed)
brew install ollama
ollama pull llama3.2:3b
```

### Step 2: Get Free API Keys (Optional but Recommended)

Get as many as you want - they're ALL FREE!

#### **Groq (Recommended - FASTEST)**
1. Go to: https://console.groq.com
2. Sign up (free)
3. Create API key
4. 30 requests/min, 14,400/day FREE

#### **Google Gemini Flash (SMARTEST)**
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Create API key
4. 15 requests/min, 1,500/day FREE

#### **Hugging Face (LARGEST LIMIT)**
1. Go to: https://huggingface.co/settings/tokens
2. Sign up (free)
3. Create access token
4. 30,000 requests/month FREE

#### **Together AI (GOOD FALLBACK)**
1. Go to: https://api.together.xyz
2. Sign up (free)
3. Get $25 free credits (about 1M tokens)

### Step 3: Configure API Keys

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys
# You can use ANY combination - even just one is fine!
nano .env
```

Example `.env`:
```bash
# Add the ones you have (all optional)
GROQ_API_KEY=gsk_your_actual_key_here
GEMINI_API_KEY=AIza_your_actual_key_here
HUGGINGFACE_API_KEY=hf_your_actual_key_here

# Enable LLM decisions
USE_LLM_DECISIONS=true

# How often agents plan long-term (ticks)
LONG_TERM_PLANNING_INTERVAL=100
REFLECTION_INTERVAL=500
```

**Note:** If you don't add ANY keys, agents will use local Ollama (still works great!).

---

## 💻 Integration into Your Code

### Option A: Quick Integration (Recommended)

Modify your `engine/simulation.py` to use autonomous agents:

```python
# At the top of simulation.py
from agents.llm_brain import MultiLLMBrain
from agents.autonomous_agent import AutonomousAgentMixin
from config import load_config

class Simulation:
    def __init__(self):
        # Load configuration
        self.config = load_config()
        self.config.print_status()  # Show what's configured

        # Initialize multi-LLM brain (shared by all agents)
        self.llm_brain = MultiLLMBrain(api_keys=self.config.get_api_keys())

        # ... rest of your init code ...

    def create_agent(self, ...):
        """Create agent with autonomous capabilities"""
        agent = Agent(...)  # Your normal agent creation

        # Add autonomous systems to agent
        if hasattr(agent, 'init_autonomous_systems'):
            agent.init_autonomous_systems(llm_brain=self.llm_brain)

        return agent

    def run_tick(self):
        """Run one simulation tick"""
        for agent in self.world.agents:
            perceptions = self.get_perceptions(agent)

            # Let agent make autonomous decision
            if hasattr(agent, 'autonomous_decide'):
                action = agent.autonomous_decide(
                    perceptions=perceptions,
                    current_tick=self.current_tick,
                    config=self.config
                )
            else:
                # Fallback to regular decision
                action = agent.decide(perceptions)

            # Execute action
            self.execute_action(agent, action)
```

### Option B: Extend Agent Class

Add the mixin to your `Agent` class in `agents/agent.py`:

```python
# In agents/agent.py
from agents.autonomous_agent import AutonomousAgentMixin

class Agent(AutonomousAgentMixin):  # Add mixin here
    def __init__(self, ...):
        # ... your existing init code ...

        # Initialize autonomous systems (add at end of __init__)
        self.init_autonomous_systems(llm_brain=None)  # LLM brain set later
```

Then in your simulation, set the brain:

```python
# In simulation.py
llm_brain = MultiLLMBrain(api_keys=config.get_api_keys())

for agent in agents:
    agent.llm_brain = llm_brain
```

---

## 🎮 How It Works

### Agent Decision Process (Full Autonomy)

1. **Emergency Survival**: If dying, immediately eat/drink (no AI needed)

2. **Long-Term Planning** (every 100 ticks by default):
   - Agent thinks: "What are my goals in life?"
   - AI generates goals based on personality
   - Examples: "Get rich", "Build a family", "Discover new knowledge"

3. **Self-Reflection** (every 500 ticks by default):
   - Agent reviews their memories
   - Learns from successes/failures
   - Adjusts their approach

4. **Contextual Decision**:
   - AI considers: personality, needs, goals, nearby people, inventory
   - Makes decision like a real person would
   - Can choose ANY action they want

### Example Agent Thinking

**Agent:** Zara (Ambitious: 0.8, Creative: 0.9, Social: 0.4)

**Long-term Planning:**
> "I want to discover new technologies through experimentation. I'll gather materials and try different combinations. My goal is to be known as a great inventor."

**Immediate Decision:**
> "I'm feeling creative and I have wood and stone in my inventory. I'll experiment with combining them to see what I can create. This aligns with my goal of becoming an inventor."

**Self-Reflection (after failed experiment):**
> "My experiment with wood and fire failed and caused an explosion. I learned that I need to be more careful. Next time I'll use less volatile materials. I feel frustrated but determined to succeed."

---

## 📊 Multi-LLM Provider Rotation

The system automatically rotates between providers to maximize free usage:

```
Decision 1: Groq (30/min available) ✅
Decision 2: Groq (29/min available) ✅
Decision 3: Groq (28/min available) ✅
...
Decision 30: Groq (1/min available) ✅
Decision 31: Groq (limit reached) ❌
           → Tries Together AI (60/min available) ✅
Decision 32: Together AI (59/min available) ✅
...
Decision 90: All providers exhausted ❌
           → Falls back to Ollama (unlimited) ✅
```

**Result:** ~27,000 free cloud API calls/day + unlimited local!

---

## 🎯 Agent Goals System

Agents can pursue multiple goals simultaneously:

```python
# Agents automatically set goals based on their personality

# Ambitious agent's goals:
- "Become wealthy through trade" (priority: 0.9)
- "Build a large house" (priority: 0.7)

# Creative agent's goals:
- "Discover 10 new materials" (priority: 0.9)
- "Create beautiful art" (priority: 0.8)

# Social agent's goals:
- "Make 5 close friends" (priority: 0.9)
- "Organize community celebrations" (priority: 0.7)

# Family-oriented agent's goals:
- "Find a romantic partner" (priority: 0.9)
- "Have children and raise them well" (priority: 0.8)
```

Goals influence decision-making:
- Agent pursuing wealth will prioritize trading and gathering valuable resources
- Creative agent will experiment more and take creative actions
- Social agent will spend more time socializing and building relationships

---

## 💾 Memory System

Agents remember significant events:

```python
# Automatic memory storage for:

# Life events
agent.memory.remember(
    tick=1000,
    event_type="birth",
    description="My child Luna was born!",
    emotional_intensity=0.9,
    importance=1.0,
    participants=[partner_id, baby_id]
)

# Discoveries
agent.memory.remember(
    tick=2000,
    event_type="discovery",
    description="I discovered how to make bronze!",
    emotional_intensity=0.8,
    importance=0.9
)

# Failures (they learn!)
agent.memory.remember(
    tick=3000,
    event_type="failure",
    description="My experiment exploded and injured me",
    emotional_intensity=0.7,
    importance=0.7
)
```

Memories influence future decisions:
- Agent who got injured in explosion will be more careful
- Agent who succeeded in trading will try trading again
- Agent who made friends while socializing will socialize more

---

## 🔧 Configuration Options

In `.env`:

```bash
# Enable/disable LLM decisions
USE_LLM_DECISIONS=true  # Set to false for rule-based only

# How often agents think long-term (in ticks)
LONG_TERM_PLANNING_INTERVAL=100  # Lower = more frequent planning

# How often agents reflect (in ticks)
REFLECTION_INTERVAL=500  # Lower = more frequent reflection

# Ollama settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b  # Or phi3:mini for faster, mistral:7b for smarter
```

---

## 📈 Monitoring & Debugging

### Check LLM Usage Stats

```python
# In your simulation
stats = llm_brain.get_stats()
print(stats)

# Output:
{
    "total_decisions": 1523,
    "provider_usage": {
        "groq": 450,
        "gemini_flash": 200,
        "together": 300,
        "ollama": 573
    },
    "rate_limits": {
        "groq": {"minute": 12, "day": 450},
        "gemini_flash": {"minute": 5, "day": 200}
    }
}
```

### Enable Debug Logging

```python
import logging

# See all agent decisions
logging.basicConfig(level=logging.INFO)

# See LLM calls and responses
logging.getLogger('agents.llm_brain').setLevel(logging.DEBUG)
logging.getLogger('agents.autonomous_agent').setLevel(logging.DEBUG)
```

Example output:
```
[INFO] 🧠 Zara thinking via groq: decide_action
[DEBUG] [Zara] Chose experiment based on: I'm feeling creative and want to discover...
[INFO] 🎯 [Zara] New goal: Discover new knowledge (priority: 0.85)
[INFO] 💭 Marcus is reflecting on their life...
```

---

## 🎨 Customization

### Change How Often Agents Think

```python
# Make agents plan more frequently
config.long_term_planning_interval = 50  # Every 50 ticks instead of 100

# Make agents reflect more often
config.reflection_interval = 200  # Every 200 ticks instead of 500
```

### Add Custom Thinking Modes

In `llm_brain.py`, add new thinking modes:

```python
def agent_think(self, agent, perceptions, thinking_mode="decide_action"):
    # Add custom mode
    if thinking_mode == "moral_dilemma":
        prompt = f"{context}\n\nYou face a moral choice. What do you do?"
        # ... rest of code ...
```

### Extend Memory Types

In `autonomous_agent.py`:

```python
# Add specialized memory types
class SkillMemory:
    """Remember what worked and what didn't"""
    def __init__(self):
        self.successes = {}  # action -> success_count
        self.failures = {}   # action -> failure_count
```

---

## ❓ Troubleshooting

### "Ollama not running"
```bash
# Start Ollama
ollama serve

# In another terminal, test it
ollama run llama3.2:3b "Hello"
```

### "API key invalid"
- Check `.env` file has correct keys (no quotes, no spaces)
- Try regenerating keys from provider websites
- Set `USE_LLM_DECISIONS=false` to disable cloud APIs temporarily

### "Agents making random decisions"
- Check if Ollama is running: `curl http://localhost:11434`
- Enable debug logging to see what LLM is returning
- Try a larger model: `ollama pull mistral:7b` and update `.env`

### "Too slow"
- Use faster providers first (Groq is fastest)
- Reduce planning frequency: `LONG_TERM_PLANNING_INTERVAL=200`
- Use smaller Ollama model: `ollama pull phi3:mini`
- Disable reflection: `REFLECTION_INTERVAL=999999`

### "Running out of free API calls"
- System automatically falls back to Ollama (unlimited)
- Add more free API providers (Hugging Face has 30k/month)
- Reduce simulation speed to spread calls over time

---

## 🎉 What's Next?

Your agents now have TRUE AUTONOMY! They will:

✅ Set their own life goals based on personality
✅ Remember their experiences and learn from them
✅ Make creative decisions using AI reasoning
✅ Reflect on their life and grow over time
✅ Pursue different paths (wealth, family, knowledge, etc.)
✅ Surprise you with emergent behavior

**Watch them build civilization from nothing - their way!**

---

## 🛠️ Example: Full Integration

```python
# main.py
from agents.llm_brain import MultiLLMBrain
from config import load_config
from engine.simulation import Simulation

def main():
    # Load config
    config = load_config()
    config.print_status()

    # Create simulation with LLM brain
    sim = Simulation(config=config)

    print("\n🌍 NEURONAUT WORLD - TRUE AI AUTONOMY")
    print("=" * 50)
    print(f"Agents: {len(sim.world.agents)}")
    print(f"LLM Providers: {', '.join(config.get_available_providers())}")
    print(f"Full Autonomy: {'✅ ENABLED' if config.use_llm_decisions else '❌ DISABLED'}")
    print("=" * 50)
    print("\nWatch agents live their lives with complete freedom!\n")

    # Run simulation
    sim.run()

if __name__ == "__main__":
    main()
```

---

## 📚 Further Reading

- `agents/llm_brain.py` - Multi-LLM system implementation
- `agents/autonomous_agent.py` - Goal planning & memory systems
- `config.py` - Configuration loader
- `.env.example` - Configuration template

**Questions?** Check the code comments - everything is documented!

---

**Built with ❤️ for TRUE AI AUTONOMY**
