#!/bin/bash

# Setup script for Autonomous AI Agents
# This installs dependencies and helps you get API keys

echo "🧠 AUTONOMOUS AGENT SETUP"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this from the neuronaut-world directory"
    exit 1
fi

echo "📦 Installing Python dependencies..."
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 not found. Please install Python 3 first."
    exit 1
fi

# Install optional LLM dependencies
echo "Installing LLM client libraries (optional)..."
pip3 install groq google-genai python-dotenv --quiet

if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed"
else
    echo "⚠️  Some dependencies failed to install (they're optional)"
fi

echo ""
echo "🖥️  Installing Ollama (local LLM - 100% FREE)..."
echo ""

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama already installed"
else
    echo "Installing Ollama..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo "⚠️  Homebrew not found. Install manually from: https://ollama.com"
        fi
    else
        echo "Install Ollama from: https://ollama.com"
    fi
fi

# Download recommended model
echo ""
echo "⬇️  Downloading recommended model (llama3.2:3b)..."
echo "   This may take a few minutes..."
ollama pull llama3.2:3b 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Model downloaded successfully"
else
    echo "⚠️  Model download failed. You can download it later with: ollama pull llama3.2:3b"
fi

echo ""
echo "📝 Setting up configuration..."
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "   Edit .env to add your API keys (all optional)"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔑 FREE API KEYS (All Optional)"
echo "========================================"
echo ""
echo "Get FREE API keys from these providers:"
echo ""
echo "1. Groq (FASTEST - Recommended)"
echo "   → https://console.groq.com"
echo "   → Free: 30/min, 14,400/day"
echo ""
echo "2. Google Gemini Flash (SMARTEST)"
echo "   → https://makersuite.google.com/app/apikey"
echo "   → Free: 15/min, 1,500/day"
echo ""
echo "3. Hugging Face (MOST GENEROUS)"
echo "   → https://huggingface.co/settings/tokens"
echo "   → Free: 30,000/month"
echo ""
echo "4. Together AI (GOOD FALLBACK)"
echo "   → https://api.together.xyz"
echo "   → Free: \$25 credits (~1M tokens)"
echo ""
echo "Add your keys to the .env file (nano .env)"
echo ""
echo "⚠️  Note: You can skip API keys and just use Ollama (local, unlimited)"
echo ""

echo "✅ SETUP COMPLETE!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. (Optional) Add API keys to .env:"
echo "   nano .env"
echo ""
echo "2. Test the integration:"
echo "   python3 test_autonomous_agents.py"
echo ""
echo "3. Run the simulation:"
echo "   python3 main.py"
echo ""
echo "Documentation: AI_AUTONOMY_INTEGRATION_GUIDE.md"
echo ""
echo "========================================"
