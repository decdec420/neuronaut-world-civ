# TRUE PURPOSE SYSTEM
## Creating Meaningful Decisions That Matter

Every action an agent takes should answer these questions:
1. **WHY** are they doing this? (What need drives it?)
2. **WHO** are they as a person? (Does this match their personality?)
3. **CAN** they do it? (What are their skills and confidence?)
4. **WHAT** do they expect? (What outcome are they hoping for?)
5. **DID IT WORK?** (How do we measure success/failure?)

---

## The Problem We're Solving

Currently, agents act somewhat randomly. Looking at Mororos's card:
- **Needs**: Hunger 68%, Meaning 82%, Security 94%
- **Personality**: High risk_taking (76%), low aggression (25%)
- **Current Action**: "trade"

**Questions:**
- Why is Mororos trading when hunger is at 68%?
- Does trading match their high risk-taking personality?
- Will this improve their "Meaning" need (82%)?
- How do we know if this trade succeeded or failed?

---

## The Solution: Holistic Purpose Evaluation

### 1. **ActionPurpose** - The "WHY" Behind Every Decision

When Mororos decides to experiment, the system evaluates:

```python
ActionPurpose(
    # PRIMARY DRIVER
    primary_need=NeedType.MEANING,  # Experimenting gives meaning
    primary_need_urgency=0.82,  # Their meaning need is at 82%

    # SECONDARY BENEFITS
    secondary_needs=[NeedType.CREATIVITY, NeedType.ACHIEVEMENT],

    # PERSONALITY FIT
    personality_fit=0.85,  # HIGH! Matches their risk-taking (76%)
    personality_reasoning="High openness and risk_taking make experimenting appealing",

    # SKILL READINESS
    skill_level=0.13,  # They have experiment_skill of 13%
    skill_confidence=0.35,  # Low skill but high risk-taking boosts confidence

    # RISK ASSESSMENT
    risk_level=0.6,  # Experimenting is moderately risky
    risk_tolerance=0.76,  # They LOVE risk!

    # EXPECTED OUTCOME
    expected_need_satisfaction={
        NeedType.MEANING: 0.45,  # Expect 45% satisfaction
        NeedType.CREATIVITY: 0.40,
        NeedType.ACHIEVEMENT: 0.35
    },
    expected_life_satisfaction_change=+0.15,  # Expect to feel better!

    # FULL REASONING
    reasoning_summary="""
        I'm urgently driven by my search for purpose.
        High openness and risk_taking make this feel natural to me.
        I'm inexperienced, but I need to try.
        This is risky, but I enjoy taking chances.
        If I discover something new, it will give my life meaning.
    """
)
```

**This is what shows in their card's chain-of-thought!**

---

### 2. **ActionOutcome** - The "DID IT WORK?" Measurement

After Mororos experiments and discovers "compressed_wood":

```python
ActionOutcome(
    # SUCCESS/FAILURE
    succeeded=True,

    # NEED CHANGES (what actually happened)
    need_changes={
        NeedType.MEANING: +0.35,  # Meaning improved by 35%!
        NeedType.CREATIVITY: +0.30,
        NeedType.ACHIEVEMENT: +0.25,
        NeedType.HUNGER: -0.10  # BUT hunger got worse (used energy)
    },

    # LIFE SATISFACTION
    life_satisfaction_before=0.62,
    life_satisfaction_after=0.74,
    life_satisfaction_delta=+0.12,  # IMPROVED!

    # SKILL GROWTH
    skill_growth=0.03,  # experiment_skill: 13% → 16%
    skill_name="experiment_skill",

    # EMOTIONAL IMPACT
    emotions_triggered={
        'joy': 0.45,  # Felt joy from success
        'pride': 0.50,  # Felt pride from achievement
        'excitement': 0.40
    },

    # ECONOMIC IMPACT
    wealth_change=0,  # Didn't make money
    resources_lost={'wood': 1, 'stone': 1},  # Used materials

    # MEMORY
    memorable=True,  # Big life satisfaction change = memorable!
    emotional_impact=+0.12,

    # OUTCOME NARRATIVE
    what_happened="I discovered compressed_wood by pressing materials together!",
    why_it_worked="I successfully addressed my search for meaning. My willingness to take risks helped.",
    lesson_learned="Experimenting is a good choice for satisfying my search for purpose."
)
```

---

## Success Metrics - What Makes an Action Successful?

### Multi-Dimensional Success Scoring

An action is considered **successful** if:

1. **Primary Need Satisfied** (40% weight)
   - Did the need level decrease?
   - By how much?
   - Was it the most urgent need?

2. **Life Satisfaction Improved** (30% weight)
   - Overall happiness increased
   - Multiple needs improved
   - No critical needs worsened

3. **Skill Growth** (10% weight)
   - Agent learned something
   - Can do it better next time

4. **Personality Alignment** (10% weight)
   - Action matched who they are
   - Feels authentic/natural

