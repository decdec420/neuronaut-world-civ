"""
FastAPI Server - REST API and WebSocket for Neuronaut World

Provides:
- REST endpoints for world state, agents, events
- WebSocket for real-time updates
- Character creation
- Authentication and monetization hooks
"""

import asyncio
import hmac
from contextlib import asynccontextmanager
import json
import logging
from typing import List, Dict, Optional
from functools import lru_cache
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field, constr, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Logging when run as `uvicorn api.server:app` (main.py sets its own format)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO")
logger = logging.getLogger(__name__)

from config import load_config
from engine.simulation import SimulationEngine
from agents.agent import Gender
from engine.psychology import PersonalityProfile
from economy.materials import (
    ALL_MATERIALS, MaterialCategory, get_material,
    get_materials_by_category, get_category_summary
)
from economy.recipes import ALL_RECIPES, get_recipe, get_craftable_recipes


# Pydantic models for API
class CreateCharacterRequest(BaseModel):
    """Request model for creating a new character with validation"""
    name: constr(min_length=1, max_length=50, strip_whitespace=True) = Field(
        ...,
        description="Character name (1-50 characters)",
        examples=["Alice"]
    )
    age: int = Field(
        default=20,
        ge=18,
        le=100,
        description="Character age (18-100)"
    )
    gender: constr(to_lower=True) = Field(
        default="male",
        description="Character gender (male, female, non_binary)"
    )
    personality: Optional[Dict] = Field(
        default=None,
        description="Optional personality traits"
    )

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        valid_genders = ['male', 'female', 'non_binary']
        if v not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v


