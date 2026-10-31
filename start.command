#!/bin/bash
set -e

SCRIPT_DIR=$(cd $(dirname $0) && pwd)
cd $SCRIPT_DIR

echo ""
echo "========================================"
echo "   JiangSu Exam Matcher"
echo "========================================"
echo ""

# Step 1: Check Python
echo "[1/4] Check Python..."
if ! command -v python3 &> /dev/null; then
    echo "  FAIL: python3 not found"
    echo "  Please install Python 3.8+ from https://www.python.org/downloads/"
    echo "Press Enter to exit..."
    read
    exit 1
fi
PYVER=$(python3 --version 2>&1)
echo "  OK: $PYVER"
echo ""

# Step 2: Check database
echo "[2/4] Check database..."
if [ -f "backend/jiangsu_exam.db" ]; then
    DBSIZE=$(du -h backend/jiangsu_exam.db | cut -f1)
    echo "  OK: database ready ($DBSIZE)"
else
    echo "  -> Importing from Excel..."
    if [ -f "etl/run_etl.py" ]; then
        python3 etl/run_etl.py
        echo "  OK: database imported"
    else
        echo "  FAIL: ETL script not found"
        echo "Press Enter to exit..."
        read
        exit 1
    fi
fi
echo ""

# Step 3: Install dependencies
echo "[3/4] Check dependencies..."
NEED_INSTALL=false
python3 -c "import flask" 2>/dev/null || NEED_INSTALL=true
python3 -c "import flask_cors" 2>/dev/null || NEED_INSTALL=true
python3 -c "import xlrd" 2>/dev/null || NEED_INSTALL=true
python3 -c "import openpyxl" 2>/dev/null || NEED_INSTALL=true

if [ "$NEED_INSTALL" = false ]; then
    echo "  OK: all dependencies installed"
else
    echo "  -> Installing dependencies..."
    pip3 install -r requirements.txt
    echo "  OK: dependencies installed"
fi
echo ""

# Step 4: Start server
echo "[4/4] Starting server..."
echo ""

# Kill existing process on port 5000
lsof -ti:5000 2>/dev/null | xargs kill -9 2>/dev/null || true

echo "========================================"
echo "  Started! Open: http://localhost:5000"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

# Auto open browser after 2 seconds
(sleep 2 && open "http://localhost:5000") &

python3 backend/app.py
