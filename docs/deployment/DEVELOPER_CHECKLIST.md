# 🔍 Developer Checklist - What You Don't Know You Don't Know

## For People Who "Don't Code" But Are Building Cool Shit

This is everything an experienced developer would check that you probably wouldn't think of.

---

## 🐛 **1. Error Handling & Edge Cases**

### What Could Go Wrong?

#### **A. Attribute Errors (Like the one we just fixed!)**
- **Problem**: Code tries to access `agent.needs.social` but that attribute doesn't exist
- **Why it happens**: Someone added a feature but didn't update all the places that use it
- **How to catch it**:
  ```bash
  # Search for all uses of .needs
  grep -r "\.needs\." --include="*.py"

  # Look for AttributeError in logs
  grep "AttributeError" logs/*.log
  ```
- **Prevention**: Use `hasattr()` checks or `getattr()` with defaults

#### **B. Division by Zero**
- **Problem**: `total_wealth / num_agents` when `num_agents = 0`
- **Where to look**:
  - Any calculation with division
  - Averages, percentages, ratios
- **Quick fix**: Always check if denominator is zero first

#### **C. None Values**
- **Problem**: `agent.location.x` when `agent.location` is `None`
- **Common in**:
  - New features before full initialization
  - Optional fields
  - Data from external sources
- **Quick check**:
  ```python
  if agent.location is not None:
      x = agent.location.x
  ```

#### **D. List/Dict Access**
- **Problem**: `agents[5]` when list only has 3 items
- **Problem**: `resources['gold']` when 'gold' key doesn't exist
- **Better way**:
  ```python
  resources.get('gold', 0)  # Returns 0 if gold doesn't exist
  ```

---

## 🔄 **2. State Management & Synchronization**

### Is Everything in Sync?

#### **A. Multiple Data Sources**
You have:
- Agent data in `simulation.world.agents`
- Cached data in `simulation.agent_cache`
- UI data sent via WebSocket
- Database/file persistence (if you add it later)

**Problem**: One gets updated, others don't

**How to check**:
```bash
# Search for places agents are created/modified
grep -r "Agent(" --include="*.py"
grep -r "\.agents\." --include="*.py"

# Make sure cache is updated everywhere
grep -r "agent_cache" --include="*.py"
```

**Best practice**: Update everything in ONE place (like a method that handles all updates)

#### **B. Race Conditions**
- **Problem**: Two things try to modify the same data at the same time
- **Common with**: WebSockets, async code, multi-threading
- **Symptoms**:
  - Random crashes
  - Data corruption
  - Works sometimes, fails other times
- **Where to look**:
  - Anything with `async`/`await`
  - WebSocket handlers
  - Background tasks

#### **C. Stale Data**
- **Problem**: UI shows old information
- **Causes**:
  - WebSocket not updating
  - Cache not cleared
  - Client-side caching
- **Quick test**: Refresh browser, does it fix it?

---

## 💾 **3. Memory & Performance**

### Will It Scale?

#### **A. Memory Leaks**
- **Problem**: Program uses more and more RAM over time
- **Common causes**:
  - Lists that grow forever (event logs, history)
  - Cache that's never cleared
  - Circular references
- **How to check**:
  ```bash
  # Run simulation for 1 hour, watch RAM usage
  top -p $(pgrep python)

  # Or use htop, better visualization
  htop
  ```
- **Symptoms**:
  - Slow down over time
  - Eventually crashes
  - System becomes unresponsive

**Quick fixes**:
- Limit list sizes: `events = events[-1000:]  # Keep only last 1000`
- Clear old data periodically
- Use generators instead of lists for big data

#### **B. Performance Bottlenecks**
- **Problem**: Simulation slows down as it grows
- **Common culprits**:
  - Nested loops (O(n²) or worse)
  - Searching lists repeatedly
  - LLM calls in tight loops
  - Canvas rendering every frame

**How to profile**:
```python
import cProfile
cProfile.run('simulation.tick()', 'output.prof')

# View results
python -m pstats output.prof
```

**Red flags**:
- Loop inside a loop inside a loop
- Calling LLM 100 times per tick
- Redrawing entire canvas when only one agent moved

#### **C. Database/File I/O**
Even though you don't have a database yet, when you add one:
- **Problem**: Writing to disk on every tick = SLOW
- **Better**: Batch writes (write every 10 ticks)
- **Even better**: Use in-memory DB with periodic snapshots

---

## 🌐 **4. Network & API Issues**

### External Dependencies

