"""
Knowledge Action Handler - Handles agent knowledge and learning actions.

This handler manages all knowledge-related actions including:
- EXPERIMENT: Discovering new materials through experimentation
- TEACH: Sharing knowledge through oral transmission
- WRITE: Preserving knowledge in written documents

These actions enable agents to learn, discover, and preserve knowledge across
generations, driving technological and cultural progress.
"""

from typing import TYPE_CHECKING
import random
import logging

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    validate_agent_alive,
    validate_agent_energy,
    combine_validations,
)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)


class KnowledgeActionHandler(ActionHandler):
    """
    Handles knowledge and learning actions for agents.

    This handler processes EXPERIMENT, TEACH, and WRITE actions by delegating
    to specialized systems (experimentation_engine, knowledge_system) and
    managing knowledge creation, transfer, and preservation.

    Action Details:

    EXPERIMENT:
    - Delegates to experimentation_engine.attempt_experiment()
    - Agents combine 2-3 materials using various methods (heat, mix, compress, etc.)
    - Era-specific weighting (Stone Age favors heat for fire discovery)
    - Success creates new materials and knowledge records
    - Checks for civilization milestones (fire, bronze, etc.)
    - May trigger meta-discoveries (new capabilities)
    - Failures create cautionary tale knowledge
    - Dangerous failures trigger consequences (explosion, fire, injury)
    - Requires at least 2 materials in inventory

    TEACH:
    - Delegates to knowledge_system.oral_transmission()
    - Teacher shares knowledge with target agent
    - Success rate depends on teacher's teaching skill
    - Both agents learn from the interaction
    - Teacher improves teaching skill (0.03 per success)
    - Requires target_agent and existing knowledge records

    WRITE:
    - Delegates to knowledge_system.agent_writes_document()
    - Preserves 1-3 knowledge records in written form
    - Requires literacy skill > 0.3
    - Creates permanent knowledge documents
    - Writer improves literacy skill (0.05 per document)
    - Requires knowledge records to exist

    Validation Requirements:
    - Agent must be alive for all actions
    - Agent must have sufficient energy (minimum 10%)
    - EXPERIMENT: Requires at least 2 materials in inventory
    - TEACH: Requires target_agent and knowledge records
    - WRITE: Requires literacy skill > 0.3 and knowledge records

    Examples:
        >>> handler = KnowledgeActionHandler(context)
        >>> action = Action(ActionType.EXPERIMENT)
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if experiment succeeded

        >>> action = Action(ActionType.TEACH, target_agent="agent_123")
        >>> result = handler.execute(agent, action)
        >>> print(result.success)  # True if knowledge transferred
    """

    # Minimum energy required for knowledge actions (as fraction 0-1)
    MIN_ENERGY_FOR_KNOWLEDGE = 0.1

    def can_handle(self, action_type: ActionType) -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if action_type is EXPERIMENT, TEACH, or WRITE, False otherwise
        """
        return action_type in [
            ActionType.EXPERIMENT,
            ActionType.TEACH,
            ActionType.WRITE
        ]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if the agent can perform the knowledge action.

        Checks:
        1. Agent is alive (all actions)
        2. Agent has sufficient energy (at least 10%)
        3. EXPERIMENT: At least 2 materials in inventory
        4. TEACH: Target agent specified
        5. WRITE: Literacy skill > 0.3

        Args:
            agent: The agent attempting the action
            action: The knowledge action to validate

        Returns:
            Tuple of (can_execute, reason):
            - (True, "") if validation passes
            - (False, reason_string) if validation fails

        Examples:
            >>> can_execute, reason = handler.validate(agent, experiment_action)
            >>> if not can_execute:
            ...     print(f"Cannot experiment: {reason}")
        """
        # Check if agent is alive
        alive_valid = validate_agent_alive(agent)

        # Check if agent has sufficient energy
        energy_valid = validate_agent_energy(agent, self.MIN_ENERGY_FOR_KNOWLEDGE)

        # Combine basic validations
        basic_validation = combine_validations(alive_valid, energy_valid)
        if not basic_validation[0]:
            return basic_validation

        # Action-specific validation
        if action.action_type == ActionType.EXPERIMENT:
            # Need at least 2 materials to experiment
            available_materials = list(agent.inventory.items.keys())
            if len(available_materials) < 2:
                return False, "Need at least 2 materials to experiment"

        elif action.action_type == ActionType.TEACH:
            # Need target agent
            if not action.target_agent:
                return False, "No target agent specified for teaching"

            # Check if target exists and is alive
            target = self.context.get_agent_by_id(action.target_agent)
            if not target:
                return False, f"Target agent not found: {action.target_agent}"

            target_alive_valid = validate_agent_alive(target)
            if not target_alive_valid[0]:
                return False, f"Target agent is dead: {target.name}"

        elif action.action_type == ActionType.WRITE:
            # Need literacy skill
            literacy_skill = agent.skills.get_skill('literacy')
            if literacy_skill < 0.3:
                return False, f"Literacy skill too low ({literacy_skill:.1%}, need 30%)"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the knowledge action.

        Processes EXPERIMENT, TEACH, or WRITE actions by delegating to appropriate
        systems and managing the full lifecycle of knowledge creation and transfer.

        EXPERIMENT Algorithm:
        1. Select 2-3 materials from inventory (era-weighted for stone age)
        2. Choose experiment method (heat, mix, compress, refine, shape)
        3. Attempt experiment via experimentation_engine
        4. On success:
           - Add discovered material to inventory
           - Create knowledge record with recipe
           - Check for civilization milestone
           - Check for meta-discovery
           - Trigger celebration
           - Improve crafting skill
        5. On failure:
           - Create cautionary tale knowledge
           - Apply consequences if dangerous
           - Learn from failure

        TEACH Algorithm:
        1. Get target agent
        2. Select random knowledge record
        3. Call knowledge_system.oral_transmission()
        4. On success, improve teaching skill

        WRITE Algorithm:
        1. Check literacy skill >= 0.3
        2. Select 1-3 knowledge records
        3. Call knowledge_system.agent_writes_document()
        4. On success, improve literacy skill

        Args:
            agent: The agent performing the action
            action: The knowledge action to execute

        Returns:
            ActionResult with:
            - success: True if action completed successfully
            - emotional_impact: Emotional effect (varies by outcome)
            - message: Description of what occurred
            - metadata: Action-specific details

        Examples:
            >>> action = Action(ActionType.EXPERIMENT)
            >>> result = handler.execute(agent, action)
            >>> if result.success and 'discovered_material' in result.metadata:
            ...     print(f"Discovered: {result.metadata['discovered_material']}")
        """
        current_tick = self.context.current_tick

        if action.action_type == ActionType.EXPERIMENT:
            return self._handle_experiment(agent, current_tick)

        elif action.action_type == ActionType.TEACH:
            return self._handle_teach(agent, action, current_tick)

        elif action.action_type == ActionType.WRITE:
            return self._handle_write(agent, current_tick)

        # Should never reach here due to can_handle check
        return ActionResult(
            success=False,
            emotional_impact=0.0,
            message=f"Unknown knowledge action: {action.action_type.value}",
            metadata={'action_type': action.action_type.value}
        )

    def _handle_experiment(self, agent: 'Agent', current_tick: int) -> ActionResult:
        """Handle EXPERIMENT action - discover new materials through experimentation."""
        from world.civilization_progression import Era
        from world.experimentation import ExperimentMethod
        from engine.events import EventCategory, EventImportance
        from world.fun_system import CelebrationType
        from engine.psychology import EmotionType

        # Get required systems
        experimentation_engine = self.context.get_system('experimentation_engine')
        knowledge_system = self.context.get_system('knowledge_system')
        civilization = self.context.get_system('civilization')
        consequence_engine = self.context.get_system('consequence_engine')
        meta_progression = self.context.get_system('meta_progression')
        fun_system = self.context.get_system('fun_system')

        if not experimentation_engine:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="Experimentation engine not available"
            )

        available_materials = list(agent.inventory.items.keys())

        # Pick 2-3 materials to combine
        num_materials = min(random.randint(2, 3), len(available_materials))

        # In Stone Age, HEAVILY prioritize wood/plant_fiber (needed for fire!)
        if civilization and civilization.current_era == Era.STONE_AGE:
            # Build weighted list favoring wood and plant_fiber
            weighted_materials = []
            for mat in available_materials:
                if mat in ['wood', 'plant_fiber']:
                    # Add 5x for fire-making materials
                    weighted_materials.extend([mat] * 5)
                else:
                    weighted_materials.append(mat)

            # Sample from weighted list
            material_names = []
            attempts = 0
            while len(material_names) < num_materials and attempts < 20:
                mat = random.choice(weighted_materials)
                if mat not in material_names:
                    material_names.append(mat)
                attempts += 1
        else:
            # Normal random selection for other eras
            material_names = random.sample(available_materials, num_materials)

        # Convert to dict with quantities
        materials = {name: 1 for name in material_names}

        # Choose method - WEIGHTED toward era-appropriate discoveries
        if civilization and civilization.current_era == Era.STONE_AGE:
            # AGGRESSIVELY favor heat (fire is the key!)
            methods = [ExperimentMethod.HEAT] * 9 + [ExperimentMethod.MIX]
        elif civilization and civilization.current_era == Era.BRONZE_AGE:
            # Favor refine (for metallurgy)
            methods = [ExperimentMethod.REFINE] * 3 + [ExperimentMethod.HEAT] * 2 + [ExperimentMethod.MIX]
        else:
            # Balanced for later eras
            methods = [
                ExperimentMethod.HEAT, ExperimentMethod.MIX,
                ExperimentMethod.COMPRESS, ExperimentMethod.REFINE,
                ExperimentMethod.SHAPE
            ]

        method = random.choice(methods)

        # Try experiment!
        skill = agent.skills.get_skill('crafting')
        result = experimentation_engine.attempt_experiment(
            agent.id,
            agent.name,
            materials,
            method,
            {'skill': skill, 'location': agent.location}
        )

        if result.success:
            # SUCCESS! Add discovered material to inventory
            if result.discovered_material.name == "coins":
                # Special case: minting coins
                coins_value = 10
                agent.wealth += coins_value
                logger.info(f"💰 {agent.name} minted {coins_value} coins! New wealth: {agent.wealth:.1f}")
            else:
                agent.inventory.add_item(result.discovered_material.name, 1)

            agent.skills.learn_skill('crafting', 0.05)

            # Meta-progression check
            if meta_progression:
                intelligence = (agent.personality.rationality + agent.personality.openness) / 2
                creativity = agent.personality.creativity
                knowledge = sum(skill.level for skill in agent.skills.skills.values()) if agent.skills else 0

                meta_discovery = meta_progression.attempt_discovery(
                    agent.id, agent.name, current_tick // 144,
                    intelligence, creativity, int(knowledge * 100)
                )

                if meta_discovery:
                    logger.info(f"🧬 META-DISCOVERY! {agent.name} unlocked {meta_discovery.capability.value}!")

            # Check for civilization milestone
            milestone = None
            if civilization and knowledge_system:
                milestone = civilization.check_discovery(
                    result.discovered_material.name,
                    agent.id,
                    agent.name
                )

                if milestone:
                    # GAME-CHANGING MOMENT!
                    agent.status = min(1.0, agent.status + 0.3)
                    agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.8)
                    agent.needs.satisfy_need(NeedType.RECOGNITION, 0.9)
                    agent.needs.satisfy_need(NeedType.MEANING, 0.7)
                    agent.emotions.emotions[EmotionType.PRIDE].intensity = 1.0
                    agent.emotions.emotions[EmotionType.JOY].intensity = 0.9
                    logger.info(f"🏆 MILESTONE! {agent.name} discovered {milestone.name}!")

            # Trigger discovery celebration
            if fun_system:
                nearby_agents = [
                    a.id for a in self.context.world.agents
                    if abs(a.location.x - agent.location.x) < 20 and
                       abs(a.location.y - agent.location.y) < 20 and
                       a.id != agent.id
                ]
                fun_system.trigger_celebration(
                    CelebrationType.DISCOVERY_PARTY,
                    agent.id, agent.name,
                    f"Discovery of {result.discovered_material.name}",
                    (agent.location.x, agent.location.y),
                    nearby_agents
                )

            # Create knowledge record with full recipe
            if knowledge_system:
                recipe_content = {
                    "inputs": materials,
                    "method": method,
                    "output": result.discovered_material.name,
                    "properties": [prop.value for prop in result.discovered_properties] if result.discovered_properties else []
                }
                knowledge_system.create_knowledge(
                    agent.id,
                    'recipe',
                    f"How to make {result.discovered_material.name}",
                    recipe_content
                )

            return ActionResult(
                success=True,
                emotional_impact=0.3,
                message=f"Discovered {result.discovered_material.name}!",
                metadata={
                    'action_type': 'experiment',
                    'discovered_material': result.discovered_material.name,
                    'method': method.value,
                    'materials_used': materials,
                    'milestone': milestone.name if milestone else None
                }
            )
        else:
            # FAILURE - Record as cautionary tale
            if knowledge_system:
                failure_content = {
                    "attempted_recipe": {"inputs": materials, "method": method},
                    "failure_reason": result.failure_reason,
                    "lesson_learned": result.lesson_learned,
                    "consequences": {
                        "explosion": result.explosion,
                        "fire": result.fire,
                        "injury": result.injury,
                        "materials_lost": result.materials_consumed
                    },
                    "warning": f"Don't {method} {', '.join(materials.keys())} - {result.failure_reason}"
                }
                knowledge_system.create_knowledge(
                    agent.id,
                    'cautionary_tale',
                    f"Failed: {method} with {', '.join(materials.keys())}",
                    failure_content
                )

            # Apply consequences if dangerous
            if consequence_engine and (result.explosion or result.fire or result.injury):
                severity = 0.7 if result.explosion else 0.4
                consequence_engine.apply_consequence(
                    'explosion' if result.explosion else 'fire' if result.fire else 'injury',
                    {agent.id},
                    'experiment',
                    severity,
                    {
                        'had_explosion': result.explosion,
                        'had_fire': result.fire,
                        'current_tick': current_tick
                    },
                    agent_objects=[agent]
                )

            return ActionResult(
                success=False,
                emotional_impact=-0.2,
                message=result.failure_reason or "Experiment failed",
                metadata={
                    'action_type': 'experiment',
                    'failure_reason': result.failure_reason,
                    'explosion': result.explosion,
                    'fire': result.fire,
                    'injury': result.injury
                }
            )

    def _handle_teach(self, agent: 'Agent', action: 'Action', current_tick: int) -> ActionResult:
        """Handle TEACH action - share knowledge with another agent."""
        knowledge_system = self.context.get_system('knowledge_system')

        if not knowledge_system or len(knowledge_system.knowledge_records) == 0:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="No knowledge to teach"
            )

        target = self.context.get_agent_by_id(action.target_agent)
        if not target:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="Target agent not found"
            )

        # Pick random knowledge to teach
        knowledge_id = random.choice(list(knowledge_system.knowledge_records.keys()))
        teacher_skill = agent.skills.get_skill('teaching')

        result = knowledge_system.oral_transmission(
            agent.id, target.id, knowledge_id, teacher_skill
        )

        if result['success']:
            agent.skills.learn_skill('teaching', 0.03)
            return ActionResult(
                success=True,
                emotional_impact=0.2,
                message=f"Taught knowledge to {target.name}",
                metadata={
                    'action_type': 'teach',
                    'knowledge_id': knowledge_id,
                    'target_agent': target.id
                }
            )

        return ActionResult(
            success=False,
            emotional_impact=0.0,
            message="Teaching failed",
            metadata={'action_type': 'teach'}
        )

    def _handle_write(self, agent: 'Agent', current_tick: int) -> ActionResult:
        """Handle WRITE action - preserve knowledge in written form."""
        knowledge_system = self.context.get_system('knowledge_system')

        if not knowledge_system or len(knowledge_system.knowledge_records) == 0:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="No knowledge to write"
            )

        literacy_skill = agent.skills.get_skill('literacy')
        if literacy_skill < 0.3:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message=f"Literacy skill too low ({literacy_skill:.1%})"
            )

        # Select 1-3 knowledge records to write
        knowledge_ids = random.sample(
            list(knowledge_system.knowledge_records.keys()),
            min(3, len(knowledge_system.knowledge_records))
        )

        doc = knowledge_system.agent_writes_document(
            agent.id,
            f"Document by {agent.name}",
            knowledge_ids,
            'paper',
            literacy_skill
        )

        if doc:
            agent.skills.learn_skill('literacy', 0.05)
            return ActionResult(
                success=True,
                emotional_impact=0.25,
                message=f"Wrote document with {len(knowledge_ids)} knowledge records",
                metadata={
                    'action_type': 'write',
                    'document_id': doc.id if hasattr(doc, 'id') else None,
                    'knowledge_count': len(knowledge_ids)
                }
            )

        return ActionResult(
            success=False,
            emotional_impact=0.0,
            message="Writing failed",
            metadata={'action_type': 'write'}
        )

    def get_required_systems(self) -> list[str]:
        """
        Return list of required system dependencies.

        Knowledge handler requires:
        - world: For basic world access
        - experimentation_engine: For EXPERIMENT action
        - knowledge_system: For TEACH and WRITE actions
        - civilization: For milestone checking (optional)
        - meta_progression: For meta-discoveries (optional)
        - fun_system: For celebrations (optional)
        - consequence_engine: For dangerous failures (optional)

        Returns:
            List of required system attribute names
        """
        return ['world', 'experimentation_engine', 'knowledge_system']
