"""
Emergent Roles System - Pure Behavioral Foundation

This is NOT a job system. This is a behavior pattern tracker.

How it works:
1. Track what agents ACTUALLY DO (action patterns)
2. When a pattern emerges (agent specializes), they DISCOVER they have a role
3. Agent NAMES their own role (generates custom title based on their language/culture)
4. Community learns the role name through observation
5. Role names can mutate, evolve, or be replaced

ZERO predefined job titles. Agents create their own occupational language.

Example emergence:
- Agent does lots of crafting with stone
- Pattern detected: "primary_crafting_stone"
- Agent generates name: "Stone-Maker" or "Rock-Shaper" or whatever they invent
- Others observe and learn the term
- Over time, might evolve to "Mason" or stay unique

Full autonomy. No interference.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import random
import zlib

# Actions that keep an agent alive but aren't work anyone specializes in
SELF_MAINTENANCE_ACTIONS = frozenset({'idle', 'wait', 'rest', 'sleep', 'eat', 'drink'})

# A share of recent actions (not counting self-maintenance) that makes a role,
# and the share below which it lapses: a role is what someone does now, not
# what they once did for a while
ROLE_SHARE = 0.30
ROLE_LAPSES_BELOW = 0.15


@dataclass
class BehaviorPattern:
    """
    A detected pattern in agent behavior.

    This is JUST the pattern - no name assigned yet!
    """
    pattern_type: str  # e.g., "primary_crafting", "frequent_building", "specialized_gathering"
    dominant_actions: List[str]  # What they actually do
    action_frequency: Dict[str, int]  # How often
    pattern_strength: float  # 0-1, how specialized

    # Context about the pattern
    primary_materials: List[str] = field(default_factory=list)  # What they work with
    primary_tools: List[str] = field(default_factory=list)  # What they use
    primary_locations: List[str] = field(default_factory=list)  # Where they work


@dataclass
class EmergentRole:
    """
    An agent-discovered, agent-named role.

    NOT assigned by system - CREATED by agent!
    """
    role_id: str
    agent_id: str

    # The behavior pattern that led to role emergence
    behavior_pattern: BehaviorPattern

    # AGENT-GENERATED NAME (not predefined!)
    custom_role_name: Optional[str] = None  # Agent creates this
    role_name_language: str = "unknown"  # What language/culture it's from

    # When and how it emerged
    emergence_date: datetime = field(default_factory=datetime.now)
    emergence_context: str = ""  # How did they realize this was their role?

    # Community recognition
    recognized_by: Set[str] = field(default_factory=set)  # Who knows this role exists
    name_adopters: Set[str] = field(default_factory=set)  # Who uses this role name
    recognition_strength: float = 0.0  # 0-1

    # Role authority/status (emerges from community respect)
    authority_level: float = 0.0  # 0-1, granted by community
    social_status_bonus: float = 0.0

    # Performance tracking
    times_acted_in_role: int = 0
    role_effectiveness: float = 0.5

    # Role evolution
    previous_names: List[str] = field(default_factory=list)  # Name history

    # Sim ticks (emergence_date is wall-clock): when it began, and when it
    # lapsed because they stopped doing it (None while it's theirs)
    started_tick: Optional[int] = None
    ended_tick: Optional[int] = None
    active: bool = True


class RoleEmergence:
    """
    Pure behavioral pattern observation system.

    NO job assignments. NO predefined titles.

    Agents discover patterns in their own behavior, name their roles,
    and share these names with their community.
    """

    def __init__(self):
        self.agent_roles: Dict[str, List[EmergentRole]] = {}

        # Behavior tracking
        self.agent_action_history: Dict[str, List[str]] = {}  # agent_id -> recent actions
        self.detected_patterns: Dict[str, List[BehaviorPattern]] = {}  # agent_id -> patterns

        # Role naming vocabulary (community-generated)
        self.role_vocabulary: Dict[str, int] = {}  # custom_role_name -> usage_count
        self.role_name_origins: Dict[str, str] = {}  # role_name -> creator_agent_id

        # Statistics
        self.total_roles_created: int = 0
        self.total_role_names_invented: int = 0

    def record_action(self, agent_id: str, action: str, context: Dict = None):
        """
        Record an agent's action for pattern detection.

        Context can include materials used, tools, location, etc.
        """
        # Looking after yourself isn't a specialization. Counting these made
        # "specialized_idle" every agent's role (named from the food-gathering
        # vocabulary, e.g. "Wandering Gatherer").
        if action in SELF_MAINTENANCE_ACTIONS:
            return

        if agent_id not in self.agent_action_history:
            self.agent_action_history[agent_id] = []

        # Keep last 100 actions for pattern detection
        self.agent_action_history[agent_id].append(action)
        if len(self.agent_action_history[agent_id]) > 100:
            self.agent_action_history[agent_id].pop(0)
        for role in self.agent_roles.get(agent_id, ()):
            if getattr(role, 'active', True) and action in role.behavior_pattern.dominant_actions:
                role.times_acted_in_role += 1

    def detect_behavior_patterns(self, agent_id: str) -> List[BehaviorPattern]:
        """
        Analyze agent's behavior to identify patterns.

        Returns detected patterns WITHOUT names - just pure behavior!
        """
        actions = self.agent_action_history.get(agent_id, [])

        if len(actions) < 15:
            return []  # Not enough data (lowered from 20 to 15)

        # Count action types
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1

        detected_patterns = []

        # Look for specialization patterns
        total_actions = len(actions)

        for action_type, count in action_counts.items():
            frequency = count / total_actions

            # Pattern detected if agent does this action often (ROLE_SHARE)
            if frequency >= ROLE_SHARE:
                pattern = BehaviorPattern(
                    pattern_type=f"specialized_{action_type}",
                    dominant_actions=[action_type],
                    action_frequency=action_counts,
                    pattern_strength=frequency
                )
                detected_patterns.append(pattern)

        # Look for combination patterns (e.g., "crafting + smelting")
        # This would detect things like blacksmithing without naming it

        self.detected_patterns[agent_id] = detected_patterns
        return detected_patterns

    def agent_discovers_role(
        self,
        agent_id: str,
        agent_name: str,
        pattern: BehaviorPattern,
        agent_generated_name: Optional[str] = None
    ) -> Optional[EmergentRole]:
        """
        Agent realizes they have a specialized role!

        They can NAME it themselves, or it can remain unnamed until they do.

        agent_generated_name: What the AGENT calls this role (not system-defined!)
        """

        # Check if agent already has this pattern as a role
        existing_roles = self.agent_roles.get(agent_id, [])
        for role in existing_roles:
            if role.behavior_pattern.pattern_type == pattern.pattern_type:
                return None  # Already discovered

        # Create emergent role (initially unnamed)
        role = EmergentRole(
            role_id=f"{agent_id}_{pattern.pattern_type}_{self.total_roles_created}",
            agent_id=agent_id,
            behavior_pattern=pattern,
            custom_role_name=agent_generated_name,
            emergence_date=datetime.now(),
            emergence_context=f"{agent_name} noticed they specialize in {', '.join(pattern.dominant_actions)}"
        )

        # Add to agent's roles
        if agent_id not in self.agent_roles:
            self.agent_roles[agent_id] = []

        self.agent_roles[agent_id].append(role)
        self.total_roles_created += 1

        # Track role name if provided
        if agent_generated_name:
            self.register_role_name(agent_generated_name, agent_id)

        return role

    def share(self, agent_id: str, action: str) -> float:
        """How much of what the agent has done lately (self-maintenance aside) is this."""
        actions = self.agent_action_history.get(agent_id, [])
        return actions.count(action) / len(actions) if actions else 0.0

    def review_roles(self, agent_id: str, tick: int) -> List[EmergentRole]:
        """Roles lapse when the agent has mostly stopped doing that work, and
        come back (with the name they gave it) if they take it up again.
        Returns the roles that lapsed."""
        lapsed = []
        for role in self.agent_roles.get(agent_id, ()):
            action = role.behavior_pattern.dominant_actions[0]
            now = self.share(agent_id, action)
            if getattr(role, 'active', True):
                role.behavior_pattern.pattern_strength = now
                if now < ROLE_LAPSES_BELOW:
                    role.active, role.ended_tick = False, tick
                    lapsed.append(role)
            elif now >= ROLE_SHARE:
                role.active, role.ended_tick = True, None
                role.behavior_pattern.pattern_strength = now
        return lapsed

    def agent_names_role(
        self,
        agent_id: str,
        role_id: str,
        custom_name: str,
        language: str = "agent_created"
    ) -> bool:
        """
        Agent gives a name to their role.

        This is THEIR creation - not a predefined title!

        Examples:
        - "Stone-Shaper" (agent invented this)
        - "Food-Finder" (their term for gatherer)
        - "Fire-Keeper" (their term for... fire keeper)
        - "Word-Maker" (their term for teacher/scholar)
        """
        roles = self.agent_roles.get(agent_id, [])

        for role in roles:
            if role.role_id == role_id:
                # Save old name if it had one
                if role.custom_role_name:
                    role.previous_names.append(role.custom_role_name)

                # Set new name
                role.custom_role_name = custom_name
                role.role_name_language = language

                # Register in vocabulary
                self.register_role_name(custom_name, agent_id)

                return True

        return False

    def register_role_name(self, role_name: str, creator_agent_id: str):
        """
        Register a new role name in the community vocabulary.

        Tracks who invented which role names.
        """
        if role_name not in self.role_vocabulary:
            self.role_vocabulary[role_name] = 0
            self.role_name_origins[role_name] = creator_agent_id
            self.total_role_names_invented += 1

        self.role_vocabulary[role_name] += 1

    def community_learns_role_name(
        self,
        observer_agent_id: str,
        role_holder_agent_id: str,
        role_name: str
    ) -> bool:
        """
        Another agent observes and learns a role name.

        This is how role vocabulary spreads!
        """
        roles = self.agent_roles.get(role_holder_agent_id, [])

        for role in roles:
            if role.custom_role_name == role_name:
                role.recognized_by.add(observer_agent_id)
                role.name_adopters.add(observer_agent_id)
                role.recognition_strength = min(1.0, len(role.recognized_by) / 10)

                # Increase vocabulary usage
                self.role_vocabulary[role_name] = self.role_vocabulary.get(role_name, 0) + 1

                return True

        return False

    def get_agent_primary_role(self, agent_id: str) -> Optional[EmergentRole]:
        """Get agent's most recognized role"""
        roles = self.agent_roles.get(agent_id, [])

        if not roles:
            return None

        # Return most recognized role
        return max(roles, key=lambda r: r.recognition_strength)

    def get_role_by_name(self, role_name: str) -> List[EmergentRole]:
        """Find all roles with this custom name"""
        matching_roles = []

        for agent_id, roles in self.agent_roles.items():
            for role in roles:
                if role.custom_role_name == role_name:
                    matching_roles.append(role)

        return matching_roles

    def get_statistics(self) -> Dict:
        """Get role emergence statistics"""

        total_roles = sum(len(roles) for roles in self.agent_roles.values())

        # Count named vs unnamed roles
        named_roles = 0
        unnamed_roles = 0
        for roles in self.agent_roles.values():
            for role in roles:
                if role.custom_role_name:
                    named_roles += 1
                else:
                    unnamed_roles += 1

        return {
            "total_roles_emerged": total_roles,
            "named_roles": named_roles,
            "unnamed_roles": unnamed_roles,
            "agents_with_roles": len(self.agent_roles),
            "unique_role_names_invented": len(self.role_vocabulary),
            "total_role_names_created": self.total_role_names_invented,
            "role_vocabulary": dict(sorted(
                self.role_vocabulary.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]),  # Top 20 role names
            "role_name_creators": self.role_name_origins,
        }

    def generate_agent_role_name(
        self,
        pattern: BehaviorPattern,
        agent_personality: Optional[Dict] = None,
        agent_recent_discoveries: Optional[List[str]] = None,
        agent_culture_context: Optional[Dict] = None,
        agent_seed: str = ""
    ) -> str:
        """
        Generate a meaningful, agent-driven role name.

        This creates names that reflect:
        - What the agent actually does (behavior)
        - Their personality and style
        - Recent discoveries or innovations they made
        - Cultural context and language evolution

        NOT just templates - these are culturally emergent names!
        """

        primary_action = pattern.dominant_actions[0] if pattern.dominant_actions else "work"

        # Base vocabularies for different action types
        # These feel more organic and varied
        action_vocabularies = {
            "gather_food": {
                "nouns": ["Gatherer", "Forager", "Seeker", "Harvester", "Collector", "Hunter", "Provider", "Finder"],
                "descriptors": ["Skilled", "Swift", "Keen", "Patient", "Tireless", "Wandering", "Far-seeing"],
                "materials": ["Plant", "Root", "Berry", "Herb", "Fruit", "Game", "Food"],
                "compounds": ["Food-Bringer", "Plant-Knower", "Forest-Walker", "Field-Tender", "Wild-Harvester"]
            },
            "experiment": {
                "nouns": ["Experimenter", "Discoverer", "Inventor", "Creator", "Innovator", "Alchemist", "Maker", "Thinker"],
                "descriptors": ["Curious", "Bold", "Clever", "Reckless", "Brilliant", "Mad", "Wise"],
                "materials": ["Fire", "Stone", "Metal", "Material", "Element", "Mixture"],
                "compounds": ["Fire-Tamer", "Stone-Mixer", "Material-Binder", "Element-Weaver", "Mystery-Solver"]
            },
            "build": {
                "nouns": ["Builder", "Architect", "Constructor", "Raiser", "Craftsperson", "Shaper", "Engineer"],
                "descriptors": ["Master", "Skilled", "Great", "Stone", "Wood", "Strong"],
                "materials": ["Stone", "Wood", "Clay", "Wall", "Foundation", "Structure"],
                "compounds": ["Wall-Raiser", "Stone-Layer", "Structure-Maker", "Shelter-Builder", "Foundation-Setter"]
            },
            "craft": {
                "nouns": ["Crafter", "Artisan", "Smith", "Shaper", "Former", "Maker", "Worker"],
                "descriptors": ["Skilled", "Master", "Fine", "Careful", "Precise", "Creative"],
                "materials": ["Stone", "Wood", "Metal", "Tool", "Object", "Craft"],
                "compounds": ["Tool-Maker", "Stone-Worker", "Hand-Crafter", "Object-Shaper", "Metal-Former"]
            },
            "teach": {
                "nouns": ["Teacher", "Scholar", "Guide", "Elder", "Mentor", "Keeper", "Sage", "Lorekeeper"],
                "descriptors": ["Wise", "Patient", "Ancient", "Knowing", "Learned", "Respected"],
                "materials": ["Knowledge", "Wisdom", "Lore", "Story", "Teaching", "Word"],
                "compounds": ["Knowledge-Keeper", "Wisdom-Sharer", "Story-Teller", "Lore-Holder", "Word-Weaver"]
            },
            "trade": {
                "nouns": ["Trader", "Merchant", "Dealer", "Exchanger", "Broker", "Negotiator"],
                "descriptors": ["Fair", "Shrewd", "Wealthy", "Traveling", "Silver-tongued", "Cunning"],
                "materials": ["Goods", "Wealth", "Treasure", "Trade", "Exchange"],
                "compounds": ["Trade-Master", "Goods-Exchanger", "Wealth-Builder", "Market-Maker", "Deal-Striker"]
            },
            "rest": {
                "nouns": ["Contemplator", "Dreamer", "Rester", "Thinker", "Watcher", "Observer"],
                "descriptors": ["Quiet", "Calm", "Peaceful", "Meditative", "Still", "Thoughtful"],
                "materials": ["Peace", "Silence", "Dream", "Thought", "Vision"],
                "compounds": ["Peace-Seeker", "Dream-Walker", "Thought-Keeper", "Silence-Holder"]
            },
            "socialize": {
                "nouns": ["Speaker", "Connector", "Diplomat", "Friend-Maker", "Talker", "Mediator"],
                "descriptors": ["Friendly", "Charismatic", "Warm", "Social", "Beloved", "Popular"],
                "materials": ["People", "Friends", "Community", "Bond", "Connection"],
                "compounds": ["People-Bringer", "Bond-Maker", "Community-Builder", "Friend-Keeper", "Heart-Connector"]
            },
            "write": {
                "nouns": ["Scribe", "Writer", "Recorder", "Chronicler", "Author", "Documenter"],
                "descriptors": ["Careful", "Precise", "Learned", "Patient", "Dedicated"],
                "materials": ["Word", "Record", "Document", "Story", "History", "Mark"],
                "compounds": ["Word-Marker", "Story-Recorder", "History-Keeper", "Mark-Maker", "Document-Writer"]
            },
            # Common work that used to fall back to the food-gathering words
            # (gather_materials agents were called "Food-Harvester").
            "gather_materials": {
                "nouns": ["Quarrier", "Woodcutter", "Hauler", "Gatherer", "Provisioner", "Digger"],
                "descriptors": ["Strong", "Tireless", "Steady", "Hardy", "Skilled"],
                "materials": ["Stone", "Wood", "Clay", "Fiber", "Timber"],
                "compounds": ["Stone-Hauler", "Wood-Cutter", "Clay-Digger", "Timber-Bringer", "Fiber-Twister"]
            },
            "gather_water": {
                "nouns": ["Water-Carrier", "Bearer", "Well-Keeper", "Drawer"],
                "descriptors": ["Steady", "Faithful", "Tireless", "Patient"],
                "materials": ["Water", "Spring", "River", "Well"],
                "compounds": ["Water-Bearer", "Spring-Finder", "River-Walker", "Well-Tender"]
            },
            "explore": {
                "nouns": ["Scout", "Explorer", "Pathfinder", "Wanderer", "Ranger"],
                "descriptors": ["Far-roaming", "Bold", "Restless", "Keen-eyed"],
                "materials": ["Trail", "Horizon", "Land", "Path"],
                "compounds": ["Path-Finder", "Land-Walker", "Trail-Blazer", "Horizon-Seeker"]
            },
            "tell_story": {
                "nouns": ["Storyteller", "Bard", "Teller", "Singer", "Entertainer"],
                "descriptors": ["Lively", "Beloved", "Wise", "Merry", "Spellbinding"],
                "materials": ["Tale", "Song", "Legend", "Story"],
                "compounds": ["Tale-Spinner", "Song-Keeper", "Story-Weaver", "Legend-Teller"]
            },
            "create_art": {
                "nouns": ["Artist", "Painter", "Carver", "Artisan", "Sculptor"],
                "descriptors": ["Inspired", "Gifted", "Dreaming", "Bold"],
                "materials": ["Color", "Stone", "Image", "Form"],
                "compounds": ["Image-Maker", "Stone-Carver", "Color-Weaver", "Form-Shaper"]
            },
            "heal": {
                "nouns": ["Healer", "Mender", "Herbalist", "Caregiver"],
                "descriptors": ["Gentle", "Wise", "Patient", "Kind"],
                "materials": ["Herb", "Remedy", "Wound", "Life"],
                "compounds": ["Wound-Mender", "Herb-Healer", "Life-Keeper", "Fever-Breaker"]
            }
        }

        action_vocabularies.update(LIFE_VOCABULARIES)

        # The vocabulary for this action, or one whose name it contains
        # (build -> build_temple). Work with no vocabulary used to take the
        # food-gathering words, so a suitor was called "Harvester"; now it's
        # named for what they do ("One-Who-Dances-Wildly").
        action = primary_action.lower()
        vocab = action_vocabularies.get(action) or next(
            (v for key, v in action_vocabularies.items() if key in action), None)
        if not vocab:
            return one_who(action)

        # Names come from the agent's own draw, not the world's dice: naming a
        # role doesn't change what happens next
        random = _NameDice(agent_seed, primary_action)

        # Decide on naming style (creates variety)
        style_roll = random.random()

        if style_roll < 0.3:
            # Simple noun (e.g., "Gatherer", "Builder")
            return random.choice(vocab["nouns"])

        elif style_roll < 0.6:
            # Descriptor + Noun (e.g., "Skilled Gatherer", "Master Builder")
            descriptor = random.choice(vocab["descriptors"])
            noun = random.choice(vocab["nouns"])
            return f"{descriptor} {noun}"

        elif style_roll < 0.85:
            # Compound name (e.g., "Food-Bringer", "Stone-Worker")
            return random.choice(vocab["compounds"])

        else:
            # Material-based compound (e.g., "Stone Shaper", "Plant Keeper")
            material = random.choice(vocab["materials"])
            noun = random.choice(vocab["nouns"])
            separator = "-" if random.random() < 0.5 else " "
            return f"{material}{separator}{noun}"