#### **A. API Rate Limits**
You're using LLMs (Groq, Gemini, etc.):
- **Problem**: Hit rate limit, simulation stops
- **Current protection**: Provider rotation
- **What to add**:
  - Exponential backoff
  - Queue system
  - Local fallback (simpler AI for non-critical decisions)

**Check your limits**:
```bash
# Count API calls in logs
grep "LLM call" logs/*.log | wc -l

# See which provider is used most
grep "Using provider" logs/*.log | sort | uniq -c
```

#### **B. Network Timeouts**
- **Problem**: API call hangs forever
- **Solution**: Always set timeouts
  ```python
  response = requests.get(url, timeout=10)  # 10 second max
  ```

#### **C. API Key Issues**
- **Problem**: Keys expire, get revoked, or hit spending limits
- **How to check**:
  ```bash
  # Test each API key
  curl -H "Authorization: Bearer $GROQ_API_KEY" \
       https://api.groq.com/v1/models
  ```
- **What to monitor**: Error rates, failed requests

---

## 🗂️ **5. Data Integrity & Validation**

### Is Your Data Correct?

#### **A. Data Types**
- **Problem**: Expecting int, got string
- **Example**: `age = "25"` vs `age = 25`
- **Symptoms**: Math operations fail, comparisons wrong
- **Fix**: Use type hints and validation
  ```python
  def create_agent(name: str, age: int) -> Agent:
      assert isinstance(age, int), "Age must be integer"
      assert 0 < age < 120, "Age must be realistic"
  ```

#### **B. Data Ranges**
- **Health**: Should be 0-100, not 150 or -50
- **Coordinates**: Should be within world bounds
- **Probabilities**: Should be 0-1, not 5.3

**Quick validation**:
```python
def validate_agent(agent):
    assert 0 <= agent.health <= 100
    assert 0 <= agent.location.x <= WORLD_WIDTH
    assert 0 <= agent.mood <= 1.0
```

#### **C. Null/Empty Checks**
Before processing data:
```python
if not agents:
    return  # Don't process empty list

if agent is None:
    return  # Don't process null agent
```

---

## 🔐 **6. Security & Safety**

### Even for Local Projects

#### **A. API Keys in Code**
- **NEVER**: `GROQ_API_KEY = "abc123"` in Python files
- **ALWAYS**: Use `.env` files (which are in `.gitignore`)
- **Check**:
  ```bash
  # Search for hardcoded keys
  grep -r "api_key\s*=\s*['\"]" --include="*.py"
  ```

#### **B. User Input Validation**
When you add features where user can:
- Create agents with custom names
- Upload files
- Enter commands

**Always validate**:
- Max length limits
- Allowed characters
- File type/size limits

#### **C. Injection Attacks**
If you ever:
- Build SQL queries from user input
- Execute system commands with user data
- Eval user code

**Use parameterized queries, not string concatenation!**

---

## 📊 **7. Logging & Monitoring**

### How Do You Know It's Working?

#### **A. Log Levels**
Use different levels for different importance:
```python
logging.debug("Agent moved to (5, 10)")      # Details
logging.info("Simulation started")           # Major events
logging.warning("Low health detected")       # Concerns
logging.error("Failed to save state")        # Problems
logging.critical("Simulation crashed!")      # EMERGENCY
```

#### **B. What to Log**
**Too little**: Only errors
**Too much**: Every line of code
**Just right**:
- Major events (births, deaths, conflicts)
- Errors with full context
- Performance metrics (tick time, LLM calls)
- State changes (era transitions, tech unlocks)

#### **C. Log Rotation**
- **Problem**: Log file grows to 10GB
- **Solution**: Rotate daily/weekly
  ```python
  from logging.handlers import RotatingFileHandler

  handler = RotatingFileHandler(
      'game.log',
      maxBytes=10*1024*1024,  # 10MB
      backupCount=5            # Keep 5 old files
  )
  ```

#### **D. Monitoring Dashboard**
Track in real-time:
- ✅ Tick rate (should be steady)
- ✅ Agent count (detect mass deaths)
- ✅ Error rate (should be near zero)
- ✅ Memory usage (should be stable)
- ✅ API call count (watch for spikes)

---

## 🧪 **8. Testing Strategies**

### How Do You Know It Works?

#### **A. Manual Testing Checklist**
Before releasing a feature:
- [ ] Start fresh simulation - does it work?
- [ ] Run for 100 ticks - any errors?
- [ ] Run for 1000 ticks - still stable?
- [ ] Add 50 agents - does it scale?
- [ ] Pause/resume - state preserved?
- [ ] Refresh browser - reconnects?
- [ ] Kill server - graceful shutdown?

