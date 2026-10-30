#!/bin/bash
cd "$(dirname "$0")"
echo "=== 江苏省考岗位智能匹配系统 ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
    echo ""
fi

# Check if database exists
if [ ! -f backend/jiangsu_exam.db ]; then
    echo "数据库不存在，正在从 Excel 导入数据..."
    python3 etl/run_etl.py
    echo ""
fi

echo "启动服务器: http://localhost:5000"
echo "按 Ctrl+C 停止"
echo ""
python3 backend/app.py
