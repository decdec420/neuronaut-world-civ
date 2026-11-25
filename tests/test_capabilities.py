"""
End-to-end proofs that the world's capabilities work when agents choose them.

Each test sets up a small village and has agents take actions directly
("A founds a government", "B joins"), to prove the path works. The sim itself
never forces any of this; whether it happens is up to the agents.

    python3 -m pytest tests/test_capabilities.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402


def act(sim, agent, name, target=None, **params):
    """Have an agent validate and execute an action. Returns the ActionResult."""
    from agents.agent import Action, ActionType
    action = Action(ActionType(name), target_agent=target.id if target else None, parameters=params)
    handler = sim._handler_registry.get_handler(action.action_type)
    with quiet():
        ok, reason = handler.validate(agent, action)
        assert ok, f"{name} rejected: {reason}"
        return handler.execute(agent, action)


def court_until_partners(sim, a, b, visits=12):
    """A and B court each other in turn, in person, a visit every
    BOND_SPACING ticks, until they're partners. Returns how many visits it
    took (each deepens the bond: life/family.py PARTNER_BOND)."""
    from social.relationships import BOND_SPACING
    for n in range(1, visits + 1):
        if act(sim, a if n % 2 else b, "seek_romance", target=b if n % 2 else a).metadata.get("partnership_formed"):
            return n
        sim.world.time.current_tick += BOND_SPACING
    raise AssertionError(f"not partners after {visits} visits")


def befriend(sim, a, b, strength=0.9):
    from social.relationships import RelationshipType
    with quiet():
        rel = sim.relationship_manager.get_relationship(a.id, b.id)
        if rel is None:
            rel = sim.relationship_manager.create_relationship(a.id, b.id, RelationshipType.FRIENDSHIP, strength)
        rel.strength = strength


def test_governance_found_join_law_vote_elect_enforce_repeal():
    from world.governance import GovernmentType
    sim, roles = make_world()
    a, b, c = roles["actor"], roles["neighbour"], roles["sick"]
    gm = sim.governance_manager
    a.personality.openness, a.personality.conscientiousness, a.personality.aggression = 0.9, 0.5, 0.1

    # A founds a democracy; B, who likes A, joins it rather than founding another
    assert act(sim, a, "govern").metadata.get("founded")
    gov = gm.get_agent_government(a.id)
    assert gov.government_type == GovernmentType.DEMOCRACY and gov.leader_id == a.id
    befriend(sim, b, a)
    assert act(sim, b, "govern").metadata.get("joined")
    assert b.id in gov.citizens and len(gm.governments) == 1

    # A proposes a law; B votes on it (a real target, found by the handler)
    law_result = act(sim, a, "make_law", details="no fighting in the village")
    law = gm.laws[law_result.metadata["law_id"]]
    assert law.prohibition == "fight" and law.active
    assert act(sim, b, "vote").metadata["vote_type"] == "law"
    assert b.id in law.supporters | law.opposers

    # The democracy holds an election; B stands, A votes, the count makes a leader
    gm.update_governments(current_tick=gm.ELECTION_EVERY + 1)
    election = gm.open_election(gov.id)
    assert election is not None
    assert act(sim, b, "govern").metadata.get("candidate")
    assert act(sim, a, "vote").metadata["vote_type"] == "election"
    gm.update_governments(current_tick=election.ends_tick)
    assert election.complete and gov.leader_id == election.winner

    # B fights within sight of A: the law is broken and noticed
    sim._agent_updater._observe_laws(b, "fight", current_tick=1)
    assert law.times_broken == 1 and law.times_enforced == 1

    # C joins; with B and C against it, the law is repealed
    befriend(sim, c, a)
    act(sim, c, "govern")
    gm.vote_on_law(b.id, law.id, False)
    gm.vote_on_law(c.id, law.id, False)
    gm.update_governments(current_tick=election.ends_tick + 1)
    assert not law.active


def test_a_ban_already_in_force_is_not_proposed_again():
    from agents.agent import Action, ActionType
    sim, roles = make_world()
    a = roles["actor"]
    a.personality.aggression, a.personality.ambition = 0.1, 0.1
    act(sim, a, "govern")
    act(sim, a, "make_law", details="no fighting")
    handler = sim._handler_registry.get_handler(ActionType.MAKE_LAW)
    ok, why = handler.validate(a, Action(ActionType.MAKE_LAW, parameters={"details": "no fighting ever"}))
    assert not ok and why == "No fight is already the law"
    assert act(sim, a, "make_law", details="no gambling").metadata["prohibition"] == "gamble"


def test_nothing_to_vote_on_is_rejected_up_front():
    from agents.agent import Action, ActionType
    sim, roles = make_world()
    handler = sim._handler_registry.get_handler(ActionType.VOTE)
    ok, reason = handler.validate(roles["actor"], Action(ActionType.VOTE))
    assert not ok and reason == "Nothing to vote on"


def test_religion_found_join_ritual_temple_convert_lapse():
    sim, roles = make_world()
    a, b, d = roles["actor"], roles["neighbour"], roles["partner"]
    rel = sim.religion

    # Nobody A cares about has a faith, so worshipping founds one
    founded = act(sim, a, "worship")
    assert founded.metadata.get("founded")
    faith = rel.get_agent_religion(a.id)

    # B likes A, so B's worship joins A's faith instead of founding another
    befriend(sim, b, a)
    assert act(sim, b, "worship").metadata.get("joined")
    assert b.id in faith.followers and len(rel.religions) == 1

    # A leads a ritual (B is nearby and takes part) and builds a temple
    assert act(sim, a, "perform_ritual").metadata["participants"] >= 2
    assert act(sim, a, "build_temple").success

    # D, who cares for nobody in A's faith, founds a second one; B comes to
    # like D far more than A and converts
    befriend(sim, d, a, 0.0)
    befriend(sim, d, b, 0.0)
    assert act(sim, d, "worship").metadata.get("founded")
    befriend(sim, b, a, 0.1)
    befriend(sim, b, d, 0.95)
    assert act(sim, b, "worship").metadata.get("joined")
    assert b.id not in faith.followers and b.id in rel.get_agent_religion(d.id).followers

    # A faith nobody practises fades: A lapses after LAPSE_TICKS without practice
    rel.record_practice(a.id, 0)
    lapsed = rel.lapse_inactive_followers(rel.LAPSE_TICKS)
    assert a.id in lapsed and rel.get_agent_religion(a.id) is None


def test_a_faith_left_unpractised_is_felt_and_seen():
    """Holding a faith weighs on the agent more as it fades (the rule brain),
    and the agent is told when it last practised and that faiths lapse (the
    AI brain's prompt)."""
    from agents.utility_brain import UtilityBrain, FAITH_PULL
    sim, roles = make_world()
    believer, other = roles["actor"], roles["neighbour"]
    brain = UtilityBrain(sim, ["pray", "worship"])
    assert brain._faith_pull(believer) == 0.0               # no faith, nothing to fade
    assert act(sim, believer, "worship").metadata.get("founded")
    assert brain._faith_pull(believer) == 0.0               # just practised
    sim.world.time.current_tick += sim.religion.LAPSE_TICKS // 2
    assert abs(brain._faith_pull(believer) - FAITH_PULL / 2) < 1e-9
    assert brain._faith_pull(other) == 0.0
    told = sim._perception_builder._add_social_info(believer, {})["community"]["religions"]
    assert any("you are one" in r and "hours ago" in r and "lapses" in r for r in told)
    assert not any("you are one" in r for r in sim._perception_builder._add_social_info(other, {})["community"]["religions"])
    act(sim, believer, "pray")
    assert brain._faith_pull(believer) == 0.0


def test_a_faith_can_be_shared_and_the_listener_decides():
    """convert: a believer tells someone about its faith; whether they take
    it up comes from the listener (engine/handlers/religion.py)."""
    import random
    from agents.agent import Action, ActionType, NeedType
    sim, roles = make_world()
    believer, friend, rival = roles["actor"], roles["neighbour"], roles["partner"]
    convert = sim._handler_registry.get_handler(ActionType.CONVERT)
    assert not convert.validate(believer, Action(ActionType.CONVERT, target_agent=friend.id))[0]   # no faith yet
    faith = sim.religion.religions[act(sim, believer, "worship").metadata["religion_id"]]
    rm, tick = sim.relationship_manager, sim.world.time.current_tick

    # a friend who is open and looking for meaning: likely to take it up
    for _ in range(10):
        rm.update_relationship(friend.id, believer.id, 'socialize', True)
    friend.personality.openness = 0.9
    friend.needs.needs[NeedType.MEANING].level = 0.9
    likely = convert._listener_takes_it_up(friend, believer, tick)
    friend.personality.openness = 0.1
    friend.needs.needs[NeedType.MEANING].level = 0.1
    assert convert._listener_takes_it_up(friend, believer, tick) < likely
    friend.personality.openness, friend.needs.needs[NeedType.MEANING].level = 0.9, 0.9

    # a rival never does
    from social.relationships import RelationshipType
    rel = rm.get_relationship(rival.id, believer.id) or rm.create_relationship(rival.id, believer.id,
                                                                               RelationshipType.RIVALRY)
    rel.relationship_type, rel.strength = RelationshipType.RIVALRY, 0.8
    assert convert._listener_takes_it_up(rival, believer, tick) == 0.0

    random.seed(3)
    for _ in range(40):
        result = act(sim, believer, "convert", target=friend)
        if result.metadata["converted"]:
            break
    assert result.metadata["converted"] and friend.id in faith.followers
    assert any("joined" in e.title for e in sim.event_logger.events)
    # now they share it: nothing more to tell them
    assert not convert.validate(believer, Action(ActionType.CONVERT, target_agent=friend.id))[0]

    # someone whose own faith is fresh is held by it
    other = sim.religion.religions[act(sim, rival, "worship").metadata["religion_id"]]
    assert other is not faith
    rel.relationship_type, rel.strength = RelationshipType.FRIENDSHIP, 0.8
    assert convert._listener_takes_it_up(rival, believer, sim.world.time.current_tick) == 0.0


def test_inventions_are_recorded_once_and_spread_by_teaching():
    sim, roles = make_world()
    a, b = roles["actor"], roles["neighbour"]
    innovations = sim.innovation_manager
    updater = sim._agent_updater

    # A succeeds at an experiment; whatever it made is A's invention
    for _ in range(200):
        result = act(sim, a, "experiment")
        updater._record_invention(a, "experiment", result.to_dict(), current_tick=1)
        if result.success:
            break
    assert result.success and len(innovations.innovations) == 1
    invention = next(iter(innovations.innovations.values()))
    assert invention.discoverer_id == a.id
    assert invention.name == result.metadata["discovered_material"].replace("_", " ")
    assert innovations.experiment_log

    # Making the same thing again is not a new invention
    updater._record_invention(b, "experiment", {"success": True, "discovered_material": invention.name.replace(" ", "_")}, 2)
    assert len(innovations.innovations) == 1 and innovations.agent_knows(b.id, invention.id)

    # Teaching passes an invention on
    c = roles["partner"]
    assert not innovations.agent_knows(c.id, invention.id)
    for _ in range(50):
        if act(sim, a, "teach", target=c).success:
            break
    assert innovations.agent_knows(c.id, invention.id)


def test_each_world_lights_its_own_first_fire():
    """Milestones belong to one world: lighting the first fire in one doesn't
    light it in the next world made in the same process (the server's reset
    did, and so did one test for the ones after it)."""
    from world.civilization_progression import CivilizationProgressionEngine
    first = CivilizationProgressionEngine()
    assert first.check_discovery("fire", "a1", "Ada") is not None
    second = CivilizationProgressionEngine()
    assert not second.milestones["first_fire"].is_achieved
    assert second.check_discovery("fire", "b1", "Bo") is not None


def test_economy_barter_mint_bank_loan():
    sim, roles = make_world()
    a, b = roles["actor"], roles["neighbour"]

    # A has no money: buying from B becomes a swap of goods
    a.wealth = 0.0
    b.inventory.items["herbs"] = 5
    a.inventory.items.pop("herbs", None)
    result = None
    for _ in range(20):
        result = act(sim, a, "trade", target=b)
        if result.success:
            break
    assert result.success and result.metadata.get("barter"), result.message

    # A mints coins from metal ore until it can open a bank; B borrows from it
    while a.wealth < 100 and a.inventory.has_item("metal_ore", 4):
        assert act(sim, a, "mint_coins").success
    assert a.wealth >= 100
    assert act(sim, a, "open_bank").success
    assert act(sim, b, "apply_for_loan").success

    # A loan left unpaid defaults, and the world carries on (logging a
    # default used to raise inside tick())
    import asyncio
    loan = next(iter(sim.economy.banking.loans.values()))
    loan.missed_payments = 3
    with quiet():
        asyncio.run(sim.tick())
    assert loan.status.value == "defaulted"


def test_a_barter_never_overfills_the_buyer():
    sim, roles = make_world()
    a, b = roles["actor"], roles["neighbour"]
    a.wealth = 0.0
    a.inventory.items = {"wood": 149}
    a.inventory.capacity = 150
    b.inventory.items["herbs"] = 50
    before = a.inventory.get_total_items() + b.inventory.get_total_items()
    for _ in range(10):
        with quiet():
            from agents.agent import Action, ActionType
            sim._handler_registry.get_handler(ActionType.TRADE).execute(a, Action(ActionType.TRADE, target_agent=b.id))
    assert a.inventory.get_total_items() <= a.inventory.capacity
    assert a.inventory.get_total_items() + b.inventory.get_total_items() == before  # nothing vanished


def test_taxes_collected_resisted_and_repealed():
    sim, roles = make_world()
    leader, a, c = roles["neighbour"], roles["actor"], roles["sick"]
    leader.personality.aggression = 0.1
    act(sim, leader, "govern")
    befriend(sim, a, leader)
    befriend(sim, c, leader)
    act(sim, a, "govern")
    act(sim, c, "govern")
    tax = act(sim, leader, "make_law", details="a tax to build the granary")
    assert tax.metadata.get("tax_policy_id")

    # The leader collects; A starts a revolt against the tax and C joins it
    before = a.wealth
    assert act(sim, leader, "govern").metadata.get("taxes", 0) > 0 and a.wealth < before
    assert act(sim, a, "join_tax_revolt").metadata["started"]
    assert act(sim, c, "join_tax_revolt").metadata["revolt_size"] == 2

    # Citizens vote the tax down: the law is repealed and the tax ends
    gm, law = sim.governance_manager, sim.governance_manager.laws[tax.metadata["law_id"]]
    gm.vote_on_law(a.id, law.id, False)
    gm.vote_on_law(c.id, law.id, False)
    gm.update_governments(current_tick=10)
    for policy_id in gm.repealed_tax_policies:
        sim.economy.taxation.repeal_tax_policy(policy_id, 10)
    assert not law.active and not sim.economy.taxation.tax_policies[tax.metadata["tax_policy_id"]].active


def test_steel_from_refined_iron():
    sim, roles = make_world()
    a = roles["actor"]
    assert act(sim, a, "refine_material", details="iron ore").metadata["product"] == "iron"
    first = act(sim, a, "create_alloy")
    assert first.success and first.metadata["product"] == "steel"
    act(sim, a, "refine_material", details="iron ore")
    assert act(sim, a, "create_alloy").success  # a known alloy can be made again


def test_courting_needs_having_met_and_is_done_in_person():
    """Only someone you've met (life/family.py knows); farther than
    COURT_REACH, you walk to them first. Courting used to reach any stranger
    anywhere, and every couple formed in the first hours of day one."""
    from agents.agent import Action, ActionType, Position
    from life import family
    sim, roles = make_world()
    b, d = roles["partner"], roles["neighbour"]      # B and D have never met
    romance = sim._handler_registry.get_handler(ActionType.SEEK_ROMANCE)
    b.partner_id = None
    roles["actor"].partner_id = None
    with quiet():
        ok, why = romance.validate(d, Action(ActionType.SEEK_ROMANCE, target_agent=b.id))
    assert not ok and "haven't met" in why
    befriend(sim, b, d, 0.4)
    d.location = Position(*next((x, y) for (x, y) in sorted(sim.world.map.land_component)
                                if 15 <= ((x - b.location.x) ** 2 + (y - b.location.y) ** 2) ** 0.5 <= 20))
    far = d.location.distance_to(b.location)
    walking = act(sim, d, "seek_romance", target=b)
    assert walking.success and "On your way" in walking.message and walking.metadata.get("underway")
    assert d.location.distance_to(b.location) < far and d.id not in b.admirers
    d.location = Position(b.location.x + 1, b.location.y)
    assert act(sim, d, "seek_romance", target=b).success and d.id in b.admirers


def test_a_courtship_deepens_with_time_between_visits_not_with_haste():
    """Visits in quick succession hardly deepen the bond; spaced over days
    they do (social/relationships.py BOND_SPACING)."""
    sim, roles = make_world()
    c, d = roles["sick"], roles["neighbour"]
    rel = sim.relationship_manager.get_relationship(c.id, d.id)
    act(sim, d, "seek_romance", target=c)
    act(sim, c, "seek_romance", target=d)              # both courting: getting to know each other
    start = rel.strength
    for i in range(20):                                # an afternoon of visits, back to back
        act(sim, d if i % 2 else c, "seek_romance", target=c if i % 2 else d)
    assert rel.strength - start < 0.05 and c.partner_id is None
    visits = court_until_partners(sim, d, c)           # a visit every 8 hours
    assert visits >= 3 and c.partner_id == d.id


def test_partnership_needs_both_to_choose_and_either_can_end_it():
    from life import family
    sim, roles = make_world()
    a, c, d = roles["actor"], roles["sick"], roles["neighbour"]
    from agents.agent import Action, ActionType
    romance = sim._handler_registry.get_handler(ActionType.SEEK_ROMANCE)

    # D courts C: interest on one side makes nobody a partner
    assert act(sim, d, "seek_romance", target=c).success
    assert d.partner_id is None and c.partner_id is None
    with quiet():                                             # still no answer: it's up to C
        ok, why = romance.validate(d, Action(ActionType.SEEK_ROMANCE, target_agent=c.id))
    assert not ok and "up to them" in why

    # C, on its own turn, courts D back: both chose it, but they've only just
    # met (bond 0.4), so they're getting to know each other
    back = act(sim, c, "seek_romance", target=d)
    assert back.success and back.metadata.get("mutual") and c.partner_id is None
    # A few more visits, each deepening the bond, and they're partners
    assert court_until_partners(sim, d, c) > 1
    assert c.partner_id == d.id and d.partner_id == c.id

    # A has a partner (from make_world) and C is taken: neither can court
    ok, why = romance.validate(a, Action(ActionType.SEEK_ROMANCE, target_agent=c.id))
    assert not ok and "partner" in why

    # Either partner can end it alone
    assert act(sim, c, "separate").success
    assert c.partner_id is None and d.partner_id is None

    # Interest fades: courting someone isn't remembered forever
    assert act(sim, d, "seek_romance", target=c).success
    sim.world.time.current_tick += family.INTEREST_MEMORY_TICKS + 1
    assert not act(sim, c, "seek_romance", target=d).metadata.get("partnership_formed")


def test_a_partner_dying_frees_the_other():
    sim, roles = make_world()
    a, b = roles["actor"], roles["partner"]
    b.alive = False
    sim.lifecycle_manager.handle_deaths()
    assert a.partner_id is None


def test_glass_from_sand_burns_fuel():
    sim, roles = make_world()
    a = roles["actor"]
    for item in ("iron_ore", "metal_ore", "coal", "wood"):
        a.inventory.items.pop(item, None)
    a.inventory.items["sand"] = 3
    from agents.agent import Action, ActionType
    handler = sim._handler_registry.get_handler(ActionType.REFINE_MATERIAL)
    ok, why = handler.validate(a, Action(ActionType.REFINE_MATERIAL))
    assert not ok and "wood or coal" in why  # no fire, no glass
    a.inventory.items["wood"] = 2
    result = act(sim, a, "refine_material", details="sand into glass")
    assert result.metadata["product"] == "glass" and a.inventory.items["glass"] == 1
    assert a.inventory.items["sand"] == 2 and a.inventory.items["wood"] == 1


def test_land_already_claimed_is_refused_before_the_turn_is_spent():
    """validate, not execute, says the land is taken, so the brains choose
    something else (it used to fail ~75 turns per dawn world)."""
    from agents.agent import Action, ActionType
    sim, roles = make_world()
    owner, other = roles["actor"], roles["neighbour"]
    assert act(sim, owner, "claim_territory").success
    handler = sim._handler_registry.get_handler(ActionType.CLAIM_TERRITORY)
    with quiet():
        mine = handler.validate(owner, Action(ActionType.CLAIM_TERRITORY))
        theirs = handler.validate(other, Action(ActionType.CLAIM_TERRITORY))
    assert mine == (False, "Already own this territory") and theirs == (False, "Land already claimed by another")
    assert not sim._agent_updater._can_run(other, Action(ActionType.CLAIM_TERRITORY))
