"""
ACHIEVEMENT SYSTEM - Track Epic Moments & Milestones

Every agent can earn achievements that define their legacy.
Every civilization can unlock milestones that mark progress.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from datetime import datetime
from enum import Enum


class AchievementType(Enum):
    """Types of achievements"""
    # Personal Achievements
    FIRST_BUILDER = "first_builder"  # Built first building ever
    MASTER_BUILDER = "master_builder"  # Built 10+ buildings
    LEGENDARY_BUILDER = "legendary_builder"  # Built 50+ buildings
    
    FIRST_DISCOVERER = "first_discoverer"  # First discovery
    KNOWLEDGE_SEEKER = "knowledge_seeker"  # Learned 10+ skills
    
    SURVIVOR = "survivor"  # Survived 100 days
    ELDER = "elder"  # Lived to 70+
    ANCIENT_ONE = "ancient_one"  # Lived to 90+
    
    BELOVED = "beloved"  # Had 10+ strong relationships
    PARENT = "parent"  # Had first child
    DYNASTY_FOUNDER = "dynasty_founder"  # Had 5+ children
    PATRIARCH = "patriarch"  # Had 10+ descendants
    
    WEALTHY = "wealthy"  # Accumulated 100+ wealth
    TYCOON = "tycoon"  # Accumulated 500+ wealth
    
    WARRIOR = "warrior"  # Won first conflict
    CHAMPION = "champion"  # Won 10+ conflicts
    
    ARTIST = "artist"  # Created 10+ artworks
    INVENTOR = "inventor"  # Made 5+ discoveries
    
    # Civilization Achievements  
    FIRST_BIRTH = "first_birth"  # First baby born in civilization
    POPULATION_10 = "population_10"
    POPULATION_50 = "population_50"
    POPULATION_100 = "population_100"
    
    FIRST_DEATH = "first_death"
    FIRST_WAR = "first_war"
    FIRST_GOVERNMENT = "first_government"
    
    BRONZE_AGE = "bronze_age"
    IRON_AGE = "iron_age"
    RENAISSANCE = "renaissance"


@dataclass
class Achievement:
    """A single achievement"""
    achievement_type: AchievementType
    name: str
    description: str
    icon: str
    unlocked_at: datetime
    day: int
    agent_id: Optional[str] = None  # None for civilization achievements


@dataclass
class AgentAchievements:
    """Track all achievements for an agent"""
    agent_id: str
    agent_name: str
    achievements: List[Achievement] = field(default_factory=list)
    
    # Stats for achievement tracking
    buildings_built: int = 0
    discoveries_made: int = 0
    children_count: int = 0
    relationships_count: int = 0
    conflicts_won: int = 0
    artworks_created: int = 0
    max_wealth: float = 0.0
    days_survived: int = 0
    
    def check_and_award(self, current_day: int) -> List[Achievement]:
        """Check if agent earned new achievements"""
        new_achievements = []
        achieved_types = {a.achievement_type for a in self.achievements}
        
        # Building achievements - From first building to legendary architect
        if AchievementType.FIRST_BUILDER not in achieved_types and self.buildings_built >= 1:
            new_achievements.append(Achievement(
                AchievementType.FIRST_BUILDER,
                "🏗️ First Builder",
                f"Constructed your first building! The foundation of civilization begins with you.",
                "🏗️",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        elif AchievementType.LEGENDARY_BUILDER not in achieved_types and self.buildings_built >= 50:
            new_achievements.append(Achievement(
                AchievementType.LEGENDARY_BUILDER,
                "🏛️ Legendary Builder",
                f"Constructed 50+ buildings! The world is your canvas!",
                "🏛️",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        elif AchievementType.MASTER_BUILDER not in achieved_types and self.buildings_built >= 10:
            new_achievements.append(Achievement(
                AchievementType.MASTER_BUILDER,
                "🏗️ Master Builder",
                f"Constructed 10+ buildings. Architecture is your calling!",
                "🏗️",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        
        # Survival achievements
        if AchievementType.ANCIENT_ONE not in achieved_types and self.days_survived >= 90 * 144:  # 90 years
            new_achievements.append(Achievement(
                AchievementType.ANCIENT_ONE,
                "👴 The Ancient One",
                f"Lived to 90 years old! A living legend!",
                "👴",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        elif AchievementType.ELDER not in achieved_types and self.days_survived >= 70 * 144:  # 70 years
            new_achievements.append(Achievement(
                AchievementType.ELDER,
                "🧓 The Elder",
                f"Lived to 70 years! Wisdom comes with age.",
                "🧓",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        elif AchievementType.SURVIVOR not in achieved_types and current_day >= 100:
            new_achievements.append(Achievement(
                AchievementType.SURVIVOR,
                "💪 Survivor",
                f"Survived 100 days in this brutal world!",
                "💪",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        
        # Family achievements
        if AchievementType.PATRIARCH not in achieved_types and self.children_count >= 10:
            new_achievements.append(Achievement(
                AchievementType.PATRIARCH,
                "👑 Patriarch/Matriarch",
                f"10+ descendants! Your bloodline is STRONG!",
                "👑",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        elif AchievementType.DYNASTY_FOUNDER not in achieved_types and self.children_count >= 5:
            new_achievements.append(Achievement(
                AchievementType.DYNASTY_FOUNDER,
                "👨‍👩‍👧‍👦 Dynasty Founder",
                f"5+ children! Your family will rule for generations!",
                "👨‍👩‍👧‍👦",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        elif AchievementType.PARENT not in achieved_types and self.children_count >= 1:
            new_achievements.append(Achievement(
                AchievementType.PARENT,
                "👶 Proud Parent",
                f"Had your first child! The legacy begins.",
                "👶",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        
        # Wealth achievements
        if AchievementType.TYCOON not in achieved_types and self.max_wealth >= 500:
            new_achievements.append(Achievement(
                AchievementType.TYCOON,
                "💰 Tycoon",
                f"Accumulated 500+ wealth! You're RICH!",
                "💰",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        elif AchievementType.WEALTHY not in achieved_types and self.max_wealth >= 100:
            new_achievements.append(Achievement(
                AchievementType.WEALTHY,
                "💵 Wealthy",
                f"Accumulated 100+ wealth! Living large!",
                "💵",
                datetime.now(),
                current_day,
                self.agent_id
            ))
        
        # Add to agent's achievements
        self.achievements.extend(new_achievements)
        return new_achievements


class AchievementTracker:
    """Tracks achievements for all agents and civilization"""
    
    def __init__(self):
        self.agent_achievements: Dict[str, AgentAchievements] = {}
        self.civilization_achievements: List[Achievement] = []
        self.unlocked_types: Set[AchievementType] = set()
        
    def track_agent(self, agent_id: str, agent_name: str):
        """Start tracking an agent"""
        if agent_id not in self.agent_achievements:
            self.agent_achievements[agent_id] = AgentAchievements(agent_id, agent_name)
    
    def update_agent_stat(self, agent_id: str, stat: str, value):
        """Update agent stat for achievement tracking"""
        if agent_id in self.agent_achievements:
            setattr(self.agent_achievements[agent_id], stat, value)
    
    def check_agent_achievements(self, agent_id: str, current_day: int) -> List[Achievement]:
        """Check if agent earned achievements"""
        if agent_id in self.agent_achievements:
            return self.agent_achievements[agent_id].check_and_award(current_day)
        return []
    
    def unlock_civilization_achievement(self, achievement_type: AchievementType, day: int) -> Optional[Achievement]:
        """Unlock a civilization-wide achievement"""
        if achievement_type in self.unlocked_types:
            return None
        
        achievement_data = {
            AchievementType.FIRST_BIRTH: ("👶 First Birth", "The first baby was born! Civilization can grow!"),
            AchievementType.FIRST_DEATH: ("💀 First Death", "The first soul was lost. Mortality is real."),
            AchievementType.POPULATION_10: ("🎉 Population: 10", "10 agents strong!"),
            AchievementType.POPULATION_50: ("🎊 Population: 50", "50 agents! We're thriving!"),
            AchievementType.POPULATION_100: ("🎆 Population: 100", "100 agents! A true civilization!"),
            AchievementType.FIRST_WAR: ("⚔️ First War", "Conflict has begun. Peace was never an option."),
            AchievementType.BRONZE_AGE: ("🥉 Bronze Age", "Entered the Bronze Age!"),
        }
        
        if achievement_type in achievement_data:
            name, desc = achievement_data[achievement_type]
            achievement = Achievement(
                achievement_type,
                name,
                desc,
                name.split()[0],  # Get emoji as icon
                datetime.now(),
                day,
                None
            )
            self.civilization_achievements.append(achievement)
            self.unlocked_types.add(achievement_type)
            return achievement
        
        return None
    
    def to_dict(self) -> Dict:
        """Serialize for API"""
        return {
            'civilization_achievements': [
                {
                    'type': a.achievement_type.value,
                    'name': a.name,
                    'description': a.description,
                    'icon': a.icon,
                    'day': a.day,
                    'unlocked_at': a.unlocked_at.isoformat()
                }
                for a in self.civilization_achievements
            ],
            'agent_achievements': {
                agent_id: {
                    'agent_name': ach.agent_name,
                    'achievements': [
                        {
                            'type': a.achievement_type.value,
                            'name': a.name,
                            'description': a.description,
                            'icon': a.icon,
                            'day': a.day
                        }
                        for a in ach.achievements
                    ],
                    'total_count': len(ach.achievements)
                }
                for agent_id, ach in self.agent_achievements.items()
            },
            'total_unlocked': len(self.unlocked_types)
        }