#### **B. Edge Case Testing**
Test the extremes:
- **Zero agents**: Does UI show "no agents"?
- **One agent**: No division by zero?
- **1000 agents**: Performance acceptable?
- **Zero resources**: Agents don't crash?
- **Full resources**: No overflow?

#### **C. Chaos Testing**
Intentionally break things:
- Disconnect network mid-simulation
- Fill disk space
- Kill random processes
- Send invalid WebSocket messages
- Corrupt save files

**Goal**: System should fail gracefully, not catastrophically

#### **D. Regression Testing**
After fixing a bug:
1. Write down how to reproduce it
2. Fix the bug
3. Try to reproduce again (should be fixed)
4. Keep that test case for future checks

---

## 🏗️ **9. Architecture & Code Quality**

### Will Future You Hate Current You?

#### **A. Code Duplication**
- **Problem**: Same logic in 5 different places
- **Why bad**: Fix bug once, miss it in 4 other places
- **Solution**: Extract to function/class
  ```python
  # Before: Copy-pasted 10 times
  if agent.health < 20:
      agent.health = 20
      log("Healing agent")

  # After: One function
  def heal_agent(agent, min_health=20):
      if agent.health < min_health:
          agent.health = min_health
          log("Healing agent")
  ```

#### **B. God Objects**
- **Problem**: One class that does EVERYTHING
- **Example**: `SimulationEngine` is 3000+ lines
- **Better**: Break into smaller pieces
  - `EconomyManager`
  - `ConflictResolver`
  - `AgentSpawner`
  - etc.

#### **C. Magic Numbers**
```python
# Bad: What is 0.7?
if agent.mood > 0.7:
    seek_fun()

# Good: Now it's clear
HAPPINESS_THRESHOLD = 0.7
if agent.mood > HAPPINESS_THRESHOLD:
    seek_fun()
```

#### **D. Comments & Documentation**
Comment **why**, not **what**:
```python
# Bad comment
x = x + 1  # Increment x

# Good comment
x = x + 1  # Skip first element (header row)
```

---

## 🔄 **10. Version Control & Deployment**

### Protecting Your Work

#### **A. Git Best Practices**
- **Commit often**: Small, focused commits
- **Good messages**: "Fix agent spawn bug" not "stuff"
- **Branches**: Use feature branches for big changes
- **Backups**: Push to GitHub regularly

#### **B. What to Track**
Track in git:
- ✅ All Python code
- ✅ Config files
- ✅ Documentation
- ✅ Requirements.txt

DON'T track:
- ❌ `.env` files (secrets)
- ❌ `__pycache__` folders
- ❌ Large data files
- ❌ Virtual environments
- ❌ Log files

#### **C. Deployment Checklist**
Before "releasing":
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog written
- [ ] Dependencies listed
- [ ] README accurate

---

## 🛠️ **11. Dependencies & Environment**

### Library Management

#### **A. Requirements.txt**
Always keep updated:
```bash
# Generate current deps
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

#### **B. Version Pinning**
```python
# Loose (dangerous)
fastapi

# Pinned (safe)
fastapi==0.104.1

# Range (flexible but controlled)
fastapi>=0.104.0,<0.105.0
```

#### **C. Virtual Environments**
- **Always use venv**: Keeps project deps isolated
- **Never commit venv**: It's machine-specific
- **Document Python version**: `python --version` in README

---

## 🚨 **12. Common "WTF" Moments**

### Things That Will Confuse You

#### **A. "It works on my machine!"**
- **Causes**:
  - Different Python versions
  - Missing dependencies
  - Environment variables not set
  - OS-specific paths
- **Solution**: Docker, or very detailed setup docs

#### **B. "It worked yesterday!"**
- **Causes**:
  - Someone pushed breaking changes
  - API changed
  - Disk full
  - Certificate expired
- **Solution**: Git blame to see what changed

#### **C. "It only fails sometimes!"**
- **Causes**:
  - Race conditions
  - Random number seed
  - Time-dependent logic
  - API rate limits
- **Solution**: Add more logging, test more times

#### **D. "It's slow after running for a while!"**
- **Causes**:
  - Memory leak
  - Log files growing huge
  - Cache not pruned
  - Database indexes missing
- **Solution**: Profile, monitor, optimize

---

## 📋 **13. Quick Health Check Commands**

### Run These Regularly

```bash
# 1. Check for common errors
grep -i "error\|exception\|failed" logs/*.log | tail -20

# 2. Check memory usage
ps aux | grep python

# 3. Check disk space
df -h

# 4. Check running processes
ps aux | grep neuronaut

# 5. Check port availability
lsof -i :8000

# 6. Check Python syntax
python -m py_compile **/*.py

