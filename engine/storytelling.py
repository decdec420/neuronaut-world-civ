"""
STORY ENGINE - Transform Events into Epic Narratives

This is where we turn raw simulation data into LEGENDARY STORIES.
Every birth, death, achievement, and relationship becomes a memorable tale.
"""

import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class StoryType(Enum):
    """Types of stories we tell"""
    BIRTH = "birth"
    DEATH = "death"
    ROMANCE = "romance"
    ACHIEVEMENT = "achievement"
    TRAGEDY = "tragedy"
    TRIUMPH = "triumph"
    CONFLICT = "conflict"
    DISCOVERY = "discovery"
    LEGACY = "legacy"

    # AGENT-CREATED STORIES - Cultural emergence!
    MYTH = "myth"  # Made-up tales explaining the unknown
    LEGEND = "legend"  # Exaggerated heroic tales
    TEACHING = "teaching"  # Wisdom passed down
    WARNING = "warning"  # Cautionary tales
    HISTORY = "history"  # Factual accounts
    PROPHECY = "prophecy"  # Predictions/visions
    SONG = "song"  # Musical stories
    PARABLE = "parable"  # Moral lessons


class StoryTone(Enum):
    """Emotional tone of the story"""
    EPIC = "epic"
    TRAGIC = "tragic"
    ROMANTIC = "romantic"
    HUMOROUS = "humorous"
    DRAMATIC = "dramatic"
    INSPIRING = "inspiring"


@dataclass
class Story:
    """A generated narrative story"""
    story_type: StoryType
    title: str
    narrative: str
    tone: StoryTone
    agent_ids: List[str]
    day: int
    importance: int  # 1-5, how memorable
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    tick: Optional[int] = None          # sim time it was told
    source: Optional[str] = None        # the memory it was told from


