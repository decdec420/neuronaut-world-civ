"""
Fun & Entertainment System - Because agents need to LIVE, not just survive!

Implements:
- Games & Gambling (dice, races, competitions)
- Celebrations & Parties (festivals, weddings, achievements)
- Art & Performance (music, theater, storytelling)
- Sports & Athletics (competitions, spectating)
- Hobbies & Leisure (collecting, gardening, crafting)

Philosophy: Fun is a psychological NEED for happiness and culture.
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class CelebrationType(Enum):
    """Types of celebrations"""
    DISCOVERY_PARTY = "discovery_party"  # New material/innovation discovered
    BIRTH_CELEBRATION = "birth_celebration"  # New agent born
    WEDDING = "wedding"  # Marriage ceremony
    FUNERAL = "funeral"  # Honor the dead
    HARVEST_FESTIVAL = "harvest_festival"  # Seasonal celebration
    ACHIEVEMENT_PARTY = "achievement_party"  # Major accomplishment
    BUILDING_COMPLETION = "building_completion"  # New structure finished
    VICTORY_CELEBRATION = "victory_celebration"  # Won a competition/conflict


class GameType(Enum):
    """Types of games agents can play"""
    DICE = "dice"  # Simple gambling with dice
    RACE = "race"  # Speed competition
    SKILL_CONTEST = "skill_contest"  # Show off a skill
    STRENGTH_TEST = "strength_test"  # Physical competition
    RIDDLES = "riddles"  # Intelligence game
    STORYTELLING_CONTEST = "storytelling_contest"  # Creative competition


@dataclass
class Celebration:
    """A celebration event"""
    id: str
    celebration_type: CelebrationType
    organizer_id: str
    participants: Set[str] = field(default_factory=set)
    location: Tuple[float, float] = (50.0, 50.0)
    start_time: datetime = field(default_factory=datetime.now)
    duration_ticks: int = 20  # How long it lasts
    mood_boost: float = 0.3  # Happiness increase for participants
    
    # What triggered this celebration
    trigger_event: Optional[str] = None
    celebration_name: Optional[str] = None
    
    # Resources spent (food, decorations, etc)
    resources_spent: Dict[str, int] = field(default_factory=dict)
    
    # Outcomes
    relationships_strengthened: int = 0
    traditions_created: List[str] = field(default_factory=list)


@dataclass
class Game:
    """A game session"""
    id: str
    game_type: GameType
    players: List[str]
    stakes: Dict[str, float] = field(default_factory=dict)  # player_id -> amount wagered
    winner: Optional[str] = None
    
    # Game results
    scores: Dict[str, float] = field(default_factory=dict)
    rewards: Dict[str, float] = field(default_factory=dict)
    
    # Social impact
    spectators: Set[str] = field(default_factory=set)
    reputation_changes: Dict[str, float] = field(default_factory=dict)
    
    start_time: datetime = field(default_factory=datetime.now)
    completed: bool = False


@dataclass
class ArtPiece:
    """A piece of art created by an agent"""
    id: str
    art_type: str  # "painting", "sculpture", "song", "story", "dance"
    creator_id: str
    title: str
    quality: float  # 0-1, based on creator's creativity + skill
    
    # Impact
    fame_generated: float = 0.0
    cultural_value: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)
    viewers: Set[str] = field(default_factory=set)
    reactions: Dict[str, float] = field(default_factory=dict)  # agent_id -> enjoyment (0-1)


class FunSystem:
    """
    Manages all fun and entertainment in the simulation.
    
    Agents need fun to be happy! This creates:
    - Stronger social bonds
    - Cultural development  
    - Memorable stories
    - Emotional variety
    """
    
    HISTORY_LIMIT = 1000  # finished games and celebrations remembered

    def __init__(self):
        self.active_celebrations: Dict[str, Celebration] = {}
        self.celebration_history: List[Celebration] = []
        
        self.active_games: Dict[str, Game] = {}
        self.game_history: List[Game] = []
        
        self.art_pieces: Dict[str, ArtPiece] = {}
        self._art_sorted: List[ArtPiece] = []  # art_pieces by quality, best first

        # Per agent: celebrations attended, games played and won, art made.
        # Counted as they happen (get_agent_fun_stats used to rescan the whole
        # history for every agent, every tick)
        self.agent_counts: Dict[str, Dict[str, int]] = {}
        
        # Traditions that emerge from repeated celebrations
        self.traditions: Dict[str, int] = {}  # tradition_name -> times_performed
        
        # Statistics
        self.total_celebrations = 0
        self.total_games = 0
        self.total_art_created = 0
    
    # ============================================
    # CELEBRATIONS
    # ============================================
    
    def trigger_celebration(
        self,
        celebration_type: CelebrationType,
        organizer_id: str,
        organizer_name: str,
        trigger_event: str,
        location: Tuple[float, float],
        nearby_agents: List[str] = None
    ) -> Celebration:
        """
        Trigger a celebration event!
        
        Nearby agents will be invited to join.
        """
        celebration_id = str(new_uuid())
        
        # Generate celebration name
        celebration_names = {
            CelebrationType.DISCOVERY_PARTY: f"{organizer_name}'s Discovery Celebration",
            CelebrationType.ACHIEVEMENT_PARTY: f"{organizer_name}'s Achievement Festival",
            CelebrationType.BUILDING_COMPLETION: f"Grand Opening Celebration",
            CelebrationType.HARVEST_FESTIVAL: "Harvest Festival",
            CelebrationType.WEDDING: "Wedding Ceremony",
            CelebrationType.BIRTH_CELEBRATION: "Birth Celebration",
            CelebrationType.FUNERAL: "Memorial Ceremony",
            CelebrationType.VICTORY_CELEBRATION: "Victory Feast",
        }
        
        celebration = Celebration(
            id=celebration_id,
            celebration_type=celebration_type,
            organizer_id=organizer_id,
            participants={organizer_id},
            location=location,
            trigger_event=trigger_event,
            celebration_name=celebration_names.get(celebration_type, "Celebration"),
            duration_ticks=random.randint(15, 30),
            mood_boost=0.3
        )
        
        # Invite nearby agents
        if nearby_agents:
            for agent_id in nearby_agents[:10]:  # Max 10 participants
                if random.random() < 0.7:  # 70% accept invitation
                    celebration.participants.add(agent_id)
        
        self.active_celebrations[celebration_id] = celebration
        self.total_celebrations += 1
        
        return celebration
    
    def update_celebrations(self, delta_time: float = 1.0) -> List[Celebration]:
        """Update active celebrations, return completed ones"""
        completed = []
        
        for cel_id, celebration in list(self.active_celebrations.items()):
            celebration.duration_ticks -= delta_time
            
            if celebration.duration_ticks <= 0:
                # Celebration complete!
                self.celebration_history.append(celebration)
                del self.celebration_history[:-self.HISTORY_LIMIT]
                for agent_id in celebration.participants:
                    self._count(agent_id, 'celebrations_attended')
                completed.append(celebration)
                del self.active_celebrations[cel_id]
                
                # Check if this becomes a tradition
                cel_type = celebration.celebration_type.value
                self.traditions[cel_type] = self.traditions.get(cel_type, 0) + 1
        
        return completed
    
    # ============================================
    # GAMES & GAMBLING
    # ============================================
    
    def start_dice_game(
        self,
        players: List[Tuple[str, str]],  # [(agent_id, agent_name), ...]
        stakes: float = 10.0
    ) -> Game:
        """
        Start a dice gambling game!
        
        Simple: Each player rolls, highest wins all the stakes.
        """
        game_id = str(new_uuid())
        
        game = Game(
            id=game_id,
            game_type=GameType.DICE,
            players=[p[0] for p in players],
            stakes={p[0]: stakes for p in players},
            scores={},
            rewards={}
        )
        
        self.active_games[game_id] = game
        self.total_games += 1
        
        return game
    
    def _finish_game(self, game: Game) -> None:
        """A finished game leaves active_games for the (bounded) history. It
        used to stay "active" forever: every agent's perception looped over
        every game ever played, every tick."""
        game.completed = True
        self.active_games.pop(game.id, None)
        self.game_history.append(game)
        del self.game_history[:-self.HISTORY_LIMIT]
        for agent_id in game.players:
            self._count(agent_id, 'games_played')
        if game.winner:
            self._count(game.winner, 'games_won')

    def _count(self, agent_id: str, what: str) -> None:
        counts = self.agent_counts.setdefault(agent_id, {})
        counts[what] = counts.get(what, 0) + 1

    def art_by_quality(self) -> List[ArtPiece]:
        """Every art piece, best first (re-sorted only when art is added)."""
        if len(self._art_sorted) != len(self.art_pieces):
            self._art_sorted = sorted(self.art_pieces.values(), key=lambda a: a.quality, reverse=True)
        return self._art_sorted

    def resolve_dice_game(self, game: Game) -> Dict:
        """
        Resolve a dice game - determine winner!
        
        Returns outcome data for logging.
        """
        if game.completed:
            return {}
        
        # Each player rolls
        for player_id in game.players:
            roll = random.randint(1, 6)
            game.scores[player_id] = roll
        
        # Determine winner (highest roll)
        winner_id = max(game.scores.items(), key=lambda x: x[1])[0]
        game.winner = winner_id
        
        # Winner takes all stakes
        total_pot = sum(game.stakes.values())
        game.rewards[winner_id] = total_pot
        
        # Reputation changes
        game.reputation_changes[winner_id] = 0.05  # Small fame boost
        
        self._finish_game(game)
        
        return {
            'winner': winner_id,
            'pot': total_pot,
            'rolls': game.scores,
            'game_type': 'dice'
        }
    
    def start_race(
        self,
        racers: List[Tuple[str, str, float]],  # [(id, name, speed_skill), ...]
        distance: float = 100.0
    ) -> Game:
        """Start a racing competition"""
        game_id = str(new_uuid())
        
        game = Game(
            id=game_id,
            game_type=GameType.RACE,
            players=[r[0] for r in racers],
            scores={},
            rewards={}
        )
        
        self.active_games[game_id] = game
        self.total_games += 1
        
        return game
    
    def resolve_race(self, game: Game, agent_skills: Dict[str, float]) -> Dict:
        """Resolve race based on agent speed/agility"""
        if game.completed:
            return {}
        
        # Calculate race times (lower is better)
        for player_id in game.players:
            skill = agent_skills.get(player_id, 0.5)
            # Time = base_time * (1 - skill_modifier) + randomness
            time = 100.0 * (1.0 - skill * 0.3) + random.uniform(-10, 10)
            game.scores[player_id] = time
        
        # Winner is fastest (lowest time)
        winner_id = min(game.scores.items(), key=lambda x: x[1])[0]
        game.winner = winner_id
        
        # Rewards: Fame and status
        game.reputation_changes[winner_id] = 0.1
        
        self._finish_game(game)
        
        return {
            'winner': winner_id,
            'times': game.scores,
            'game_type': 'race'
        }
    
    # ============================================
    # ART & CREATIVITY
    # ============================================
    
    def create_art(
        self,
        creator_id: str,
        creator_name: str,
        art_type: str,
        creativity_skill: float,
        relevant_skill: float = 0.5
    ) -> ArtPiece:
        """
        Agent creates a piece of art!
        
        Quality depends on creativity + relevant skill.
        """
        art_id = str(new_uuid())
        
        # Generate title
        titles = {
            "painting": ["Sunrise", "The Hunt", "Portrait", "Landscape", "Abstract Vision"],
            "sculpture": ["The Builder", "Mother and Child", "Victory", "The Thinker", "Nature's Form"],
            "song": ["Song of Joy", "The Working Man", "Love's Melody", "Battle Hymn", "Lullaby"],
            "story": ["The First Fire", "Hero's Journey", "The Clever Fox", "Creation Myth", "Love Lost"],
            "dance": ["Harvest Dance", "War Dance", "Rain Dance", "Celebration", "Ritual Movement"]
        }
        
        title_options = titles.get(art_type, ["Untitled"])
        title = f"{creator_name}'s {random.choice(title_options)}"
        
        # Calculate quality
        quality = (creativity_skill * 0.6 + relevant_skill * 0.4) * random.uniform(0.8, 1.2)
        quality = min(1.0, max(0.0, quality))
        
        art = ArtPiece(
            id=art_id,
            art_type=art_type,
            creator_id=creator_id,
            title=title,
            quality=quality,
            fame_generated=quality * 0.1,
            cultural_value=quality * random.uniform(0.5, 1.5)
        )
        
        self.art_pieces[art_id] = art
        self._count(creator_id, 'art_created')
        self.total_art_created += 1
        
        return art
    
    def view_art(self, art_id: str, viewer_id: str, viewer_creativity: float) -> float:
        """
        Agent views art and reacts to it.
        
        Returns enjoyment level (0-1).
        """
        if art_id not in self.art_pieces:
            return 0.0
        
        art = self.art_pieces[art_id]
        art.viewers.add(viewer_id)
        
        # Enjoyment based on quality + viewer's appreciation
        base_enjoyment = art.quality * 0.7
        appreciation_bonus = viewer_creativity * 0.3
        randomness = random.uniform(-0.1, 0.1)
        
        enjoyment = min(1.0, max(0.0, base_enjoyment + appreciation_bonus + randomness))
        art.reactions[viewer_id] = enjoyment
        
        return enjoyment
    
    # ============================================
    # STATISTICS & QUERIES
    # ============================================
    
    def get_stats(self) -> Dict:
        """Get fun system statistics"""
        return {
            'total_celebrations': self.total_celebrations,
            'active_celebrations': len(self.active_celebrations),
            'total_games': self.total_games,
            'active_games': len(self.active_games),
            'total_art': self.total_art_created,
            'traditions_count': len(self.traditions),
            'most_popular_tradition': max(self.traditions.items(), key=lambda x: x[1])[0] if self.traditions else None
        }
    
    def get_agent_fun_stats(self, agent_id: str) -> Dict:
        """Get fun statistics for specific agent"""
        counts = self.agent_counts.get(agent_id, {})
        celebrations_attended = counts.get('celebrations_attended', 0)
        games_played = counts.get('games_played', 0)
        games_won = counts.get('games_won', 0)
        art_created = counts.get('art_created', 0)
        
        return {
            'celebrations_attended': celebrations_attended,
            'games_played': games_played,
            'games_won': games_won,
            'win_rate': games_won / games_played if games_played > 0 else 0.0,
            'art_created': art_created,
            'fun_score': celebrations_attended * 2 + games_played + art_created * 3
        }

