-- ============================================================
-- 主题扩展管道：发现候选表 + 发现提案表 + 价值评分快照表
--
-- 小白讲解：这 3 张表是 SPEC 2 自我发现管道的核心存储。
-- discovery_candidate：所有新发现的标的先进这里（"候选区"）
-- discovery_proposal：通过 VFM 评分后晋升到这里（"提案区"）
-- value_score_snapshot：每次评分的历史记录（"成绩单"）
-- ============================================================

-- 自主发现候选表（发现管线产出，不一定会入池）
CREATE TABLE IF NOT EXISTS discovery_candidate (
    ticker TEXT NOT NULL,                          -- 股票代码，如 300308.SZ
    name TEXT,                                     -- 股票名称
    market TEXT,                                   -- A / H / US
    sector TEXT,                                   -- 主题 key，如 semiconductor_compute
    discovery_method TEXT NOT NULL,                -- theme_extension / supply_chain / us_benchmark / manual
    hit_methods INTEGER DEFAULT 1,                 -- 被多少个发现方法命中（越高越可信）
    discovery_date TEXT NOT NULL,                  -- 发现日期 YYYY-MM-DD
    raw_source TEXT,                               -- 来源信息（如"概念板块：光模块"）
    added_at TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE(ticker, discovery_method, discovery_date)
);

-- 发现提案表（通过 VFM 评分后提案，等待人工批准）
CREATE TABLE IF NOT EXISTS discovery_proposal (
    proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    name TEXT,
    market TEXT,
    sector TEXT,
    composite_score REAL,                          -- VFM composite_score
    score_card_json TEXT,                          -- 完整评分卡 JSON
    discovery_evidence_json TEXT,                  -- 发现方法与证据摘要
    status TEXT DEFAULT 'pending_approval',        -- pending_approval / approved / rejected
    approved_by TEXT,                              -- 人工批准人/脚本标识
    approved_at TEXT,
    reason TEXT,                                   -- 批准/拒绝理由
    created_at TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE(ticker)
);

-- 价值评分快照表（每次 VFM 评分的历史记录，用于追踪变化）
CREATE TABLE IF NOT EXISTS value_score_snapshot (
    ticker TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,                   -- YYYY-MM-DD
    fundamental_quality REAL,
    valuation_position REAL,
    technical_momentum REAL,
    theme_relevance REAL,
    industry_position REAL,
    composite_score REAL,
    red_flags_json TEXT,                           -- 警示信号清单（JSON 数组）
    score_detail_json TEXT,                        -- 完整评分细节
    created_at TEXT DEFAULT (datetime('now','localtime')),
    PRIMARY KEY(ticker, snapshot_date)
);