class AgentResponse(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    location: Dict
    health: float
    wealth: float
    status: float
    mood: float
    life_satisfaction: float
    is_player: bool


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Start the world and its broadcasts with the server; stop them with it."""
    await startup_event()
    try:
        yield
    finally:
        await shutdown_event()


# Initialize FastAPI app
app = FastAPI(
    title="Neuronaut World API",
    description="API for observing and interacting with Neuronaut World",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Controls: anything that changes the world (pause, speed, reset, saves,
# disasters, new characters) must carry the X-Neuronaut-Control header. A
# browser can't send a custom header to another site without asking first
# (a CORS preflight), and other sites aren't allowed, so a page on another
# site can't reset or pause your world. Before, CORS allowed every origin
# with credentials, and a bare POST to /reset from any website worked.
# If NEURONAUT_ADMIN_TOKEN is set, controls also need
# "Authorization: Bearer <token>" (the dashboard asks for it once per tab).
CONTROL_HEADER = "x-neuronaut-control"
CONTROL_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _admin_token() -> str:
    return os.getenv("NEURONAUT_ADMIN_TOKEN", "").strip()


async def guard_controls(request: Request, call_next):
    if request.method in CONTROL_METHODS:
        if request.headers.get(CONTROL_HEADER) != "1":
            return JSONResponse(status_code=403, content={
                "detail": "Requests that change the world need the header 'X-Neuronaut-Control: 1'"})
        token = _admin_token()
        if token:
            supplied = request.headers.get("authorization", "")
            given = supplied[7:].strip() if supplied.lower().startswith("bearer ") else ""
            if not hmac.compare_digest(given.encode(), token.encode()):
                return JSONResponse(status_code=401, headers={"WWW-Authenticate": "Bearer"}, content={
                    "detail": "This server needs its admin token (Authorization: Bearer <token>) to change the world"})
    return await call_next(request)


app.middleware("http")(guard_controls)

# Cross-origin access only for the origins listed in CORS_ORIGINS (comma
# separated); the dashboard itself is same-origin and needs none
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Neuronaut-Control"],
    )

# Global simulation instance
simulation: Optional[SimulationEngine] = None
simulation_task: Optional[asyncio.Task] = None
broadcast_task: Optional[asyncio.Task] = None

# WebSocket connections
active_websockets: List[WebSocket] = []

# Simple caches for expensive operations (tick-based invalidation)
_stats_cache = {"data": None, "tick": -1}
_world_state_cache = {"data": None, "tick": -1}

# Files the server hands out, found from this file rather than the current
# directory, so the server works wherever it is started from
WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# How often viewers get a new snapshot, and how long one slow viewer may hold
# up the others before it is dropped (it reconnects by itself)
BROADCAST_INTERVAL = float(os.getenv("BROADCAST_INTERVAL", "2.0"))
SEND_TIMEOUT = 5.0


def _drop_websocket(ws: WebSocket) -> None:
    if ws in active_websockets:
        active_websockets.remove(ws)


async def startup_event():
    """Initialize simulation on startup"""
    global simulation, simulation_task, broadcast_task

    print("🌍 Starting Neuronaut World...")

    # Create simulation
    simulation = SimulationEngine(world_width=100, world_height=100)

    # NUM_AGENTS agents (default 12), half of each sex
    simulation.initialize_world(num_agents=load_config().num_agents)

    # Start simulation loop in background
    simulation_task = asyncio.create_task(simulation.run())

    # Start broadcast task
    broadcast_task = asyncio.create_task(broadcast_updates())

    print("✅ Neuronaut World is running!")


async def shutdown_event():
    """Cleanup on shutdown"""
    if simulation:
        simulation.stop()

    for task in (simulation_task, broadcast_task):
        if task:
            task.cancel()

    print("Neuronaut World stopped")


async def broadcast_updates():
    """Send every viewer a snapshot every BROADCAST_INTERVAL seconds.

    The snapshot is serialized once for everyone. A viewer whose socket fails
    or is too slow is dropped (the dashboard reconnects). A failure while
    building the snapshot is logged with its traceback and the loop carries
    on: before, any error other than a disconnect ended this task for good
    and every open dashboard silently stopped updating.
    """
    while True:
        try:
            if simulation and active_websockets:
                message = json.dumps({
                    "type": "simulation_update",
                    "data": simulation.get_state_snapshot(),
                    "tick": simulation.world.time.current_tick,
                })
                for ws in list(active_websockets):
                    try:
                        await asyncio.wait_for(ws.send_text(message), timeout=SEND_TIMEOUT)
                    except Exception as e:  # closed, broken or too slow: drop this viewer
                        logger.info("Dropping a viewer (%s: %s)", type(e).__name__, e)
                        _drop_websocket(ws)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Could not broadcast a snapshot; trying again next time")
        await asyncio.sleep(BROADCAST_INTERVAL)


# REST Endpoints

@app.get("/health")
async def health():
    """For load balancers and container health checks: 200 while the world
    is running (paused counts as running), 503 if its loop has stopped."""
    running = simulation is not None and simulation_task is not None and not simulation_task.done()
    body = {
        "status": "ok" if running else "down",
        "tick": simulation.world.time.current_tick if simulation else None,
        "paused": bool(simulation.paused) if simulation else None,
        "alive_agents": sum(1 for a in simulation.world.agents if a.alive) if simulation else 0,
        "viewers": len(active_websockets),
    }
    return JSONResponse(status_code=200 if running else 503, content=body)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Neuronaut World",
        "version": "1.0.0",
        "status": "running" if simulation and simulation.running else "stopped",
        "agents": len(simulation.world.agents) if simulation else 0
    }


@app.get("/world")
async def get_world_state():
    """Get current world state with enhanced error handling (cached per tick)"""
    global _world_state_cache

    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Check cache
    current_tick = simulation.world.time.current_tick
    if _world_state_cache["tick"] == current_tick and _world_state_cache["data"] is not None:
        return _world_state_cache["data"]

    try:
        state = simulation.get_state_snapshot()
        # Cache the result
        _world_state_cache["data"] = state
        _world_state_cache["tick"] = current_tick
        return state
    except Exception as e:
        # Enhanced error handling - return partial state if full snapshot fails
        logger.error(f"Error getting state snapshot: {e}")
        try:
            # Return basic state as fallback
            return {
                'world': simulation.world.get_statistics() if hasattr(simulation.world, 'get_statistics') else {},
                'agents': [],  # Skip agents if causing error
                'economy': simulation.economy.get_statistics() if hasattr(simulation.economy, 'get_statistics') else {},
                'events': simulation.event_logger.get_statistics() if hasattr(simulation.event_logger, 'get_statistics') else {},
                'error': f"Partial data: {str(e)}"
            }
        except Exception as fallback_error:
            raise HTTPException(status_code=500, detail=f"Unable to get world state: {str(fallback_error)}")


@app.get("/agents")
async def get_agents(page: int = 1, limit: int = 50):
    """
    Get paginated list of agents

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 50, max: 500)
    """
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Validate and clamp pagination parameters
    page = max(1, page)
    limit = max(1, min(500, limit))  # Max 500 agents per request

    try:
        # Get alive agents only
        alive_agents = [a for a in simulation.world.agents if a.alive]
        total_agents = len(alive_agents)

        # Calculate pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        total_pages = (total_agents + limit - 1) // limit  # Ceiling division

        # Check if page is out of bounds
        if start_idx >= total_agents and total_agents > 0:
            raise HTTPException(status_code=404, detail=f"Page {page} not found. Total pages: {total_pages}")

        # Get paginated slice
        paginated_agents = alive_agents[start_idx:end_idx]

        agents = []
        errors = []

        for agent in paginated_agents:
            try:
                agents.append(agent.to_dict())
            except Exception as e:
                # Log error but continue with other agents
                errors.append(f"Agent {agent.id}: {str(e)[:50]}")
                logger.error(f"Error serializing agent {agent.id}: {e}")

        result = {
            "agents": agents,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_agents,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

        if errors:
            result["errors"] = errors[:5]  # Include first 5 errors for debugging

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agents: {str(e)}")


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent - COMPREHENSIVE PROFILE"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    agent = simulation._get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Build comprehensive profile
    profile = simulation.profile_builder.build_profile(agent_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "profile": profile.to_dict(),
        # Also include legacy format for backwards compatibility
        "agent": agent.to_dict(),
    }


@app.get("/agents/{agent_id}/profile")
async def get_agent_full_profile(agent_id: str):
    """Get FULL detailed profile for agent"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    profile = simulation.profile_builder.build_profile(agent_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Agent not found")

    return profile.to_dict()


@app.get("/events")
async def get_events(limit: int = 50, min_importance: int = 1):
    """Get recent events"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    from engine.events import EventImportance

    events = simulation.event_logger.get_recent_events(
        count=limit,
        min_importance=EventImportance(min_importance)
    )

    return {
        "events": [e.to_dict() for e in events],
        "total": len(events)
    }


@app.get("/consequences")
async def get_consequences():
    """Get detailed consequences list"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    consequences_list = []
    for consequence_id, consequence in simulation.consequence_engine.consequences.items():
        consequences_list.append({
            "id": consequence.id,
            "type": consequence.consequence_type,
            "severity": consequence.severity,
            "description": consequence.description,
            "caused_by": consequence.caused_by_action,
            "affected_agents": list(consequence.affected_agents),
            "timestamp": consequence.timestamp.isoformat(),
            "secondary_effects": consequence.secondary_consequences
        })

    # Sort by timestamp, most recent first
    consequences_list.sort(key=lambda x: x['timestamp'], reverse=True)

    return {
        "consequences": consequences_list,
        "statistics": simulation.consequence_engine.get_statistics()
    }


