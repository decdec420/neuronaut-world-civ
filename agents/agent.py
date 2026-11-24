"""
Agent System - Autonomous AI entities with psychology and agency

Each agent is an independent entity with:
- Unique psychology (needs, personality, emotions)
- Memory and learning
- Decision-making based on psychology
- Actions and interactions
- Social relationships
"""

from engine.ids import new_uuid
import random
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
from datetime import datetime

import sys
import os

logger = logging.getLogger(__name__)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.psychology import (
    NeedState, PersonalityProfile, EmotionalState,
    PsychologyEngine, NeedType, EmotionType
)
from engine.smart_memory import SmartMemorySystem, EventImportance, MemoryType


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"


class ActionType(Enum):
    """Types of actions agents can take - EXPANDED FOR FULL AUTONOMY"""

    # ===== MOVEMENT & EXPLORATION =====
    MOVE = "move"
    EXPLORE = "explore"
    SCOUT = "scout"
    MAP_AREA = "map_area"
    SEARCH = "search"
    WANDER = "wander"
    FOLLOW = "follow"
    CHASE = "chase"
    HIDE = "hide"

    # ===== RESOURCE GATHERING =====
    GATHER_FOOD = "gather_food"
    GATHER_WATER = "gather_water"
    GATHER_MATERIALS = "gather_materials"
    HUNT = "hunt"
    FISH = "fish"
    FORAGE = "forage"
    MINE = "mine"
    CHOP_WOOD = "chop_wood"

    # ===== AGRICULTURE & FOOD =====
    PLANT_CROPS = "plant_crops"
    TEND_CROPS = "tend_crops"
    HARVEST = "harvest"
    RAISE_ANIMALS = "raise_animals"
    COOK = "cook"
    BREW = "brew"
    PRESERVE_FOOD = "preserve_food"

    # ===== CONSTRUCTION & BUILDING =====
    BUILD = "build"
    BUILD_HOUSE = "build_house"
    BUILD_WORKSHOP = "build_workshop"
    BUILD_MARKET = "build_market"
    BUILD_TEMPLE = "build_temple"
    BUILD_WALL = "build_wall"
    REPAIR = "repair"
    DEMOLISH = "demolish"

    # ===== CRAFTING & PRODUCTION =====
    CRAFT = "craft"
    CRAFT_TOOL = "craft_tool"
    CRAFT_WEAPON = "craft_weapon"
    CRAFT_ARMOR = "craft_armor"
    CRAFT_CLOTHING = "craft_clothing"
    CRAFT_FURNITURE = "craft_furniture"
    CRAFT_JEWELRY = "craft_jewelry"
    SMELT = "smelt"
    WEAVE = "weave"
    POTTERY = "pottery"

    # ===== REST & RECOVERY =====
    REST = "rest"
    SLEEP = "sleep"
    RELAX = "relax"
    EAT = "eat"
    MEDITATE = "meditate"
    BATHE = "bathe"

    # ===== SOCIAL INTERACTION =====
    SOCIALIZE = "socialize"
    COMMUNICATE = "communicate"
    CONVERSE = "converse"
    GOSSIP = "gossip"
    JOKE = "joke"
    COMPLIMENT = "compliment"
    INSULT = "insult"
    APOLOGIZE = "apologize"
    COMFORT = "comfort"
    CELEBRATE = "celebrate"

    # ===== ROMANCE & REPRODUCTION =====
    SEEK_ROMANCE = "seek_romance"
    FLIRT = "flirt"
    COURT = "court"
    PROPOSE = "propose"
    MARRY = "marry"
    HAVE_SEX = "have_sex"
    GIVE_BIRTH = "give_birth"
    CARE_FOR_CHILD = "care_for_child"
    PARENT = "parent"
    SEPARATE = "separate"
    TRY_FOR_CHILD = "try_for_child"

    # ===== PUBLIC WORKS (world/infrastructure.py) =====
    BUILD_ROAD = "build_road"
    DIG_WELL = "dig_well"
    BUILD_STREETLIGHT = "build_streetlight"

    # ===== ECONOMIC & TRADE =====
    TRADE = "trade"
    SELL = "sell"
    BUY = "buy"
    BARTER = "barter"
    WORK = "work"
    EMPLOY = "employ"
    INVEST = "invest"
    STEAL = "steal"
    BEG = "beg"

    # ===== ADVANCED FINANCIAL SYSTEM =====
    # Minting & Currency
    MINT_COINS = "mint_coins"
    COUNTERFEIT_COINS = "counterfeit_coins"
    DEBASE_CURRENCY = "debase_currency"

    # Banking & Credit
    OPEN_BANK = "open_bank"
    OPEN_SAVINGS_ACCOUNT = "open_savings_account"
    WITHDRAW_SAVINGS = "withdraw_savings"
    APPLY_FOR_LOAN = "apply_for_loan"
    MAKE_LOAN_PAYMENT = "make_loan_payment"
    DEFAULT_ON_LOAN = "default_on_loan"

    # Taxation & Revenue
    COLLECT_TAX = "collect_tax"
    PAY_TAX = "pay_tax"
    EVADE_TAX = "evade_tax"
    START_TAX_REVOLT = "start_tax_revolt"
    JOIN_TAX_REVOLT = "join_tax_revolt"

    # Trade Routes & Commerce
    ESTABLISH_TRADE_ROUTE = "establish_trade_route"
    SEND_CARAVAN = "send_caravan"
    FORM_MERCHANT_GUILD = "form_merchant_guild"
    ATTACK_CARAVAN = "attack_caravan"

    # Speculation & Investment
    INVEST_IN_BUBBLE = "invest_in_bubble"
    SELL_INVESTMENT = "sell_investment"
    SPECULATE = "speculate"

    # ===== CONFLICT & COMBAT =====
    FIGHT = "fight"
    ATTACK = "attack"
    DEFEND = "defend"
    FLEE = "flee"
    DUEL = "duel"
    AMBUSH = "ambush"
    GUARD = "guard"
    PATROL = "patrol"
    THREATEN = "threaten"
    INTIMIDATE = "intimidate"

    # ===== CREATIVE & ARTS =====
    CREATE_ART = "create_art"
    PAINT = "paint"
    SCULPT = "sculpt"
    WRITE = "write"
    COMPOSE_MUSIC = "compose_music"
    SING = "sing"
    DANCE = "dance"
    TELL_STORY = "tell_story"
    PERFORM = "perform"
    ENTERTAIN = "entertain"

    # ===== LEARNING & EDUCATION =====
    LEARN_SKILL = "learn_skill"
    TEACH = "teach"
    STUDY = "study"
    PRACTICE = "practice"
    MENTOR = "mentor"
    APPRENTICE = "apprentice"
    RESEARCH = "research"
    EXPERIMENT = "experiment"
    INVENT = "invent"
    DISCOVER = "discover"

    # ===== LEADERSHIP & POLITICS =====
    LEAD = "lead"
    GOVERN = "govern"
    MAKE_LAW = "make_law"
    JUDGE = "judge"
    NEGOTIATE = "negotiate"
    FORM_ALLIANCE = "form_alliance"
    DECLARE_WAR = "declare_war"
    MAKE_PEACE = "make_peace"
    VOTE = "vote"
    CAMPAIGN = "campaign"

    # ===== GROUP & COMMUNITY =====
    JOIN_GROUP = "join_group"
    LEAVE_GROUP = "leave_group"
    FORM_GROUP = "form_group"
    RECRUIT = "recruit"
    EXILE = "exile"
    ORGANIZE_EVENT = "organize_event"
    ATTEND_EVENT = "attend_event"

    # ===== SPIRITUAL & RITUAL =====
    PRAY = "pray"
    WORSHIP = "worship"
    PERFORM_RITUAL = "perform_ritual"
    BLESS = "bless"
    CURSE = "curse"
    PROPHESY = "prophesy"
    CONVERT = "convert"

    # ===== HEALTH & MEDICINE =====
    HEAL = "heal"
    CURE = "cure"
    DIAGNOSE = "diagnose"
    TREAT = "treat"
    MIDWIFE = "midwife"
    COMFORT_SICK = "comfort_sick"

    # ===== EXPLORATION & DISCOVERY =====
    EXPLORE_UNKNOWN = "explore_unknown"
    CHART_MAP = "chart_map"
    SURVEY_LAND = "survey_land"
    FIND_RESOURCES = "find_resources"
    CLAIM_TERRITORY = "claim_territory"

    # ===== CHEMISTRY & SCIENCE =====
    PERFORM_CHEMISTRY = "perform_chemistry"
    SMELT_ORE = "smelt_ore"
    DISCOVER_ELEMENT = "discover_element"
    SYNTHESIZE_COMPOUND = "synthesize_compound"

    # ===== ENERGY & POWER =====
    BUILD_POWER_PLANT = "build_power_plant"
    DISCOVER_ENERGY = "discover_energy"
    OPERATE_POWER_PLANT = "operate_power_plant"

    # ===== MATERIALS SCIENCE =====
    DISCOVER_MATERIAL = "discover_material"
    CREATE_ALLOY = "create_alloy"
    REFINE_MATERIAL = "refine_material"

    # ===== ENTERTAINMENT & LEISURE =====
    PLAY_GAME = "play_game"
    GAMBLE = "gamble"
    WATCH = "watch"
    LISTEN = "listen"
    FEAST = "feast"
    DRINK = "drink"
    SMOKE = "smoke"

    # ===== MISCELLANEOUS =====
    IDLE = "idle"
    WAIT = "wait"
    OBSERVE = "observe"
    CONTEMPLATE = "contemplate"
    SCHEME = "scheme"
    PLAN = "plan"


