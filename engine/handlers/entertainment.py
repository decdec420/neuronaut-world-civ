"""
Entertainment Action Handler - Handles agent entertainment and fun actions.

This handler manages all entertainment-related actions including:
- GAMBLE: Dice gambling games with stakes
- PLAY_GAME: Competitive games and races
- CREATE_ART: Artistic creation (painting, sculpture, music, etc.)
- CELEBRATE: Organizing celebrations and parties
- TELL_STORY: Storytelling between agents

These actions provide emotional satisfaction, social bonding, and cultural enrichment.
"""

from typing import TYPE_CHECKING
import random
import logging

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    validate_agent_alive,
    combine_validations,
)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)


class EntertainmentHandler(ActionHandler):
    """Handles entertainment and fun actions for agents."""

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [
            ActionType.GAMBLE,
            ActionType.PLAY_GAME,
            ActionType.CREATE_ART,
            ActionType.CELEBRATE,
            ActionType.TELL_STORY
        ]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid

        # GAMBLE, PLAY_GAME, TELL_STORY need target
        if action.action_type in [ActionType.GAMBLE, ActionType.PLAY_GAME, ActionType.TELL_STORY]:
            if not action.target_agent:
                return False, "No target agent specified"
            target = self.context.get_agent_by_id(action.target_agent)
            if not target or not target.alive:
                return False, "Target not found or dead"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.fun_system import CelebrationType
        from engine.events import EventCategory, EventImportance
        from engine.psychology import EmotionType

        fun_system = self.context.get_system('fun_system')
        current_tick = self.context.current_tick

        if action.action_type == ActionType.GAMBLE:
            return self._handle_gamble(agent, action, fun_system, current_tick)
        elif action.action_type == ActionType.PLAY_GAME:
            return self._handle_play_game(agent, action, fun_system, current_tick)
        elif action.action_type == ActionType.CREATE_ART:
            return self._handle_create_art(agent, fun_system, current_tick)
        elif action.action_type == ActionType.CELEBRATE:
            return self._handle_celebrate(agent, fun_system, current_tick)
        elif action.action_type == ActionType.TELL_STORY:
            return self._handle_tell_story(agent, action, current_tick)

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown entertainment action")

    def _handle_gamble(self, agent, action, fun_system, current_tick):
        from engine.psychology import EmotionType

        target = self.context.get_agent_by_id(action.target_agent)
        if not target or not fun_system:
            return ActionResult(success=False, emotional_impact=0.0, message="Cannot gamble")

        avg_wealth = (agent.wealth + target.wealth) / 2
        stakes = max(0.0, min(10.0, avg_wealth * 0.1))

        game = fun_system.start_dice_game(
            players=[(agent.id, agent.name), (target.id, target.name)],
            stakes=stakes
        )
        result = fun_system.resolve_dice_game(game)

        if result and 'winner' in result:
            winner = self.context.get_agent_by_id(result['winner'])
            loser = agent if result['winner'] != agent.id else target

            if stakes > 0:
                loser.wealth = max(0, loser.wealth - stakes)
                winner.wealth += result['pot']

            if result['winner'] == agent.id:
                agent.emotions.trigger_emotion(EmotionType.JOY, 0.3)
                target.emotions.trigger_emotion(EmotionType.SADNESS, 0.15)
                emotional_impact = 0.3
            else:
                agent.emotions.trigger_emotion(EmotionType.SADNESS, 0.15)
                target.emotions.trigger_emotion(EmotionType.JOY, 0.3)
                emotional_impact = -0.15

            agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
            target.needs.satisfy_need(NeedType.BELONGING, 0.2)
            winner.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.25)

            return ActionResult(
                success=True,
                emotional_impact=emotional_impact,
                message=f"Gambling game: {winner.name} won!",
                metadata={'winner': winner.id, 'stakes': stakes}
            )

        return ActionResult(success=False, emotional_impact=0.0, message="Gambling failed")

    def _handle_play_game(self, agent, action, fun_system, current_tick):
        from engine.psychology import EmotionType

        target = self.context.get_agent_by_id(action.target_agent)
        if not target or not fun_system:
            return ActionResult(success=False, emotional_impact=0.0, message="Cannot play game")

        if random.random() < 0.5:
            # RACE
            agent_speed = agent.skills.get_skill('agility') if hasattr(agent.skills, 'agility') else 0.5
            target_speed = target.skills.get_skill('agility') if hasattr(target.skills, 'agility') else 0.5

            game = fun_system.start_race(
                racers=[(agent.id, agent.name, agent_speed), (target.id, target.name, target_speed)]
            )
            result = fun_system.resolve_race(game, {agent.id: agent_speed, target.id: target_speed})

            if result and 'winner' in result:
                winner = self.context.get_agent_by_id(result['winner'])

                if result['winner'] == agent.id:
                    agent.emotions.trigger_emotion(EmotionType.JOY, 0.25)
                    target.emotions.trigger_emotion(EmotionType.SADNESS, 0.1)
                    emotional_impact = 0.25
                else:
                    agent.emotions.trigger_emotion(EmotionType.SADNESS, 0.1)
                    target.emotions.trigger_emotion(EmotionType.JOY, 0.25)
                    emotional_impact = -0.1

                agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
                target.needs.satisfy_need(NeedType.BELONGING, 0.2)
                winner.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)

                return ActionResult(
                    success=True,
                    emotional_impact=emotional_impact,
                    message=f"Race: {winner.name} won!",
                    metadata={'winner': winner.id, 'type': 'race'}
                )
        else:
            # Simple game - both have fun
            from engine.psychology import EmotionType
            agent.emotions.trigger_emotion(EmotionType.JOY, 0.2)
            target.emotions.trigger_emotion(EmotionType.JOY, 0.2)
            agent.needs.satisfy_need(NeedType.BELONGING, 0.25)
            target.needs.satisfy_need(NeedType.BELONGING, 0.25)

            return ActionResult(
                success=True,
                emotional_impact=0.2,
                message=f"Played game with {target.name}",
                metadata={'type': 'simple_game'}
            )

        return ActionResult(success=False, emotional_impact=0.0, message="Game failed")

    def _handle_create_art(self, agent, fun_system, current_tick):
        from engine.psychology import EmotionType

        if not fun_system:
            return ActionResult(success=False, emotional_impact=0.0, message="Fun system unavailable")

        creativity_skill = agent.personality.creativity
        relevant_skill = agent.skills.get_skill('crafting')

        art_types = ["painting", "sculpture", "song", "story", "dance"]
        if agent.personality.creativity > 0.8:
            art_type = random.choice(art_types)
        else:
            art_type = random.choice(["song", "story"])

        art = fun_system.create_art(
            agent.id,
            agent.name,
            art_type,
            creativity_skill,
            relevant_skill
        )

        emotional_impact = 0.2 + (art.quality * 0.3)
        agent.emotions.trigger_emotion(EmotionType.JOY, emotional_impact)
        agent.needs.satisfy_need(NeedType.CREATIVITY, 0.4)
        agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
        agent.needs.satisfy_need(NeedType.MEANING, 0.2)

        if art.quality > 0.7:
            agent.status = min(1.0, agent.status + art.fame_generated)

        return ActionResult(
            success=True,
            emotional_impact=emotional_impact,
            message=f"Created {art_type}: {art.title}",
            metadata={'art_type': art_type, 'quality': art.quality, 'title': art.title}
        )

    def _handle_celebrate(self, agent, fun_system, current_tick):
        from world.fun_system import CelebrationType
        from engine.psychology import EmotionType

        if not fun_system:
            return ActionResult(success=False, emotional_impact=0.0, message="Fun system unavailable")

        nearby_agents = [
            a.id for a in self.context.world.agents
            if abs(a.location.x - agent.location.x) < 20 and
               abs(a.location.y - agent.location.y) < 20 and
               a.id != agent.id and a.alive
        ]

        celebration = fun_system.trigger_celebration(
            CelebrationType.ACHIEVEMENT_PARTY,
            agent.id,
            agent.name,
            "Organized for fun and social bonding",
            (agent.location.x, agent.location.y),
            nearby_agents
        )

        agent.emotions.trigger_emotion(EmotionType.JOY, 0.3)
        agent.needs.satisfy_need(NeedType.BELONGING, 0.3)
        agent.needs.satisfy_need(NeedType.MEANING, 0.25)

        return ActionResult(
            success=True,
            emotional_impact=0.3,
            message=f"Organized celebration with {len(celebration.participants)} attendees",
            metadata={'participants': len(celebration.participants)}
        )

    def _handle_tell_story(self, agent, action, current_tick):
        from engine.psychology import EmotionType

        target = self.context.get_agent_by_id(action.target_agent)
        if not target:
            return ActionResult(success=False, emotional_impact=0.0, message="Target not found")

        agent.emotions.trigger_emotion(EmotionType.JOY, 0.15)
        target.emotions.trigger_emotion(EmotionType.JOY, 0.15)
        agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
        target.needs.satisfy_need(NeedType.BELONGING, 0.2)
        agent.needs.satisfy_need(NeedType.MEANING, 0.15)
        target.needs.satisfy_need(NeedType.MEANING, 0.15)

        relationship_manager = self.context.get_system('relationship_manager')
        if relationship_manager:
            relationship_manager.update_relationship(
                agent.id, target.id, 'storytelling', positive=True
            )

        return ActionResult(
            success=True,
            emotional_impact=0.15,
            message=f"Told story to {target.name}",
            metadata={'target': target.id}
        )

    def get_required_systems(self) -> list[str]:
        return ['world', 'fun_system']