# 7. Check for TODO/FIXME comments
grep -r "TODO\|FIXME" --include="*.py" | wc -l

# 8. Check file sizes
du -sh logs/ data/ web/

# 9. Check git status
git status

# 10. Check requirements
pip list | grep -E "fastapi|uvicorn|groq"
```

---

## 🎯 **14. Specific to Your Project**

### Neuronaut World Gotchas

#### **A. LLM Dependencies**
- **Check**: All API keys in `.env`
- **Test**: Each provider individually
- **Monitor**: API spend/quota
- **Fallback**: What happens if ALL providers fail?

#### **B. Agent Count Scaling**
- **Current**: 12 agents (fine)
- **Target**: 100+ agents (need to optimize)
- **Bottlenecks**:
  - LLM calls for each agent every tick
  - Canvas redrawing all agents every frame
  - Pathfinding for each agent
- **Solutions**:
  - Batch LLM calls
  - Only redraw changed agents
  - Cache pathfinding results

#### **C. WebSocket Stability**
- **Test**: What if client disconnects?
- **Test**: What if 10 clients connect?
- **Test**: What if client never disconnects for 24 hours?

#### **D. Save/Load System**
You don't have one yet, but you'll need:
- Save entire world state
- Load and resume from save
- Handle incompatible save versions
- Backup saves (don't overwrite only save)

---

## 🎓 **15. Learning Resources**

### Where to Learn More

#### **A. Error Messages**
When you see an error:
1. Read the LAST line (actual error)
2. Read the traceback (where it happened)
3. Google the error + "python"
4. Check Stack Overflow

#### **B. Python-Specific**
- **Type hints**: Make errors obvious before running
- **Linting**: Use `pylint` or `flake8` to catch issues
- **Formatting**: Use `black` for consistent style
- **Testing**: Use `pytest` for automated tests

#### **C. Web Development**
- **FastAPI docs**: fastapi.tiangolo.com
- **WebSocket guide**: Read about ping/pong, reconnection
- **Frontend**: Learn basic JavaScript debugging (F12 console)

---

## ✅ **Your Pre-Launch Checklist**

Before showing to anyone:

### **Functionality**
- [ ] Simulation runs for 10+ minutes without crashes
- [ ] All tabs in UI display data
- [ ] Agents move, act, and evolve
- [ ] WebSocket reconnects if disconnected
- [ ] Speed controls work (pause, 1x, 2x, etc.)
- [ ] Click agent shows detailed info

### **Performance**
- [ ] Tick rate stays consistent
- [ ] Memory usage stable (not growing)
- [ ] Browser doesn't lag/freeze
- [ ] API calls don't hit rate limits

### **User Experience**
- [ ] Clear error messages (not "AttributeError line 2572")
- [ ] Loading states (not blank screens)
- [ ] Tooltips/help text for confusing features
- [ ] Works in Chrome, Firefox, Safari

### **Documentation**
- [ ] README explains how to install
- [ ] README explains how to run
- [ ] ENV variables documented
- [ ] Known issues listed

### **Safety**
- [ ] No API keys in code
- [ ] `.env` in `.gitignore`
- [ ] No passwords in logs
- [ ] Error logs don't leak secrets

---

## 🚀 **Pro Tips for Non-Coders**

1. **Use Claude/ChatGPT to audit code**
   - "Review this code for common bugs"
   - "What edge cases am I missing?"
   - "How can this fail?"

2. **Write down every weird behavior**
   - Keep a "bugs.txt" file
   - Even if you don't know why

3. **Test in weird ways**
   - Click things fast
   - Refresh during actions
   - Leave running overnight
   - Disconnect internet

4. **Ask "What if..."**
   - What if no agents alive?
   - What if disk full?
   - What if API down?
   - What if 1000 users?

5. **Version everything**
   - Before big changes, commit
   - Tag releases: v1.0, v1.1, etc.
   - You can always roll back

6. **Monitor in production**
   - Set up alerts (email when crash)
   - Track uptime
   - Watch error rates

7. **Have a rollback plan**
   - Old version still accessible
   - Backups of data
   - Quick way to revert

---

## 🎉 **Bottom Line**

The fact that you're asking "what am I not thinking about?" means you're already ahead of 90% of people! Most bugs come from:

1. **Not checking if things exist** before using them
2. **Not handling errors** gracefully
3. **Not testing edge cases** (0, 1, 1000, null, empty)
4. **Not monitoring** what's actually happening
5. **Not planning for growth** (will this work with 10x users?)

**Your mantra**: "What could go wrong?" and test it!

---

**Remember**: Every developer has broken something in production. The difference is experienced devs have broken MORE things and learned from it! 🚀😄
