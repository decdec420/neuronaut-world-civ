"""
Action Handlers Module - Phase 4 Refactoring

Extracted from simulation.py InteractionHandler class.
Contains all action handler methods (handle_trade, handle_socialize, etc.)
that process agent actions and interactions.

This is part of Phase 4 refactoring to modularize simulation.py.
"""

import random
import logging
from typing import Dict

logger = logging.getLogger(__name__)

from agents.agent import Agent, Position
from world.simulation import ResourceType
from social.relationships import RelationshipType
from engine.events import EventGenerator, EventCategory, EventImportance
from engine.psychology import NeedType, EmotionType
from engine.storytelling import StoryGenerator, StoryType


class ActionHandlers:
    """
    Handles all agent action execution.

    This class contains the handler methods for various agent actions:
    - Trade
    - Socialize
    - Romance
    - Gather food
    - Gather materials
    - Rest
    - Chop wood
    - Mine
    - Hunt
    - Gather water

    Each handler method receives the necessary context and returns a result dict
    with success status, emotional impact, and message.
    """

    def __init__(self, sim):
        """
        Initialize ActionHandlers with reference to simulation engine.

        Args:
            sim: The SimulationEngine instance (provides access to all simulation state)
        """
        self.sim = sim

    def handle_trade(
        self,
        agent: Agent,
        target_agent: Agent,
        current_tick: int
    ) -> Dict:
        """Handle trade between agents - with VALUE LEARNING and REPUTATION!"""
        # Check reputation first - agents won't trade with untrusted partners!
        if not agent.is_willing_to_trade_with(target_agent):
            return {
                'success': False,
                'reason': f"{agent.name} doesn't trust {target_agent.name} (poor reputation)",
                'emotional_impact': -0.05
            }

        if not target_agent.is_willing_to_trade_with(agent):
            return {
                'success': False,
                'reason': f"{target_agent.name} doesn't trust {agent.name} (poor reputation)",
                'emotional_impact': -0.05
            }

        # Simple trade: agent wants to buy something target has
        target_items = list(target_agent.inventory.items.keys())

        if not target_items:
            return {'success': False, 'reason': 'No items to trade'}

        # Pick random item
        item = random.choice(target_items)
        quantity = 1
        market_price = self.sim.economy.market.get_market_price(item)

        # ===== VALUE LEARNING: PRICE NEGOTIATION =====
        # Buyer (agent) and seller (target_agent) negotiate based on learned values!

        # Get buyer's estimate and acceptable price
        buyer_estimate = agent.get_estimated_value(item, market_price)
        buyer_max_price = buyer_estimate * 1.3  # Willing to pay 30% over estimate

        # Get seller's estimate and acceptable price
        seller_estimate = target_agent.get_estimated_value(item, market_price)
        seller_min_price = seller_estimate * 0.7  # Willing to sell at 70% of estimate

        # Negotiate: meet in the middle if possible
        if buyer_max_price >= seller_min_price:
            # Trade possible! Use average of buyer max and seller min
            negotiated_price = (buyer_max_price + seller_min_price) / 2
        else:
            # No deal - price expectations don't overlap
            return {
                'success': False,
                'reason': f'Price disagreement: buyer offers {buyer_max_price:.1f}, seller wants {seller_min_price:.1f}',
                'emotional_impact': -0.05
            }

        # Attempt trade at negotiated price
        success, message = self.sim.economy.execute_trade(
            agent, target_agent, item, quantity, negotiated_price
        )

        if success:
            # ===== LEARNING: Both agents learn from this trade! =====
            agent.learn_from_trade(item, negotiated_price, was_buyer=True)
            target_agent.learn_from_trade(item, negotiated_price, was_buyer=False)

            # ===== REPUTATION: Track trade fairness =====
            agent.update_reputation_after_trade(
                target_agent.id, negotiated_price, market_price, was_successful=True
            )
            target_agent.update_reputation_after_trade(
                agent.id, negotiated_price, market_price, was_successful=True
            )

            # Update relationship (positive interaction)
            self.sim.relationship_manager.update_relationship(
                agent.id, target_agent.id, 'trade', positive=True
            )

            # Log event
            title, desc = EventGenerator.trade_completed(
                agent.name, target_agent.name, item, quantity, negotiated_price
            )
            self.sim.event_logger.log_event(
                EventCategory.ECONOMIC,
                EventImportance.MINOR,
                title, desc,
                current_tick,
                [agent.id, target_agent.id]
            )

            # Satisfy needs
            agent.needs.satisfy_need(NeedType.RESOURCES, 0.2)

            return {
                'success': True,
                'emotional_impact': 0.3,
                'message': message
            }
        else:
            # ===== REPUTATION: Failed trade penalties =====
            agent.update_reputation_after_trade(
                target_agent.id, 0, market_price, was_successful=False
            )
            target_agent.update_reputation_after_trade(
                agent.id, 0, market_price, was_successful=False
            )

            return {
                'success': False,
                'emotional_impact': -0.1,
                'message': message
            }

    def handle_socialize(
        self,
        agent: Agent,
        target_agent: Agent,
        current_tick: int
    ) -> Dict:
        """Handle social interaction"""
        # Check compatibility
        compatibility = agent.personality.compatibility_with(target_agent.personality)

        # Positive interaction if compatible
        if compatibility > 0.5:
            # Form or strengthen relationship
            self.sim.relationship_manager.update_relationship(
                agent.id, target_agent.id, 'socialize', positive=True
            )

            # Check if new friendship forms
            existing_rel = self.sim.relationship_manager.get_relationship(
                agent.id, target_agent.id
            )

            if existing_rel and existing_rel.relationship_type == RelationshipType.FRIENDSHIP:
                if existing_rel.strength > 0.6 and len(existing_rel.history) == 1:
                    # New friendship!
                    title, desc = EventGenerator.relationship_formed(
                        agent.name, target_agent.name, 'friendship'
                    )
                    self.sim.event_logger.log_event(
                        EventCategory.SOCIAL,
                        EventImportance.MODERATE,
                        title, desc,
                        current_tick,
                        [agent.id, target_agent.id]
                    )

            # Satisfy social needs
            agent.needs.satisfy_need(NeedType.FRIENDSHIP, 0.3)
            agent.needs.satisfy_need(NeedType.BELONGING, 0.2)

            # Positive emotions
            agent.emotions.trigger_emotion(EmotionType.JOY, 0.2)

            # CULTURAL STORY CREATION - Agents tell stories during socialization!
            if self.sim.story_generator and self.sim.story_feed:
                # Creative agents are more likely to tell stories
                creativity = agent.personality.get_trait('openness')
                story_chance = creativity * 0.15  # Up to 15% chance for very creative agents

                if random.random() < story_chance:
                    current_day = current_tick // 144

                    # Choose story type based on agent state and personality
                    story_type = self._choose_story_type(agent)

                    # Create the story!
                    story = StoryGenerator.agent_creates_story(
                        agent.name,
                        {
                            'creativity': creativity,
                            'openness': agent.personality.get_trait('openness')
                        },
                        story_type,
                        current_day,
                        {'agent_id': agent.id}
                    )

                    self.sim.story_feed.add_story(story)

            return {
                'success': True,
                'emotional_impact': 0.4,
                'message': 'Pleasant conversation'
            }
        else:
            # Negative interaction
            self.sim.relationship_manager.update_relationship(
                agent.id, target_agent.id, 'socialize', positive=False
            )

            agent.emotions.trigger_emotion(EmotionType.SADNESS, 0.1)

            return {
                'success': False,
                'emotional_impact': -0.2,
                'message': 'Awkward interaction'
            }

    def handle_romance(
        self,
        agent: Agent,
        target_agent: Agent,
        current_tick: int
    ) -> Dict:
        """Handle romantic interaction"""
        # Check attraction
        from engine.psychology import PsychologyEngine

        attraction, rel_type = PsychologyEngine.relationship_attraction(
            agent.personality,
            target_agent.personality,
            agent.needs,
            target_agent.needs
        )

        if attraction > 0.6 and rel_type == 'romance':
            # Mutual attraction
            self.sim.relationship_manager.update_relationship(
                agent.id, target_agent.id, 'romance', positive=True
            )

            # Check if romance forms
            existing_rel = self.sim.relationship_manager.get_relationship(
                agent.id, target_agent.id
            )

            if existing_rel and existing_rel.relationship_type == RelationshipType.ROMANCE:
                if existing_rel.strength > 0.7:
                    # Romance blossoms!
                    title, desc = EventGenerator.relationship_formed(
                        agent.name, target_agent.name, 'romance'
                    )
                    self.sim.event_logger.log_event(
                        EventCategory.SOCIAL,
                        EventImportance.MAJOR,
                        title, desc,
                        current_tick,
                        [agent.id, target_agent.id]
                    )

            # Satisfy needs
            agent.needs.satisfy_need(NeedType.SEX, 0.5)
            agent.needs.satisfy_need(NeedType.ROMANCE, 0.6)

            # Positive emotions
            agent.emotions.trigger_emotion(EmotionType.LOVE, 0.4)
            agent.emotions.trigger_emotion(EmotionType.LUST, 0.3)
            agent.emotions.trigger_emotion(EmotionType.JOY, 0.3)

            # ===== PREGNANCY CHANCE =====
            # Check if one is female and not already pregnant
            female_agent = agent if agent.gender.value == 'female' else target_agent if target_agent.gender.value == 'female' else None
            male_agent = agent if agent.gender.value == 'male' else target_agent if target_agent.gender.value == 'male' else None

            if female_agent and male_agent and not female_agent.is_pregnant:
                # Pregnancy chance based on attraction and age
                base_chance = 0.15  # 15% base chance
                age_factor = 1.0 if 18 <= female_agent.age <= 40 else 0.3  # Reduced fertility outside prime years
                pregnancy_chance = base_chance * age_factor * attraction

                if random.random() < pregnancy_chance:
                    # PREGNANCY!
                    female_agent.is_pregnant = True
                    female_agent.pregnancy_partner_id = male_agent.id
                    female_agent.pregnancy_start_tick = current_tick
                    logger.info(f"👶 {female_agent.name} is PREGNANT! Father: {male_agent.name}")

            return {
                'success': True,
                'emotional_impact': 0.8,
                'message': 'Romance flourishes',
                'reproduction_attempted': True  # Signal for reproduction attempt
            }
        else:
            # Rejection
            agent.emotions.trigger_emotion(EmotionType.SADNESS, 0.3)
            agent.emotions.trigger_emotion(EmotionType.SHAME, 0.2)

            return {
                'success': False,
                'emotional_impact': -0.5,
                'message': 'Romantic advance rejected'
            }

    def handle_gather_food(
        self,
        agent: Agent,
        target_position: Position,
        current_tick: int
    ) -> Dict:
        """Handle food gathering with intelligent pathfinding"""
        # Check if agent remembers a food location
        memory = self.sim.resource_memory.recall_resource(
            agent.id,
            'food',
            current_tick,
            max_age=500  # Remember for 500 ticks
        )

        # Find food resource (use memory if available, otherwise search)
        if memory:
            # Try to navigate to remembered location
            target_x, target_y = memory['x'], memory['y']
            distance = agent.location.distance_to(Position(target_x, target_y))

            # If close enough, try to harvest
            if distance < 2.0:
                resource = self.sim.world.find_nearest_resource(
                    agent.location,
                    ResourceType.FOOD
                )
            else:
                # Navigate toward remembered location
                next_step = self.sim.pathfinder.get_next_step(
                    agent.location.x, agent.location.y,
                    target_x, target_y
                )
                if next_step:
                    agent.location = Position(next_step[0], next_step[1])

                return {
                    'success': True,
                    'emotional_impact': 0.05,
                    'message': f'Navigating to food source (distance: {distance:.1f})'
                }
        else:
            # Search for food
            resource = self.sim.world.find_nearest_resource(
                agent.location,
                ResourceType.FOOD
            )

        if not resource or resource.quantity <= 0:
            return {
                'success': False,
                'emotional_impact': -0.1,
                'message': 'No food found'
            }

        # Check distance to resource
        distance = agent.location.distance_to(resource.location)

        # If too far, navigate closer
        if distance > 3.0:
            next_step = self.sim.pathfinder.get_next_step(
                agent.location.x, agent.location.y,
                resource.location.x, resource.location.y
            )

            if next_step:
                agent.location = Position(next_step[0], next_step[1])
                # Remember this resource location
                self.sim.resource_memory.remember_resource(
                    agent.id,
                    'food',
                    resource.location.x,
                    resource.location.y,
                    resource.quantity,
                    current_tick
                )

                return {
                    'success': True,
                    'emotional_impact': 0.05,
                    'message': f'Moving toward food (distance: {distance:.1f})'
                }

        # Close enough to harvest!
        # Harvest food - INCREASED YIELD for survival!
        amount = self.sim.world.harvest_resource(resource.id, 12.0)  # Was 5.0, now 12.0

        if amount > 0:
            # Add to inventory
            agent.inventory.add_item('food', int(amount))

            # Immediately eat to survive - satisfy hunger MORE
            agent.needs.satisfy_need(NeedType.HUNGER, amount / 8.0)  # Was /10, now /8 - more satisfying
            # Restore energy from eating
            agent.energy = min(100.0, agent.energy + 8.0)  # Was +5, now +8

            # Remember this successful location
            self.sim.resource_memory.remember_resource(
                agent.id,
                'food',
                resource.location.x,
                resource.location.y,
                resource.quantity,
                current_tick
            )

            return {
                'success': True,
                'emotional_impact': 0.2,
                'message': f'Gathered {amount:.1f} food'
            }
        else:
            # Resource depleted, forget this location
            self.sim.resource_memory.forget_resource(
                agent.id,
                resource.location.x,
                resource.location.y
            )

            return {
                'success': False,
                'emotional_impact': -0.1,
                'message': 'Failed to gather food'
            }

    def handle_gather_materials(
        self,
        agent: Agent,
        current_tick: int
    ) -> Dict:
        """
        Handle gathering building materials (stone, wood, clay, metal_ore, etc.)

        This is CRITICAL for civilization building!
        Agents need materials to:
        - Build structures
        - Experiment with new materials
        - Trade with others
        """
        # Determine what material to gather based on availability and need
        # Priority: stone > wood > clay > metal_ore (if unlocked)
        material_priority = ['stone', 'wood', 'clay', 'plant_fiber', 'metal_ore', 'iron_ore']

        gathered_material = None
        gathered_amount = 0

        for material_name in material_priority:
            # TOOL REQUIREMENT CHECKS
            # Advanced materials require proper tools!
            if material_name in ['metal_ore', 'iron_ore']:
                # Mining requires at least stone tools
                if not agent.inventory.has_item('stone'):
                    continue  # Skip this material, need tools!

            # Check if material is available in world resource pools
            available = self.sim.world.resource_pools.get(material_name, 0)

            if available > 10:  # Only gather if there's enough
                # Base gathering amount - INCREASED for faster progress!
                base_amount = random.uniform(8.0, 15.0)  # Was 3.0-8.0, now 8.0-15.0

                # TOOL EFFICIENCY BONUSES
                efficiency_multiplier = 1.0
                if material_name == 'wood' and agent.inventory.has_item('stone'):
                    efficiency_multiplier = 1.5  # Stone axe helps
                elif material_name == 'stone' and agent.inventory.has_item('wood'):
                    efficiency_multiplier = 1.3  # Wooden handle helps
                elif material_name in ['metal_ore', 'iron_ore'] and agent.inventory.has_item('stone'):
                    efficiency_multiplier = 1.4  # Stone pickaxe

                amount_to_gather = base_amount * efficiency_multiplier
                # Only take what the agent can carry; the rest stays in the world
                space = agent.inventory.capacity - agent.inventory.get_total_items()
                if space <= 0:
                    break
                amount_to_gather = min(amount_to_gather, float(space))
                actual_amount = self.sim.world.harvest_from_pool(material_name, amount_to_gather)

                if actual_amount > 0:
                    # Add to inventory
                    agent.inventory.add_item(material_name, int(actual_amount))
                    gathered_material = material_name
                    gathered_amount = int(actual_amount)

                    # Learn gathering skill
                    agent.skills.learn_skill('gathering', 0.05)

                    # CREATE KNOWLEDGE from gathering (every 10th time to avoid spam)
                    if self.sim.knowledge_system and random.random() < 0.1:
                        # Determine tool used
                        tool_used = None
                        if material_name == 'wood' and agent.inventory.has_item('stone'):
                            tool_used = "stone axe"
                        elif material_name == 'stone' and agent.inventory.has_item('wood'):
                            tool_used = "wooden lever/handle"
                        elif material_name in ['metal_ore', 'iron_ore'] and agent.inventory.has_item('stone'):
                            tool_used = "stone pickaxe"

                        gathering_skill = agent.skills.get_skill('gathering')

                        knowledge_content = {
                            "material": material_name,
                            "amount_gathered": gathered_amount,
                            "tool_used": tool_used if tool_used else "bare hands",
                            "efficiency_bonus": round(efficiency_multiplier, 2),
                            "gatherer_skill": round(gathering_skill, 2),
                            "location_type": "wilderness",
                            "technique": "manual gathering" if not tool_used else f"tool-assisted gathering ({tool_used})",
                            "purpose": "acquiring raw materials for construction and survival",
                            "lessons": f"{agent.name} discovered {material_name} in the wilderness and gathered {gathered_amount} units using {tool_used if tool_used else 'bare hands'}. {'Using tools increased efficiency by ' + str(int((efficiency_multiplier - 1) * 100)) + '%.' if tool_used else 'Tools would improve gathering speed.'} This resource is essential for civilization development.",
                            "process": f"1. Located {material_name} deposit in wilderness\n2. Used {tool_used if tool_used else 'manual labor'} to extract material\n3. Gathered {gathered_amount} units\n4. Stored in personal inventory\n5. Resource can be used for building or crafting",
                            "outcome": f"Successfully acquired {gathered_amount} {material_name} for community use"
                        }
                        self.sim.knowledge_system.create_knowledge(
                            agent.id,
                            "technique",
                            f"Gathering {material_name}",
                            knowledge_content
                        )

                    # Satisfy resource need slightly
                    agent.needs.satisfy_need(NeedType.RESOURCES, 0.1)

                    break

        if gathered_material:
            return {
                'success': True,
                'emotional_impact': 0.15,
                'message': f'Gathered {gathered_amount} {gathered_material}'
            }
        else:
            return {
                'success': False,
                'emotional_impact': -0.05,
                'message': 'No materials available to gather'
            }

    def handle_rest(self, agent: Agent) -> Dict:
        """Handle rest/sleep"""
        # Restore energy
        agent.energy = min(100.0, agent.energy + 20.0)

        # Satisfy sleep need
        agent.needs.satisfy_need(NeedType.SLEEP, 0.5)

        # Reduce stress
        agent.emotions.stress = max(0.0, agent.emotions.stress - 0.2)

        # CULTURAL STORY CREATION - Agents reflect and create stories while resting!
        if self.sim.story_generator and self.sim.story_feed:
            # Thoughtful, open-minded agents create stories while reflecting
            openness = agent.personality.get_trait('openness')
            story_chance = openness * 0.08  # Lower chance during rest (up to 8%)

            if random.random() < story_chance:
                # Rest encourages reflective stories: teachings, warnings, prophecies
                story_types = [StoryType.TEACHING, StoryType.WARNING]

                # Very creative agents might imagine myths or songs
                if openness > 0.7:
                    story_types.extend([StoryType.MYTH, StoryType.SONG])

                story_type = random.choice(story_types)

                story = StoryGenerator.agent_creates_story(
                    agent.name,
                    {
                        'creativity': openness,
                        'openness': openness
                    },
                    story_type,
                    0,  # Will be set by simulation
                    {'agent_id': agent.id}
                )

                self.sim.story_feed.add_story(story)

        return {
            'success': True,
            'emotional_impact': 0.1,
            'message': 'Rested and recovered'
        }

    def _choose_story_type(self, agent: Agent) -> StoryType:
        """Choose which type of cultural story an agent tells based on their state"""
        # Happy agents tell songs and legends
        joy_level = getattr(agent.emotions.emotions.get(EmotionType.JOY), 'intensity', 0.0)

        # Fearful agents tell warnings
        fear_level = getattr(agent.emotions.emotions.get(EmotionType.FEAR), 'intensity', 0.0)

        # Check agent achievements and experiences
        has_achievements = hasattr(agent, 'achievements') and len(agent.achievements) > 0

        # Build weighted story type list
        story_options = []

        # Myths - explaining the unknown (base chance)
        story_options.extend([StoryType.MYTH] * 2)

        # Legends - heroic tales (higher if agent has achievements)
        legend_weight = 3 if has_achievements else 1
        story_options.extend([StoryType.LEGEND] * legend_weight)

        # Teachings - wisdom (higher if agent is older/experienced)
        teaching_weight = 3 if agent.age > 30 else 1
        story_options.extend([StoryType.TEACHING] * teaching_weight)

        # Warnings - cautionary tales (higher if fearful or stressed)
        warning_weight = 4 if fear_level > 0.5 or agent.emotions.stress > 0.6 else 1
        story_options.extend([StoryType.WARNING] * warning_weight)

        # Songs - joyful tales (higher if happy)
        song_weight = 4 if joy_level > 0.6 else 1
        story_options.extend([StoryType.SONG] * song_weight)

        return random.choice(story_options)

    def handle_chop_wood(self, agent: Agent) -> Dict:
        """Handle chopping wood from trees - specialized wood gathering"""
        # Check if wood is available in resource pools
        available = self.sim.world.resource_pools.get('wood', 0)

        if available < 5:
            return {
                'success': False,
                'emotional_impact': -0.05,
                'message': 'No trees available to chop'
            }

        # Base gathering amount
        base_amount = random.uniform(4.0, 10.0)

        # Tool efficiency - stone tools help chop wood faster
        efficiency_multiplier = 1.0
        if agent.inventory.has_item('stone'):
            efficiency_multiplier = 1.8  # Stone axe is very effective!

        # Skill bonus - gathering/crafting skill improves efficiency
        gathering_skill = agent.skills.get_skill('gathering')
        skill_bonus = 1.0 + (gathering_skill * 0.5)

        amount_to_gather = base_amount * efficiency_multiplier * skill_bonus
        actual_amount = self.sim.world.harvest_from_pool('wood', amount_to_gather)

        if actual_amount > 0:
            # Add to inventory
            agent.inventory.add_item('wood', int(actual_amount))

            # Learn gathering skill
            agent.skills.learn_skill('gathering', 0.08)

            # Satisfy resource need
            agent.needs.satisfy_need(NeedType.RESOURCES, 0.15)

            # Restore a bit of energy from productive work
            agent.energy = min(100.0, agent.energy + 2.0)

            return {
                'success': True,
                'emotional_impact': 0.2,
                'message': f'Chopped {int(actual_amount)} wood from trees'
            }
        else:
            return {
                'success': False,
                'emotional_impact': -0.05,
                'message': 'Failed to chop wood'
            }

    def handle_mine(self, agent: Agent) -> Dict:
        """Handle mining stone and minerals - specialized mining"""
        # Priority: stone > metal_ore > iron_ore > clay
        materials_to_mine = ['stone', 'metal_ore', 'iron_ore', 'clay']

        for material_name in materials_to_mine:
            # Tool requirement for advanced materials
            if material_name in ['metal_ore', 'iron_ore']:
                # Mining ores requires stone tools
                if not agent.inventory.has_item('stone'):
                    continue

            # Check availability
            available = self.sim.world.resource_pools.get(material_name, 0)

            if available > 5:
                # Base mining amount
                base_amount = random.uniform(3.0, 8.0)

                # Tool efficiency
                efficiency_multiplier = 1.0
                if agent.inventory.has_item('wood'):
                    efficiency_multiplier = 1.3  # Wooden handle helps
                if agent.inventory.has_item('stone') and material_name in ['metal_ore', 'iron_ore']:
                    efficiency_multiplier = 1.6  # Stone pickaxe for ore mining

                # Skill bonus
                gathering_skill = agent.skills.get_skill('gathering')
                skill_bonus = 1.0 + (gathering_skill * 0.5)

                amount_to_gather = base_amount * efficiency_multiplier * skill_bonus
                # Only take what the agent can carry; the rest stays in the world
                space = agent.inventory.capacity - agent.inventory.get_total_items()
                if space <= 0:
                    break
                amount_to_gather = min(amount_to_gather, float(space))
                actual_amount = self.sim.world.harvest_from_pool(material_name, amount_to_gather)

                if actual_amount > 0:
                    # Add to inventory
                    agent.inventory.add_item(material_name, int(actual_amount))

                    # Learn gathering skill
                    agent.skills.learn_skill('gathering', 0.08)

                    # Satisfy resource need
                    agent.needs.satisfy_need(NeedType.RESOURCES, 0.15)

                    # Restore a bit of energy
                    agent.energy = min(100.0, agent.energy + 2.0)

                    return {
                        'success': True,
                        'emotional_impact': 0.2,
                        'message': f'Mined {int(actual_amount)} {material_name}'
                    }

        return {
            'success': False,
            'emotional_impact': -0.05,
            'message': 'No minerals available to mine'
        }

    def handle_hunt(self, agent: Agent) -> Dict:
        """Handle hunting animals for food - specialized hunting"""
        # Hunting is more effective than foraging but requires skill/luck
        hunting_skill = agent.skills.get_skill('hunting')

        # Base success chance
        success_chance = 0.4 + (hunting_skill * 0.5)  # 40-90% depending on skill

        # Tool bonus - having weapons helps
        tool_bonus = 0.0
        if agent.inventory.has_item('stone'):
            tool_bonus = 0.15  # Stone spear/knife
        if agent.inventory.has_item('wood'):
            tool_bonus += 0.1  # Wooden spear

        success_chance = min(0.95, success_chance + tool_bonus)

        if random.random() < success_chance:
            # Successful hunt!
            amount = random.randint(8, 15)  # Hunting gives more food than gathering

            # Add to inventory
            agent.inventory.add_item('food', amount)

            # Learn hunting skill
            agent.skills.learn_skill('hunting', 0.1)

            # Satisfy hunger immediately (eating fresh meat)
            agent.needs.satisfy_need(NeedType.HUNGER, 0.4)

            # Restore energy from eating
            agent.energy = min(100.0, agent.energy + 8.0)

            # Gain achievement satisfaction
            agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.1)

            return {
                'success': True,
                'emotional_impact': 0.3,
                'message': f'Successfully hunted and gained {amount} food!'
            }
        else:
            # Failed hunt
            agent.skills.learn_skill('hunting', 0.02)  # Learn from failure

            return {
                'success': False,
                'emotional_impact': -0.1,
                'message': 'Hunt unsuccessful - prey escaped'
            }

    def handle_gather_water(self, agent: Agent, current_tick: int) -> Dict:
        """Handle gathering water with intelligent pathfinding"""
        # Check if agent remembers a water location
        memory = self.sim.resource_memory.recall_resource(
            agent.id,
            'water',
            current_tick,
            max_age=500
        )

        # Find water resource (use memory if available, otherwise search)
        if memory:
            # Try to navigate to remembered location
            target_x, target_y = memory['x'], memory['y']
            distance = agent.location.distance_to(Position(target_x, target_y))

            # If close enough, try to harvest
            if distance < 2.0:
                resource = self.sim.world.find_nearest_resource(
                    agent.location,
                    ResourceType.WATER
                )
            else:
                # Navigate toward remembered location
                next_step = self.sim.pathfinder.get_next_step(
                    agent.location.x, agent.location.y,
                    target_x, target_y
                )
                if next_step:
                    agent.location = Position(next_step[0], next_step[1])

                return {
                    'success': True,
                    'emotional_impact': 0.05,
                    'message': f'Navigating to water source (distance: {distance:.1f})'
                }
        else:
            # Search for water
            resource = self.sim.world.find_nearest_resource(
                agent.location,
                ResourceType.WATER
            )

        if not resource or resource.quantity <= 0:
            # No nearby water source - try resource pools
            available = self.sim.world.resource_pools.get('water', 0)

            if available > 5:
                # Gather from pool - INCREASED for survival!
                amount = random.randint(10, 18)  # Was 3-8, now 10-18
                actual_amount = self.sim.world.harvest_from_pool('water', amount)

                if actual_amount > 0:
                    agent.inventory.add_item('water', int(actual_amount))

                    # Immediately drink to satisfy thirst MORE
                    agent.needs.satisfy_need(NeedType.THIRST, 0.6)  # Was 0.4, now 0.6

                    # Restore energy
                    agent.energy = min(100.0, agent.energy + 8.0)  # Was +5, now +8

                    return {
                        'success': True,
                        'emotional_impact': 0.2,
                        'message': f'Gathered {int(actual_amount)} water'
                    }

            return {
                'success': False,
                'emotional_impact': -0.1,
                'message': 'No water source found'
            }

        # Check distance to resource
        distance = agent.location.distance_to(resource.location)

        # If too far, navigate closer
        if distance > 3.0:
            next_step = self.sim.pathfinder.get_next_step(
                agent.location.x, agent.location.y,
                resource.location.x, resource.location.y
            )

            if next_step:
                agent.location = Position(next_step[0], next_step[1])
                # Remember this resource location
                self.sim.resource_memory.remember_resource(
                    agent.id,
                    'water',
                    resource.location.x,
                    resource.location.y,
                    resource.quantity,
                    current_tick
                )

                return {
                    'success': True,
                    'emotional_impact': 0.05,
                    'message': f'Moving toward water (distance: {distance:.1f})'
                }

        # Close enough to harvest!
        # Harvest water from resource - INCREASED for survival!
        amount = self.sim.world.harvest_resource(resource.id, 12.0)  # Was 5.0, now 12.0

        if amount > 0:
            # Add to inventory
            agent.inventory.add_item('water', int(amount))

            # Immediately drink to satisfy thirst MORE
            agent.needs.satisfy_need(NeedType.THIRST, 0.6)  # Was 0.4, now 0.6

            # Restore energy
            agent.energy = min(100.0, agent.energy + 8.0)  # Was +5, now +8

            # Remember this successful location
            self.sim.resource_memory.remember_resource(
                agent.id,
                'water',
                resource.location.x,
                resource.location.y,
                resource.quantity,
                current_tick
            )

            return {
                'success': True,
                'emotional_impact': 0.2,
                'message': f'Gathered {amount:.1f} water'
            }
        else:
            # Resource depleted, forget this location
            self.sim.resource_memory.forget_resource(
                agent.id,
                resource.location.x,
                resource.location.y
            )

            return {
                'success': False,
                'emotional_impact': -0.1,
                'message': 'Failed to gather water'
            }
