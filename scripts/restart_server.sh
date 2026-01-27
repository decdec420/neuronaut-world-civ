#!/bin/bash

echo "🔄 Restarting Neuronaut World Server..."
echo ""

# Kill any running Python server
echo "🛑 Stopping old server..."
pkill -f "python.*api/server.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 2

# Check if anything is using port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 still in use, force killing..."
    kill -9 $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null || true
    sleep 1
fi

echo "✅ Old server stopped"
echo ""

# Start new server
echo "🚀 Starting new server..."
./start_game.sh