5. **Social/Economic Gains** (10% weight)
   - Relationships improved
   - Wealth increased
   - Status enhanced

### Example: Trade Action

**Mororos trades with Velix:**

```
PRIMARY NEED: Resources (need level: 0.93)
PERSONALITY FIT: 0.45 (medium - not very extraverted)
SKILL: trade_skill = 0.11

OUTCOME:
✓ Got 5 food, 3 wood
✓ Resources need: 0.93 → 0.75 (improved 18%)
✓ Friendship with Velix: 60 → 65 (improved!)
✗ Hunger worsened: 0.68 → 0.72 (cost energy)
✓ Life satisfaction: 0.62 → 0.66 (+0.04)

SUCCESS SCORE:
- Need satisfied: 0.18 * 40% = 7.2%
- Life improved: 0.04 * 30% = 1.2%
- Skill growth: 0.02 * 10% = 0.2%
- Personality fit: 0.45 * 10% = 4.5%
- Social gain: 0.05 * 10% = 0.5%

TOTAL: 13.6% success

VERDICT: Moderate success
- Addressed urgent need for resources
- Made friend happier
- But cost energy, worsening hunger
```

---

## Influence & Success Metrics in Agent Card

### New Metrics to Add to Each Agent Card:

#### 1. **Purpose Clarity** (0-100)
How clear is their current life purpose?
- Based on: Meaning need, recent achievement, life satisfaction
- Mororos: 44 (struggling to find meaning - at 82% need)

#### 2. **Decision Quality** (0-100)
How good are their recent decisions?
- Based on: Average success scores from last 10 actions
- Mororos: 23 (low - making risky choices with low skills)

#### 3. **Influence** (0-100) - **ALREADY EXISTS**
How much they affect others
- Based on: Teaching sessions, relationship count, status
- Mororos: 33

#### 4. **Life Trajectory** (↑ ↓ →)
Is their life getting better or worse?
- ↑ Improving: Life satisfaction trending up
- ↓ Declining: Life satisfaction trending down
- → Stable: No major changes

#### 5. **Most Urgent Need** (visible label)
What's driving their behavior RIGHT NOW?
- Mororos: "SEEKING MEANING" (82% need)

#### 6. **Personality-Action Alignment** (0-100)
Are they being true to themselves?
- Based on: Average personality_fit of recent actions
- Mororos: High alignment when experimenting, low when trading

---

## Integration with Agent Card UI

### Current Action Display Enhancement

**Before:**
```
⚙️ trade
```

**After:**
```
⚙️ Trading (to satisfy RESOURCES need - 93% urgent)
💭 "I need materials to feel secure, though this doesn't excite me much."
📊 Expected Success: 45% | Personality Fit: 40%
```

### Hover/Click Tooltip Shows Full Purpose:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💭 WHY AM I DOING THIS?

PRIMARY DRIVER:
🎯 Resources Need (93% urgent)
   I desperately need materials to feel secure.

PERSONALITY FIT: 40%
⚠️ Low extraversion makes trading less appealing,
   but necessity drives me.

SKILL LEVEL: 11%
⚠️ I'm inexperienced at trading.

EXPECTED OUTCOME:
✓ Resources: -30% need
✓ Belonging: -10% need
✗ Hunger: +5% need (costs energy)

CONFIDENCE: 35%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### After Action Completes, Show Outcome:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ OUTCOME: MODERATE SUCCESS (58%)

WHAT HAPPENED:
I traded with Velix and got 5 food, 3 wood.

NEED CHANGES:
✓ Resources: 93% → 75% (improved!)
✓ Belonging: 100% → 95% (social contact)
✗ Hunger: 68% → 72% (got hungry)

LIFE SATISFACTION: 62% → 66% (+4%)

EMOTIONS FELT:
😊 Joy (mild)
😌 Relief (moderate)

WHAT I LEARNED:
"Trading works for getting resources, but
I need to eat first next time."

SKILL GROWTH:
trade_skill: 11% → 13%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Linking to Experimentation

Your experiment system already has intent! Now we make it even deeper:

### Experiment Intent Enhancement

**Current:**
```python
ExperimentIntent(
    problem="I'm hungry",
    goal="Make food more nutritious",
    reasoning="Heat made food better before",
    hypothesis="This should work",
    motivation="hunger"
)
```

