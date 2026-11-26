"""
Stories are told from what the teller remembers (engine/storytelling.py
story_from_memory). They used to be fixed templates picked at random ("I
once saw someone wander too far... they never returned"), whatever had
happened, and stories told while resting were dated day 0.

    python3 -m pytest tests/test_stories.py -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_reachability import make_world, quiet  # noqa: E402


def test_a_warning_is_told_from_something_the_teller_saw_or_heard():
    from engine.storytelling import StoryType, story_from_memory
    sim, roles = make_world()
    a = roles["actor"]
    a.memory_stream.records.clear()
    assert story_from_memory(a, StoryType.WARNING, 300) is None        # nothing to tell, no story
    a.memory_stream.add(290, "Mira told me: 💀 Tom died of starvation", 0.8)
    story = story_from_memory(a, StoryType.WARNING, 300)
    assert story.day == 3 and story.tick == 300 and story.agent_ids == [a.id]
    assert "Mira told them" in story.narrative and "Tom died of starvation" in story.narrative
    assert story.source.endswith("Tom died of starvation")


def test_a_teaching_passes_on_know_how_as_it_was_learned():
    from engine.storytelling import StoryType, story_from_memory
    from test_knowhow import dawn_world
    sim, roles = dawn_world()
    a, b = roles["actor"], roles["partner"]
    with quiet():
        sim.knowhow.learn(a, "stone_tools", "insight", 30)
        sim.knowhow.learn(b, "stone_tools", "taught", 40, teacher=a)
    story = story_from_memory(b, StoryType.TEACHING, 50, sim.knowhow)
    assert story.narrative == f"{b.name} passes on making stone tools, as {a.name} taught it to them."


def test_resting_storytellers_date_their_stories():
    from engine.storytelling import StoryType
    sim, roles = make_world()
    a = roles["actor"]
    sim.world.time.current_tick = 144 * 4 + 10
    a.memory_stream.add(144 * 4, "🎉 Ann's gathering at the clearing: 6 came", 0.7)
    a.personality.openness = 1.0
    import random
    for seed in range(60):                                     # rest tells a story now and then
        random.seed(seed)
        sim.interaction_handler.handle_rest(a)
    told = [s for s in sim.story_feed.stories if s.agent_ids == [a.id]]
    assert told and all(s.day == 5 for s in told)
    assert all(s.story_type in (StoryType.TEACHING, StoryType.WARNING, StoryType.MYTH, StoryType.SONG) for s in told)