@dataclass
class Position:
    """2D position in the world"""
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def move_toward(self, target: 'Position', distance: float) -> 'Position':
        """Move toward target by distance"""
        current_dist = self.distance_to(target)
        if current_dist <= distance:
            return Position(target.x, target.y)

        ratio = distance / current_dist
        new_x = self.x + (target.x - self.x) * ratio
        new_y = self.y + (target.y - self.y) * ratio
        return Position(new_x, new_y)


@dataclass
class Memory:
    """Memory of a past event or interaction (LEGACY - for backward compatibility)"""
    timestamp: datetime
    event_type: str
    agents_involved: List[str]
    location: Position
    emotional_impact: float  # -1 to 1
    data: Dict = field(default_factory=dict)


@dataclass
class Skill:
    """A skill the agent possesses"""
    name: str
    level: float = 0.0  # 0-1, proficiency
    experience: float = 0.0  # Cumulative practice

    def practice(self, amount: float = 0.1):
        """Improve skill through practice"""
        self.experience += amount
        # Logarithmic growth
        self.level = min(1.0, 0.1 + 0.9 * (self.experience / (self.experience + 10)))


@dataclass
class SkillSet:
    """Collection of agent's skills"""
    skills: Dict[str, Skill] = field(default_factory=dict)

    def get_skill(self, skill_name: str) -> float:
        """Get skill level (0 if doesn't have it)"""
        if skill_name not in self.skills:
            return 0.0
        return self.skills[skill_name].level

    def learn_skill(self, skill_name: str, amount: float = 0.1):
        """Learn or improve a skill"""
        if skill_name not in self.skills:
            self.skills[skill_name] = Skill(skill_name)
        self.skills[skill_name].practice(amount)

    def get_top_skills(self, count: int = 5) -> List[Tuple[str, float]]:
        """Get agent's top skills"""
        sorted_skills = sorted(self.skills.items(),
                             key=lambda x: x[1].level,
                             reverse=True)
        return [(name, skill.level) for name, skill in sorted_skills[:count]]


@dataclass
class Inventory:
    """Agent's possessions"""
    items: Dict[str, int] = field(default_factory=dict)  # item_name -> quantity
    capacity: int = 150  # was 20: a basic shelter needs ~55 materials

    def add_item(self, item_name: str, quantity: int = 1) -> bool:
        """Add item to inventory"""
        current_total = sum(self.items.values())
        if current_total + quantity > self.capacity:
            return False

        self.items[item_name] = self.items.get(item_name, 0) + quantity
        return True

    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item from inventory"""
        if self.items.get(item_name, 0) < quantity:
            return False

        self.items[item_name] -= quantity
        if self.items[item_name] <= 0:
            del self.items[item_name]
        return True

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if has item"""
        return self.items.get(item_name, 0) >= quantity

    def consume_items(self, items_needed: Dict[str, int]) -> bool:
        """
        Consume multiple items from inventory (for crafting, building, etc.)
        Returns True if successful, False if insufficient materials
        """
        # First check if we have all items
        for item_name, quantity in items_needed.items():
            if not self.has_item(item_name, quantity):
                return False

        # We have everything, now consume it
        for item_name, quantity in items_needed.items():
            self.remove_item(item_name, quantity)

        return True

    def get_total_items(self) -> int:
        """Get total item count"""
        return sum(self.items.values())

    def get_value(self) -> float:
        """Estimate total value of inventory"""
        # Simplified: each item worth 1 unit
        return float(self.get_total_items())


@dataclass
class Action:
    """An action the agent wants to perform"""
    action_type: ActionType
    target_agent: Optional[str] = None
    target_position: Optional[Position] = None
    parameters: Dict = field(default_factory=dict)
    priority: float = 0.5


