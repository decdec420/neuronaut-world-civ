"""
Multi-LLM Agent Brain - TRUE AUTONOMY with Free LLMs

This system gives agents UNLIMITED decision-making power using multiple free LLM providers.
Agents can think, plan, reason, and make complex decisions like real people.

Key Features:
- Rotates between multiple free LLM providers to avoid rate limits
- Agents make autonomous decisions based on their psychology
- Long-term planning and goal setting
- Memory-based learning from past experiences
- NO artificial constraints on agent thinking

Supported Providers:
- Ollama (local, unlimited, always available)
- Groq (30/min, 14,400/day - very fast)
- Google Gemini Flash (15/min, 1,500/day - smart)
- Hugging Face (30,000/month)
- Together AI (60/min with free credits)
"""

import requests
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    OLLAMA_LOCAL = "ollama"
    GROQ = "groq"
    GEMINI_FLASH = "gemini_flash"
    HUGGING_FACE = "huggingface"
    TOGETHER_AI = "together"


@dataclass
class LLMResponse:
    """Response from LLM"""
    text: str
    provider: LLMProvider
    tokens_used: int = 0
    response_time: float = 0.0


class RateLimiter:
    """
    Track usage across all LLM providers to maximize free tier usage
    """

    def __init__(self):
        # Rate limits for each provider
        self.limits = {
            LLMProvider.GROQ: {
                "per_minute": 30,
                "per_day": 14400
            },
            LLMProvider.GEMINI_FLASH: {
                "per_minute": 15,
                "per_day": 1500
            },
            LLMProvider.HUGGING_FACE: {
                "per_minute": 100,
                "per_month": 30000
            },
            LLMProvider.TOGETHER_AI: {
                "per_minute": 60,
                "per_day": 10000
            }
        }

        # Usage tracking
        self.usage = {}
        for provider in self.limits.keys():
            self.usage[provider] = {
                "minute_count": 0,
                "day_count": 0,
                "month_count": 0,
                "last_reset_minute": datetime.now(),
                "last_reset_day": datetime.now(),
                "last_reset_month": datetime.now()
            }

    def reset_if_needed(self, provider: LLMProvider):
        """Reset counters when time windows expire"""
        if provider == LLMProvider.OLLAMA_LOCAL:
            return

        now = datetime.now()
        usage = self.usage[provider]

        # Reset minute counter
        if (now - usage["last_reset_minute"]).seconds >= 60:
            usage["minute_count"] = 0
            usage["last_reset_minute"] = now

        # Reset day counter
        if (now - usage["last_reset_day"]).days >= 1:
            usage["day_count"] = 0
            usage["last_reset_day"] = now

        # Reset month counter
        if (now - usage["last_reset_month"]).days >= 30:
            usage["month_count"] = 0
            usage["last_reset_month"] = now

    def can_use(self, provider: LLMProvider) -> bool:
        """Check if provider is available within rate limits"""
        if provider == LLMProvider.OLLAMA_LOCAL:
            return True  # Always available

        self.reset_if_needed(provider)
        usage = self.usage[provider]
        limits = self.limits[provider]

        # Check all applicable limits
        if limits.get("per_minute") and usage["minute_count"] >= limits["per_minute"]:
            return False
        if limits.get("per_day") and usage["day_count"] >= limits["per_day"]:
            return False
        if limits.get("per_month") and usage["month_count"] >= limits["per_month"]:
            return False

        return True

    def record_usage(self, provider: LLMProvider):
        """Record that we used this provider"""
        if provider == LLMProvider.OLLAMA_LOCAL:
            return

        usage = self.usage[provider]
        usage["minute_count"] += 1
        usage["day_count"] += 1
        usage["month_count"] += 1

        logger.debug(f"[{provider.value}] Usage: {usage['minute_count']}/min, {usage['day_count']}/day")


