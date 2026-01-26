#!/usr/bin/env python3
"""
Neuronaut World - Main Entry Point

Run this to start the world:
    python main.py

Then open http://localhost:8000/app in your browser
"""

import asyncio
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.server import app
import uvicorn

# Configure logging to show DEBUG level for our code
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set our modules to DEBUG level
logging.getLogger('agents.agent').setLevel(logging.DEBUG)
logging.getLogger('engine.simulation').setLevel(logging.INFO)
logging.getLogger('engine.psychology').setLevel(logging.DEBUG)


def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║            🧠  NEURONAUT WORLD  🌍                       ║
    ║                                                           ║
    ║        An Autonomous Virtual World Powered by AI         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

    Starting Neuronaut World...

    📡 API Server: http://localhost:8000
    🌐 Web Interface: http://localhost:8000/app
    📚 API Docs: http://localhost:8000/docs

    The world will start with 50 AI agents who will:
    - Form relationships and groups
    - Trade and build economies
    - Fight, love, and create
    - Evolve their own society

    Press Ctrl+C to stop the world.

    """)

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Neuronaut World stopped by user.")
        print("Thank you for watching!")


if __name__ == "__main__":
    main()
