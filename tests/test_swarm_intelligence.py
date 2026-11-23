"""
Swarm intelligence (agents/swarm_intelligence.py): group decisions by
opinion, debate and consensus; alliances and rivalries.

    python3 -m pytest tests/test_swarm_intelligence.py -q

The engine builds this system when the AI brain is on but doesn't call it
yet, so these tests pin down what it does. The model is faked: no network.
(This file used to be a script: its tests needed fixtures that didn't exist,
async tests pytest couldn't run, and every check was inside a try/except
that printed the error, so nothing could fail.)
"""

import asyncio
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.swarm_intelligence import ConsensusType, SwarmIntelligence  # noqa: E402


class FakeBrain:
    """The two calls the swarm makes on MultiLLMBrain. `answer` maps a
    prompt to the model's text (None = no answer, as with no model)."""

    def __init__(self, answer):
        self.answer = answer
        self.prompts = []

    def get_available_provider(self, complexity="simple"):
        return "fake"

    def call_llm(self, provider, prompt, temperature=0.7, max_tokens=150):
        self.prompts.append(prompt)
        text = self.answer(prompt)
        return None if text is None else SimpleNamespace(text=text)


def villagers(n):
    kinds = ["aggressive", "peaceful", "cautious", "adventurous", "balanced"]
    return [SimpleNamespace(agent_id=f"agent_{i}", name=f"Agent{i}", personality=kinds[i % len(kinds)])
            for i in range(n)]


def make_swarm(answer, parallel=False):
    return SwarmIntelligence(llm_brain=FakeBrain(answer), config={
        'max_swarm_size': 10, 'consensus_threshold': 0.6,
        'coordination_radius': 5.0, 'enable_parallel_llm': parallel})


def test_it_starts_empty_with_its_settings():
    swarm = make_swarm(lambda p: None)
    assert (swarm.max_swarm_size, swarm.consensus_threshold, swarm.coordination_radius) == (10, 0.6, 5.0)
    stats = swarm.get_statistics()
    assert stats['total_swarm_decisions'] == 0 and stats['emergent_alliances'] == 0


def test_an_agent_weighs_what_its_neighbours_intend():
    swarm = make_swarm(lambda p: "DECISION: A | REASONING: my ally is gathering too")
    me, *others = villagers(4)
    swarm.alliances[me.agent_id] = [others[0].agent_id]
    decision, why = asyncio.run(swarm.social_network_decision(
        agent=me, action_type="gather_food", nearby_agents=others, context={}))
    assert decision == "coordinate_with_allies" and "ally" in why
    assert swarm.intentions[me.agent_id].action_type == "gather_food"


def test_with_no_model_an_agent_acts_on_its_own():
    swarm = make_swarm(lambda p: None)
    me, *others = villagers(3)
    decision, why = asyncio.run(swarm.social_network_decision(
        agent=me, action_type="explore", nearby_agents=others, context={}))
    assert decision == "explore" and "No social coordination" in why


@pytest.mark.parametrize("parallel", [False, True])
def test_the_group_settles_on_the_option_most_choose(parallel):
    # everyone first answers by personality; in the debate the cautious and
    # peaceful come round to option 2
    def answer(prompt):
        if "Reconsidering" in prompt:
            return "CHOICE: 2 | REASON: the hill is safer"
        return "CHOICE: 1 | REASON: water first" if "aggressive" in prompt else "CHOICE: 2 | REASON: defence"
    swarm = make_swarm(answer, parallel=parallel)
    result = asyncio.run(swarm.emergent_consensus(
        agents=villagers(6), decision_topic="Where to build?",
        options=["By the river", "On the hill", "In the forest"], consensus_type=ConsensusType.MAJORITY))
    assert result.decision == "option_2" and result.consensus_level == 1.0
    assert len(result.participants) == 6
    assert swarm.get_statistics()['total_swarm_decisions'] == 1


def test_a_split_group_keeps_the_dissent():
    picks = {}

    def answer(prompt):
        # agents 0-3 choose 1, agents 4-5 choose 3, and nobody changes their mind
        for i in range(6):
            if f"As Agent{i}," in prompt:
                picks[i] = 1 if i < 4 else 3
                return f"CHOICE: {picks[i]} | REASON: mine"
        return None
    swarm = make_swarm(answer)
    result = asyncio.run(swarm.emergent_consensus(
        agents=villagers(6), decision_topic="Which to research?", options=["Farming", "Metal", "Writing"]))
    assert result.decision == "option_1" and abs(result.consensus_level - 4 / 6) < 1e-9
    assert result.dissenting_opinions == ["Option 3: 2 votes"]


def test_no_one_to_decide_means_no_decision():
    swarm = make_swarm(lambda p: "CHOICE: 1 | REASON: x")
    result = asyncio.run(swarm.emergent_consensus(agents=[], decision_topic="?", options=["a", "b"]))
    assert result.consensus_level == 0.0 and result.participants == []
    assert swarm.llm_brain.prompts == []


def test_alliances_and_rivalries_follow_what_happened():
    swarm = make_swarm(lambda p: None)
    swarm.update_relationships("alpha", "beta", interaction_type="cooperate", success=True)
    assert "beta" in swarm.get_agent_allies("alpha")
    swarm.update_relationships("alpha", "gamma", interaction_type="compete", success=False)
    assert "gamma" in swarm.get_agent_rivals("alpha")
    swarm.update_relationships("alpha", "beta", interaction_type="attack", success=True)
    assert "beta" not in swarm.get_agent_allies("alpha") and "beta" in swarm.get_agent_rivals("alpha")
