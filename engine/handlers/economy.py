"""Advanced Economy Action Handler - Handles advanced financial system actions."""

from typing import TYPE_CHECKING
import random
import logging

from engine.action_handlers import (ActionHandler, ActionResult, ActionContext, validate_agent_alive)
from agents.agent import ActionType, Action, NeedType

if TYPE_CHECKING:
    from agents.agent import Agent

logger = logging.getLogger(__name__)

class AdvancedEconomyHandler(ActionHandler):
    def can_handle(self, action_type: ActionType) -> bool:
        return action_type in [
            ActionType.MINT_COINS, ActionType.OPEN_BANK, ActionType.APPLY_FOR_LOAN,
            ActionType.JOIN_TAX_REVOLT, ActionType.SEND_CARAVAN
        ]

    def validate(self, agent: 'Agent', action: 'Action') -> tuple[bool, str]:
        if not validate_agent_alive(agent)[0]:
            return validate_agent_alive(agent)
        
        if action.action_type == ActionType.MINT_COINS:
            if not (agent.inventory.has_item('copper_ore') or agent.inventory.has_item('silver_ore') or agent.inventory.has_item('gold_ore')):
                return False, "No metal ore to mint coins"
        
        if action.action_type == ActionType.OPEN_BANK:
            initial_capital = max(100, agent.wealth * 0.5)
            if agent.wealth < initial_capital:
                return False, "Not enough wealth to open bank"
        
        if action.action_type == ActionType.SEND_CARAVAN:
            if agent.wealth < 50:
                return False, "Not enough wealth to send caravan"

        # Reject what can only fail, so the agent picks something else
        economy = self.context.get_system('economy')
        if action.action_type == ActionType.APPLY_FOR_LOAN:
            banks = economy.banking.banks.values() if economy else []
            if not any(((agent.location.x - b.location[0]) ** 2 + (agent.location.y - b.location[1]) ** 2) ** 0.5 <= 30.0
                       for b in banks):
                return False, "No bank nearby"
        if action.action_type == ActionType.JOIN_TAX_REVOLT:
            revolts = economy.taxation.revolts.values() if economy else []
            if not any(r.active and agent.id not in r.participants for r in revolts):
                return False, "No tax revolts to join"

        return True, ""

    def execute(self, agent: 'Agent', action: 'Action') -> ActionResult:
        from economy.minting import CoinType, MintQuality
        from economy.banking import LoanType
        from engine.psychology import EmotionType
        
        economy = self.context.get_system('economy')
        if not economy:
            return ActionResult(success=False, emotional_impact=0.0, message="Economy system unavailable")
        
        current_tick = self.context.current_tick
        
        if action.action_type == ActionType.MINT_COINS:
            if agent.inventory.has_item('copper_ore'):
                coin_type, ore_type = CoinType.COPPER_PENNY, 'copper_ore'
            elif agent.inventory.has_item('silver_ore'):
                coin_type, ore_type = CoinType.SILVER_SHILLING, 'silver_ore'
            elif agent.inventory.has_item('gold_ore'):
                coin_type, ore_type = CoinType.GOLD_CROWN, 'gold_ore'
            else:
                return ActionResult(success=False, emotional_impact=-0.1, message="No metal ore to mint coins")
            
            agent_mints = economy.minting.get_mints_by_owner(agent.id)
            if not agent_mints:
                mint = economy.minting.build_mint(agent.id, (agent.location.x, agent.location.y), MintQuality.BASIC, current_tick)
                logger.info(f"🏦 {agent.name} established a mint!")
            else:
                mint = agent_mints[0]
            
            metal_available = {ore_type.replace('_ore', ''): agent.inventory.items.get(ore_type, 0) * 10}
            result = economy.minting.mint_coins(mint.id, coin_type, quantity=10, metal_available=metal_available)
            
            if result['success']:
                agent.inventory.remove_item(ore_type, 1)
                agent.wealth += result['coins_minted']
                logger.info(f"🪙 {agent.name} minted {result['coins_minted']} coins!")
                agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
                return ActionResult(success=True, emotional_impact=0.5, message=f"Minted {result['coins_minted']} coins!", metadata={'coins': result['coins_minted']})
            return ActionResult(success=False, emotional_impact=-0.2, message=result.get('reason', 'Minting failed'))
        
        elif action.action_type == ActionType.OPEN_BANK:
            initial_capital = max(100, agent.wealth * 0.5)
            bank = economy.banking.found_bank(agent.id, (agent.location.x, agent.location.y), initial_capital, current_tick)
            agent.wealth -= initial_capital
            logger.info(f"🏦 {agent.name} opened a bank!")
            agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.5)
            return ActionResult(success=True, emotional_impact=0.7, message="Opened a bank!", metadata={'bank_id': bank.id})
        
        elif action.action_type == ActionType.APPLY_FOR_LOAN:
            nearest_bank_id = None
            min_distance = float('inf')
            for bank_id, bank in economy.banking.banks.items():
                dist = ((agent.location.x - bank.location[0])**2 + (agent.location.y - bank.location[1])**2)**0.5
                if dist < min_distance:
                    min_distance, nearest_bank_id = dist, bank_id
            
            if not nearest_bank_id or min_distance > 30.0:
                return ActionResult(success=False, emotional_impact=-0.2, message="No bank nearby")
            
            loan_amount = min(agent.wealth * 2, 1000)
            result = economy.banking.apply_for_loan(
                nearest_bank_id, agent.id, loan_amount, LoanType.PERSONAL,
                term_ticks=100, collateral={'wealth': agent.wealth * 0.5}, current_tick=current_tick
            )
            
            if result['approved']:
                agent.wealth += loan_amount
                logger.info(f"💰 {agent.name} got a loan of {loan_amount:.0f}")
                agent.needs.satisfy_need(NeedType.SECURITY, 0.3)
                return ActionResult(success=True, emotional_impact=0.4, message=f"Loan approved: {loan_amount:.0f} coins!", metadata={'loan_amount': loan_amount})
            return ActionResult(success=False, emotional_impact=-0.3, message=result.get('reason', 'Loan denied'))
        
        elif action.action_type == ActionType.JOIN_TAX_REVOLT:
            active_revolts = [r for r in economy.taxation.revolts.values() if r.active and agent.id not in r.participants]
            if not active_revolts:
                return ActionResult(success=False, emotional_impact=0.0, message="No tax revolts to join")
            
            revolt = active_revolts[0]
            revolt.participants.add(agent.id)
            logger.info(f"✊ {agent.name} joined tax revolt!")
            agent.needs.satisfy_need(NeedType.STATUS, 0.4)
            agent.emotions.trigger_emotion(EmotionType.ANGER, 0.3)
            return ActionResult(success=True, emotional_impact=0.3, message=f"Joined tax revolt with {len(revolt.participants)} others!", metadata={'revolt_size': len(revolt.participants)})
        
        elif action.action_type == ActionType.SEND_CARAVAN:
            dest_x, dest_y = random.uniform(0, self.context.world.map.width), random.uniform(0, self.context.world.map.height)
            
            cargo = {}
            for item, quantity in list(agent.inventory.items.items())[:3]:
                if quantity > 0:
                    take_qty = min(quantity, 10)
                    cargo[item] = take_qty
                    agent.inventory.remove_item(item, take_qty)
            
            if not cargo:
                return ActionResult(success=False, emotional_impact=-0.1, message="No goods to trade")
            
            caravan_id = economy.trade_routes.send_caravan(
                agent.id, (agent.location.x, agent.location.y), (dest_x, dest_y), cargo, current_tick=current_tick
            )
            
            logger.info(f"🐪 {agent.name} sent trading caravan!")
            agent.needs.satisfy_need(NeedType.ACHIEVEMENT, 0.3)
            return ActionResult(success=True, emotional_impact=0.4, message="Sent trading caravan!", metadata={'caravan_id': caravan_id})
        
        return ActionResult(success=False, emotional_impact=0.0, message="Unknown economy action")

    def get_required_systems(self) -> list[str]:
        return ['world', 'economy']
