#!/bin/bash
cd "$(dirname "$0")"
echo "=== 江苏省考岗位智能匹配系统 ==="
# Check if database exists
if [ ! -f backend/jiangsu_exam.db ]; then
    echo "数据库不存在，正在导入数据..."
    python3 etl/run_etl.py
fi
echo "启动服务器: http://localhost:5000"
echo "按 Ctrl+C 停止"
python3 backend/app.py

