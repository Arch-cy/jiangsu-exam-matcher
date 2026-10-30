-- ============================================================
-- 江苏省考岗位智能匹配系统 - 数据库 Schema
-- ============================================================
-- 使用方法：
--   方式1（推荐）：直接使用 backend/jiangsu_exam.db（已含全部数据）
--   方式2：从零构建 -> python3 etl/run_etl.py（需先放入数据文件）
-- ============================================================

-- 岗位主表（2027年岗位 + 2019-2026年历史数据）
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,              -- 年份：2027 或 2019-2026
    affiliation TEXT,                   -- 隶属关系
    region_code TEXT,                   -- 地区代码
    region_name TEXT,                   -- 地区名称
    unit_code TEXT,                     -- 单位代码
    unit_name TEXT,                     -- 单位名称
    position_code TEXT,                 -- 职位代码
    position_name TEXT,                 -- 职位名称
    position_desc TEXT,                 -- 职位描述
    exam_category TEXT,                 -- 考试类别
    open_ratio TEXT,                    -- 开考比例
    recruit_count INTEGER,             -- 招考人数
    education_req TEXT,                 -- 学历要求
    major_req TEXT,                     -- 专业要求（原始文本）
    other_req TEXT,                     -- 其他要求
    source_sheet TEXT,                  -- 数据来源工作表
    applicants_count INTEGER,           -- 报名人数（仅历史数据）
    score_max REAL,                     -- 进面最高分（仅历史数据）
    score_min REAL,                     -- 进面最低分（仅历史数据）
    city TEXT,                          -- 城市（标准化）
    match_key TEXT,                     -- 匹配键：单位代码-职位代码
    requires_fresh BOOLEAN DEFAULT 0,   -- 是否限应届
    requires_party BOOLEAN DEFAULT 0,   -- 是否限党员
    requires_male BOOLEAN DEFAULT 0,    -- 是否限男性
    requires_female BOOLEAN DEFAULT 0,  -- 是否限女性
    requires_degree BOOLEAN DEFAULT 0,  -- 是否需学位
    requires_work_exp BOOLEAN DEFAULT 0,-- 是否需基层工作经历
    requires_legal_cert BOOLEAN DEFAULT 0 -- 是否需法律职业资格
);

CREATE INDEX idx_year ON positions(year);
CREATE INDEX idx_city ON positions(city);
CREATE INDEX idx_mk ON positions(match_key);
CREATE INDEX idx_edu ON positions(education_req);
CREATE INDEX idx_un ON positions(unit_name);
CREATE INDEX idx_mk_year_app ON positions(match_key, year DESC, applicants_count);

-- 专业目录表
CREATE TABLE major_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major_name TEXT NOT NULL,           -- 专业名称
    major_category TEXT,                -- 所属类别（仅类别行有值）
    is_category BOOLEAN DEFAULT 0,      -- 是否为专业类别（如"计算机类"）
    UNIQUE(major_name)
);

-- 岗位-专业关联表
CREATE TABLE position_majors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,       -- 关联 positions.id
    major_name TEXT NOT NULL,           -- 专业名称（已拆分，括号内容完整保留）
    is_category BOOLEAN DEFAULT 0,      -- 是否为类别
    FOREIGN KEY (position_id) REFERENCES positions(id)
);

CREATE INDEX idx_pm_major ON position_majors(major_name);
CREATE INDEX idx_pm_pos ON position_majors(position_id);

-- 收藏表
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,
    note TEXT,
    created_at TEXT,
    FOREIGN KEY (position_id) REFERENCES positions(id)
);