def _roman(n: int) -> str:
    """2 -> II, 14 -> XIV (for repeated names)."""
    out = ""
    for value, numeral in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                           (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out += numeral
            n -= value
    return out


class Agent:
    """Autonomous agent with psychology and agency"""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        age: int = 20,
        gender: Optional[Gender] = None,
        personality: Optional[PersonalityProfile] = None,
        is_player: bool = False
    ):
        # Identity
        self.id = agent_id or str(new_uuid())
        self.gender = gender or random.choice(list(Gender))  # Set gender FIRST
        self.name = name or self._generate_name()  # THEN generate name based on gender
        Agent._used_names.add(self.name)
        self.age = age

        # Psychology
        self.needs = NeedState.create_default()
        self.personality = personality or PersonalityProfile.random()
        self.emotions = EmotionalState.create_default()

        # Cognition - Smart Memory System (industry-standard 2026)
        self.memory = SmartMemorySystem(
            agent_id=self.id,
            working_memory_size=100,
            decay_factor=0.995  # Redis AI agent standard
        )
        self.skills = SkillSet()

        # Physical
        self.location = Position(0.0, 0.0)
        self.health = 100.0
        self.energy = 100.0
        self.alive = True

        # Economic - Start with NOTHING, must survive from scratch
        self.inventory = Inventory()
        self.wealth = 0.0  # No starting wealth - earn it or die
        self.property_ids: List[str] = []

        # VALUE LEARNING - Agents learn item worth through trading!
        # Start with vague estimates, learn true value through experience
        self.learned_values: Dict[str, float] = {}  # item -> learned value
        self.value_confidence: Dict[str, float] = {}  # item -> confidence (0-1)
        self.trade_count: Dict[str, int] = {}  # item -> number of trades

        # REPUTATION SYSTEM - Track trustworthiness in trading
        self.trading_reputation: float = 0.5  # 0-1 scale (0.5 = neutral/unknown)
        self.successful_trades: int = 0
        self.failed_trades: int = 0
        self.reputation_by_agent: Dict[str, float] = {}  # Per-agent reputation memory

        # Social
        self.status = 0.5  # 0-1, social status
        self.group_memberships: Set[str] = set()

        # Meta
        self.is_player = is_player
        self.created_at = datetime.now()
        self.ticks_lived = 0

        # ===== LIFE CYCLE - Birth, Family, Death =====
        # Family tracking
        self.mother_id: Optional[str] = None  # ID of mother (if born in-game)
        self.father_id: Optional[str] = None  # ID of father (if born in-game)
        self.children_ids: List[str] = []  # IDs of children

        # Partnership (life/family.py): formed only when both chose each other
        self.partner_id: Optional[str] = None
        self.admirers: Dict[str, int] = {}  # who courted this agent -> tick they last did
        # What it knows how to do beyond what comes with being human
        # (world/knowhow.py); None: everything (a settlers' world)
        self.knowhow: Optional[Set[str]] = None
        self.generation: int = 1   # founders are 1; a child is one more than its parents
        self.child_wish_tick: Optional[int] = None  # when it last said it wants a child
        self.home_id: Optional[str] = None  # the building it lives in (life/homes.py)

        # Pregnancy (for females only)
        self.is_pregnant: bool = False
        self.pregnancy_partner_id: Optional[str] = None  # ID of father
        self.pregnancy_start_tick: int = 0
        self.pregnancy_duration_ticks: int = 1500  # ~9 months (at ~144 ticks/day = 10.4 days)

        # Life stage; age_ticks counts toward the next birthday (life/aging.py)
        self.life_stage: str = self._determine_life_stage()  # baby, child, adult, elder
        self.age_ticks: int = 0

        # Death tracking
        self.death_tick: Optional[int] = None
        self.death_cause: Optional[str] = None
        self.death_recorded: bool = False  # counted, logged and mourned once

        # Current action
        self.current_action: Optional[Action] = None
        self.active_construction_id: Optional[str] = None  # Building being constructed

        # Daily life: when they sleep and work, and the job that emerges from
        # the work they do (agents/daily_life.py)
        from agents.daily_life import DailyRoutine, WorkLife
        self.routine = DailyRoutine.for_personality(self.personality)
        self.work_life = WorkLife()
        self.shift_job: Optional[str] = None
        from agents.utility_brain import ActionMemory
        self.action_memory = ActionMemory()  # what has worked for this agent
        from agents.memory_stream import MemoryStream
        self.memory_stream = MemoryStream()  # what it has done and lived through (Smallville-style)

        # PURPOSEFUL ACTION TRACKING - Creates empire builders!
        self.current_action_purpose: Optional[Dict] = None  # Why they're doing this
        self.recent_action_outcomes: List[Dict] = []  # Last 10 action results
        self.life_satisfaction_history: List[float] = []  # Track life trajectory
        self.decision_quality_scores: List[float] = []  # How good their choices are

    # Names in use in the current world (reset by WorldInitializer.initialize_world)
    _used_names = set()

    MALE_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
                  "Thomas", "Charles", "Daniel", "Matthew", "Andrew", "Benjamin", "Samuel", "Henry",
                  "Christopher", "Joshua", "George", "Kenneth", "Steven", "Edward", "Brian", "Ronald",
                  "Arthur", "Walter", "Peter", "Hugo", "Oscar", "Felix", "Leo", "Theo",
                  "Isaac", "Elias", "Jonah", "Silas", "Owen", "Rafael", "Mateo", "Kofi"]
    FEMALE_NAMES = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan",
                    "Jessica", "Sarah", "Karen", "Nancy", "Margaret", "Lisa", "Betty", "Dorothy", "Emily",
                    "Ashley", "Michelle", "Kimberly", "Amanda", "Stephanie", "Rebecca", "Laura", "Helen",
                    "Alice", "Clara", "Rose", "Iris", "Hazel", "Ruth", "Esther", "Nora",
                    "Lucia", "Maya", "Ada", "Ivy", "Freya", "Amara", "Sofia", "Yara"]

    @classmethod
    def reset_names(cls, in_use=()) -> None:
        """Start a new world's name registry (optionally with names already taken)."""
        cls._used_names = set(in_use)

    def _generate_name(self) -> str:
        """A name nobody in this world has had. When a list runs out, names
        come back with a numeral: "James II", "James III"... (This used to
        fall back to random numbers, which could repeat.)"""
        if self.gender == Gender.MALE:
            pool = Agent.MALE_NAMES
        elif self.gender == Gender.FEMALE:
            pool = Agent.FEMALE_NAMES
        else:
            pool = Agent.MALE_NAMES + Agent.FEMALE_NAMES
        available = [n for n in pool if n not in Agent._used_names]
        if available:
            name = random.choice(available)
        else:
            base, n = random.choice(pool), 2
            while f"{base} {_roman(n)}" in Agent._used_names:
                n += 1
            name = f"{base} {_roman(n)}"
        Agent._used_names.add(name)
        return name

    def __getstate__(self) -> Dict:
        """For saving (engine/persistence.py): the AI-brain methods bound to this
        agent can't be pickled (they refer back to it); they are re-bound on load."""
        import types
        state = self.__dict__.copy()
        bound = [k for k, v in state.items() if isinstance(v, types.MethodType) and v.__self__ is self]
        for k in bound:
            del state[k]
        state['_had_ai_methods'] = bool(bound)
        return state

    def __setstate__(self, state: Dict) -> None:
        had_ai = state.pop('_had_ai_methods', False)
        self.__dict__.update(state)
        if had_ai:
            from agents.autonomous_agent import bind_autonomous_methods
            bind_autonomous_methods(self, init=False)

    def _determine_life_stage(self) -> str:
        """baby, child, adult or elder, by age (life/aging.py)"""
        from life.aging import life_stage
        return life_stage(self.age)

    def _create_inherited_personality(self, father_personality: Optional[PersonalityProfile]) -> PersonalityProfile:
        """Create baby personality by inheriting from parents"""
        # Mother's traits
        mother_traits = self.personality

        if father_personality:
            # Blend mother and father traits (50/50 mix + random mutation)
            return PersonalityProfile(
                openness=self._inherit_trait(mother_traits.openness, father_personality.openness),
                conscientiousness=self._inherit_trait(mother_traits.conscientiousness, father_personality.conscientiousness),
                extraversion=self._inherit_trait(mother_traits.extraversion, father_personality.extraversion),
                agreeableness=self._inherit_trait(mother_traits.agreeableness, father_personality.agreeableness),
                neuroticism=self._inherit_trait(mother_traits.neuroticism, father_personality.neuroticism),
                risk_taking=self._inherit_trait(mother_traits.risk_taking, father_personality.risk_taking),
                aggression=self._inherit_trait(mother_traits.aggression, father_personality.aggression),
                sexuality=self._inherit_trait(mother_traits.sexuality, father_personality.sexuality),
                ambition=self._inherit_trait(mother_traits.ambition, father_personality.ambition),
                creativity=self._inherit_trait(mother_traits.creativity, father_personality.creativity),
                empathy=self._inherit_trait(mother_traits.empathy, father_personality.empathy),
                rationality=self._inherit_trait(mother_traits.rationality, father_personality.rationality),
            )
        else:
            # Only mother traits available (with mutation)
            return PersonalityProfile(
                openness=self._mutate_trait(mother_traits.openness),
                conscientiousness=self._mutate_trait(mother_traits.conscientiousness),
                extraversion=self._mutate_trait(mother_traits.extraversion),
                agreeableness=self._mutate_trait(mother_traits.agreeableness),
                neuroticism=self._mutate_trait(mother_traits.neuroticism),
                risk_taking=self._mutate_trait(mother_traits.risk_taking),
                aggression=self._mutate_trait(mother_traits.aggression),
                sexuality=self._mutate_trait(mother_traits.sexuality),
                ambition=self._mutate_trait(mother_traits.ambition),
                creativity=self._mutate_trait(mother_traits.creativity),
                empathy=self._mutate_trait(mother_traits.empathy),
                rationality=self._mutate_trait(mother_traits.rationality),
            )

    def _inherit_trait(self, mother_value: float, father_value: float) -> float:
        """Inherit trait from both parents with mutation"""
        # Average of parents + small random mutation
        inherited = (mother_value + father_value) / 2.0
        mutation = random.gauss(0, 0.1)  # Small random change
        return max(0.0, min(1.0, inherited + mutation))

    def _mutate_trait(self, value: float) -> float:
        """Mutate a single trait slightly"""
        mutation = random.gauss(0, 0.15)  # Slightly larger mutation when only one parent
        return max(0.0, min(1.0, value + mutation))

    def update(self, delta_time: float = 1.0):
        """Update agent state (called each simulation tick)"""
        if not self.alive:
            return

        # Update psychology
        self.needs.update(delta_time)
        self.emotions.update(delta_time)

        # Update physical state - energy drains (very slow)
        self.energy = max(0, self.energy - 0.1 * delta_time)  # Very slow drain

        # ===== SURVIVAL CONSEQUENCES - DEATH IS REAL =====
        # Agents can die from starvation, dehydration, exhaustion, disease, or old age

        # Low energy causes health damage (exhaustion)
        if self.energy <= 0:
            self.health -= 0.01 * delta_time  # Slow exhaustion
            if random.random() < 0.001:  # Rare collapse
                logger.warning(f"💀 {self.name} collapsed from exhaustion!")

        # STARVATION - Hunger kills slowly but surely (REDUCED DAMAGE)
        hunger_need = self.needs.needs.get(NeedType.HUNGER)
        if hunger_need and hunger_need.level > 0.95:  # Critical hunger
            damage = 0.01 * delta_time  # REDUCED from 0.05 to 0.01 - much slower death
            self.health -= damage
            if random.random() < 0.01:  # Log starvation occasionally
                logger.warning(f"💀 {self.name} is STARVING! Health: {self.health:.1f}")

        # DEHYDRATION - Thirst kills FAST but not instantly (REDUCED DAMAGE)
        thirst_need = self.needs.needs.get(NeedType.THIRST)
        if thirst_need and thirst_need.level > 0.95:  # Critical thirst
            damage = 0.03 * delta_time  # REDUCED from 0.15 to 0.03 - gives time to find water
            self.health -= damage
            if random.random() < 0.01:
                logger.warning(f"💀 {self.name} is DYING of thirst! Health: {self.health:.1f}")

        # NATURAL RECOVERY - health slowly returns when basic needs are met.
        # Without this, every storm, illness or hungry spell did permanent
        # damage and every agent eventually died of "unknown causes".
        if (self.health < 100.0
                and (not hunger_need or hunger_need.level < 0.6)
                and (not thirst_need or thirst_need.level < 0.6)
                and self.energy > 20):
            self.health = min(100.0, self.health + 0.05 * delta_time)

        # DISEASE - Random illness (rare but deadly)
        if random.random() < 0.0001 * delta_time:  # ~0.01% chance per tick
            disease_damage = random.uniform(5, 20)
            self.health -= disease_damage
            logger.warning(f"🦠 {self.name} contracted a disease! Lost {disease_damage:.1f} health!")

        # Age tracking (birthdays, life stages and old age: LifecycleManager.update_aging)
        self.ticks_lived += 1

        # Memory runs on the agent's own clock; decay every 60 ticks (10 sim hours)
        self.memory.clock = self.ticks_lived
        if self.ticks_lived % 60 == 0:
            self.memory.decay_memories()

        # Check death conditions
        if self.health <= 0:
            if self.alive:  # Only log death once
                cause = "starvation" if hunger_need and hunger_need.level > 0.95 else \
                        "dehydration" if thirst_need and thirst_need.level > 0.95 else \
                        "exhaustion" if self.energy <= 0 else "unknown causes"
                self.death_cause = cause
                self.death_tick = self.ticks_lived
                logger.info(f"💀💀💀 {self.name} ({self.age}y) DIED from {cause}!")
            self.alive = False

    def perceive(self, world_state: Dict) -> Dict:
        """
        Perceive the world around the agent

        Returns: Perceptions dictionary
        """
        perceptions = {
            'nearby_agents': [],
            'nearby_resources': [],
            'nearby_locations': [],
            'current_location': self.location,
            'time_of_day': world_state.get('time_of_day', 12),
        }

        # Get nearby agents (within perception range)
        perception_range = 10.0
        all_agents = world_state.get('agents', [])

        for other_agent in all_agents:
            if other_agent.id == self.id:
                continue

            distance = self.location.distance_to(other_agent.location)
            if distance <= perception_range:
                doing = getattr(other_agent, 'current_action', None)
                perceptions['nearby_agents'].append({
                    'id': other_agent.id,
                    'name': other_agent.name,
                    'distance': distance,
                    'location': other_agent.location,
                    # what it chose last: others can see what you're up to
                    'doing': doing.action_type.value if doing is not None else None,
                })

        # Get nearby resources
        all_resources = world_state.get('resources', [])
        for resource in all_resources:
            distance = self.location.distance_to(resource.get('location'))
            if distance <= perception_range:
                perceptions['nearby_resources'].append(resource)

        return perceptions

    def decide(self, perceptions: Dict, can_run=None) -> Action:
        """
        Decide what action to take based on psychology and perceptions

        This is where the magic happens - psychology drives behavior

        can_run: optional callable(action) -> bool. When given, options the
        action's handler would reject right now are not considered.
        """

        # ===== EMERGENCY SURVIVAL OVERRIDE =====
        # If critically hungry/thirsty AND have food/water, EAT/DRINK IMMEDIATELY!
        # This prevents stupid death when agents have food but don't eat
        hunger_need = self.needs.needs.get(NeedType.HUNGER)
        thirst_need = self.needs.needs.get(NeedType.THIRST)

        # CRITICAL THIRST - drink if we have water (thirst kills faster!)
        if thirst_need and thirst_need.level > 0.8 and self.inventory.has_item('water'):
            logger.info(f"🚨 {self.name} EMERGENCY DRINK - critically thirsty!")
            return Action(ActionType.DRINK)

        # CRITICAL HUNGER - eat if we have food
        if hunger_need and hunger_need.level > 0.8 and self.inventory.has_item('food'):
            logger.info(f"🚨 {self.name} EMERGENCY EAT - critically hungry!")
            return Action(ActionType.EAT)

        # CRITICALLY LOW HEALTH - rest to recover
        if self.health < 30 and self.energy > 20:
            logger.info(f"🚨 {self.name} EMERGENCY REST - health critical!")
            return Action(ActionType.REST)

        # Get most urgent need
        urgent_need, urgency = self.needs.get_most_urgent_need()
        logger.debug(f"[{self.name}] Most urgent need: {urgent_need.value} (urgency: {urgency:.2f})")

        # Generate possible actions based on need
        possible_actions = self._generate_possible_actions(urgent_need, perceptions, can_run)
        logger.debug(f"[{self.name}] Generated {len(possible_actions)} possible actions: {[a.action_type.value for a in possible_actions]}")

        # Evaluate each action based on psychology
        best_action = None
        best_motivation = 0.0

        for action in possible_actions:
            motivation = PsychologyEngine.calculate_action_motivation(
                self.needs,
                self.personality,
                self.emotions,
                action.action_type.value
            )

            # Add randomness for variety
            motivation *= random.uniform(0.8, 1.2)

            if motivation > best_motivation:
                best_motivation = motivation
                best_action = action

        # If no good action, idle
        if best_action is None or best_motivation < 0.3:
            best_action = Action(ActionType.IDLE)
            logger.debug(f"[{self.name}] No motivated action found, defaulting to IDLE")

        logger.info(f"[{self.name}] CHOSE ACTION: {best_action.action_type.value} (motivation: {best_motivation:.2f}) to address {urgent_need.value}")
        self.current_action = best_action
        return best_action

    def _generate_possible_actions(
        self,
        urgent_need: NeedType,
        perceptions: Dict,
        can_run=None
    ) -> List[Action]:
        """Generate possible actions to satisfy needs"""
        actions = []

        # Always can idle
        actions.append(Action(ActionType.IDLE, priority=0.1))

        # Need-based actions
        if urgent_need == NeedType.HUNGER:
            # If have food, eat it! (highest priority)
            if self.inventory.has_item('food'):
                food_count = self.inventory.items.get('food', 0)
                logger.info(f"[{self.name}] HUNGER detected! Has {food_count} food → adding EAT action (priority 0.95)")
                actions.append(Action(ActionType.EAT, priority=0.95))
            # Otherwise, look for food to gather
            elif perceptions['nearby_resources']:
                food_resources = [r for r in perceptions['nearby_resources']
                                if r.get('type') == 'food']
                if food_resources:
                    actions.append(Action(
                        ActionType.GATHER_FOOD,
                        target_position=food_resources[0]['location'],
                        priority=0.9
                    ))
                else:
                    # No nearby food resources - HUNT for animals!
                    # Agents learn: "I'm hungry + no plants → hunt animals"
                    actions.append(Action(ActionType.HUNT, priority=0.85))
            else:
                # No resources nearby at all - HUNT!
                actions.append(Action(ActionType.HUNT, priority=0.85))

        elif urgent_need == NeedType.THIRST:
            # If have water, drink it! (highest priority)
            if self.inventory.has_item('water'):
                actions.append(Action(ActionType.DRINK, priority=0.95))
            # Otherwise, look for water to gather
            elif perceptions['nearby_resources']:
                water_resources = [r for r in perceptions['nearby_resources']
                                if r.get('type') == 'water']
                if water_resources:
                    actions.append(Action(
                        ActionType.GATHER_WATER,
                        target_position=water_resources[0]['location'],
                        priority=0.9
                    ))
                else:
                    # No water resources visible - gather water from environment
                    # Agents learn: "I'm thirsty → find water sources"
                    actions.append(Action(ActionType.GATHER_WATER, priority=0.85))
            else:
                # No resources nearby - search for water
                actions.append(Action(ActionType.GATHER_WATER, priority=0.85))

        elif urgent_need == NeedType.SLEEP:
            actions.append(Action(ActionType.REST, priority=0.8))

        elif urgent_need in [NeedType.SEX, NeedType.ROMANCE]:
            # Look for potential partners
            nearby = perceptions['nearby_agents']
            for agent_info in nearby:
                actions.append(Action(
                    ActionType.SEEK_ROMANCE,
                    target_agent=agent_info['id'],
                    priority=0.7
                ))

        elif urgent_need in [NeedType.BELONGING, NeedType.FRIENDSHIP]:
            # Socialize with nearby agents
            nearby = perceptions['nearby_agents']
            for agent_info in nearby:
                actions.append(Action(
                    ActionType.SOCIALIZE,
                    target_agent=agent_info['id'],
                    priority=0.6
                ))

        elif urgent_need == NeedType.RESOURCES:
            # Gather materials - ALWAYS available!
            # Agents can gather from global resource pools
            actions.append(Action(
                ActionType.GATHER_MATERIALS,
                priority=0.8
            ))

        elif urgent_need == NeedType.CREATIVITY:
            actions.append(Action(ActionType.CREATE_ART, priority=0.6))

        # ===== AUTONOMOUS ACTIONS - TRUE FREEDOM! =====
        # These are always available based on personality, not just urgent needs

        # EXPERIMENTATION - High openness + creativity agents love to discover!
        if self.personality.openness > 0.6 or self.personality.creativity > 0.6:
            # Check if agent has materials
            if len(self.inventory.items) >= 2:
                priority = (self.personality.openness + self.personality.creativity) / 2
                actions.append(Action(ActionType.EXPERIMENT, priority=priority * 0.7))

        # GATHERING MATERIALS - Proactive resource collection!
        # Agents with low inventory should gather materials for future use
        if len(self.inventory.items) < 15:  # Not at capacity
            # More conscientious agents gather more proactively
            priority = 0.5 + (self.personality.conscientiousness * 0.3)
            actions.append(Action(ActionType.GATHER_MATERIALS, priority=priority * 0.5))

        # ========== INTELLIGENT BUILDING WITH RESOURCE GATHERING ==========
        # Agents learn: "I need materials to build" → gather specific resources!

        # CRITICAL: If agent is already working on a building, CONTINUE building!
        if hasattr(self, 'active_construction_id') and self.active_construction_id:
            # High priority to finish what we started!
            priority = 0.85  # Very high - finish the job!
            actions.append(Action(ActionType.BUILD, priority=priority))
        else:
            # Check if we have urgent building needs (shelter, security, storage, etc.)
            building_needs = [
                (NeedType.SHELTER, 0.6),
                (NeedType.SECURITY, 0.7),
                (NeedType.RESOURCES, 0.5),
                (NeedType.CREATIVITY, 0.7),
                (NeedType.BELONGING, 0.6),
                (NeedType.ACHIEVEMENT, 0.7),
            ]

            has_building_need = any(
                self.needs.needs.get(need_type) and self.needs.needs[need_type].level > threshold
                for need_type, threshold in building_needs
            )

            if has_building_need:
                # Determine what materials we'd need for building
                total_building_materials = sum(
                    self.inventory.items.get(mat, 0)
                    for mat in ['wood', 'stone', 'clay', 'plant_fiber', 'metal_ore', 'iron_ore']
                )

                if total_building_materials >= 5:
                    # We have enough materials - BUILD!
                    priority = 0.6 + (self.personality.conscientiousness * 0.3)
                    actions.append(Action(ActionType.BUILD, priority=priority))
                else:
                    # NOT ENOUGH MATERIALS - Figure out what to gather!
                    # Agents learn: "I need wood → chop trees" or "I need stone → mine rocks"

                    wood_count = self.inventory.items.get('wood', 0)
                    stone_count = self.inventory.items.get('stone', 0)
                    clay_count = self.inventory.items.get('clay', 0)

                    # Prioritize gathering what we have LEAST of
                    if wood_count < 5:
                        # Need wood - CHOP TREES!
                        priority = 0.7  # High priority - need this to build
                        actions.append(Action(ActionType.CHOP_WOOD, priority=priority))

                    if stone_count < 5:
                        # Need stone - MINE ROCKS!
                        priority = 0.7
                        actions.append(Action(ActionType.MINE, priority=priority))

                    if clay_count < 3:
                        # Need clay - GATHER from ground
                        priority = 0.6
                        actions.append(Action(ActionType.GATHER_MATERIALS, priority=priority))

        # TEACHING - High agreeableness + empathy agents share knowledge!
        if self.personality.agreeableness > 0.6 or self.personality.empathy > 0.6:
            nearby = perceptions['nearby_agents']
            if nearby:
                target_id = random.choice([a['id'] for a in nearby])
                priority = (self.personality.agreeableness + self.personality.empathy) / 2
                actions.append(Action(
                    ActionType.TEACH,
                    target_agent=target_id,
                    priority=priority * 0.5
                ))

        # WRITING - High rationality + conscientiousness agents preserve knowledge!
        if self.personality.rationality > 0.7 and self.skills.get_skill('literacy') > 0.3:
            priority = self.personality.rationality * 0.7
            actions.append(Action(ActionType.WRITE, priority=priority * 0.5))

        # TRADING - Agents with resources might trade
        if self.wealth > 50 or len(self.inventory.items) > 5:
            nearby = perceptions['nearby_agents']
            if nearby:
                target_id = random.choice([a['id'] for a in nearby])
                actions.append(Action(
                    ActionType.TRADE,
                    target_agent=target_id,
                    priority=0.4
                ))

        # ========== FUN & ENTERTAINMENT - AGENTS NEED TO HAVE FUN! ==========
        # Low happiness or high boredom → seek fun activities!

        meaning_need = self.needs.needs.get(NeedType.MEANING)
        belonging_need = self.needs.needs.get(NeedType.BELONGING)
        achievement_need = self.needs.needs.get(NeedType.ACHIEVEMENT)
        creativity_need = self.needs.needs.get(NeedType.CREATIVITY)

        meaning_level = meaning_need.level if meaning_need else 0.5
        belonging_level = belonging_need.level if belonging_need else 0.5
        achievement_level = achievement_need.level if achievement_need else 0.5
        creativity_level = creativity_need.level if creativity_need else 0.5

        # 1. GAMBLING/DICE GAMES - When bored or seeking excitement!
        # High risk-takers with low happiness love to gamble
        if (meaning_level > 0.5 or self.personality.risk_taking > 0.6) and self.wealth > 10:
            nearby = perceptions['nearby_agents']
            if nearby:
                # Find other agents who might want to play
                gambling_priority = self.personality.risk_taking * 0.6
                if meaning_level > 0.6:  # Really bored
                    gambling_priority += 0.2

                target_id = random.choice([a['id'] for a in nearby])
                actions.append(Action(
                    ActionType.GAMBLE,
                    target_agent=target_id,
                    priority=gambling_priority
                ))

        # 2. GAMES & COMPETITIONS - Extraverted or competitive agents!
        # High extraversion or achievement need → organize/join games
        if (self.personality.extraversion > 0.6 or achievement_level > 0.6):
            nearby = perceptions['nearby_agents']
            if nearby and len(nearby) >= 1:  # Need at least one other agent
                game_priority = (self.personality.extraversion + achievement_level) / 2
                target_id = random.choice([a['id'] for a in nearby])
                actions.append(Action(
                    ActionType.PLAY_GAME,
                    target_agent=target_id,
                    priority=game_priority * 0.6
                ))

        # 3. CREATE ART - High creativity agents who are happy create MORE art!
        # (Not just when creativity is urgent need)
        if self.personality.creativity > 0.65 and creativity_level > 0.5:
            art_priority = self.personality.creativity * 0.8
            actions.append(Action(
                ActionType.CREATE_ART,
                priority=art_priority
            ))

        # 4. CELEBRATE - When really happy, organize parties!
        # High extraversion + happiness → throw celebrations
        if meaning_level < 0.3 and self.personality.extraversion > 0.7:  # Low happiness but extraverted
            # Organize celebration to boost mood
            actions.append(Action(
                ActionType.CELEBRATE,
                priority=0.7
            ))
        elif meaning_level < 0.4 and belonging_level > 0.6:
            # Need social connection, organize gathering
            actions.append(Action(
                ActionType.CELEBRATE,
                priority=0.6
            ))

        # 5. STORYTELLING - Share experiences with others
        # High agreeableness + extraversion = love to tell stories
        if (self.personality.agreeableness > 0.6 and self.personality.extraversion > 0.6):
            nearby = perceptions['nearby_agents']
            if nearby:
                target_id = random.choice([a['id'] for a in nearby])
                priority = (self.personality.agreeableness + self.personality.extraversion) / 2
                actions.append(Action(
                    ActionType.TELL_STORY,
                    target_agent=target_id,
                    priority=priority * 0.5
                ))

        # ROMANCE & REPRODUCTION - Agents with high SEX/ROMANCE needs seek partners!
        # This is ALWAYS available (not just when it's the most urgent need)
        sex_need = self.needs.needs.get(NeedType.SEX)
        romance_need = self.needs.needs.get(NeedType.ROMANCE)

        if (sex_need and sex_need.level > 0.6) or (romance_need and romance_need.level > 0.6):
            nearby = perceptions['nearby_agents']
            if nearby:
                # Seek romance with nearby agents
                for agent_info in nearby[:3]:  # Consider up to 3 nearby agents
                    # Priority based on how strong the needs are
                    sex_urgency = sex_need.level if sex_need else 0.0
                    romance_urgency = romance_need.level if romance_need else 0.0
                    priority = max(sex_urgency, romance_urgency) * 0.95  # Very high priority!

                    actions.append(Action(
                        ActionType.SEEK_ROMANCE,
                        target_agent=agent_info['id'],
                        priority=priority
                    ))

        # A full inventory can't take more materials; offering these would make
        # the agent fail the same gather every tick.
        if self.inventory.get_total_items() >= self.inventory.capacity:
            actions = [a for a in actions if a.action_type not in
                       (ActionType.GATHER_MATERIALS, ActionType.CHOP_WOOD, ActionType.MINE)]

        # Drop options the handler would reject right now (e.g. BUILD with no
        # unbuilt purpose or too few materials). The checks above use their own
        # thresholds, which don't match the handlers', so agents picked these
        # and failed the same action every tick.
        if can_run is not None:
            actions = [a for a in actions if a.action_type == ActionType.IDLE or can_run(a)]

        # Explore if nothing else to do
        if len(actions) <= 1:  # Only idle
            # Random exploration
            random_target = Position(
                self.location.x + random.uniform(-20, 20),
                self.location.y + random.uniform(-20, 20)
            )
            actions.append(Action(
                ActionType.EXPLORE,
                target_position=random_target,
                priority=0.4
            ))

        return actions

    def learn_from_outcome(self, action: Action, outcome: Dict):
        """
        Learn from the result of an action

        Updates skills, memories, and emotions using smart memory system
        """
        success = outcome.get('success', False)
        emotional_impact = outcome.get('emotional_impact', 0.0)

        # Determine memory importance based on action outcome
        importance = self._calculate_memory_importance(action, success, emotional_impact)

        # Determine memory type
        memory_type = self._determine_memory_type(action.action_type)

        # Add to smart memory system
        memory_content = f"{action.action_type.value}"
        if action.target_agent:
            memory_content += f" with agent {action.target_agent}"
        if success:
            memory_content += f" - SUCCESS"
        else:
            memory_content += f" - FAILED"

        self.memory.add_memory(
            content=memory_content,
            importance=importance,
            emotional_weight=emotional_impact,
            memory_type=memory_type,
            metadata={'action_type': action.action_type.value, 'outcome': 'action_outcome'}
        )

        # Update skill patterns (compressed knowledge)
        if success:
            skill_name = f"{action.action_type.value}"
            self.memory.update_skill_pattern(skill_name, success=True)
            # Also update SkillSet for backward compatibility
            self.skills.learn_skill(f"{skill_name}_skill", amount=0.05)
        else:
            self.memory.update_skill_pattern(action.action_type.value, success=False)

        # Update emotions based on outcome
        if emotional_impact > 0.5:
            self.emotions.trigger_emotion(EmotionType.JOY, emotional_impact * 0.5)
        elif emotional_impact < -0.5:
            self.emotions.trigger_emotion(EmotionType.SADNESS, abs(emotional_impact) * 0.5)

        # PERSONALITY EVOLUTION - Experiences shape who we become!
        self._evolve_personality(action, success, emotional_impact)

    def _calculate_memory_importance(self, action: Action, success: bool, emotional_impact: float) -> EventImportance:
        """Calculate importance level for memory storage"""
        # Life-changing events: MAJOR or LEGENDARY
        if action.action_type in [ActionType.GIVE_BIRTH, ActionType.MARRY, ActionType.HAVE_SEX]:
            return EventImportance.MAJOR

        # Significant achievements
        if action.action_type in [ActionType.BUILD_HOUSE, ActionType.INVENT, ActionType.DISCOVER]:
            return EventImportance.SIGNIFICANT

        # Important but not life-changing
        if abs(emotional_impact) > 0.7:
            return EventImportance.SIGNIFICANT

        # Notable events
        if abs(emotional_impact) > 0.4 or action.action_type in [ActionType.BUILD, ActionType.CRAFT, ActionType.TRADE]:
            return EventImportance.MINOR

        # Routine mundane actions (will decay quickly)
        return EventImportance.MUNDANE

    def _determine_memory_type(self, action_type: ActionType) -> MemoryType:
        """Determine memory type based on action"""
        # Emotional events
        if action_type in [ActionType.SEEK_ROMANCE, ActionType.MARRY, ActionType.SOCIALIZE, ActionType.CELEBRATE]:
            return MemoryType.EMOTIONAL

        # Skill-based actions
        if action_type in [ActionType.CRAFT, ActionType.BUILD, ActionType.HUNT, ActionType.GATHER_FOOD]:
            return MemoryType.PROCEDURAL

        # Knowledge and facts
        if action_type in [ActionType.LEARN_SKILL, ActionType.STUDY, ActionType.RESEARCH, ActionType.DISCOVER]:
            return MemoryType.SEMANTIC

        # Default to episodic
        return MemoryType.EPISODIC

    def _evolve_personality(self, action: Action, success: bool, emotional_impact: float):
        """
        Personality traits evolve slowly based on repeated experiences

        Traits change by tiny amounts (~0.001-0.005 per action) so evolution is gradual
        """
        if not success or abs(emotional_impact) < 0.1:
            return  # Only meaningful experiences shape personality

        # Small evolution rate - personality changes slowly over many experiences
        evolution_rate = 0.002

        # Different actions reinforce different traits
        if action.action_type in [ActionType.BUILD, ActionType.CRAFT, ActionType.WRITE]:
            # Successful creative/productive work increases conscientiousness
            self.personality.conscientiousness = min(1.0, self.personality.conscientiousness + evolution_rate)

        elif action.action_type in [ActionType.SOCIALIZE, ActionType.TEACH, ActionType.SEEK_ROMANCE]:
            # Social success increases extraversion and agreeableness
            self.personality.extraversion = min(1.0, self.personality.extraversion + evolution_rate)
            self.personality.agreeableness = min(1.0, self.personality.agreeableness + evolution_rate)

        elif action.action_type in [ActionType.EXPERIMENT, ActionType.EXPLORE]:
            # Exploration and experimentation increase openness
            self.personality.openness = min(1.0, self.personality.openness + evolution_rate)

        elif action.action_type in [ActionType.FIGHT, ActionType.STEAL]:
            # Conflict increases aggression, decreases agreeableness
            self.personality.aggression = min(1.0, self.personality.aggression + evolution_rate * 2)
            self.personality.agreeableness = max(0.0, self.personality.agreeableness - evolution_rate)

        elif action.action_type == ActionType.TRADE:
            # Successful trading increases openness and rationality
            self.personality.openness = min(1.0, self.personality.openness + evolution_rate)
            self.personality.rationality = min(1.0, self.personality.rationality + evolution_rate)

        # Negative experiences increase neuroticism slightly
        if emotional_impact < -0.3:
            self.personality.neuroticism = min(1.0, self.personality.neuroticism + evolution_rate)
        # Very positive experiences decrease neuroticism slightly
        elif emotional_impact > 0.6:
            self.personality.neuroticism = max(0.0, self.personality.neuroticism - evolution_rate)

    def to_dict(self) -> Dict:
        """Convert agent to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender.value,
            'location': {'x': self.location.x, 'y': self.location.y},
            'health': self.health,
            'energy': self.energy,
            'alive': self.alive,
            'wealth': self.wealth,
            'status': self.status,
            'current_action': self.current_action.action_type.value if self.current_action else None,
            'active_construction_id': self.active_construction_id,
            **self.work_life.to_dict(),
            'routine': self.routine.to_dict(),
            'dominant_emotion': self.emotions.get_dominant_emotion()[0].value,
            'mood': self.emotions.mood,
            'life_satisfaction': self.needs.get_overall_satisfaction(),
            'is_player': self.is_player,
            # Life Cycle data
            'life_stage': self.life_stage,
            'generation': getattr(self, 'generation', 1),
            # Know-how beyond what comes with being human (world/knowhow.py); None: everything
            'knowhow': sorted(self.knowhow) if getattr(self, 'knowhow', None) is not None else None,
            'mother_id': self.mother_id,
            'father_id': self.father_id,
            'children_ids': self.children_ids,
            'partner_id': self.partner_id,
            'home_id': getattr(self, 'home_id', None),
            'is_pregnant': self.is_pregnant,
            'pregnancy_partner_id': self.pregnancy_partner_id,
            'death_cause': self.death_cause,
            'death_tick': self.death_tick,
            # Psychology data
            'needs': {need.value: value.level for need, value in self.needs.needs.items()},
            'personality': {
                'openness': self.personality.openness,
                'conscientiousness': self.personality.conscientiousness,
                'extraversion': self.personality.extraversion,
                'agreeableness': self.personality.agreeableness,
                'neuroticism': self.personality.neuroticism,
                'risk_taking': self.personality.risk_taking,
                'aggression': self.personality.aggression,
                'sexuality': self.personality.sexuality,
                'ambition': self.personality.ambition,
                'creativity': self.personality.creativity,
                'empathy': self.personality.empathy,
                'rationality': self.personality.rationality,
            },
            'emotions': {emotion.value: intensity.intensity for emotion, intensity in self.emotions.emotions.items()},
            'skills': {name: skill.level for name, skill in self.skills.skills.items()},
            'inventory': {'items': self.inventory.items, 'capacity': self.inventory.capacity, 'total': self.inventory.get_total_items()},
            # Enhanced memory handling - support both MemorySystem and simple memory list
            'memories': self._serialize_memories(),
            # PURPOSEFUL ACTION DATA - Creates empire builders!
            'current_action_purpose': self.current_action_purpose,
            'recent_outcomes': self.recent_action_outcomes[-5:] if self.recent_action_outcomes else [],
            'decision_quality': sum(self.decision_quality_scores) / len(self.decision_quality_scores) * 100 if self.decision_quality_scores else 50.0,
            'life_trajectory': self._calculate_life_trajectory(),
            'purpose_clarity': self._calculate_purpose_clarity(),
        }

    def _serialize_memories(self) -> List[Dict]:
        """
        Enhanced memory serialization supporting SmartMemorySystem.
        Handles different memory backend implementations gracefully.
        """
        try:
            # Check if memory is SmartMemorySystem
            if hasattr(self.memory, 'get_recent_context'):
                # SmartMemorySystem - get recent memories
                recent = self.memory.get_recent_context(limit=20)

                return [
                    {
                        'event': mem.content,
                        'timestamp': mem.timestamp,
                        'emotional_impact': mem.emotional_weight,
                        'importance': mem.importance.name,
                        'memory_type': mem.memory_type.name if mem.memory_type else 'EPISODIC'
                    }
                    for mem in recent
                ]
            elif hasattr(self.memory, 'episodic_memory'):
                # Legacy MemorySystem with episodic_memory
                memories = self.memory.episodic_memory[-20:]
                return [
                    {
                        'event': mem.event_type,
                        'timestamp': mem.timestamp.isoformat() if hasattr(mem.timestamp, 'isoformat') else str(mem.timestamp),
                        'emotional_impact': mem.emotional_intensity,
                        'description': mem.description,
                        'importance': mem.importance if hasattr(mem, 'importance') else 0.5
                    }
                    for mem in memories
                ]
            elif hasattr(self.memory, 'memories'):
                # Old memory list format
                memories = list(self.memory.memories)[-20:]
                return [
                    {
                        'event': mem.event_type,
                        'timestamp': mem.timestamp.isoformat() if hasattr(mem.timestamp, 'isoformat') else str(mem.timestamp),
                        'emotional_impact': mem.emotional_impact if hasattr(mem, 'emotional_impact') else mem.emotional_intensity if hasattr(mem, 'emotional_intensity') else 0.5,
                        'description': f"{mem.event_type} at ({mem.location.x:.1f}, {mem.location.y:.1f})" if hasattr(mem, 'location') else mem.description
                    }
                    for mem in memories
                ]
            else:
                # No memory system or empty
                return []
        except Exception as e:
            # Fail gracefully - return empty list rather than breaking serialization
            logger.warning(f"Error serializing memories for agent {self.id}: {e}")
            return []

    def _calculate_life_trajectory(self) -> str:
        """Calculate if life is improving, declining, or stable"""
        if len(self.life_satisfaction_history) < 5:
            return "stable"

        # Simple linear regression on recent history
        recent = self.life_satisfaction_history[-10:]
        if len(recent) < 2:
            return "stable"

        # Compare first half to second half
        first_half = sum(recent[:len(recent)//2]) / (len(recent)//2)
        second_half = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)

        diff = second_half - first_half

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def _calculate_purpose_clarity(self) -> float:
        """
        How clear is their life purpose? (0-100)
        Based on meaning need - lower need = higher clarity
        """
        meaning_need = self.needs.needs.get(NeedType.MEANING)
        if not meaning_need:
            return 50.0

        # Inverse of meaning need level
        # Low need (satisfied) = high clarity
        # High need (unfulfilled) = low clarity
        clarity = (1.0 - meaning_need.level) * 100
        return clarity

    # ===== VALUE LEARNING SYSTEM =====
    # Agents learn item worth through trading - creating natural price discovery!

    def initialize_value_estimates(self, market_prices: Dict[str, float]):
        """
        Initialize rough value estimates for basic items.
        New agents have vague, personality-influenced guesses about item worth.
        """
        for item, true_value in market_prices.items():
            if item not in self.learned_values:
                # Start with rough estimate influenced by personality
                # Risk-takers overvalue, cautious agents undervalue
                personality_bias = (self.personality.risk_taking - 0.5) * 0.4  # -0.2 to +0.2
                randomness = random.uniform(-0.3, 0.3)  # ±30% error

                initial_estimate = true_value * (1.0 + personality_bias + randomness)
                initial_estimate = max(0.1, initial_estimate)  # Never zero

                self.learned_values[item] = initial_estimate
                self.value_confidence[item] = 0.1  # Very low confidence initially
                self.trade_count[item] = 0

    def get_estimated_value(self, item: str, market_price: float) -> float:
        """
        Get agent's current estimate of item value.
        Returns learned value if known, otherwise makes a personality-based guess.
        """
        if item in self.learned_values:
            return self.learned_values[item]

        # Never seen this item before - make an educated guess
        personality_bias = (self.personality.risk_taking - 0.5) * 0.4
        guess = market_price * (1.0 + personality_bias + random.uniform(-0.4, 0.4))

        # Initialize tracking
        self.learned_values[item] = max(0.1, guess)
        self.value_confidence[item] = 0.05  # Almost no confidence
        self.trade_count[item] = 0

        return self.learned_values[item]

    def learn_from_trade(self, item: str, trade_price: float, was_buyer: bool):
        """
        Update value estimate after completing a trade.
        Agents learn faster if trade was surprising (big price difference).

        Args:
            item: Item that was traded
            trade_price: Actual price in the trade
            was_buyer: True if agent bought (accepted price), False if sold
        """
        if item not in self.learned_values:
            # First trade with this item
            self.learned_values[item] = trade_price
            self.value_confidence[item] = 0.2  # Some confidence from real trade
            self.trade_count[item] = 1
            return

        # Calculate learning rate based on:
        # 1. Personality (open-minded learn faster)
        # 2. Current confidence (less confident = faster learning)
        # 3. Surprise factor (big difference = faster learning)

        base_learning_rate = 0.1 + (self.personality.openness * 0.2)  # 0.1-0.3
        confidence_modifier = 1.0 - (self.value_confidence[item] * 0.5)  # Less confident = learn faster

        current_estimate = self.learned_values[item]
        surprise = abs(trade_price - current_estimate) / max(current_estimate, 0.1)
        surprise_modifier = 1.0 + min(surprise, 1.0)  # More surprising = learn faster

        learning_rate = base_learning_rate * confidence_modifier * surprise_modifier
        learning_rate = min(learning_rate, 0.8)  # Cap at 80% learning rate

        # Update estimate (exponential moving average)
        self.learned_values[item] = (
            current_estimate * (1.0 - learning_rate) +
            trade_price * learning_rate
        )

        # Increase confidence with each trade (logarithmic growth)
        self.trade_count[item] += 1
        self.value_confidence[item] = min(0.95,
            0.1 + 0.85 * (self.trade_count[item] / (self.trade_count[item] + 10))
        )

    def get_value_confidence(self, item: str) -> float:
        """
        Get confidence in value estimate for item (0-1).
        Higher confidence = more trades experienced.
        """
        return self.value_confidence.get(item, 0.0)

    def should_accept_trade_price(
        self,
        item: str,
        price: float,
        market_price: float,
        is_buying: bool
    ) -> bool:
        """
        Decide if agent should accept a trade at given price.
        Based on learned value, confidence, and personality.

        Args:
            item: Item being traded
            price: Proposed price
            market_price: Current market price (for fallback)
            is_buying: True if buying, False if selling

        Returns:
            True if should accept trade, False otherwise
        """
        # Get estimated value and confidence
        estimated_value = self.get_estimated_value(item, market_price)
        confidence = self.get_value_confidence(item)

        # Calculate acceptable price range based on confidence and personality
        # Low confidence = wider acceptance range (willing to experiment)
        # High risk-taking = wider acceptance range (willing to gamble)

        base_tolerance = 0.3  # ±30% by default
        confidence_adjustment = confidence * 0.2  # More confident = stricter
        personality_adjustment = self.personality.risk_taking * 0.3  # Risk-takers more flexible

        tolerance = base_tolerance - confidence_adjustment + personality_adjustment
        tolerance = max(0.1, min(0.6, tolerance))  # 10%-60% range

        if is_buying:
            # Buying: accept if price is below (estimated_value * (1 + tolerance))
            max_acceptable = estimated_value * (1.0 + tolerance)
            return price <= max_acceptable
        else:
            # Selling: accept if price is above (estimated_value * (1 - tolerance))
            min_acceptable = estimated_value * (1.0 - tolerance)
            return price >= min_acceptable

    # ===== REPUTATION SYSTEM =====
    # Track trustworthiness in trading - good traders get better deals!

    def update_reputation_after_trade(
        self,
        other_agent_id: str,
        trade_price: float,
        fair_price: float,
        was_successful: bool
    ):
        """
        Update reputation after a trade attempt.

        Args:
            other_agent_id: ID of trading partner
            trade_price: Actual trade price
            fair_price: Fair market price
            was_successful: Whether trade completed
        """
        if was_successful:
            self.successful_trades += 1

            # Calculate trade fairness (how close to fair price)
            price_ratio = trade_price / max(fair_price, 0.1)
            # Ratio of 1.0 = perfectly fair
            # Ratio of 0.5 or 2.0 = very unfair

            if 0.8 <= price_ratio <= 1.2:
                # Fair trade! Boost reputation
                reputation_change = 0.05
            elif 0.6 <= price_ratio <= 1.4:
                # Somewhat fair
                reputation_change = 0.02
            else:
                # Unfair trade (exploited or got exploited)
                reputation_change = -0.03

            # Update global reputation (clamped to 0-1)
            self.trading_reputation = max(0.0, min(1.0,
                self.trading_reputation + reputation_change
            ))

            # Update reputation with specific agent
            if other_agent_id not in self.reputation_by_agent:
                self.reputation_by_agent[other_agent_id] = 0.5

            self.reputation_by_agent[other_agent_id] = max(0.0, min(1.0,
                self.reputation_by_agent[other_agent_id] + reputation_change * 2
            ))

        else:
            # Failed trade
            self.failed_trades += 1
            # Small penalty for failed negotiations
            self.trading_reputation = max(0.0, self.trading_reputation - 0.01)

    def get_reputation_with_agent(self, other_agent_id: str) -> float:
        """
        Get this agent's reputation from another agent's perspective.

        Returns:
            Reputation score 0-1 (0.5 = neutral/unknown)
        """
        # If they've traded before, use specific reputation
        if other_agent_id in self.reputation_by_agent:
            return self.reputation_by_agent[other_agent_id]

        # Otherwise use global reputation
        return self.trading_reputation

    def is_willing_to_trade_with(self, other_agent: 'Agent') -> bool:
        """
        Check if this agent is willing to trade with another based on reputation.

        Args:
            other_agent: The potential trading partner

        Returns:
            True if willing to trade, False if reputation too low
        """
        # Get other agent's reputation from our perspective
        # Note: We look at THEIR reputation stored in THEIR data
        # (since reputation is how others see you)
        their_reputation = other_agent.trading_reputation

        # Personality affects trust threshold
        # High agreeableness = more trusting, lower threshold
        # Low agreeableness = suspicious, higher threshold
        trust_threshold = 0.3 - (self.personality.agreeableness * 0.2)
        trust_threshold = max(0.1, trust_threshold)  # Minimum 0.1

        # Also check specific history with this agent
        if other_agent.id in self.reputation_by_agent:
            specific_rep = self.reputation_by_agent[other_agent.id]
            # Use worse of global and specific reputation
            their_reputation = min(their_reputation, specific_rep)

        return their_reputation >= trust_threshold

    def decay_reputation(self, decay_rate: float = 0.001):
        """
        Slowly decay reputation toward neutral (0.5) over time.
        People forget past behavior - need to maintain good reputation!

        Args:
            decay_rate: How fast reputation decays toward neutral (default 0.1%)
        """
        # Decay toward 0.5 (neutral)
        if self.trading_reputation > 0.5:
            self.trading_reputation = max(0.5,
                self.trading_reputation - decay_rate
            )
        elif self.trading_reputation < 0.5:
            self.trading_reputation = min(0.5,
                self.trading_reputation + decay_rate
            )

        # Decay per-agent reputations too
        for agent_id in list(self.reputation_by_agent.keys()):
            rep = self.reputation_by_agent[agent_id]
            if rep > 0.5:
                self.reputation_by_agent[agent_id] = max(0.5, rep - decay_rate)
            elif rep < 0.5:
                self.reputation_by_agent[agent_id] = min(0.5, rep + decay_rate)

            # Remove neutral reputations (forgotten)
            if abs(self.reputation_by_agent[agent_id] - 0.5) < 0.01:
                del self.reputation_by_agent[agent_id]