class StoryGenerator:
    """Generates epic narratives from simulation events"""

    @staticmethod
    def agent_creates_story(agent_name: str, agent_personality: Dict, story_type: StoryType, day: int, context: Dict = None) -> Story:
        """
        AGENT-CREATED STORIES - True cultural emergence!

        Agents CREATE stories based on:
        - Their personality (creative agents tell better stories)
        - Their experiences (survivors tell warnings, builders tell legends)
        - Their emotions (happy agents tell songs, scared ones tell warnings)
        - Pure imagination (myths about the unknown)

        This is how culture emerges organically!
        """
        creativity = agent_personality.get('creativity', 0.5)
        openness = agent_personality.get('openness', 0.5)
        context = context or {}

        narratives = []
        title = ""
        tone = StoryTone.EPIC

        if story_type == StoryType.MYTH:
            # Explain the unknown with imagination
            tone = StoryTone.DRAMATIC
            myths = [
                f"{agent_name} speaks of the Great Stone Spirit that watches over our people. "
                f"They say on quiet nights, you can hear it breathing in the mountains. "
                f"It gives us stone for building, but demands respect in return.",

                f"By the fire, {agent_name} tells the tale of the Sky Father and Earth Mother. "
                f"They say when it rains, the Sky Father weeps for joy at seeing Earth Mother bloom. "
                f"This is why plants grow after rain - it's their love made manifest.",

                f"{agent_name} shares the legend of the First Fire. "
                f"Long ago, they say, the world was cold and dark. A brave spirit stole flame from the sun "
                f"and brought it to the people. We must keep fire burning to honor that sacrifice.",
            ]
            narratives = [random.choice(myths)]
            title = f"🌟 Myth: {agent_name}'s Tale"

        elif story_type == StoryType.LEGEND:
            # Exaggerated heroic tales
            tone = StoryTone.EPIC
            legends = [
                f"They say {agent_name} once built a shelter in a single day during a storm! "
                f"With hands bleeding and muscles aching, they worked through thunder and lightning. "
                f"When morning came, the structure stood tall - a testament to human will!",

                f"The story goes that {agent_name} discovered food where others found nothing. "
                f"They wandered into the wilderness for three days and nights, following bird songs. "
                f"When they returned, their arms were full of bounty. Some say the forest spoke to them.",

                f"Legend tells of {agent_name} facing death itself and living to tell the tale. "
                f"When sickness swept through the settlement, they stood firm. "
                f"Their strength inspired others to keep fighting. Death moved on, defeated.",
            ]
            narratives = [random.choice(legends)]
            title = f"⚔️ Legend: The Tale of {agent_name}"

        elif story_type == StoryType.WARNING:
            # Cautionary tales
            tone = StoryTone.TRAGIC
            warnings = [
                f"{agent_name} warns: 'I once saw someone wander too far in search of resources. "
                f"They never returned. The wilderness is beautiful but merciless. "
                f"Stay close to your people. Safety comes from community.'",

                f"A grave tale from {agent_name}: 'I knew someone who hoarded resources without sharing. "
                f"When hard times came, no one helped them in return. They perished alone, "
                f"surrounded by riches that couldn't save them. Generosity is survival.'",

                f"{agent_name} speaks solemnly: 'Never build in haste. I saw a shelter collapse "
                f"because the builder rushed. Materials wasted, hope crushed. "
                f"Take your time. Do it right. Your life may depend on it.'",
            ]
            narratives = [random.choice(warnings)]
            title = f"⚠️ Warning: {agent_name}'s Lesson"

        elif story_type == StoryType.TEACHING:
            # Wisdom and practical knowledge
            tone = StoryTone.INSPIRING
            teachings = [
                f"{agent_name} teaches: 'To survive winter, you must prepare in summer. "
                f"When food is plenty, store it. When water is clear, save it. "
                f"The world gives in cycles - abundance and scarcity dance together. "
                f"Those who understand this rhythm will endure.'",

                f"Wisdom from {agent_name}: 'A single person can build a house. "
                f"But a community builds a home. Share your skills, learn from others. "
                f"The strongest buildings are raised by many hands working as one.'",

                f"{agent_name} shares knowledge: 'Watch the animals. They know things we've forgotten. "
                f"Where birds gather, food grows. Where water pools, life thrives. "
                f"Nature is the greatest teacher for those willing to observe.'",
            ]
            narratives = [random.choice(teachings)]
            title = f"📚 Teaching: {agent_name}'s Wisdom"

        elif story_type == StoryType.SONG:
            # Musical/poetic stories
            tone = StoryTone.ROMANTIC
            songs = [
                f"{agent_name} sings by the fire:\n"
                f"'Stone by stone, we build our home,\n"
                f"Hand in hand, we're not alone,\n"
                f"Through the night, through the cold,\n"
                f"Together strong, together bold!'",

                f"A melody from {agent_name}:\n"
                f"'Seeds we plant, food we share,\n"
                f"Love we give, friends who care,\n"
                f"This is life, this is true,\n"
                f"Building worlds, me and you!'",

                f"{agent_name}'s voice rises:\n"
                f"'Sun will rise, rain will fall,\n"
                f"We survive through it all,\n"
                f"Hearts of fire, spirits bright,\n"
                f"Dancing through the endless night!'",
            ]
            narratives = [random.choice(songs)]
            title = f"🎵 Song: {agent_name}'s Melody"

        return Story(
            story_type=story_type,
            title=title,
            narrative=random.choice(narratives) if narratives else f"{agent_name} created a story.",
            tone=tone,
            agent_ids=[context.get('agent_id', '')],
            day=day,
            importance=3 + int(creativity * 2),  # Creative agents create more important stories
            tags=["agent_created", "culture", story_type.value]
        )

    @staticmethod
    def generate_birth_story(baby_name: str, mother_name: str, father_name: str, day: int, family_context: Dict) -> Story:
        """Generate an EPIC birth announcement"""
        
        # Epic opening lines
        openings = [
            f"On the dawn of Day {day}, the world grew brighter.",
            f"Day {day} will be remembered as the day hope was born.",
            f"The {family_context.get('generation', 1)}th generation begins.",
            f"A new chapter begins on Day {day}.",
        ]
        
        # Main narrative with drama
        narratives = [
            f"{mother_name} brought forth new life into the world. Baby {baby_name}, child of {mother_name} and {father_name}, "
            f"enters a civilization of {family_context.get('population', '?')} souls. "
            f"The bloodline continues. The family grows stronger.",
            
            f"After months of anticipation, {mother_name} gave birth to {baby_name}. "
            f"Father {father_name} stood watch as the newest member of their dynasty took their first breath. "
            f"In a world where survival is never guaranteed, every new life is a miracle.",
            
            f"{baby_name} was born to {mother_name} and {father_name} on this historic day. "
            f"The child carries the traits of both parents - a blend of {mother_name}'s spirit and {father_name}'s strength. "
            f"What legacy will they create?",
        ]
        
        opening = random.choice(openings)
        narrative = random.choice(narratives)
        full_story = f"{opening}\n\n{narrative}"
        
        return Story(
            story_type=StoryType.BIRTH,
            title=f"👶 A New Life: {baby_name} is Born",
            narrative=full_story,
            tone=StoryTone.INSPIRING,
            agent_ids=[family_context.get('mother_id', ''), family_context.get('father_id', '')],
            day=day,
            importance=4,
            tags=["birth", "family", "generation"]
        )

    @staticmethod
    def generate_death_story(agent_name: str, age: int, cause: str, day: int, legacy_context: Dict) -> Story:
        """Generate a LEGENDARY death story"""
        
        # Dramatic death announcements
        if cause == "starvation":
            narratives = [
                f"On Day {day}, {agent_name} drew their final breath. At {age} years old, they succumbed to starvation - "
                f"a grim reminder that survival is never guaranteed. They fought until the end, but the hunger proved too strong. "
                f"{legacy_context.get('achievement_count', 0)} achievements will be their monument.",
                
                f"The world lost {agent_name} to starvation on Day {day}. For {age} years they survived, thrived, and built. "
                f"But in the end, even the strongest fall when food runs dry. "
                f"Their {legacy_context.get('children_count', 0)} children will remember them.",
            ]
        elif cause == "dehydration":
            narratives = [
                f"Day {day} marks a dark chapter. {agent_name}, {age} years of age, died of thirst. "
                f"Without water, even legends perish. They leave behind {legacy_context.get('wealth', 0)} in wealth "
                f"and memories that will echo through generations.",
            ]
        elif cause == "old age":
            narratives = [
                f"On Day {day}, {agent_name} passed peacefully at the ripe age of {age}. "
                f"They lived a FULL life - survived famines, built wonders, loved deeply, and fought bravely. "
                f"Their {legacy_context.get('children_count', 0)} children and {legacy_context.get('grandchildren_count', 0)} grandchildren "
                f"carry their bloodline forward. A true legend of the {legacy_context.get('generation', 1)}th generation.",
                
                f"{agent_name}'s story ends at age {age}, but their legend begins. "
                f"They were there from Day {legacy_context.get('birth_day', 0)}, witnessed civilization rise from nothing, "
                f"and helped build a world worth living in. Rest in power, {agent_name}.",
            ]
        elif cause == "disease":
            narratives = [
                f"Tragedy struck on Day {day}. {agent_name}, only {age} years old, fell to disease. "
                f"The illness took them swiftly, leaving loved ones in shock. "
                f"In a world without medicine, even the young can fall. May they find peace.",
            ]
        else:
            narratives = [
                f"{agent_name} died on Day {day} at age {age}. Cause: {cause}. "
                f"Their story is complete, but the impact remains. "
                f"{legacy_context.get('buildings_built', 0)} buildings, {legacy_context.get('discoveries', 0)} discoveries, "
                f"and a lifetime of memories.",
            ]
        
        narrative = random.choice(narratives)
        
        return Story(
            story_type=StoryType.DEATH,
            title=f"💀 Farewell: {agent_name} Has Fallen",
            narrative=narrative,
            tone=StoryTone.TRAGIC if age < 50 else StoryTone.EPIC,
            agent_ids=[legacy_context.get('agent_id', '')],
            day=day,
            importance=5 if legacy_context.get('children_count', 0) > 3 else 4,
            tags=["death", cause, "memorial"]
        )

    @staticmethod
    def generate_romance_story(agent1_name: str, agent2_name: str, day: int, relationship_strength: float) -> Story:
        """Generate a PASSIONATE romance story"""
        
        if relationship_strength > 0.8:
            narratives = [
                f"Day {day}: TRUE LOVE FOUND. {agent1_name} and {agent2_name} have formed a bond that transcends mere attraction. "
                f"Their chemistry is undeniable, their connection profound. In a harsh world, they found each other. "
                f"Will their love story become legendary?",
                
                f"The stars aligned on Day {day}. {agent1_name} and {agent2_name} fell DEEPLY in love. "
                f"What started as attraction has blossomed into something beautiful. "
                f"Their romance gives hope to everyone watching.",
            ]
            title = f"❤️ TRUE LOVE: {agent1_name} & {agent2_name}"
            importance = 4
        else:
            narratives = [
                f"{agent1_name} and {agent2_name} shared an intimate moment on Day {day}. "
                f"Is this the beginning of something special, or just a fleeting romance? Only time will tell.",
            ]
            title = f"💕 Romance: {agent1_name} & {agent2_name}"
            importance = 2
        
        return Story(
            story_type=StoryType.ROMANCE,
            title=title,
            narrative=random.choice(narratives),
            tone=StoryTone.ROMANTIC,
            agent_ids=[],  # Will be filled by caller
            day=day,
            importance=importance,
            tags=["romance", "love", "relationship"]
        )

    @staticmethod
    def generate_achievement_story(agent_name: str, achievement: str, day: int, context: Dict) -> Story:
        """Generate an EPIC achievement story"""
        
        achievement_narratives = {
            "first_building": [
                f"HISTORY WAS MADE on Day {day}! {agent_name} constructed the FIRST BUILDING in civilization history! "
                f"What was once wilderness is now marked by human creation. "
                f"This moment will be remembered for generations.",
            ],
            "first_discovery": [
                f"Day {day}: BREAKTHROUGH! {agent_name} made the FIRST DISCOVERY! "
                f"They unlocked knowledge that will change everything. "
                f"Future generations will study what {agent_name} learned today.",
            ],
            "master_builder": [
                f"{agent_name} has become a MASTER BUILDER! With {context.get('building_count', 10)} buildings to their name, "
                f"they've literally shaped the landscape of civilization. Every structure tells their story.",
            ],
            "population_milestone": [
                f"Day {day}: Thanks to {agent_name} and their {context.get('children_count', 5)} children, "
                f"the population has reached {context.get('total_population', 50)}! "
                f"Their family tree is becoming a forest. A true dynasty builder!",
            ],
            "survived_100_days": [
                f"{agent_name} has survived 100 DAYS in this brutal world! "
                f"Through starvation scares, conflicts, and chaos - they endured. "
                f"Few can claim such resilience.",
            ],
        }
        
        name = context.get('name') or achievement.replace('_', ' ').title()
        what = (context.get('description') or '').strip()
        built = f" with {context['building']}" if context.get('building') else ""
        narratives = achievement_narratives.get(achievement, [
            f"Day {day}: {agent_name}{built}: {name}." + (f" {what}" if what else "")
        ])
        personal = context.get('personal', False)

        return Story(
            story_type=StoryType.ACHIEVEMENT,
            title=f"🏆 {agent_name}: {name}",
            narrative=random.choice(narratives),
            tone=StoryTone.EPIC,
            agent_ids=[context.get('agent_id', '')],
            day=day,
            # a first for the whole world is epic; someone's own first is not
            importance=3 if personal else (5 if "first" in achievement else 3),
            tags=["achievement", achievement, "milestone"]
        )

    @staticmethod
    def generate_weekly_summary(day: int, stats: Dict) -> Story:
        """Generate EPIC weekly recap"""
        
        narrative = f"**WEEK {day // 7} RECAP**\n\n"
        
        highlights = []
        if stats.get('births', 0) > 0:
            highlights.append(f"👶 {stats['births']} new lives entered the world!")
        if stats.get('deaths', 0) > 0:
            highlights.append(f"💀 {stats['deaths']} souls were lost.")
        if stats.get('buildings', 0) > 0:
            highlights.append(f"🏛️ {stats['buildings']} new structures rose from the ground.")
        if stats.get('discoveries', 0) > 0:
            highlights.append(f"✨ {stats['discoveries']} discoveries expanded our knowledge.")
        if stats.get('romances', 0) > 0:
            highlights.append(f"❤️ {stats['romances']} couples found love.")
        
        narrative += "\n".join(highlights)
        narrative += f"\n\nPopulation: {stats.get('population', 0)} ({stats.get('alive', 0)} alive)"
        narrative += f"\nCivilization Progress: {stats.get('progress_percent', 0)}%"
        
        return Story(
            story_type=StoryType.LEGACY,
            title=f"📜 Week {day // 7} in Review",
            narrative=narrative,
            tone=StoryTone.EPIC,
            agent_ids=[],
            day=day,
            importance=3,
            tags=["weekly", "summary", "recap"]
        )