@app.get("/economy")
async def get_economy():
    """Get economy statistics"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    return {
        "wealth_stats": simulation.economy.get_wealth_statistics(),
        "market_stats": simulation.economy.market.get_market_statistics()
    }


@app.post("/characters")
@limiter.limit("5/minute")  # Max 5 character creations per minute
async def create_character(request: Request, char_request: CreateCharacterRequest):
    """Create a custom character"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Parse personality
    personality = None
    if char_request.personality:
        personality = PersonalityProfile(**char_request.personality)

    # Create agent
    agent = simulation.create_agent(
        name=char_request.name,
        age=char_request.age,
        is_player=True
    )

    if personality:
        agent.personality = personality

    # Set gender
    if char_request.gender.lower() == "male":
        agent.gender = Gender.MALE
    elif request.gender.lower() == "female":
        agent.gender = Gender.FEMALE
    else:
        agent.gender = Gender.NON_BINARY

    # Add to world
    import random
    agent.location.x = random.uniform(20, 80)
    agent.location.y = random.uniform(20, 80)
    # SURVIVAL MODE - No free wealth!
    agent.wealth = 0.0

    simulation.world.agents.append(agent)

    # Log creation
    from engine.events import EventGenerator, EventCategory, EventImportance
    title, desc = EventGenerator.agent_born(
        agent.name,
        {'x': agent.location.x, 'y': agent.location.y}
    )
    simulation.event_logger.log_event(
        EventCategory.LIFE,
        EventImportance.MAJOR,  # Player character is major event
        title + " (Player Character)",
        desc + " This is a player-controlled character.",
        simulation.world.time.current_tick,
        [agent.id]
    )

    return {
        "success": True,
        "agent": agent.to_dict()
    }


@app.get("/stats")
async def get_statistics():
    """Get world statistics - COMPREHENSIVE (cached per tick)"""
    global _stats_cache

    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Check cache - only recompute if tick changed
    current_tick = simulation.world.time.current_tick
    if _stats_cache["tick"] == current_tick and _stats_cache["data"] is not None:
        return _stats_cache["data"]

    # Compute expensive statistics
    stats = {
        "world": simulation.world.get_statistics(),
        "events": simulation.event_logger.get_statistics(),
        "economy": simulation.economy.get_wealth_statistics(),
        "agents": {
            "total": len(simulation.world.agents),
            "alive": sum(1 for a in simulation.world.agents if a.alive),
            "player_characters": sum(1 for a in simulation.world.agents if a.is_player and a.alive)
        },
        # OLD SYSTEMS (kept for compatibility)
        "buildings": simulation.building_manager.get_statistics(),
        "innovations": simulation.innovation_manager.get_statistics(),
        "warfare": simulation.warfare_manager.get_statistics(),
        "governance": simulation.governance_manager.get_statistics(),
        "production": simulation.production_manager.get_statistics(),
        "strategy": simulation.strategy_manager.get_statistics(),
        # NEW AUTONOMOUS SYSTEMS
        "experimentation": simulation.experimentation_engine.get_statistics(),
        "dynamic_buildings": simulation.dynamic_building_system.get_statistics(),
        "knowledge": simulation.knowledge_system.get_statistics(),
        "consequences": simulation.consequence_engine.get_statistics(),
        "roles": simulation.role_emergence.get_statistics(),
        "tech_progression": simulation.tech_progression.get_statistics(),
        # CIVILIZATION PROGRESSION - Stone Age → Space Age!
        "civilization": simulation.civilization.get_stats(),
        # STORY ENGINE & ACHIEVEMENTS - Epic narratives and milestones!
        "stories": simulation.story_feed.to_dict(),
        "achievements": simulation.achievement_tracker.to_dict(),
        # META-PROGRESSION - AI Self-Improvement!
        "meta_progression": simulation.meta_progression.to_dict(),
        # POPULATION TRACKING - Births, deaths, demographics over time!
        "population": simulation.get_population_statistics(),
        # WEATHER SYSTEM - Dynamic environmental effects!
        "weather": simulation.weather.get_statistics(),
        # NATURAL DISASTERS - Catastrophic world events!
        "disasters": simulation.disasters.get_statistics(),
    }

    # Cache the result
    _stats_cache["data"] = stats
    _stats_cache["tick"] = current_tick

    return stats


# SAVE/LOAD SYSTEM - Multiple World Saves!

from engine.save_manager import SaveManager

# Initialize save manager
save_manager = SaveManager()


@app.get("/chronicle")
async def get_chronicle(limit: int = 100):
    """The village's history: firsts, milestones, and agents' own words (engine/chronicle.py)."""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")
    return simulation.chronicle.to_dict(limit=max(1, min(limit, 300)))


@app.get("/society")
async def get_society():
    """Governments and laws, faiths, families, economy and inventions (engine/society.py)."""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")
    from engine.society import society_snapshot
    return society_snapshot(simulation)


