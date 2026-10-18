#!/usr/bin/env bash
set -eo pipefail

# ==============================================================================
#  ImpactGraph (ORACLE) - All-in-One Runner Script
#  Operational Reasoning & Causal Analysis through Linked Evidence (FalkorDB)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMMAND="${1:-all}"

case "$COMMAND" in
    help|--help|-h)
        echo ""
        echo "ImpactGraph (ORACLE) Runner Commands:"
        echo "  ./run.sh          - Run all services at once (FalkorDB + Seed + Backend + Frontend)"
        echo "  ./run.sh api      - Run FastAPI backend only (serves UI at port 8000)"
        echo "  ./run.sh test     - Run pytest acceptance test suite (18/18 tests)"
        echo "  ./run.sh seed     - Reset & seed synthetic incident graph in FalkorDB"
        echo "  ./run.sh build    - Build production React UI with Vite"
        echo "  ./run.sh help     - Display this help message"
        echo ""
        exit 0
        ;;
    test)
        echo "[TESTS] Running acceptance test suite..."
        [ -f ".venv/bin/activate" ] && source .venv/bin/activate
        pytest -v
        exit 0
        ;;
    seed)
        echo "[SEED] Resetting and seeding synthetic graph data in FalkorDB..."
        [ -f ".venv/bin/activate" ] && source .venv/bin/activate
        python3 -m oracle.seed_data
        exit 0
        ;;
    build)
        echo "[BUILD] Building frontend Vite bundle..."
        cd frontend
        npm install
        npm run build
        cd ..
        echo "[BUILD] Frontend successfully compiled to frontend/dist!"
        exit 0
        ;;
    api)
        echo "[API] Starting FastAPI backend only..."
        [ -f ".venv/bin/activate" ] && source .venv/bin/activate
        exec uvicorn oracle.api:app --host 0.0.0.0 --port 8000 --reload
        ;;
    all|"")
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run './run.sh help' for usage instructions."
        exit 1
        ;;
esac

echo ""
echo " =========================================================================="
echo "   ___  ____     _    ____ _     _____ "
echo "  / _ \|  _ \   / \  / ___| |   | ____|"
echo " | | | | |_) | / _ \| |   | |   |  _|  "
echo " | |_| |  _ < / ___ \ |___| |___| |___ "
echo "  \___/|_| \_/_/   \_\____|_____|_____|"
echo ""
echo "  ImpactGraph: Operational Reasoning & Causal Analysis (FalkorDB Track 01)"
echo " =========================================================================="
echo ""

# Step 1: Check Python
echo "[1/6] Checking Python installation..."
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not found in PATH! Please install Python 3.10+."
    exit 1
fi

# Step 2: Virtual Environment
echo "[2/6] Checking Python virtual environment..."
if [ ! -f ".venv/bin/activate" ]; then
    echo "  - Creating virtual environment in .venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "  - Installing Python dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Step 3: Check .env
echo "[3/6] Checking configuration (.env)..."
if [ ! -f ".env" ]; then
    echo "  - Creating .env from .env.example..."
    cp .env.example .env
fi

# Step 4: Docker & FalkorDB
echo "[4/6] Checking FalkorDB container..."
if ! command -v docker &>/dev/null; then
    echo "[WARNING] Docker is not detected in PATH. Ensure FalkorDB is running on localhost:6379."
else
    if ! docker info &>/dev/null; then
        echo "[WARNING] Docker daemon is not running. Please start Docker."
    else
        if docker ps -q --filter "name=falkordb" | grep -q .; then
            echo "  - FalkorDB container is running."
        elif docker ps -aq --filter "name=falkordb" | grep -q .; then
            echo "  - Starting existing FalkorDB container..."
            docker start falkordb >/dev/null
        else
            echo "  - Launching new FalkorDB container on ports 6379 and 3000..."
            docker run -d --name falkordb --restart unless-stopped -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
        fi
    fi
fi

# Step 5: Check Frontend Build
echo "[5/6] Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "  - Installing frontend dependencies..."
    (cd frontend && npm install)
fi

if [ ! -f "frontend/dist/index.html" ]; then
    echo "  - Compiling initial frontend build..."
    (cd frontend && npm run build)
fi

# Step 6: Seed Database
echo "[6/6] Seeding FalkorDB graph data..."
python3 -m oracle.seed_data || echo "[WARNING] Seeding returned an error. Check FalkorDB at localhost:6379."

echo ""
echo " =========================================================================="
echo "  ORACLE Stack Starting (All services running at once)!"
echo ""
echo "  * Web Application (Vite HMR): http://localhost:5173"
echo "  * FastAPI Backend & API Docs: http://localhost:8000"
echo "  * FalkorDB Browser UI:        http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop all services."
echo " =========================================================================="
echo ""

# Cleanup trap to kill background processes on Ctrl+C or script exit
cleanup() {
    echo ""
    echo "Shutting down all services..."
    trap - SIGINT SIGTERM EXIT
    kill $(jobs -p) 2>/dev/null || true
    wait 2>/dev/null || true
    echo "All services stopped."
}
trap cleanup SIGINT SIGTERM EXIT

# Start FastAPI backend in background
uvicorn oracle.api:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start Vite frontend dev server in background
(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Try opening the web app in user's browser if available
sleep 1
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:5173" 2>/dev/null &
elif command -v open &>/dev/null; then
    open "http://localhost:5173" 2>/dev/null &
fi

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
