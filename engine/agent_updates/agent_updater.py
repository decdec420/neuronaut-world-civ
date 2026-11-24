"""
Agent Updater - Phase 3 Refactoring
Handles the main agent update loop that was previously in simulation.py lines ~1605-1850

This class is responsible for:
- Updating all agents each tick
- Applying resource sinks, weather effects, disease effects
- Managing births and pregnancy
- Building perceptions
- Making decisions (AI or rule-based)
- Executing actions and measuring outcomes
- Learning from action outcomes
"""

import logging
import random
from typing import Dict, Any, Optional
from agents.agent import Action, ActionType
from agents.daily_life import JOBS, SLEEP, WORK, job_for
from agents.utility_brain import UtilityBrain

logger = logging.getLogger(__name__)


class AgentUpdater:
    """Manages the agent update loop - extracted from simulation.py for Phase 3 refactoring"""

    def __init__(self, simulation):
        """
        Initialize the AgentUpdater with a reference to the main simulation.

        Args:
            simulation: The SimulationEngine instance that contains all subsystems
        """
        self.sim = simulation

        # The rule-based brain weighs every action the engine can run (the same
        # list the AI brain's menu is built from)
        from agents.action_menu import build_menu
        from engine.simulation import UNHANDLED_ACTION_FALLBACKS
        menu = build_menu(simulation._handler_registry, UNHANDLED_ACTION_FALLBACKS)
        self.utility_brain = UtilityBrain(
            simulation, [e.action for entries in menu.by_category.values() for e in entries])

        # The AI brain's calls run in worker threads (agents/thinking.py)
        self.thinking = None
        self._in_tick = False
        brain = getattr(simulation, 'llm_brain', None)
        config = simulation.config
        if config.use_llm_decisions and brain is not None:
            from agents.thinking import ThinkingScheduler
            self.thinking = ThinkingScheduler(
                brain.think,
                workers=config.llm_workers, think_every=config.llm_think_every,
                tick_budget=config.llm_tick_budget)

    async def update_all_agents(self, current_tick: int) -> None:
        """
        Main entry point for updating all agents in the simulation.

        This method:
        1. Iterates through all living agents
        2. Applies environmental effects (weather, disease)
        3. Builds perceptions of the world
        4. Makes decisions (AI or rule-based)
        5. Executes actions and measures outcomes
        6. Tracks learning and role emergence

        Args:
            current_tick: Current simulation tick
        """
        # Get world state once for all agents (performance optimization)
        world_state = self.sim.world.get_state()

        # Agents due to think ask their model now, in parallel; the tick waits
        # a bounded time for the answers (agents/thinking.py)
        # (No model to ask, e.g. Ollama is down: don't build prompts for nobody)
        if self.thinking is not None and self.sim.llm_brain.providers_to_try():
            self.thinking.start([a for a in self.sim.world.agents if a.alive], current_tick,
                                lambda agent: self._next_thought(agent, world_state, current_tick))
            self.thinking.wait()

        # Update all agents with error isolation
        self._in_tick = True
        try:
            for agent in self.sim.world.agents:
                if not agent.alive:
                    if self.thinking is not None:
                        self.thinking.forget(agent.id)
                    continue

                await self._update_single_agent(agent, current_tick, world_state)
        finally:
            self._in_tick = False

    def _wants_to_think(self, agent) -> bool:
        """Whether this agent's own model decides (survival first, babies never)."""
        return (hasattr(agent, 'autonomous_decide') and agent.life_stage != "baby"
                and self._survival_override(agent) is None)

    def _next_thought(self, agent, world_state, current_tick: int):
        """(kind, prompt, schema) for what the agent should think about next,
        Smallville-style: plan its day when it's awake and has no plan for
        today; reflect once enough has happened; otherwise decide what to do."""
        if not self._wants_to_think(agent):
            return None
        perceptions = self.sim._perception_builder.build_perceptions(agent, world_state)
        agent.last_perception = perceptions
        brain, time, stream = self.sim.llm_brain, self.sim.world.time, agent.memory_stream
        if stream.plan_day != time.day and agent.routine.block(time.hour) != SLEEP:
            return ("plan",) + brain.plan_prompt(agent, perceptions, time.day)
        if stream.wants_reflection():
            return ("reflect",) + brain.reflection_prompt(agent, current_tick)
        return "decide", brain._build_thinking_prompt(agent, perceptions, "decide_action"), brain.decision_schema()

    def _apply_thought(self, agent, kind: str, answer: str, current_tick: int) -> None:
        """A day plan or reflection came back: keep it in the memory stream."""
        from agents.action_menu import parse_plan, parse_insights
        stream = agent.memory_stream
        if kind == "plan":
            plan = parse_plan(answer, self.sim.llm_brain.action_menu.names)
            stream.set_plan(self.sim.world.time.day, current_tick, plan)
            self.thinking.stats["plans" if plan else "unreadable_plans"] += 1
        elif kind.startswith("talk:"):
            self._apply_dialogue(agent, kind.split(":", 1)[1], answer, current_tick)
        elif kind == "reflect":
            insights = parse_insights(answer)
            added = stream.reflected(current_tick, insights)
            self.thinking.stats["reflections"] += added
            for insight in insights:
                self.sim.chronicle.voice(current_tick, agent.name, insight)

    async def _update_single_agent(self, agent, current_tick: int, world_state: Dict) -> None:
        """
        Update a single agent with full error isolation.

        This method is wrapped in a try/except to ensure one agent's failure
        doesn't crash the entire simulation.

        Args:
            agent: The agent to update
            current_tick: Current simulation tick
            world_state: Pre-computed world state dict for performance
        """
        try:
            # Update agent state
            agent.update()
        except Exception as e:
            # CRITICAL: Isolate agent failures to prevent cascade
            logger.error(f"❌ Agent {agent.name} ({agent.id}) update failed: {e}")
            logger.exception(e)
            # Mark agent as errored but keep alive
            agent.health = max(0, agent.health - 10)  # Apply damage
            if agent.health <= 0:
                agent.alive = False
                agent.death_cause = "system_error"
                logger.error(f"💀 Agent {agent.name} killed due to critical error")
            return  # Skip rest of update for this agent

        # ===== APPLY RESOURCE SINKS (prevent inflation) =====
        self.sim.system_coordinator.apply_resource_sinks(agent)

        # ===== REPUTATION DECAY (people forget!) =====
        agent.decay_reputation(decay_rate=0.001)  # 0.1% per tick

        # ===== APPLY WEATHER EFFECTS TO AGENT =====
        self._apply_weather_effects(agent)

        # ===== APPLY DISEASE EFFECTS =====
        self._apply_disease_effects(agent, current_tick)

        # ===== CHECK FOR TRESPASSING =====
        self._check_trespassing(agent, current_tick)

        # ===== RANDOM DISEASE INFECTIONS =====
        self._check_random_disease_infection(agent, current_tick)

        # ===== CHECK FOR BIRTHS =====
        await self._check_for_births(agent, current_tick)

        # ===== STRATEGIC PLANNING =====
        self._update_strategic_goals(agent, current_tick)

        # ===== BUILD PERCEPTIONS =====
        perceptions = self.sim._perception_builder.build_perceptions(agent, world_state)
        # The AI brain's prompt reads its context (laws, buildings, combat...) from here;
        # it was never set, so every one of those prompt sections came out empty
        agent.last_perception = perceptions

        # ===== MAKE DECISION =====
        action, current_goal = await self._make_agent_decision(agent, perceptions, current_tick)

        # ===== EXECUTE ACTION WITH PURPOSE TRACKING =====
        await self._execute_action_with_purpose(agent, action, current_goal, current_tick)

    def _apply_weather_effects(self, agent) -> None:
        """
        Apply weather effects to agent (damage, energy drain).

        Args:
            agent: The agent to apply weather effects to
        """
        # Shelter = standing near a finished building (or working on one)
        has_shelter = agent.active_construction_id is not None
        dbs = getattr(self.sim, 'dynamic_building_system', None)
        if not has_shelter and dbs is not None:
            for b in dbs.buildings.values():
                if b.is_complete and not b.collapsed:
                    bx, by = b.location
                    if ((agent.location.x - bx) ** 2 + (agent.location.y - by) ** 2) ** 0.5 < 6:
                        has_shelter = True
                        break
        weather_impact = self.sim.weather.apply_weather_to_agent(
            agent.health,
            agent.energy,
            has_shelter
        )

        # Apply weather damage (storms, blizzards, heat waves)
        if weather_impact['damage'] > 0:
            damage = weather_impact['damage']
            # Resting means hunkering down: partial cover even without a building
            current = getattr(agent, 'current_action', None)
            if current is not None and current.action_type == ActionType.REST:
                damage *= 0.3
            agent.health -= damage
            if agent.health < 30 and not has_shelter:
                logger.warning(f"⚠️  {agent.name} taking weather damage! Health: {agent.health:.1f}")

        # Apply weather energy drain (cold, heat, storms)
        if weather_impact['energy_drain'] > 0:
            agent.energy = max(0, agent.energy - weather_impact['energy_drain'])

    def _apply_disease_effects(self, agent, current_tick: int) -> None:
        """
        Apply disease effects to agent (health damage, energy drain).

        Args:
            agent: The agent to apply disease effects to
            current_tick: Current simulation tick
        """
        agent_diseases = self.sim.health.get_agent_diseases(agent.id)
        for disease in agent_diseases:
            # Apply disease damage and energy drain
            agent.health = max(0, agent.health - disease.health_damage_per_tick)
            agent.energy = max(0, agent.energy - disease.energy_drain_per_tick)

            # Log if health is critically low
            if agent.health < 20 and disease.severity.value in ['severe', 'critical']:
                logger.warning(f"⚠️  {agent.name} critically ill from {disease.disease_type.value}! Health: {agent.health:.1f}")

    def _check_trespassing(self, agent, current_tick: int) -> None:
        """
        Check if agent is trespassing and apply consequences.

        Args:
            agent: The agent to check for trespassing
            current_tick: Current simulation tick
        """
        from engine.psychology import NeedType

        trespassing_territory = self.sim.territory.check_trespassing(
            agent.id,
            (agent.location.x, agent.location.y),
            current_tick
        )

        if trespassing_territory:
            # Agent is trespassing!
            if trespassing_territory.defended:
                # Defended territory - owner might be alerted
                agent.needs.satisfy_need(NeedType.SECURITY, -0.1)  # Feel unsafe

                # Chance of conflict with owner/guards
                if random.random() < 0.05 and trespassing_territory.guards:
                    logger.warning(f"⚔️  {agent.name} caught trespassing in {trespassing_territory.name}!")

    def _check_random_disease_infection(self, agent, current_tick: int) -> None:
        """
        Check for random environmental disease infections.

        Args:
            agent: The agent to check for disease infection
            current_tick: Current simulation tick
        """
        from engine.psychology import NeedType

        # Random disease infections (environmental)
        if random.random() < 0.0005:  # 0.05% chance per tick
            from world.health import DiseaseType, Severity

            # Environmental diseases based on conditions. Need levels run
            # 0 = satisfied -> 1 = desperate; this used to test < 0.3, giving
            # well-fed agents malnutrition (AUDIT.md #9)
            if hasattr(agent, 'needs') and agent.needs.needs.get(NeedType.HUNGER) and agent.needs.needs[NeedType.HUNGER].level > 0.7:
                # Malnutrition from starvation
                self.sim.health.infect_agent(agent.id, DiseaseType.MALNUTRITION, Severity.MODERATE, current_tick)
            elif hasattr(agent, 'needs') and agent.needs.needs.get(NeedType.THIRST) and agent.needs.needs[NeedType.THIRST].level > 0.7:
                # Dehydration
                self.sim.health.infect_agent(agent.id, DiseaseType.DEHYDRATION, Severity.MODERATE, current_tick)
            elif agent.energy < 20:
                # Exhaustion
                self.sim.health.infect_agent(agent.id, DiseaseType.EXHAUSTION, Severity.MILD, current_tick)
            elif self.sim.weather.current_weather.value in ['heat_wave']:
                # Heat stroke
                self.sim.health.infect_agent(agent.id, DiseaseType.HEAT_STROKE, Severity.MODERATE, current_tick)
            else:
                # Random flu
                self.sim.health.infect_agent(agent.id, DiseaseType.FLU, Severity.MILD, current_tick)

    async def _check_for_births(self, agent, current_tick: int) -> None:
        """A pregnancy that has come to term ends in a birth
        (LifecycleManager.deliver_baby is the only way a child is born)."""
        if agent.is_pregnant and current_tick - agent.pregnancy_start_tick >= agent.pregnancy_duration_ticks:
            self.sim.lifecycle_manager.deliver_baby(agent, current_tick)

    def _update_strategic_goals(self, agent, current_tick: int) -> None:
        """
        Update agent's strategic goals using the StrategicPlanner.

        Args:
            agent: The agent to update strategic goals for
            current_tick: Current simulation tick
        """
        from agents.strategy import StrategicPlanner

        # Strategic planning - agent chooses/updates goals
        if self.sim.strategy_manager.should_pursue_new_goal(agent.id, agent):
            world_context = {
                'has_rivals': len(self.sim.warfare_manager.get_agent_conflicts(agent.id)) > 0,
                'nearby_agents': len([a for a in self.sim.world.agents
                                    if a.alive and a.location.distance_to(agent.location) < 20]),
            }
            new_goal = StrategicPlanner.choose_goal(agent, world_context)
            if new_goal:
                self.sim.strategy_manager.add_goal(agent.id, new_goal)

    async def _make_agent_decision(self, agent, perceptions: Dict, current_tick: int):
        """
        Make a decision for the agent using AI or rule-based logic.

        Args:
            agent: The agent making the decision
            perceptions: Perceptions of the world built by PerceptionBuilder
            current_tick: Current simulation tick

        Returns:
            Tuple of (action, current_goal) where current_goal may be None
        """
        from agents.agent import Action, ActionType

        # Initialize current_goal for later use
        current_goal = None

        # ===== AI-POWERED DECISION MAKING =====
        # The agent's own model decides when it has an answer ready
        # (agents/thinking.py); otherwise the rule-based brain below
        llm_action = None
        if self.thinking is not None and self._wants_to_think(agent):
            result = self.thinking.take(agent.id, current_tick)
            if result is None and not self._in_tick and self.thinking.is_due(agent.id, current_tick) \
                    and self.sim.llm_brain.providers_to_try():
                # Asked outside a tick (a tool or a test): think now, within the budget
                brain = self.sim.llm_brain
                self.thinking.submit(agent.id, brain._build_thinking_prompt(agent, perceptions, "decide_action"),
                                     current_tick, "decide", brain.decision_schema())
                self.thinking.wait()
                result = self.thinking.take(agent.id, current_tick)
            if result is not None and result[0] != "decide":
                self._apply_thought(agent, result[0], result[1], current_tick)
            elif result is not None:
                llm_action = agent._parse_action_from_llm(result[1].strip(), perceptions)
            # Unusable answer: use the rule-based brain below
            if llm_action is not None and llm_action.action_type in (ActionType.IDLE, ActionType.WAIT):
                llm_action = None
            if llm_action is not None and not self._can_run(agent, llm_action):
                self.thinking.stats["not_possible"] += 1
                llm_action = None

        if llm_action is not None:
            action = llm_action
            current_goal = self.sim.strategy_manager.get_current_goal(agent.id)
            # Until it thinks again, the rule-based brain leans toward this
            agent.ai_intent = (self._resolved_name(action), current_tick + self.thinking.think_every)
            self.thinking.stats["used"] += 1
            self.sim.chronicle.on_choice(current_tick, agent, self._resolved_name(action),
                                         action.parameters.get('reason', ''))
        else:
            # Rule-based brain: survival first, then every runnable action
            # weighed by the agent's needs, personality, memory, people and day plan
            current_goal = self.sim.strategy_manager.get_current_goal(agent.id)
            survival_action = self._survival_override(agent)
            part_of_day = agent.routine.block(self.sim.world.time.hour)
            if survival_action is not None:
                # Urgent physical needs always come first
                action = survival_action
            else:
                goal_action = None
                intent = getattr(agent, 'ai_intent', None)
                planned = agent.memory_stream.planned_action(self.sim.world.time.hour)
                if intent is not None and current_tick <= intent[1]:
                    goal_action = intent[0]  # what its own model last decided
                elif planned:
                    from engine.simulation import UNHANDLED_ACTION_FALLBACKS
                    goal_action = UNHANDLED_ACTION_FALLBACKS.get(planned, planned)  # its plan for this hour
                elif current_goal:
                    from engine.simulation import UNHANDLED_ACTION_FALLBACKS
                    step = self.sim.strategy_manager.evaluate_goal_action(agent, current_goal)
                    goal_action = UNHANDLED_ACTION_FALLBACKS.get(step, step) if step else None
                action = self.utility_brain.choose(
                    agent, perceptions, lambda a: self._can_run(agent, a), part_of_day, goal_action)
            # Work done in work hours counts toward the agent's job
            agent.shift_job = job_for(self._resolved_name(action), agent.work_life.job) if part_of_day == WORK else None
        agent.current_action = action
        return action, current_goal

    def _apply_dialogue(self, agent, other_id: str, answer: str, current_tick: int) -> None:
        """A conversation the model wrote: both remember it; the village log
        and the chronicle keep its words."""
        from agents.action_menu import parse_dialogue
        from engine.events import EventCategory, EventImportance
        other = self.sim._get_agent_by_id(other_id)
        if other is None:
            return
        lines = parse_dialogue(answer, {agent.name, other.name})
        if not lines:
            self.thinking.stats["unreadable_talks"] += 1
            return
        self.thinking.stats["talks"] += 1
        said = " / ".join(f"{who}: {text}" for who, text in lines)
        for who in (agent, other):
            who.memory_stream.add(current_tick, f"Talked with {other.name if who is agent else agent.name}: {said}", 0.4)
        self.sim.chronicle.voice(current_tick, lines[0][0], lines[0][1], about=f"talking with "
                                 f"{other.name if lines[0][0] == agent.name else agent.name}")
        self.sim.event_logger.log_event(EventCategory.SOCIAL, EventImportance.MINOR,
                                        f"💬 {agent.name} and {other.name} talked", said[:300],
                                        current_tick, [agent.id, other.id])

    def _move_into(self, agent, building_id, current_tick: int) -> None:
        """A finished shelter becomes home to its builders who have none, and
        to their partners and young children who have none (life/homes.py)."""
        from life import homes, family
        dbs, events = self.sim.dynamic_building_system, self.sim.life_events
        building = dbs.buildings.get(building_id)
        if building is None or not homes.is_shelter(dbs, building):
            return
        for builder_id in sorted(building.builder_ids | {agent.id}):
            builder = self.sim._get_agent_by_id(builder_id)
            if builder is None or not builder.alive:
                continue
            homes.move_in(dbs, builder, building, current_tick, "I built it", events)
            partner = family.partner_of(builder, self.sim._get_agent_by_id)
            if partner is not None:
                homes.move_in(dbs, partner, building, current_tick, f"{builder.name} built it", events)
            for child_id in builder.children_ids:
                child = self.sim._get_agent_by_id(child_id)
                if child is not None and family.is_young(child):
                    homes.move_in(dbs, child, building, current_tick, f"{builder.name} built it", events)

    def _converse(self, agent, action, current_tick: int) -> None:
        """Talking passes news on (world/news.py): socializing both ways, a
        story one way. With a model, the two may also have a few lines of
        dialogue, written in the background (kind "talk")."""
        name = self._resolved_name(action)
        if name not in ('socialize', 'tell_story') or not action.target_agent:
            return
        other = self.sim._get_agent_by_id(action.target_agent)
        if other is None or not other.alive:
            return
        passed = self.sim.news.converse(agent, other, current_tick, both_ways=(name == 'socialize'))
        thinking = self.thinking
        if (thinking is not None and name == 'socialize' and self._wants_to_think(agent)
                and hasattr(other, 'autonomous_decide') and agent.id not in thinking.pending
                and agent.id not in thinking.ready and len(thinking.pending) < thinking.workers
                and self.sim.llm_brain.providers_to_try()):
            prompt, schema = self.sim.llm_brain.dialogue_prompt(agent, other, passed, current_tick)
            thinking.submit(agent.id, prompt, current_tick, f"talk:{other.id}", schema)

    def _remember_action(self, agent, action, outcome: Dict, current_tick: int) -> None:
        """A first-person memory of what the agent did and how it went; what
        moved it more (or failed) matters more."""
        name = self._resolved_name(action).replace('_', ' ')
        target = self.sim._get_agent_by_id(action.target_agent) if action.target_agent else None
        doing = name + (f" with {target.name}" if target is not None else "")
        succeeded = bool(outcome.get('success', False))
        message = str(outcome.get('message', '') or '').strip()
        text = (doing[0].upper() + doing[1:] if succeeded else f"Tried to {doing}") + (f": {message}" if message else "")
        try:
            impact = abs(float(outcome.get('emotional_impact', 0.0) or 0.0))
        except (TypeError, ValueError):
            impact = 0.0
        importance = 0.1 + 0.4 * min(1.0, impact) + (0.0 if succeeded else 0.1)
        agent.memory_stream.add(current_tick, text, importance)

    @staticmethod
    def _snapshot_needs(needs):
        """A copy of an agent's need levels."""
        from engine.psychology import NeedState, Need
        return NeedState(needs={t: Need(t, n.level, n.priority, n.decay_rate) for t, n in needs.needs.items()})

    @staticmethod
    def _success_score(action_outcome, action_succeeded: bool) -> float:
        """0-1: 0 if the action failed; otherwise 0.5-1 by how much better off
        it left the agent. (This called SimulationEngine._calculate_success_score,
        which never existed; the error was swallowed, so nothing was recorded.)"""
        if not action_succeeded:
            return 0.0
        lift = max(0.0, min(1.0, 0.5 + 10.0 * action_outcome.life_satisfaction_delta))
        return 0.5 + 0.5 * lift

    @staticmethod
    def _resolved_name(action) -> str:
        """The action that will actually run (aliases resolve to their action)."""
        from engine.simulation import UNHANDLED_ACTION_FALLBACKS
        name = action.action_type.value
        return UNHANDLED_ACTION_FALLBACKS.get(name, name)

    # Actions that can make something new, and what kind of discovery it is
    INVENTIVE_ACTIONS = {
        'experiment': 'item', 'discover_material': 'item', 'create_alloy': 'item',
        'refine_material': 'item', 'perform_chemistry': 'recipe', 'smelt_ore': 'technique',
        'discover_element': 'concept', 'discover_energy': 'concept',
        'build_power_plant': 'method', 'build': 'method',
    }

    def _record_invention(self, agent, action_name: str, outcome: Dict, current_tick: int) -> None:
        """Record experiments, and inventions in InnovationManager (it used to
        be written to by nothing, so no innovation was ever recorded)."""
        from world.innovations import DiscoveryType
        from engine.events import EventCategory, EventImportance
        innovations = self.sim.innovation_manager
        if action_name == 'experiment':
            innovations.record_experiment(agent.id, action_name, [], str(outcome.get('message', '')),
                                          bool(outcome.get('success')))
        kind = self.INVENTIVE_ACTIONS.get(action_name)
        if not kind or not outcome.get('success'):
            return
        product = outcome.get('product') or outcome.get('discovered_material')
        if not product and outcome.get('building_complete') and outcome.get('purpose'):
            product = f"{outcome['purpose']} building"
            if not any(c.intended_purpose == outcome['purpose'] for c in innovations.building_concepts.values()):
                innovations.agent_invents_building(agent.id, agent.name, outcome['purpose'], dict(agent.inventory.items))
        if not product:
            return
        invention = innovations.record_creation(agent.id, agent.name, str(product), DiscoveryType(kind), action_name)
        if invention is not None:
            self.sim.event_logger.log_event(
                EventCategory.CULTURAL, EventImportance.MODERATE,
                f"💡 {agent.name} invented {invention.name}",
                f"{agent.name} was the first to make {invention.name}.", current_tick, [agent.id])

    def _observe_laws(self, agent, action_name: str, current_tick: int) -> None:
        """Record a broken law; witnesses who are citizens think less of the offender."""
        from engine.psychology import EmotionType
        from engine.events import EventCategory, EventImportance
        gm = self.sim.governance_manager
        broken = [law for law in gm.laws_binding(agent.id) if law.prohibition == action_name]
        if not broken:
            return
        government = gm.get_agent_government(agent.id)
        witnesses = [a for a in self.sim.world.agents
                     if a.alive and a.id != agent.id and a.id in government.citizens
                     and a.location.distance_to(agent.location) <= 10.0]
        for law in broken:
            law.times_broken += 1
            if not witnesses:
                continue
            law.times_enforced += 1
            for witness in witnesses:
                self.sim.relationship_manager.update_relationship(witness.id, agent.id, 'broke_law', False)
                witness.reputation_by_agent[agent.id] = max(0.0, witness.reputation_by_agent.get(agent.id, 0.5) - 0.1)
            agent.emotions.trigger_emotion(EmotionType.SHAME, 0.2 + 0.4 * agent.personality.conscientiousness)
            self.sim.event_logger.log_event(
                EventCategory.POLITICAL, EventImportance.MINOR,
                f"{agent.name} broke the law: {law.name}",
                f"{len(witnesses)} citizen(s) saw {agent.name} {action_name.replace('_', ' ')}.",
                current_tick, [agent.id] + [w.id for w in witnesses])

    def _announce_job(self, agent, job_key: str, current_tick: int) -> None:
        """Log an agent settling into (or changing) its job."""
        from engine.events import EventCategory, EventImportance
        title = JOBS[job_key].title
        shifts = sum(1 for j in agent.work_life.recent_shifts if j == job_key)
        logger.info(f"🧰 {agent.name} now works as a {title}")
        self.sim.event_logger.log_event(
            EventCategory.CULTURAL,
            EventImportance.MODERATE,
            f"{agent.name} works as a {title}",
            f"After {shifts} of their last {len(agent.work_life.recent_shifts)} work shifts "
            f"were {title.lower()} work, {agent.name} has made it their job.",
            current_tick,
            [agent.id]
        )

    def _can_run(self, agent, action) -> bool:
        """True if the handler that will actually run this action accepts it now."""
        from engine.simulation import UNHANDLED_ACTION_FALLBACKS
        from life.family import allowed_at_stage
        try:
            resolved = ActionType(UNHANDLED_ACTION_FALLBACKS.get(action.action_type.value, action.action_type.value))
            if not allowed_at_stage(agent, resolved.value):
                return False
            handler = self.sim._handler_registry.get_handler(resolved)
            if handler is None:
                return False
            probe = Action(resolved, target_agent=action.target_agent,
                           target_position=action.target_position, parameters=action.parameters)
            if probe.target_agent is None and resolved.value in ('socialize', 'seek_romance', 'trade', 'teach', 'heal', 'fight', 'tell_story'):
                return True  # partner gets auto-picked at execution
            return handler.validate(agent, probe)[0]
        except Exception:
            return True

    def _survival_override(self, agent):
        """Return an urgent survival action, or None if the agent is fine."""
        from agents.agent import NeedType
        def level(n):
            need = agent.needs.needs.get(n)
            return need.level if need else 0.0
        thirst, hunger, sleep = level(NeedType.THIRST), level(NeedType.HUNGER), level(NeedType.SLEEP)
        worst = max(thirst, hunger, sleep)
        weather = getattr(self.sim, 'weather', None)
        try:
            effects = weather.get_current_effects() if weather else None
        except Exception:
            effects = None
        if (effects is not None and getattr(effects, 'shelter_required', False)
                and agent.active_construction_id is None and worst < 0.85
                and agent.health < 70):
            return Action(ActionType.REST)  # storm and hurt: take cover
        if getattr(agent, 'energy', 100) < 15 and worst < 0.9:
            return Action(ActionType.REST)  # exhausted: recover before anything else
        if worst < 0.7:
            return None
        if agent.life_stage == "baby":
            # A baby can only eat or drink what it's given; otherwise it rests
            # (and is looked after, if anyone chooses to: care_for_child)
            if worst == thirst and agent.inventory.has_item('water', 1):
                return Action(ActionType.DRINK)
            if worst == hunger and agent.inventory.has_item('food', 1):
                return Action(ActionType.EAT)
            return Action(ActionType.REST)
        if worst == thirst:
            # Drink what you carry; fetch water only if you have none. (It always
            # fetched: every bout of thirst was a walk to the lake, several turns
            # of being thirsty, with water in the pack.)
            if agent.inventory.has_item('water', 1):
                return Action(ActionType.DRINK)
            return Action(ActionType.GATHER_WATER)
        if worst == hunger:
            if agent.inventory.has_item('food', 1) if hasattr(agent.inventory, 'has_item') else False:
                return Action(ActionType.EAT)
            return Action(ActionType.GATHER_FOOD)
        return Action(ActionType.REST)

    async def _execute_action_with_purpose(self, agent, action, current_goal: Optional[Any], current_tick: int) -> None:
        """
        Execute an action with full purpose tracking and outcome measurement.

        This implements the PURPOSEFUL ACTION SYSTEM which:
        1. Captures agent state BEFORE action
        2. Evaluates WHY agent is doing this (purpose evaluation)
        3. Executes action
        4. Captures agent state AFTER action
        5. Measures ACTUAL outcome (success/failure)
        6. Agent learns from outcome
        7. Tracks role emergence
        8. Updates goal progress

        Args:
            agent: The agent executing the action
            action: The action to execute
            current_goal: The agent's current strategic goal (may be None)
            current_tick: Current simulation tick
        """
        # 1. Capture agent state BEFORE action (a copy: this used to be the same
        # object as "after", so every measured change was zero)
        needs_before = self._snapshot_needs(agent.needs)
        life_sat_before = needs_before.get_overall_satisfaction()

        # 2. Evaluate WHY agent is doing this (purpose evaluation)
        action_name = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)

        # Get agent's skill levels as dict
        agent_skills = {
            name: skill.level
            for name, skill in agent.skills.skills.items()
        }

        # Generate purpose - the FULL reasoning
        purpose = None
        try:
            purpose = self.sim.purposeful_evaluator.evaluate_purpose(
                action=action_name,
                agent_needs=agent.needs,
                agent_personality=agent.personality,
                agent_skills=agent_skills,
                context={}
            )

            # Store purpose with agent (visible in UI!)
            agent.current_action_purpose = {
                'action': action_name,
                'primary_need': purpose.primary_need.value,
                'primary_urgency': purpose.primary_need_urgency,
                'personality_fit': purpose.personality_fit,
                'skill_level': purpose.skill_level,
                'reasoning': purpose.reasoning_summary,
                'expected_satisfaction': purpose.expected_life_satisfaction_change
            }
        except Exception as e:
            logger.warning(f"Purpose evaluation failed for {agent.name} ({action_name}): {e}")
            agent.current_action_purpose = None

        # 3. Execute action
        outcome = await self.sim.execute_action(agent, action)

        # 4. Capture agent state AFTER action
        needs_after = agent.needs
        life_sat_after = needs_after.get_overall_satisfaction()

        # 5. Measure ACTUAL outcome (success/failure)
        if agent.current_action_purpose and purpose:
            try:
                action_outcome = self.sim.purposeful_evaluator.measure_outcome(
                    purpose=purpose,
                    action_succeeded=outcome.get('success', False),
                    agent_needs_before=needs_before,
                    agent_needs_after=needs_after,
                    context={
                        'action': action_name,
                        'what_happened': outcome.get('message', 'Action completed'),
                        'wealth_change': outcome.get('wealth_change', 0.0),
                        'resources_gained': outcome.get('resources_gained', {}),
                        'resources_lost': outcome.get('resources_lost', {})
                    }
                )

                # Store outcome with agent (for learning & UI)
                outcome_data = {
                    'action': action_name,
                    'tick': current_tick,
                    'succeeded': action_outcome.succeeded,
                    'life_satisfaction_delta': action_outcome.life_satisfaction_delta,
                    'need_changes': {nt.value: change for nt, change in action_outcome.need_changes.items()},
                    'skill_growth': action_outcome.skill_growth,
                    'lesson_learned': action_outcome.lesson_learned,
                    'success_score': self._success_score(action_outcome, bool(outcome.get('success', False)))
                }

                # Add to recent outcomes (keep last 10)
                agent.recent_action_outcomes.append(outcome_data)
                if len(agent.recent_action_outcomes) > 10:
                    agent.recent_action_outcomes = agent.recent_action_outcomes[-10:]

                # Track life satisfaction over time
                agent.life_satisfaction_history.append(life_sat_after)
                if len(agent.life_satisfaction_history) > 50:
                    agent.life_satisfaction_history = agent.life_satisfaction_history[-50:]

                # Track decision quality
                agent.decision_quality_scores.append(outcome_data['success_score'])
                if len(agent.decision_quality_scores) > 10:
                    agent.decision_quality_scores = agent.decision_quality_scores[-10:]

            except Exception as e:
                # Report, don't hide (this used to swallow an AttributeError
                # every tick, so no outcome was ever recorded)
                logger.warning(f"Outcome measurement failed for {agent.name} ({action_name}): {e}")

        # 6. Agent learns from outcome (existing system)
        agent.learn_from_outcome(action, outcome)

        # 6a. ...and remembers it (agents/memory_stream.py)
        self._remember_action(agent, action, outcome, current_tick)

        # 6b. The village's record: counts, and any first (engine/chronicle.py)
        if outcome.get('success', False):
            self._converse(agent, action, current_tick)
            if outcome.get('building_complete'):
                self._move_into(agent, outcome.get('building_id'), current_tick)
            self.sim.action_successes[self._resolved_name(action)] += 1
            if outcome.get('product'):
                self.sim.products[str(outcome['product'])] += 1
            self.sim.chronicle.on_action(self.sim, agent, self._resolved_name(action), outcome, current_tick)

        # 7. TRACK ACTION FOR ROLE EMERGENCE - Pure behavioral observation!
        # Record what agent actually did (not what they're "supposed" to do)
        if outcome.get('success', False):
            action_name = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)
            self.sim.role_emergence.record_action(agent.id, action_name)

        # 7a. Remember how well it worked (shapes the rule-based brain's next
        # choices): the measured score when there is one (did it succeed and
        # leave the agent better off), otherwise plain success
        if hasattr(agent, 'action_memory'):
            measured = agent.recent_action_outcomes[-1] if agent.recent_action_outcomes else None
            if measured is not None and measured.get('action') == action_name and measured.get('tick') == current_tick:
                worked = measured['success_score']
            else:
                worked = 1.0 if outcome.get('success', False) else 0.0
            agent.action_memory.record(self._resolved_name(action), worked)

        # 7b'. What was made: the first maker of anything invents it
        self._record_invention(agent, self._resolved_name(action), outcome, current_tick)

        # 7c. Doing something your government has banned is noticed by citizens
        # nearby and costs you their regard (the law's own consequence)
        if outcome.get('success', False):
            self._observe_laws(agent, self._resolved_name(action), current_tick)

        # 7b. A work shift counts toward the agent's job (the action passed
        # validation before it was chosen, so this was real work)
        shift_job = getattr(agent, 'shift_job', None)
        agent.shift_job = None
        if shift_job:
            new_job = agent.work_life.record_shift(shift_job)
            if new_job:
                self._announce_job(agent, new_job, current_tick)

        # 8. Update goal progress if relevant
        if current_goal:
            progress_amount = 0.1 if outcome.get('success', False) else 0.0
            self.sim.strategy_manager.update_goal_progress(
                agent.id, current_goal.id, progress_amount, outcome
            )