@app.get("/saves")
async def list_saves():
    """Get list of all saves"""
    return {"saves": save_manager.list_saves()}


class SaveRequest(BaseModel):
    name: Optional[constr(strip_whitespace=True, min_length=1, max_length=80)] = None


@app.post("/saves")
async def create_save(save_request: SaveRequest):
    """Create a new save"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    save_name = save_request.name or f"World {len(save_manager.list_saves()) + 1}"

    # Get current world state
    world_data = simulation.persistence.create_snapshot()

    success = save_manager.create_save(save_name, world_data, simulation=simulation)
    return {"success": success, "id": save_manager.last_save_id, "message": f"Saved as '{save_name}'"}


@app.post("/saves/{save_id}/load")
async def load_save(save_id: str):
    """Load a save"""
    global simulation, simulation_task

    world_data = save_manager.load_save(save_id)
    if not world_data:
        raise HTTPException(status_code=404, detail="Save not found")
    state_path = save_manager.state_path(save_id)
    if state_path is None:
        # Saves made before full saves existed hold only a summary. (Loading
        # used to "succeed" here and start a fresh, empty world instead.)
        raise HTTPException(status_code=409, detail="This save holds only a summary and can't be loaded")

    # Stop current simulation
    if simulation and simulation.running:
        simulation.stop()

    # Load the world exactly as it was saved, and carry on
    from engine.persistence import load_full_state
    simulation = load_full_state(str(state_path))
    if simulation_task:
        simulation_task.cancel()
    simulation_task = asyncio.create_task(simulation.run())

    return {"success": True, "message": "World loaded successfully"}


@app.delete("/saves/{save_id}")
async def delete_save(save_id: str):
    """Delete a save"""
    success = save_manager.delete_save(save_id)
    if not success:
        raise HTTPException(status_code=404, detail="Save not found")
    return {"success": True, "message": "Save deleted"}


@app.post("/reset")
@limiter.limit("1/minute")  # Max 1 reset per minute (destructive operation)
async def reset_world(request: Request):
    """Reset to a fresh world"""
    global simulation, simulation_task

    # Stop current simulation
    if simulation and simulation.running:
        simulation.stop()

    # Create new simulation
    simulation = SimulationEngine(world_width=100, world_height=100)
    simulation.initialize_world(num_agents=load_config().num_agents)

    # Start new simulation
    if simulation_task:
        simulation_task.cancel()
    simulation_task = asyncio.create_task(simulation.run())

    return {"success": True, "message": "World reset successfully"}


# SIMULATION SPEED CONTROLS
@app.post("/simulation/pause")
async def pause_simulation():
    """Pause/unpause simulation"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    simulation.paused = not simulation.paused
    status = "paused" if simulation.paused else "resumed"
    return {"success": True, "paused": simulation.paused, "message": f"Simulation {status}"}


class SetSpeedRequest(BaseModel):
    """Request model for setting simulation speed"""
    speed: str = Field(
        default="normal",
        description="Simulation speed setting"
    )

    @field_validator('speed')
    @classmethod
    def validate_speed(cls, v):
        valid_speeds = ['paused', 'slow', 'normal', 'fast', 'ultra']
        if v not in valid_speeds:
            raise ValueError(f"Speed must be one of: {', '.join(valid_speeds)}")
        return v


