#!/bin/bash

# Neuronaut World - Game Interface Launcher (with venv)
# Activates virtual environment and starts server

echo "🌍 Starting Neuronaut World..."
echo ""

# Check if we're in the right directory
if [ ! -f "api/server.py" ]; then
    echo "❌ Error: api/server.py not found"
    echo "   Please run this script from the neuronaut-world root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  Warning: No virtual environment found"
    echo "   Using system Python..."
fi

# Start the server
echo "🚀 Starting FastAPI server..."
python api/server.py

# Note: This script runs in foreground, so Ctrl+C to stop
