#!/usr/bin/env python3
"""Write SMR development plan to Documents directory."""

import os

TARGET = "/Users/apple/Documents/同行-trae开发/SMR-二级市场业务线开发计划.md"

CONTENT = r"""# SMR — 同行资本二级市场业务线开发计划

> 版本：v1.0 | 日期：2026-04-09 | 作者：Trae IDE
> 状态：规划中，待用户确认

---

## 一、项目定位

### 1.1 业务线全称

**SMR（Secondary Market Research）— 二级市场研究、跟踪、股票推荐与持仓管理**

### 1.2 与现有业务线的关系

| 业务线 | 代号 | 核心产出 | 运行平台 |
|--------|------|----------|----------|
| 虚拟VC投研 | VCR | Project Card、Top-down报告 | OpenClaw |
| 市场内容 | MCT | 多平台适配文章、微信公众号 | OpenClaw |
| **二级市场研究** | **SMR** | **研报、股票池、持仓管理、风控信号** | **OpenClaw + 独立Python服务** |

### 1.3 核心原则

1. **零侵入**：不修改任何现有 agent（VCR 6个 + MCT 8个 = 14个），不动现有 cron job、workspace、session
2. **完全隔离**：独立目录、独立 agent 体系、独立 session、独立 memory、独立 cron
3. **OpenClaw优先**：能用 OpenClaw 跑的尽量用 OpenClaw，不适合的用独立 Python 服务
4. **合规先行**：所有推荐类产出必须附带免责声明和风险提示

---

## 二、业务需求拆解

### 2.1 功能模块

| 模块 | 功能描述 | 适合OpenClaw | 备注 |
|------|----------|:---:|------|
| 市场研究 | 行业/板块/个股深度研究，产出研报 | ✅ | Agent驱动，类似VCR的top-down |
| 舆情跟踪 | 新闻/公告/社交媒体实时监控 | ⚠️ | 数据采集需Python，分析可Agent |
| 股票筛选 | 多因子筛选、量化打分 | ❌ | 需要大量数值计算，Python服务 |
| 股票推荐 | 基于筛选结果+研究结论的推荐 | ✅ | Agent综合判断+模板输出 |
| 持仓管理 | 持仓记录、盈亏跟踪、调仓建议 | ⚠️ | 数据存储Python，建议可Agent |
| 风险监控 | 回撤预警、仓位风控、黑天鹅检测 | ❌ | 实时计算，Python服务 |
| 日报/周报 | 市场复盘、持仓总结、操作建议 | ✅ | Agent驱动，类似MCT的晨间线 |
| 微信推送 | 研究结论/推荐/预警推送到微信 | ✅ | 复用MCT的微信桥接架构（独立实例） |

### 2.2 "OpenClaw做大脑，Python做手脚"架构

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw 层（大脑）                     │
│                                                         │
│  smr-lead ──► smr-researcher ──► smr-analyst           │
│      │              │                  │                 │
│      ▼              ▼                  ▼                 │
│  smr-brief-writer  smr-advisor    smr-portfolio-mgr     │
│      │              │                  │                 │
│      └──────────────┼──────────────────┘                 │
│                     ▼                                    │
│              smr-risk-controller                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                  独立 Python 服务层（手脚）                │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 数据采集  │  │ 因子计算  │  │ 风控引擎  │              │
│  │ Service  │  │ Service  │  │ Service  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│       │              │              │                    │
│       ▼              ▼              ▼                    │
│  ┌──────────────────────────────────────┐               │
│  │         SMR SQLite 数据库             │               │
│  │  (行情/因子/持仓/信号/研报索引)        │               │
│  └──────────────────────────────────────┘               │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   数据源层                                │
│                                                         │
│  AkShare(免费) / Tushare(需积分) / 东方财富 / 同花顺      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**分工原则：**
- **OpenClaw Agent**：研究分析、判断决策、内容生成、推送调度 — 需要"思考"的工作
- **Python 服务**：数据采集、因子计算、回测验证、风控监控 — 需要"计算"的工作
- **交互方式**：Agent 通过读写共享文件系统（SQLite + Markdown）与 Python 服务交互，不走网络API

---

## 三、隔离方案

### 3.1 目录隔离

```
/Users/apple/Documents/同行资本二级市场/          ← SMR独立根目录
├── 00_control/                    # 控制中心（调度面板、优先级）
├── 01_data/                       # 数据层
│   ├── db/                        #   SQLite数据库
│   │   └── smr.db                 #     主数据库（行情/因子/持仓/信号）
│   ├── raw/                       #   原始数据缓存（按日期）
│   └── factor/                    #   因子计算结果
├── 02_research/                   # 研究产出
│   ├── industry/                  #   行业研究
│   ├── sector/                    #   板块研究
│   └── stock/                     #   个股研究
├── 03_stock_pool/                 # 股票池
│   ├── watchlist/                 #   观察池
│   ├── candidate/                 #   候选池
│   └── recommended/               #   推荐池
├── 04_portfolio/                  # 持仓管理
│   ├── positions/                 #   持仓记录
│   ├── trades/                    #   交易记录
│   └── performance/               #   绩效分析
├── 05_risk/                       # 风控
│   ├── alerts/                    #   预警记录
│   ├── rules/                     #   风控规则
│   └── logs/                      #   风控日志
├── 06_reports/                    # 报告产出
│   ├── daily/                     #   日报
│   ├── weekly/                    #   周报
│   └── adhoc/                     #   临时报告
├── 07_publish/                    # 发布队列（独立于MCT）
│   ├── queue/                     #   待发布
│   └── archive/                   #   已发布
├── 08_scripts/                    # Python脚本
│   ├── data_harvester/            #   数据采集
│   ├── factor_engine/             #   因子计算
│   ├── risk_engine/               #   风控引擎
│   └── backtest/                  #   回测框架
├── 09_runbooks/                   # Runbook（独立于MCT）
│   ├── scripts/                   #   Python执行脚本
│   ├── skills/                    #   Skill定义
│   └── templates/                 #   模板
└── 10_logs/                       # 运行日志
```

### 3.2 Agent 隔离

SMR 的所有 agent 使用 `smr-` 前缀，与现有 agent 零重叠：

| 现有Agent | SMR Agent | 隔离维度 |
|-----------|-----------|----------|
| lead, knowledge-curator, ... | smr-lead, smr-researcher, ... | ID前缀不同 |
| workspace-lead, workspace-kc, ... | workspace-smr-lead, ... | 目录完全独立 |
| agents/lead/, agents/kc/, ... | agents/smr-lead/, ... | 运行时数据独立 |
| memory/lead.sqlite, ... | memory/smr-lead.sqlite, ... | 向量记忆独立 |
| cron job: agentId=lead, ... | cron job: agentId=smr-lead, ... | 调度独立 |

**关键隔离规则：**
- SMR agent 不加入现有 `tools.agentToAgent.allow` 列表（VCR/MCT agent 无法直接与 SMR agent 通信）
- SMR agent 不绑定现有飞书 bot 账号（如需飞书推送，创建独立 bot）
- SMR 的 cron job 使用独立的 `sessionTarget: "isolated"`，不污染现有 session

### 3.3 Session 隔离

- 每个 SMR agent 有独立的 `agents/smr-{id}/sessions/sessions.json`
- SMR 的 cron session key 格式：`agent:smr-{id}:cron:{uuid}`
- SMR agent 之间通过**共享文件系统**（`/Users/apple/Documents/同行资本二级市场/`）交接，不走 agent-to-agent 消息

### 3.4 Memory 隔离

- 每个 SMR agent 有独立的 `memory/smr-{id}.sqlite`（向量记忆）
- 每个 SMR agent 有独立的 `workspace-smr-{id}/memory/`（文件记忆）
- SMR agent 的 `MEMORY.md` 仅在 SMR 内部 session 加载

### 3.5 Cron 隔离

- SMR 的 cron job 写入同一个 `cron/jobs.json`（OpenClaw 只有一个 cron 文件）
- 但 `agentId` 全部使用 `smr-` 前缀，确保路由到 SMR agent
- SMR cron job 的 `name` 统一使用 `SMR-` 前缀，便于识别和过滤

---

## 四、Agent 体系设计

### 4.1 Agent 清单

| ID | 角色 | 职责 | 心跳 | 模型 |
|----|------|------|------|------|
| smr-lead | SMR参谋长 | 调度、优先级管理、跨模块协调 | 3h | MiniMax-M2.7 |
| smr-researcher | 行业研究员 | 行业/板块/个股深度研究，产出研报 | 3h | MiniMax-M2.7 |
| smr-analyst | 量化分析师 | 因子分析、选股模型、回测验证 | 3h | MiniMax-M2.7 |
| smr-advisor | 投资顾问 | 综合研究+量化结论，产出推荐 | 3h | MiniMax-M2.7 |
| smr-portfolio-mgr | 持仓经理 | 持仓记录、盈亏跟踪、调仓建议 | 3h | MiniMax-M2.7 |
| smr-risk-controller | 风控官 | 风险监控、预警触发、仓位控制 | 1h | MiniMax-M2.7 |
| smr-brief-writer | 简报撰写 | 日报/周报/临时报告撰写与推送 | 3h | MiniMax-M2.7 |

### 4.2 协作拓扑

```
smr-lead（调度中心）
    │
    ├──► smr-researcher ──产出──► 研报 → 02_research/
    │                                    │
    ├──► smr-analyst ──产出──► 因子报告 → 01_data/factor/
    │                                    │
    │         ┌──────────────────────────┘
    │         ▼
    ├──► smr-advisor ◄──研报+因子── 产出推荐 → 03_stock_pool/
    │         │
    │         ▼
    ├──► smr-portfolio-mgr ◄──推荐── 产出调仓建议 → 04_portfolio/
    │         │
    │         ▼
    ├──► smr-risk-controller ◄──持仓── 产出预警 → 05_risk/
    │
    └──► smr-brief-writer ◄──全量数据── 产出报告 → 06_reports/
```

### 4.3 Agent Workspace 结构

每个 SMR agent 的 workspace 遵循 OpenClaw 标准结构：

```
workspace-smr-{id}/
├── AGENTS.md          # 行为规范（启动读取顺序）
├── SOUL.md            # 人格定义
├── IDENTITY.md        # 身份信息
├── USER.md            # 用户信息
├── MEMORY.md          # 长期记忆
├── HEARTBEAT.md       # 心跳任务
├── TOOLS.md           # 工具笔记
├── prompt-pack/       # prompt覆盖包
│   ├── AGENTS.md
│   └── TOOLS.md
├── memory/            # 记忆目录
│   ├── 00_longterm.md
│   ├── 01_midterm.md
│   ├── 02_shortterm.md
│   └── YYYY-MM-DD.md
└── skills/            # 专属技能
```

### 4.4 openclaw.json 配置变更

**仅新增，不修改现有配置：**

```json
{
  "agents": {
    "list": [
      // === 现有14个agent保持不变 ===

      // === SMR 新增7个agent ===
      {
        "id": "smr-lead",
        "workspace": "/Users/apple/.openclaw/workspace-smr-lead",
        "heartbeat": { "every": "3h" },
        "groupChat": { "mentionPatterns": ["@smr-lead", "@二级市场"] }
      },
      {
        "id": "smr-researcher",
        "workspace": "/Users/apple/.openclaw/workspace-smr-researcher",
        "heartbeat": { "every": "3h" }
      },
      {
        "id": "smr-analyst",
        "workspace": "/Users/apple/.openclaw/workspace-smr-analyst",
        "heartbeat": { "every": "3h" }
      },
      {
        "id": "smr-advisor",
        "workspace": "/Users/apple/.openclaw/workspace-smr-advisor",
        "heartbeat": { "every": "3h" }
      },
      {
        "id": "smr-portfolio-mgr",
        "workspace": "/Users/apple/.openclaw/workspace-smr-portfolio-mgr",
        "heartbeat": { "every": "3h" }
      },
      {
        "id": "smr-risk-controller",
        "workspace": "/Users/apple/.openclaw/workspace-smr-risk-controller",
        "heartbeat": { "every": "1h" }
      },
      {
        "id": "smr-brief-writer",
        "workspace": "/Users/apple/.openclaw/workspace-smr-brief-writer",
        "heartbeat": { "every": "3h" }
      }
    ]
  },
  "tools": {
    "agentToAgent": {
      "enabled": true,
      "allow": [
        // === 现有列表保持不变 ===
        "lead", "knowledge-curator", "thesis-architect",
        "opportunity-scout", "signal-harvester", "market-editor",
        "market-scout", "topic-planner", "content-writer",
        "redteam-reviewer", "publish-ops", "content-analyst",
        // === SMR 内部通信（不与现有agent互通）===
        "smr-lead", "smr-researcher", "smr-analyst",
        "smr-advisor", "smr-portfolio-mgr", "smr-risk-controller",
        "smr-brief-writer"
      ]
    }
  }
}
```

**注意**：SMR agent 的 `agentToAgent.allow` 列表只包含 SMR 内部的 7 个 agent，不包含 VCR/MCT 的 agent。这意味着 SMR agent 之间可以互相通信，但不能与现有 agent 直接通信，实现完全隔离。

---

## 五、数据层设计

### 5.1 数据源选型

| 数据源 | 类型 | 覆盖范围 | 成本 | 推荐用途 |
|--------|------|----------|------|----------|
| **AkShare** | Python库 | A股行情/财务/宏观数据 | 免费 | 主力数据源 |
| **Tushare** | Python库 | A股全量数据 | 需积分(免费注册) | 补充数据源 |
| **东方财富** | 网页爬取 | 实时行情/资金流 | 免费 | 实时数据 |
| **同花顺iFinD** | API | 全市场数据 | 付费 | 备选（后期） |

**推荐方案**：以 AkShare 为主、Tushare 为辅，零成本启动。

### 5.2 数据库设计（SQLite）

```sql
-- 日线行情
CREATE TABLE daily_bar (
    ts_code    TEXT NOT NULL,       -- 股票代码 如 000001.SZ
    trade_date TEXT NOT NULL,       -- 交易日期 YYYY-MM-DD
    open       REAL, close         REAL,
    high       REAL, low           REAL,
    vol        REAL, amount        REAL,
    pct_chg    REAL,               -- 涨跌幅%
    turnover   REAL,               -- 换手率%
    PRIMARY KEY (ts_code, trade_date)
);

-- 因子数据
CREATE TABLE factor_daily (
    ts_code    TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    factor_name TEXT NOT NULL,      -- 因子名 如 pe_ttm, momentum_20d
    factor_value REAL,
    PRIMARY KEY (ts_code, trade_date, factor_name)
);

-- 股票池
CREATE TABLE stock_pool (
    pool_type  TEXT NOT NULL,       -- watchlist/candidate/recommended
    ts_code    TEXT NOT NULL,
    added_date TEXT NOT NULL,
    added_reason TEXT,
    score      REAL,                -- 综合评分
    status     TEXT DEFAULT 'active', -- active/removed/paused
    PRIMARY KEY (pool_type, ts_code, added_date)
);

-- 持仓记录
CREATE TABLE position (
    ts_code      TEXT NOT NULL,
    entry_date   TEXT NOT NULL,     -- 建仓日期
    entry_price  REAL,              -- 建仓价格
    shares       INTEGER,           -- 持仓数量
    cost         REAL,              -- 持仓成本
    exit_date    TEXT,              -- 清仓日期
    exit_price   REAL,              -- 清仓价格
    pnl          REAL,              -- 盈亏
    pnl_pct      REAL,              -- 盈亏%
    status       TEXT DEFAULT 'open', -- open/closed
    PRIMARY KEY (ts_code, entry_date)
);

-- 风控预警
CREATE TABLE risk_alert (
    alert_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_time  TEXT NOT NULL,
    alert_type  TEXT NOT NULL,      -- drawdown/position_limit/black_swan
    severity    TEXT NOT NULL,      -- info/warning/critical
    ts_code     TEXT,               -- 关联股票（可为空=组合级）
    message     TEXT,
    action      TEXT,               -- 建议动作
    acknowledged INTEGER DEFAULT 0
);

-- 研报索引
CREATE TABLE research_index (
    report_id   TEXT PRIMARY KEY,   -- 如 industry-ai-20260409
    report_type TEXT NOT NULL,      -- industry/sector/stock
    title       TEXT,
    ts_codes    TEXT,               -- 关联股票代码（逗号分隔）
    created_at  TEXT,
    file_path   TEXT                -- Markdown文件路径
);
```

### 5.3 Python 服务设计

#### 5.3.1 数据采集服务（data_harvester）

```python
# 核心职责：定时采集行情、财务、宏观数据
# 运行方式：cron 驱动的 Python 脚本（非常驻进程）
# 数据写入：SQLite

# 采集频率：
# - 日线行情：每日 15:30（收盘后）
# - 实时行情（盘中）：每5分钟（仅交易时段）— 可选
# - 财务数据：每周六
# - 宏观数据：每月初
# - 新闻舆情：每小时
```

#### 5.3.2 因子计算服务（factor_engine）

```python
# 核心职责：计算技术因子、基本面因子、情绪因子
# 运行方式：cron 驱动的 Python 脚本
# 依赖：pandas, numpy, talib（技术指标）

# 因子类别：
# - 技术因子：MA5/10/20/60, MACD, RSI, KDJ, BOLL, 成交量比
# - 基本面因子：PE_TTM, PB, ROE, 营收增速, 净利增速
# - 情绪因子：换手率, 涨停/跌停比, 北向资金净流入
# - 复合因子：动量得分, 价值得分, 质量得分
```

#### 5.3.3 风控引擎（risk_engine）

```python
# 核心职责：实时监控组合风险，触发预警
# 运行方式：cron 驱动（盘中每10分钟，盘后每小时）
# 预警写入：risk_alert 表 + 05_risk/alerts/ Markdown

# 风控规则：
# - 单票最大仓位：≤20%
# - 组合最大回撤：≤15%
# - 单日最大亏损：≤5%
# - 行业集中度：≤40%
# - 止损线：个股-8%自动预警
```

#### 5.3.4 回测框架（backtest）

```python
# 核心职责：验证选股策略和调仓逻辑的历史表现
# 运行方式：按需触发（Agent调用或手动）
# 框架选型：backtrader 或 vectorbt

# 回测输出：
# - 年化收益率
# - 最大回撤
# - 夏普比率
# - 胜率
# - 收益曲线图
```

---

## 六、核心流程设计

### 6.1 每日运行时间线

```
08:30  ── 数据采集（前日行情+隔夜新闻）
09:00  ── smr-brief-writer: 盘前简报
09:30  ── 开盘（风控引擎启动盘中监控）
11:30  ── 午间数据更新
13:00  ── 开盘（风控继续）
15:00  ── 收盘
15:30  ── 数据采集（当日行情）
16:00  ── smr-analyst: 因子计算 + 选股更新
17:00  ── smr-researcher: 深度研究（如有触发）
18:00  ── smr-advisor: 推荐更新
19:00  ── smr-portfolio-mgr: 持仓复盘
20:00  ── smr-brief-writer: 日报撰写
21:00  ── smr-risk-controller: 风控日报
22:00  ── smr-lead: 次日计划
```

### 6.2 研究流程

```
触发源（新闻/异动/用户指定）
    │
    ▼
smr-researcher 读取触发信息
    │
    ├── 调用 Python 数据服务获取基本面数据
    ├── 读取 01_data/ 中的因子数据
    ├── 搜索相关研报/新闻
    │
    ▼
产出研报 → 02_research/{type}/{report-id}/
    ├── 00_research-card.md      # 研究卡片（元数据）
    ├── summary.md               # 摘要
    ├── analysis.md              # 分析正文
    ├── valuation.md             # 估值分析
    ├── risk_assessment.md       # 风险评估
    └── conclusion.md            # 结论与建议
```

### 6.3 推荐流程

```
smr-analyst 产出因子报告
    +
smr-researcher 产出研报
    │
    ▼
smr-advisor 综合判断
    │
    ├── 读取因子排名（Python产出）
    ├── 读取研报结论
    ├── 读取当前持仓
    ├── 读取风控状态
    │
    ▼
产出推荐 → 03_stock_pool/recommended/{date}/
    ├── recommendation-card.md   # 推荐卡片
    ├── stock_pick.md            # 选股逻辑
    ├── entry_plan.md            # 建仓计划
    ├── stop_loss.md             # 止损方案
    └── disclaimer.md            # 免责声明（必须）
```

### 6.4 持仓管理流程

```
用户确认买入 → smr-portfolio-mgr 记录持仓
    │
    ├── 写入 position 表
    ├── 更新 04_portfolio/positions/
    │
    ▼
每日收盘后自动更新
    │
    ├── 计算盈亏（Python服务）
    ├── 更新 position 表
    ├── smr-risk-controller 检查风控规则
    │
    ▼
触发调仓建议（如有）
    │
    ├── smr-advisor 产出调仓建议
    ├── smr-portfolio-mgr 更新持仓记录
    └── smr-brief-writer 通知用户
```

---

## 七、合规框架

### 7.1 免责声明（所有推荐类产出必须附带）

```
⚠️ 风险提示与免责声明

本内容仅供参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
本系统基于公开数据和量化模型生成分析，不保证数据的完整性和准确性。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
```

### 7.2 合规规则

| 规则 | 实现 |
|------|------|
| 不承诺收益 | 推荐模板中禁止出现"保证"、"稳赚"等词汇 |
| 风险提示 | 每篇推荐必须包含风险提示段 |
| 数据来源标注 | 研报必须标注数据来源 |
| 模型局限性说明 | 量化结论必须说明模型假设和局限 |
| 不代客操作 | 系统只提供建议，所有操作需用户确认 |

---

## 八、开发计划

### Phase 0：基础设施搭建（1-2天）

**目标**：建立隔离的目录结构、数据库、Agent workspace

| 任务 | 产出 | 依赖 |
|------|------|------|
| 创建 SMR 根目录结构 | `/Users/apple/Documents/同行资本二级市场/` 全套目录 | 无 |
| 初始化 SQLite 数据库 | `smr.db` + 全部表结构 | 无 |
| 创建 7 个 Agent workspace | `workspace-smr-{id}/` + 核心文件 | 无 |
| 修改 openclaw.json | 新增 7 个 agent 定义 | 无 |
| 安装 Python 依赖 | akshare, tushare, pandas, numpy, talib | 无 |

**验收标准**：
- `openclaw agent list` 能看到 7 个 smr-* agent
- 每个 smr-* agent 能独立启动 session
- SQLite 数据库可正常读写
- AkShare 能成功拉取测试数据

### Phase 1：数据管道（2-3天）

**目标**：实现数据采集和因子计算

| 任务 | 产出 | 依赖 |
|------|------|------|
| 日线行情采集脚本 | `08_scripts/data_harvester/daily_bar.py` | Phase 0 |
| 财务数据采集脚本 | `08_scripts/data_harvester/financial.py` | Phase 0 |
| 基本面因子计算 | `08_scripts/factor_engine/fundamental.py` | Phase 0 |
| 技术因子计算 | `08_scripts/factor_engine/technical.py` | Phase 0 |
| 数据采集 cron job | 每日15:30自动采集 | 采集脚本 |
| 因子计算 cron job | 每日16:00自动计算 | 因子脚本 |
| 数据完整性校验 | 采集后自动校验 | 采集脚本 |

**验收标准**：
- 自动采集 A 股日线行情（至少沪深300成分股）
- 计算至少 10 个技术因子 + 5 个基本面因子
- 数据库中有连续 5 个交易日的完整数据

### Phase 2：研究与分析（2-3天）

**目标**：实现研究流程和选股逻辑

| 任务 | 产出 | 依赖 |
|------|------|------|
| smr-researcher SOUL + AGENTS | 研究员人格与行为规范 | Phase 0 |
| smr-analyst SOUL + AGENTS | 分析师人格与行为规范 | Phase 0 |
| 行业研究 Skill | `09_runbooks/skills/smr-industry-research/` | Phase 1 |
| 选股模型 Skill | `09_runbooks/skills/smr-stock-screening/` | Phase 1 |
| 研究产出模板 | `09_runbooks/templates/` | Phase 0 |
| 研究触发 cron | 异动/新闻触发研究 | Skill |

**验收标准**：
- smr-researcher 能产出一份完整的行业研报
- smr-analyst 能基于因子数据产出选股报告
- 研报包含免责声明

### Phase 3：推荐与持仓（2-3天）

**目标**：实现推荐和持仓管理

| 任务 | 产出 | 依赖 |
|------|------|------|
| smr-advisor SOUL + AGENTS | 投资顾问人格与行为规范 | Phase 2 |
| smr-portfolio-mgr SOUL + AGENTS | 持仓经理人格与行为规范 | Phase 2 |
| 推荐产出 Skill | `09_runbooks/skills/smr-recommendation/` | Phase 2 |
| 持仓管理 Skill | `09_runbooks/skills/smr-portfolio/` | Phase 2 |
| 持仓录入脚本 | `08_scripts/portfolio/entry.py` | Phase 0 |
| 盈亏计算脚本 | `08_scripts/portfolio/pnl.py` | Phase 1 |

**验收标准**：
- smr-advisor 能产出包含建仓计划、止损方案的推荐
- smr-portfolio-mgr 能记录持仓并计算盈亏
- 所有推荐附带免责声明

### Phase 4：风控与报告（2-3天）

**目标**：实现风控监控和报告推送

| 任务 | 产出 | 依赖 |
|------|------|------|
| smr-risk-controller SOUL + AGENTS | 风控官人格与行为规范 | Phase 3 |
| smr-brief-writer SOUL + AGENTS | 简报撰写人格与行为规范 | Phase 3 |
| 风控引擎脚本 | `08_scripts/risk_engine/monitor.py` | Phase 1 |
| 风控预警 Skill | `09_runbooks/skills/smr-risk-alert/` | Phase 3 |
| 日报 Skill | `09_runbooks/skills/smr-daily-brief/` | Phase 3 |
| 周报 Skill | `09_runbooks/skills/smr-weekly-brief/` | Phase 3 |
| 微信推送（独立实例） | 复用桥接架构，独立 outbox | Phase 3 |
| 全量 cron job 配置 | 每日运行时间线 | 全部 |

**验收标准**：
- 风控引擎能在回撤超限时触发预警
- smr-brief-writer 能自动产出日报
- 日报能推送到微信（草稿箱）

### Phase 5：联调与优化（2-3天）

**目标**：端到端联调，优化体验

| 任务 | 产出 | 依赖 |
|------|------|------|
| 端到端联调 | 完整流程跑通 | Phase 4 |
| 性能优化 | 数据采集/因子计算耗时优化 | 联调 |
| 异常处理 | 网络超时、数据缺失、API限流 | 联调 |
| 回测验证 | 至少一个策略的回测报告 | Phase 4 |
| 用户文档 | 使用说明（如何录入持仓、查看推荐等） | 全部 |

**验收标准**：
- 从数据采集到日报推送的完整链路无人工干预
- 连续 3 个交易日稳定运行
- 无数据丢失、无风控误报

---

## 九、技术选型与依赖

### 9.1 Python 依赖

```
akshare>=1.12          # A股数据采集（免费）
tushare>=1.4           # 补充数据源（免费注册）
pandas>=2.0            # 数据处理
numpy>=1.24            # 数值计算
TA-Lib>=0.4.28         # 技术指标计算
backtrader>=1.9        # 回测框架（备选：vectorbt）
matplotlib>=3.7        # 图表生成
jinja2>=3.1            # 模板渲染
```

### 9.2 不引入的重型依赖

| 不使用 | 原因 |
|--------|------|
| Django/Flask | 不需要 Web 服务，cron 驱动即可 |
| Redis | 数据量小，SQLite 足够 |
| Docker | 单机部署，无需容器化 |
| PostgreSQL | SQLite 完全满足需求 |
| qlib | 过重，初期用自建因子即可 |

### 9.3 与现有系统的技术栈对比

| 维度 | VCR/MCT | SMR |
|------|---------|-----|
| 数据存储 | Markdown文件 | SQLite + Markdown |
| 脚本语言 | Python 3 | Python 3 |
| 数据源 | RSS/网页抓取 | AkShare/Tushare API |
| 推送渠道 | 微信公众号 | 微信公众号（独立实例） |
| Agent框架 | OpenClaw | OpenClaw |
| 调度方式 | OpenClaw cron | OpenClaw cron + 系统 cron |

---

## 十、风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| AkShare API 限流/不稳定 | 中 | 数据采集中断 | 多数据源降级（Tushare备用） |
| 因子计算性能瓶颈 | 低 | 计算超时 | 限定股票范围（先沪深300） |
| OpenClaw agent 并发上限 | 低 | SMR agent 无法同时运行 | 调整 maxConcurrent 或错峰 |
| 数据合规风险 | 中 | 法律问题 | 严格免责声明，不提供代客操作 |
| 与现有业务线冲突 | 低 | 资源竞争 | 完全隔离设计，独立目录/agent/session |
| 回测过拟合 | 高 | 策略实盘失效 | 样本外验证，多周期回测 |

---

## 十一、后续扩展方向（Phase 6+）

1. **港股/美股覆盖**：扩展数据源至港股（富途API）和美股（yfinance）
2. **ETF策略**：增加ETF轮动策略，降低个股风险
3. **可转债分析**：可转债双低策略、下修博弈
4. **期权策略**：波动率分析、备兑策略
5. **飞书实时推送**：盘中异动通过飞书 bot 实时推送
6. **多策略组合**：多策略等权/风险平价组合
7. **机器学习选股**：LightGBM/XGBoost 因子挖掘

---

## 附录A：SMR Cron Job 清单（规划）

| Job名称 | Agent | 频率 | 说明 |
|---------|-------|------|------|
| SMR-日线行情采集 | smr-analyst | 15:30 | 收盘后采集当日行情 |
| SMR-因子计算 | smr-analyst | 16:00 | 计算技术+基本面因子 |
| SMR-选股更新 | smr-analyst | 16:30 | 更新股票池排名 |
| SMR-盘前简报 | smr-brief-writer | 09:00 | 盘前市场概览 |
| SMR-盘中风控 | smr-risk-controller | 10:00,11:00,13:30,14:30 | 盘中风控检查 |
| SMR-盘后风控 | smr-risk-controller | 15:30 | 盘后风控总结 |
| SMR-持仓复盘 | smr-portfolio-mgr | 19:00 | 持仓盈亏更新 |
| SMR-日报撰写 | smr-brief-writer | 20:00 | 每日市场复盘 |
| SMR-周报撰写 | smr-brief-writer | 周六10:00 | 每周总结 |
| SMR-次日计划 | smr-lead | 22:00 | 次日研究/操作计划 |
| SMR-财务数据更新 | smr-analyst | 周六08:00 | 每周财务数据 |
| SMR-行业研究触发 | smr-researcher | 按需 | 异动/新闻触发 |

## 附录B：SMR 与现有系统零交叉检查清单

- [ ] SMR agent ID 全部使用 `smr-` 前缀
- [ ] SMR workspace 路径全部在 `/Users/apple/.openclaw/workspace-smr-*/`
- [ ] SMR 数据目录全部在 `/Users/apple/Documents/同行资本二级市场/`
- [ ] SMR agent 不在现有 `agentToAgent.allow` 列表中与 VCR/MCT agent 互通
- [ ] SMR cron job 的 `name` 全部使用 `SMR-` 前缀
- [ ] SMR 不使用现有飞书 bot 账号
- [ ] SMR 不读写 VCR/MCT 的任何目录
- [ ] SMR 的微信桥接使用独立 outbox 目录
- [ ] SMR 的 SQLite 数据库与 VCR/MCT 完全独立
- [ ] SMR 的 Python 脚本不 import VCR/MCT 的任何模块
"""

os.makedirs(os.path.dirname(TARGET), exist_ok=True)
with open(TARGET, "w", encoding="utf-8") as f:
    f.write(CONTENT)

print(f"Written {len(CONTENT)} chars to {TARGET}")