@app.post("/simulation/speed")
@limiter.limit("30/minute")  # Max 30 speed changes per minute
async def set_simulation_speed(request: Request, speed_request: SetSpeedRequest):
    """Set simulation speed"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    speed_map = {
        "paused": (True, 1.0),
        "slow": (False, 2.0),
        "normal": (False, 1.0),
        "fast": (False, 0.5),
        "ultra": (False, 0.1)
    }

    # Validation already done by Pydantic
    paused, tick_rate = speed_map[speed_request.speed]
    simulation.paused = paused
    simulation.tick_rate = tick_rate

    return {
        "success": True,
        "speed": speed_request.speed,
        "tick_rate": tick_rate,
        "paused": paused
    }


@app.get("/simulation/status")
async def get_simulation_status():
    """Get simulation running status"""
    if not simulation:
        return {"running": False, "paused": False, "speed": "stopped"}

    # Determine speed from tick_rate
    if simulation.paused:
        speed = "paused"
    elif simulation.tick_rate >= 2.0:
        speed = "slow"
    elif simulation.tick_rate >= 1.0:
        speed = "normal"
    elif simulation.tick_rate >= 0.5:
        speed = "fast"
    else:
        speed = "ultra"

    return {
        "running": simulation.running,
        "paused": simulation.paused,
        "speed": speed,
        "tick_rate": simulation.tick_rate,
        "current_day": simulation.world.time.day
    }


@app.post("/disasters/trigger")
async def trigger_disaster(request: dict):
    """Force a disaster to occur (for testing/god mode)"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    from world.disasters import DisasterType, DisasterSeverity

    disaster_type_str = request.get("type", "earthquake")
    severity_str = request.get("severity", "moderate")

    try:
        disaster_type = DisasterType(disaster_type_str.lower())
        severity = DisasterSeverity(severity_str.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid disaster type or severity")

    current_tick = simulation.world.time.current_tick
    simulation.disasters.force_disaster(disaster_type, severity, current_tick)

    return {
        "success": True,
        "message": f"Triggered {severity.value} {disaster_type.value}",
        "disaster_type": disaster_type.value,
        "severity": severity.value
    }


# STORY ENGINE & ACHIEVEMENTS - EPIC NARRATIVES!

@app.get("/stories")
async def get_stories():
    """Get epic stories from the story feed"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    return simulation.story_feed.to_dict()


@app.get("/achievements")
async def get_achievements():
    """Get all achievements (agent + civilization)"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    return simulation.achievement_tracker.to_dict()


# NEW ENDPOINTS FOR NEW SYSTEMS

@app.get("/buildings")
async def get_buildings():
    """Get all buildings with category information"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Get buildings from the dynamic building system (completed buildings only)
    buildings = []
    for building in simulation.dynamic_building_system.buildings.values():
        if building.is_complete and not building.collapsed:
            # Get design to find category and purposes
            design = simulation.dynamic_building_system.designs.get(building.design_id)
            category = design.category if design else "Unknown"
            purposes = design.intended_purposes if design else []

            buildings.append({
                'id': building.id,
                'name': building.name,
                'category': category,  # NEW!
                'purposes': purposes,  # NEW!
                'location': {'x': building.location[0], 'y': building.location[1]},
                'builders': list(building.builder_ids),
                'materials_used': building.materials_used,
                'built_date': building.built_date.isoformat() if building.built_date else None,
                'is_complete': building.is_complete,
                'construction_progress': building.construction_progress,
                'collapsed': building.collapsed
            })

    return {"buildings": buildings, "total": len(buildings)}


@app.get("/experiments")
async def get_experiments():
    """Get all experiments - discoveries and failures with rich detail"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Get discoveries with full detail
    discoveries = []
    for discovery in simulation.experimentation_engine.discoveries.values():
        # Get discoverer name
        discoverer = None
        for agent in simulation.world.agents:
            if agent.id == discovery.discovered_by:
                discoverer = agent.name
                break

        # Extract intent data if available
        intent_data = None
        if discovery.intent:
            intent_data = {
                'problem': discovery.intent.problem,
                'goal': discovery.intent.goal,
                'reasoning': discovery.intent.reasoning,
                'hypothesis': discovery.intent.hypothesis,
                'motivation': discovery.intent.motivation
            }

        discoveries.append({
            'id': discovery.id,
            'name': discovery.name,
            'discovered_by_id': discovery.discovered_by,
            'discovered_by_name': discoverer or 'Unknown',
            'discovery_date': discovery.discovery_date.isoformat(),
            'material_name': discovery.material.name if discovery.material else None,
            'properties': [prop.value for prop in discovery.properties] if discovery.properties else [],
            'recipe': discovery.recipe,
            'effectiveness': discovery.effectiveness,
            'category': discovery.category.value,  # What domain: cooking, crafting, etc.
            # ENHANCED: Full discovery story
            'description': discovery.description,
            'discovery_context': discovery.discovery_context,
            'known_by_count': len(discovery.known_by),
            'known_by_ids': list(discovery.known_by),
            'times_used': discovery.times_used,
            'success_rate': discovery.success_rate,
            # CHAIN-OF-THOUGHT: Agent's reasoning
            'intent': intent_data,
        })

    # Get failures with full detail
    failures = []
    for failure in simulation.experimentation_engine.failed_experiments:
        # Get agent name
        agent_name = None
        for agent in simulation.world.agents:
            if agent.id == failure['agent_id']:
                agent_name = agent.name
                break

        failures.append({
            'agent_id': failure['agent_id'],
            'agent_name': agent_name or 'Unknown',
            'inputs': failure['inputs'],
            'method': failure['method'],
            'category': failure.get('category', 'material_science'),  # What domain
            'reason': failure['reason'],
            'date': failure['date'].isoformat(),
            # ENHANCED: Full failure story
            'lesson_learned': failure.get('lesson_learned'),
            'consequences': failure.get('consequences', {}),
            # CHAIN-OF-THOUGHT: Agent's reasoning
            'intent': failure.get('intent'),
        })

    # Get all materials (base + discovered)
    materials = []
    for mat_name, material in simulation.experimentation_engine.materials.items():
        materials.append({
            'name': material.name,
            'hardness': material.hardness,
            'properties': [prop.value for prop in material.all_properties()],
            'is_base': mat_name in ['wood', 'stone', 'clay', 'plant_fiber', 'water', 'sand', 'metal_ore', 'hide']
        })

    return {
        "discoveries": discoveries,
        "failures": failures,
        "materials": materials,
        "total_discoveries": len(discoveries),
        "total_failures": len(failures),
        "success_rate": len(discoveries) / (len(discoveries) + len(failures)) if (len(discoveries) + len(failures)) > 0 else 0
    }


@app.get("/innovations")
async def get_innovations():
    """Get all innovations discovered"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    innovations = [i.to_dict() for i in simulation.innovation_manager.innovations.values()]
    return {"innovations": innovations, "total": len(innovations)}


@app.get("/conflicts")
async def get_conflicts():
    """Get active conflicts"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    conflicts = list(simulation.warfare_manager.active_conflicts.values())
    return {
        "active_conflicts": len(conflicts),
        "conflicts": [
            {
                "id": c.id,
                "type": c.conflict_type.value,
                "reason": c.reason.value,
                "side_a_size": len(c.side_a),
                "side_b_size": len(c.side_b),
                "turns_elapsed": c.turns_elapsed,
            }
            for c in conflicts
        ]
    }


@app.get("/politics")
async def get_politics():
    """Get political landscape - governments, power structures, authority"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    try:
        # Get all governments with enhanced data
        governments = []
        for g in simulation.governance_manager.governments.values():
            if g.active:
                governments.append({
                    "id": g.id,
                    "name": g.name,
                    "type": g.government_type.value,
                    "citizens": len(g.citizens),
                    "approval": g.approval_rating,
                    "leader": g.leader_id,
                    "laws": len(g.laws) if hasattr(g, 'laws') else 0,
                    "authority": g.authority if hasattr(g, 'authority') else 0.5
                })
        
        # Get governance stats
        gov_stats = simulation.governance_manager.get_statistics()
        
        return {
            "governments": governments,
            "total_governments": len(governments),
            "total_citizens": sum(len(g.citizens) for g in simulation.governance_manager.governments.values() if g.active),
            "statistics": gov_stats
        }
    except Exception as e:
        logger.error(f"Error getting politics data: {e}")
        return {
            "governments": [],
            "total_governments": 0,
            "error": str(e)
        }


@app.get("/culture")
async def get_culture():
    """Get cultural data - groups, traditions, shared values, celebrations"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    try:
        # Get all social groups with cultural aspects
        groups = []
        for group in simulation.group_manager.groups.values():
            groups.append({
                "id": group.id,
                "name": group.name,
                "members": len(group.members),
                "leader": group.leader_id,
                "cohesion": group.cohesion if hasattr(group, 'cohesion') else 0.5,
                "purpose": group.purpose if hasattr(group, 'purpose') else "General"
            })
        
        # Get fun system cultural data (celebrations, traditions, art)
        fun_stats = simulation.fun_system.get_stats() if hasattr(simulation, 'fun_system') else {}
        
        # Get knowledge system cultural knowledge
        cultural_knowledge = []
        if hasattr(simulation, 'knowledge_system'):
            for kr in simulation.knowledge_system.knowledge_records.values():
                if hasattr(kr, 'knowledge_type') and 'culture' in kr.knowledge_type.lower():
                    cultural_knowledge.append({
                        "name": kr.name,
                        "type": kr.knowledge_type,
                        "discoverer": kr.discoverer_id if hasattr(kr, 'discoverer_id') else None
                    })
        
        return {
            "groups": groups,
            "total_groups": len(groups),
            "celebrations_held": fun_stats.get('celebrations_held', 0),
            "games_played": fun_stats.get('games_played', 0),
            "art_created": fun_stats.get('art_created', 0),
            "traditions": fun_stats.get('traditions', {}),
            "cultural_knowledge": cultural_knowledge[:20],  # Top 20
            "statistics": {
                "social_cohesion": sum(g.cohesion if hasattr(g, 'cohesion') else 0.5 for g in simulation.group_manager.groups.values()) / max(len(groups), 1)
            }
        }
    except Exception as e:
        logger.error(f"Error getting culture data: {e}")
        return {
            "groups": [],
            "total_groups": 0,
            "error": str(e)
        }


@app.get("/governments")
async def get_governments():
    """Get all governments"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    governments = [
        {
            "id": g.id,
            "name": g.name,
            "type": g.government_type.value,
            "citizens": len(g.citizens),
            "approval": g.approval_rating,
            "leader": g.leader_id,
        }
        for g in simulation.governance_manager.governments.values()
        if g.active
    ]
    return {"governments": governments, "total": len(governments)}


@app.get("/knowledge")
async def get_knowledge():
    """Get all knowledge records"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    knowledge_records = [
        {
            "id": kr.id,
            "name": kr.name,
            "type": kr.knowledge_type,
            "content": kr.content,
            "author": kr.original_author,
            "transmission_method": kr.transmission_method,
            "accuracy": kr.accuracy,
            "known_by_count": len(kr.known_by),
            "times_taught": kr.times_taught,
            "mutation_count": kr.mutation_count,
            "has_mutated": kr.content != kr.original_content,
        }
        for kr in simulation.knowledge_system.knowledge_records.values()
    ]
    return {"knowledge": knowledge_records, "total": len(knowledge_records)}


