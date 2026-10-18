@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM  ImpactGraph (ORACLE) - Windows Runner Script
REM  Operational Reasoning & Causal Analysis through Linked Evidence (FalkorDB)
REM ============================================================================

cd /d "%~dp0"
title ImpactGraph - ORACLE Cockpit

if "%1"=="help" goto :help
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help
if "%1"=="test" goto :run_tests
if "%1"=="seed" goto :run_seed
if "%1"=="build" goto :build_frontend
if "%1"=="dev" goto :run_dev

:main_start
echo.
echo  ==========================================================================
echo    ___  ____     _    ____ _     _____ 
echo   / _ \|  _ \   / \  / ___| |   | ____|
echo  ^| ^| ^| ^| ^|_) ^| / _ \^| ^|   ^| ^|   ^|  _^|  
echo  ^| ^|_^| ^|  _ ^< / ___ \ ^|___^| ^|___^| ^|___ 
echo   \___/^|_^| \_/_/   \_\\____^|_____^|_____^|
echo.
echo   ImpactGraph: Operational Reasoning ^& Causal Analysis (FalkorDB Track 01)
echo  ==========================================================================
echo.

REM --- Step 1: Check Python ---
echo [1/6] Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

REM --- Step 2: Virtual Environment ---
echo [2/6] Checking Python virtual environment...
if not exist ".venv\Scripts\activate.bat" (
    echo   - Creating virtual environment in .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    echo   - Installing Python dependencies from requirements.txt...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM --- Step 3: Environment Configuration (.env) ---
echo [3/6] Checking configuration (.env)...
if not exist ".env" (
    echo   - Creating .env from .env.example...
    copy .env.example .env >nul
)

REM --- Step 4: Docker & FalkorDB ---
echo [4/6] Checking FalkorDB container...
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Docker is not detected in PATH.
    echo Ensure FalkorDB is running at localhost:6379 before continuing.
) else (
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] Docker daemon is not running. Please launch Docker Desktop.
    ) else (
        REM Check if container is running
        for /f "tokens=*" %%i in ('docker ps -q --filter "name=falkordb"') do set FALKOR_RUNNING=%%i
        if not "!FALKOR_RUNNING!"=="" (
            echo   - FalkorDB container is running.
        ) else (
            REM Check if stopped container exists
            for /f "tokens=*" %%i in ('docker ps -aq --filter "name=falkordb"') do set FALKOR_EXISTS=%%i
            if not "!FALKOR_EXISTS!"=="" (
                echo   - Starting existing FalkorDB container...
                docker start falkordb >nul
            ) else (
                echo   - Launching new FalkorDB container on ports 6379 and 3000...
                docker run -d --name falkordb --restart unless-stopped -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
            )
        )
    )
)

REM --- Step 5: Verify Frontend Build ---
echo [5/6] Checking frontend build...
if not exist "frontend\dist\index.html" (
    echo   - frontend\dist not found. Checking Node.js to build UI...
    where npm >nul 2>&1
    if %errorlevel% equ 0 (
        echo   - Installing frontend dependencies and compiling Vite build...
        cd frontend
        call npm install
        call npm run build
        cd ..
    ) else (
        echo   - Node.js not detected. Fallback embedded HTML dashboard will be served.
    )
) else (
    echo   - Production frontend build verified.
)

REM --- Step 6: Seed FalkorDB Graph ---
echo [6/6] Seeding FalkorDB graph data...
python -m oracle.seed_data
if %errorlevel% neq 0 (
    echo [WARNING] Seeding returned an error. Check if FalkorDB is reachable on localhost:6379.
)

echo.
echo  ==========================================================================
echo   ORACLE Cockpit Ready!
echo   * Web Application:  http://localhost:8000
echo   * FalkorDB Browser: http://localhost:3000
echo   * Acceptance Tests: run.bat test
echo  ==========================================================================
echo.

REM Automatically open browser
start "" "http://localhost:8000"

REM Launch FastAPI / Uvicorn server
echo Starting Uvicorn server on http://0.0.0.0:8000 (Press Ctrl+C to stop)...
uvicorn oracle.api:app --host 0.0.0.0 --port 8000 --reload
goto :eof

:run_tests
echo [TESTS] Running acceptance test suite...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)
pytest -v
goto :eof

:run_seed
echo [SEED] Resetting and seeding synthetic graph data in FalkorDB...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)
python -m oracle.seed_data
goto :eof

:build_frontend
echo [BUILD] Building frontend Vite bundle...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is required to build the frontend!
    exit /b 1
)
cd frontend
call npm install
call npm run build
cd ..
echo [BUILD] Frontend successfully compiled to frontend\dist!
goto :eof

:run_dev
echo [DEV] Launching FastAPI backend and Vite HMR dev server...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)
start "FastAPI Backend" cmd /k "uvicorn oracle.api:app --host 0.0.0.0 --port 8000 --reload"
cd frontend
start "Vite Dev Server" cmd /k "npm run dev"
cd ..
start "" "http://localhost:5173"
goto :eof

:help
echo.
echo ImpactGraph (ORACLE) Runner Commands:
echo   run.bat          - Setup dependencies, verify FalkorDB, seed graph, start server
echo   run.bat test     - Run pytest acceptance test suite (18/18 tests)
echo   run.bat seed     - Seed synthetic incident graph in FalkorDB
echo   run.bat build    - Build production React UI with Vite
echo   run.bat dev      - Start both FastAPI backend and Vite dev server in parallel
echo   run.bat help     - Display this help message
echo.
goto :eof
