"""
The AI brain's menu of actions, and how its answers are read.

The menu is generated from the same things the engine uses to run actions:
every ActionType that a handler runs, directly or through
UNHANDLED_ACTION_FALLBACKS. So the brain can never be offered something the
engine can't do, and nothing the engine can do is left off. Aliases ("gossip"
runs socialize) are listed next to the action they run, to keep the prompt
compact without dropping any word an agent might use.

The answer format is strict:

    ACTION: <an action name from the menu>
    TARGET: <a person's name, or none>
    DETAILS: <optional>
    REASON: <one short sentence>

and parsing is forgiving about formatting (markdown, quotes, case, spaces
instead of underscores) but never guesses: if no listed action name is in the
ACTION line, it is a parse failure and the caller falls back to the
rule-based brain.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

# Not offered: an agent does these by default or as a bodily event, not by choice.
INTERNAL_ACTIONS = frozenset({"idle", "wait", "give_birth"})

CATEGORIES = [
    "survival", "health", "building", "crafting and invention", "knowledge",
    "social", "romance and family", "culture", "economy", "politics and land",
    "religion", "conflict",
]

# canonical action -> (category, a few words). Actions missing here still go
# on the menu (under "other"), so nothing the engine can run is ever dropped.
ACTION_INFO = {
    "eat": ("survival", "eat food you carry"),
    "drink": ("survival", "drink water you carry"),
    "rest": ("survival", "rest or sleep"),
    "gather_food": ("survival", "pick wild food"),
    "gather_water": ("survival", "fetch water"),
    "hunt": ("survival", "hunt animals for food"),
    "plant_crops": ("survival", "plant seeds you carry"),
    "tend_crops": ("survival", "look after planted crops"),
    "harvest": ("survival", "harvest ripe crops"),
    "raise_animals": ("survival", "keep animals"),
    "explore": ("survival", "look around new places"),
    "move": ("survival", "walk somewhere"),
    "heal": ("health", "treat someone who is sick (TARGET)"),
    "cure": ("health", "cure someone's illness (TARGET)"),
    "diagnose": ("health", "find out what ails someone (TARGET)"),
    "gather_materials": ("building", "collect wood, stone, clay or fiber"),
    "chop_wood": ("building", "cut wood"),
    "mine": ("building", "dig stone or ore"),
    "build": ("building", "build a home, workshop, store or hall"),
    "experiment": ("crafting and invention", "combine materials to discover things"),
    "smelt_ore": ("crafting and invention", "smelt ore into metal"),
    "refine_material": ("crafting and invention", "refine a raw material"),
    "create_alloy": ("crafting and invention", "make an alloy"),
    "perform_chemistry": ("crafting and invention", "try a chemical process"),
    "discover_element": ("crafting and invention", "research new elements"),
    "discover_material": ("crafting and invention", "research new materials"),
    "discover_energy": ("crafting and invention", "look for new energy sources"),
    "build_power_plant": ("crafting and invention", "build a power plant"),
    "operate_power_plant": ("crafting and invention", "run a power plant"),
    "teach": ("knowledge", "teach someone what you know (TARGET)"),
    "write": ("knowledge", "write down what you know"),
    "socialize": ("social", "spend time with someone (TARGET)"),
    "seek_romance": ("romance and family", "court someone you're drawn to (TARGET)"),
    "celebrate": ("culture", "throw or join a celebration"),
    "tell_story": ("culture", "tell someone a story (TARGET)"),
    "play_game": ("culture", "play a game with someone (TARGET)"),
    "create_art": ("culture", "make art"),
    "gamble": ("culture", "bet with someone (TARGET)"),
    "trade": ("economy", "trade with someone (TARGET)"),
    "mint_coins": ("economy", "make coins from ore"),
    "open_bank": ("economy", "open a bank"),
    "apply_for_loan": ("economy", "borrow from a bank"),
    "send_caravan": ("economy", "send goods to trade far away"),
    "join_tax_revolt": ("economy", "protest taxes"),
    "govern": ("politics and land", "found or lead a government"),
    "make_law": ("politics and land", "propose a law (DETAILS: what it says)"),
    "vote": ("politics and land", "vote on a law or in an election (DETAILS: yes or no)"),
    "claim_territory": ("politics and land", "claim land as yours"),
    "guard": ("politics and land", "guard your land"),
    "patrol": ("politics and land", "patrol your land"),
    "pray": ("religion", "pray"),
    "worship": ("religion", "worship with your faith"),
    "perform_ritual": ("religion", "lead a ritual"),
    "build_temple": ("religion", "build a temple"),
    "fight": ("conflict", "fight someone (TARGET)"),
}


@dataclass
class MenuEntry:
    action: str
    description: str
    aliases: List[str] = field(default_factory=list)


@dataclass
class ActionMenu:
    by_category: Dict[str, List[MenuEntry]]
    names: Set[str]        # every name the brain may answer with (actions and aliases)
    text: str              # the menu as it appears in the prompt


def build_menu(registry, fallbacks: Dict[str, str]) -> ActionMenu:
    """Build the menu from the handler registry and the alias table."""
    from agents.agent import ActionType

    entries: Dict[str, MenuEntry] = {}
    alias_of: Dict[str, str] = {}
    for action_type in ActionType:
        name = action_type.value
        if name in INTERNAL_ACTIONS:
            continue
        if registry.get_handler(action_type) is not None:
            category, words = ACTION_INFO.get(name, ("other", ""))
            entries.setdefault(name, MenuEntry(name, words))
        else:
            target = fallbacks.get(name)
            if target and registry.get_handler(ActionType(target)) is not None:
                alias_of[name] = target
    for alias, target in alias_of.items():
        if target not in entries:  # an alias whose action is itself internal
            entries[target] = MenuEntry(target, ACTION_INFO.get(target, ("other", ""))[1])
        entries[target].aliases.append(alias)

    by_category: Dict[str, List[MenuEntry]] = {}
    for entry in entries.values():
        category = ACTION_INFO.get(entry.action, ("other", ""))[0]
        by_category.setdefault(category, []).append(entry)

    lines = []
    for category in CATEGORIES + sorted(set(by_category) - set(CATEGORIES)):
        if category not in by_category:
            continue
        lines.append(f"{category.capitalize()}:")
        for entry in by_category[category]:
            also = f" [also {', '.join(entry.aliases)}]" if entry.aliases else ""
            words = f" - {entry.description}" if entry.description else ""
            lines.append(f" {entry.action}{words}{also}")
    names = set(entries) | set(alias_of)
    return ActionMenu(by_category=by_category, names=names, text="\n".join(lines))


RESPONSE_FORMAT = """Answer in exactly this format:
ACTION: <one action name from the list, written exactly>
TARGET: <a person's name, or none>
DETAILS: <optional: e.g. what a law says, or yes/no for a vote>
REASON: <one short sentence>"""


# ---------------------------------------------------------------------------
# Parsing the brain's answer
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    action: str
    target_id: Optional[str] = None
    details: str = ""
    reason: str = ""


def _field(text: str, label: str) -> Optional[str]:
    """Value of a 'LABEL: value' line, tolerating markdown and odd spacing."""
    match = re.search(rf"^[\s*_#>`-]*{label}[\s*_`]*[:=]\s*(.+?)\s*$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip(" *_`\"'[]<>.") if match else None


def _action_name(value: str, valid: Set[str]) -> Optional[str]:
    normalized = re.sub(r"[\s\-]+", "_", value.strip().lower())
    normalized = normalized.strip("_*`\"'[]<>.()")
    if normalized in valid:
        return normalized
    # The value may carry extra words ("build_temple for my faith", "make law
    # against theft"). Take the longest listed name that appears as a whole
    # word, written with underscores or spaces, so build_temple wins over build.
    # Underscores count as part of a word, so "eat" never matches inside
    # "create_art".
    spaced = value.strip().lower()
    found = [name for name in valid
             if re.search(rf"(?<![a-z_]){re.escape(name)}(?![a-z_])", spaced)
             or re.search(rf"(?<![a-z_]){re.escape(name.replace('_', ' '))}(?![a-z_])", spaced)]
    return max(found, key=len) if found else None


def parse_decision(text: str, valid: Set[str], people_by_name: Dict[str, str]) -> Optional[Decision]:
    """Read an answer in RESPONSE_FORMAT. Returns None if no listed action is named."""
    if not text:
        return None
    value = _field(text, "ACTION")
    if value is None:
        return None
    action = _action_name(value, valid)
    if action is None:
        return None

    target_id = None
    target = _field(text, "TARGET")
    if target and target.lower() not in ("none", "nobody", "no one", "-", "n/a", "myself", "self"):
        lowered = target.lower()
        target_id = people_by_name.get(lowered) or people_by_name.get(lowered.split()[0])
    return Decision(action=action, target_id=target_id,
                    details=_field(text, "DETAILS") or "", reason=_field(text, "REASON") or "")
