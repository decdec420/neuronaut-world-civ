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
from agents.daily_life import JOBS, WORK, job_for
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

        # Update all agents with error isolation
        for agent in self.sim.world.agents:
            if not agent.alive:
                continue

            await self._update_single_agent(agent, current_tick, world_state)

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

            # Environmental diseases based on conditions
            if hasattr(agent, 'needs') and agent.needs.needs.get(NeedType.HUNGER) and agent.needs.needs[NeedType.HUNGER].level < 0.3:
                # Malnutrition from starvation
                self.sim.health.infect_agent(agent.id, DiseaseType.MALNUTRITION, Severity.MODERATE, current_tick)
            elif hasattr(agent, 'needs') and agent.needs.needs.get(NeedType.THIRST) and agent.needs.needs[NeedType.THIRST].level < 0.3:
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
        """
        Check if agent is ready to give birth and handle birth event.

        This includes:
        - Checking pregnancy status
        - Creating baby with genetic inheritance
        - Logging birth event
        - Generating birth story
        - Tracking achievements

        Args:
            agent: The agent to check for birth
            current_tick: Current simulation tick
        """
        from engine.events import EventCategory, EventImportance
        from engine.achievements import AchievementType

        if not agent.is_pregnant:
            return

        baby = agent.check_pregnancy(current_tick)
        if not baby:
            return

        # Get father for genetic inheritance
        father = next((a for a in self.sim.world.agents if a.id == agent.pregnancy_partner_id), None)
        if father:
            # Re-create baby with father's traits included
            baby = agent.give_birth(current_tick)
            baby._create_inherited_personality(father.personality)
            father.children_ids.append(baby.id)

        # Add baby to world
        self.sim.world.agents.append(baby)

        # Log birth event
        father_name = father.name if father else "unknown"
        self.sim.event_logger.log_event(
            EventCategory.LIFE,
            EventImportance.MAJOR,
            f"👶 Birth: {baby.name} was born!",
            f"{agent.name} gave birth to {baby.name}! Father: {father_name}",
            current_tick,
            [agent.id, father.id] if father else [agent.id]
        )

        # ===== STORY GENERATION - Make this birth LEGENDARY! =====
        current_day = current_tick // 144  # Convert ticks to days
        population = sum(1 for a in self.sim.world.agents if a.alive)
        family_context = {
            'mother_id': agent.id,
            'father_id': father.id if father else None,
            'population': population,
            'generation': 2  # TODO: Track generation properly
        }
        birth_story = self.sim.story_generator.generate_birth_story(
            baby.name, agent.name, father_name, current_day, family_context
        )
        self.sim.story_feed.add_story(birth_story)
        logger.info(f"📜 STORY: {birth_story.title}")

        # ===== ACHIEVEMENT TRACKING =====
        # Track all family members for achievements
        self.sim.achievement_tracker.track_agent(baby.id, baby.name)
        self.sim.achievement_tracker.track_agent(agent.id, agent.name)
        if father:
            self.sim.achievement_tracker.track_agent(father.id, father.name)
            # Update father's children count
            self.sim.achievement_tracker.update_agent_stat(father.id, 'children_count', len(father.children_ids))

        # Update mother's children count
        self.sim.achievement_tracker.update_agent_stat(agent.id, 'children_count', len(agent.children_ids))

        # Check for PARENT achievement
        mother_achievements = self.sim.achievement_tracker.check_agent_achievements(agent.id, current_day)
        if father:
            father_achievements = self.sim.achievement_tracker.check_agent_achievements(father.id, current_day)
            for ach in father_achievements:
                logger.info(f"🏆 {father.name} unlocked: {ach.name}")
        for ach in mother_achievements:
            logger.info(f"🏆 {agent.name} unlocked: {ach.name}")

        # Civilization achievement - FIRST BIRTH
        first_birth_ach = self.sim.achievement_tracker.unlock_civilization_achievement(
            AchievementType.FIRST_BIRTH, current_day
        )
        if first_birth_ach:
            logger.info(f"🎆 CIVILIZATION ACHIEVEMENT: {first_birth_ach.name}")

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
        # Use autonomous AI decisions if enabled, otherwise fall back to rule-based
        llm_action = None
        if self.sim.config.use_llm_decisions and hasattr(agent, 'autonomous_decide') \
                and self._survival_override(agent) is None:
            # Make AI-powered decision (handles planning and reflection internally)
            try:
                llm_action = agent.autonomous_decide(perceptions, current_tick, self.sim.config)
            except Exception as e:
                logger.error(f"AI decision failed for {agent.name}: {e}")
            # No model reachable / unusable answer: use the rule-based brain below
            if llm_action is not None and llm_action.action_type in (ActionType.IDLE, ActionType.WAIT):
                llm_action = None
            if llm_action is not None and not self._can_run(agent, llm_action):
                llm_action = None

        if llm_action is not None:
            action = llm_action
            current_goal = self.sim.strategy_manager.get_current_goal(agent.id)
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
                if current_goal:
                    from engine.simulation import UNHANDLED_ACTION_FALLBACKS
                    step = self.sim.strategy_manager.evaluate_goal_action(agent, current_goal)
                    goal_action = UNHANDLED_ACTION_FALLBACKS.get(step, step) if step else None
                action = self.utility_brain.choose(
                    agent, perceptions, lambda a: self._can_run(agent, a), part_of_day, goal_action)
            # Work done in work hours counts toward the agent's job
            agent.shift_job = job_for(self._resolved_name(action), agent.work_life.job) if part_of_day == WORK else None
        agent.current_action = action
        return action, current_goal

    @staticmethod
    def _resolved_name(action) -> str:
        """The action that will actually run (aliases resolve to their action)."""
        from engine.simulation import UNHANDLED_ACTION_FALLBACKS
        name = action.action_type.value
        return UNHANDLED_ACTION_FALLBACKS.get(name, name)

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
        try:
            resolved = ActionType(UNHANDLED_ACTION_FALLBACKS.get(action.action_type.value, action.action_type.value))
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
        if worst == thirst:
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
        # 1. Capture agent state BEFORE action
        needs_before = agent.needs
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
            # Fallback if evaluation fails
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
                        'what_happened': outcome.get('reason', 'Action completed'),
                        'wealth_change': outcome.get('wealth_change', 0.0),
                        'resources_gained': outcome.get('resources_gained', {}),
                        'resources_lost': outcome.get('resources_lost', {})
                    }
                )

                # Store outcome with agent (for learning & UI)
                outcome_data = {
                    'action': action_name,
                    'succeeded': action_outcome.succeeded,
                    'life_satisfaction_delta': action_outcome.life_satisfaction_delta,
                    'need_changes': {nt.value: change for nt, change in action_outcome.need_changes.items()},
                    'skill_growth': action_outcome.skill_growth,
                    'lesson_learned': action_outcome.lesson_learned,
                    'success_score': self.sim._calculate_success_score(action_outcome)
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
                # Fallback if outcome measurement fails
                pass

        # 6. Agent learns from outcome (existing system)
        agent.learn_from_outcome(action, outcome)

        # 7. TRACK ACTION FOR ROLE EMERGENCE - Pure behavioral observation!
        # Record what agent actually did (not what they're "supposed" to do)
        if outcome.get('success', False):
            action_name = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)
            self.sim.role_emergence.record_action(agent.id, action_name)

        # 7a. Remember whether it worked (shapes the rule-based brain's next choices)
        if hasattr(agent, 'action_memory'):
            agent.action_memory.record(self._resolved_name(action), bool(outcome.get('success', False)))

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
