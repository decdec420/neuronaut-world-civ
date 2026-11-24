"""
Governance Action Handler - Handles agent political and governance actions.

This handler manages all governance-related actions including:
- GOVERN: Forming governments and establishing political power
- MAKE_LAW: Proposing and creating laws within governments
- VOTE: Voting on laws and elections

These actions enable agents to create political structures, establish rules,
and participate in collective decision-making.
"""

from typing import TYPE_CHECKING
import logging

from engine.action_handlers import (
    ActionHandler,
    ActionResult,
    ActionContext,
    validate_agent_alive,
)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)


# What a law can forbid when its proposer doesn't say: things done to other
# people. The proposer picks the one it has suffered from most.
BANNABLE = ("fight", "gamble", "trade", "claim_territory")


class GovernanceHandler(ActionHandler):
    """Governments, laws and votes.

    GOVERN  - take part in governing: an agent outside any government joins
              the one its best-liked acquaintance belongs to, or founds one if
              it knows nobody in one; a leader exercises leadership; during an
              open election a citizen stands as a candidate.
    MAKE_LAW - propose a law in your government (if its rules let you). It
              bans an action: the one named in the parameters/details, or the
              one the proposer has suffered from most.
    VOTE    - vote in your government's open election, or on a law you
              haven't voted on, according to your own view.
    """

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [ActionType.GOVERN, ActionType.MAKE_LAW, ActionType.VOTE]

    # -- helpers ---------------------------------------------------------------

    def _liking(self, agent_id: str, other_id: str) -> float:
        rel = self.context.get_system('relationship_manager').get_relationship(agent_id, other_id)
        if rel is None:
            return 0.0
        return -rel.strength if rel.relationship_type.value == 'rivalry' else rel.strength

    def _government_to_join(self, agent):
        """The government of the person this agent likes best, if any."""
        gm = self.context.get_system('governance_manager')
        best, best_liking = None, 0.0
        for gov in gm.governments.values():
            if not gov.active:
                continue
            for citizen in sorted(gov.citizens):   # ties go the same way every time
                liking = self._liking(agent.id, citizen)
                if liking > best_liking:
                    best, best_liking = gov, liking
        return best

    def _vote_target(self, agent):
        """('election', election) or ('law', law) the agent can vote on now."""
        gm = self.context.get_system('governance_manager')
        gov = gm.get_agent_government(agent.id)
        if gov is None:
            return None
        election = gm.open_election(gov.id)
        if election and agent.id in election.eligible_voters and agent.id not in election.votes_cast \
                and election.candidates:
            return 'election', election
        for law_id in gov.laws:
            law = gm.laws.get(law_id)
            if law and law.active and agent.id not in law.supporters and agent.id not in law.opposers:
                return 'law', law
        return None

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        alive_valid = validate_agent_alive(agent)
        if not alive_valid[0]:
            return alive_valid
        gm = self.context.get_system('governance_manager')
        if gm is None:
            return False, "Governance system unavailable"
        if action.action_type == ActionType.MAKE_LAW:
            gov = gm.get_agent_government(agent.id)
            if gov is None:
                return False, "Not part of any government"
            if not gm._can_make_law(agent.id, gov):
                return False, "No authority to make laws here"
            params = action.parameters or {}
            if not self._wants_tax(agent, gov, params):
                ban = self._proposed_ban(agent, params)
                if ban in self._bans_in_force(gm, gov):
                    # Proposing it again changes nothing (agents used to pass
                    # "No gamble" three and four times over)
                    return False, f"No {ban.replace('_', ' ')} is already the law"
        if action.action_type == ActionType.VOTE:
            params = action.parameters or {}
            if not params.get('vote_target') and self._vote_target(agent) is None:
                return False, "Nothing to vote on"
        return True, ""

    # -- actions -----------------------------------------------------------------

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from world.governance import GovernmentType
        from engine.psychology import EmotionType

        gm = self.context.get_system('governance_manager')
        tick = self.context.current_tick
        params = action.parameters or {}

        if action.action_type == ActionType.GOVERN:
            gov = gm.get_agent_government(agent.id)
            if gov is None:
                to_join = self._government_to_join(agent)
                if to_join is not None:
                    gm.agent_joins_government(agent.id, to_join.id)
                    agent.needs.satisfy_need(NeedType.BELONGING, 0.3)
                    self._log(f"{agent.name} joined {to_join.name}",
                              f"{agent.name} became a citizen of {to_join.name}.", tick, [agent.id])
                    return ActionResult(success=True, emotional_impact=0.3, message=f"Joined {to_join.name}",
                                        metadata={'government_id': to_join.id, 'joined': True})

                # Found one. The form follows the founder's temperament.
                p = agent.personality
                if p.aggression > 0.7:
                    gov_type = GovernmentType.STRONGMAN
                elif p.conscientiousness > 0.7:
                    gov_type = GovernmentType.COUNCIL
                elif p.openness > 0.7:
                    gov_type = GovernmentType.DEMOCRACY
                else:
                    gov_type = GovernmentType.OLIGARCHY
                name = params.get('name') or params.get('details') or f"{agent.name}'s Government"
                gov = gm.agent_forms_government(founder_id=agent.id, name=name[:60], gov_type=gov_type)
                gov.last_election_tick = tick
                agent.emotions.trigger_emotion(EmotionType.PRIDE, 0.8)
                agent.needs.satisfy_need(NeedType.STATUS, 0.5)
                self._log(f"🏛️ {agent.name} founded {gov.name}",
                          f"{agent.name} founded {gov.name}, a {gov_type.value}.", tick, [agent.id])
                return ActionResult(success=True, emotional_impact=0.7, message=f"Founded {gov.name}",
                                    metadata={'government_id': gov.id, 'type': gov_type.value, 'founded': True})

            election = gm.open_election(gov.id)
            if election and agent.id not in election.candidates:
                gm.agent_runs_for_office(agent.id, election.id)
                agent.needs.satisfy_need(NeedType.STATUS, 0.2)
                return ActionResult(success=True, emotional_impact=0.2,
                                    message=f"Running for {election.position} of {gov.name}",
                                    metadata={'government_id': gov.id, 'candidate': True})

            # A leader collects the taxes the government's laws levy
            collected = self._collect_taxes(agent, gov, tick) if agent.id == gov.leader_id else 0.0
            if collected:
                agent.needs.satisfy_need(NeedType.STATUS, 0.2)
                return ActionResult(success=True, emotional_impact=0.2,
                                    message=f"Collected {collected:.0f} coins in taxes for {gov.name}",
                                    metadata={'government_id': gov.id, 'taxes': collected})

            # Taking part in running things builds standing
            gm.political_power[agent.id] = min(1.0, gm.political_power.get(agent.id, 0.0) + 0.05)
            agent.needs.satisfy_need(NeedType.STATUS, 0.2 if agent.id == gov.leader_id else 0.1)
            role = "Led" if agent.id == gov.leader_id else "Took part in"
            return ActionResult(success=True, emotional_impact=0.2, message=f"{role} {gov.name}",
                                metadata={'government_id': gov.id})

        if action.action_type == ActionType.MAKE_LAW:
            gov = gm.get_agent_government(agent.id)
            if self._wants_tax(agent, gov, params):
                return self._propose_tax(agent, gov, tick)
            banned = self._proposed_ban(agent, params)
            name = params.get('law_name') or f"No {banned.replace('_', ' ')}"
            description = params.get('description') or params.get('details') or f"Nobody may {banned.replace('_', ' ')}."
            law = gm.agent_creates_law(creator_id=agent.id, government_id=gov.id, name=name[:60],
                                       description=description[:200], prohibition=banned,
                                       requirement=params.get('requirement'))
            if not law:
                return ActionResult(success=False, emotional_impact=-0.2, message="No authority to make laws here")
            agent.emotions.trigger_emotion(EmotionType.PRIDE, 0.5)
            agent.needs.satisfy_need(NeedType.STATUS, 0.3)
            self._log(f"📜 {agent.name} proposed: {law.name}", f"In {gov.name}: {law.description}", tick, [agent.id])
            return ActionResult(success=True, emotional_impact=0.4, message=f"Proposed law: {law.name}",
                                metadata={'law_id': law.id, 'law_name': law.name, 'prohibition': banned})

        if action.action_type == ActionType.VOTE:
            target = params.get('vote_target')
            if target and target in gm.laws:
                kind, item = 'law', gm.laws[target]
            elif target and target in gm.elections:
                kind, item = 'election', gm.elections[target]
            else:
                found = self._vote_target(agent)
                if found is None:
                    return ActionResult(success=False, emotional_impact=0.0, message="Nothing to vote on")
                kind, item = found

            if kind == 'law':
                choice = params.get('choice')
                support = (choice == 'yes') if choice in ('yes', 'no') else self._supports(agent, item)
                gm.vote_on_law(agent.id, item.id, support)
                agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
                return ActionResult(success=True, emotional_impact=0.2,
                                    message=f"Voted {'for' if support else 'against'} {item.name}",
                                    metadata={'vote_type': 'law', 'support': support})

            candidate = action.target_agent if action.target_agent in item.candidates else \
                max(item.candidates, key=lambda c: (1.0 if c == agent.id else self._liking(agent.id, c)))
            if not gm.agent_votes(agent.id, item.id, candidate):
                return ActionResult(success=False, emotional_impact=-0.1, message="Cannot vote in this election")
            agent.needs.satisfy_need(NeedType.STATUS, 0.1)
            agent.needs.satisfy_need(NeedType.BELONGING, 0.2)
            return ActionResult(success=True, emotional_impact=0.2, message="Voted in the election",
                                metadata={'vote_type': 'election', 'candidate': candidate})

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown governance action")

    # A tax law takes this share of each citizen's wealth when the leader collects
    TAX_RATE = 0.05

    def _tax_policy(self, gov):
        economy = self.context.get_system('economy')
        for policy in (economy.taxation.tax_policies.values() if economy else []):
            if policy.active and getattr(policy, 'government_id', None) == gov.id:
                return policy
        return None

    def _wants_tax(self, agent, gov, params) -> bool:
        """A tax if the proposal says so; otherwise an ambitious lawmaker whose
        government has no tax yet may propose one."""
        details = (params.get('details') or params.get('description') or '').lower()
        if 'tax' in details:
            return self._tax_policy(gov) is None
        if params:
            return False
        return self._tax_policy(gov) is None and agent.personality.ambition > 0.6

    def _propose_tax(self, agent, gov, tick):
        from economy.taxation import TaxType
        from world.governance import GovernmentType
        economy = self.context.get_system('economy')
        gm = self.context.get_system('governance_manager')
        say = gov.government_type in (GovernmentType.DEMOCRACY, GovernmentType.COUNCIL)
        policy = economy.taxation.enact_tax_policy(TaxType.WEALTH_TAX, self.TAX_RATE, gov.leader_id, say, tick)
        policy.government_id = gov.id
        law = gm.agent_creates_law(creator_id=agent.id, government_id=gov.id, name="Tax",
                                   description=f"Citizens pay {self.TAX_RATE:.0%} of their wealth to {gov.name}.",
                                   requirement='pay_tax')
        if law is None:
            economy.taxation.repeal_tax_policy(policy.id, tick)
            return ActionResult(success=False, emotional_impact=-0.2, message="No authority to make laws here")
        law.tax_policy_id = policy.id
        self._log(f"📜 {agent.name} proposed a tax", law.description, tick, [agent.id])
        return ActionResult(success=True, emotional_impact=0.3, message="Proposed a tax",
                            metadata={'law_id': law.id, 'law_name': law.name, 'tax_policy_id': policy.id})

    def _collect_taxes(self, leader, gov, tick) -> float:
        policy = self._tax_policy(gov)
        if policy is None:
            return 0.0
        economy = self.context.get_system('economy')
        total = 0.0
        for citizen in self.context.world.agents:
            if citizen.alive and citizen.id in gov.citizens and citizen.id != leader.id and citizen.wealth > 0:
                result = economy.taxation.collect_tax(policy.id, citizen.id, citizen.wealth, 0.0, tick)
                paid = min(citizen.wealth, result.get('amount_collected', 0.0)) if result.get('success') else 0.0
                citizen.wealth -= paid
                total += paid
        gov.treasury += total
        return total

    def _supports(self, agent, law) -> bool:
        """Support a law if you like who proposed it and it doesn't ban what you do."""
        memory = getattr(agent, 'action_memory', None)
        banned_habit = bool(law.prohibition and memory and law.prohibition in memory.rate)
        return self._liking(agent.id, law.created_by) - (0.5 if banned_habit else 0.0) \
            + (agent.personality.agreeableness - 0.5) * 0.4 >= 0.0

    def _proposed_ban(self, agent, params) -> str:
        """What a proposed law would ban: what the proposal names, else what
        bothers the agent most."""
        return params.get('prohibition') or self._ban_from_details(params.get('details', '')) \
            or self._grievance(agent)

    @staticmethod
    def _bans_in_force(gm, gov) -> set:
        return {gm.laws[l].prohibition for l in gov.laws if l in gm.laws and gm.laws[l].active}

    # Words that name each thing a law can ban ("no gambling" bans gamble)
    BAN_WORDS = {"fight": ("fight", "violence", "brawl"), "gamble": ("gambl", "betting"),
                 "trade": ("trade", "trading", "barter"), "claim_territory": ("claim", "territor", "land grab")}

    @classmethod
    def _ban_from_details(cls, details: str):
        lowered = (details or '').lower()
        return next((b for b in BANNABLE if any(w in lowered for w in cls.BAN_WORDS.get(b, (b,)))), None)

    def _grievance(self, agent) -> str:
        """The thing others have done to this agent most (fights by default)."""
        warfare = self.context.get_system('warfare_manager')
        attacked = 0
        if warfare is not None:
            attacked = len(warfare.get_agent_conflicts(agent.id))
        return 'fight' if attacked or agent.personality.agreeableness >= 0.5 else 'gamble'

    def _log(self, title, description, tick, agent_ids):
        from engine.events import EventCategory, EventImportance
        event_logger = self.context.event_logger
        if event_logger:
            event_logger.log_event(EventCategory.POLITICAL, EventImportance.MAJOR, title, description,
                                   tick, agent_ids)

    def get_required_systems(self) -> list[str]:
        return ['governance_manager', 'relationship_manager']
