"""
Event System - Track and narrate world events

Tracks all significant happenings:
- Agent actions and outcomes
- Births, deaths, relationships
- Economic transactions
- Conflicts and resolutions
- Cultural moments
"""

from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Deque
from datetime import datetime
from enum import Enum
from collections import deque


class EventCategory(Enum):
    """Categories of events"""
    LIFE = "life"  # Birth, death, aging
    SOCIAL = "social"  # Relationships, social interactions
    ECONOMIC = "economic"  # Trade, wealth changes
    CONFLICT = "conflict"  # Fights, wars
    CULTURAL = "cultural"  # Art, stories, traditions
    ENVIRONMENTAL = "environmental"  # Resource changes, disasters
    POLITICAL = "political"  # Leadership, groups


class EventImportance(Enum):
    """How important/notable is the event"""
    TRIVIAL = 0
    MINOR = 1
    MODERATE = 2
    MAJOR = 3
    CRITICAL = 4


@dataclass
class Event:
    """A single event in the world"""
    id: str
    timestamp: datetime
    tick: int
    category: EventCategory
    importance: EventImportance
    title: str
    description: str
    agents_involved: List[str] = field(default_factory=list)
    location: Optional[Dict] = None
    data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'tick': self.tick,
            'category': self.category.value,
            'importance': self.importance.value,
            'title': self.title,
            'description': self.description,
            'agents_involved': self.agents_involved,
            'location': self.location,
            'data': self.data,
        }


class EventLogger:
    """Logs and manages world events"""

    def __init__(self):
        # Use deque with maxlen for automatic memory management
        self.max_events = 10000  # Keep last 10k events
        self.events: Deque[Event] = deque(maxlen=self.max_events)
        self.listeners = []  # called with each new event (e.g. agents' memories)

    def log_event(
        self,
        category: EventCategory,
        importance: EventImportance,
        title: str,
        description: str,
        current_tick: int,
        agents_involved: List[str] = None,
        location: Dict = None,
        data: Dict = None
    ) -> Event:
        """Log a new event"""
        event = Event(
            id=str(new_uuid()),
            timestamp=datetime.now(),
            tick=current_tick,
            category=category,
            importance=importance,
            title=title,
            description=description,
            agents_involved=agents_involved or [],
            location=location,
            data=data or {}
        )

        # Deque automatically drops oldest when full
        self.events.append(event)
        for listener in self.listeners:
            listener(event)

        return event

    def get_recent_events(
        self,
        count: int = 50,
        min_importance: EventImportance = EventImportance.MINOR
    ) -> List[Event]:
        """Get recent events above importance threshold"""
        filtered = [e for e in self.events
                   if e.importance.value >= min_importance.value]
        return filtered[-count:]

    def get_events_by_category(
        self,
        category: EventCategory,
        count: int = 50
    ) -> List[Event]:
        """Get events of specific category"""
        filtered = [e for e in self.events if e.category == category]
        return filtered[-count:]

    def get_events_involving_agent(
        self,
        agent_id: str,
        count: int = 50
    ) -> List[Event]:
        """Get events involving specific agent"""
        filtered = [e for e in self.events if agent_id in e.agents_involved]
        return filtered[-count:]

    def get_statistics(self) -> Dict:
        """Get event statistics"""
        category_counts = {}
        importance_counts = {}

        for event in self.events:
            category_counts[event.category.value] = \
                category_counts.get(event.category.value, 0) + 1
            importance_counts[event.importance.value] = \
                importance_counts.get(event.importance.value, 0) + 1

        return {
            'total_events': len(self.events),
            'by_category': category_counts,
            'by_importance': importance_counts,
        }

    def generate_story(self, agent_id: str, event_count: int = 10) -> str:
        """Generate a narrative story from agent's events"""
        events = self.get_events_involving_agent(agent_id, event_count)

        if not events:
            return f"No significant events recorded."

        story_parts = []
        for event in events:
            story_parts.append(f"- {event.title}: {event.description}")

        return "\n".join(story_parts)


class EventGenerator:
    """Generates event descriptions from game state"""

    @staticmethod
    def agent_born(agent_name: str, location: Dict) -> Tuple[str, str]:
        """Generate birth event"""
        title = f"{agent_name} was born"
        description = f"A new agent named {agent_name} entered the world."
        return title, description

    @staticmethod
    def agent_died(agent_name: str, age: int, cause: str) -> Tuple[str, str]:
        """Generate death event"""
        title = f"{agent_name} has died"
        description = f"{agent_name} died at age {age}. Cause: {cause}"
        return title, description

    @staticmethod
    def relationship_formed(
        agent_a_name: str,
        agent_b_name: str,
        relationship_type: str
    ) -> Tuple[str, str]:
        """Generate relationship event"""
        if relationship_type == "friendship":
            title = f"{agent_a_name} and {agent_b_name} became friends"
            description = f"A friendship has formed between {agent_a_name} and {agent_b_name}."
        elif relationship_type == "romance":
            title = f"{agent_a_name} and {agent_b_name} fell in love"
            description = f"Romance has blossomed between {agent_a_name} and {agent_b_name}."
        elif relationship_type == "rivalry":
            title = f"{agent_a_name} and {agent_b_name} became rivals"
            description = f"A rivalry has formed between {agent_a_name} and {agent_b_name}."
        else:
            title = f"Relationship formed"
            description = f"{agent_a_name} and {agent_b_name} formed a {relationship_type} relationship."

        return title, description

    @staticmethod
    def trade_completed(
        buyer_name: str,
        seller_name: str,
        item: str,
        quantity: int,
        price: float
    ) -> Tuple[str, str]:
        """Generate trade event"""
        title = f"Trade: {buyer_name} bought {item}"
        description = f"{buyer_name} purchased {quantity} {item} from {seller_name} for {price:.1f} coins."
        return title, description

    @staticmethod
    def fight_occurred(
        agent_a_name: str,
        agent_b_name: str,
        winner_name: str
    ) -> Tuple[str, str]:
        """Generate fight event"""
        title = f"Fight: {agent_a_name} vs {agent_b_name}"
        description = f"{agent_a_name} fought {agent_b_name}. {winner_name} emerged victorious."
        return title, description

    @staticmethod
    def group_formed(group_name: str, founder_name: str) -> Tuple[str, str]:
        """Generate group formation event"""
        title = f"New group formed: {group_name}"
        description = f"{founder_name} founded a new group called {group_name}."
        return title, description

    @staticmethod
    def agent_joined_group(agent_name: str, group_name: str) -> Tuple[str, str]:
        """Generate group join event"""
        title = f"{agent_name} joined {group_name}"
        description = f"{agent_name} has become a member of {group_name}."
        return title, description