@app.get("/knowledge/libraries")
async def get_knowledge_libraries():
    """Get all libraries"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    libraries = [
        {
            "id": lib.id,
            "name": lib.name,
            "location": {"x": lib.location[0], "y": lib.location[1]},
            "founder": lib.founded_by,
            "founded_date": lib.founded_date.isoformat(),
            "documents_count": len(lib.documents),
            "total_knowledge": lib.total_knowledge_pieces,
            "visitors_count": len(lib.visitors),
            "times_visited": lib.times_visited,
            "is_famous": lib.is_famous,
            "librarian": lib.librarian_id,
        }
        for lib in simulation.knowledge_system.libraries.values()
    ]
    return {"libraries": libraries, "total": len(libraries)}


@app.get("/knowledge/teaching")
async def get_teaching_sessions():
    """Get recent teaching sessions"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Get last 50 teaching sessions
    recent_sessions = simulation.knowledge_system.teaching_sessions[-50:]

    sessions = [
        {
            "id": ts.id,
            "teacher": ts.teacher_id,
            "students_count": len(ts.student_ids),
            "knowledge_count": len(ts.knowledge_taught),
            "date": ts.session_date.isoformat(),
            "teacher_skill": ts.teacher_skill,
            "method": ts.method,
        }
        for ts in recent_sessions
    ]
    return {"sessions": sessions, "total": len(sessions)}