# What memories each kind of story is told from (agents/memory_stream.py text)
_STORY_WORDS = {
    StoryType.WARNING: ('died', 'death', 'starv', 'hurt', 'injur', 'flood', 'quake', 'storm', 'wildfire',
                        'lost', 'separated', 'collapsed', 'sick', 'drought', 'fight', 'killed', 'burn', 'failed'),
    StoryType.LEGEND: ('worked out', 'invented', 'built', 'first', 'founded', 'discovered', 'won'),
    StoryType.SONG: ('gathering', 'born', 'partner', 'came', 'feast', 'together', 'celebrat', 'child', 'married'),
    StoryType.MYTH: ('flood', 'quake', 'storm', 'rain', 'drought', 'wildfire', 'fire', 'lake', 'disaster', 'sky', 'died'),
}
_MYTH_CAUSES = ("the spirits of the land were restless", "the sky grew jealous of the people",
                "someone forgot to thank the earth", "the old ones beneath the hills turned in their sleep",
                "the water remembered a wrong done to it long ago")
_ICONS = {StoryType.WARNING: '⚠️', StoryType.LEGEND: '⚔️', StoryType.SONG: '🎵', StoryType.MYTH: '🌟',
          StoryType.TEACHING: '📚'}


def _clean(text: str) -> str:
    """A memory as it would be said aloud: no leading emoji, no trailing tally."""
    text = text.strip()
    while text and not text[0].isalnum():
        text = text[1:].lstrip()
    return text.rstrip('.')


