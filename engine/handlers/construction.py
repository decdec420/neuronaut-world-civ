"""
Construction Action Handler - Handles agent building and construction actions.

This handler manages the BUILD action which includes:
- Multi-tick construction process with state management
- Dynamic building design based on agent needs
- Knowledge creation for completed buildings
- Achievement tracking for builders
- Celebration triggering for building completion

Building is a complex action that can span multiple ticks as agents invest labor
into construction projects.
"""

from typing import TYPE_CHECKING
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


class ConstructionHandler(ActionHandler):
    """
    Handles building and construction actions.

    This handler processes the BUILD action which is unique in that it spans
    multiple ticks. Agents can start, continue, and complete construction projects.

    Action Details:

    BUILD:
    - Need-based building (shelter, defense, storage, workshop, gathering_space)
    - Multi-tick construction with progress tracking
    - Consumes materials from agent inventory
    - Creates knowledge record on completion
    - Triggers building completion celebration
    - Satisfies the need that motivated the building
    - Tracks building achievements
    - Agent stores active_construction_id for multi-tick projects

    Construction Flow:
    1. If agent.active_construction_id exists: Continue working on building
    2. If no active construction: Determine building purpose from needs
    3. Design building based on purpose and available materials
    4. Start construction (consumes materials)
    5. Apply labor each tick until complete
    6. On completion: Create knowledge, satisfy needs, celebrate, track achievement

    Validation Requirements:
    - Agent must be alive
    - Agent must have sufficient energy (minimum 10%)
    - Must have at least 2 materials to start new construction
    - Existing construction must still exist and not be complete

    Examples:
        >>> handler = ConstructionHandler(context)
        >>> action = Action(ActionType.BUILD)
        >>> result = handler.execute(agent, action)
        >>> print(result.message)  # "Started construction" or "Completed building!"
    """

    # Minimum energy required for construction (as fraction 0-1)
    MIN_MATERIALS_TO_START = 40
    MIN_ENERGY_FOR_CONSTRUCTION = 0.1

    def can_handle(self, action_type: ActionType) -> bool:
        """
        Check if this handler can process the given action type.

        Args:
            action_type: The type of action to check

        Returns:
            True if action_type is BUILD, False otherwise
        """
        return action_type == ActionType.BUILD

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        """
        Validate if the agent can perform the construction action.

        Checks:
        1. Agent is alive
        2. Agent has sufficient energy (at least 10%)
        3. If starting new construction: Has at least 2 materials

        Args:
            agent: The agent attempting construction
            action: The BUILD action to validate

        Returns:
            Tuple of (can_execute, reason):
            - (True, "") if validation passes
            - (False, reason_string) if validation fails

        Examples:
            >>> can_execute, reason = handler.validate(agent, build_action)
            >>> if not can_execute:
            ...     print(f"Cannot build: {reason}")
        """
        # Check if agent is alive
        alive_valid = validate_agent_alive(agent)

        # Check if agent has sufficient energy
        energy_valid = validate_agent_energy(agent, self.MIN_ENERGY_FOR_CONSTRUCTION)

        # Combine validations
        basic_validation = combine_validations(alive_valid, energy_valid)
        if not basic_validation[0]:
            return basic_validation

        # If starting new construction (no active project), need materials
        if not agent.active_construction_id:
            available_materials = agent.inventory.items
            building_materials = sum(
                qty for name, qty in available_materials.items()
                if name in ('wood', 'stone', 'plant_fiber', 'clay', 'metal_ore')
            )
            # A basic shelter needs ~55 materials; don't attempt (and fail)
            # every tick before the agent has gathered enough.
            if building_materials < self.MIN_MATERIALS_TO_START:
                return False, f"Need more materials to build ({building_materials}/{self.MIN_MATERIALS_TO_START})"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        """
        Execute the construction action.

        Handles both continuing existing construction and starting new projects.

        Algorithm:
        1. Check if agent has active_construction_id
        2. If yes: Continue working on existing building
           - Apply labor based on skill
           - Check if complete
           - On completion: Create knowledge, satisfy needs, celebrate
        3. If no: Start new construction
           - Determine building purpose from agent needs
           - Design building using dynamic_building_system
           - Start construction (consumes materials)
           - Apply first tick of labor
           - Check if complete (simple buildings complete in one tick)

        Args:
            agent: The agent performing construction
            action: The BUILD action to execute

        Returns:
            ActionResult with:
            - success: True if construction progressed
            - emotional_impact: Varies (0.05 for progress, 0.3 for completion, -0.2 for collapse)
            - message: Description of construction status
            - metadata: Construction details

        Examples:
            >>> action = Action(ActionType.BUILD)
            >>> result = handler.execute(agent, action)
            >>> if result.metadata.get('building_complete'):
            ...     print("Building finished!")
        """
        from world.fun_system import CelebrationType
        from engine.events import EventCategory, EventImportance
        from engine.psychology import EmotionType

        dynamic_building_system = self.context.get_system('dynamic_building_system')
        knowledge_system = self.context.get_system('knowledge_system')
        fun_system = self.context.get_system('fun_system')
        civilization = self.context.get_system('civilization')
        achievement_tracker = self.context.get_system('achievement_tracker')
        story_generator = self.context.get_system('story_generator')
        story_feed = self.context.get_system('story_feed')

        if not dynamic_building_system:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message="Building system not available"
            )

        current_tick = self.context.current_tick

        # Check if agent is already working on a building
        if agent.active_construction_id:
            return self._continue_construction(
                agent, current_tick, dynamic_building_system,
                knowledge_system, fun_system, achievement_tracker,
                story_generator, story_feed
            )
        else:
            return self._start_construction(
                agent, current_tick, dynamic_building_system,
                knowledge_system, fun_system, civilization,
                achievement_tracker, story_generator, story_feed
            )

    def _continue_construction(
        self, agent, current_tick, dynamic_building_system,
        knowledge_system, fun_system, achievement_tracker,
        story_generator, story_feed
    ) -> ActionResult:
        """Continue working on existing construction."""
        building = dynamic_building_system.buildings.get(agent.active_construction_id)

        if not building or building.is_complete:
            # Building no longer exists or is complete
            agent.active_construction_id = None
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message='No active construction',
                metadata={'action_type': 'build'}
            )

        # Apply partial labor based on skill
        skill = agent.skills.get_skill('construction')
        labor_per_tick = max(5.0, skill * 10.0)

        completed = dynamic_building_system.update_construction(
            building.id,
            labor_per_tick
        )

        if completed and not building.collapsed:
            # Building finished!
            result = self._handle_building_completion(
                agent, building, current_tick, dynamic_building_system,
                knowledge_system, fun_system, achievement_tracker,
                story_generator, story_feed
            )
            agent.active_construction_id = None
            return result
        elif building.collapsed:
            # Building collapsed during construction!
            agent.active_construction_id = None
            consequence_engine = self.context.get_system('consequence_engine')
            if consequence_engine:
                design = dynamic_building_system.designs.get(building.design_id)
                consequence_engine.apply_consequence(
                    'building_collapse',
                    {agent.id},
                    'build',
                    0.5,
                    {
                        'building_name': design.name if design else 'structure',
                        'current_tick': current_tick
                    },
                    agent_objects=[agent]
                )

            return ActionResult(
                success=False,
                emotional_impact=-0.2,
                message='Building collapsed!',
                metadata={'action_type': 'build', 'collapsed': True}
            )
        else:
            # Still working...
            return ActionResult(
                success=True,
                emotional_impact=0.05,
                message='Working on construction',
                metadata={
                    'action_type': 'build',
                    'building_id': building.id,
                    'progress': labor_per_tick
                }
            )

    def _start_construction(
        self, agent, current_tick, dynamic_building_system,
        knowledge_system, fun_system, civilization,
        achievement_tracker, story_generator, story_feed
    ) -> ActionResult:
        """Start new construction project."""
        available_materials = agent.inventory.items

        # NEED-BASED BUILDING - Choose purpose based on agent's urgent needs!
        purpose = self._determine_building_purpose(agent)

        # Each agent builds one of each kind (one home, one workshop...).
        # Without this, wandering agents built hut after hut (~10 each).
        built = getattr(agent, 'built_purposes', None)
        if built is None:
            built = agent.built_purposes = set()
        if purpose in built:
            purpose = None

        if not purpose:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message='No building need',
                metadata={'action_type': 'build'}
            )

        skill = agent.skills.get_skill('construction')
        era_value = civilization.current_era.value if civilization else 'stone_age'
        agent_inventory_items = agent.inventory.items if hasattr(agent.inventory, 'items') else {}

        design = dynamic_building_system.agent_designs_building(
            agent.id,
            agent.name,
            [purpose],
            available_materials,
            skill,
            era_value,
            agent_inventory_items
        )

        if not design:
            return ActionResult(
                success=False,
                emotional_impact=0.0,
                message='Could not design building',
                metadata={'action_type': 'build'}
            )

        # Start construction
        building = dynamic_building_system.start_construction(
            design.id,
            (agent.location.x, agent.location.y),
            {agent.id},
            available_materials,
            builder_agent=agent
        )

        if not building:
            return ActionResult(
                success=False,
                emotional_impact=-0.2,
                message='Construction failed to start',
                metadata={'action_type': 'build'}
            )

        # Set as active construction
        agent.active_construction_id = building.id
        agent.built_purposes.add(purpose)

        # Apply first tick of labor
        labor_per_tick = max(5.0, skill * 10.0)
        completed = dynamic_building_system.update_construction(
            building.id,
            labor_per_tick
        )

        if completed and not building.collapsed:
            # Simple building completed in one tick!
            result = self._handle_building_completion(
                agent, building, current_tick, dynamic_building_system,
                knowledge_system, fun_system, achievement_tracker,
                story_generator, story_feed
            )
            agent.active_construction_id = None
            return result
        elif building.collapsed:
            agent.active_construction_id = None
            return ActionResult(
                success=False,
                emotional_impact=-0.3,
                message='Building collapsed during construction!',
                metadata={'action_type': 'build', 'collapsed': True}
            )
        else:
            # Still under construction
            return ActionResult(
                success=True,
                emotional_impact=0.05,
                message='Started construction',
                metadata={
                    'action_type': 'build',
                    'building_id': building.id,
                    'building_name': design.name
                }
            )

    def _handle_building_completion(
        self, agent, building, current_tick, dynamic_building_system,
        knowledge_system, fun_system, achievement_tracker,
        story_generator, story_feed
    ) -> ActionResult:
        """Handle completion of building - knowledge, needs, celebration, achievements."""
        from world.fun_system import CelebrationType
        from engine.events import EventCategory, EventImportance

        logger.info(f"🏛️ {agent.name} COMPLETED BUILDING: {building.name}")
        agent.skills.learn_skill('construction', 0.05)

        # Get purpose from design
        design = dynamic_building_system.designs.get(building.design_id)
        purpose = design.intended_purposes[0] if design and design.intended_purposes else 'general'

        # Create knowledge
        if knowledge_system:
            materials_list = ", ".join([f"{amt} {mat}" for mat, amt in building.materials_used.items()])
            purpose_descriptions = {
                'shelter': 'protection from elements and safe resting place',
                'defense': 'security against threats and territorial control',
                'storage': 'preserving resources and organizing inventory',
                'workshop': 'enabling crafting and creative work',
                'gathering_space': 'fostering community and social bonds'
            }
            purpose_desc = purpose_descriptions.get(purpose, 'general utility')
            skill_level = agent.skills.get_skill('construction')
            estimated_labor = design.estimated_build_time if design else 10
            days_invested = estimated_labor / 24.0

            knowledge_content = {
                "building_name": building.name,
                "purpose": purpose,
                "purpose_description": purpose_desc,
                "materials_used": building.materials_used,
                "materials_list": materials_list,
                "construction_method": design.construction_method if design else "unknown",
                "labor_invested": estimated_labor,
                "days_to_build": round(days_invested, 1),
                "builder_skill": round(skill_level, 2),
                "location": {"x": building.location[0], "y": building.location[1]},
                "lessons": f"{agent.name} constructed {building.name} to provide {purpose_desc}. Using {materials_list}, the structure took {round(days_invested, 1)} days to complete using the {design.construction_method if design else 'basic'} method. This building serves as a vital {purpose} infrastructure for the civilization.",
                "process": f"1. Gathered materials: {materials_list}\n2. Designed structure for {purpose}\n3. Applied {design.construction_method if design else 'basic'} construction technique\n4. Invested {estimated_labor} labor over {round(days_invested, 1)} days\n5. Completed functional {purpose} building",
                "outcome": f"Successfully created {building.name} that fulfills {purpose} needs for the settlement"
            }
            knowledge_system.create_knowledge(
                agent.id,
                "building_method",
                f"How to build {building.name}",
                knowledge_content
            )

        # Satisfy needs
        need_mapping = {
            'shelter': NeedType.SHELTER,
            'defense': NeedType.SECURITY,
            'storage': NeedType.RESOURCES,
            'workshop': [NeedType.CREATIVITY, NeedType.ACHIEVEMENT],
            'gathering_space': NeedType.BELONGING
        }
        needs_to_satisfy = need_mapping.get(purpose, [])
        if not isinstance(needs_to_satisfy, list):
            needs_to_satisfy = [needs_to_satisfy]

        for need_type in needs_to_satisfy:
            if purpose == 'workshop':
                agent.needs.satisfy_need(need_type, 0.3 if need_type == NeedType.CREATIVITY else 0.2)
            else:
                agent.needs.satisfy_need(need_type, 0.3)

        # Log event
        event_logger = self.context.event_logger
        if event_logger:
            title = f"{agent.name} completed {building.name}!"
            desc = f"After {estimated_labor:.0f} labor invested, {agent.name} has completed a {purpose} structure." if design else f"{agent.name} completed a building."
            event_logger.log_event(
                EventCategory.CULTURAL,
                EventImportance.MODERATE,
                title, desc,
                current_tick,
                [agent.id]
            )

        # Celebration
        if fun_system:
            nearby_agents = [
                a.id for a in self.context.world.agents
                if abs(a.location.x - building.location[0]) < 25 and
                   abs(a.location.y - building.location[1]) < 25 and
                   a.id != agent.id
            ]
            celebration = fun_system.trigger_celebration(
                CelebrationType.BUILDING_COMPLETION,
                agent.id,
                agent.name,
                f"Completion of {building.name}",
                building.location,
                nearby_agents
            )

            if event_logger:
                event_logger.log_event(
                    EventCategory.CULTURAL,
                    EventImportance.MODERATE,
                    f"🏛️ Grand Opening Celebration",
                    f"{agent.name} celebrates the completion of {building.name}! {len(celebration.participants)} agents attended the grand opening.",
                    current_tick,
                    list(celebration.participants)
                )

        # Achievement tracking
        if achievement_tracker and story_generator and story_feed:
            current_day = current_tick // 144
            achievement_tracker.track_agent(agent.id, agent.name)

            if agent.id in achievement_tracker.agent_achievements:
                current_count = achievement_tracker.agent_achievements[agent.id].buildings_built
                achievement_tracker.update_agent_stat(agent.id, 'buildings_built', current_count + 1)

                building_achievements = achievement_tracker.check_agent_achievements(agent.id, current_day)
                for ach in building_achievements:
                    logger.info(f"🏆 {agent.name} unlocked: {ach.name}")
                    achievement_story = story_generator.generate_achievement_story(
                        agent.name,
                        ach.achievement_type.value,
                        current_day,
                        {
                            'agent_id': agent.id,
                            'building_count': current_count + 1
                        }
                    )
                    story_feed.add_story(achievement_story)

        return ActionResult(
            success=True,
            emotional_impact=0.3,
            message=f'Completed {building.name}!',
            metadata={
                'action_type': 'build',
                'building_id': building.id,
                'building_name': building.name,
                'purpose': purpose,
                'building_complete': True
            }
        )

    def _determine_building_purpose(self, agent: 'Agent') -> str:
        """Determine what type of building agent needs based on urgent needs."""
        # Check needs and determine purpose
        needs = agent.needs.needs

        # Need levels run 0 (satisfied) -> 1 (desperate). The old code treated
        # LOW levels as urgent, so agents only built when they didn't need to.
        def level(n):
            need = needs.get(n)
            return need.level if need else 0.0

        # Priority order: survival > security > comfort > creativity
        if level(NeedType.SHELTER) > 0.7:
            return 'shelter'
        elif level(NeedType.SECURITY) > 0.7:
            return 'defense'
        elif level(NeedType.RESOURCES) > 0.6:
            return 'storage'
        elif level(NeedType.CREATIVITY) > 0.6:
            return 'workshop'
        elif level(NeedType.BELONGING) > 0.6:
            return 'gathering_space'

        # Default to shelter only if there's no finished building nearby already
        # (otherwise agents kept building hut after hut on the same spot)
        if level(NeedType.SHELTER) > 0.3 and not self._has_shelter_nearby(agent):
            return 'shelter'

        return None

    def _has_shelter_nearby(self, agent, radius: float = 8.0) -> bool:
        dbs = self.context.get_system('dynamic_building_system') if getattr(self, 'context', None) else None
        if dbs is None:
            return False
        for b in dbs.buildings.values():
            if b.is_complete and not b.collapsed:
                bx, by = b.location
                if ((agent.location.x - bx) ** 2 + (agent.location.y - by) ** 2) ** 0.5 < radius:
                    return True
        return False

    def get_required_systems(self) -> list[str]:
        """
        Return list of required system dependencies.

        Construction handler requires:
        - world: For basic world access
        - dynamic_building_system: For building design and construction
        - knowledge_system: For creating building knowledge (optional)
        - fun_system: For celebrations (optional)
        - civilization: For era-based building (optional)
        - achievement_tracker: For tracking building achievements (optional)

        Returns:
            List of required system attribute names
        """
        return ['world', 'dynamic_building_system']
