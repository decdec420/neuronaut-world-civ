"""
Agent Cache Helper - O(1) Agent Lookups

Provides fast hash-map based agent lookups instead of O(n) linear search.
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class AgentCacheHelper:
    """
    Helper for O(1) agent lookups using hash map.

    Provides:
    - Fast agent lookup by ID
    - Automatic cache rebuilding
    - Graceful fallback to linear search on cache miss
    """

    def __init__(self):
        self._agent_cache: Dict[str, 'Agent'] = {}
        logger.debug("AgentCacheHelper initialized")

    def rebuild_cache(self, agents: List['Agent']) -> None:
        """
        Rebuild the agent lookup cache for O(1) access by ID.

        This should be called after:
        - New agents are created
        - Agents are removed
        - Loading from save

        Args:
            agents: List of all agents in the simulation
        """
        self._agent_cache = {
            agent.id: agent
            for agent in agents
            if agent.alive
        }
        logger.debug(f"Agent cache rebuilt: {len(self._agent_cache)} agents indexed")

    def get_agent_by_id(self, agent_id: str, agents: List['Agent']) -> Optional['Agent']:
        """
        Fast O(1) agent lookup by ID using cache.
        Falls back to linear search if cache is stale.

        Args:
            agent_id: The agent ID to look up
            agents: List of all agents (for fallback search)

        Returns:
            Agent if found and alive, None otherwise
        """
        # Try cache first (O(1))
        agent = self._agent_cache.get(agent_id)
        if agent and agent.alive:
            return agent

        # Cache miss - do linear search and update cache (O(n))
        for agent in agents:
            if agent.id == agent_id and agent.alive:
                self._agent_cache[agent_id] = agent
                logger.debug(f"Cache miss for agent {agent_id}, updated cache")
                return agent

        return None

    def remove_from_cache(self, agent_id: str) -> None:
        """
        Remove an agent from the cache (e.g., when they die).

        Args:
            agent_id: The agent ID to remove
        """
        if agent_id in self._agent_cache:
            del self._agent_cache[agent_id]
            logger.debug(f"Removed agent {agent_id} from cache")

    def get_cache_size(self) -> int:
        """
        Get the current size of the agent cache.

        Returns:
            Number of agents in cache
        """
        return len(self._agent_cache)

    def clear_cache(self) -> None:
        """Clear the entire cache (useful for reset)."""
        self._agent_cache.clear()
        logger.debug("Agent cache cleared")
