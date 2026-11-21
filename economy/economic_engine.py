"""
Unified Economic Engine - Complete Financial System

Integrates:
- Minting & Coinage
- Banking & Credit
- Taxation & Revenue
- Trade Routes & Commerce
- Economic Crises & Cycles
- Original Market System

This is the central controller for the entire economy.
"""

from typing import Dict, List, Optional
from economy.minting import MintingManager, CoinType, MintQuality
from economy.banking import BankingManager, LoanType, CreditRating
from economy.taxation import TaxationManager, TaxType, ResistanceLevel
from economy.trade_routes import TradeRoutesManager
from economy.crises import EconomicCrisesManager, CrisisType, EconomicPhase
from economy.market import Economy as BaseEconomy, CurrencyType


class EconomicEngine:
    """
    Complete economic system integrating all financial subsystems.

    Manages the entire economic lifecycle from ore → coins → banking → trade → crises.
    """

    def __init__(self):
        # Core systems
        self.base_economy = BaseEconomy()  # Original market system
        self.minting = MintingManager()
        self.banking = BankingManager()
        self.taxation = TaxationManager()
        self.trade_routes = TradeRoutesManager()
        self.crises = EconomicCrisesManager()

        # Unified statistics
        self.total_gdp: float = 0.0  # Gross Domestic Product
        self.gdp_growth_rate: float = 0.0
        self.total_transactions_this_tick: int = 0

    # ===== TICK UPDATE =====

    def tick_update(self, current_tick: int, agents: List):
        """Update all economic systems each tick"""

        # 1. Update trade caravans
        caravan_events = self.trade_routes.update_caravans(current_tick)

        # 2. Update asset bubbles
        bubble_events = self.crises.update_bubbles(current_tick)

        # 3. Update active crises
        crisis_events = self.crises.update_crises(current_tick)

        # 4. Check for loan defaults
        defaulted_loans = self.banking.check_for_defaults(current_tick)

        # 5. Apply interest to savings accounts
        if current_tick % 10 == 0:  # Every 10 ticks
            self.banking.apply_interest_to_savings(current_tick)

        # 6. Update inflation
        money_supply_change = self._calculate_money_supply_change()
        goods_production_change = self._estimate_production_change(agents)
        self.crises.update_inflation(money_supply_change, goods_production_change)

        # 7. Update wealth distribution
        self.base_economy.update_wealth_distribution(agents)

        # 8. Calculate GDP
        self._calculate_gdp(agents)

        # Return all events
        return {
            'caravan_events': caravan_events,
            'bubble_events': bubble_events,
            'crisis_events': crisis_events,
            'defaulted_loans': defaulted_loans
        }

    def _calculate_money_supply_change(self) -> float:
        """Calculate change in money supply"""

        # Money supply = coins + bank credit
        stats = self.minting.get_statistics()
        bank_stats = self.banking.get_statistics()

        coins_minted_change = stats.get('total_coins_minted', 0) * 0.01  # 1% growth
        credit_change = bank_stats.get('outstanding_debt', 0) * 0.01

        return (coins_minted_change + credit_change) / 10000  # Normalize

    def _estimate_production_change(self, agents: List) -> float:
        """Estimate change in goods production"""

        # Simplified: count agent actions that produce goods
        # More complex: track actual production from agriculture, crafting, etc.

        active_producers = sum(1 for a in agents if a.alive and hasattr(a, 'inventory'))
        return active_producers * 0.001  # Very simplified

    def _calculate_gdp(self, agents: List):
        """Calculate Gross Domestic Product"""

        # GDP = sum of all production + trade value
        market_stats = self.base_economy.market.get_market_statistics()
        trade_stats = self.trade_routes.get_statistics()

        production_value = sum(a.wealth for a in agents if a.alive) / 10
        trade_value = trade_stats.get('total_trade_volume', 0)
        market_value = market_stats.get('total_volume', 0)

        new_gdp = production_value + trade_value + market_value

        # Calculate growth rate
        if self.total_gdp > 0:
            self.gdp_growth_rate = (new_gdp - self.total_gdp) / self.total_gdp

        self.total_gdp = new_gdp

        # Update economic phase based on growth
        self.crises.update_economic_phase(self.gdp_growth_rate)

    # ===== CURRENCY EVOLUTION =====

    def check_currency_evolution(self, current_tick: int) -> Optional[str]:
        """Check if currency should evolve (barter → commodity → coins)"""

        # Check if coins have been discovered
        if CoinType.COPPER_PENNY in self.minting.discovered_coins:
            # Coins exist - check if economy should adopt them
            if self.base_economy.market.current_currency_type.value == 'barter':
                # Upgrade from barter to coins!
                self.base_economy.market.current_currency_type = CurrencyType.COINS
                self.base_economy.market.currency_adoption_tick = current_tick
                return "🪙 Economic revolution! COINS have been adopted as standard currency!"

        # Check for commodity currency emergence (original system)
        return self.base_economy.market.detect_currency_evolution(current_tick)

    # ===== UNIFIED STATISTICS =====

    def get_complete_statistics(self) -> Dict:
        """Get comprehensive economic statistics"""

        return {
            # Macroeconomic
            'gdp': round(self.total_gdp, 2),
            'gdp_growth_rate': round(self.gdp_growth_rate * 100, 2),
            'economic_phase': self.crises.economic_phase.value,
            'inflation_rate': round(self.crises.inflation_rate * 100, 2),

            # Markets
            'market': self.base_economy.market.get_market_statistics(),

            # Monetary
            'minting': self.minting.get_statistics(),
            'currency_type': self.base_economy.market.current_currency_type.value,

            # Banking
            'banking': self.banking.get_statistics(),

            # Taxation
            'taxation': self.taxation.get_statistics(),

            # Trade
            'trade': self.trade_routes.get_statistics(),

            # Crises
            'crises': self.crises.get_statistics(),

            # Wealth
            'wealth': self.base_economy.get_wealth_statistics()
        }

    # ===== AGENT ECONOMIC INFO =====

    def get_agent_economic_info(self, agent_id: str, agent_wealth: float, agent_income: float = 0.0) -> Dict:
        """Get complete economic info for an agent (for AI perception)"""

        # Credit rating
        credit_rating = self.banking.get_credit_rating(agent_id)

        # Active loans
        active_loans = self.banking.get_agent_loans(agent_id)
        total_debt = sum(l.amount_remaining for l in active_loans if l.status.value == 'active')

        # Savings
        savings_accounts = self.banking.get_agent_savings_accounts(agent_id)
        total_savings = sum(a.balance for a in savings_accounts)

        # Tax burden
        tax_burden_info = self.taxation.calculate_tax_burden(agent_wealth, agent_income)

        # Tax resistance
        active_policies = self.taxation.get_active_policies()
        resistance_levels = []
        for policy in active_policies:
            level = self.taxation.get_resistance_level(agent_id, policy)
            resistance_levels.append({
                'policy': policy.tax_type.value,
                'rate': policy.rate,
                'resistance': level.value
            })

        # Economic environment
        in_crisis = self.crises.is_in_crisis()
        market_confidence = self.crises.market_confidence

        return {
            # Personal finances
            'wealth': agent_wealth,
            'savings': round(total_savings, 2),
            'debt': round(total_debt, 2),
            'net_worth': round(agent_wealth + total_savings - total_debt, 2),

            # Credit
            'credit_rating': credit_rating.value,
            'active_loans': len([l for l in active_loans if l.status.value == 'active']),
            'can_borrow': credit_rating not in [CreditRating.VERY_POOR, CreditRating.POOR] or total_debt < agent_wealth,

            # Taxation
            'tax_burden': tax_burden_info,
            'tax_resistance': resistance_levels if resistance_levels else None,

            # Economic environment
            'in_crisis': in_crisis,
            'market_confidence': round(market_confidence * 100, 1),
            'inflation_rate': round(self.crises.inflation_rate * 100, 2),
            'economic_phase': self.crises.economic_phase.value,

            # Currency
            'currency_type': self.base_economy.market.current_currency_type.value,
        }

    # ===== COMPATIBILITY LAYER - Maintains old Economy interface =====

    @property
    def market(self):
        """Direct access to market (for backward compatibility)"""
        return self.base_economy.market

    @property
    def property_manager(self):
        """Direct access to property manager (for backward compatibility)"""
        return self.base_economy.property_manager

    def execute_trade(self, buyer_agent, seller_agent, item: str, quantity: int, price: float):
        """Execute trade (delegates to base economy)"""
        return self.base_economy.execute_trade(buyer_agent, seller_agent, item, quantity, price)

    def calculate_item_value(self, item: str, quantity: int) -> float:
        """Calculate item value (delegates to base economy)"""
        return self.base_economy.calculate_item_value(item, quantity)

    def update_wealth_distribution(self, agents: List):
        """Update wealth distribution (delegates to base economy)"""
        self.base_economy.update_wealth_distribution(agents)

    def get_wealth_statistics(self) -> Dict:
        """Get wealth statistics (delegates to base economy)"""
        return self.base_economy.get_wealth_statistics()
