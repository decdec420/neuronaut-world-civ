"""
Perception Builder - Constructs comprehensive perceptions for agent decision-making

Extracted from simulation.py to reduce file size and improve modularity.
This module handles building all perception data that agents need for decision-making.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class PerceptionBuilder:
    """
    Builds comprehensive perceptions for agent decision-making.

    Handles:
    - Combat/warfare information
    - Governance/political information
    - Resource scarcity information
    - Life/romance/family information
    - Economic/trade information
    - Religious information
    - Strategic information
    """

    def __init__(self, simulation):
        """
        Initialize perception builder with reference to simulation engine.

        Args:
            simulation: The main SimulationEngine instance
        """
        self.sim = simulation
        logger.debug("PerceptionBuilder initialized")

    def build_perceptions(self, agent, world_state: Dict) -> Dict[str, Any]:
        """
        Build full perceptions for an agent.

        This is the main entry point that orchestrates building all perception types.

        Args:
            agent: The agent to build perceptions for
            world_state: Current state of the world

        Returns:
            Dict containing all perception data
        """
        # Start with basic perception from agent
        perceptions = agent.perceive(world_state)
        perceptions['tick'] = world_state.get('tick', self.sim.world.time.current_tick)

        # === REFACTORED SECTIONS (implemented in PerceptionBuilder) ===
        perceptions = self._add_combat_info(agent, perceptions)
        perceptions = self._add_governance_info(agent, perceptions)
        perceptions = self._add_scarcity_info(agent, perceptions)

        # === STUB METHODS (TODOs - still in simulation.py) ===
        perceptions = self._add_tech_info(agent, perceptions)
        perceptions = self._add_weather_info(agent, perceptions)
        perceptions = self._add_buildings_info(agent, perceptions)
        perceptions = self._add_knowledge_info(agent, perceptions)
        perceptions = self._add_disaster_info(agent, perceptions)
        perceptions = self._add_experimentation_info(agent, perceptions)
        perceptions = self._add_role_info(agent, perceptions)
        perceptions = self._add_innovation_info(agent, perceptions)
        perceptions = self._add_entertainment_info(agent, perceptions)
        perceptions = self._add_consequences_info(agent, perceptions)
        perceptions = self._add_agriculture_info(agent, perceptions)
        perceptions = self._add_health_info(agent, perceptions)
        perceptions = self._add_territory_info(agent, perceptions)
        perceptions = self._add_chemistry_info(agent, perceptions)
        perceptions = self._add_energy_info(agent, perceptions)
        perceptions = self._add_materials_info(agent, perceptions)
        perceptions = self._add_life_info(agent, perceptions)
        perceptions = self._add_economic_info(agent, perceptions)
        perceptions = self._add_religious_info(agent, perceptions)
        perceptions = self._add_strategic_info(agent, perceptions)
        perceptions = self._add_social_info(agent, perceptions)
        perceptions = self._add_works_info(agent, perceptions)

        return perceptions

    def _add_works_info(self, agent, perceptions: Dict) -> Dict:
        """Roads, wells and street lights (world/infrastructure.py), as the agent
        would see them: what's near, what the village has, how much it walks."""
        from world import infrastructure as infra
        works = self.sim.infrastructure
        x, y, tick = agent.location.x, agent.location.y, self.sim.world.time.current_tick
        lamp = works.light_near(x, y, infra.LIGHT_RADIUS)
        perceptions['news'] = [n.text for n in self.sim.news.heard_by(agent.id, tick, 3)]
        perceptions['works'] = {
            'road_tiles': len(works.roads),
            'on_road': (int(x), int(y)) in works.roads,
            'wells': len(works.wells),
            'well_nearby': works.well_near(x, y, infra.WELL_SPACING) is not None,
            'street_lights': len(works.lights),
            'lit_lamp_nearby': bool(lamp and lamp.lit),
            'lamp_needs_fuel': bool(lamp and lamp.fuel == 0),
            'walking_lately': round(works.walking_burden(agent.id, tick), 2),
        }
        from life import homes
        dbs = self.sim.dynamic_building_system
        home = homes.home_of(dbs, agent)
        perceptions['works']['home'] = home.name if home else None
        perceptions['works']['home_distance'] = round(homes.distance_home(dbs, agent), 1) if home else None
        return perceptions

    def _add_social_info(self, agent, perceptions: Dict) -> Dict:
        """The people an agent knows, and what its village has built socially.

        Adds 'relationships' (name, type, strength; strongest first),
        'people_by_name' (lower-case first name -> id, so the AI brain can
        name anyone in the village as a target) and 'community' (governments,
        laws and religions as short descriptions).
        """
        sim = self.sim
        by_id = {a.id: a for a in sim.world.agents if a.alive}
        perceptions['people_by_name'] = {a.name.lower(): a.id for a in by_id.values() if a.id != agent.id}

        known = []
        for rel in sim.relationship_manager.get_agent_relationships(agent.id):
            other = by_id.get(rel.agent_b if rel.agent_a == agent.id else rel.agent_a)
            if other is not None:
                known.append({'name': other.name, 'type': rel.relationship_type.value, 'strength': rel.strength})
        perceptions['relationships'] = sorted(known, key=lambda r: -r['strength'])

        def name_of(agent_id):
            other = by_id.get(agent_id)
            return other.name if other else 'someone gone'

        governance = sim.governance_manager
        governments = [f"{g.name} ({g.government_type.value}, led by {name_of(g.leader_id)}, "
                       f"{len(g.citizens)} citizens{', you are one' if agent.id in g.citizens else ''})"
                       for g in governance.governments.values()]
        laws = [f"{law.name}: {law.description} ({'in force' if law.active else 'repealed'})"
                for law in governance.laws.values()]
        def mine(r):
            """For its own faith: when it last practised, and that faiths fade."""
            if agent.id not in r.followers:
                return ''
            last = getattr(sim.religion, 'last_practice', {}).get(agent.id)
            hours = (sim.world.time.current_tick - last) // 6 if last is not None else None
            when = f"you last prayed, worshipped or held a ritual {hours} hours ago" if hours is not None else ''
            days = sim.religion.LAPSE_TICKS // 144
            return f", you are one; {when}{'; ' if when else ''}a faith unpractised for {days} days lapses"
        religions = [f"{r.name} (founded by {r.founder_name or name_of(r.founder_id)}, "
                     f"{len(r.followers)} followers{mine(r)})"
                     for r in sim.religion.religions.values()]
        perceptions['community'] = {'governments': governments, 'laws': laws, 'religions': religions}
        return perceptions

    def _add_combat_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add combat and warfare information to perceptions.

        Includes:
        - Nearby agents with valuable resources
        - Weak targets
        - Grudges and conflicts
        - Agent's resource desperation
        """
        # Find nearby agents with resources worth fighting for
        nearby_agents_with_resources = []

        for other_agent in self.sim.world.agents:
            if other_agent.id != agent.id and other_agent.alive:
                distance = agent.location.distance_to(other_agent.location)

                if distance < 30:  # Within combat range
                    # Check if they have resources worth fighting for
                    has_food = other_agent.inventory.has_item('food')
                    has_water = other_agent.inventory.has_item('water')
                    has_valuable_resources = other_agent.wealth > 50 or has_food or has_water

                    # Check if they're weak (low health)
                    is_weak = other_agent.health < 50

                    # Check for grudges
                    grudge_level = self.sim.warfare_manager.get_grudge(agent.id, other_agent.id)

                    if has_valuable_resources or is_weak or grudge_level > 0.3:
                        nearby_agents_with_resources.append({
                            'id': other_agent.id,
                            'name': other_agent.name,
                            'distance': distance,
                            'health': other_agent.health,
                            'has_food': has_food,
                            'has_water': has_water,
                            'wealth': other_agent.wealth,
                            'is_weak': is_weak,
                            'grudge_level': grudge_level
                        })

        # Add to perceptions
        perceptions['potential_combat_targets'] = nearby_agents_with_resources

        # Add agent's own resource desperation
        from engine.psychology import NeedType
        perceptions['resource_desperation'] = {
            'hunger': agent.needs.needs[NeedType.HUNGER].level if hasattr(agent.needs.needs.get(NeedType.HUNGER), 'level') else 0.0,
            'thirst': agent.needs.needs[NeedType.THIRST].level if hasattr(agent.needs.needs.get(NeedType.THIRST), 'level') else 0.0,
            'has_food': agent.inventory.has_item('food'),
            'has_water': agent.inventory.has_item('water')
        }

        return perceptions

    def _add_governance_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add governance and political information to perceptions.

        Includes:
        - Citizenship status
        - Leadership roles
        - Active laws
        - Pending votes
        - Political power
        """
        governance_info = {}

        # Check if agent is in a government
        agent_government = None
        for gov_id, gov in self.sim.governance_manager.governments.items():
            if agent.id in gov.citizens and gov.active:
                agent_government = gov
                break

        if agent_government:
            governance_info['is_citizen'] = True
            governance_info['government_name'] = agent_government.name
            governance_info['government_type'] = agent_government.government_type.value
            governance_info['is_leader'] = (agent.id == agent_government.leader_id)
            governance_info['approval_rating'] = agent_government.approval_rating

            # Check if agent can make laws
            governance_info['can_make_laws'] = self.sim.governance_manager._can_make_law(agent.id, agent_government)

            # Get active laws
            governance_info['active_laws'] = [
                self.sim.governance_manager.laws[law_id].name
                for law_id in agent_government.laws
                if law_id in self.sim.governance_manager.laws and self.sim.governance_manager.laws[law_id].active
            ]

            # Check for pending votes
            pending_votes = []
            for law_id, law in self.sim.governance_manager.laws.items():
                if law_id in agent_government.laws and law.active:
                    if agent.id not in law.supporters and agent.id not in law.opposers:
                        pending_votes.append(law_id)
            governance_info['pending_votes'] = pending_votes

        else:
            # Not in government - check if could form one
            governance_info['is_citizen'] = False
            governance_info['is_leader'] = False

            # Count nearby agents (potential followers)
            nearby_count = sum(1 for other in self.sim.world.agents
                             if other.id != agent.id and other.alive
                             and agent.location.distance_to(other.location) < 50)
            governance_info['nearby_agents_count'] = nearby_count

        # Add political power
        governance_info['political_power'] = self.sim.governance_manager.political_power.get(agent.id, 0.0)

        # The prompt reads 'governance_info' (it used to be written as 'governance'
        # and never reached the AI brain)
        perceptions['governance_info'] = governance_info
        return perceptions

    def _add_scarcity_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add resource scarcity information to perceptions.

        Includes:
        - Scarce vs abundant resources
        - Critical scarcity (resources agent needs that are scarce)
        - Resource availability
        """
        from engine.psychology import NeedType

        scarcity_info = {}

        # Get global resource pool status
        resource_status = self.sim.world.get_resource_pool_status()
        pools = resource_status['pools']

        # Calculate scarcity levels for key resources
        scarcity_thresholds = {
            'critical': 0.2,  # < 20% remaining
            'low': 0.4,       # < 40% remaining
            'moderate': 0.7,  # < 70% remaining
        }

        # Initial resource amounts (from world/simulation.py)
        initial_amounts = {
            'stone': 3000.0,
            'wood': 2500.0,
            'food': 2000.0,
            'water': 3500.0,
            'clay': 1200.0,
            'sand': 1000.0,
            'hide': 600.0,
            'plant_fiber': 1500.0,
        }

        scarce_resources = []
        abundant_resources = []

        for resource_name, current_amount in pools.items():
            if resource_name in initial_amounts:
                initial = initial_amounts[resource_name]
                ratio = current_amount / initial if initial > 0 else 0.0

                if ratio < scarcity_thresholds['critical']:
                    scarce_resources.append({
                        'name': resource_name,
                        'amount': current_amount,
                        'ratio': ratio,
                        'level': 'CRITICAL'
                    })
                elif ratio < scarcity_thresholds['low']:
                    scarce_resources.append({
                        'name': resource_name,
                        'amount': current_amount,
                        'ratio': ratio,
                        'level': 'LOW'
                    })
                elif ratio > 0.9:  # > 90% = abundant
                    abundant_resources.append({
                        'name': resource_name,
                        'amount': current_amount,
                        'ratio': ratio
                    })

        scarcity_info['scarce_resources'] = scarce_resources
        scarcity_info['abundant_resources'] = abundant_resources
        scarcity_info['total_resources'] = resource_status['total_resources']

        # Check what resources agent needs
        agent_needs_resources = []
        if hasattr(agent, 'needs') and agent.needs.needs.get(NeedType.HUNGER) and agent.needs.needs[NeedType.HUNGER].level > 0.5:
            agent_needs_resources.append('food')
        if hasattr(agent, 'needs') and agent.needs.needs.get(NeedType.THIRST) and agent.needs.needs[NeedType.THIRST].level > 0.5:
            agent_needs_resources.append('water')

        # Check if needed resources are scarce (creates urgency!)
        critical_scarcity = []
        for needed in agent_needs_resources:
            for scarce in scarce_resources:
                if scarce['name'] == needed:
                    critical_scarcity.append(scarce)

        scarcity_info['critical_scarcity'] = critical_scarcity
        scarcity_info['needs_resources'] = agent_needs_resources

        perceptions['scarcity_info'] = scarcity_info
        return perceptions

    def _add_life_info(self, agent, perceptions: Dict) -> Dict:
        """Partner, courtships and family, as names the agent would know.

        'partner': the partner's name or None; 'admirers': people who courted
        this agent recently and are free (it can court them back); 'courting':
        people it courted who haven't answered yet; plus age, life stage and
        pregnancy. (This used to list opposite-sex strangers as "potential
        partners" and read a spouse field nothing ever set.)
        """
        from life import family
        now = self.sim.world.time.current_tick
        partner = family.partner_of(agent, self.sim._get_agent_by_id)
        life_info = {
            'age': agent.age,
            'life_stage': agent.life_stage,
            'partner': partner.name if partner else None,
            'is_pregnant': agent.is_pregnant,
            'admirers': [],
            'courting': [],
        }
        for other in self.sim.world.agents:
            if not other.alive or other.id == agent.id:
                continue
            if family.recently(agent.admirers, other.id, now) and family.free_to_court(agent, other)[0]:
                life_info['admirers'].append(other.name)
            if family.recently(other.admirers, agent.id, now):
                life_info['courting'].append(other.name)
        if agent.is_pregnant:
            life_info['due_in_ticks'] = max(0, agent.pregnancy_duration_ticks - (now - agent.pregnancy_start_tick))
        if partner is not None and partner.child_wish_tick is not None and \
                now - partner.child_wish_tick <= family.INTEREST_MEMORY_TICKS:
            life_info['partner_wants_child'] = True
        children = [self.sim._get_agent_by_id(cid) for cid in agent.children_ids]
        life_info['children'] = [{'name': c.name, 'age': c.age, 'stage': c.life_stage,
                                  'needs_care': family.is_young(c) and family.neediness(c) > 0.5}
                                 for c in children if c is not None and c.alive]
        if family.is_young(agent):
            parents = [self.sim._get_agent_by_id(pid) for pid in (agent.mother_id, agent.father_id) if pid]
            life_info['parents'] = [p.name for p in parents if p is not None and p.alive]
            life_info['can_do'] = sorted(family.BABY_ACTIONS if agent.life_stage == "baby" else family.CHILD_ACTIONS)
        perceptions['life_info'] = life_info
        return perceptions

    def _add_economic_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add economic and trade information to perceptions.

        Includes:
        - Wealth levels
        - Trade opportunities
        - Market prices
        - Taxation information
        """
        # Complete financial system: wealth, banking, taxation, trade, crises, etc.
        economic_info = self.sim.economy.get_agent_economic_info(
            agent.id,
            agent.wealth,
            agent_income=0.0  # TODO: Track agent income
        )

        # Add accessible economic opportunities
        from economy.minting import CoinType
        from economy.trade_routes import RouteStatus

        # Minting opportunities - can agent mint coins?
        has_metal_ore = (agent.inventory.has_item('copper_ore') or
                       agent.inventory.has_item('silver_ore') or
                       agent.inventory.has_item('gold_ore'))
        economic_info['can_mint_coins'] = has_metal_ore
        economic_info['discovered_coins'] = [c.value for c in self.sim.economy.minting.discovered_coins]

        # Banking opportunities
        economic_info['total_banks'] = len(self.sim.economy.banking.banks)
        nearest_bank = None
        min_distance = float('inf')
        for bank in self.sim.economy.banking.banks.values():
            dist = ((agent.location.x - bank.location[0])**2 +
                   (agent.location.y - bank.location[1])**2)**0.5
            if dist < min_distance:
                min_distance = dist
                nearest_bank = bank

        if nearest_bank:
            economic_info['nearest_bank_distance'] = round(min_distance, 1)
            economic_info['can_access_bank'] = min_distance < 30.0
        else:
            economic_info['nearest_bank_distance'] = None
            economic_info['can_access_bank'] = False

        # Trade route opportunities
        active_routes = [r for r in self.sim.economy.trade_routes.trade_routes.values()
                       if r.status == RouteStatus.ACTIVE]
        economic_info['active_trade_routes'] = len(active_routes)

        # Agent's caravans
        agent_caravans = [c for c in self.sim.economy.trade_routes.caravans.values()
                        if c.merchant_id == agent.id]
        economic_info['my_caravans'] = len(agent_caravans)

        # Tax revolts - can join?
        active_revolts = [r for r in self.sim.economy.taxation.revolts.values()
                        if not r.succeeded and agent.id not in r.participants]
        economic_info['active_tax_revolts'] = len(active_revolts)
        economic_info['can_join_revolt'] = len(active_revolts) > 0

        # Investment opportunities (bubbles)
        active_bubbles = [b for b in self.sim.economy.crises.asset_bubbles.values()
                        if not b.burst]
        economic_info['investment_opportunities'] = len(active_bubbles)

        perceptions['economic_info'] = economic_info
        return perceptions

    def _add_religious_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add religious and spiritual information to perceptions.

        Includes:
        - Religious affiliations
        - Faith levels
        - Religious opportunities
        - Temples and rituals
        """
        religion_info = {}

        # Agent's religion
        agent_religion = self.sim.religion.get_agent_religion(agent.id)
        if agent_religion:
            religion_info['my_religion'] = agent_religion.name
            religion_info['my_religion_type'] = agent_religion.religion_type.value
            religion_info['is_priest'] = agent.id in agent_religion.priests
            religion_info['fellow_believers'] = len(agent_religion.followers)
        else:
            religion_info['my_religion'] = None
            religion_info['is_priest'] = False

        # Total religions
        religion_info['total_religions'] = len(self.sim.religion.religions)

        # Can found religion?
        has_no_religion = agent_religion is None
        religion_info['can_found_religion'] = has_no_religion

        # Nearby temples
        nearby_temples = self.sim.religion.get_nearby_temples(
            (agent.location.x, agent.location.y),
            radius=50.0
        )
        religion_info['nearby_temples'] = len(nearby_temples)

        # Active rituals
        religion_info['active_rituals'] = len(self.sim.religion.active_rituals)

        perceptions['religion_info'] = religion_info
        return perceptions

    def _add_strategic_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add strategic planning information to perceptions.

        Includes:
        - Long-term goals
        - Strategic priorities
        - Alliances
        - Territory control
        """
        # TODO: Extract from simulation.py strategic planning sections
        return perceptions

    def _add_tech_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add technology progression information to perceptions.

        Includes:
        - Current era (Stone Age → Silicon Age)
        - Achieved milestones
        - Available technologies
        - Next milestones to pursue
        """
        tech_info = {}

        # Get current civilization era
        current_era = self.sim.civilization.current_era
        tech_info['current_era'] = current_era.value

        # Get achieved milestones
        achieved_milestones = [
            {'name': m.name, 'achieved_by': m.achieved_by_name, 'impact': m.impact}
            for m in self.sim.civilization.milestones.values()
            if m.is_achieved
        ]
        tech_info['achieved_milestones'] = achieved_milestones

        # Get next milestone to pursue
        unachieved_milestones = [
            {'id': m_id, 'name': m.name, 'description': m.description,
             'unlocks_era': m.unlocks_era.value if m.unlocks_era else None,
             'production_multiplier': m.production_multiplier}
            for m_id, m in self.sim.civilization.milestones.items()
            if not m.is_achieved
        ]
        tech_info['next_milestones'] = unachieved_milestones[:3]  # Show top 3

        # Check if agent knows about specific technologies
        agent_knowledge = []
        for discovery in self.sim.civilization.discoveries_made:
            agent_knowledge.append(discovery)
        tech_info['known_discoveries'] = agent_knowledge

        # Get available resources for current era
        from world.civilization_progression import RESOURCE_TIERS
        current_tier = RESOURCE_TIERS.get(current_era)
        if current_tier:
            tech_info['available_resources'] = current_tier.base_resources
            tech_info['discoverable'] = current_tier.discoverable_resources
            tech_info['prerequisite'] = current_tier.required_prerequisite

        perceptions['tech_info'] = tech_info
        return perceptions

    def _add_weather_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add weather and environmental information to perceptions.

        Includes:
        - Current weather conditions
        - Weather effects (gathering efficiency, energy drain, etc.)
        - Shelter status and needs
        """
        weather_info = {}
        current_weather = self.sim.weather.current_weather
        current_effects = self.sim.weather.get_current_effects()

        weather_info['current_weather'] = current_weather.value
        weather_info['emoji'] = current_effects.emoji
        weather_info['description'] = current_effects.description

        # Effects that agents should know about
        weather_info['effects'] = {
            'water_regeneration': current_effects.water_regeneration,
            'food_regeneration': current_effects.food_regeneration,
            'energy_drain': current_effects.energy_drain,
            'movement_speed': current_effects.movement_speed,
            'gathering_efficiency': current_effects.gathering_efficiency,
            'danger_level': current_effects.danger_level,
            'shelter_required': current_effects.shelter_required,
            'visibility_range': current_effects.visibility_range
        }

        # Check if agent is in shelter (has building nearby)
        has_shelter = False
        for building in self.sim.dynamic_building_system.buildings.values():
            if building.is_complete and not building.collapsed:
                dist = ((agent.location.x - building.location[0])**2 +
                        (agent.location.y - building.location[1])**2)**0.5
                if dist < 5:  # Within 5 units = sheltered
                    has_shelter = True
                    break

        weather_info['has_shelter'] = has_shelter
        weather_info['needs_shelter'] = current_effects.shelter_required and not has_shelter

        perceptions['weather_info'] = weather_info
        return perceptions

    def _add_buildings_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add buildings and construction information to perceptions.

        Includes:
        - Nearby buildings
        - Building benefits (shelter, storage, defense)
        - Buildable structures based on resources
        """
        buildings_info = {}

        # Find nearby buildings
        nearby_buildings = []
        for building in self.sim.dynamic_building_system.buildings.values():
            dist = ((agent.location.x - building.location[0])**2 +
                    (agent.location.y - building.location[1])**2)**0.5

            if dist < 50:  # Within 50 units
                building_data = {
                    'id': building.id,
                    'name': building.name,
                    'distance': round(dist, 1),
                    'is_complete': building.is_complete,
                    'construction_progress': round(building.construction_progress * 100, 1) if not building.is_complete else 100,
                    'collapsed': building.collapsed
                }

                # Add benefits if building is complete and not collapsed
                if building.is_complete and not building.collapsed:
                    benefits = {}
                    if building.shelter_value and building.shelter_value > 0:
                        benefits['shelter'] = building.shelter_value
                    if building.storage_capacity and building.storage_capacity > 0:
                        benefits['storage'] = building.storage_capacity
                    if building.production_bonus and building.production_bonus > 0:
                        benefits['production_bonus'] = building.production_bonus
                    if building.comfort_value and building.comfort_value > 0:
                        benefits['comfort'] = building.comfort_value
                    if building.defense_value and building.defense_value > 0:
                        benefits['defense'] = building.defense_value

                    if benefits:
                        building_data['benefits'] = benefits

                    # Add occupancy info
                    building_data['occupants_count'] = len(building.occupants)
                    building_data['workers_count'] = len(building.workers)

                nearby_buildings.append(building_data)

        # Sort by distance
        nearby_buildings.sort(key=lambda b: b['distance'])
        buildings_info['nearby_buildings'] = nearby_buildings[:10]  # Top 10 closest

        # Check if agent can build (has resources)
        agent_resources = {}
        if hasattr(agent.inventory, 'items'):
            for item in agent.inventory.items:
                resource_name = item.name if hasattr(item, 'name') else str(item)
                if resource_name in agent_resources:
                    agent_resources[resource_name] += 1
                else:
                    agent_resources[resource_name] = 1

        buildings_info['can_build'] = len(agent_resources) > 0
        buildings_info['available_materials'] = agent_resources

        # Suggest buildable structures based on materials and era
        buildable = []
        if 'wood' in agent_resources or 'stone' in agent_resources:
            # Basic shelter
            if agent_resources.get('wood', 0) >= 10 or agent_resources.get('stone', 0) >= 5:
                buildable.append({
                    'purpose': 'shelter',
                    'name': 'Basic Shelter',
                    'materials': {'wood': 10} if 'wood' in agent_resources else {'stone': 5},
                    'benefit': 'Protection from weather'
                })

        if 'wood' in agent_resources and agent_resources.get('wood', 0) >= 20:
            buildable.append({
                'purpose': 'crafting',
                'name': 'Workshop',
                'materials': {'wood': 20, 'stone': 10},
                'benefit': 'Crafting bonus +20%'
            })

        buildings_info['buildable_structures'] = buildable

        perceptions['buildings_info'] = buildings_info
        return perceptions

    def _knowledge_by_agent(self) -> Dict:
        """agent id -> knowledge records it knows, rebuilt once per tick."""
        tick = self.sim.world.time.current_tick
        records = self.sim.knowledge_system.knowledge_records
        cached = getattr(self, '_knowledge_index', None)
        if cached is None or cached[0] != tick or cached[1] != len(records):
            index = {}
            for record in records.values():
                for agent_id in record.known_by:
                    index.setdefault(agent_id, []).append(record)
            self._knowledge_index = cached = (tick, len(records), index)
        return cached[2]

    def _add_knowledge_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add knowledge system information to perceptions.

        Includes:
        - What agent knows
        - Teaching opportunities (what I can teach others)
        - Learning opportunities (what others can teach me)
        """
        knowledge_info = {}
        # Who knows what, built once per tick (this rescanned every record for
        # every agent, and again for every pair of nearby agents, every tick)
        known = self._knowledge_by_agent()
        mine = known.get(agent.id, [])

        knowledge_info['known_knowledge'] = [{
            'id': k.id,
            'name': k.name,
            'type': k.knowledge_type,
            'accuracy': k.accuracy,
            'mastery': 'expert' if k.original_author == agent.id else 'learned'
        } for k in mine]
        knowledge_info['knowledge_count'] = len(mine)

        # Teaching and learning opportunities with agents nearby
        teaching_opportunities = []
        learning_opportunities = []

        for other_agent in self.sim.world.agents:
            if other_agent.id != agent.id and other_agent.alive:
                dist = agent.location.distance_to(other_agent.location)
                if dist < 30:  # Within teaching range
                    can_teach = [k.name for k in mine if other_agent.id not in k.known_by][:3]
                    if can_teach:
                        teaching_opportunities.append({
                            'agent_id': other_agent.id,
                            'agent_name': other_agent.name,
                            'distance': round(dist, 1),
                            'can_teach': can_teach  # Top 3 things they could learn
                        })
                    can_learn = [k.name for k in known.get(other_agent.id, []) if agent.id not in k.known_by][:3]
                    if can_learn:
                        learning_opportunities.append({
                            'agent_id': other_agent.id,
                            'agent_name': other_agent.name,
                            'distance': round(dist, 1),
                            'can_learn': can_learn  # Top 3 things I could learn
                        })

        knowledge_info['teaching_opportunities'] = teaching_opportunities[:5]
        knowledge_info['learning_opportunities'] = learning_opportunities[:5]

        # Find nearby libraries
        nearby_libraries = []
        for lib_id, library in self.sim.knowledge_system.libraries.items():
            # Libraries have locations
            if hasattr(library, 'location'):
                dist = ((agent.location.x - library.location[0])**2 +
                        (agent.location.y - library.location[1])**2)**0.5
                if dist < 50:
                    nearby_libraries.append({
                        'name': library.name if hasattr(library, 'name') else 'Library',
                        'distance': round(dist, 1),
                        'document_count': len(library.documents)
                    })

        knowledge_info['nearby_libraries'] = nearby_libraries

        # Total civilization knowledge
        knowledge_info['total_civilization_knowledge'] = len(self.sim.knowledge_system.knowledge_records)

        perceptions['knowledge_info'] = knowledge_info
        return perceptions

    def _add_disaster_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add disaster and emergency information to perceptions.

        Includes:
        - Active disasters
        - Disaster warnings
        - Safe zones
        """
        disaster_info = {}

        # Check for active disasters nearby
        active_disasters_nearby = []
        for disaster in self.sim.disasters.active_disasters:
            # Calculate distance from agent to disaster epicenter
            dist = ((agent.location.x - disaster.location_x)**2 +
                    (agent.location.y - disaster.location_y)**2)**0.5

            # Check if agent is in or near affected area
            in_range = dist < (disaster.radius * 1.5)  # Alert zone is 1.5x radius

            if in_range or dist < 100:  # Also show if within 100 units
                disaster_data = {
                    'type': disaster.disaster_type.value,
                    'severity': disaster.severity.value,
                    'distance_from_epicenter': round(dist, 1),
                    'radius': disaster.radius,
                    'in_danger_zone': dist < disaster.radius,
                    'damage_potential': getattr(self.sim.disasters.get_disaster_effects(disaster), 'agent_damage', 0)
                }

                # Add warning level
                if dist < disaster.radius:
                    disaster_data['warning'] = 'CRITICAL - You are in the disaster zone!'
                elif dist < disaster.radius * 1.5:
                    disaster_data['warning'] = 'HIGH - Disaster nearby, evacuate!'
                else:
                    disaster_data['warning'] = 'MODERATE - Disaster in the distance'

                active_disasters_nearby.append(disaster_data)

        disaster_info['active_disasters'] = active_disasters_nearby
        disaster_info['disaster_count'] = len(active_disasters_nearby)
        disaster_info['in_immediate_danger'] = any(d['in_danger_zone'] for d in active_disasters_nearby)

        # Disasters that were warned of: what is coming, when, and whether
        # this agent is where it will hit. What to do about it is up to them.
        coming = []
        now = self.sim.world.time.current_tick
        for warning in getattr(self.sim.disasters, 'pending_warnings', []):
            disaster = warning['disaster']
            dist = ((agent.location.x - disaster.location_x) ** 2 +
                    (agent.location.y - disaster.location_y) ** 2) ** 0.5
            coming.append({
                'type': disaster.disaster_type.value,
                'severity': disaster.severity.value,
                'ticks_until_impact': max(0, warning['impact_tick'] - now),
                'distance_from_epicenter': round(dist, 1),
                'radius': disaster.radius,
                'will_reach_you': dist < disaster.radius,
            })
        disaster_info['warnings'] = coming

        perceptions['disaster_info'] = disaster_info
        return perceptions

    def _add_experimentation_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add experimentation and science information to perceptions.

        Includes:
        - Ongoing experiments
        - Lab access
        - Experiment opportunities
        """
        experimentation_info = {}

        # Available materials for experimentation (from inventory)
        available_for_experiments = []
        if hasattr(agent.inventory, 'items'):
            material_counts = {}
            for item in agent.inventory.items:
                mat_name = item.name if hasattr(item, 'name') else str(item)
                material_counts[mat_name] = material_counts.get(mat_name, 0) + 1

            for mat_name, count in material_counts.items():
                available_for_experiments.append({
                    'material': mat_name,
                    'quantity': count
                })

        experimentation_info['available_materials'] = available_for_experiments

        # Suggest interesting experiment combinations
        experiment_suggestions = []

        # Get agent's current era to suggest era-appropriate experiments
        current_era = self.sim.civilization.current_era.value if hasattr(self.sim.civilization, 'current_era') else 'Stone Age'

        # Stone Age suggestions
        if current_era == 'Stone Age':
            if any(m['material'] == 'wood' for m in available_for_experiments):
                experiment_suggestions.append({
                    'materials': ['wood', 'friction'],
                    'method': 'rub/heat',
                    'expected_result': 'fire',
                    'benefit': 'Unlocks Bronze Age!'
                })
            if any(m['material'] == 'stone' for m in available_for_experiments):
                experiment_suggestions.append({
                    'materials': ['stone', 'stone'],
                    'method': 'strike/sharpen',
                    'expected_result': 'sharp stone tool',
                    'benefit': 'Better gathering efficiency'
                })

        # Bronze Age suggestions
        elif 'Bronze' in current_era:
            if any(m['material'] == 'metal_ore' for m in available_for_experiments):
                experiment_suggestions.append({
                    'materials': ['metal_ore', 'fire'],
                    'method': 'heat/refine',
                    'expected_result': 'bronze',
                    'benefit': 'Unlocks Iron Age!'
                })

        # Add general suggestions based on materials
        material_names = [m['material'] for m in available_for_experiments]
        if 'clay' in material_names and 'water' in material_names:
            experiment_suggestions.append({
                'materials': ['clay', 'water'],
                'method': 'mix/shape',
                'expected_result': 'pottery',
                'benefit': 'Storage and cooking'
            })

        experimentation_info['experiment_suggestions'] = experiment_suggestions[:5]
        experimentation_info['can_experiment'] = len(available_for_experiments) > 0

        perceptions['experimentation_info'] = experimentation_info
        return perceptions

    def _add_role_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add role emergence and specialization information to perceptions.

        Includes:
        - Agent's specialized roles
        - Role opportunities
        - Expertise levels
        """
        roles_info = {}

        # Detect behavior patterns for this agent
        detected_patterns = self.sim.role_emergence.detect_behavior_patterns(agent.id)

        # Get agent's discovered roles
        agent_roles = self.sim.role_emergence.agent_roles.get(agent.id, [])

        # Pattern detection (agent might not know they have a pattern yet!)
        if detected_patterns:
            patterns_data = []
            for pattern in detected_patterns:
                # Extract pattern info
                pattern_data = {
                    'type': pattern.pattern_type,
                    'primary_actions': pattern.dominant_actions,
                    'specialization_strength': round(pattern.pattern_strength * 100, 1),
                    'action_counts': pattern.action_frequency
                }

                # Check if this pattern has been discovered as a role yet
                is_discovered = False
                for role in agent_roles:
                    if role.behavior_pattern.pattern_type == pattern.pattern_type:
                        is_discovered = True
                        break

                pattern_data['has_discovered_role'] = is_discovered

                patterns_data.append(pattern_data)

            roles_info['detected_patterns'] = patterns_data
        else:
            roles_info['detected_patterns'] = []

        # Agent's named roles
        named_roles = []
        unnamed_roles = []

        for role in agent_roles:
            role_data = {
                'role_id': role.role_id,
                'pattern_type': role.behavior_pattern.pattern_type,
                'primary_actions': role.behavior_pattern.dominant_actions,
                'specialization': round(role.behavior_pattern.pattern_strength * 100, 1),
                'times_performed': role.times_acted_in_role,
                'effectiveness': round(role.role_effectiveness * 100, 1),
                'recognition_strength': round(role.recognition_strength * 100, 1)
            }

            if role.custom_role_name:
                role_data['custom_name'] = role.custom_role_name
                role_data['recognized_by_count'] = len(role.recognized_by)
                role_data['community_adoption'] = len(role.name_adopters)
                named_roles.append(role_data)
            else:
                role_data['can_name'] = True  # Agent can name this role!
                unnamed_roles.append(role_data)

        roles_info['named_roles'] = named_roles
        roles_info['unnamed_roles'] = unnamed_roles

        # Community roles (what other agents are doing)
        community_roles = []

        for other_agent in self.sim.world.agents:
            if other_agent.id != agent.id and other_agent.alive:
                # Check if close enough to observe
                dist = agent.location.distance_to(other_agent.location)

                if dist < 40:  # Can observe roles within 40m
                    other_roles = self.sim.role_emergence.agent_roles.get(other_agent.id, [])

                    for role in other_roles:
                        if role.custom_role_name:  # Only show named roles
                            community_roles.append({
                                'agent_name': other_agent.name,
                                'role_name': role.custom_role_name,
                                'pattern': role.behavior_pattern.pattern_type,
                                'primary_actions': role.behavior_pattern.dominant_actions[:2],
                                'distance': round(dist, 1),
                                'can_learn_from': agent.id not in role.recognized_by
                            })

        # Sort by distance
        community_roles.sort(key=lambda r: r['distance'])
        roles_info['community_roles'] = community_roles[:8]  # Show closest 8

        # Role vocabulary (community-wide role names)
        popular_roles = []
        for role_name, usage_count in sorted(
            self.sim.role_emergence.role_vocabulary.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]:
            creator_id = self.sim.role_emergence.role_name_origins.get(role_name)
            creator_name = None
            if creator_id:
                for a in self.sim.world.agents:
                    if a.id == creator_id:
                        creator_name = a.name
                        break

            popular_roles.append({
                'role_name': role_name,
                'usage_count': usage_count,
                'invented_by': creator_name or 'Unknown'
            })

        roles_info['popular_role_names'] = popular_roles

        # Can agent name a role?
        roles_info['can_name_role'] = len(unnamed_roles) > 0

        perceptions['roles_info'] = roles_info
        return perceptions

    def _add_innovation_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add innovation and breakthrough information to perceptions.

        Includes:
        - Recent innovations
        - Innovation opportunities
        - Technological breakthroughs
        """
        innovations_info = {}

        # Get agent's known innovations
        agent_innovations = self.sim.innovation_manager.get_agent_innovations(agent.id)

        known_innovations = []
        for innovation in agent_innovations:
            innovation_data = {
                'id': innovation.id,
                'name': innovation.name,
                'type': innovation.discovery_type.value,
                'description': innovation.description,
                'efficiency_bonus': round(innovation.efficiency_bonus * 100, 1),
                'times_used': innovation.times_used,
                'success_rate': round(innovation.success_rate * 100, 1),
                'is_discoverer': innovation.discoverer_id == agent.id
            }

            if innovation.applies_to_actions:
                innovation_data['applies_to'] = innovation.applies_to_actions
            if innovation.produces_items:
                innovation_data['produces'] = innovation.produces_items

            known_innovations.append(innovation_data)

        innovations_info['known_innovations'] = known_innovations

        # Find nearby agents who could teach innovations
        teaching_opportunities_innovations = []

        for other_agent in self.sim.world.agents:
            if other_agent.id != agent.id and other_agent.alive:
                dist = agent.location.distance_to(other_agent.location)

                if dist < 30:  # Can learn from agents within 30m
                    other_innovations = self.sim.innovation_manager.get_agent_innovations(other_agent.id)

                    # What can they teach us?
                    can_teach_innovations = []
                    for other_innovation in other_innovations:
                        if not self.sim.innovation_manager.agent_knows(agent.id, other_innovation.id):
                            can_teach_innovations.append({
                                'name': other_innovation.name,
                                'type': other_innovation.discovery_type.value,
                                'efficiency_bonus': round(other_innovation.efficiency_bonus * 100, 1)
                            })

                    if can_teach_innovations:
                        teaching_opportunities_innovations.append({
                            'agent_name': other_agent.name,
                            'distance': round(dist, 1),
                            'can_teach': can_teach_innovations[:3]  # Show top 3
                        })

        innovations_info['learning_opportunities'] = teaching_opportunities_innovations[:5]

        # Building concepts available to use
        available_concepts = []
        for concept in self.sim.innovation_manager.building_concepts.values():
            if concept.successfully_built:
                success_rate = concept.times_succeeded / max(1, concept.times_attempted)

                available_concepts.append({
                    'id': concept.id,
                    'name': concept.name,
                    'purpose': concept.intended_purpose,
                    'materials_needed': {
                        'wood': concept.estimated_wood,
                        'stone': concept.estimated_stone,
                        'metal': concept.estimated_metal
                    },
                    'success_rate': round(success_rate * 100, 1),
                    'times_built': concept.times_succeeded,
                    'creator_id': concept.creator_id
                })

        # Sort by success rate
        available_concepts.sort(key=lambda c: c['success_rate'], reverse=True)
        innovations_info['proven_building_designs'] = available_concepts[:5]

        # Can agent innovate? (based on creativity and knowledge)
        can_innovate = False
        if hasattr(agent, 'personality'):
            creativity = getattr(agent.personality, 'creativity', 0.5)
            openness = getattr(agent.personality, 'openness', 0.5)
            can_innovate = (creativity + openness) / 2 > 0.4

        innovations_info['can_innovate'] = can_innovate

        perceptions['innovations_info'] = innovations_info
        return perceptions

    def _add_entertainment_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add fun and entertainment information to perceptions.

        Includes:
        - Games and parties
        - Art and creativity
        - Social events
        """
        from engine.psychology import NeedType

        fun_info = {}

        # Active celebrations nearby
        nearby_celebrations = []
        for celebration in self.sim.fun_system.active_celebrations.values():
            cel_loc = celebration.location
            dist = ((agent.location.x - cel_loc[0])**2 +
                    (agent.location.y - cel_loc[1])**2)**0.5

            if dist < 60:  # Can see celebrations within 60m
                nearby_celebrations.append({
                    'id': celebration.id,
                    'type': celebration.celebration_type.value,
                    'name': celebration.celebration_name,
                    'distance': round(dist, 1),
                    'participants_count': len(celebration.participants),
                    'time_remaining': max(0, int(celebration.duration_ticks)),
                    'mood_boost': celebration.mood_boost,
                    'is_participant': agent.id in celebration.participants,
                    'can_join': dist < 20 and agent.id not in celebration.participants
                })

        nearby_celebrations.sort(key=lambda c: c['distance'])
        fun_info['nearby_celebrations'] = nearby_celebrations

        # Active games nearby
        nearby_games = []
        for game in self.sim.fun_system.active_games.values():
            # Games don't have locations, assume they're at organizer's location
            # For simplicity, show all active games
            if not game.completed:
                nearby_games.append({
                    'id': game.id,
                    'type': game.game_type.value,
                    'players_count': len(game.players),
                    'spectators_count': len(game.spectators),
                    'is_player': agent.id in game.players,
                    'is_spectator': agent.id in game.spectators,
                    'can_spectate': agent.id not in game.players
                })

        fun_info['nearby_games'] = nearby_games[:5]

        # The best art this agent hasn't seen yet (walking the pieces in order of
        # quality, so this doesn't build a record for every piece ever made)
        nearby_art = []
        for art_piece in self.sim.fun_system.art_by_quality():
            if agent.id not in art_piece.viewers:
                nearby_art.append({
                    'id': art_piece.id,
                    'type': art_piece.art_type,
                    'title': art_piece.title,
                    'quality': round(art_piece.quality * 100, 1),
                    'viewers_count': len(art_piece.viewers),
                    'cultural_value': round(art_piece.cultural_value, 2)
                })
                if len(nearby_art) == 5:
                    break
        fun_info['art_to_view'] = nearby_art

        # Can agent create art?
        can_create_art = False
        if hasattr(agent, 'personality'):
            creativity = getattr(agent.personality, 'creativity', 0.5)
            can_create_art = creativity > 0.3

        fun_info['can_create_art'] = can_create_art

        # Agent's fun statistics
        fun_stats = self.sim.fun_system.get_agent_fun_stats(agent.id)
        fun_info['your_fun_stats'] = {
            'celebrations_attended': fun_stats.get('celebrations_attended', 0),
            'games_played': fun_stats.get('games_played', 0),
            'games_won': fun_stats.get('games_won', 0),
            'art_created': fun_stats.get('art_created', 0),
            'fun_score': fun_stats.get('fun_score', 0)
        }

        # Should agent seek fun? (based on mood/happiness)
        should_seek_fun = False
        if hasattr(agent, 'happiness'):
            should_seek_fun = agent.happiness < 0.6
        elif hasattr(agent, 'needs') and hasattr(agent.needs, 'needs'):

            # Check if they need social interaction or fun (using NeedType from top-level import)
            social_need = agent.needs.needs.get(NeedType.BELONGING)
            friendship_need = agent.needs.needs.get(NeedType.FRIENDSHIP)
            social_level = social_need.level if social_need else 1.0
            friendship_level = friendship_need.level if friendship_need else 1.0
            should_seek_fun = (social_level < 0.5 or friendship_level < 0.5)

        fun_info['should_seek_fun'] = should_seek_fun

        # Traditions in community
        popular_traditions = []
        for tradition_name, count in sorted(
            self.sim.fun_system.traditions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]:
            popular_traditions.append({
                'tradition': tradition_name.replace('_', ' ').title(),
                'times_celebrated': count
            })

        fun_info['community_traditions'] = popular_traditions

        perceptions['fun_info'] = fun_info
        return perceptions

    def _add_consequences_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add consequences and reputation information to perceptions.

        Includes:
        - Karma and reputation
        - Historical precedents
        - Social consequences
        """
        from datetime import datetime

        consequences_info = {}

        # Recent consequences in community (warnings!)
        recent_consequences = []
        for consequence in list(self.sim.consequence_engine.consequences.values())[-20:]:  # Last 20
            # Calculate time since consequence
            time_since = (datetime.now() - consequence.timestamp).total_seconds()

            if time_since < 3600:  # Last hour
                recent_consequences.append({
                    'type': consequence.consequence_type,
                    'action': consequence.caused_by_action,
                    'severity': round(consequence.severity * 100, 1),
                    'description': consequence.description,
                    'affected_count': len(consequence.affected_agents),
                    'was_affected': agent.id in consequence.affected_agents,
                    'secondary_effects': consequence.secondary_consequences
                })

        consequences_info['recent_consequences'] = recent_consequences[:5]

        # Agent's past consequences (learn from mistakes!)
        agent_consequences = []
        for consequence in self.sim.consequence_engine.consequences.values():
            if agent.id in consequence.affected_agents:
                agent_consequences.append({
                    'type': consequence.consequence_type,
                    'action': consequence.caused_by_action,
                    'severity': round(consequence.severity * 100, 1),
                    'description': consequence.description
                })

        # Show worst consequences experienced
        agent_consequences.sort(key=lambda c: c['severity'], reverse=True)
        consequences_info['your_past_consequences'] = agent_consequences[:3]

        # Risk warnings for common actions
        risk_warnings = {}

        # Evaluate risk of fighting if there are nearby enemies
        combat_risks = {}
        nearby_enemies = combat_risks.get('nearby_agents', [])

        if nearby_enemies:
            # Get strongest enemy
            strongest = max(nearby_enemies, key=lambda e: e.get('health', 50))
            opponent_strength = strongest.get('health', 50) / 100.0

            fight_risk = self.sim.consequence_engine.evaluate_action_risk(
                'fight',
                0.5,  # Default skill
                {'opponent_strength': opponent_strength}
            )

            if fight_risk['total_risk'] > 0.2:
                risk_warnings['fight'] = {
                    'total_risk': round(fight_risk['total_risk'] * 100, 1),
                    'main_risks': [
                        {
                            'type': r['type'],
                            'probability': round(r['probability'] * 100, 1),
                            'severity': round(r['severity'] * 100, 1)
                        }
                        for r in fight_risk['risks'][:2]
                    ]
                }

        # Experimentation risks
        experimentation_info = perceptions.get('experimentation_info', {})
        if experimentation_info.get('can_experiment'):
            exp_risk = self.sim.consequence_engine.evaluate_action_risk(
                'experiment',
                0.5,
                {'materials': ['unknown']}
            )

            if exp_risk['total_risk'] > 0.1:
                risk_warnings['experiment'] = {
                    'total_risk': round(exp_risk['total_risk'] * 100, 1),
                    'warning': 'Experimentation can be dangerous!'
                }

        consequences_info['current_risk_warnings'] = risk_warnings

        # Learned dangers (from agent memory)
        learned_dangers = []
        if hasattr(agent, 'memory') and hasattr(agent.memory, 'procedural_memory'):
            for risk_key, risk_value in agent.memory.procedural_memory.items():
                if risk_key.startswith('risk_') and risk_value > 0.6:
                    action_name = risk_key.replace('risk_', '')
                    learned_dangers.append({
                        'action': action_name,
                        'perceived_risk': round(risk_value * 100, 1)
                    })

        learned_dangers.sort(key=lambda d: d['perceived_risk'], reverse=True)
        consequences_info['learned_dangers'] = learned_dangers[:5]

        # Community danger statistics
        danger_stats = self.sim.consequence_engine.get_statistics()

        consequences_info['community_stats'] = {
            'total_deaths': danger_stats.get('deaths', 0),
            'total_bankruptcies': danger_stats.get('bankruptcies', 0),
            'total_consequences': danger_stats.get('total_consequences', 0),
            'most_dangerous_action': danger_stats.get('most_dangerous_action', 'None')
        }

        perceptions['consequences_info'] = consequences_info
        return perceptions

    def _add_agriculture_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add agriculture and farming information to perceptions.

        Includes:
        - Crop status
        - Farm locations
        - Seasonal cycles
        """
        agriculture_info = {}
        from world.agriculture import Season, CropType, AnimalType

        # Current season and its effects
        current_season = self.sim.agriculture.current_season
        growth_multiplier = self.sim.agriculture.get_season_growth_multiplier()

        agriculture_info['current_season'] = current_season.value
        agriculture_info['growth_multiplier'] = growth_multiplier
        agriculture_info['best_for_planting'] = current_season.value in ['spring', 'summer']
        agriculture_info['harvest_season'] = current_season.value == 'autumn'

        # Agent's crops and animals
        agent_fields = [f for f in self.sim.agriculture.crop_fields.values() if f.owner_id == agent.id]
        agent_livestock = [a for a in self.sim.agriculture.domesticated_animals.values() if a.owner_id == agent.id]

        agriculture_info['my_crop_fields'] = len(agent_fields)
        agriculture_info['my_animals'] = len(agent_livestock)

        # Crop maturity
        mature_crops = [f for f in agent_fields if f.growth_progress >= 1.0 and not f.harvested]
        agriculture_info['crops_ready_to_harvest'] = len(mature_crops)

        # Animal products ready
        # An animal has something to give once its production interval has passed
        tick = self.sim.world.time.current_tick
        animals_ready = [a for a in agent_livestock if tick - a.last_production >= a.production_rate]
        agriculture_info['animals_ready_for_harvest'] = len(animals_ready)

        # Can plant crops?
        has_seeds = agent.inventory.has_item('seeds')
        agriculture_info['can_plant_crops'] = has_seeds
        agriculture_info['has_seeds'] = has_seeds

        perceptions['agriculture_info'] = agriculture_info
        return perceptions

    def _add_health_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add health and disease information to perceptions.

        Includes:
        - Current illnesses
        - Available medicines
        - Healer locations
        """
        health_info = {}
        from world.health import DiseaseType, Severity

        # Agent's diseases
        agent_diseases = self.sim.health.get_agent_diseases(agent.id)
        health_info['is_sick'] = len(agent_diseases) > 0
        health_info['disease_count'] = len(agent_diseases)

        if agent_diseases:
            worst_disease = max(agent_diseases, key=lambda d: d.severity.value if hasattr(d.severity, 'value') else 0)
            health_info['worst_disease'] = worst_disease.disease_type.value
            health_info['worst_severity'] = worst_disease.severity.value

        # Known medicines (access medicines dict directly)
        known_medicines = list(self.sim.health.medicines.values())
        health_info['known_medicines_count'] = len(known_medicines)

        # Can heal others?
        agent_is_healer = agent.id in [m.discoverer_id for m in known_medicines if m.discoverer_id]
        health_info['is_healer'] = agent_is_healer

        # Nearby sick agents
        sick_agents_nearby = []
        for other_agent in self.sim.world.agents:
            if other_agent.id == agent.id or not other_agent.alive:
                continue
            dist = agent.location.distance_to(other_agent.location)
            if dist < 30:
                other_diseases = self.sim.health.get_agent_diseases(other_agent.id)
                if other_diseases:
                    sick_agents_nearby.append({
                        'agent_id': other_agent.id,
                        'agent_name': other_agent.name,
                        'disease_count': len(other_diseases),
                        'distance': round(dist, 1)
                    })

        health_info['sick_agents_nearby'] = sick_agents_nearby
        health_info['can_heal_others'] = agent_is_healer and len(sick_agents_nearby) > 0

        perceptions['health_info'] = health_info
        return perceptions

    def _add_territory_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add territory and land ownership information to perceptions.

        Includes:
        - Land ownership
        - Borders and boundaries
        - Trespassing conflicts
        """
        territory_info = {}

        # Agent's territories
        agent_territories = self.sim.territory.get_agent_territories(agent.id)
        territory_info['my_territories'] = len(agent_territories)

        # Current location territory
        current_territory = self.sim.territory.get_territory_at_location(
            (agent.location.x, agent.location.y)
        )

        if current_territory:
            territory_info['in_territory'] = True
            territory_info['territory_name'] = current_territory.name
            territory_info['is_my_territory'] = current_territory.owner_id == agent.id
            territory_info['is_trespassing'] = current_territory.owner_id != agent.id and agent.id not in current_territory.allowed_agents
            territory_info['territory_defended'] = current_territory.defended
        else:
            territory_info['in_territory'] = False
            territory_info['is_trespassing'] = False

        # Can claim territory?
        unclaimed_location = current_territory is None
        territory_info['can_claim_here'] = unclaimed_location

        # Nearby territories
        nearby_territories = self.sim.territory.get_nearby_territories(
            (agent.location.x, agent.location.y),
            radius=50.0
        )
        territory_info['nearby_territories'] = len(nearby_territories)

        perceptions['territory_info'] = territory_info
        return perceptions

    def _add_chemistry_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add chemistry and reactions information to perceptions.

        Includes:
        - Known elements
        - Chemical reactions
        - Compound synthesis
        """
        chemistry_info = {}

        # Discovered elements
        discovered_elements = self.sim.chemistry.get_discovered_elements()
        chemistry_info['discovered_elements'] = len(discovered_elements)
        chemistry_info['total_elements'] = len(self.sim.chemistry.elements)

        # Element discovery progress
        chemistry_info['element_discovery_percent'] = round(
            (len(discovered_elements) / max(1, len(self.sim.chemistry.elements))) * 100, 1
        )

        # Known compounds
        discovered_compounds = self.sim.chemistry.get_discovered_compounds()
        chemistry_info['discovered_compounds'] = len(discovered_compounds)

        # Can perform chemistry?
        has_materials_for_chemistry = agent.inventory.has_item('wood') or agent.inventory.has_item('iron_ore')
        chemistry_info['can_perform_chemistry'] = has_materials_for_chemistry

        # Can smelt iron?
        can_smelt = agent.inventory.has_item('iron_ore') and agent.inventory.has_item('wood')
        chemistry_info['can_smelt_iron'] = can_smelt

        # Agent's discoveries
        agent_element_discoveries = [e for e in discovered_elements if e.discoverer_id == agent.id]
        chemistry_info['my_element_discoveries'] = len(agent_element_discoveries)

        perceptions['chemistry_info'] = chemistry_info
        return perceptions

    def _add_energy_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add energy systems information to perceptions.

        Includes:
        - Power plants
        - Fuel sources
        - Electricity grid
        """
        energy_info = {}
        from world.energy import EnergyType

        # Discovered energy sources
        discovered_energy = self.sim.energy.get_discovered_energy_sources()
        energy_info['discovered_energy_sources'] = len(discovered_energy)
        energy_info['available_energy_types'] = [e.value for e in self.sim.energy.discovered_energy_types]

        # Current era progression
        has_fire = EnergyType.FIRE in self.sim.energy.discovered_energy_types
        has_coal = EnergyType.COAL in self.sim.energy.discovered_energy_types
        has_oil = EnergyType.OIL in self.sim.energy.discovered_energy_types
        has_nuclear = EnergyType.NUCLEAR in self.sim.energy.discovered_energy_types

        energy_info['has_fire'] = has_fire
        energy_info['has_coal'] = has_coal
        energy_info['has_oil'] = has_oil
        energy_info['has_nuclear'] = has_nuclear

        # Agent's power plants
        agent_plants = self.sim.energy.get_plants_by_owner(agent.id)
        energy_info['my_power_plants'] = len(agent_plants)

        if agent_plants:
            total_output = sum(p.current_output for p in agent_plants)
            energy_info['my_power_output'] = round(total_output, 1)
        else:
            energy_info['my_power_output'] = 0.0

        # Can build power plant?
        has_materials = agent.inventory.has_item('materials')
        energy_info['can_build_power_plant'] = has_materials

        perceptions['energy_info'] = energy_info
        return perceptions

    def _add_materials_info(self, agent, perceptions: Dict) -> Dict:
        """
        Add materials science information to perceptions.

        Includes:
        - Material ages (Stone → Silicon)
        - Alloy discoveries
        - Material properties
        """
        materials_info = {}

        # Current material era
        current_era = self.sim.materials_science.get_current_era()
        materials_info['current_era'] = current_era.value
        materials_info['current_era_name'] = current_era.value.replace('_', ' ').title()

        # Discovered materials
        discovered_mats = self.sim.materials_science.get_discovered_materials()
        materials_info['discovered_materials'] = len(discovered_mats)
        materials_info['total_materials'] = len(self.sim.materials_science.materials)

        # Material discovery progress
        materials_info['material_discovery_percent'] = round(
            (len(discovered_mats) / max(1, len(self.sim.materials_science.materials))) * 100, 1
        )

        # Alloys created
        materials_info['alloys_created'] = len(self.sim.materials_science.discovered_alloys)
        materials_info['total_alloys'] = len(self.sim.materials_science.alloys)

        # Can create alloys?
        can_make_bronze = agent.inventory.has_item('copper') and agent.inventory.has_item('tin')
        can_make_steel = agent.inventory.has_item('iron') and agent.inventory.has_item('carbon')

        materials_info['can_make_bronze'] = can_make_bronze
        materials_info['can_make_steel'] = can_make_steel

        # Can refine materials?
        can_refine = agent.inventory.has_item('iron_ore') or agent.inventory.has_item('sand')
        materials_info['can_refine_materials'] = can_refine

        # Agent's material discoveries
        agent_material_discoveries = [m for m in discovered_mats if m.discoverer_id == agent.id]
        materials_info['my_material_discoveries'] = len(agent_material_discoveries)

        perceptions['materials_info'] = materials_info
        return perceptions