class MultiLLMBrain:
    """
    Intelligent agent brain using multiple free LLM providers

    This gives agents TRUE AUTONOMY:
    - Unlimited decisions (rotates providers)
    - Complex reasoning and planning
    - Memory-based learning
    - Long-term goal setting
    - Creative problem solving
    """

    # The key each cloud provider needs (in api_keys); Ollama needs none
    KEY_NAMES = {
        LLMProvider.GROQ: 'groq', LLMProvider.TOGETHER_AI: 'together',
        LLMProvider.GEMINI_FLASH: 'gemini', LLMProvider.HUGGING_FACE: 'huggingface',
    }
    OLLAMA_RETRY_AFTER = 30.0  # seconds to wait before trying a down Ollama again

    def __init__(self, api_keys: Dict[str, str] = None, config=None):
        self.api_keys = api_keys or {}
        self.rate_limiter = RateLimiter()

        # Local model (config.py: OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_NUM_CTX, LLM_TIMEOUT)
        self.ollama_url = (getattr(config, 'ollama_host', None) or 'http://localhost:11434').rstrip('/')
        self.ollama_model = getattr(config, 'ollama_model', None) or 'llama3.2:3b'
        self.ollama_num_ctx = getattr(config, 'ollama_num_ctx', 4096)
        self.timeout = getattr(config, 'llm_timeout', 60.0)
        self.context_chars = getattr(config, 'llm_context_chars', 1800)
        self._ollama_retry_at = 0.0

        # Calls, failures and time spent (model calls can run in threads)
        self._stats_lock = threading.Lock()
        self.calls = 0
        self.call_failures = 0
        self.total_latency = 0.0

        # Provider priority (fastest/best first, fallback to local)
        self.provider_priority = [
            LLMProvider.GROQ,           # Fastest, use first
            LLMProvider.TOGETHER_AI,    # Also fast
            LLMProvider.GEMINI_FLASH,   # Smart but limited
            LLMProvider.HUGGING_FACE,   # Large monthly limit
            LLMProvider.OLLAMA_LOCAL,   # Unlimited fallback
        ]

        # Statistics
        self.total_decisions = 0
        self.provider_usage = {p: 0 for p in LLMProvider}

        # The action menu (set by the simulation from its handler registry) and
        # how often answers could / couldn't be read as a listed action
        self.action_menu = None
        self.decisions_parsed = 0
        self.parse_failures = 0
        self.last_parse_failures: List[str] = []  # a few recent unreadable answers, for debugging

    def __getstate__(self) -> Dict:
        state = self.__dict__.copy()
        state.pop('_stats_lock', None)  # a lock can't be saved; a new one is made on load
        return state

    def __setstate__(self, state: Dict) -> None:
        self.__dict__.update(state)
        self._stats_lock = threading.Lock()

    def set_action_menu(self, menu) -> None:
        """Use this menu (agents.action_menu.ActionMenu) in decision prompts."""
        self.action_menu = menu

    def record_parse(self, ok: bool, response: str = "") -> None:
        if ok:
            self.decisions_parsed += 1
        else:
            self.parse_failures += 1
            self.last_parse_failures = (self.last_parse_failures + [response[:200]])[-5:]
            logger.warning(f"Could not read an action from the AI answer: {response[:120]!r}")

    def get_available_provider(self, complexity: str = "simple") -> LLMProvider:
        """
        Get best available provider for this decision

        complexity: "simple" or "complex"
        - Simple: Use fastest provider
        - Complex: Use smartest available provider
        """

        candidates = self.providers_to_try(complexity)
        return candidates[0] if candidates else LLMProvider.OLLAMA_LOCAL

    def _configured(self, provider: LLMProvider) -> bool:
        """A cloud provider counts only with its API key; Ollama unless it was
        just found down."""
        if provider == LLMProvider.OLLAMA_LOCAL:
            return time.monotonic() >= self._ollama_retry_at
        return bool(self.api_keys.get(self.KEY_NAMES[provider]))

    def providers_to_try(self, complexity: str = "simple") -> List[LLMProvider]:
        """Providers to ask, in order: configured ones within their rate limits.

        (This used to pick the first provider within its rate limits whether or
        not it had a key, so with no cloud keys every call went to Groq, failed,
        and never reached Ollama.)"""
        if complexity == "complex":
            priority = [LLMProvider.GEMINI_FLASH, LLMProvider.GROQ, LLMProvider.TOGETHER_AI,
                        LLMProvider.HUGGING_FACE, LLMProvider.OLLAMA_LOCAL]
        else:
            priority = self.provider_priority
        return [p for p in priority if self._configured(p) and self.rate_limiter.can_use(p)]

    def call_llm(
        self,
        provider: LLMProvider,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 200,
        json_schema: Optional[Dict] = None
    ) -> Optional[LLMResponse]:
        """
        Make LLM call to specified provider

        Returns LLMResponse or None if failed
        """

        start_time = datetime.now()

        try:
            # Route to appropriate provider
            if provider == LLMProvider.OLLAMA_LOCAL:
                response_text = self._call_ollama(prompt, temperature, max_tokens, json_schema)
            elif provider == LLMProvider.GROQ:
                response_text = self._call_groq(prompt, temperature, max_tokens)
            elif provider == LLMProvider.GEMINI_FLASH:
                response_text = self._call_gemini(prompt, temperature, max_tokens)
            elif provider == LLMProvider.HUGGING_FACE:
                response_text = self._call_huggingface(prompt, temperature, max_tokens)
            elif provider == LLMProvider.TOGETHER_AI:
                response_text = self._call_together(prompt, temperature, max_tokens)
            else:
                logger.warning(f"Unknown provider: {provider}")
                return None

            response_time = (datetime.now() - start_time).total_seconds()
            with self._stats_lock:
                self.calls += 1
                self.total_latency += response_time
                if not response_text:
                    self.call_failures += 1
            if response_text:
                # Record usage
                self.rate_limiter.record_usage(provider)
                self.provider_usage[provider] += 1

                return LLMResponse(
                    text=response_text,
                    provider=provider,
                    response_time=response_time
                )

            return None

        except Exception as e:
            logger.error(f"LLM call failed for {provider.value}: {e}")
            with self._stats_lock:
                self.calls += 1
                self.call_failures += 1
            return None

    def _call_ollama(self, prompt: str, temperature: float, max_tokens: int,
                     json_schema: Optional[Dict] = None) -> Optional[str]:
        """Call the local Ollama model set in .env (it used to ignore the
        settings: always localhost and llama3.2:3b, with Ollama's default
        context window, which can cut a decision prompt short)."""
        body = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",  # stay loaded between ticks
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.ollama_num_ctx,
            }
        }
        if json_schema is not None:
            # Structured output: the model can only answer with a listed action.
            # Without it, small models write "EAT: None" or "Explore - follow"
            # about half the time.
            body["format"] = json_schema
        try:
            response = requests.post(f'{self.ollama_url}/api/generate', json=body, timeout=self.timeout)

            if response.status_code == 200:
                return response.json().get('response', '')

            logger.warning(f"Ollama returned status {response.status_code}: {response.text[:200]}")
            return None

        except requests.exceptions.ConnectionError:
            # Don't make every agent wait on a server that isn't there
            self._ollama_retry_at = time.monotonic() + self.OLLAMA_RETRY_AFTER
            logger.warning(f"Ollama not reachable at {self.ollama_url}. Start it with: ollama serve")
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"Ollama took longer than {self.timeout:.0f}s; the agent uses the rule-based brain")
            return None
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    def _call_groq(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Call Groq API - very fast, 30/min limit"""
        api_key = self.api_keys.get('groq')
        if not api_key:
            return None

        try:
            from groq import Groq

            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated to current model
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq error: {e}")
            return None

    def _call_gemini(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Call Google Gemini Flash - smart, 15/min limit"""
        api_key = self.api_keys.get('gemini')
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # Try multiple model names (Google keeps changing them)
            model_names = [
                'models/gemini-2.5-flash',
                'models/gemini-flash-latest',
                'models/gemini-2.0-flash',
                'models/gemini-pro-latest'
            ]

            for model_name in model_names:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens
                        )
                    )
                    return response.text
                except Exception as model_error:
                    # Try next model name
                    logger.debug(f"Gemini model {model_name} failed: {model_error}")
                    continue

            # If all models failed
            logger.error(f"Gemini error: All model names failed")
            return None

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None

    def _call_huggingface(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Call Hugging Face API - 30k/month free tier"""
        api_key = self.api_keys.get('huggingface')
        if not api_key:
            return None

        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "temperature": temperature,
                        "max_new_tokens": max_tokens
                    }
                },
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')

            return None

        except Exception as e:
            logger.error(f"Hugging Face error: {e}")
            return None

    def _call_together(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Call Together AI - fast, good free tier"""
        api_key = self.api_keys.get('together')
        if not api_key:
            return None

        try:
            response = requests.post(
                "https://api.together.xyz/v1/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "meta-llama/Llama-3-8b-chat-hf",
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=15
            )

            if response.status_code == 200:
                return response.json()['choices'][0]['text']

            return None

        except Exception as e:
            logger.error(f"Together AI error: {e}")
            return None

    def agent_think(
        self,
        agent,
        perceptions: Dict,
        thinking_mode: str = "decide_action"
    ) -> Optional[str]:
        """
        Agent uses AI to think about their situation

        thinking_mode options:
        - "decide_action": What should I do right now?
        - "long_term_planning": What are my goals for the next week/month?
        - "reflection": What have I learned? How do I feel about my life?
        - "social_strategy": How should I interact with others?
        - "creative_thinking": What new ideas can I discover?
        """

        # Determine complexity
        complexity = self._assess_complexity(agent, perceptions, thinking_mode)

        # Build prompt based on thinking mode
        prompt = self._build_thinking_prompt(agent, perceptions, thinking_mode)
        schema = self.decision_schema() if thinking_mode == "decide_action" else None
        return self.complete(prompt, complexity, label=f"{agent.name}: {thinking_mode}", json_schema=schema)

    def think(self, prompt: str, schema: Optional[Dict] = None) -> Optional[str]:
        """One agent thought (agents/thinking.py calls this from worker threads)."""
        return self.complete(prompt, label="thought", json_schema=schema)

    def complete(self, prompt: str, complexity: str = "simple", label: str = "",
                 temperature: float = 0.8, max_tokens: int = 300,
                 json_schema: Optional[Dict] = None) -> Optional[str]:
        """Ask each configured provider in turn; the first answer wins.
        json_schema: hold the answer to this shape where the provider can
        (Ollama); others get the prompt's own format instructions.
        Safe to call from worker threads."""
        for provider in self.providers_to_try(complexity):
            if json_schema is not None and provider == LLMProvider.OLLAMA_LOCAL:
                response = self.call_llm(provider, prompt, temperature=temperature, max_tokens=max_tokens,
                                         json_schema=json_schema)
            else:
                response = self.call_llm(provider, prompt, temperature=temperature, max_tokens=max_tokens)
            if response:
                with self._stats_lock:
                    self.total_decisions += 1
                logger.info(f"🧠 {label} via {provider.value} ({response.response_time:.1f}s)")
                return response.text
        return None

    def decision_preamble(self) -> str:
        """The fixed opening of every decision prompt: the menu and the answer format."""
        from agents.action_menu import RESPONSE_FORMAT
        menu_text = self.action_menu.text if self.action_menu else "(no actions available)"
        return ("You are a person living in a small village. Each turn you decide what to do next.\n\n"
                "What you can do (write the action name exactly as listed):\n"
                f"{menu_text}\n\n{RESPONSE_FORMAT}\n\n")

    def decision_schema(self) -> Optional[Dict]:
        """JSON schema holding a model's answer to the menu (where supported)."""
        from agents.action_menu import decision_schema
        return decision_schema(self.action_menu.names) if self.action_menu else None

    def _assess_complexity(self, agent, perceptions: Dict, thinking_mode: str) -> str:
        """Determine if this requires simple or complex reasoning"""

        # Long-term planning and creative thinking need smart models
        if thinking_mode in ["long_term_planning", "creative_thinking", "reflection"]:
            return "complex"

        # Social situations with multiple agents need smart models
        if len(perceptions.get('nearby_agents', [])) > 3:
            return "complex"

        # Creative/ambitious agents get smarter models
        if agent.personality.creativity > 0.7 or agent.personality.ambition > 0.7:
            return "complex"

        # Complex inventory/choices need smart models
        if len(agent.inventory.items) > 10:
            return "complex"

        # Simple decisions can use faster models
        return "simple"

    def _build_thinking_prompt(
        self,
        agent,
        perceptions: Dict,
        thinking_mode: str
    ) -> str:
        """Build appropriate prompt for agent's thinking"""

        # Import here to avoid circular imports
        from engine.psychology import NeedType

        # Get agent state
        nearby_agents = perceptions.get('nearby_agents', [])
        nearby_resources = perceptions.get('nearby_resources', [])

        # Format nearby resources (handle both string and dict formats)
        if nearby_resources:
            if isinstance(nearby_resources[0], dict):
                resources_str = ', '.join([r.get('type', str(r)) for r in nearby_resources[:5]])
            else:
                resources_str = ', '.join(nearby_resources[:5])
        else:
            resources_str = 'none visible'

        context = self._describe_agent(agent, perceptions, resources_str)

        # Add thinking mode specific instructions
        if thinking_mode == "decide_action":
            # CRITICAL: Add active goals to context
            goal_context = self._get_goal_context(agent)

            # Add warnings from past consequences
            risk_warnings = self._get_risk_warnings(agent)

            # Add recent memories
            memory_context = self._get_memory_context(agent, perceptions)

            # Add combat context if targets available
            combat_context = self._get_combat_context(agent)

            # Add governance context if relevant
            governance_context = self._get_governance_context(agent)

            # Add scarcity context if relevant
            scarcity_context = self._get_scarcity_context(agent)

            # Add tech progression context
            tech_context = self._get_tech_context(agent)

            # Add weather context
            weather_context = self._get_weather_context(agent)

            # Add buildings context
            buildings_context = self._get_buildings_context(agent)

            # Add knowledge context
            knowledge_context = self._get_knowledge_context(agent)

            # Add disaster context
            disaster_context = self._get_disaster_context(agent)

            # Add experimentation context
            experimentation_context = self._get_experimentation_context(agent)

            # Add roles context
            roles_context = self._get_roles_context(agent)

            # Add innovations context
            innovations_context = self._get_innovations_context(agent)

            # Add fun/entertainment context
            fun_context = self._get_fun_context(agent)

            # Add consequences context
            consequences_context = self._get_consequences_context(agent)

            # Most useful to a decision first: what the agent remembers and is
            # aiming for, then dangers and its surroundings, then the rest
            sections = [memory_context, goal_context, risk_warnings, disaster_context, scarcity_context,
                        governance_context, buildings_context, weather_context, combat_context,
                        roles_context, knowledge_context, experimentation_context, innovations_context,
                        tech_context, fun_context, consequences_context]
            # The same text opens every decision prompt, so a local model can
            # reuse its work on it from one call to the next (Ollama caches a
            # shared prompt prefix); what's particular to this agent follows.
            prompt = self.decision_preamble() + "About you, right now:\n" + context + \
                self._fit_sections(sections) + """
What do you want to do right now? You decide: weigh your needs, your
personality, the people in your life and what you're working toward.
Answer in the format above.
"""

        elif thinking_mode == "long_term_planning":
            prompt = context + f"""
You have COMPLETE FREEDOM to live your life however you want. What are your goals?

Think about:
1. What kind of life do you want to build?
2. What would give your life meaning?
3. What do you want to be known for?
4. What makes you happy?

Examples of goals you could pursue:
- "Become wealthy through trade and innovation"
- "Build a family and raise children"
- "Discover new knowledge through experimentation"
- "Create beautiful art that inspires others"
- "Become a leader and guide the community"
- "Live a simple, peaceful life close to nature"
- "Have fun, make friends, enjoy each day"

What are YOUR personal goals for the next month? List 2-3 goals.
"""

        elif thinking_mode == "reflection":
            # Get recent memories (if available)
            recent_memories = getattr(agent, 'recent_memories', [])[-5:]
            memory_text = '\n'.join([f"- {m}" for m in recent_memories]) if recent_memories else "- [No recent memories]"

            prompt = context + f"""
Recent experiences:
{memory_text}

Reflect on your life:
1. How do you feel about your current situation?
2. What are you proud of? What do you regret?
3. What have you learned recently?
4. What do you want to change about your life?

Be honest and introspective. This is your private thoughts.
"""

        elif thinking_mode == "social_strategy":
            prompt = context + f"""
People nearby: {', '.join([a['name'] for a in nearby_agents]) or 'You are alone'}

Think about your social life:
1. Who do you want to spend time with and why?
2. Are there people you're attracted to or want to befriend?
3. Who do you trust? Who do you avoid?
4. What do you want from your relationships?

What's your social strategy right now?
"""

        elif thinking_mode == "creative_thinking":
            prompt = context + f"""
You have the freedom to experiment, invent, and discover!

Your creative interests:
- Creativity drive: {agent.personality.creativity:.1f}/1.0
- Openness to new ideas: {agent.personality.openness:.1f}/1.0

Think creatively:
1. What new things could you try with the materials you have?
2. What problems could you solve through invention?
3. What would you like to create or discover?
4. What experiments interest you?

Be bold! Think of something interesting to try.
"""

        else:
            # Default general thinking
            prompt = context + "\n\nWhat are you thinking about right now? What matters to you?"

        return prompt

    def _fit_sections(self, sections: List[str]) -> str:
        """As many context sections as fit in context_chars (LLM_CONTEXT_CHARS),
        in order, each compacted. Prompt length is most of a local model's time
        per decision: ~1,000 tokens take ~10 s on a 4-core CPU."""
        out, used = [], 0
        for section in sections:
            text = self._compact(section)
            if not text.strip():
                continue
            if used + len(text) > self.context_chars:
                break
            out.append(text)
            used += len(text)
        return "".join(out)

    @staticmethod
    def _compact(section: str, max_chars: int = 450) -> str:
        """Trim a context section for the prompt: no markdown bold, no blank
        lines, cut at a line boundary. Keeps the decision prompt small enough
        for a local model's context window."""
        lines = [line.replace("**", "").rstrip() for line in section.splitlines() if line.strip()]
        kept, size = [], 0
        for line in lines:
            if size + len(line) > max_chars:
                kept.append("  ...")
                break
            kept.append(line)
            size += len(line) + 1
        return ("\n".join(kept) + "\n") if kept else ""

    def _describe_agent(self, agent, perceptions: Dict, resources_str: str) -> str:
        """Who the agent is and what it knows about its world, compactly."""
        p = agent.personality
        traits = ", ".join(f"{t.replace('_', '-')} {getattr(p, t):.1f}" for t in (
            "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism",
            "ambition", "creativity", "empathy", "risk_taking", "aggression", "sexuality", "rationality"))
        needs = ", ".join(f"{nt.value} {need.level:.2f}" for nt, need in agent.needs.needs.items())
        carried = sorted(((k, v) for k, v in agent.inventory.items.items() if v > 0), key=lambda kv: -kv[1])
        inventory = ", ".join(f"{k} {v}" for k, v in carried[:12]) or "nothing"
        if len(carried) > 12:
            inventory += f" (+{len(carried) - 12} other things)"

        lines = [f"You are {agent.name}, a {agent.age}-year-old {agent.gender.value}."]
        hour = perceptions.get("time_of_day")
        if hour is not None:
            lines.append(f"It is {hour:02d}:00.")
        work_life = getattr(agent, "work_life", None)
        if work_life is not None and work_life.job:
            lines.append(f"Your work: {work_life.to_dict()['job_title']}.")
        lines += [
            f"Personality (0-1): {traits}",
            f"Needs (0 = satisfied, 1 = desperate): {needs}",
            f"Energy {agent.energy:.0f}/100, health {agent.health:.0f}/100, money {agent.wealth:.0f}",
            f"You carry: {inventory} (capacity {agent.inventory.capacity})",
        ]

        nearby = perceptions.get("nearby_agents", [])
        if nearby:
            lines.append("Near you: " + "; ".join(
                f"{a['name']} ({a.get('distance', 0):.0f} away)" for a in nearby[:6]))
        else:
            lines.append("Nobody is near you.")
        lines.append(f"Resources in sight: {resources_str}")

        life = perceptions.get("life_info", {})
        if life:
            heart = [f"Partner: {life['partner']}." if life.get("partner") else "You have no partner."]
            if life.get("admirers"):
                heart.append(f"Courting you: {', '.join(life['admirers'][:4])} (court them back to become partners).")
            if life.get("courting"):
                heart.append(f"You courted {', '.join(life['courting'][:4])}; no answer yet.")
            if life.get("is_pregnant"):
                heart.append("You are expecting a child.")
            if life.get("partner_wants_child"):
                heart.append(f"{life['partner']} has said they want a child with you.")
            if life.get("children"):
                heart.append("Your children: " + "; ".join(
                    f"{c['name']} ({c['age']}, {c['stage']}{', needs looking after' if c['needs_care'] else ''})"
                    for c in life["children"][:6]) + ".")
            if life.get("can_do"):
                heart = [f"You are a {life['life_stage']}"
                         + (f"; your parents are {' and '.join(life['parents'])}" if life.get("parents") else "")
                         + f". You can only: {', '.join(life['can_do'])}."]
            lines.append(" ".join(heart))

        works = perceptions.get("works")
        if works:
            parts = [f"{works['road_tiles']} road tiles", f"{works['wells']} wells", f"{works['street_lights']} street lights"]
            notes = []
            if works.get("lit_lamp_nearby"):
                notes.append("a street light is lit near you")
            elif works.get("lamp_needs_fuel"):
                notes.append("the street light near you has no fuel")
            if works.get("well_nearby"):
                notes.append("there is a well nearby")
            if works.get("walking_lately", 0) > 0.5:
                notes.append("you have been walking a lot lately")
            lines.append("The village has " + ", ".join(parts) + (" (" + "; ".join(notes) + ")" if notes else "") + ".")

        known = perceptions.get("relationships", [])
        if known:
            lines.append("People you know: " + "; ".join(
                f"{r['name']} ({r['type']}, {r['strength']:.1f})" for r in known[:8]))

        community = perceptions.get("community", {})
        for label, key in (("Governments", "governments"), ("Laws", "laws"), ("Religions", "religions")):
            items = community.get(key) or []
            lines.append(f"{label}: " + ("; ".join(items[:5]) if items else "none yet"))
        return "\n".join(lines) + "\n"

    def _get_goal_context(self, agent) -> str:
        """
        CRITICAL FIX #1: Extract agent's active goals for decision-making

        Returns formatted goals that drive agent behavior
        """

        if not hasattr(agent, 'goals'):
            return ""

        # Get top 3 most important goals
        top_goals = agent.goals.get_top_goals(3) if hasattr(agent.goals, 'get_top_goals') else []

        if not top_goals:
            return "\n🎯 **YOUR LIFE GOALS:** None yet - you're just trying to survive.\n\n"

        goal_lines = []
        for i, goal in enumerate(top_goals, 1):
            progress_bar = "█" * int(goal.progress * 10) + "░" * (10 - int(goal.progress * 10))
            goal_lines.append(
                f"{i}. {goal.description} [{progress_bar}] {goal.progress:.0%} (priority: {goal.priority:.1f})"
            )

        return f"""
🎯 **YOUR LIFE GOALS:**
{chr(10).join(goal_lines)}

**IMPORTANT:** Your actions should move you toward these goals! Choose actions that align with what you're trying to achieve in life.

"""

    def _get_memory_context(self, agent, perceptions: Optional[Dict] = None) -> str:
        """The agent's most useful memories right now (agents/memory_stream.py:
        recency + importance + relevance to its needs, people and work) and its
        plan for today. (This used to read memory methods that don't exist, so
        the model never saw a memory.)"""
        stream = getattr(agent, 'memory_stream', None)
        if stream is None:
            return ""
        perceptions = perceptions or {}
        now = perceptions.get('tick', max((r.tick for r in stream.records), default=0))
        urgent = sorted(agent.needs.needs.items(), key=lambda kv: -kv[1].level)[:3]
        about = [nt.value for nt, _ in urgent]
        about += [a['name'] for a in perceptions.get('nearby_agents', [])[:4]]
        life = perceptions.get('life_info', {})
        if life.get('partner'):
            about.append(life['partner'])
        work = getattr(agent, 'work_life', None)
        if work is not None and work.job:
            about.append(work.to_dict().get('job_title', ''))
        lines = [f"- {r.to_dict()['text']}" for r in stream.retrieve(" ".join(about), now, k=5)]
        if stream.day_plan:
            lines.append("Your plan for today: " + "; ".join(
                f"{h:02d}:00 {a}" + (f" ({why})" if why else "") for h, a, why in stream.day_plan))
        return ("What you remember:\n" + "\n".join(lines) + "\n") if lines else ""

    def plan_prompt(self, agent, perceptions: Dict, day: int):
        """(prompt, schema): plan the day, Smallville-style."""
        from agents.action_menu import plan_schema
        prompt = (self.decision_preamble() + "About you, right now:\n"
                  + self._describe_agent(agent, perceptions, "") + self._get_memory_context(agent, perceptions)
                  + f"\nIt is the start of day {day}. Plan your day: up to 5 things you mean to do, "
                    "each with the hour you'll start it (0-23), an action from the list, and why.\n"
                    'This time, answer as JSON: {"plan": [{"hour": 8, "action": "<action>", "why": "<reason>"}]}\n')
        return prompt, plan_schema(self.action_menu.names) if self.action_menu else None

    def reflection_prompt(self, agent, current_tick: int):
        """(prompt, schema): what the agent makes of what has happened lately."""
        from agents.action_menu import INSIGHTS_SCHEMA
        recent = agent.memory_stream.recent(20)
        lines = "\n".join(f"{i}. {r.to_dict()['text']}" for i, r in enumerate(recent, 1))
        prompt = (f"You are {agent.name}, a {agent.age}-year-old living in a small village.\n"
                  f"Things that happened to you lately, oldest first:\n{lines}\n\n"
                  "What do these tell you about your life, the people around you or your village? "
                  "Give 1 to 3 insights, one sentence each, in your own words.\n"
                  'Answer as JSON: {"insights": ["..."]}\n')
        return prompt, INSIGHTS_SCHEMA

    def _get_risk_warnings(self, agent) -> str:
        """
        Extract risk warnings from agent's memory of past consequences

        Returns formatted warnings for the LLM to consider
        """

        warnings = []

        # Check if agent has autonomous memory with risk tracking
        if hasattr(agent, 'memory') and hasattr(agent.memory, 'procedural_memory'):
            # Check for high-risk actions in procedural memory
            for action, risk_level in agent.memory.procedural_memory.items():
                if action.startswith('risk_') and risk_level > 0.6:
                    action_name = action.replace('risk_', '')
                    severity = "VERY DANGEROUS" if risk_level > 0.8 else "DANGEROUS"
                    warnings.append(f"⚠️  {action_name.upper()} is {severity}! (risk: {risk_level:.0%})")

            # Get consequence memories (episodic)
            if hasattr(agent.memory, 'episodic_memory'):
                consequence_memories = [
                    m for m in agent.memory.episodic_memory
                    if m.event_type.startswith('consequence_') and m.importance > 0.5
                ]

                # Add most severe consequences to warnings
                for memory in sorted(consequence_memories, key=lambda m: m.importance, reverse=True)[:3]:
                    warnings.append(f"💀 {memory.description}")

        if warnings:
            return f"""
⚠️  **DANGER WARNINGS:**
{chr(10).join(warnings)}

BE CAREFUL! Avoid repeating past mistakes!

"""
        else:
            return ""

    def _get_combat_context(self, agent) -> str:
        """
        Extract combat opportunities from agent's perceptions

        Returns formatted combat context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception

        # Check for potential combat targets
        combat_targets = perceptions.get('potential_combat_targets', [])
        if not combat_targets:
            return ""

        # Check agent's desperation level
        desperation = perceptions.get('resource_desperation', {})
        hunger = desperation.get('hunger', 0.0)
        thirst = desperation.get('thirst', 0.0)
        has_food = desperation.get('has_food', False)
        has_water = desperation.get('has_water', False)

        # Only show combat context if agent is desperate OR has grudges
        is_desperate = (hunger > 0.7 and not has_food) or (thirst > 0.7 and not has_water)
        has_grudges = any(t.get('grudge_level', 0) > 0.3 for t in combat_targets)

        if not is_desperate and not has_grudges:
            return ""

        # Format combat opportunities
        target_lines = []
        for target in combat_targets[:3]:  # Show top 3 targets
            name = target.get('name', 'Unknown')
            health = target.get('health', 100)
            has_food = "🍖" if target.get('has_food') else ""
            has_water = "💧" if target.get('has_water') else ""
            wealth = target.get('wealth', 0)
            grudge = target.get('grudge_level', 0)
            distance = target.get('distance', 999)

            status = "WEAK" if health < 50 else "healthy"
            resources = f"{has_food}{has_water}" if has_food or has_water else ""
            wealth_str = f"(wealth: {wealth})" if wealth > 50 else ""
            grudge_str = f"[GRUDGE: {grudge:.0%}]" if grudge > 0.3 else ""

            target_lines.append(
                f"  • {name} - {status} ({health}% health) {resources} {wealth_str} {grudge_str} [{distance:.0f}m away]"
            )

        # Build context message based on situation
        if is_desperate:
            urgency = "⚠️  **YOU ARE DESPERATE FOR SURVIVAL!**"
            if hunger > 0.7:
                urgency += f"\n  Hunger: {hunger:.0%} - You need food urgently!"
            if thirst > 0.7:
                urgency += f"\n  Thirst: {thirst:.0%} - You need water urgently!"

            message = f"""
{urgency}

⚔️  **COMBAT OPPORTUNITIES:**
{chr(10).join(target_lines)}

**You could FIGHT for resources.** They have what you need, and some are weak.
But fighting is dangerous - you could get hurt or killed. Is it worth the risk?

"""
        else:
            # Just grudges, not desperate
            message = f"""
⚔️  **POTENTIAL CONFLICTS:**
{chr(10).join(target_lines)}

You have unresolved conflicts with nearby agents. You could FIGHT to settle grudges,
but consider if violence is the answer.

"""

        return message

    def _get_governance_context(self, agent) -> str:
        """
        Extract governance opportunities from agent's situation

        Returns formatted governance context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception

        # Check for governance opportunities
        governance_info = perceptions.get('governance_info', {})
        if not governance_info:
            return ""

        # Check if agent is in a government
        is_citizen = governance_info.get('is_citizen', False)
        is_leader = governance_info.get('is_leader', False)
        can_make_laws = governance_info.get('can_make_laws', False)
        government_name = governance_info.get('government_name', 'Unknown')
        government_type = governance_info.get('government_type', 'unknown')

        # Check political power
        political_power = governance_info.get('political_power', 0.0)
        charisma = agent.personality.charisma if hasattr(agent.personality, 'charisma') else 0.5

        # Build context based on situation
        if is_leader:
            # Agent is already a leader
            active_laws = governance_info.get('active_laws', [])
            approval_rating = governance_info.get('approval_rating', 0.5)

            message = f"""
🏛️  **YOU ARE THE LEADER!**
  Government: {government_name} ({government_type})
  Approval: {approval_rating:.0%}
  Active Laws: {len(active_laws)}

**You can MAKE_LAW to create new rules for your citizens.**
Consider what laws would benefit your people and maintain your power.

"""
            return message

        elif is_citizen:
            # Agent is a citizen
            pending_votes = governance_info.get('pending_votes', [])

            if pending_votes:
                message = f"""
🏛️  **POLITICAL PARTICIPATION:**
  You are a citizen of {government_name}
  Pending votes: {len(pending_votes)}

**You can VOTE on laws and elections to influence your government.**
"""
                return message

            elif can_make_laws and political_power > 0.2:
                message = f"""
🏛️  **POLITICAL OPPORTUNITY:**
  You are a citizen of {government_name} ({government_type})
  Your political power: {political_power:.0%}

**You have enough influence to MAKE_LAW and propose new rules.**
What would make your society better?

"""
                return message

            else:
                # Citizen but no immediate political actions
                return ""

        else:
            # Not in any government - could form one
            nearby_agents = governance_info.get('nearby_agents_count', 0)

            if charisma > 0.6 and nearby_agents >= 2:
                message = f"""
🏛️  **LEADERSHIP OPPORTUNITY:**
  Your charisma: {charisma:.0%}
  Nearby agents: {nearby_agents}

**You could GOVERN and form your own government!**
With your influence and nearby people, you could establish leadership.
Types: strongman (power), democracy (freedom), council (wisdom), oligarchy (elite)

"""
                return message

            elif political_power > 0.3:
                message = f"""
🏛️  **POLITICAL POTENTIAL:**
  Political power: {political_power:.0%}

**You have influence but need more support to GOVERN.**
Build relationships and demonstrate leadership to form a government.

"""
                return message

            else:
                # Not ready for politics
                return ""

    def _get_scarcity_context(self, agent) -> str:
        """
        Extract resource scarcity information

        Returns formatted scarcity context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        scarcity_info = perceptions.get('scarcity_info', {})

        if not scarcity_info:
            return ""

        scarce_resources = scarcity_info.get('scarce_resources', [])
        critical_scarcity = scarcity_info.get('critical_scarcity', [])
        needs_resources = scarcity_info.get('needs_resources', [])

        # If agent has critical scarcity (needs something that's running out)
        if critical_scarcity:
            resource_list = []
            for resource in critical_scarcity:
                name = resource['name']
                ratio = resource['ratio']
                level = resource['level']

                if level == 'CRITICAL':
                    urgency = "🔴 CRITICALLY LOW"
                elif level == 'LOW':
                    urgency = "🟡 RUNNING LOW"
                else:
                    urgency = "🟢 LOW"

                resource_list.append(f"  • {name.upper()}: {urgency} ({ratio:.0%} remaining)")

            message = f"""
⚠️  **RESOURCE CRISIS!**
{chr(10).join(resource_list)}

**The world is running out of critical resources you need!**
Competition will be fierce. Consider gathering NOW before it's too late,
or fighting others for what remains. Resources are finite and depleting fast!

"""
            return message

        # If general scarcity exists (even if agent doesn't need them)
        elif scarce_resources:
            resource_list = []
            for resource in scarce_resources[:3]:  # Top 3 scarce
                name = resource['name']
                ratio = resource['ratio']
                level = resource['level']

                if level == 'CRITICAL':
                    urgency = "🔴 CRITICAL"
                else:
                    urgency = "🟡 LOW"

                resource_list.append(f"  • {name}: {urgency} ({ratio:.0%} left)")

            message = f"""
⚠️  **RESOURCE SCARCITY WARNING:**
{chr(10).join(resource_list)}

The world's resources are depleting. Plan ahead and gather what you can
while supplies last. This could drive competition and conflict.

"""
            return message

        else:
            # No immediate scarcity
            return ""

    def _get_tech_context(self, agent) -> str:
        """
        Extract technological progression information

        Returns formatted tech context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        tech_info = perceptions.get('tech_info', {})

        if not tech_info:
            return ""

        current_era = tech_info.get('current_era', 'Stone Age')
        next_milestones = tech_info.get('next_milestones', [])
        achieved_milestones = tech_info.get('achieved_milestones', [])
        discoverable = tech_info.get('discoverable', [])
        known_discoveries = tech_info.get('known_discoveries', [])

        # Only show tech context if there's something meaningful
        if not next_milestones and not achieved_milestones:
            return ""

        # Build context based on era and opportunities
        message_parts = []

        # Show current era
        message_parts.append(f"🏛️  **CIVILIZATION ERA: {current_era}**")

        # Show recent achievements (if any)
        if achieved_milestones:
            recent = achieved_milestones[-3:]  # Last 3
            achievement_lines = []
            for milestone in recent:
                achiever = milestone.get('achieved_by', 'Someone')
                name = milestone.get('name', 'Unknown')
                impact = milestone.get('impact', '')
                achievement_lines.append(f"  ✅ {name} (by {achiever})")
                if impact:
                    achievement_lines.append(f"      → {impact}")

            if achievement_lines:
                message_parts.append("\n📜 **RECENT BREAKTHROUGHS:**")
                message_parts.extend(achievement_lines)

        # Show next milestone opportunity (most important!)
        if next_milestones:
            next_milestone = next_milestones[0]  # Most immediate
            name = next_milestone.get('name', 'Unknown')
            description = next_milestone.get('description', '')
            unlocks_era = next_milestone.get('unlocks_era')
            multiplier = next_milestone.get('production_multiplier', 1.0)

            message_parts.append(f"\n🎯 **NEXT FRONTIER: {name}**")
            if description:
                message_parts.append(f"   {description}")

            if unlocks_era:
                message_parts.append(f"   Unlocks: {unlocks_era} (×{multiplier:.0f} production!)")

        # Show what can be discovered in current era
        if discoverable and len(discoverable) > 0:
            # Filter out already discovered
            undiscovered = [d for d in discoverable if d not in known_discoveries]

            if undiscovered:
                discovery_sample = undiscovered[:5]  # Show first 5
                message_parts.append(f"\n🔬 **POSSIBLE DISCOVERIES:**")
                for discovery in discovery_sample:
                    message_parts.append(f"   • {discovery}")

                message_parts.append("\n**You could EXPERIMENT to discover new materials and advance civilization!**")

        # Add context about knowledge/innovation
        if current_era == 'Stone Age' and not achieved_milestones:
            message_parts.append("\n💡 **You are among the first humans. Everything must be discovered from scratch.**")
            message_parts.append("   Try EXPERIMENT to discover fire, tools, and new materials.")

        elif current_era != 'Stone Age' and next_milestones:
            message_parts.append(f"\n💡 **The {current_era} has unlocked new possibilities.**")
            message_parts.append("   Experiment with new materials to push civilization forward!")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_weather_context(self, agent) -> str:
        """
        Extract weather information

        Returns formatted weather context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        weather_info = perceptions.get('weather_info', {})

        if not weather_info:
            return ""

        current_weather = weather_info.get('current_weather', 'sunny')
        emoji = weather_info.get('emoji', '☀️')
        description = weather_info.get('description', '')
        effects = weather_info.get('effects', {})
        has_shelter = weather_info.get('has_shelter', False)
        needs_shelter = weather_info.get('needs_shelter', False)

        # Build context based on weather conditions
        message_parts = []

        # Show current weather
        message_parts.append(f"🌦️  **WEATHER: {current_weather.title()}** {emoji}")
        if description:
            message_parts.append(f"   {description}")

        # Show critical effects
        danger = effects.get('danger_level', 0)
        energy_drain = effects.get('energy_drain', 0)
        gathering_eff = effects.get('gathering_efficiency', 1.0)
        movement = effects.get('movement_speed', 1.0)

        effect_lines = []

        # Resource regeneration effects
        water_regen = effects.get('water_regeneration', 1.0)
        food_regen = effects.get('food_regeneration', 1.0)
        if water_regen > 1.2:
            effect_lines.append(f"   💧 Water sources refilling rapidly (+{int((water_regen-1)*100)}%)")
        elif water_regen < 0.5:
            effect_lines.append(f"   💧 Water sources drying up ({int(water_regen*100)}% normal)")

        if food_regen > 1.2:
            effect_lines.append(f"   🌾 Plants growing well (+{int((food_regen-1)*100)}%)")
        elif food_regen < 0.5:
            effect_lines.append(f"   🌾 Plants withering ({int(food_regen*100)}% normal)")

        # Agent effects
        if movement < 1.0:
            effect_lines.append(f"   🏃 Movement slowed ({int(movement*100)}% speed)")
        if gathering_eff < 1.0:
            effect_lines.append(f"   ⛏️  Gathering harder ({int(gathering_eff*100)}% efficiency)")
        if energy_drain > 0:
            effect_lines.append(f"   ⚡ Energy draining faster (+{energy_drain:.1f}/tick)")

        if effect_lines:
            message_parts.append("\n**Effects:**")
            message_parts.extend(effect_lines)

        # Critical warnings
        if needs_shelter:
            message_parts.append(f"\n⚠️  **DANGER! SEEK SHELTER IMMEDIATELY!**")
            if danger > 0:
                message_parts.append(f"   Exposed agents take {danger:.1f} damage per tick!")
            message_parts.append("   **Find a building or construct shelter to survive.**")
        elif danger > 0:
            message_parts.append(f"\n⚠️  Weather is dangerous! ({danger:.1f} damage if exposed)")
            if has_shelter:
                message_parts.append("   ✅ You are safe in shelter")
            else:
                message_parts.append("   Seek shelter if health is low")

        # Shelter status
        if has_shelter and not needs_shelter:
            message_parts.append(f"\n🏠 You are near shelter (building protection available)")

        # Strategic advice based on weather
        if current_weather in ['rainy', 'stormy'] and water_regen > 1.5:
            message_parts.append("\n💡 Good time to collect water while it's abundant")
        elif current_weather in ['drought', 'heat_wave']:
            message_parts.append("\n💡 Water is scarce - conserve and seek reliable sources")
        elif current_weather in ['snowy', 'blizzard']:
            message_parts.append("\n💡 Cold weather - stay near fire and shelter")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_buildings_context(self, agent) -> str:
        """
        Extract building information

        Returns formatted building context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        buildings_info = perceptions.get('buildings_info', {})

        if not buildings_info:
            return ""

        nearby_buildings = buildings_info.get('nearby_buildings', [])
        buildable_structures = buildings_info.get('buildable_structures', [])
        available_materials = buildings_info.get('available_materials', {})

        message_parts = []

        # Show nearby buildings
        if nearby_buildings:
            # Show complete, functional buildings first
            functional = [b for b in nearby_buildings if b.get('is_complete') and not b.get('collapsed')]
            under_construction = [b for b in nearby_buildings if not b.get('is_complete')]
            collapsed = [b for b in nearby_buildings if b.get('collapsed')]

            if functional:
                message_parts.append("🏛️  **NEARBY BUILDINGS:**")
                for building in functional[:5]:  # Top 5
                    name = building.get('name', 'Unknown')
                    dist = building.get('distance', 0)
                    benefits = building.get('benefits', {})

                    building_line = f"  • {name} ({dist}m away)"

                    if benefits:
                        benefit_str = []
                        if 'shelter' in benefits:
                            benefit_str.append(f"Shelter: {benefits['shelter']:.0%}")
                        if 'production_bonus' in benefits:
                            benefit_str.append(f"Crafting: +{benefits['production_bonus']:.0%}")
                        if 'defense' in benefits:
                            benefit_str.append(f"Defense: +{benefits['defense']:.0f}")
                        if 'storage' in benefits:
                            benefit_str.append(f"Storage: {benefits['storage']:.0f}")
                        if 'comfort' in benefits:
                            benefit_str.append(f"Comfort: {benefits['comfort']:.0%}")

                        if benefit_str:
                            building_line += " - " + ", ".join(benefit_str)

                    message_parts.append(building_line)

            if under_construction:
                message_parts.append("\n🏗️  **UNDER CONSTRUCTION:**")
                for building in under_construction[:3]:
                    name = building.get('name', 'Unknown')
                    progress = building.get('construction_progress', 0)
                    dist = building.get('distance', 0)
                    message_parts.append(f"  • {name} ({progress}% complete, {dist}m away)")

            if collapsed:
                message_parts.append("\n💥 **COLLAPSED BUILDINGS:**")
                for building in collapsed[:2]:
                    name = building.get('name', 'Unknown')
                    dist = building.get('distance', 0)
                    message_parts.append(f"  • {name} (collapsed, {dist}m away)")

        # Show buildable structures
        if buildable_structures:
            message_parts.append("\n💡 **YOU COULD BUILD:**")
            for structure in buildable_structures:
                name = structure.get('name', 'Unknown')
                purpose = structure.get('purpose', '')
                benefit = structure.get('benefit', '')
                materials = structure.get('materials', {})

                mat_str = ", ".join([f"{amt} {mat}" for mat, amt in materials.items()])
                build_line = f"  • {name} - Cost: {mat_str}"
                if benefit:
                    build_line += f" ({benefit})"

                message_parts.append(build_line)

            # Encourage building if needed
            if not nearby_buildings or len(functional) == 0:
                message_parts.append("\n**Building shelter will protect you from weather and provide storage.**")

        elif available_materials:
            # Has materials but not enough for suggested structures
            mat_list = ", ".join([f"{amt} {mat}" for mat, amt in available_materials.items()])
            message_parts.append(f"\n🔨 **BUILDING MATERIALS:** {mat_list}")
            message_parts.append("   Gather more materials to build structures")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_knowledge_context(self, agent) -> str:
        """
        Extract knowledge and teaching/learning information

        Returns formatted knowledge context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        knowledge_info = perceptions.get('knowledge_info', {})

        if not knowledge_info:
            return ""

        known_knowledge = knowledge_info.get('known_knowledge', [])
        knowledge_count = knowledge_info.get('knowledge_count', 0)
        teaching_opps = knowledge_info.get('teaching_opportunities', [])
        learning_opps = knowledge_info.get('learning_opportunities', [])
        libraries = knowledge_info.get('nearby_libraries', [])
        total_civ_knowledge = knowledge_info.get('total_civilization_knowledge', 0)

        message_parts = []

        # Show agent's knowledge
        if known_knowledge:
            message_parts.append(f"📚 **YOUR KNOWLEDGE ({knowledge_count} items):**")

            # Categorize by type
            expert_knowledge = [k for k in known_knowledge if k.get('mastery') == 'expert']
            learned_knowledge = [k for k in known_knowledge if k.get('mastery') == 'learned']

            if expert_knowledge:
                message_parts.append("   **Mastered (you discovered):**")
                for k in expert_knowledge[:3]:
                    name = k.get('name', 'Unknown')
                    k_type = k.get('type', '')
                    message_parts.append(f"     ✅ {name} ({k_type})")

            if learned_knowledge:
                message_parts.append("   **Learned (from others):**")
                for k in learned_knowledge[:3]:
                    name = k.get('name', 'Unknown')
                    accuracy = k.get('accuracy', 1.0)
                    acc_str = f" - {int(accuracy*100)}% accurate" if accuracy < 1.0 else ""
                    message_parts.append(f"     📖 {name}{acc_str}")

        elif total_civ_knowledge > 0:
            message_parts.append(f"📚 **KNOWLEDGE STATUS:**")
            message_parts.append(f"   You know: 0 items")
            message_parts.append(f"   Civilization knows: {total_civ_knowledge} items")
            message_parts.append("   **You could learn from others!**")

        # Show teaching opportunities
        if teaching_opps:
            message_parts.append(f"\n🎓 **TEACHING OPPORTUNITIES:**")
            for opp in teaching_opps[:3]:
                name = opp.get('agent_name', 'Unknown')
                dist = opp.get('distance', 0)
                can_teach = opp.get('can_teach', [])
                teach_str = ", ".join(can_teach)
                message_parts.append(f"   • {name} ({dist}m) could learn: {teach_str}")

            message_parts.append("   **Use TEACH action to share your knowledge**")

        # Show learning opportunities
        if learning_opps:
            message_parts.append(f"\n📖 **LEARNING OPPORTUNITIES:**")
            for opp in learning_opps[:3]:
                name = opp.get('agent_name', 'Unknown')
                dist = opp.get('distance', 0)
                can_learn = opp.get('can_learn', [])
                learn_str = ", ".join(can_learn)
                message_parts.append(f"   • {name} ({dist}m) knows: {learn_str}")

            message_parts.append("   **Use LEARN action to gain knowledge from experts**")

        # Show nearby libraries
        if libraries:
            message_parts.append(f"\n📕 **NEARBY LIBRARIES:**")
            for lib in libraries:
                name = lib.get('name', 'Library')
                dist = lib.get('distance', 0)
                docs = lib.get('document_count', 0)
                message_parts.append(f"   • {name} ({dist}m) - {docs} documents")

            message_parts.append("   **Libraries preserve knowledge permanently**")

        # Strategic advice
        if not known_knowledge and learning_opps:
            message_parts.append("\n💡 **Gain knowledge through LEARN action to advance your skills**")
        elif known_knowledge and teaching_opps:
            message_parts.append("\n💡 **Teaching spreads your knowledge and builds community**")

        # Knowledge importance message
        if total_civ_knowledge > 0 and knowledge_count == 0:
            message_parts.append("\n⚠️  **Without knowledge, you must rediscover everything from scratch!**")
            message_parts.append("   Learning from others builds civilization faster.")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_disaster_context(self, agent) -> str:
        """
        Extract disaster warning information

        Returns formatted disaster context for decision-making
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        disaster_info = perceptions.get('disaster_info', {})

        if not disaster_info:
            return ""

        active_disasters = disaster_info.get('active_disasters', [])
        in_danger = disaster_info.get('in_immediate_danger', False)

        if not active_disasters:
            return ""

        message_parts = []

        # Critical disasters first
        critical_disasters = [d for d in active_disasters if d.get('in_danger_zone')]
        warning_disasters = [d for d in active_disasters if not d.get('in_danger_zone')]

        if critical_disasters:
            message_parts.append("🚨 **DISASTER ALERT - IMMEDIATE DANGER!**")
            for disaster in critical_disasters:
                d_type = disaster.get('type', 'unknown').upper()
                severity = disaster.get('severity', 'unknown')
                dist = disaster.get('distance_from_epicenter', 0)
                radius = disaster.get('radius', 0)
                damage = disaster.get('damage_potential', 0)

                message_parts.append(f"   💥 {d_type} ({severity})")
                message_parts.append(f"      Distance: {dist}m from epicenter (radius: {radius}m)")
                if damage > 0:
                    message_parts.append(f"      Damage: {damage:.0f}/tick if you stay!")

            message_parts.append("\n⚠️  **EVACUATE IMMEDIATELY! Move away from the disaster zone!**")
            message_parts.append("   Seek shelter in buildings or move to safe distance")

        elif warning_disasters:
            message_parts.append("⚠️  **DISASTER WARNING:**")
            for disaster in warning_disasters[:2]:  # Top 2 warnings
                d_type = disaster.get('type', 'unknown')
                severity = disaster.get('severity', 'unknown')
                dist = disaster.get('distance_from_epicenter', 0)
                warning_level = disaster.get('warning', '')

                message_parts.append(f"   🌪️  {d_type.title()} ({severity}) - {dist}m away")
                message_parts.append(f"      {warning_level}")

            message_parts.append("\n💡 Monitor the situation and prepare to evacuate if it approaches")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_experimentation_context(self, agent) -> str:
        """
        Extract experimentation hints and opportunities

        Returns formatted experimentation context
        """

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        exp_info = perceptions.get('experimentation_info', {})

        if not exp_info:
            return ""

        available_materials = exp_info.get('available_materials', [])
        suggestions = exp_info.get('experiment_suggestions', [])
        can_experiment = exp_info.get('can_experiment', False)

        if not can_experiment and not suggestions:
            return ""

        message_parts = []

        # Show experiment suggestions
        if suggestions:
            message_parts.append("🔬 **EXPERIMENT OPPORTUNITIES:**")
            for suggestion in suggestions:
                materials = suggestion.get('materials', [])
                method = suggestion.get('method', '')
                result = suggestion.get('expected_result', '')
                benefit = suggestion.get('benefit', '')

                mat_str = " + ".join(materials)
                msg = f"   • {mat_str} ({method}) → {result}"
                if benefit:
                    msg += f"\n      💡 {benefit}"

                message_parts.append(msg)

            message_parts.append("\n**Use EXPERIMENT action to try these combinations!**")

        elif available_materials:
            # Has materials but no specific suggestions
            mat_list = ", ".join([f"{m['quantity']}x {m['material']}" for m in available_materials[:5]])
            message_parts.append(f"🔬 **MATERIALS FOR EXPERIMENTS:** {mat_list}")
            message_parts.append("   Try combining materials in different ways to discover new things")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_roles_context(self, agent) -> str:
        """Extract role emergence and community role information"""

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        roles_info = perceptions.get('roles_info', {})

        if not roles_info:
            return ""

        message_parts = []

        # Detected behavior patterns (agent might be specializing!)
        detected_patterns = roles_info.get('detected_patterns', [])
        unnamed_roles = roles_info.get('unnamed_roles', [])
        named_roles = roles_info.get('named_roles', [])

        if detected_patterns and not any(p.get('has_discovered_role') for p in detected_patterns):
            # Agent has patterns but hasn't discovered roles yet
            message_parts.append("👷 **BEHAVIORAL PATTERN DETECTED:**")

            for pattern in detected_patterns[:2]:  # Show top 2 patterns
                pattern_type = pattern.get('type', 'unknown')
                primary_actions = pattern.get('primary_actions', [])
                strength = pattern.get('specialization_strength', 0)

                action_str = ", ".join(primary_actions[:2])
                message_parts.append(f"   • You frequently {action_str} ({strength:.0f}% of your actions)")

            message_parts.append("\n   💡 **You're developing a specialization!**")
            message_parts.append("   You could discover and NAME your role to become recognized by the community.")

        # Unnamed roles (discovered but not named yet)
        if unnamed_roles:
            message_parts.append("🌟 **ROLE DISCOVERED - NEEDS A NAME!**")

            for role in unnamed_roles:
                pattern_type = role.get('pattern_type', 'unknown')
                primary_actions = role.get('primary_actions', [])
                specialization = role.get('specialization', 0)

                action_str = ", ".join(primary_actions[:2])
                message_parts.append(f"   • You've specialized in {action_str} ({specialization:.0f}% specialization)")
                message_parts.append(f"     Times performed: {role.get('times_performed', 0)}")

            message_parts.append("\n   **YOU SHOULD NAME YOUR ROLE!**")
            message_parts.append("   Examples: \"Stone-Maker\", \"Fire-Keeper\", \"Food-Gatherer\", \"Builder\"")
            message_parts.append("   Or invent your own unique name that reflects what you do!")

        # Named roles (agent's established identity)
        if named_roles:
            message_parts.append(f"👤 **YOUR ROLE{'S' if len(named_roles) > 1 else ''}:**")

            for role in named_roles:
                custom_name = role.get('custom_name', 'Unknown')
                primary_actions = role.get('primary_actions', [])
                specialization = role.get('specialization', 0)
                recognized_by = role.get('recognized_by_count', 0)
                adoption = role.get('community_adoption', 0)
                effectiveness = role.get('effectiveness', 50)

                action_str = ", ".join(primary_actions[:2])

                message_parts.append(f"   🏆 **{custom_name}**")
                message_parts.append(f"      Specialization: {action_str} ({specialization:.0f}%)")
                message_parts.append(f"      Effectiveness: {effectiveness:.0f}%")

                if recognized_by > 0:
                    message_parts.append(f"      Community recognition: {recognized_by} agents know your role")
                    if adoption > 0:
                        message_parts.append(f"      {adoption} agents use this role name")
                else:
                    message_parts.append(f"      ⚠️  Not yet recognized by community - keep performing this role!")

        # Community roles (what others are doing)
        community_roles = roles_info.get('community_roles', [])

        if community_roles:
            message_parts.append(f"\n🏘️ **COMMUNITY ROLES (nearby agents):**")

            for comm_role in community_roles[:5]:  # Show top 5
                agent_name = comm_role.get('agent_name', 'Unknown')
                role_name = comm_role.get('role_name', 'Unknown')
                primary_actions = comm_role.get('primary_actions', [])
                distance = comm_role.get('distance', 0)
                can_learn = comm_role.get('can_learn_from', False)

                action_str = ", ".join(primary_actions[:2])
                message_parts.append(f"   • {agent_name}: **{role_name}** ({action_str}) - {distance:.0f}m away")

                if can_learn:
                    message_parts.append(f"      💡 You could learn from their expertise!")

        # Popular role names in community
        popular_roles = roles_info.get('popular_role_names', [])

        if popular_roles:
            message_parts.append(f"\n📊 **POPULAR ROLES IN CIVILIZATION:**")

            for pop_role in popular_roles[:3]:  # Show top 3
                role_name = pop_role.get('role_name', 'Unknown')
                usage = pop_role.get('usage_count', 0)
                inventor = pop_role.get('invented_by', 'Unknown')

                message_parts.append(f"   • {role_name} ({usage} uses) - invented by {inventor}")

        # Guidance
        if unnamed_roles:
            message_parts.append("\n💬 **ROLE NAMING:**")
            message_parts.append("   To name your role, choose a name that reflects what you do.")
            message_parts.append("   Your role name will become part of the community vocabulary!")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_innovations_context(self, agent) -> str:
        """Extract innovations and agent discoveries"""

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        innovations_info = perceptions.get('innovations_info', {})

        if not innovations_info:
            return ""

        message_parts = []

        # Known innovations (what agent has discovered or learned)
        known_innovations = innovations_info.get('known_innovations', [])

        if known_innovations:
            # Separate discoveries from learned
            discoveries = [i for i in known_innovations if i.get('is_discoverer')]
            learned = [i for i in known_innovations if not i.get('is_discoverer')]

            if discoveries:
                message_parts.append(f"💡 **YOUR DISCOVERIES ({len(discoveries)}):**")

                for innovation in discoveries[:5]:  # Show top 5
                    name = innovation.get('name', 'Unknown')
                    i_type = innovation.get('type', 'unknown')
                    efficiency = innovation.get('efficiency_bonus', 0)
                    success_rate = innovation.get('success_rate', 100)
                    times_used = innovation.get('times_used', 0)

                    message_parts.append(f"   🏆 **{name}** ({i_type})")

                    if efficiency > 0:
                        message_parts.append(f"      Efficiency bonus: +{efficiency:.0f}%")

                    if times_used > 0:
                        message_parts.append(f"      Used {times_used} times (success: {success_rate:.0f}%)")

                    applies_to = innovation.get('applies_to', [])
                    if applies_to:
                        message_parts.append(f"      Improves: {', '.join(applies_to)}")

            if learned:
                message_parts.append(f"\n📚 **INNOVATIONS YOU'VE LEARNED ({len(learned)}):**")

                for innovation in learned[:3]:  # Show top 3
                    name = innovation.get('name', 'Unknown')
                    i_type = innovation.get('type', 'unknown')
                    efficiency = innovation.get('efficiency_bonus', 0)

                    message_parts.append(f"   • {name} ({i_type})")

                    if efficiency > 0:
                        message_parts.append(f"      Bonus: +{efficiency:.0f}%")

        # Learning opportunities (nearby agents with innovations)
        learning_opps = innovations_info.get('learning_opportunities', [])

        if learning_opps:
            message_parts.append(f"\n🎓 **INNOVATION LEARNING OPPORTUNITIES:**")

            for opp in learning_opps[:3]:  # Show top 3
                agent_name = opp.get('agent_name', 'Unknown')
                distance = opp.get('distance', 0)
                can_teach = opp.get('can_teach', [])

                message_parts.append(f"   • {agent_name} ({distance:.0f}m away) knows:")

                for innovation in can_teach[:2]:  # Show 2 per teacher
                    name = innovation.get('name', 'Unknown')
                    i_type = innovation.get('type', 'unknown')
                    bonus = innovation.get('efficiency_bonus', 0)

                    bonus_str = f" (+{bonus:.0f}%)" if bonus > 0 else ""
                    message_parts.append(f"       - {name} ({i_type}){bonus_str}")

            message_parts.append("\n   💬 Approach them to learn their innovations!")

        # Proven building designs
        building_designs = innovations_info.get('proven_building_designs', [])

        if building_designs:
            message_parts.append(f"\n🏛️ **PROVEN BUILDING DESIGNS:**")

            for design in building_designs[:3]:  # Show top 3
                name = design.get('name', 'Unknown')
                purpose = design.get('purpose', 'unknown')
                materials = design.get('materials_needed', {})
                success_rate = design.get('success_rate', 0)
                times_built = design.get('times_built', 0)

                mat_str = ", ".join([f"{v} {k}" for k, v in materials.items() if v > 0])

                message_parts.append(f"   • **{name}** ({purpose})")
                message_parts.append(f"      Materials: {mat_str}")
                message_parts.append(f"      Proven: {times_built} built, {success_rate:.0f}% success")

        # Can agent innovate?
        can_innovate = innovations_info.get('can_innovate', False)

        if can_innovate:
            if not known_innovations:
                message_parts.append("\n🌟 **YOU HAVE INNOVATIVE POTENTIAL!**")
                message_parts.append("   Your creativity and openness could lead to discoveries.")
                message_parts.append("   Try experimenting with new approaches to tasks!")
            elif len(discoveries) > 0:
                message_parts.append("\n🔬 **KEEP INNOVATING!**")
                message_parts.append("   You've already made discoveries - keep trying new things!")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_fun_context(self, agent) -> str:
        """Extract fun and entertainment information"""

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        fun_info = perceptions.get('fun_info', {})

        if not fun_info:
            return ""

        message_parts = []

        # Nearby celebrations
        celebrations = fun_info.get('nearby_celebrations', [])

        if celebrations:
            message_parts.append("🎉 **CELEBRATIONS HAPPENING:**")

            for cel in celebrations[:3]:  # Show top 3
                name = cel.get('name', 'Celebration')
                cel_type = cel.get('type', 'unknown')
                distance = cel.get('distance', 0)
                participants = cel.get('participants_count', 0)
                time_left = cel.get('time_remaining', 0)
                mood_boost = cel.get('mood_boost', 0)
                is_participant = cel.get('is_participant', False)
                can_join = cel.get('can_join', False)

                if is_participant:
                    message_parts.append(f"   🎊 **{name}** (you're participating!)")
                    message_parts.append(f"      {participants} participants, {time_left} ticks remaining")
                    message_parts.append(f"      Mood boost: +{mood_boost:.0%}")
                elif can_join:
                    message_parts.append(f"   🎈 **{name}** ({distance:.0f}m away)")
                    message_parts.append(f"      {participants} participants, {time_left} ticks remaining")
                    message_parts.append(f"      **You can join! Mood boost: +{mood_boost:.0%}**")
                else:
                    message_parts.append(f"   • {name} ({distance:.0f}m away, {participants} participants)")

        # Active games
        games = fun_info.get('nearby_games', [])

        if games:
            message_parts.append("\n🎲 **GAMES IN PROGRESS:**")

            for game in games[:3]:
                game_type = game.get('type', 'unknown').replace('_', ' ').title()
                players = game.get('players_count', 0)
                spectators = game.get('spectators_count', 0)
                is_player = game.get('is_player', False)
                is_spectator = game.get('is_spectator', False)
                can_spectate = game.get('can_spectate', False)

                if is_player:
                    message_parts.append(f"   🏆 **{game_type}** (you're playing!)")
                elif is_spectator:
                    message_parts.append(f"   👀 **{game_type}** (you're watching)")
                elif can_spectate:
                    message_parts.append(f"   • {game_type} - {players} players, {spectators} spectators")
                    message_parts.append(f"      You could watch and enjoy!")

        # Art to view
        art_pieces = fun_info.get('art_to_view', [])

        if art_pieces:
            message_parts.append("\n🎨 **ART TO EXPERIENCE:**")

            for art in art_pieces[:3]:
                title = art.get('title', 'Untitled')
                art_type = art.get('type', 'unknown')
                quality = art.get('quality', 0)
                viewers = art.get('viewers_count', 0)

                quality_desc = "masterpiece" if quality > 80 else "high quality" if quality > 60 else "decent"

                message_parts.append(f"   • **{title}** ({art_type}, {quality_desc})")
                message_parts.append(f"      {viewers} viewers, quality: {quality:.0f}%")

        # Agent's fun stats
        fun_stats = fun_info.get('your_fun_stats', {})
        celebrations_count = fun_stats.get('celebrations_attended', 0)
        games_played = fun_stats.get('games_played', 0)
        games_won = fun_stats.get('games_won', 0)
        art_created = fun_stats.get('art_created', 0)
        fun_score = fun_stats.get('fun_score', 0)

        if celebrations_count > 0 or games_played > 0 or art_created > 0:
            message_parts.append(f"\n📊 **YOUR FUN EXPERIENCE:**")
            if celebrations_count > 0:
                message_parts.append(f"   Celebrations attended: {celebrations_count}")
            if games_played > 0:
                win_rate = (games_won / games_played * 100) if games_played > 0 else 0
                message_parts.append(f"   Games played: {games_played} (won: {games_won}, {win_rate:.0f}%)")
            if art_created > 0:
                message_parts.append(f"   Art pieces created: {art_created}")

        # Should seek fun?
        should_seek_fun = fun_info.get('should_seek_fun', False)
        can_create_art = fun_info.get('can_create_art', False)

        if should_seek_fun:
            message_parts.append("\n💭 **FEELING DOWN?**")
            message_parts.append("   Your happiness is low. Consider:")
            if celebrations:
                message_parts.append("   • Join a celebration to boost your mood")
            if games:
                message_parts.append("   • Play or watch a game for entertainment")
            if art_pieces:
                message_parts.append("   • View art to appreciate beauty")
            if can_create_art:
                message_parts.append("   • Create art to express yourself")
            message_parts.append("   • Socialize with others for joy")

        # Community traditions
        traditions = fun_info.get('community_traditions', [])

        if traditions:
            message_parts.append("\n🏛️ **COMMUNITY TRADITIONS:**")
            for trad in traditions:
                trad_name = trad.get('tradition', 'Unknown')
                times = trad.get('times_celebrated', 0)
                message_parts.append(f"   • {trad_name} (celebrated {times} times)")

        # Creative opportunities
        if can_create_art and not should_seek_fun:
            message_parts.append("\n🎨 **CREATIVE OPPORTUNITY:**")
            message_parts.append("   You have the creativity to make art!")
            message_parts.append("   Consider painting, sculpting, singing, or storytelling.")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def _get_consequences_context(self, agent) -> str:
        """Extract consequence and risk information"""

        if not hasattr(agent, 'last_perception') or not agent.last_perception:
            return ""

        perceptions = agent.last_perception
        consequences_info = perceptions.get('consequences_info', {})

        if not consequences_info:
            return ""

        message_parts = []

        # Recent consequences in community (warnings!)
        recent = consequences_info.get('recent_consequences', [])

        if recent:
            message_parts.append("⚠️  **RECENT DISASTERS IN COMMUNITY:**")

            for cons in recent[:3]:
                cons_type = cons.get('type', 'unknown')
                action = cons.get('action', 'unknown')
                severity = cons.get('severity', 0)
                description = cons.get('description', '')
                was_affected = cons.get('was_affected', False)

                severity_label = "CRITICAL" if severity > 80 else "SEVERE" if severity > 60 else "MODERATE"

                if was_affected:
                    message_parts.append(f"   🔴 **YOU EXPERIENCED: {description}**")
                    message_parts.append(f"      Type: {cons_type.upper()}, Severity: {severity:.0f}% ({severity_label})")
                    message_parts.append(f"      **Learn from this! Avoid {action} in dangerous situations.**")
                else:
                    message_parts.append(f"   ⚠️  {description}")
                    message_parts.append(f"      Type: {cons_type}, Severity: {severity:.0f}% ({severity_label})")

        # Agent's past consequences (trauma/learning)
        past_cons = consequences_info.get('your_past_consequences', [])

        if past_cons:
            message_parts.append(f"\n💔 **YOUR PAST TRAUMAS:**")

            for cons in past_cons:
                cons_type = cons.get('type', 'unknown')
                action = cons.get('action', 'unknown')
                severity = cons.get('severity', 0)

                message_parts.append(f"   • {cons_type.title()} from {action} (severity: {severity:.0f}%)")

            message_parts.append(f"\n   **You've learned to be more careful from these experiences.**")

        # Current risk warnings
        risk_warnings = consequences_info.get('current_risk_warnings', {})

        if risk_warnings:
            message_parts.append(f"\n🚨 **CURRENT RISK WARNINGS:**")

            for action, risk_data in risk_warnings.items():
                total_risk = risk_data.get('total_risk', 0)
                main_risks = risk_data.get('main_risks', [])
                warning = risk_data.get('warning', '')

                message_parts.append(f"\n   **{action.upper()}**: {total_risk:.0f}% overall risk")

                if warning:
                    message_parts.append(f"      ⚠️  {warning}")

                if main_risks:
                    for risk in main_risks:
                        risk_type = risk.get('type', 'unknown')
                        probability = risk.get('probability', 0)
                        severity = risk.get('severity', 0)

                        message_parts.append(f"      • {risk_type}: {probability:.0f}% chance, {severity:.0f}% severity")

            message_parts.append(f"\n   **CONSIDER THE RISKS BEFORE ACTING!**")

        # Learned dangers (from experience)
        learned = consequences_info.get('learned_dangers', [])

        if learned:
            message_parts.append(f"\n🧠 **DANGERS YOU'VE LEARNED:**")

            for danger in learned:
                action = danger.get('action', 'unknown')
                risk = danger.get('perceived_risk', 0)

                risk_label = "EXTREMELY DANGEROUS" if risk > 80 else "VERY RISKY" if risk > 60 else "RISKY"

                message_parts.append(f"   • {action.title()}: {risk:.0f}% ({risk_label})")

            message_parts.append(f"\n   Your past experiences make you cautious about these actions.")

        # Community statistics
        stats = consequences_info.get('community_stats', {})

        deaths = stats.get('total_deaths', 0)
        bankruptcies = stats.get('total_bankruptcies', 0)
        most_dangerous = stats.get('most_dangerous_action', 'None')

        if deaths > 0 or bankruptcies > 0:
            message_parts.append(f"\n📊 **COMMUNITY DANGER STATISTICS:**")

            if deaths > 0:
                message_parts.append(f"   ☠️  Total deaths: {deaths}")
            if bankruptcies > 0:
                message_parts.append(f"   💸 Total bankruptcies: {bankruptcies}")
            if most_dangerous != 'None':
                message_parts.append(f"   ⚠️  Most dangerous action: {most_dangerous}")

            message_parts.append(f"\n   **This world is dangerous. Act wisely.**")

        # General wisdom
        if past_cons or learned:
            message_parts.append(f"\n💡 **SURVIVAL WISDOM:**")
            message_parts.append("   • Remember your past mistakes")
            message_parts.append("   • Evaluate risks before acting")
            message_parts.append("   • Sometimes avoiding danger is the wisest choice")
            message_parts.append("   • Learn from others' failures too")

        if message_parts:
            return "\n" + "\n".join(message_parts) + "\n\n"
        else:
            return ""

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_decisions": self.total_decisions,
            "calls": self.calls,
            "call_failures": self.call_failures,
            "average_latency_s": round(self.total_latency / self.calls, 2) if self.calls else None,
            "decisions_parsed": self.decisions_parsed,
            "parse_failures": self.parse_failures,
            "ollama": {"url": self.ollama_url, "model": self.ollama_model, "num_ctx": self.ollama_num_ctx},
            "provider_usage": {p.value: count for p, count in self.provider_usage.items()},
            "rate_limits": {
                p.value: {
                    "minute": self.rate_limiter.usage[p]["minute_count"],
                    "day": self.rate_limiter.usage[p]["day_count"]
                }
                for p in self.rate_limiter.limits.keys()
            }
        }
