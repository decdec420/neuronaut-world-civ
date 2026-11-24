#!/usr/bin/env python3
"""
Neuronaut World - Main Entry Point

Run this to start the world:
    python main.py

Then open http://localhost:8000/app in your browser
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info < (3, 9):
    sys.exit(f"Neuronaut World needs Python 3.9 or newer; this is Python {sys.version.split()[0]}.")
try:
    import fastapi, uvicorn, pydantic, slowapi  # noqa: F401  (what the server needs)
except ModuleNotFoundError as missing:
    sys.exit(f"The package '{missing.name}' isn't installed for this Python ({sys.executable}).\n"
             f"Install what the world needs with:\n\n"
             f"    {os.path.basename(sys.executable)} -m pip install -r requirements-minimal.txt\n")

from config import load_config
from api.server import app


def configure_logging(level: str) -> None:
    """One format for everything at LOG_LEVEL (default INFO). This used to
    force DEBUG on agents.agent and engine.psychology, which wrote a line for
    every need an agent satisfied: ~1.5 KB a tick, ~130 MB a day of logs."""
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(name)s: %(message)s', force=True)


def main():
    """Main entry point"""
    cfg = load_config()
    if cfg.world_seed is not None and "PYTHONHASHSEED" not in os.environ:
        # A seeded world must also walk its sets in the same order every run
        os.environ["PYTHONHASHSEED"] = "0"
        os.execv(sys.executable, [sys.executable] + sys.argv)
    configure_logging(cfg.log_level)
    log = logging.getLogger("neuronaut")
    url = f"http://{'localhost' if cfg.host in ('127.0.0.1', '0.0.0.0', '::') else cfg.host}:{cfg.port}"
    print(f"""
    🧠  NEURONAUT WORLD  🌍

    {cfg.num_agents} agents with needs, memories and personalities, in a world they run.

    🌐 Watch:    {url}/app
    📚 API docs: {url}/docs
    ❤️  Health:   {url}/health

    Press Ctrl+C to stop.
    """)
    loopback = cfg.host in ('127.0.0.1', 'localhost', '::1')
    if not loopback and not os.getenv('NEURONAUT_ADMIN_TOKEN', '').strip():
        log.warning("Serving on %s with no NEURONAUT_ADMIN_TOKEN: anyone who can reach this "
                    "port can pause, reset or reload the world. Set a token.", cfg.host)

    try:
        uvicorn.run(app, host=cfg.host, port=cfg.port, log_level=cfg.log_level.lower())
    except KeyboardInterrupt:
        print("\n🛑 Neuronaut World stopped.")


if __name__ == "__main__":
    main()
