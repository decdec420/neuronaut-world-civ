"""
The chronicle: the village's history as it happens.

It records "firsts" (first home, first couple, first birth, first government
and its founder, first law, first religion and its prophet, first invention,
first trade, first war, first death of old age...), a few milestones
(population, eras), and the words of agents with minds of their own: their
reflections, and the reasons they gave for choices that shape the village
(founding, law-making, faith, love).

Nothing here makes anything happen; it only writes down what agents did.
Served at GET /chronicle and shown in the dashboard's Chronicle tab.
Bounded: MAX_ENTRIES events and MAX_VOICES quotes.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set

TICKS_PER_DAY = 144
POPULATION_MILESTONES = (20, 30, 40, 50, 60)
# Choices whose stated reason is worth keeping (the action that runs)
NOTABLE_CHOICES = {"govern", "make_law", "vote", "worship", "perform_ritual", "build_temple",
                   "join_tax_revolt", "separate", "try_for_child", "fight", "open_bank", "mint_coins"}


@dataclass
class ChronicleEntry:
    tick: int
    kind: str            # first | milestone | voice
    key: str
    title: str
    text: str = ""
    agents: List[str] = field(default_factory=list)   # names, as they were then

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["day"] = self.tick // TICKS_PER_DAY + 1
        return d


class Chronicle:
    MAX_ENTRIES = 300
    MAX_VOICES = 100

    def __init__(self):
        self.entries: List[ChronicleEntry] = []
        self.voices: List[ChronicleEntry] = []
        self.done: Set[str] = set()
        self._era: Optional[str] = None
        self._peak_population = 0

    # -- writing -----------------------------------------------------------------

    def first(self, key: str, tick: int, title: str, text: str = "", agents=()) -> bool:
        """Record something that happened for the first time (once per key)."""
        return self._once("first", key, tick, title, text, agents)

    def milestone(self, key: str, tick: int, title: str, text: str = "", agents=()) -> bool:
        return self._once("milestone", key, tick, title, text, agents)

    def _once(self, kind: str, key: str, tick: int, title: str, text: str, agents) -> bool:
        if key in self.done:
            return False
        self.done.add(key)
        self._add(ChronicleEntry(tick, kind, key, title, text, [a for a in agents if a]))
        return True

    def voice(self, tick: int, name: str, text: str, about: str = "") -> None:
        """An agent's own words: a reflection, or its reason for a choice."""
        text = (text or "").strip()
        if not text:
            return
        self.voices.append(ChronicleEntry(tick, "voice", about or "reflection", name, text, [name]))
        del self.voices[:-self.MAX_VOICES]

    def _add(self, entry: ChronicleEntry) -> None:
        self.entries.append(entry)
        if len(self.entries) > self.MAX_ENTRIES:
            # Firsts are the history; drop the oldest milestone before any first
            for i, old in enumerate(self.entries):
                if old.kind != "first":
                    del self.entries[i]
                    break
            else:
                del self.entries[0]

    # -- watching the world --------------------------------------------------------

    def on_action(self, sim, agent, action: str, outcome: Dict, tick: int) -> None:
        """Firsts that show up as a successful action."""
        if not outcome.get("success"):
            return
        name = agent.name
        target_id = outcome.get("target_agent_id") or getattr(agent.current_action, "target_agent", None)
        target = sim._get_agent_by_id(target_id) if target_id else None
        with_whom = f" with {target.name}" if target is not None else ""
        if action == "trade":
            self.first("first_trade", tick, f"First trade: {name}{with_whom}",
                       str(outcome.get("message", "")), [name, target.name if target else None])
        elif action == "fight":
            self.first("first_fight", tick, f"First fight: {name}{' against ' + target.name if target else ''}",
                       str(outcome.get("message", "")), [name, target.name if target else None])
        elif action == "mint_coins":
            self.first("first_coins", tick, f"First coins minted, by {name}", str(outcome.get("message", "")), [name])
        elif action == "build_temple":
            self.first("first_temple", tick, f"First temple, built by {name}", "", [name])
        elif action == "create_art":
            self.first("first_art", tick, f"First work of art, by {name}", str(outcome.get("message", "")), [name])
        elif action == "refine_material" and outcome.get("product") in ("glass", "iron", "copper"):
            product = outcome["product"]
            self.first(f"first_{product}", tick, f"First {product}, made by {name}", str(outcome.get("message", "")), [name])
        elif action == "create_alloy" and outcome.get("product"):
            product = outcome["product"]
            self.first(f"first_{product}", tick, f"First {product}, made by {name}", "", [name])
        elif action == "teach":
            self.first("first_lesson", tick, f"First lesson: {name} taught{' ' + target.name if target else ''}",
                       "", [name, target.name if target else None])

    def on_choice(self, tick: int, agent, action: str, reason: str) -> None:
        """An AI-brain choice and the reason the agent gave for it."""
        if action in NOTABLE_CHOICES and reason:
            self.voice(tick, agent.name, reason, about=action)

    def observe(self, sim, tick: int) -> None:
        """Check the world for firsts and milestones (cheap: counts first)."""
        by_id = sim._get_agent_by_id
        name_of = lambda agent_id: (by_id(agent_id).name if agent_id and by_id(agent_id) else None)  # noqa: E731
        events = sim.life_events

        if "first_home" not in self.done:
            dbs = getattr(sim, "dynamic_building_system", None)
            done = [b for b in dbs.buildings.values() if b.is_complete] if dbs else []
            if done:
                b = done[0]
                builders = [name_of(i) for i in sorted(b.builder_ids)]
                self.first("first_home", tick, f"First building finished: {b.name}",
                           f"Built by {', '.join(n for n in builders if n) or 'someone'}.", builders)

        if "first_couple" not in self.done and events["partnered"]:
            couple = next((a for a in sim.world.agents if a.partner_id), None)
            if couple is not None:
                partner = name_of(couple.partner_id)
                self.first("first_couple", tick, f"First couple: {couple.name} and {partner}",
                           "Each chose the other.", [couple.name, partner])

        if "first_birth" not in self.done and events["born"]:
            child = next((a for a in sim.world.agents if a.mother_id), None)
            if child is not None:
                parents = [name_of(child.mother_id), name_of(child.father_id)]
                self.first("first_birth", tick, f"First child born: {child.name}",
                           f"Child of {' and '.join(p for p in parents if p)}.", [child.name] + parents)

        if "first_coming_of_age" not in self.done and events["became_adult"]:
            grown = next((a for a in sim.world.agents if a.mother_id and a.life_stage == "adult"), None)
            if grown is not None:
                self.first("first_coming_of_age", tick, f"First child of the village grows up: {grown.name}",
                           "", [grown.name])

        gm = sim.governance_manager
        if "first_government" not in self.done and gm.governments:
            gov = next(iter(gm.governments.values()))
            founder = name_of(gov.leader_id)
            self.first("first_government", tick, f"First government: {gov.name}",
                       f"A {gov.government_type.value}, founded by {founder or 'someone'}.", [founder])
        if "first_law" not in self.done and gm.laws:
            law = next(iter(gm.laws.values()))
            self.first("first_law", tick, f"First law: {law.name}", law.description, [name_of(law.created_by)])

        if "first_religion" not in self.done and sim.religion.religions:
            faith = next(iter(sim.religion.religions.values()))
            prophet = faith.founder_name or name_of(faith.founder_id)
            self.first("first_religion", tick, f"First faith: {faith.name}", f"Its prophet: {prophet}.", [prophet])

        innovations = sim.innovation_manager.innovations
        if "first_invention" not in self.done and innovations:
            inv = next(iter(innovations.values()))
            inventor = name_of(inv.discoverer_id)
            self.first("first_invention", tick, f"First invention: {inv.name}",
                       f"Made first by {inventor or 'someone'}.", [inventor])

        wars = getattr(sim.warfare_manager, "active_conflicts", {})
        if "first_war" not in self.done and wars:
            war = next(iter(wars.values()))
            leaders = [name_of(war.leader_a), name_of(war.leader_b)]
            self.first("first_war", tick, f"First war: {' against '.join(n for n in leaders if n) or 'a conflict'}",
                       f"Over {getattr(war.reason, 'value', war.reason)}.", leaders)

        if "first_death" not in self.done or "first_death_old_age" not in self.done:
            for a in sim.world.agents:
                if a.alive:
                    continue
                self.first("first_death", tick, f"First death: {a.name}", f"{a.name} died of {a.death_cause}.", [a.name])
                if a.death_cause == "old age":
                    self.first("first_death_old_age", tick, f"First death of old age: {a.name}",
                               f"{a.name} lived to {a.age}.", [a.name])

        if "first_separation" not in self.done and events["separated"]:
            self.first("first_separation", tick, "First couple to part ways", "", [])

        if "first_job" not in self.done:
            worker = next((a for a in sim.world.agents if a.alive and a.work_life.job), None)
            if worker is not None:
                self.first("first_job", tick, f"First trade of one's own: {worker.name}",
                           f"{worker.name} works as a {worker.work_life.to_dict().get('job_title', 'worker')}.",
                           [worker.name])

        works = getattr(sim, "infrastructure", None)
        if works is not None:
            if "first_road" not in self.done and works.roads:
                self.first("first_road", tick, "First road laid", f"{len(works.roads)} tiles paved.", [])
            if "first_well" not in self.done and works.wells:
                well = next(iter(works.wells.values()))
                self.first("first_well", tick, f"First well, dug by {name_of(well.builder)}", "", [name_of(well.builder)])
            if "first_streetlight" not in self.done and works.lights:
                lamp = next(iter(works.lights.values()))
                self.first("first_streetlight", tick, f"First street light, put up by {name_of(lamp.builder)}",
                           "A glass lamp to light the night.", [name_of(lamp.builder)])
            if "first_lit_night" not in self.done and any(l.lit for l in works.lights.values()):
                self.first("first_lit_night", tick, "The first night with a street lit", "", [])
            for n in (50, 200, 500):
                if len(works.roads) >= n:
                    self.milestone(f"roads_{n}", tick, f"{n} tiles of road")

        # Milestones: population, eras
        alive = sum(1 for a in sim.world.agents if a.alive)
        if alive > self._peak_population:
            for n in POPULATION_MILESTONES:
                if self._peak_population < n <= alive:
                    self.milestone(f"population_{n}", tick, f"The village reaches {n} people")
            self._peak_population = alive
        # The era the dashboard header shows (tech progression)
        era = getattr(getattr(sim, "tech_progression", None), "current_era", None)
        if era and era != self._era:
            if self._era is not None:
                self.milestone(f"era_{era}", tick, f"A new era: {era}")
            self._era = era

    # -- reading -----------------------------------------------------------------

    def to_dict(self, limit: int = 100) -> Dict:
        return {
            "entries": [e.to_dict() for e in self.entries[-limit:]],
            "voices": [v.to_dict() for v in self.voices[-limit:]],
            "firsts": sorted(k for k in self.done if k.startswith("first_")),
        }