@app.get("/materials")
async def get_materials():
    """Get all materials organized by category (for card-based display)"""
    category_summary = {}

    for category in MaterialCategory:
        materials_in_category = get_materials_by_category(category)
        if materials_in_category:
            category_summary[category.value] = {
                "name": category.value.replace('_', ' ').title(),
                "count": len(materials_in_category),
                "materials": [
                    {
                        "id": mat.id,
                        "name": mat.name,
                        "description": mat.description,
                        "hardness": mat.hardness,
                        "weight": mat.weight,
                        "durability": mat.durability,
                        "flammable": mat.flammable,
                        "edible": mat.edible,
                        "liquid": mat.liquid,
                        "tags": mat.tags
                    }
                    for mat in materials_in_category
                ]
            }

    return {
        "categories": category_summary,
        "total_materials": len(ALL_MATERIALS)
    }


@app.get("/materials/{category}")
async def get_materials_by_category_endpoint(category: str):
    """Get detailed materials in a specific category"""
    try:
        cat = MaterialCategory(category)
        materials = get_materials_by_category(cat)
        return {
            "category": category,
            "materials": [
                {
                    "id": mat.id,
                    "name": mat.name,
                    "description": mat.description,
                    "hardness": mat.hardness,
                    "weight": mat.weight,
                    "durability": mat.durability,
                    "flammable": mat.flammable,
                    "edible": mat.edible,
                    "liquid": mat.liquid,
                    "stackable": mat.stackable,
                    "tags": mat.tags,
                    "discovered_by": mat.discovered_by,
                    "discovery_method": mat.discovery_method
                }
                for mat in materials
            ]
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")


@app.get("/recipes")
async def get_recipes():
    """Get all crafting recipes"""
    return {
        "recipes": [
            {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "output_item": recipe.output_item,
                "output_quantity": recipe.output_quantity,
                "inputs": recipe.inputs,
                "requires_fire": recipe.requires_fire,
                "requires_water": recipe.requires_water,
                "requires_tool": recipe.requires_tool,
                "required_skill": recipe.required_skill,
                "min_skill_level": recipe.min_skill_level,
                "is_basic": recipe.is_basic,
                "difficulty": recipe.difficulty,
                "times_crafted": recipe.times_crafted
            }
            for recipe in ALL_RECIPES.values()
        ],
        "total": len(ALL_RECIPES)
    }


@app.get("/agents/{agent_id}/inventory")
async def get_agent_inventory(agent_id: str):
    """Get agent's inventory organized by material category"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    agent = simulation._get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Organize inventory by category
    inventory_by_category = {}

    for item_id, quantity in agent.inventory.items.items():
        material = get_material(item_id)
        if material:
            category = material.category.value
            if category not in inventory_by_category:
                inventory_by_category[category] = {
                    "name": category.replace('_', ' ').title(),
                    "items": []
                }

            inventory_by_category[category]["items"].append({
                "id": material.id,
                "name": material.name,
                "description": material.description,
                "quantity": quantity,
                "hardness": material.hardness,
                "weight": material.weight,
                "durability": material.durability,
                "tags": material.tags
            })

    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "inventory_by_category": inventory_by_category,
        "total_items": agent.inventory.get_total_items(),
        "capacity": agent.inventory.capacity
    }


@app.get("/roles")
async def get_emergent_roles():
    """Get all emergent roles - agent-discovered, agent-named!"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Get all roles with agent names
    roles_data = []
    for agent_id, roles in simulation.role_emergence.agent_roles.items():
        # Get agent name
        agent = simulation._get_agent_by_id(agent_id)
        agent_name = agent.name if agent else "Unknown"

        for role in roles:
            roles_data.append({
                'role_id': role.role_id,
                'agent_id': role.agent_id,
                'agent_name': agent_name,
                # AGENT-CREATED NAME (not system defined!)
                'custom_role_name': role.custom_role_name,
                'role_name_language': role.role_name_language,
                # Behavior pattern that led to this role
                'pattern_type': role.behavior_pattern.pattern_type,
                'dominant_actions': role.behavior_pattern.dominant_actions,
                'pattern_strength': role.behavior_pattern.pattern_strength,
                # Emergence details
                'emergence_date': role.emergence_date.isoformat(),
                'emergence_context': role.emergence_context,
                # Community recognition
                'recognized_by_count': len(role.recognized_by),
                'recognition_strength': role.recognition_strength,
                'name_adopters_count': len(role.name_adopters),
                # Role performance
                'times_acted_in_role': role.times_acted_in_role,
                'role_effectiveness': role.role_effectiveness,
                # Name evolution
                'previous_names': role.previous_names,
            })

    # Get role vocabulary (what role names exist in the community)
    role_vocabulary = simulation.role_emergence.role_vocabulary
    role_name_creators = simulation.role_emergence.role_name_origins

    # Get role name origins with creator names
    vocabulary_with_creators = []
    for role_name, usage_count in sorted(role_vocabulary.items(), key=lambda x: x[1], reverse=True):
        creator_id = role_name_creators.get(role_name, "Unknown")
        creator = simulation._get_agent_by_id(creator_id)
        creator_name = creator.name if creator else "Unknown"

        vocabulary_with_creators.append({
            'role_name': role_name,
            'usage_count': usage_count,
            'created_by_id': creator_id,
            'created_by_name': creator_name
        })

    return {
        "roles": roles_data,
        "total_roles": len(roles_data),
        "agents_with_roles": len(simulation.role_emergence.agent_roles),
        "unique_role_names": len(role_vocabulary),
        "role_vocabulary": vocabulary_with_creators,
        "statistics": simulation.role_emergence.get_statistics()
    }


@app.get("/fun/stats")
async def get_fun_statistics():
    """Get fun system statistics - celebrations, games, art!"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    stats = simulation.fun_system.get_stats()

    return {
        "celebrations": {
            "total": stats['total_celebrations'],
            "active": stats['active_celebrations'],
            "traditions_count": stats['traditions_count'],
            "most_popular_tradition": stats.get('most_popular_tradition')
        },
        "games": {
            "total": stats['total_games'],
            "active": stats['active_games']
        },
        "art": {
            "total_created": stats['total_art']
        }
    }


@app.get("/fun/celebrations")
async def get_celebrations():
    """Get all active and recent celebrations"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    active_celebrations = []
    for celebration in simulation.fun_system.active_celebrations.values():
        active_celebrations.append({
            "id": celebration.id,
            "type": celebration.celebration_type.value,
            "name": celebration.celebration_name,
            "organizer_id": celebration.organizer_id,
            "participants": list(celebration.participants),
            "participant_count": len(celebration.participants),
            "location": celebration.location,
            "trigger_event": celebration.trigger_event,
            "duration_remaining": celebration.duration_ticks,
            "mood_boost": celebration.mood_boost
        })

    recent_celebrations = []
    for celebration in simulation.fun_system.celebration_history[-10:]:  # Last 10
        recent_celebrations.append({
            "id": celebration.id,
            "type": celebration.celebration_type.value,
            "name": celebration.celebration_name,
            "participant_count": len(celebration.participants),
            "trigger_event": celebration.trigger_event
        })

    return {
        "active": active_celebrations,
        "recent": recent_celebrations,
        "traditions": simulation.fun_system.traditions
    }


@app.get("/fun/games")
async def get_games():
    """Get all active and recent games"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    active_games = []
    for game in simulation.fun_system.active_games.values():
        active_games.append({
            "id": game.id,
            "type": game.game_type.value,
            "players": game.players,
            "player_count": len(game.players),
            "stakes": game.stakes,
            "spectators": list(game.spectators),
            "completed": game.completed
        })

    recent_games = []
    for game in simulation.fun_system.game_history[-10:]:  # Last 10
        if game.winner:
            recent_games.append({
                "id": game.id,
                "type": game.game_type.value,
                "winner": game.winner,
                "players": game.players,
                "scores": game.scores
            })

    return {
        "active": active_games,
        "recent": recent_games
    }


@app.get("/fun/art")
async def get_art_pieces():
    """Get all art created in the civilization"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    art_pieces = []
    for art in simulation.fun_system.art_pieces.values():
        # Get creator name
        creator = simulation._get_agent_by_id(art.creator_id)
        creator_name = creator.name if creator else "Unknown"

        art_pieces.append({
            "id": art.id,
            "type": art.art_type,
            "title": art.title,
            "creator_id": art.creator_id,
            "creator_name": creator_name,
            "quality": art.quality,
            "fame_generated": art.fame_generated,
            "cultural_value": art.cultural_value,
            "created_at": art.created_at.isoformat(),
            "viewer_count": len(art.viewers),
            "reactions": art.reactions
        })

    # Sort by quality
    art_pieces.sort(key=lambda x: x['quality'], reverse=True)

    return {
        "art_pieces": art_pieces,
        "total_art": len(art_pieces),
        "by_type": {
            art_type: len([a for a in art_pieces if a['type'] == art_type])
            for art_type in set(a['type'] for a in art_pieces)
        }
    }


@app.get("/agents/{agent_id}/fun")
async def get_agent_fun_stats(agent_id: str):
    """Get fun statistics for a specific agent"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")

    stats = simulation.fun_system.get_agent_fun_stats(agent_id)

    return stats


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time world updates"""
    await websocket.accept()
    active_websockets.append(websocket)

    try:
        # Send initial state
        if simulation:
            state = simulation.get_state_snapshot()
            await websocket.send_json(state)

        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        pass
    finally:
        # The broadcast loop may already have dropped it
        _drop_websocket(websocket)


# Serve static files (web interface)
@app.get("/app")
async def serve_app():
    """Serve enhanced web interface"""
    return FileResponse(WEB_DIR / "enhanced.html")


@app.get("/app/town_map.js")
async def serve_town_map():
    """The map renderer used by /app (web/town_map.js)"""
    return FileResponse(WEB_DIR / "town_map.js", media_type="application/javascript")


@app.get("/map")
async def get_map():
    """Terrain grid and resource spots, for drawing the map (world/town_view.py)"""
    if not simulation:
        raise HTTPException(status_code=503, detail="Simulation not running")
    from world.town_view import map_layout
    return map_layout(simulation)


@app.get("/materials_example")
async def serve_materials_example():
    """Serve materials system example"""
    return FileResponse(WEB_DIR / "materials_example.html")


@app.get("/inventory")
async def serve_player_inventory():
    """Serve player inventory & crafting interface"""
    return FileResponse(WEB_DIR / "player_inventory.html")

@app.get("/app/classic")
async def serve_classic_app():
    """Serve original web interface"""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/game")
async def serve_game_interface():
    """Redirect /game to /app for consistency"""
    return FileResponse(WEB_DIR / "enhanced.html")


def main():
    """Run the server"""
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
