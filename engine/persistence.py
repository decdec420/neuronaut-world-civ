"""
Persistent State System - Continuous Simulation Runs

Enables simulations to run continuously for weeks/months!

Features:
- Auto-save every N ticks
- State snapshots for rollback
- Historical data tracking
- Resume from saved state
- Export civilization history

This lets you run the simulation overnight, come back, and see what happened!
"""

import json
import pickle
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import gzip


@dataclass
class Snapshot:
    """A point-in-time snapshot of the simulation"""
    snapshot_id: str
    tick: int
    world_day: int
    timestamp: datetime

    # Statistics at this moment
    total_agents: int
    alive_agents: int
    total_buildings: int
    total_innovations: int
    total_conflicts: int

    # File paths
    full_state_path: str
    compressed: bool = True


class PersistenceEngine:
    """
    Manages persistent state for continuous runs.

    Auto-saves, snapshots, and historical tracking.
    """

    def __init__(self, save_directory: str = "./save_states"):
        self.save_dir = save_directory
        self.snapshots: List[Snapshot] = []

        # Create save directory
        os.makedirs(save_directory, exist_ok=True)

        # Auto-save settings
        self.auto_save_interval = 1000  # Save every 1000 ticks
        self.keep_last_n_snapshots = 10

        # Reference to simulation (set externally)
        self.simulation = None

    def save_simulation_state(
        self,
        simulation,
        snapshot_name: Optional[str] = None
    ) -> Snapshot:
        """
        Save complete simulation state to disk.

        Returns snapshot record.
        """

        # Generate snapshot ID
        if not snapshot_name:
            snapshot_name = f"snapshot_tick_{simulation.world.time.current_tick}"

        snapshot_id = f"{snapshot_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Collect state
        state = {
            "version": "2.0_autonomous",
            "tick": simulation.world.time.current_tick,
            "world_day": simulation.world.time.day,
            "timestamp": datetime.now().isoformat(),

            # World state
            "world": {
                "width": simulation.world.map.width,
                "height": simulation.world.map.height,
                "season": simulation.world.time.season,
                "resource_pools": simulation.world.resource_pools,
            },

            # Agents
            "agents": [agent.to_dict() for agent in simulation.world.agents],

            # NEW SYSTEMS
            "experimentation": self._serialize_experimentation(simulation.experimentation_engine) if hasattr(simulation, 'experimentation_engine') else {},
            "dynamic_buildings": self._serialize_buildings(simulation.dynamic_building_system) if hasattr(simulation, 'dynamic_building_system') else {},
            "knowledge": self._serialize_knowledge(simulation.knowledge_system) if hasattr(simulation, 'knowledge_system') else {},
            "consequences": self._serialize_consequences(simulation.consequence_engine) if hasattr(simulation, 'consequence_engine') else {},
            "roles": self._serialize_roles(simulation.role_emergence) if hasattr(simulation, 'role_emergence') else {},

            # OLD SYSTEMS (for compatibility)
            "relationships": [
                {
                    "agent_a": r.agent_a,
                    "agent_b": r.agent_b,
                    "type": r.relationship_type.value if hasattr(r.relationship_type, 'value') else str(r.relationship_type),
                    "strength": r.strength
                }
                for r in simulation.relationship_manager.relationships.values()
            ] if hasattr(simulation, 'relationship_manager') else [],

            "economy": simulation.economy.get_wealth_statistics() if hasattr(simulation, 'economy') else {},

            "events": [
                e.to_dict() if hasattr(e, 'to_dict') else str(e)
                for e in simulation.event_logger.get_recent_events(100)
            ] if hasattr(simulation, 'event_logger') else [],
        }

        # Save to file
        file_path = os.path.join(self.save_dir, f"{snapshot_id}.json.gz")

        # Compress and save
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)

        # Create snapshot record
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            tick=simulation.world.time.current_tick,
            world_day=simulation.world.time.day,
            timestamp=datetime.now(),
            total_agents=len(simulation.world.agents),
            alive_agents=sum(1 for a in simulation.world.agents if a.alive),
            total_buildings=len(simulation.dynamic_building_system.buildings) if hasattr(simulation, 'dynamic_building_system') else 0,
            total_innovations=len(simulation.experimentation_engine.discoveries) if hasattr(simulation, 'experimentation_engine') else 0,
            total_conflicts=len(simulation.warfare_manager.active_conflicts) if hasattr(simulation, 'warfare_manager') else 0,
            full_state_path=file_path,
            compressed=True
        )

        self.snapshots.append(snapshot)

        # Clean old snapshots
        if len(self.snapshots) > self.keep_last_n_snapshots:
            old_snapshot = self.snapshots.pop(0)
            # Delete old file
            if os.path.exists(old_snapshot.full_state_path):
                os.remove(old_snapshot.full_state_path)

        return snapshot

    def _serialize_experimentation(self, exp_engine) -> Dict:
        """Serialize experimentation engine state"""
        return {
            "materials": {
                name: {
                    "name": mat.name,
                    "properties": [p.value for p in mat.all_properties()],
                    "hardness": mat.hardness,
                    "discovered_by": mat.discovered_by
                }
                for name, mat in exp_engine.materials.items()
            },
            "discoveries": {
                disc_id: {
                    "name": disc.name,
                    "discovered_by": disc.discovered_by,
                    "known_by": list(disc.known_by),
                    "effectiveness": disc.effectiveness
                }
                for disc_id, disc in exp_engine.discoveries.items()
            }
        }

    def _serialize_buildings(self, building_system) -> Dict:
        """Serialize dynamic building system state"""
        return {
            "designs": {
                design_id: {
                    "name": design.name,
                    "designer_id": design.designer_id,
                    "purposes": design.intended_purposes,
                    "materials_needed": design.materials_needed
                }
                for design_id, design in building_system.designs.items()
            },
            "buildings": {
                building_id: {
                    "name": building.name,
                    "location": building.location,
                    "is_complete": building.is_complete,
                    "durability": building.durability,
                    "collapsed": building.collapsed
                }
                for building_id, building in building_system.buildings.items()
            }
        }

    def _serialize_knowledge(self, knowledge_system) -> Dict:
        """Serialize knowledge system state"""
        return {
            "total_knowledge": len(knowledge_system.knowledge_records),
            "total_documents": len(knowledge_system.documents),
            "total_libraries": len(knowledge_system.libraries),
            "libraries": [
                {
                    "name": lib.name,
                    "location": lib.location,
                    "documents": len(lib.documents),
                    "visitors": len(lib.visitors)
                }
                for lib in knowledge_system.libraries.values()
            ]
        }

    def _serialize_consequences(self, consequence_engine) -> Dict:
        """Serialize consequence engine state"""
        return {
            "death_count": consequence_engine.death_count,
            "bankruptcy_count": consequence_engine.bankruptcy_count,
            "total_consequences": len(consequence_engine.consequences)
        }

    def _serialize_roles(self, role_emergence) -> Dict:
        """Serialize role emergence state"""
        return {
            "total_roles": sum(len(roles) for roles in role_emergence.agent_roles.values()),
            "role_distribution": role_emergence.role_vocabulary
        }

    def create_snapshot(self) -> Dict:
        """
        Create a snapshot dict WITHOUT saving to disk.
        Used by SaveManager to create manual saves.

        Returns:
            World state dictionary
        """
        if not self.simulation:
            raise ValueError("Simulation reference not set")

        simulation = self.simulation

        # Collect state
        state = {
            "version": "2.0_autonomous",
            "tick": simulation.world.time.current_tick,
            "world_day": simulation.world.time.day,
            "timestamp": datetime.now().isoformat(),

            # World state
            "world": {
                "width": simulation.world.map.width,
                "height": simulation.world.map.height,
                "season": simulation.world.time.season,
                "resource_pools": simulation.world.resource_pools,
                "time": {
                    "current_tick": simulation.world.time.current_tick,
                    "current_day": simulation.world.time.day,
                },
                "total_agents": len(simulation.world.agents),
                "alive_agents": sum(1 for a in simulation.world.agents if a.alive),
            },

            # Agents
            "agents": [agent.to_dict() for agent in simulation.world.agents],

            # NEW SYSTEMS
            "experimentation": self._serialize_experimentation(simulation.experimentation_engine) if hasattr(simulation, 'experimentation_engine') else {},
            "buildings": {
                building_id: {
                    "id": building.id,
                    "name": building.name,
                    "location": building.location,
                    "is_complete": building.is_complete,
                    "durability": building.durability,
                    "collapsed": building.collapsed,
                    "materials_used": building.materials_used,
                    "purposes": building.purposes,
                    "category": building.category,
                    "built_by": building.built_by,
                    "built_date": building.built_date.isoformat() if building.built_date else None,
                }
                for building_id, building in simulation.dynamic_building_system.buildings.items()
            } if hasattr(simulation, 'dynamic_building_system') else {},
            "knowledge": self._serialize_knowledge(simulation.knowledge_system) if hasattr(simulation, 'knowledge_system') else {},
            "consequences": self._serialize_consequences(simulation.consequence_engine) if hasattr(simulation, 'consequence_engine') else {},
            "roles": self._serialize_roles(simulation.role_emergence) if hasattr(simulation, 'role_emergence') else {},

            # Relationships
            "relationships": [
                {
                    "agent_a": r.agent_a,
                    "agent_b": r.agent_b,
                    "type": r.relationship_type.value if hasattr(r.relationship_type, 'value') else str(r.relationship_type),
                    "strength": r.strength
                }
                for r in simulation.relationship_manager.relationships.values()
            ] if hasattr(simulation, 'relationship_manager') else [],

            "economy": simulation.economy.get_wealth_statistics() if hasattr(simulation, 'economy') else {},

            "events": [
                e.to_dict() if hasattr(e, 'to_dict') else str(e)
                for e in simulation.event_logger.get_recent_events(100)
            ] if hasattr(simulation, 'event_logger') else [],

            # Tech progression
            "tech_progression": simulation.tech_progression.get_statistics() if hasattr(simulation, 'tech_progression') else {},

            # Meta progression
            "meta_progression": simulation.meta_progression.to_dict() if hasattr(simulation, 'meta_progression') else {},

            # Civilization progression
            "civilization_progression": {
                "current_era": simulation.civilization.current_era.value,
                "milestones_achieved": sum(1 for m in simulation.civilization.milestones.values() if m.is_achieved),
            } if hasattr(simulation, 'civilization') else {},

            # Experiments/discoveries for save metadata
            "experiments": {
                "discoveries": [
                    {
                        "name": disc.name,
                        "discovered_by": disc.discovered_by,
                        "effectiveness": disc.effectiveness
                    }
                    for disc in simulation.experimentation_engine.discoveries.values()
                ]
            } if hasattr(simulation, 'experimentation_engine') else {"discoveries": []},
        }

        return state

    def restore_snapshot(self, state: Dict):
        """
        Restore simulation from a snapshot dict.
        Used by SaveManager to load saves.

        Args:
            state: World state dictionary
        """
        if not self.simulation:
            raise ValueError("Simulation reference not set")

        # TODO: Implement full state restoration
        # For now, this is a placeholder - full restoration requires
        # reconstructing all objects from the saved state
        print(f"⚠️ Loading saves not fully implemented yet")
        print(f"   Snapshot from Day {state.get('world_day', 0)}")
        print(f"   Agents: {len(state.get('agents', []))}")
        print(f"   Buildings: {len(state.get('buildings', {}))}")

    def load_simulation_state(self, snapshot_id: str):
        """
        Load simulation state from snapshot.

        Returns state dictionary.
        """

        # Find snapshot
        snapshot = None
        for s in self.snapshots:
            if s.snapshot_id == snapshot_id:
                snapshot = s
                break

        if not snapshot:
            # Try to load from file
            file_path = os.path.join(self.save_dir, f"{snapshot_id}.json.gz")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Snapshot {snapshot_id} not found")

            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                state = json.load(f)

            return state

        # Load from snapshot
        with gzip.open(snapshot.full_state_path, 'rt', encoding='utf-8') as f:
            state = json.load(f)

        return state

    def export_civilization_history(
        self,
        simulation,
        output_file: str = "civilization_history.json"
    ):
        """
        Export complete civilization history for analysis.

        Useful for studying "what if this world evolved differently?"
        """

        history = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_ticks": simulation.world.time.current_tick,
                "total_days": simulation.world.time.day,
                "simulation_duration": f"{simulation.world.time.day} days",
            },

            "agents": {
                "total_created": simulation.total_agents_created if hasattr(simulation, 'total_agents_created') else 0,
                "currently_alive": sum(1 for a in simulation.world.agents if a.alive),
                "agent_list": [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "age": agent.age,
                        "alive": agent.alive,
                        "wealth": agent.wealth,
                        "days_survived": agent.ticks_lived // 24  # Assuming 24 ticks per day
                    }
                    for agent in simulation.world.agents
                ]
            },

            "innovations": self._export_innovations(simulation),
            "buildings": self._export_buildings(simulation),
            "knowledge": self._export_knowledge(simulation),
            "major_events": self._export_major_events(simulation),
            "milestones": self._export_milestones(simulation),
            "civilization": self._export_civilization_progress(simulation),
            "statistics": self._export_statistics(simulation),
        }

        # Save
        output_path = os.path.join(self.save_dir, output_file)
        with open(output_path, 'w') as f:
            json.dump(history, f, indent=2, default=str)

        return output_path

    def _export_innovations(self, simulation) -> Dict:
        """Export all innovations discovered"""
        if not hasattr(simulation, 'experimentation_engine'):
            return {}

        return {
            "total_discoveries": len(simulation.experimentation_engine.discoveries),
            "discoveries": [
                {
                    "name": disc.name,
                    "discovered_by": disc.discovered_by,
                    "date": disc.discovery_date.isoformat(),
                    "known_by_count": len(disc.known_by),
                    "effectiveness": disc.effectiveness
                }
                for disc in simulation.experimentation_engine.discoveries.values()
            ]
        }

    def _export_buildings(self, simulation) -> Dict:
        """Export all buildings constructed"""
        if not hasattr(simulation, 'dynamic_building_system'):
            return {}

        return {
            "total_buildings": len(simulation.dynamic_building_system.buildings),
            "collapsed": sum(1 for b in simulation.dynamic_building_system.buildings.values() if b.collapsed),
            "buildings": [
                {
                    "name": building.name,
                    "location": building.location,
                    "built_date": building.built_date.isoformat() if building.built_date else None,
                    "durability": building.durability,
                    "collapsed": building.collapsed
                }
                for building in simulation.dynamic_building_system.buildings.values()
                if building.is_complete
            ]
        }

    def _export_knowledge(self, simulation) -> Dict:
        """Export knowledge system stats"""
        if not hasattr(simulation, 'knowledge_system'):
            return {}

        return simulation.knowledge_system.get_statistics()

    def _export_major_events(self, simulation) -> List:
        """Export important historical events"""
        if not hasattr(simulation, 'event_logger'):
            return []

        from engine.events import EventImportance

        major_events = simulation.event_logger.get_recent_events(
            count=1000,
            min_importance=EventImportance.MODERATE
        )

        return [
            {
                "title": event.title,
                "description": event.description,
                "tick": event.tick,
                "category": event.category.value if hasattr(event.category, 'value') else str(event.category)
            }
            for event in major_events
        ]

    def _export_milestones(self, simulation) -> Dict:
        """Export civilization milestones achieved"""
        if not hasattr(simulation, 'milestone_history'):
            return {"total": 0, "achieved": []}

        return {
            "total": len(simulation.milestone_history),
            "achieved": simulation.milestone_history,
            "milestone_types": {
                "population": [m for m in simulation.milestone_history if m["type"] == "population"],
                "buildings": [m for m in simulation.milestone_history if m["type"] == "buildings"],
                "knowledge": [m for m in simulation.milestone_history if m["type"] == "knowledge"],
            }
        }

    def _export_civilization_progress(self, simulation) -> Dict:
        """Export civilization progression data"""
        if not hasattr(simulation, 'civilization'):
            return {}

        civ = simulation.civilization
        return {
            "current_era": civ.current_era.value,
            "available_resources": civ.available_resources,
            "tech_milestones_achieved": sum(1 for m in civ.milestones.values() if m.is_achieved),
            "tech_milestones_total": len(civ.milestones),
            "pioneers": civ.get_pioneers(),
            "next_milestone": civ.get_next_milestone().name if civ.get_next_milestone() else None,
            "production_multiplier": civ.get_production_multiplier(),
        }

    def _export_statistics(self, simulation) -> Dict:
        """Export comprehensive statistics"""
        return {
            "experimentation": simulation.experimentation_engine.get_statistics() if hasattr(simulation, 'experimentation_engine') else {},
            "buildings": simulation.dynamic_building_system.get_statistics() if hasattr(simulation, 'dynamic_building_system') else {},
            "knowledge": simulation.knowledge_system.get_statistics() if hasattr(simulation, 'knowledge_system') else {},
            "consequences": simulation.consequence_engine.get_statistics() if hasattr(simulation, 'consequence_engine') else {},
            "roles": simulation.role_emergence.get_statistics() if hasattr(simulation, 'role_emergence') else {},
        }

    def get_snapshot_history(self) -> List[Dict]:
        """Get list of all snapshots"""
        return [
            {
                "id": s.snapshot_id,
                "tick": s.tick,
                "day": s.world_day,
                "timestamp": s.timestamp.isoformat(),
                "agents": s.alive_agents,
                "buildings": s.total_buildings,
                "innovations": s.total_innovations
            }
            for s in self.snapshots
        ]