# Words for what people commonly spend their days on besides the trades above
LIFE_VOCABULARIES = {
    "seek_romance": {"nouns": ["Suitor", "Admirer", "Sweetheart", "Wooer"],
                     "descriptors": ["Ardent", "Hopeful", "Tender", "Devoted"],
                     "materials": ["Heart", "Love", "Flower"],
                     "compounds": ["Heart-Seeker", "Love-Seeker", "Flower-Giver"]},
    "care_for_child": {"nouns": ["Child-Minder", "Nurturer", "Carer", "Guardian"],
                       "descriptors": ["Gentle", "Watchful", "Loving", "Patient"],
                       "materials": ["Child", "Cradle", "Hearth"],
                       "compounds": ["Cradle-Keeper", "Child-Raiser", "Hearth-Keeper"]},
    "attend_event": {"nouns": ["Reveller", "Guest", "Feast-Goer", "Merrymaker"],
                     "descriptors": ["Eager", "Merry", "Faithful", "Lively"],
                     "materials": ["Feast", "Gathering", "Festival"],
                     "compounds": ["Feast-Goer", "Gathering-Goer", "Dance-Joiner"]},
    "organize_event": {"nouns": ["Host", "Feast-Giver", "Gatherer of People"],
                       "descriptors": ["Generous", "Open-handed", "Lively"],
                       "materials": ["Feast", "Festival", "Gathering"],
                       "compounds": ["Feast-Giver", "Fire-Circle-Caller", "People-Gatherer"]},
    "play_game": {"nouns": ["Player", "Game-Lover", "Jester"],
                  "descriptors": ["Playful", "Merry", "Quick"],
                  "materials": ["Game", "Dice", "Ball"],
                  "compounds": ["Game-Player", "Fun-Maker", "Laughter-Bringer"]},
    "patrol": {"nouns": ["Watcher", "Guard", "Sentinel", "Warden"],
               "descriptors": ["Vigilant", "Steady", "Night", "Wakeful"],
               "materials": ["Border", "Night", "Fire"],
               "compounds": ["Night-Walker", "Border-Watcher", "Fire-Guard"]},
    "try_for_child": {"nouns": ["Family-Maker", "Parent-to-be"],
                      "descriptors": ["Hopeful", "Loving"],
                      "materials": ["Family", "Cradle"],
                      "compounds": ["Family-Builder", "Cradle-Hoper"]},
    "worship": {"nouns": ["Devotee", "Worshipper", "Believer"],
                "descriptors": ["Pious", "Faithful", "Devout"],
                "materials": ["Spirit", "Shrine", "Prayer"],
                "compounds": ["Spirit-Speaker", "Shrine-Keeper", "Prayer-Sayer"]},
    "share_faith": {"nouns": ["Preacher", "Witness", "Messenger"],
                    "descriptors": ["Zealous", "Earnest", "Wandering"],
                    "materials": ["Faith", "Word", "Spirit"],
                    "compounds": ["Faith-Bringer", "Word-Spreader"]},
    "farm": {"nouns": ["Farmer", "Grower", "Tiller", "Planter"],
             "descriptors": ["Patient", "Hardworking", "Green-handed"],
             "materials": ["Field", "Grain", "Seed", "Soil"],
             "compounds": ["Field-Tender", "Seed-Sower", "Grain-Grower"]},
    "plant": {"nouns": ["Planter", "Sower", "Grower"],
              "descriptors": ["Patient", "Careful"],
              "materials": ["Seed", "Field", "Garden"],
              "compounds": ["Seed-Sower", "Garden-Keeper"]},
    "hunt": {"nouns": ["Hunter", "Tracker", "Stalker"],
             "descriptors": ["Keen", "Swift", "Silent"],
             "materials": ["Game", "Deer", "Boar"],
             "compounds": ["Game-Tracker", "Spear-Thrower"]},
    "fish": {"nouns": ["Fisher", "Netter"],
             "descriptors": ["Patient", "Quiet"],
             "materials": ["River", "Lake", "Net"],
             "compounds": ["Net-Caster", "River-Fisher"]},
    "chop_wood": {"nouns": ["Woodcutter", "Feller", "Axe-Bearer"],
                  "descriptors": ["Strong", "Tireless"],
                  "materials": ["Wood", "Timber", "Log"],
                  "compounds": ["Tree-Feller", "Wood-Cutter"]},
    "mine": {"nouns": ["Miner", "Digger", "Quarrier"],
             "descriptors": ["Hardy", "Deep", "Strong"],
             "materials": ["Stone", "Ore", "Rock"],
             "compounds": ["Ore-Digger", "Stone-Breaker"]},
    "govern": {"nouns": ["Chief", "Leader", "Elder"],
               "descriptors": ["Wise", "Firm", "Respected"],
               "materials": ["Council", "Law", "People"],
               "compounds": ["Law-Giver", "People-Leader"]},
    "make_law": {"nouns": ["Lawgiver", "Lawmaker"],
                 "descriptors": ["Stern", "Fair", "Wise"],
                 "materials": ["Law", "Rule"],
                 "compounds": ["Law-Giver", "Rule-Maker"]},
    "give_gift": {"nouns": ["Giver", "Benefactor"],
                  "descriptors": ["Generous", "Open-handed", "Kind"],
                  "materials": ["Gift", "Bounty"],
                  "compounds": ["Gift-Giver", "Bounty-Sharer"]},
}


def one_who(action: str) -> str:
    """A plain name for someone known by what they do: attend_event ->
    'One-Who-Attends-Event'."""
    words = [w for w in action.lower().split('_') if w]
    if not words:
        return "One-Who-Works"
    verb = words[0]
    if verb.endswith('y') and verb[-2:-1] not in 'aeiou':
        verb = verb[:-1] + 'ies'
    elif verb.endswith(('s', 'sh', 'ch', 'x', 'z')):
        verb += 'es'
    else:
        verb += 's'
    return '-'.join(['One', 'Who', verb.capitalize()] + [w.capitalize() for w in words[1:]])


class _NameDice(random.Random):
    """The dice one agent names one role with: the same every time."""

    def __init__(self, agent_seed: str, action: str):
        super().__init__(zlib.crc32(f"{agent_seed}:{action}".encode()))