def story_from_memory(agent, story_type: 'StoryType', tick: int, ledger=None) -> Optional[Story]:
    """A story the agent tells from its own memories (or, for a teaching,
    from what it knows how to do and how it learned it). None when it has
    nothing to tell of that kind: stories are never made up from nothing.

    Stories used to be picked from fixed templates ("I once saw someone
    wander too far... they never returned"), whatever had happened."""
    name = agent.name
    day = tick // 144 + 1
    importance = 3 + int(agent.personality.get_trait('openness') * 2) if hasattr(agent, 'personality') else 3
    if story_type == StoryType.TEACHING:
        known = sorted(getattr(agent, 'knowhow', None) or ())
        if not known or ledger is None:
            return None
        from world.knowhow import KNOWHOW
        learned = {}
        for entry in getattr(ledger, 'log', ()):
            if entry[2] == agent.id:
                learned[entry[1]] = entry
        # what it learned most recently that isn't innate, else anything it knows
        pick = max((k for k in known if k in learned), key=lambda k: learned[k][0], default=None)
        if pick is None or pick not in KNOWHOW:
            return None
        _, _, _, how, teacher = learned[pick]
        label = KNOWHOW[pick].label
        whence = {'taught': f"as {teacher_name(ledger, teacher)} taught it to them", 'watched': "as they learned it by watching",
                  'insight': "as they worked it out themselves"}.get(how, "as they came to know it")
        return Story(story_type, f"📚 Teaching: {label}, from {name}",
                     f"{name} passes on {label}, {whence}.", StoryTone.INSPIRING, [agent.id], day, importance,
                     ["agent_created", "culture", "teaching"], tick=tick, source=f"knows {label}")
    stream = getattr(agent, 'memory_stream', None)
    words = _STORY_WORDS.get(story_type)
    if stream is None or not words:
        return None
    candidates = [r for r in stream.records if r.kind != 'plan' and any(w in r.text.lower() for w in words)]
    if not candidates:
        return None
    memory = max(candidates, key=lambda r: (r.importance, r.tick))
    said = _clean(memory.text)
    when = f"day {memory.tick // 144 + 1}"
    heard = said.split(' told me: ', 1)
    told_by = heard[0] if len(heard) == 2 else None
    what = heard[1] if told_by else said
    what = _clean(what)
    if story_type == StoryType.WARNING:
        title, tone = f"⚠️ Warning: what {name} {'heard' if told_by else 'saw'}", StoryTone.TRAGIC
        text = (f"{name} passes on, as a warning, what {told_by} told them on {when}: “{what}.” Take care."
                if told_by else f"{name} tells, as a warning, of {when}: “{what}.” Take care.")
    elif story_type == StoryType.LEGEND:
        title, tone = f"⚔️ Legend, told by {name}", StoryTone.EPIC
        text = (f"{name} tells, as {told_by} told it, how {what[:1].lower() + what[1:]}. Each telling makes it a little grander."
                if told_by else f"{name} tells how, on {when}, {what[:1].lower() + what[1:]}. Each telling makes it a little grander.")
    elif story_type == StoryType.SONG:
        title, tone = f"🎵 Song: {name} sings of {when}", StoryTone.ROMANTIC
        text = f"{name} makes a song of {when}: “{what}.”"
    else:
        cause = _MYTH_CAUSES[sum(map(ord, agent.id + str(memory.tick))) % len(_MYTH_CAUSES)]
        title, tone = f"🌟 Myth, told by {name}", StoryTone.DRAMATIC
        text = f"Of {when} (“{what}”), {name} says it happened because {cause}."
    return Story(story_type, title, text, tone, [agent.id], day, importance,
                 ["agent_created", "culture", story_type.value], tick=tick, source=memory.text)


