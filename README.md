# 江苏省考岗位智能匹配系统

## 简介

本地数据库驱动的江苏省公务员考试岗位匹配系统。导入2027年省考岗位表和2019-2026年历年报考数据，考生输入专业、城市、学历等条件即可筛选可报岗位，并查看对应岗位历年的报名人数、竞争比和进面分数线。

## 功能

- **智能筛选**：按专业（多选+自动补全）、城市（多选）、学历、应届身份、政治面貌、性别、考试类别筛选2027年岗位
- **历年数据**：每个岗位关联展示历年报名人数、竞争比、进面分数线，支持精确匹配和名称匹配两级回退
- **趋势可视化**：ECharts 绘制历年进面分数线趋势图，Y轴自适应范围使趋势更清晰
- **岗位收藏**：本地收藏感兴趣的岗位，随时查看
- **液态玻璃 UI**：全站毛玻璃拟态设计，流光边框、渐变入场动画、丝滑下拉交互

## 使用方法

### 环境要求

- Python 3.8+
- 依赖：Flask, flask-cors, xlrd, openpyxl

### 安装

pip3 install -r requirements.txt

### 启动

数据库已内置，下载后直接运行：

./run.sh

脚本会自动检查并安装依赖、启动服务。

或手动执行：

pip3 install -r requirements.txt    # 安装依赖
python3 backend/app.py              # 启动 Flask 服务

浏览器打开 http://localhost:5000

如需从 Excel 重建数据库：

python3 etl/run_etl.py

## 项目结构

- README.md — 项目说明
- run.sh — 一键启动脚本
- requirements.txt — Python 依赖
- schema.sql — 数据库表结构（DDL）
- data/ — 原始 Excel 数据文件
- etl/run_etl.py — ETL：读取 Excel，清洗数据，写入 SQLite
- backend/app.py — Flask 后端（REST API + 静态文件服务）
- backend/jiangsu_exam.db — SQLite 数据库（已内置30MB，开箱即用）
- static/index.html — 前端 SPA（Vue 3 + Element Plus + ECharts）

## 数据规模

- 2027年岗位：5,725 条
- 历年数据（2019-2026）：51,606 条
- 专业目录：1,804 条
- 岗位-专业关联：106,266 条

## 匹配逻辑

- 专业：精确匹配 + 括号变体匹配（如搜"医学类"也匹配"医学类（不含...）"）
- 学历：按岗位要求学历精确映射（本科对应本科及以上/本科，硕士研究生对应硕士研究生/研究生，等）
- 应届：应届仅限应届岗，非应届排除限应届岗，不限显示全部
- 政治面貌：党员限党员岗，非党员排除限党员岗，不限显示全部
- 历史关联：优先用单位代码+职位代码精确匹配，回退到单位名+职位名匹配

## 技术栈

- 后端：Flask + SQLite（含窗口函数优化的批量历史查询）
- 前端：Vue 3 + Element Plus + ECharts（单文件 SPA）
- 数据处理：Python xlrd + openpyxl（括号感知的专业拆分）

## 性能优化

- 统计查询合并：COUNT + SUM 合为单条 SQL
- 历史数据批量查询：ROW_NUMBER 窗口函数 1 次查询替代 N 次逐行查询
- 分类名缓存：启动时加载到内存，避免每次搜索重复查询
- 复合索引：positions(match_key, year DESC, applicants_count)
- GPU 加速：will-change + backface-visibility 提升动画帧率
