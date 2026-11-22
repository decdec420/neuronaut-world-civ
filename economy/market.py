"""
Economic System - Trade, currency, markets, and wealth

Handles:
- Trade between agents
- Currency and value
- Market dynamics
- Property ownership
- Businesses
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class CurrencyType(Enum):
    """Types of currency - evolves naturally through gameplay"""
    BARTER = "barter"  # Direct item exchange (Phase 1: Early survival)
    COMMODITY = "commodity"  # Most-traded resource becomes currency (Phase 2: Specialization)
    COINS = "coins"  # Abstract minted currency (Phase 3: Advanced economy)
    REPUTATION = "reputation"  # Social credit (supplementary system)


@dataclass
class TradeOffer:
    """An offer to trade"""
    id: str
    from_agent: str
    to_agent: str
    offering_items: Dict[str, int]  # item -> quantity
    offering_wealth: float
    requesting_items: Dict[str, int]
    requesting_wealth: float
    status: str = "pending"  # pending, accepted, rejected, expired
    created_at: datetime = field(default_factory=datetime.now)

    def is_fair(self, item_values: Dict[str, float]) -> bool:
        """Check if trade is approximately fair"""
        offer_value = self.offering_wealth
        request_value = self.requesting_wealth

        for item, qty in self.offering_items.items():
            offer_value += item_values.get(item, 1.0) * qty

        for item, qty in self.requesting_items.items():
            request_value += item_values.get(item, 1.0) * qty

        # Fair if within 20%
        ratio = offer_value / request_value if request_value > 0 else 0
        return 0.8 <= ratio <= 1.2


@dataclass
class Transaction:
    """Completed transaction record"""
    id: str
    timestamp: datetime
    buyer: str
    seller: str
    item: str
    quantity: int
    price: float
    currency: CurrencyType


class Market:
    """Marketplace for trade"""

    def __init__(self):
        self.active_offers: Dict[str, TradeOffer] = {}
        self.transaction_history: List[Transaction] = []

        # Market prices (emergent from transactions)
        self.item_prices: Dict[str, float] = {
            'food': 1.0,
            'water': 0.5,
            'wood': 2.0,
            'stone': 3.0,
            'metal': 5.0,
        }

        # Currency system - evolves naturally!
        self.current_currency_type: CurrencyType = CurrencyType.BARTER  # Starts with pure barter
        self.commodity_currency: Optional[str] = None  # Which item is commodity currency (if any)
        self.currency_adoption_tick: int = 0  # When current currency was adopted

    def create_offer(
        self,
        from_agent: str,
        to_agent: str,
        offering_items: Dict[str, int] = None,
        offering_wealth: float = 0.0,
        requesting_items: Dict[str, int] = None,
        requesting_wealth: float = 0.0
    ) -> TradeOffer:
        """Create a trade offer"""
        offer_id = str(uuid.uuid4())
        offer = TradeOffer(
            id=offer_id,
            from_agent=from_agent,
            to_agent=to_agent,
            offering_items=offering_items or {},
            offering_wealth=offering_wealth,
            requesting_items=requesting_items or {},
            requesting_wealth=requesting_wealth
        )

        self.active_offers[offer_id] = offer
        return offer

    def accept_offer(self, offer_id: str) -> Tuple[bool, str]:
        """Accept a trade offer"""
        if offer_id not in self.active_offers:
            return False, "Offer not found"

        offer = self.active_offers[offer_id]
        offer.status = "accepted"

        # Record transactions for each item
        for item, qty in offer.offering_items.items():
            price = self.item_prices.get(item, 1.0) * qty
            transaction = Transaction(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                buyer=offer.to_agent,
                seller=offer.from_agent,
                item=item,
                quantity=qty,
                price=price,
                currency=CurrencyType.COINS
            )
            self.transaction_history.append(transaction)
            if len(self.transaction_history) > 1200:
                del self.transaction_history[:-1000]  # prices read the last 500

        # Update market prices based on trade
        self._update_prices_from_trade(offer)

        # Remove from active offers
        del self.active_offers[offer_id]

        return True, "Trade completed"

    def reject_offer(self, offer_id: str):
        """Reject a trade offer"""
        if offer_id in self.active_offers:
            self.active_offers[offer_id].status = "rejected"
            del self.active_offers[offer_id]

    def _update_prices_from_trade(self, offer: TradeOffer):
        """Update market prices based on completed trade"""
        # Simple supply/demand: trades increase price slightly
        for item in offer.offering_items:
            if item in self.item_prices:
                self.item_prices[item] *= 1.01  # 1% increase

        for item in offer.requesting_items:
            if item in self.item_prices:
                self.item_prices[item] *= 1.02  # 2% increase (demand)

    def get_market_price(self, item: str) -> float:
        """Get current market price for item"""
        return self.item_prices.get(item, 1.0)

    def get_recent_transactions(
        self,
        item: Optional[str] = None,
        count: int = 100
    ) -> List[Transaction]:
        """Get recent transactions"""
        if item:
            filtered = [t for t in self.transaction_history if t.item == item]
            return filtered[-count:]
        return self.transaction_history[-count:]

    def detect_currency_evolution(self, current_tick: int) -> Optional[str]:
        """
        Detect if currency should evolve to next phase.
        Returns event message if currency evolved, None otherwise.
        """
        # Need sufficient trade history to detect patterns
        if len(self.transaction_history) < 50:
            return None

        # Phase 1 → Phase 2: Detect commodity currency emergence
        if self.current_currency_type == CurrencyType.BARTER:
            commodity = self._detect_commodity_currency()
            if commodity:
                self.current_currency_type = CurrencyType.COMMODITY
                self.commodity_currency = commodity
                self.currency_adoption_tick = current_tick
                return f"💰 Economic milestone! '{commodity.upper()}' has emerged as the standard currency! Agents are now pricing items in {commodity} units."

        # Phase 2 → Phase 3: Detect when abstract coins should be adopted
        elif self.current_currency_type == CurrencyType.COMMODITY:
            if self._should_adopt_coins():
                self.current_currency_type = CurrencyType.COINS
                self.currency_adoption_tick = current_tick
                return f"🪙 Economic revolution! Abstract COINS have been adopted! The economy has matured from commodity-based to true currency."

        return None

    def _detect_commodity_currency(self) -> Optional[str]:
        """
        Analyze transactions to detect if one item has become de facto currency.
        Returns item name if detected, None otherwise.
        """
        recent_trades = self.transaction_history[-500:]  # Last 500 trades
        if len(recent_trades) < 100:
            return None

        # Count how often each item appears in trades
        item_frequency = {}
        for transaction in recent_trades:
            item = transaction.item
            item_frequency[item] = item_frequency.get(item, 0) + 1

        # If one item dominates 30%+ of trades, it's becoming commodity currency
        total_trades = len(recent_trades)
        for item, freq in item_frequency.items():
            if freq / total_trades >= 0.30:
                return item

        return None

    def _should_adopt_coins(self) -> bool:
        """
        Determine if economy is ready for abstract currency (coins).
        Requires: high trade volume, minting discovered, and time since commodity adoption.
        """
        # Need lots of trades (mature economy)
        if len(self.transaction_history) < 1000:
            return False

        # Need time to pass since commodity currency (at least 500 ticks)
        ticks_since_commodity = 0  # This would come from simulation
        # For now, just check trade volume and assume coins have been discovered
        # The actual trigger is when an agent discovers "mint_coins" recipe

        return False  # Will be triggered by minting discovery instead

    def get_market_statistics(self) -> Dict:
        """Get market statistics"""
        total_volume = sum(t.price for t in self.transaction_history)
        total_transactions = len(self.transaction_history)

        return {
            'total_volume': total_volume,
            'total_transactions': total_transactions,
            'item_prices': self.item_prices.copy(),
            'active_offers': len(self.active_offers),
            'current_currency': self.current_currency_type.value,
            'commodity_currency': self.commodity_currency,
        }


@dataclass
class Property:
    """Ownable property (land, buildings)"""
    id: str
    property_type: str  # land, building, resource
    owner_id: Optional[str] = None
    location: Tuple[int, int] = (0, 0)
    value: float = 100.0
    income_per_tick: float = 0.0


class PropertyManager:
    """Manages property ownership"""

    def __init__(self):
        self.properties: Dict[str, Property] = {}
        self.owner_properties: Dict[str, Set[str]] = {}

    def create_property(
        self,
        property_type: str,
        location: Tuple[int, int],
        value: float = 100.0
    ) -> Property:
        """Create new property"""
        prop_id = str(uuid.uuid4())
        prop = Property(
            id=prop_id,
            property_type=property_type,
            location=location,
            value=value
        )
        self.properties[prop_id] = prop
        return prop

    def transfer_ownership(
        self,
        property_id: str,
        new_owner_id: str,
        price: float = 0.0
    ) -> bool:
        """Transfer property to new owner"""
        if property_id not in self.properties:
            return False

        prop = self.properties[property_id]
        old_owner = prop.owner_id

        # Remove from old owner
        if old_owner and old_owner in self.owner_properties:
            self.owner_properties[old_owner].discard(property_id)

        # Add to new owner
        prop.owner_id = new_owner_id
        if new_owner_id not in self.owner_properties:
            self.owner_properties[new_owner_id] = set()
        self.owner_properties[new_owner_id].add(property_id)

        # Update value based on sale price
        if price > 0:
            prop.value = price

        return True

    def get_agent_properties(self, agent_id: str) -> List[Property]:
        """Get all properties owned by agent"""
        prop_ids = self.owner_properties.get(agent_id, set())
        return [self.properties[pid] for pid in prop_ids
                if pid in self.properties]

    def get_agent_net_worth(self, agent_id: str, agent_wealth: float) -> float:
        """Calculate agent's total net worth"""
        properties = self.get_agent_properties(agent_id)
        property_value = sum(p.value for p in properties)
        return agent_wealth + property_value


