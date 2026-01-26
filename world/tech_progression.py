"""
Technology Progression Tracker - Civilization Ages

Tracks civilization's progression through technological eras:
- Stone Age → Bronze Age → Iron Age → Medieval → Industrial → Modern → Space Age

NO predetermined tech tree - progression EMERGES from discoveries!

Milestones emerge organically when agents discover key technologies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from datetime import datetime


@dataclass
class TechnologyEra:
    """A technological era"""
    era_name: str
    achieved_date: Optional[datetime] = None
    key_discoveries: List[str] = field(default_factory=list)
    is_achieved: bool = False


class TechProgressionTracker:
    """
    Tracks technological progression of civilization.

    Eras emerge from actual discoveries, not predetermined paths!
    """

    def __init__(self):
        self.current_era = "Stone Age"
        self.eras_achieved: List[TechnologyEra] = []

        # Define era milestones (what needs to be discovered)
        self.era_requirements = {
            "Stone Age": {
                "required_discoveries": ["fire", "stone_tool", "sharp_stone"],
                "required_count": 1  # Just need one
            },
            "Bronze Age": {
                "required_discoveries": ["bronze", "refined_metal", "metal_tool", "pottery"],
                "required_count": 2  # Need metalworking + pottery
            },
            "Iron Age": {
                "required_discoveries": ["iron", "steel", "iron_tool", "advanced_forge"],
                "required_count": 2
            },
            "Medieval": {
                "required_discoveries": ["castle", "cathedral", "mill", "written_law"],
                "required_count": 2
            },
            "Industrial": {
                "required_discoveries": ["steam", "factory", "rail", "electricity"],
                "required_count": 2
            },
            "Modern": {
                "required_discoveries": ["electronics", "computer", "automobile", "aircraft"],
                "required_count": 2
            },
            "Space Age": {
                "required_discoveries": ["rocket", "satellite", "spacecraft", "launch_platform"],
                "required_count": 2
            }
        }

    def check_discoveries(self, all_discoveries: Set[str]) -> Optional[str]:
        """
        Check if new era has been achieved.

        Returns era name if new era reached, None otherwise.
        """

        era_order = [
            "Stone Age",
            "Bronze Age",
            "Iron Age",
            "Medieval",
            "Industrial",
            "Modern",
            "Space Age"
        ]

        # Check each era in order
        for era_name in era_order:
            if era_name == self.current_era:
                # Check if ready for next era
                next_index = era_order.index(era_name) + 1
                if next_index < len(era_order):
                    next_era = era_order[next_index]

                    if self._check_era_requirements(next_era, all_discoveries):
                        # NEW ERA ACHIEVED!
                        self.current_era = next_era

                        era = TechnologyEra(
                            era_name=next_era,
                            achieved_date=datetime.now(),
                            is_achieved=True
                        )
                        self.eras_achieved.append(era)

                        return next_era

        return None

    def _check_era_requirements(self, era_name: str, discoveries: Set[str]) -> bool:
        """Check if requirements for era are met"""

        requirements = self.era_requirements.get(era_name, {})
        required_discoveries = requirements.get("required_discoveries", [])
        required_count = requirements.get("required_count", 1)

        # Count how many required discoveries are present
        found = sum(
            1 for req in required_discoveries
            if any(req in disc for disc in discoveries)  # Fuzzy match
        )

        return found >= required_count

    def analyze_discovery(self, discovery_name: str) -> Dict:
        """
        Analyze what a discovery might unlock.

        Returns potential impacts.
        """

        impacts = {
            "era_progress": self._calculate_era_progress(discovery_name),
            "is_breakthrough": self._is_breakthrough(discovery_name),
            "unlocks": self._what_does_it_unlock(discovery_name)
        }

        return impacts

    def _calculate_era_progress(self, discovery_name: str) -> float:
        """How much does this discovery progress toward next era?"""

        # Get next era requirements
        era_order = ["Stone Age", "Bronze Age", "Iron Age", "Medieval", "Industrial", "Modern", "Space Age"]
        current_index = era_order.index(self.current_era)

        if current_index >= len(era_order) - 1:
            return 1.0  # Already at max

        next_era = era_order[current_index + 1]
        requirements = self.era_requirements.get(next_era, {})
        required_discoveries = requirements.get("required_discoveries", [])

        # Check if this discovery is required
        if any(req in discovery_name for req in required_discoveries):
            return 1.0 / requirements.get("required_count", 1)

        return 0.0

    def _is_breakthrough(self, discovery_name: str) -> bool:
        """Is this a breakthrough discovery?"""

        breakthroughs = [
            "fire", "wheel", "writing", "bronze", "iron", "steel",
            "printing", "steam", "electricity", "computer", "rocket"
        ]

        return any(bt in discovery_name.lower() for bt in breakthroughs)

    def _what_does_it_unlock(self, discovery_name: str) -> List[str]:
        """What possibilities does this discovery open?"""

        unlocks_map = {
            "fire": ["cooking", "metalworking", "pottery"],
            "pottery": ["storage", "cooking_vessels"],
            "bronze": ["better_tools", "weapons", "armor"],
            "iron": ["advanced_tools", "construction"],
            "steel": ["skyscrapers", "rails", "machinery"],
            "writing": ["libraries", "laws", "history"],
            "steam": ["factories", "trains", "industrialization"],
            "electricity": ["motors", "lights", "computers"],
            "computer": ["automation", "internet", "AI"],
            "rocket": ["satellites", "space_travel", "mars_mission"]
        }

        for key, unlocks in unlocks_map.items():
            if key in discovery_name.lower():
                return unlocks

        return []

    def get_statistics(self) -> Dict:
        """Get progression statistics"""

        return {
            "current_era": self.current_era,
            "eras_achieved": len(self.eras_achieved),
            "era_history": [
                {
                    "era": era.era_name,
                    "achieved": era.achieved_date.isoformat() if era.achieved_date else None
                }
                for era in self.eras_achieved
            ],
            "progress_to_next": self._calculate_next_era_progress()
        }

    def _calculate_next_era_progress(self) -> float:
        """Calculate % progress toward next era"""
        # Would need to check current discoveries
        # Placeholder for now
        return 0.0
