"""
Public works: build_road, dig_well, build_streetlight (world/infrastructure.py).

Each is rejected up front when it can't work (no stone, nowhere walked often
enough to pave, a well already close by, no glass...), so agents choose
something else rather than fail.
"""

from typing import TYPE_CHECKING

from engine.action_handlers import ActionHandler, ActionResult, validate_agent_alive
from agents.agent import ActionType, Action, NeedType
from world import infrastructure as infra

if TYPE_CHECKING:
    from agents.agent import Agent


class InfrastructureHandler(ActionHandler):

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in (ActionType.BUILD_ROAD, ActionType.DIG_WELL, ActionType.BUILD_STREETLIGHT)

    def get_required_systems(self) -> list[str]:
        return ['world', 'infrastructure', 'pathfinder']

    @property
    def works(self) -> infra.Infrastructure:
        return self.context.get_system('infrastructure')

    # -- what can be done here -----------------------------------------------------

    @staticmethod
    def _post(agent):
        """What the lamp post would be made of (wood leaves room for fuel)."""
        for item, qty in infra.LIGHT_POSTS:
            extra = 1 if item == "wood" and not any(agent.inventory.has_item(f) for f in infra.FUELS if f != "wood") else 0
            if agent.inventory.has_item(item, qty + extra):
                return item, qty
        return None

    @staticmethod
    def _fuel(agent, keep_wood: int = 0):
        for fuel in infra.FUELS:
            if agent.inventory.items.get(fuel, 0) > (keep_wood if fuel == "wood" else 0):
                return fuel
        return None

    def _lamp_to_refuel(self, agent):
        lamp = self.works.light_near(agent.location.x, agent.location.y, 2.5)
        if lamp is not None and lamp.fuel < infra.LIGHT_FUEL_MAX and self._fuel(agent):
            return lamp
        return None

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive = validate_agent_alive(agent)
        if not alive[0]:
            return alive
        inv = agent.inventory
        if action.action_type == ActionType.BUILD_ROAD:
            if not inv.has_item("stone", infra.ROAD_STONE_PER_TILE):
                return False, f"A road needs stone ({infra.ROAD_STONE_PER_TILE} a tile)"
            if not self.works.road_plan(agent, self.context.get_system('pathfinder')):
                return False, "Nowhere you walk often enough, or it's already paved"
            return True, ""
        if action.action_type == ActionType.DIG_WELL:
            if not all(inv.has_item(i, q) for i, q in infra.WELL_COST.items()):
                return False, "A well needs " + ", ".join(f"{q} {i}" for i, q in infra.WELL_COST.items())
            if self.works.well_near(agent.location.x, agent.location.y, infra.WELL_SPACING):
                return False, "There's already a well close by"
            tile = self.context.world.map.get_tile(agent.location)
            if tile is not None and tile.terrain.value == "water":
                return False, "You're standing in water"
            return True, ""
        # Street light: refuel one here, or put up a new one
        if self._lamp_to_refuel(agent):
            return True, ""
        if not inv.has_item("glass"):
            return False, "A street light needs glass (refine sand into glass)"
        post = self._post(agent)
        if post is None:
            return False, "A street light needs a post: 2 wood or 1 metal"
        if not self._fuel(agent, keep_wood=post[1] if post[0] == "wood" else 0):
            return False, "A street light needs fuel to burn: wood or coal"
        if self.works.light_near(agent.location.x, agent.location.y, infra.LIGHT_SPACING):
            return False, "There's already a light close by"
        return True, ""

    # -- doing it ----------------------------------------------------------------

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        tick = self.context.current_tick
        if action.action_type == ActionType.BUILD_ROAD:
            return self._road(agent, tick)
        if action.action_type == ActionType.DIG_WELL:
            return self._well(agent, tick)
        return self._light(agent, tick)

    def _log(self, importance, title, text, agent):
        if self.context.event_logger:
            from engine.events import EventCategory
            self.context.event_logger.log_event(
                EventCategory.ECONOMIC,
                importance, title, text, self.context.current_tick, [agent.id],
                {'x': agent.location.x, 'y': agent.location.y})

    def _road(self, agent, tick) -> ActionResult:
        from engine.events import EventImportance
        pathfinder = self.context.get_system('pathfinder')
        tiles = self.works.road_plan(agent, pathfinder)
        tiles = tiles[:agent.inventory.items.get("stone", 0) // infra.ROAD_STONE_PER_TILE]
        agent.inventory.remove_item("stone", len(tiles) * infra.ROAD_STONE_PER_TILE)
        self.works.pave(tiles, pathfinder)
        agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
        agent.needs.satisfy_need(NeedType.BELONGING, 0.1)
        agent.skills.learn_skill('construction', 0.05)
        if len(self.works.roads) == len(tiles):
            self._log(EventImportance.MAJOR, f"🛣️ {agent.name} laid the first road",
                      f"{len(tiles)} tiles paved toward where {agent.name} walks most.", agent)
        return ActionResult(success=True, emotional_impact=0.4,
                            message=f"Paved {len(tiles)} tiles of road ({len(self.works.roads)} in all)",
                            metadata={'road_tiles': len(tiles), 'product': 'road'})

    def _well(self, agent, tick) -> ActionResult:
        from engine.events import EventImportance
        for item, qty in infra.WELL_COST.items():
            agent.inventory.remove_item(item, qty)
        well = self.works.dig_well(self.context.world, agent, tick)
        agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.4)
        agent.needs.satisfy_need(NeedType.SECURITY, 0.2)
        agent.skills.learn_skill('construction', 0.05)
        self._log(EventImportance.MODERATE, f"💧 {agent.name} dug a well",
                  f"Water at ({well.x}, {well.y}) for anyone who needs it.", agent)
        return ActionResult(success=True, emotional_impact=0.5, message="Dug a well",
                            metadata={'well_id': well.id, 'product': 'well'})

    def _light(self, agent, tick) -> ActionResult:
        from engine.events import EventImportance
        lamp = self._lamp_to_refuel(agent)
        if lamp is not None:
            added = 0
            while lamp.fuel < infra.LIGHT_FUEL_MAX and self._fuel(agent):
                agent.inventory.remove_item(self._fuel(agent), 1)
                lamp.fuel += 1
                added += 1
            agent.needs.satisfy_need(NeedType.BELONGING, 0.1)
            return ActionResult(success=True, emotional_impact=0.2,
                                message=f"Added {added} nights of fuel to the street light",
                                metadata={'light_id': lamp.id, 'refuelled': added})
        post, post_qty = self._post(agent)
        agent.inventory.remove_item("glass", 1)
        agent.inventory.remove_item(post, post_qty)
        lamp = infra.StreetLight(self.works._id("light"), int(agent.location.x), int(agent.location.y),
                                 agent.id, tick)
        while lamp.fuel < infra.LIGHT_FUEL_MAX and self._fuel(agent):
            agent.inventory.remove_item(self._fuel(agent), 1)
            lamp.fuel += 1
        self.works.lights[lamp.id] = lamp
        agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.4)
        agent.needs.satisfy_need(NeedType.SECURITY, 0.2)
        agent.needs.satisfy_need(NeedType.CREATIVITY, 0.2)
        self._log(EventImportance.MODERATE, f"🏮 {agent.name} put up a street light",
                  f"A glass lamp on a {post} post, with {lamp.fuel} nights of fuel.", agent)
        return ActionResult(success=True, emotional_impact=0.5,
                            message=f"Put up a street light ({lamp.fuel} nights of fuel)",
                            metadata={'light_id': lamp.id, 'product': 'street light'})