class Economy:
    """Complete economic system"""

    def __init__(self):
        self.market = Market()
        self.property_manager = PropertyManager()

        # Economic statistics
        self.total_wealth = 0.0
        self.wealth_distribution: Dict[str, float] = {}

    def execute_trade(
        self,
        buyer_agent,
        seller_agent,
        item: str,
        quantity: int,
        price: float
    ) -> Tuple[bool, str]:
        """Execute a trade between agents"""
        # Check if buyer has money
        if buyer_agent.wealth < price:
            return False, "Insufficient funds"

        # Check if seller has item
        if not seller_agent.inventory.has_item(item, quantity):
            return False, "Seller doesn't have item"

        # Execute trade
        buyer_agent.wealth -= price
        seller_agent.wealth += price

        seller_agent.inventory.remove_item(item, quantity)
        success = buyer_agent.inventory.add_item(item, quantity)

        if not success:
            # Rollback if buyer inventory full
            buyer_agent.wealth += price
            seller_agent.wealth -= price
            seller_agent.inventory.add_item(item, quantity)
            return False, "Buyer inventory full"

        # Record transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            buyer=buyer_agent.id,
            seller=seller_agent.id,
            item=item,
            quantity=quantity,
            price=price,
            currency=CurrencyType.COINS
        )
        self.market.transaction_history.append(transaction)

        # Update market prices
        self.market.item_prices[item] = \
            (self.market.item_prices.get(item, 1.0) * 0.9 + price / quantity * 0.1)

        return True, "Trade successful"

    def calculate_item_value(self, item: str, quantity: int) -> float:
        """Calculate value of items"""
        return self.market.get_market_price(item) * quantity

    def update_wealth_distribution(self, agents: List):
        """Update wealth distribution statistics"""
        self.wealth_distribution = {}
        self.total_wealth = 0.0

        for agent in agents:
            if agent.alive:
                net_worth = self.property_manager.get_agent_net_worth(
                    agent.id,
                    agent.wealth
                )
                self.wealth_distribution[agent.id] = net_worth
                self.total_wealth += net_worth

    def get_wealth_statistics(self) -> Dict:
        """Get economic statistics"""
        if not self.wealth_distribution:
            return {
                'total_wealth': 0.0,
                'mean_wealth': 0.0,
                'median_wealth': 0.0,
                'gini_coefficient': 0.0,
            }

        wealths = sorted(self.wealth_distribution.values())
        n = len(wealths)

        mean_wealth = sum(wealths) / n if n > 0 else 0.0
        median_wealth = wealths[n // 2] if n > 0 else 0.0

        # Calculate Gini coefficient (wealth inequality)
        gini = 0.0
        if n > 0 and sum(wealths) > 0:
            cumsum = 0
            for i, w in enumerate(wealths):
                cumsum += w
                gini += (2 * (i + 1) - n - 1) * w
            gini = gini / (n * sum(wealths))

        return {
            'total_wealth': self.total_wealth,
            'mean_wealth': mean_wealth,
            'median_wealth': median_wealth,
            'gini_coefficient': gini,
            'richest': max(wealths) if wealths else 0.0,
            'poorest': min(wealths) if wealths else 0.0,
        }
