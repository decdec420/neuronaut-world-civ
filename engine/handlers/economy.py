"""Advanced Economy Action Handler - Handles advanced financial system actions."""

from typing import TYPE_CHECKING
import random
import logging

from engine.action_handlers import (ActionHandler, ActionResult, ActionContext, validate_agent_alive)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)

# Ore taken per minting run (10 g of copper per unit of ore; 10 pennies use 35 g)
MINT_ORE_PER_BATCH = 4
BANK_REACH = 30.0


class AdvancedEconomyHandler(ActionHandler):
    """Minting, banks and loans, tax revolts, caravans.

    Each validate() rejects what can only fail (no ore, no money, no bank
    with money to lend, nothing to revolt against), so agents choose
    something else instead of failing every tick.
    """

    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [
            ActionType.MINT_COINS, ActionType.OPEN_BANK, ActionType.APPLY_FOR_LOAN,
            ActionType.JOIN_TAX_REVOLT, ActionType.SEND_CARAVAN
        ]

    # -- helpers -----------------------------------------------------------------

    @staticmethod
    def _lendable_bank(agent, economy):
        """The nearest bank within reach that has money to lend, or None."""
        best, best_dist = None, BANK_REACH
        for bank in (economy.banking.banks.values() if economy else []):
            dist = ((agent.location.x - bank.location[0]) ** 2 + (agent.location.y - bank.location[1]) ** 2) ** 0.5
            if dist <= best_dist and bank.reserves - bank.deposits * bank.required_reserve_ratio >= 1.0:
                best, best_dist = bank, dist
        return best

    def _taxing_policy(self, agent, economy):
        """An active tax that the agent's own government levies on it."""
        gm = self.context.get_system('governance_manager')
        gov = gm.get_agent_government(agent.id) if gm else None
        if gov is None or economy is None:
            return None
        for policy in economy.taxation.tax_policies.values():
            if policy.active and getattr(policy, 'government_id', None) == gov.id and policy.collector_id != agent.id:
                return policy
        return None

    def _revolt_to_join(self, agent, economy):
        policy = self._taxing_policy(agent, economy)
        for revolt in (economy.taxation.revolts.values() if economy else []):
            if revolt.active and agent.id not in revolt.participants and \
                    (policy is None or revolt.triggering_policy_id == policy.id):
                return revolt
        return None

    def _tax_to_revolt_against(self, agent, economy):
        policy = self._taxing_policy(agent, economy)
        if policy is None:
            return None
        if any(r.active and r.triggering_policy_id == policy.id for r in economy.taxation.revolts.values()):
            return None  # there's already one: join it instead
        return policy

    @staticmethod
    def _mint_ore(agent):
        for ore in ('metal_ore', 'copper_ore'):
            if agent.inventory.has_item(ore, MINT_ORE_PER_BATCH):
                return ore
        return None

    # -- validation ----------------------------------------------------------------

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        if not validate_agent_alive(agent)[0]:
            return validate_agent_alive(agent)
        economy = self.context.get_system('economy')
        if economy is None:
            return False, "Economy system unavailable"

        if action.action_type == ActionType.MINT_COINS:
            # The world's ore is 'metal_ore' (copper-bearing). Minting used to need
            # copper/silver/gold ore items that exist nowhere, so it was impossible.
            if self._mint_ore(agent) is None:
                return False, f"Need {MINT_ORE_PER_BATCH} metal ore to mint coins"
        if action.action_type == ActionType.OPEN_BANK:
            if agent.wealth < 100:
                return False, "Need 100 coins to open a bank"
        if action.action_type == ActionType.SEND_CARAVAN:
            if agent.wealth < 50:
                return False, "Not enough wealth to send caravan"
            if not any(q > 0 for q in agent.inventory.items.values()):
                return False, "No goods to send"
        if action.action_type == ActionType.APPLY_FOR_LOAN:
            if self._lendable_bank(agent, economy) is None:
                return False, "No bank nearby with money to lend"
        if action.action_type == ActionType.JOIN_TAX_REVOLT:
            if self._revolt_to_join(agent, economy) is None and self._tax_to_revolt_against(agent, economy) is None:
                return False, "Not taxed, and no tax revolt to join"
        return True, ""

    # -- actions -----------------------------------------------------------------

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from economy.minting import CoinType, MintQuality
        from economy.banking import LoanType
        from engine.psychology import EmotionType

        economy = self.context.get_system('economy')
        current_tick = self.context.current_tick

        if action.action_type == ActionType.MINT_COINS:
            ore = self._mint_ore(agent)
            mints = economy.minting.get_mints_by_owner(agent.id)
            if mints:
                mint = mints[0]
            else:
                mint = economy.minting.build_mint(agent.id, (agent.location.x, agent.location.y),
                                                  MintQuality.BASIC, current_tick)
                logger.info(f"🏦 {agent.name} established a mint!")
            grams = MINT_ORE_PER_BATCH * 10.0
            result = economy.minting.mint_coins(mint.id, CoinType.COPPER_PENNY, quantity=10,
                                                metal_available={'copper': grams})
            if not result['success']:
                return ActionResult(success=False, emotional_impact=-0.2, message=result.get('reason', 'Minting failed'))
            agent.inventory.remove_item(ore, MINT_ORE_PER_BATCH)
            agent.wealth += result['coins_minted']
            agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
            agent.needs.satisfy_need(NeedType.RESOURCES, 0.2)
            return ActionResult(success=True, emotional_impact=0.5, message=f"Minted {result['coins_minted']} coins",
                                metadata={'coins': result['coins_minted']})

        if action.action_type == ActionType.OPEN_BANK:
            capital = max(100.0, agent.wealth * 0.5)
            bank = economy.banking.found_bank(agent.id, (agent.location.x, agent.location.y), capital, current_tick)
            agent.wealth -= capital
            agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.5)
            agent.needs.satisfy_need(NeedType.STATUS, 0.3)
            return ActionResult(success=True, emotional_impact=0.7, message="Opened a bank", metadata={'bank_id': bank.id})

        if action.action_type == ActionType.APPLY_FOR_LOAN:
            bank = self._lendable_bank(agent, economy)
            available = bank.reserves - bank.deposits * bank.required_reserve_ratio
            # Ask for what the bank could lend (the old request ignored reserves)
            amount = round(min(max(20.0, agent.wealth * 2), available, getattr(bank, 'max_loan_amount', available)), 1)
            result = economy.banking.apply_for_loan(
                bank.id, agent.id, amount, LoanType.PERSONAL,
                term_ticks=100, collateral={'wealth': agent.wealth * 0.5}, current_tick=current_tick)
            if result['approved']:
                agent.wealth += amount
                agent.needs.satisfy_need(NeedType.SECURITY, 0.3)
                return ActionResult(success=True, emotional_impact=0.4, message=f"Loan approved: {amount:.0f} coins",
                                    metadata={'loan_amount': amount})
            return ActionResult(success=False, emotional_impact=-0.3, message=result.get('reason', 'Loan denied'))

        if action.action_type == ActionType.JOIN_TAX_REVOLT:
            revolt = self._revolt_to_join(agent, economy)
            if revolt is not None:
                economy.taxation.join_revolt(revolt.id, agent.id)
                verb = "Joined"
            else:
                policy = self._tax_to_revolt_against(agent, economy)
                revolt = economy.taxation.start_tax_revolt(agent.id, policy.id, "taxes we never agreed to",
                                                           current_tick)
                verb = "Started"
            agent.needs.satisfy_need(NeedType.STATUS, 0.3)
            agent.emotions.trigger_emotion(EmotionType.ANGER, 0.3)
            if self.context.event_logger:
                from engine.events import EventCategory, EventImportance
                self.context.event_logger.log_event(
                    EventCategory.POLITICAL, EventImportance.MODERATE, f"✊ {agent.name}: {verb.lower()} a tax revolt",
                    f"{len(revolt.participants)} now refuse the tax.", current_tick, [agent.id])
            return ActionResult(success=True, emotional_impact=0.3, message=f"{verb} a tax revolt",
                                metadata={'revolt_size': len(revolt.participants), 'started': verb == "Started"})

        if action.action_type == ActionType.SEND_CARAVAN:
            world_map = self.context.world.map
            destination = (random.uniform(0, world_map.width), random.uniform(0, world_map.height))
            cargo = {}
            for item, quantity in sorted(agent.inventory.items.items(), key=lambda kv: -kv[1])[:3]:
                if quantity > 0:
                    cargo[item] = min(quantity, 10)
            value = sum(economy.market.get_market_price(i) * q for i, q in cargo.items())
            # A caravan travels a trade route (the old call skipped the route and
            # the guards argument, and raised TypeError)
            route = economy.trade_routes.establish_trade_route(
                agent.id, (agent.location.x, agent.location.y), destination, current_tick)
            caravan = economy.trade_routes.send_caravan(agent.id, route.id, cargo, value, guards=0,
                                                        current_tick=current_tick)
            if caravan is None:
                return ActionResult(success=False, emotional_impact=-0.1, message="The caravan couldn't set out")
            for item, quantity in cargo.items():
                agent.inventory.remove_item(item, quantity)
            agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
            return ActionResult(success=True, emotional_impact=0.4, message="Sent a trading caravan",
                                metadata={'caravan_id': getattr(caravan, 'id', None)})

        return ActionResult(success=False, emotional_impact=0.0, message="Unknown economy action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'economy']
