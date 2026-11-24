"""
SAVE MANAGER - named world saves you can list, load and delete.

Each save is two files in the save folder (SAVE_DIR, default save_states/ in
the repository) plus an entry in saves_metadata.json, the index:
- <name>_<id>.json.gz   a summary of the world, for the list of saves
- <name>_<id>.state.gz  the full world, which is what loading plays on

The server's autosave (AUTOSAVE_EVERY ticks) makes ordinary saves marked as
autosaves and keeps the newest AUTOSAVE_KEEP of them.

The index is read from disk before every change and written atomically
(a temporary file, then a rename), so the server and the engine's autosave
can both use it without overwriting each other's entries, and a crash
mid-write can't leave a half-written index.
"""

import gzip
import json
import logging
import os
import secrets
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SaveManager:
    """Manages multiple named world saves"""

    def __init__(self, saves_dir=None):
        if saves_dir is None:
            from config import load_config
            saves_dir = load_config().save_dir
        self.saves_dir = Path(saves_dir)
        self.saves_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.saves_dir / "saves_metadata.json"
        self._lock = threading.Lock()
        self.metadata = self._load_metadata()

    # ------------------------------------------------------------ the index
    def _load_metadata(self) -> Dict:
        """The index on disk. A damaged index is set aside (renamed with a
        .corrupt suffix and logged) rather than stopping the server."""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return {"saves": []}
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            broken = self.metadata_file.with_name(f"saves_metadata.corrupt-{datetime.now():%Y%m%d_%H%M%S}.json")
            os.replace(self.metadata_file, broken)
            logger.error("The save index was damaged (%s); moved it to %s and started a new one", e, broken.name)
            return {"saves": []}
        if not isinstance(data, dict) or not isinstance(data.get("saves"), list):
            return {"saves": []}
        return data

    def _save_metadata(self):
        """Write the index atomically: a temporary file, then a rename."""
        tmp = self.metadata_file.with_name(self.metadata_file.name + f".{os.getpid()}.tmp")
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
        os.replace(tmp, self.metadata_file)

    def _refresh(self):
        self.metadata = self._load_metadata()

    def _entry(self, save_id: str) -> Optional[Dict]:
        return next((s for s in self.metadata["saves"] if s.get("id") == save_id), None)

    # --------------------------------------------------------------- saving
    def create_save(self, save_name: str, world_data: Dict, simulation=None, autosave: bool = False) -> bool:
        """
        Create a new named save

        Args:
            save_name: User-friendly name (e.g., "My First World")
            world_data: Summary of the world (for the list of saves)
            simulation: the running SimulationEngine; if given, its full state
                is saved too, so the save can be loaded and played on
            autosave: made by the server's autosave (kept to AUTOSAVE_KEEP)

        Returns:
            True if save successful
        """
        # Sanitize filename
        safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '-', '_')).strip()[:60]
        if not safe_name:
            safe_name = "world"

        # Unique even for two saves in the same second (ids used to be the
        # time to the second, so two at once shared an id and a file)
        created = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_id = f"{created}_{secrets.token_hex(3)}"
        filename = f"{safe_name}_{save_id}.json.gz"

        with self._lock:
            # Save compressed world data
            with gzip.open(self.saves_dir / filename, 'wt', encoding='utf-8') as f:
                json.dump(world_data, f, indent=2)

            state_filename = None
            if simulation is not None:
                from engine.persistence import save_full_state
                state_filename = f"{safe_name}_{save_id}.state.gz"
                save_full_state(simulation, str(self.saves_dir / state_filename))

            world = world_data.get('world', {}) if isinstance(world_data, dict) else {}
            save_entry = {
                "id": save_id,
                "name": save_name,
                "filename": filename,
                "state_filename": state_filename,
                "created_at": created,
                "last_played": created,
                "autosave": autosave,
                "stats": {
                    "current_day": world.get('time', {}).get('current_day', 0),
                    "population": world.get('total_agents', 0),
                    "alive_agents": world.get('alive_agents', 0),
                    "buildings": len(world_data.get('buildings', {})),
                    "discoveries": len(world_data.get('experiments', {}).get('discoveries', [])),
                },
            }
            self._refresh()
            self.metadata["saves"].append(save_entry)
            self._save_metadata()
        self.last_save_id = save_id
        return True

    def list_saves(self) -> List[Dict]:
        """Get list of all saves with metadata"""
        with self._lock:
            self._refresh()
            return sorted(self.metadata["saves"], key=lambda x: x.get("last_played", ""), reverse=True)

    def load_save(self, save_id: str) -> Optional[Dict]:
        """
        Load a save's summary by ID

        Returns:
            World data dict, or None if not found
        """
        with self._lock:
            self._refresh()
            save_entry = self._entry(save_id)
            if not save_entry:
                return None
            filepath = self.saves_dir / save_entry["filename"]
            if not filepath.exists():
                return None
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                world_data = json.load(f)
            save_entry["last_played"] = datetime.now().strftime('%Y%m%d_%H%M%S')
            self._save_metadata()
        return world_data

    def state_path(self, save_id: str) -> Optional[Path]:
        """The save's full-state file, if it has one (older saves don't)."""
        with self._lock:
            self._refresh()
            save_entry = self._entry(save_id)
        if not save_entry or not save_entry.get("state_filename"):
            return None
        path = self.saves_dir / save_entry["state_filename"]
        return path if path.exists() else None

    def delete_save(self, save_id: str) -> bool:
        """Delete a save and its files. True if it existed."""
        with self._lock:
            self._refresh()
            return self._delete(save_id)

    def _delete(self, save_id: str) -> bool:
        save_entry = self._entry(save_id)
        if not save_entry:
            return False
        for key in ("filename", "state_filename"):
            if save_entry.get(key):
                path = self.saves_dir / save_entry[key]
                if path.exists():
                    path.unlink()
        self.metadata["saves"] = [s for s in self.metadata["saves"] if s.get("id") != save_id]
        self._save_metadata()
        return True

    # ------------------------------------------------------------ autosaves
    @staticmethod
    def _is_autosave(entry: Dict) -> bool:
        # Older autosaves have no flag: the server's were named "autosave...",
        # the dashboard's "AutoSave - Day N ..."
        return bool(entry.get("autosave")) or str(entry.get("name", "")).lower().startswith("autosave")

    def auto_save(self, world_data: Dict, simulation=None, keep: int = 3) -> bool:
        """An autosave of the world, then only the newest `keep` autosaves are kept."""
        day = world_data.get('world', {}).get('time', {}).get('current_day') if isinstance(world_data, dict) else None
        name = f"Autosave day {day}" if day else "Autosave"
        ok = self.create_save(name, world_data, simulation=simulation, autosave=True)
        self.cleanup_old_autosaves(keep_count=keep)
        return ok

    def cleanup_old_autosaves(self, keep_count: int = 3):
        """Keep only the N most recent autosaves"""
        with self._lock:
            self._refresh()
            autosaves = [s for s in self.metadata["saves"] if self._is_autosave(s)]
            autosaves.sort(key=lambda x: (x.get("created_at", ""), x.get("id", "")), reverse=True)
            for save in autosaves[max(0, keep_count):]:
                self._delete(save["id"])