**Enhanced with Full Psychology:**
```python
ExperimentIntent(
    # NEEDS-DRIVEN
    primary_need=NeedType.HUNGER,
    primary_need_urgency=0.76,
    secondary_needs=[NeedType.CREATIVITY, NeedType.ACHIEVEMENT],

    # PERSONALITY-INFLUENCED
    personality_fit=0.72,
    personality_factors={
        'openness': 0.68,  # Moderate openness
        'creativity': 0.43,  # Low creativity
        'risk_taking': 0.76  # HIGH - willing to try
    },

    # SKILL-INFORMED
    experiment_skill=0.12,
    confidence=0.45,  # Low skill but high risk tolerance

    # EMOTIONAL STATE
    emotions_influencing=['hunger_anxiety', 'curiosity'],

    # SOCIAL CONTEXT
    observed_someone_else_experiment=True,
    wants_to_impress_agent_id="Velix",

    # FULL REASONING
    reasoning="""
        I'm desperately hungry (76% urgent need).

        My high risk-taking personality makes me willing to try
        new things even though I lack experience (12% skill).

        I saw Velix discover something yesterday, and I want to
        prove I can do it too (status need).

        If I can make food more nutritious, I'll satisfy my hunger
        AND feel accomplished. Worth the risk of wasting materials.
    """
)
```

---

## Implementation Roadmap

### Phase 1: Core Integration (2-3 hours)
1. Import `PurposefulActionEvaluator` into agent decision system
2. For each action, generate `ActionPurpose` BEFORE executing
3. Store purpose in action context
4. After action completes, generate `ActionOutcome`
5. Feed outcome back to agent memory and needs

### Phase 2: UI Display (1-2 hours)
1. Update agent card to show:
   - Current action + primary need driving it
   - Personality fit indicator
   - Expected vs actual outcomes
2. Add tooltip with full purpose reasoning
3. Show outcome narrative after actions complete

### Phase 3: Experiment Integration (1 hour)
1. Merge experiment intent with action purpose
2. Show full psychological drivers in experiment modal
3. Display outcome measurement for experiments

### Phase 4: Learning Loop (2 hours)
1. Agents remember which actions successfully satisfied needs
2. Prefer actions that match personality AND have succeeded before
3. Learn which actions to avoid based on past failures
4. Develop personal "strategies" over time

---

## Success Metrics Summary

| Metric | What It Measures | How It's Calculated |
|--------|------------------|---------------------|
| **Action Success Rate** | % of actions that improved life | (successful actions / total actions) * 100 |
| **Need Satisfaction** | How well needs are being met | Average of (1 - need_level) across all needs |
| **Life Trajectory** | Is life getting better? | Linear regression of life_satisfaction over time |
| **Purpose Clarity** | Do they know what they want? | Inverse of "meaning" need level |
| **Decision Quality** | Are they making good choices? | Average success score of recent actions |
| **Personality Alignment** | Being true to themselves? | Average personality_fit of recent actions |
| **Skill-Action Match** | Doing what they're good at? | Correlation between action choice and skill level |
| **Influence** | Impact on others | Teaching count + relationship strength + status |

---

## Example: Full Life Cycle of a Decision

### 1. Decision Point
Mororos has multiple needs:
- Hunger: 76% (urgent)
- Meaning: 82% (very urgent)
- Resources: 93% (desperate!)

### 2. Purpose Evaluation
System evaluates each possible action:

**Gather Food:**
- Addresses: Hunger (primary)
- Personality fit: 40% (low - not conscientiousness)
- Skill: 12%
- Expected success: 55%

**Experiment:**
- Addresses: Meaning (primary), Creativity, Achievement
- Personality fit: 85% (high - matches risk-taking)
- Skill: 13%
- Expected success: 45%

**Trade:**
- Addresses: Resources (primary), Belonging
- Personality fit: 45% (medium)
- Skill: 11%
- Expected success: 50%

### 3. Decision (Personality-Weighted)
Despite Resources being most urgent (93%), Mororos chooses **Experiment** because:
- High personality fit (85%) outweighs lower expected success
- Meaning need (82%) is very high AND matches personality
- Risk-taking personality prefers exciting actions

### 4. Execution
Mororos experiments with wood + stone using compress method.

### 5. Outcome Measurement
```
SUCCESS!
- Discovered "compressed_wood"
- Meaning: 82% → 54% (massive improvement!)
- Achievement: 100% → 75%
- Resources: 93% → 97% (worsened - used materials)
- Life satisfaction: 62% → 74% (+12%)

Overall Success Score: 78%
```

### 6. Learning & Memory
Mororos creates memorable experience:
```
Memory(
    event="Successful experiment",
    emotional_impact=+0.12,
    lesson="Experimenting satisfies my need for meaning"
)
```

### 7. Future Impact
Next time Mororos faces high Meaning need:
- Will prefer experimenting (learned it works)
- Confidence in experiment_skill increases
- More likely to choose personality-aligned actions

---

## This Creates TRUE MEANING

Every action now has:
✅ **Clear purpose** - Driven by real psychological needs
✅ **Personality integration** - Actions match who they are
✅ **Measurable success** - Multi-dimensional outcome scoring
✅ **Learning feedback** - Agents improve decision-making over time
✅ **Visible reasoning** - Players see the full thought process
✅ **Life impact** - Actions meaningfully change agent's wellbeing

**Agents no longer act randomly - they act PURPOSEFULLY.**
