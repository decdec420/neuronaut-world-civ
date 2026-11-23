# 🚀 How to Run Neuronaut World in VS Code

## **Quick Start (3 Ways)**

### **Option 1: Press F5 (Recommended)**
1. Open this folder in VS Code
2. Press **F5** (or click "Run and Debug" → "🌍 Neuronaut World")
3. That's it! The simulation will start in the integrated terminal

### **Option 2: Use Terminal**
```bash
source venv/bin/activate
python3 main.py
```

### **Option 3: Build Task**
1. Press **Cmd+Shift+B** (Mac) or **Ctrl+Shift+B** (Windows/Linux)
2. Select "🚀 Run Neuronaut World"

## **Accessing the Simulation**

Once running, open your browser:
- **Web UI:** http://localhost:8000/app
- **API Docs:** http://localhost:8000/docs
- **API Stats:** http://localhost:8000/stats

## **Stopping the Simulation**

- Press **Ctrl+C** in the terminal
- Or use VS Code task: **Cmd+Shift+P** → "Run Task" → "🛑 Stop Neuronaut World"

## **What's Running**

This is a **Python FastAPI application** - NOT a Node.js project!
- No `npm run dev` needed
- No build steps
- Just pure Python + FastAPI
- The web UI is static HTML/CSS/JS served by FastAPI

## **Virtual Environment**

The `venv` is already set up with all dependencies:
- fastapi
- uvicorn
- websockets
- pydantic

If you need to reinstall:
```bash
pip3 install -r requirements-minimal.txt
```

## **All New Autonomous Systems Are Live!**

✅ Experimentation Engine (discover anything!)
✅ Dynamic Buildings (design anything!)
✅ Knowledge System (libraries, teaching, writing)
✅ Consequences (real death, explosions, collapse)
✅ Emergent Roles (behavior → identity)
✅ Tech Progression (Stone Age → Space Age)
✅ Persistence (save/resume for continuous runs)

**Watch civilization emerge from NOTHING!** 🌍🚀
