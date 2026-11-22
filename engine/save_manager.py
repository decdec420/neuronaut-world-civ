"""
SAVE MANAGER - Multiple World Saves Like A Real Game!

Allows players to:
- Create named saves (e.g., "Stone Age World", "My Dynasty")
- Load any save and continue playing
- Delete old saves
- Start new worlds without losing progress
"""

import os
import json
import gzip
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class SaveManager:
    """Manages multiple named world saves"""

    def __init__(self, saves_dir: str = "save_states"):
        self.saves_dir = Path(saves_dir)
        self.saves_dir.mkdir(exist_ok=True)

        # Metadata file tracks all saves
        self.metadata_file = self.saves_dir / "saves_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load save metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"saves": []}

    def _save_metadata(self):
        """Save metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def create_save(self, save_name: str, world_data: Dict, simulation=None) -> bool:
        """
        Create a new named save

        Args:
            save_name: User-friendly name (e.g., "My First World")
            world_data: Summary of the world (for the list of saves)
            simulation: the running SimulationEngine; if given, its full state
                is saved too, so the save can be loaded and played on

        Returns:
            True if save successful
        """
        # Sanitize filename
        safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            safe_name = f"world_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_{timestamp}.json.gz"
        filepath = self.saves_dir / filename

        # Save compressed world data
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(world_data, f, indent=2)

        state_filename = None
        if simulation is not None:
            from engine.persistence import save_full_state
            state_filename = f"{safe_name}_{timestamp}.state.gz"
            save_full_state(simulation, str(self.saves_dir / state_filename))

        # Add to metadata
        save_entry = {
            "id": timestamp,
            "name": save_name,
            "filename": filename,
            "state_filename": state_filename,
            "created_at": timestamp,
            "last_played": timestamp,
            "stats": {
                "current_day": world_data.get('world', {}).get('time', {}).get('current_day', 0),
                "population": world_data.get('world', {}).get('total_agents', 0),
                "alive_agents": world_data.get('world', {}).get('alive_agents', 0),
                "buildings": len(world_data.get('buildings', {})),
                "discoveries": len(world_data.get('experiments', {}).get('discoveries', [])),
            }
        }

        self.metadata["saves"].append(save_entry)
        self._save_metadata()

        return True

    def list_saves(self) -> List[Dict]:
        """Get list of all saves with metadata"""
        return sorted(
            self.metadata["saves"],
            key=lambda x: x["last_played"],
            reverse=True  # Most recent first
        )

    def load_save(self, save_id: str) -> Optional[Dict]:
        """
        Load a save by ID

        Args:
            save_id: The timestamp ID of the save

        Returns:
            World data dict, or None if not found
        """
        # Find save in metadata
        save_entry = next((s for s in self.metadata["saves"] if s["id"] == save_id), None)
        if not save_entry:
            return None

        filepath = self.saves_dir / save_entry["filename"]
        if not filepath.exists():
            return None

        # Load compressed data
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            world_data = json.load(f)

        # Update last played
        save_entry["last_played"] = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._save_metadata()

        return world_data

    def state_path(self, save_id: str) -> Optional[Path]:
        """The save's full-state file, if it has one (older saves don't)."""
        save_entry = next((s for s in self.metadata["saves"] if s["id"] == save_id), None)
        if not save_entry or not save_entry.get("state_filename"):
            return None
        path = self.saves_dir / save_entry["state_filename"]
        return path if path.exists() else None

    def delete_save(self, save_id: str) -> bool:
        """
        Delete a save

        Args:
            save_id: The timestamp ID of the save

        Returns:
            True if deleted successfully
        """
        # Find save in metadata
        save_entry = next((s for s in self.metadata["saves"] if s["id"] == save_id), None)
        if not save_entry:
            return False

        # Delete files
        filepath = self.saves_dir / save_entry["filename"]
        if filepath.exists():
            filepath.unlink()
        if save_entry.get("state_filename"):
            state_file = self.saves_dir / save_entry["state_filename"]
            if state_file.exists():
                state_file.unlink()

        # Remove from metadata
        self.metadata["saves"] = [s for s in self.metadata["saves"] if s["id"] != save_id]
        self._save_metadata()

        return True

    def auto_save(self, world_data: Dict, slot_name: str = "autosave") -> bool:
        """
        Auto-save to a special slot
        Overwrites previous autosave
        """
        # Delete previous autosave
        autosaves = [s for s in self.metadata["saves"] if s["name"].startswith(slot_name)]
        for save in autosaves:
            self.delete_save(save["id"])

        # Create new autosave
        return self.create_save(f"{slot_name}_{datetime.now().strftime('%H:%M')}", world_data)

    def cleanup_old_autosaves(self, keep_count: int = 3):
        """Keep only the N most recent autosaves"""
        autosaves = [s for s in self.metadata["saves"] if s["name"].startswith("autosave")]
        autosaves.sort(key=lambda x: x["created_at"], reverse=True)

        # Delete old ones
        for save in autosaves[keep_count:]:
            self.delete_save(save["id"])
