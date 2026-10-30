#!/bin/bash
set -e
REPO="https://github.com/Arch-cy/jiangsu-exam-matcher.git"
DIR="jiangsu-exam-matcher"

echo "=== 江苏省考岗位智能匹配系统 - 一键启动 ==="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi
echo "[1/4] Python3 检查通过"

# 2. Download
if [ -d "$DIR" ]; then
    echo "[2/4] 目录已存在，跳过下载"
else
    echo "[2/4] 正在下载项目..."
    git clone "$REPO" "$DIR"
fi
cd "$DIR"

# 3. Install dependencies
echo "[3/4] 检查依赖..."
if python3 -c "import flask, flask_cors, xlrd, openpyxl" 2>/dev/null; then
    echo "      依赖已安装，跳过"
else
    pip3 install -r requirements.txt
fi

# 4. Start server
if [ ! -f backend/jiangsu_exam.db ]; then
    echo "[4/4] 数据库不存在，正在导入..."
    python3 etl/run_etl.py
fi

echo ""
echo "=== 启动成功 ==="
echo "浏览器打开: http://localhost:5000"
echo "按 Ctrl+C 停止"
echo ""
python3 backend/app.py