def teacher_name(ledger, teacher_id) -> str:
    sim = getattr(ledger, 'sim', None)
    other = sim._get_agent_by_id(teacher_id) if sim is not None and teacher_id else None
    return other.name if other is not None else "someone"


class StoryFeed:
    """Manages the story feed - keeps best stories"""
    
    def __init__(self, max_stories: int = 100):
        self.stories: List[Story] = []
        self.max_stories = max_stories
        
    def add_story(self, story: Story):
        """Add story to feed"""
        self.stories.insert(0, story)  # Most recent first
        
        # Keep only max stories
        if len(self.stories) > self.max_stories:
            # Keep the most important stories
            self.stories.sort(key=lambda s: s.importance, reverse=True)
            self.stories = self.stories[:self.max_stories]
            # Re-sort by time
            self.stories.sort(key=lambda s: s.timestamp, reverse=True)
    
    def get_recent_stories(self, count: int = 10) -> List[Story]:
        """Get most recent stories"""
        return self.stories[:count]
    
    def get_epic_stories(self, count: int = 5) -> List[Story]:
        """Get most epic/important stories"""
        sorted_stories = sorted(self.stories, key=lambda s: s.importance, reverse=True)
        return sorted_stories[:count]
    
    def to_dict(self) -> Dict:
        """Serialize to dict for API"""
        return {
            'recent_stories': [
                {
                    'type': s.story_type.value,
                    'title': s.title,
                    'narrative': s.narrative,
                    'tone': s.tone.value,
                    'day': s.day,
                    'importance': s.importance,
                    'tags': s.tags,
                    'timestamp': s.timestamp.isoformat(),
                    'tellers': list(s.agent_ids),
                    'source': getattr(s, 'source', None),
                }
                for s in self.get_recent_stories(20)
            ],
            'epic_stories': [
                {
                    'type': s.story_type.value,
                    'title': s.title,
                    'narrative': s.narrative,
                    'tone': s.tone.value,
                    'day': s.day,
                    'importance': s.importance,
                    'tags': s.tags,
                }
                for s in self.get_epic_stories(10)
            ]
        }
