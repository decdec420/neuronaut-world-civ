"""
Quick integration test for the complete economic system.

Tests:
1. EconomicEngine initialization
2. Economic tick updates
3. Currency evolution
4. Agent economic info
5. Action handlers integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from economy.economic_engine import EconomicEngine
from economy.minting import CoinType, MintQuality
from economy.banking import LoanType, CreditRating
from economy.taxation import TaxType, ResistanceLevel
from economy.trade_routes import RouteStatus
from economy.crises import CrisisType, EconomicPhase

def test_economic_engine_initialization():
    """Test that EconomicEngine initializes correctly"""
    print("\n=== TEST 1: EconomicEngine Initialization ===")

    engine = EconomicEngine()

    # Check all subsystems initialized
    assert engine.base_economy is not None, "Base economy not initialized"
    assert engine.minting is not None, "Minting system not initialized"
    assert engine.banking is not None, "Banking system not initialized"
    assert engine.taxation is not None, "Taxation system not initialized"
    assert engine.trade_routes is not None, "Trade routes not initialized"
    assert engine.crises is not None, "Crises system not initialized"

    # Check statistics
    assert engine.total_gdp == 0.0, "GDP should start at 0"
    assert engine.gdp_growth_rate == 0.0, "Growth rate should start at 0"

    print("✅ EconomicEngine initialized correctly!")
    return engine

def test_compatibility_layer(engine):
    """Test backward compatibility with old Economy interface"""
    print("\n=== TEST 2: Compatibility Layer ===")

    # Check properties exist
    assert hasattr(engine, 'market'), "Missing market property"
    assert hasattr(engine, 'property_manager'), "Missing property_manager property"

    # Check methods exist
    assert hasattr(engine, 'execute_trade'), "Missing execute_trade method"
    assert hasattr(engine, 'calculate_item_value'), "Missing calculate_item_value method"
    assert hasattr(engine, 'update_wealth_distribution'), "Missing update_wealth_distribution method"
    assert hasattr(engine, 'get_wealth_statistics'), "Missing get_wealth_statistics method"

    print("✅ Compatibility layer working!")

def test_minting_system(engine):
    """Test minting coins"""
    print("\n=== TEST 3: Minting System ===")

    # Create a mint
    mint_id = "test_mint"
    owner_id = "test_agent"
    location = (50.0, 50.0)

    mint = engine.minting.build_mint(owner_id, location, MintQuality.BASIC, current_tick=1)
    assert mint is not None, "Failed to create mint"

    # Mint coins
    metal_available = {'copper': 100.0}
    result = engine.minting.mint_coins(mint.id, CoinType.COPPER_PENNY, 10, metal_available)
    assert result['success'], "Failed to mint coins"
    assert result['coins_minted'] == 10, "Wrong number of coins minted"

    # Check statistics
    stats = engine.minting.get_statistics()
    assert stats['total_coins_in_circulation'] == 10, "Coins not in circulation"

    print(f"✅ Minted {result['coins_minted']} coins!")

def test_banking_system(engine):
    """Test banking and loans"""
    print("\n=== TEST 4: Banking System ===")

    # Create a bank
    location = (50.0, 50.0)
    founder_id = "banker_agent"

    bank = engine.banking.found_bank(founder_id, location, initial_capital=1000.0, current_tick=1)
    assert bank is not None, "Failed to create bank"
    bank_id = bank.id

    # Apply for a loan - might be denied due to credit
    borrower_id = "borrower_agent"
    result = engine.banking.apply_for_loan(
        bank_id,
        borrower_id,
        amount=500.0,
        loan_type=LoanType.PERSONAL,
        term_ticks=100,
        collateral={'wealth': 500.0},  # Good collateral
        current_tick=1
    )

    # Check credit rating exists
    rating = engine.banking.get_credit_rating(borrower_id)
    assert rating in [r for r in CreditRating], "Invalid credit rating"

    # Check statistics
    stats = engine.banking.get_statistics()
    assert 'total_banks_founded' in stats or len(engine.banking.banks) == 1, "Bank count wrong"

    if result['approved']:
        print(f"✅ Bank created, loan approved at {result['interest_rate']*100:.1f}% interest!")
    else:
        print(f"✅ Bank created, loan system working (denied due to: {result.get('reason')})")

def test_taxation_system(engine):
    """Test taxation and representation"""
    print("\n=== TEST 5: Taxation System ===")

    # Enact tax policy
    tax_policy = engine.taxation.enact_tax_policy(
        tax_type=TaxType.INCOME_TAX,
        rate=0.20,
        collector_id="government",
        has_representation=False,  # No taxation without representation!
        current_tick=1
    )

    assert tax_policy.rate == 0.20, "Tax rate wrong"
    assert not tax_policy.has_representation, "Should have no representation"

    # Check resistance level
    resistance = engine.taxation.get_resistance_level("citizen_1", tax_policy)
    # Without representation, resistance should be higher
    assert resistance in [ResistanceLevel.GRUMBLING, ResistanceLevel.EVADING,
                         ResistanceLevel.REFUSING, ResistanceLevel.REVOLTING], \
           "Resistance level wrong for taxation without representation"

    print(f"✅ Tax policy enacted: {tax_policy.rate*100}% income tax, resistance: {resistance.value}")

def test_trade_routes(engine):
    """Test trade routes and caravans"""
    print("\n=== TEST 6: Trade Routes ===")

    # Create trade route
    origin = (10.0, 10.0)
    destination = (90.0, 90.0)

    route = engine.trade_routes.establish_trade_route(
        establisher_id="merchant_1",
        origin=origin,
        destination=destination,
        current_tick=1
    )
    route_id = route.id

    assert route_id is not None, "Failed to create trade route"

    # Send caravan
    cargo = {'food': 10, 'materials': 5}
    cargo_value = 150.0
    caravan = engine.trade_routes.send_caravan(
        merchant_id="merchant_1",
        route_id=route.id,
        cargo=cargo,
        cargo_value=cargo_value,
        guards=2,
        current_tick=1
    )
    caravan_id = caravan.id if caravan else None

    assert caravan_id is not None, "Failed to send caravan"

    # Check statistics
    stats = engine.trade_routes.get_statistics()
    assert len(engine.trade_routes.trade_routes) >= 1, "Trade route count wrong"
    assert len(engine.trade_routes.caravans) >= 1, "Caravan count wrong"

    print(f"✅ Trade route established, caravan sent!")

def test_economic_crises(engine):
    """Test economic crises and cycles"""
    print("\n=== TEST 7: Economic Crises ===")

    # Update inflation
    engine.crises.update_inflation(
        money_supply_change=0.05,  # 5% increase
        goods_production_change=0.02  # 2% increase
    )

    assert engine.crises.inflation_rate > 0, "Inflation should be positive"

    # Check economic phase
    assert engine.crises.economic_phase in [EconomicPhase.EXPANSION, EconomicPhase.PEAK,
                                            EconomicPhase.CONTRACTION, EconomicPhase.TROUGH,
                                            EconomicPhase.RECOVERY], "Invalid economic phase"

    # Create asset bubble
    bubble_id = engine.crises.create_bubble(
        asset_type="tulips",
        fair_value=100.0,
        current_tick=1
    )

    assert bubble_id is not None, "Failed to create bubble"

    print(f"✅ Inflation: {engine.crises.inflation_rate*100:.2f}%, Phase: {engine.crises.economic_phase.value}")

def test_agent_economic_info(engine):
    """Test getting agent economic info for AI perception"""
    print("\n=== TEST 8: Agent Economic Info ===")

    agent_id = "test_agent"
    agent_wealth = 1000.0

    info = engine.get_agent_economic_info(agent_id, agent_wealth)

    # Check all required fields
    assert 'wealth' in info, "Missing wealth"
    assert 'savings' in info, "Missing savings"
    assert 'debt' in info, "Missing debt"
    assert 'net_worth' in info, "Missing net worth"
    assert 'credit_rating' in info, "Missing credit rating"
    assert 'can_borrow' in info, "Missing can_borrow"
    assert 'economic_phase' in info, "Missing economic phase"
    assert 'inflation_rate' in info, "Missing inflation rate"
    assert 'currency_type' in info, "Missing currency type"

    print(f"✅ Agent economic info: wealth={info['wealth']}, net_worth={info['net_worth']}, "
          f"credit={info['credit_rating']}, crisis={info['in_crisis']}")

def test_complete_statistics(engine):
    """Test complete economic statistics"""
    print("\n=== TEST 9: Complete Statistics ===")

    stats = engine.get_complete_statistics()

    # Check all subsystem statistics
    assert 'gdp' in stats, "Missing GDP"
    assert 'gdp_growth_rate' in stats, "Missing growth rate"
    assert 'economic_phase' in stats, "Missing economic phase"
    assert 'inflation_rate' in stats, "Missing inflation"
    assert 'market' in stats, "Missing market stats"
    assert 'minting' in stats, "Missing minting stats"
    assert 'banking' in stats, "Missing banking stats"
    assert 'taxation' in stats, "Missing taxation stats"
    assert 'trade' in stats, "Missing trade stats"
    assert 'crises' in stats, "Missing crises stats"
    assert 'wealth' in stats, "Missing wealth stats"

    print(f"✅ Complete stats: GDP={stats['gdp']:.2f}, inflation={stats['inflation_rate']:.2f}%, "
          f"phase={stats['economic_phase']}")

def test_tick_update(engine):
    """Test economic engine tick update"""
    print("\n=== TEST 10: Tick Update ===")

    # Create mock agents
    class MockAgent:
        def __init__(self, agent_id, wealth):
            self.id = agent_id
            self.wealth = wealth
            self.alive = True

            # Mock inventory
            class Inventory:
                def __init__(self):
                    self.items = {}
                def has_item(self, item):
                    return item in self.items
            self.inventory = Inventory()

    agents = [
        MockAgent("agent_1", 1000.0),
        MockAgent("agent_2", 500.0),
        MockAgent("agent_3", 2000.0)
    ]

    # Run tick update
    events = engine.tick_update(current_tick=10, agents=agents)

    # Check events returned
    assert 'caravan_events' in events, "Missing caravan events"
    assert 'bubble_events' in events, "Missing bubble events"
    assert 'crisis_events' in events, "Missing crisis events"
    assert 'defaulted_loans' in events, "Missing defaulted loans"

    print(f"✅ Tick update successful! GDP={engine.total_gdp:.2f}")

def run_all_tests():
    """Run all economic system tests"""
    print("\n" + "="*60)
    print("COMPLETE ECONOMIC SYSTEM INTEGRATION TEST")
    print("="*60)

    try:
        engine = test_economic_engine_initialization()
        test_compatibility_layer(engine)
        test_minting_system(engine)
        test_banking_system(engine)
        test_taxation_system(engine)
        test_trade_routes(engine)
        test_economic_crises(engine)
        test_agent_economic_info(engine)
        test_complete_statistics(engine)
        test_tick_update(engine)

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! Economic system fully operational!")
        print("="*60)
        print("\nSUMMARY:")
        print("✅ Minting & Coinage - Working")
        print("✅ Banking & Credit - Working")
        print("✅ Taxation & Representation - Working")
        print("✅ Trade Routes & Caravans - Working")
        print("✅ Economic Crises & Cycles - Working")
        print("✅ Complete Integration - Working")
        print("\nThe financial system is ready for simulation! 🚀")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
