#!/bin/bash

# Neuronaut World - Game Interface Launcher
# Starts the server and opens the game interface in your browser

echo "🌍 Starting Neuronaut World..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if the API server exists
if [ ! -f "api/server.py" ]; then
    echo "❌ Error: api/server.py not found. Are you in the right directory?"
    echo "   Please run this script from the neuronaut-world root directory"
    exit 1
fi

# Start the server in the background
echo "🚀 Starting FastAPI server..."
python3 api/server.py &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server is running (PID: $SERVER_PID)"
    echo ""
    echo "🎮 Game Interface URLs:"
    echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   🌟 NEW GAME UI:      http://localhost:8000/game"
    echo "   📊 Classic UI:       http://localhost:8000/app/classic"
    echo "   🔧 Enhanced UI:      http://localhost:8000/app"
    echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Opening game in your default browser..."

    # Try to open browser (works on most systems)
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:8000/game" 2>/dev/null
    elif command -v open &> /dev/null; then
        open "http://localhost:8000/game"
    elif command -v start &> /dev/null; then
        start "http://localhost:8000/game"
    else
        echo "⚠️  Could not automatically open browser"
        echo "   Please manually open: http://localhost:8000/game"
    fi

    echo ""
    echo "Press Ctrl+C to stop the server and exit"
    echo ""

    # Wait for user interrupt
    wait $SERVER_PID
else
    echo "❌ Failed to start server"
    exit 1
fi
