"""
The AI brain's menu, prompt and answer parsing, tested with a fake LLM (no network).

    python3 -m pytest tests/test_llm_brain.py -q
"""

import contextlib
import io
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ENABLE_SEMANTIC_MEMORY", "false")


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def make_world(use_llm=True, seed=0):
    import logging
    import config
    logging.disable(logging.WARNING)
    os.environ["USE_LLM_DECISIONS"] = "true" if use_llm else "false"
    config.reset_config()
    random.seed(seed)
    with quiet():
        from engine.simulation import SimulationEngine
        sim = SimulationEngine(world_width=100, world_height=100)
        sim.initialize_world(num_agents=4)
    from agents.agent import Position
    for i, agent in enumerate(sim.world.agents):
        agent.location = Position(50 + i, 50)
        for need in agent.needs.needs.values():
            need.level = 0.2  # nobody urgent, so the AI brain is asked
        agent.energy = 90.0
    return sim


class FakeLLM:
    """Stands in for MultiLLMBrain.call_llm: returns canned answers, records prompts."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.prompts = []

    def __call__(self, provider, prompt, temperature=0.7, max_tokens=200):
        from agents.llm_brain import LLMResponse
        self.prompts.append(prompt)
        text = self.answers.pop(0) if self.answers else None
        return LLMResponse(text=text, provider=provider, response_time=0.0) if text else None


def decide(sim, agent):
    perceptions = sim._perception_builder.build_perceptions(agent, sim.world.get_state())
    agent.last_perception = perceptions
    with quiet():
        action, _ = __import__("asyncio").run(
            sim._agent_updater._make_agent_decision(agent, perceptions, sim.world.time.current_tick))
    return action


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

def test_menu_offers_every_action_the_engine_can_run():
    from agents.agent import ActionType
    from agents.action_menu import INTERNAL_ACTIONS
    from engine.simulation import UNHANDLED_ACTION_FALLBACKS
    sim = make_world()
    menu = sim.llm_brain.action_menu
    registry = sim._handler_registry
    for action_type in ActionType:
        name = action_type.value
        runs = name if registry.get_handler(action_type) else UNHANDLED_ACTION_FALLBACKS.get(name)
        if name in INTERNAL_ACTIONS or runs is None:
            continue
        assert name in menu.names, name
        assert name in menu.text, name
    assert not INTERNAL_ACTIONS & menu.names


def test_prompt_contains_menu_format_and_people():
    sim = make_world()
    agent, other = sim.world.agents[0], sim.world.agents[1]
    perceptions = sim._perception_builder.build_perceptions(agent, sim.world.get_state())
    agent.last_perception = perceptions
    with quiet():
        prompt = sim.llm_brain._build_thinking_prompt(agent, perceptions, "decide_action")
    assert "Religion:" in prompt and "perform_ritual" in prompt and "mint_coins" in prompt
    assert "ACTION:" in prompt and "TARGET:" in prompt
    assert other.name in prompt          # nearby people by name
    assert "Governments: none yet" in prompt
    assert len(prompt) < 9000, len(prompt)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

VALID = {"eat", "create_art", "build", "build_temple", "make_law", "gather_food", "gather_materials",
         "vote", "seek_romance", "tell_story", "rest"}
PEOPLE = {"brian": "id-brian", "mary": "id-mary"}


@pytest.mark.parametrize("answer, expected", [
    ("ACTION: create_art\nREASON: I feel inspired", "create_art"),            # not 'eat'
    ("**ACTION:** `gather_food`\nREASON: hungry", "gather_food"),             # markdown
    ("Action: Make Law\nDETAILS: no stealing", "make_law"),                     # spaces, case
    ("ACTION: build_temple for our gods", "build_temple"),                     # longest name wins
    ("ACTION: [build]", "build"),
    ("I think I'll rest.\nACTION: rest", "rest"),
])
def test_parse_reads_the_action(answer, expected):
    from agents.action_menu import parse_decision
    assert parse_decision(answer, VALID, PEOPLE).action == expected


@pytest.mark.parametrize("answer", [
    "ACTION: daydream", "I will gather some food", "", "ACTION:", "REASON: no action line",
])
def test_parse_refuses_to_guess(answer):
    from agents.action_menu import parse_decision
    assert parse_decision(answer, VALID, PEOPLE) is None


def test_parse_target_and_details():
    from agents.action_menu import parse_decision
    d = parse_decision("ACTION: seek_romance\nTARGET: Mary\nREASON: I like her", VALID, PEOPLE)
    assert d.target_id == "id-mary" and d.reason == "I like her"
    d = parse_decision("ACTION: tell_story\nTARGET: brian smith", VALID, PEOPLE)
    assert d.target_id == "id-brian"
    d = parse_decision("ACTION: vote\nTARGET: none\nDETAILS: no, it's unfair", VALID, PEOPLE)
    assert d.target_id is None and d.details.startswith("no")


# ---------------------------------------------------------------------------
# End to end with a fake model
# ---------------------------------------------------------------------------

def test_ai_choice_is_used_with_its_target():
    sim = make_world()
    agent, other = sim.world.agents[0], sim.world.agents[1]
    fake = FakeLLM([f"ACTION: tell_story\nTARGET: {other.name}\nREASON: they look bored"])
    sim.llm_brain.call_llm = fake
    action = decide(sim, agent)
    assert action.action_type.value == "tell_story"
    assert action.target_agent == other.id
    assert action.parameters.get("reason") == "they look bored"
    assert sim.llm_brain.decisions_parsed == 1 and sim.llm_brain.parse_failures == 0
    assert "tell_story" in fake.prompts[0]


def test_unreadable_answer_is_counted_and_rule_brain_decides():
    sim = make_world()
    agent = sim.world.agents[0]
    sim.llm_brain.call_llm = FakeLLM(["I am not sure what to do today."])
    action = decide(sim, agent)
    assert action is not None
    assert sim.llm_brain.parse_failures == 1
    assert sim.llm_brain.last_parse_failures[-1].startswith("I am not sure")


def test_no_model_means_rule_brain():
    sim = make_world()
    agent = sim.world.agents[0]
    sim.llm_brain.call_llm = FakeLLM([])  # every call: no answer
    with quiet():
        assert agent.autonomous_decide(getattr(agent, "last_perception", None) or {}, 0, sim.config) is None
    assert decide(sim, agent) is not None


# ---------------------------------------------------------------------------
# Providers: which models get asked, and the local Ollama call
# ---------------------------------------------------------------------------

class _FakeOllama:
    """A local HTTP server that answers /api/generate like Ollama and records requests."""

    def __init__(self, answer):
        import http.server
        import json
        import threading
        requests_seen = self.requests = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests_seen.append((self.path, body))
                data = json.dumps({"response": answer}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()


def _brain(**env):
    import config
    from agents.llm_brain import MultiLLMBrain
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        config.reset_config()
        cfg = config.load_config() if hasattr(config, "load_config") else config.Config()
        return MultiLLMBrain(api_keys=cfg.get_api_keys(), config=cfg)
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        config.reset_config()


def test_without_cloud_keys_the_local_model_is_asked():
    from agents.llm_brain import MultiLLMBrain, LLMProvider
    brain = MultiLLMBrain(api_keys={})
    assert brain.providers_to_try() == [LLMProvider.OLLAMA_LOCAL]
    brain = MultiLLMBrain(api_keys={"groq": "key"})
    assert brain.providers_to_try() == [LLMProvider.GROQ, LLMProvider.OLLAMA_LOCAL]


def test_ollama_call_uses_the_configured_server_model_and_context():
    fake = _FakeOllama("ACTION: rest\nREASON: tired")
    try:
        brain = _brain(OLLAMA_BASE_URL=fake.url, OLLAMA_MODEL="tiny-model:1b", OLLAMA_NUM_CTX="8192")
        assert brain.complete("What now?") == "ACTION: rest\nREASON: tired"
    finally:
        fake.close()
    path, body = fake.requests[0]
    assert path == "/api/generate" and body["model"] == "tiny-model:1b"
    assert body["options"]["num_ctx"] == 8192 and body["prompt"] == "What now?"
    assert brain.calls == 1 and brain.call_failures == 0


def test_a_down_ollama_is_skipped_for_a_while():
    import socket
    from agents.llm_brain import LLMProvider
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # nothing listens here
    brain = _brain(OLLAMA_BASE_URL=f"http://127.0.0.1:{port}")
    assert brain.complete("What now?") is None
    assert LLMProvider.OLLAMA_LOCAL not in brain.providers_to_try()
    assert brain.complete("What now?") is None and brain.calls == 1  # not asked again
