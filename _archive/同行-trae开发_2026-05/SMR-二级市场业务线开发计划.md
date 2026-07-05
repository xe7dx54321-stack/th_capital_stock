# SMR — 同行资本二级市场业务线开发计划

> 版本：v2.0 | 日期：2026-04-09 | 作者：Trae IDE
> 状态：规划中，待用户确认
> 变更：v1.0→v2.0 按用户要求收敛业务边界

---

## 一、项目定位

### 1.1 业务线全称

**SMR（Secondary Market Research）— 前沿科技赛道中长线趋势研究与持仓管理**

### 1.2 与现有业务线的关系

| 业务线 | 代号 | 核心产出 | 运行平台 |
|--------|------|----------|----------|
| 虚拟VC投研 | VCR | Project Card、Top-down报告（一级市场） | OpenClaw |
| 市场内容 | MCT | 多平台适配文章、微信公众号 | OpenClaw |
| **二级市场研究** | **SMR** | **中长线趋势研报、股票池、持仓管理、风控信号** | **OpenClaw + 独立Python服务** |

**SMR 与 VCR 的战略协同**：SMR 只关注 VCR 一级市场研究覆盖的前沿科技赛道，形成"一级看早期→二级看趋势"的产业链闭环认知优势。

### 1.3 核心原则

1. **零侵入**：不修改任何现有 agent（VCR 6个 + MCT 8个 = 14个），不动现有 cron job、workspace、session
2. **完全隔离**：独立目录、独立 agent 体系、独立 session、独立 memory、独立 cron
3. **OpenClaw优先**：能用 OpenClaw 跑的尽量用 OpenClaw，不适合的用独立 Python 服务
4. **合规先行**：所有推荐类产出必须附带免责声明和风险提示
5. **中长线唯一**：只做基于深度研究的中长线趋势交易，绝不涉足高频/短线/日内

### 1.4 业务边界（v2.0 收敛）

| 维度 | ✅ 做 | ❌ 不做 |
|------|-------|---------|
| 交易风格 | 中长线趋势交易（持仓周期：周级~月级~季级） | 高频交易、日内交易、短线打板、量化T+0 |
| 市场范围 | A股 + H股（直接投资标的） | 美股直接投资（但跟踪美股对标标的的信号） |
| 行业范围 | 具身智能、AI、半导体、量子（对齐VCR） | 能源、食品消费、家电、金属、地产、银行等传统行业 |
| 研究深度 | 行业+企业深度研究驱动 | 技术指标驱动、纯量化因子驱动 |
| 算力依赖 | 轻量级（因子计算+回测，单机可跑） | 重算力（实时tick级、高频回测、深度学习训练） |

---

## 二、行业覆盖范围（对齐VCR）

### 2.1 三大顶层行业板块

SMR 的行业覆盖严格对齐 VCR 的 `sector_priority_map`，只研究以下三个板块的 A+H 标的：

| Sector | 行业板块 | VCR优先级 | SMR定位 | A+H核心标的举例 |
|--------|----------|-----------|---------|-----------------|
| `sector:ai_automation` | AI + 自动化 | P0/P1 | **主力研究+交易** | 见2.2节 |
| `sector:advanced_hardware_manufacturing` | 先进制造 / 半导体 | P1 | **主力研究+交易** | 见2.3节 |
| `sector:frontier_science_commercialization` | 前沿科学 / 量子 | P1 | **前瞻研究+观察池** | 见2.4节 |

### 2.2 AI + 自动化板块

#### 具身智能 / 工业场景商业化（VCR P0-core-build → SMR 核心交易赛道）

| 细分赛道 | A+H核心标的 | 美股对标标的（跟踪联动） |
|----------|-------------|------------------------|
| 整机平台+工业方案 | 优必选(9880.HK)、宇树科技(拟IPO) | Tesla(TSLA)、Figure AI(未上市) |
| 关节/执行器/减速器 | 绿的谐波(688017)、汇川技术(300124)、拓普集团(601689)、三花智控(002050)、中大力德(002796)、丰立智能(301368) | Harmonic Drive(HPHT) |
| 灵巧手/末端执行器 | 鸣志电器(603728)、临界点(未上市) | None |
| 力觉/视觉/传感器 | 坤维科技(未上市)、奥比中光(688322) | None |
| VLA/数据引擎 | 觅蜂科技(未上市) | Covariant(已收购) |

#### AI Agent Infra（VCR P1 → SMR 观察池）

| 细分赛道 | A+H核心标的 | 美股对标标的 |
|----------|-------------|-------------|
| 模型/推理平台 | 科大讯飞(002230)、商汤-W(0020.HK) | OpenAI(未上市)、Anthropic(未上市) |
| GPU/算力平台 | 摩尔线程(未上市)、昆仑计算(未上市) | NVDA、AMD |
| AI应用/工作流 | 金山办公(688111)、泛微网络(603039) | CRM、NOW、AI应用层 |

### 2.3 半导体 / 先进制造板块

#### 算力芯片与加速器（VCR P1 → SMR 核心交易赛道）

| 细分赛道 | A+H核心标的 | 美股对标标的 |
|----------|-------------|-------------|
| GPU/AI加速器 | 海光信息(688041)、寒武纪(688256) | NVDA、AMD |
| CPU/DPU | 海光信息(688041)、澜起科技(688008) | INTC、AVGO |
| EDA/IP | 华大九天(301269)、芯原股份(688521) | SNPS、CDNS |

#### 光芯片/CPO/高速光互连（VCR P1 → SMR 核心交易赛道）

| 细分赛道 | A+H核心标的 | 美股对标标的 |
|----------|-------------|-------------|
| CPO/共封装光学 | 中际旭创(300308)、新易盛(300502)、天孚通信(300394) | LITE、MRVL、COHR |
| 光芯片/光引擎 | 光迅科技(002281)、索尔思光电(未上市)、光库科技(300620) | Lumentum(LITE) |
| 液冷/基础设施 | 曙光数创(872808)、英维克(002837) | VRT |

#### 半导体存储（VCR P2 → SMR 观察池）

| 细分赛道 | A+H核心标的 | 美股对标标的 |
|----------|-------------|-------------|
| HBM/高带宽存储 | 兆易创新(603986)、东芯股份(688110) | MU、SKHynix(000660.KS) |

### 2.4 量子 / 前沿科学板块（VCR P1 → SMR 前瞻观察池）

| 细分赛道 | A+H核心标的 | 美股对标标的 |
|----------|-------------|-------------|
| 量子通信 | 国盾量子(688027) | None |
| 量子计算 | 本源量子(未上市)、玻色量子(未上市) | IONQ、RGTI、QBTS |
| 量子传感 | 未磁科技(未上市) | None |
| 低温/测控系统 | 知冷低温科技(未上市) | None |

### 2.5 美股联动跟踪机制

**核心逻辑**：美股前沿科技标的的电话会纪要、业绩指引、头部研报，是预判 A+H 供应链标的需求变化和股价走势的关键领先信号。

| 联动类型 | 示例 |
|----------|------|
| 供应链映射 | NVIDIA财报→中际旭创/新易盛光模块订单预期 |
| 技术路线映射 | Tesla Optimus进展→绿的谐波/拓普集团执行器预期 |
| 估值锚映射 | IONQ/Rigetti市值→国盾量子/本源量子估值参考 |
| 需求景气映射 | Meta/Google资本开支→算力链整体景气度 |

**美股信号采集方式**：
- 财报电话会纪要：通过公开渠道获取（SEC EDGAR + 公司IR页面）
- 业绩指引/前瞻：同上
- 头部研报：通过公开摘要获取（不购买付费研报）
- 产业链分析：Agent 基于公开信息推理

---

## 三、业务需求拆解

### 3.1 功能模块

| 模块 | 功能描述 | 适合OpenClaw | 备注 |
|------|----------|:---:|------|
| 行业深度研究 | 前沿科技赛道行业研究，产出研报 | ✅ | Agent驱动，与VCR top-down协同 |
| 企业深度研究 | 个股基本面+产业链定位研究 | ✅ | Agent驱动 |
| 美股联动分析 | 美股对标标的信号→A+H映射 | ✅ | Agent推理+公开数据 |
| 中长线趋势判断 | 基于研究结论的趋势方向判断 | ✅ | Agent综合判断，非量化信号 |
| 股票池管理 | 观察→候选→推荐三级股票池 | ⚠️ | 评分Python，入池Agent |
| 持仓管理 | 持仓记录、盈亏跟踪、调仓建议 | ⚠️ | 数据Python，建议Agent |
| 风险监控 | 回撤预警、仓位风控 | ❌ | 定时计算，Python服务 |
| 日报/周报 | 市场复盘、持仓总结 | ✅ | Agent驱动 |
| 微信推送 | 研究结论/推荐/预警推送 | ✅ | 复用MCT桥接架构（独立实例） |

### 3.2 "OpenClaw做大脑，Python做手脚"架构

```
┌──────────────────────────────────────────────────────────────┐
│                    OpenClaw 层（大脑）                         │
│                                                              │
│  smr-lead ──► smr-researcher ──► smr-analyst                │
│      │              │                  │                      │
│      ▼              ▼                  ▼                      │
│  smr-brief-writer  smr-advisor    smr-portfolio-mgr          │
│      │              │                  │                      │
│      └──────────────┼──────────────────┘                      │
│                     ▼                                         │
│              smr-risk-controller                              │
│                                                              │
│  研究驱动 · 趋势判断 · 内容生成 · 推送调度                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                  独立 Python 服务层（手脚）                     │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 行情采集  │  │ 因子计算  │  │ 风控引擎  │  │ 美股信号  │    │
│  │ (A+H)   │  │ (轻量级)  │  │          │  │ 采集     │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│       │              │              │              │          │
│       ▼              ▼              ▼              ▼          │
│  ┌──────────────────────────────────────────────────┐        │
│  │         SMR SQLite 数据库                          │        │
│  │  (A+H行情 / 因子 / 持仓 / 美股信号 / 研报索引)     │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                   数据源层                                    │
│                                                              │
│  AkShare(A+H行情) / Tushare(补充) / SEC EDGAR(美股财报)       │
│  / 公司IR页面(电话会纪要) / 东方财富(资金流)                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**分工原则：**
- **OpenClaw Agent**：研究分析、趋势判断、内容生成、推送调度 — 需要"思考"的工作
- **Python 服务**：行情采集、因子计算、风控监控、美股信号采集 — 需要"计算/采集"的工作
- **交互方式**：Agent 通过读写共享文件系统（SQLite + Markdown）与 Python 服务交互

---

## 四、隔离方案

### 4.1 目录隔离

```
/Users/apple/Documents/同行资本二级市场部门/二级市场系统/          ← SMR独立根目录
├── 00_control/                    # 控制中心
│   ├── sector_priority_map.md     #   行业优先级（对齐VCR）
│   ├── dispatch_board.md          #   调度面板
│   └── watchlist_registry.md      #   标的注册表
├── 01_data/                       # 数据层
│   ├── db/                        #   SQLite数据库
│   │   └── smr.db                 #     主数据库
│   ├── raw/                       #   原始数据缓存（按日期）
│   ├── factor/                    #   因子计算结果
│   └── us_signals/                #   美股联动信号（按日期）
├── 02_research/                   # 研究产出
│   ├── industry/                  #   行业研究
│   │   ├── embodied-ai/           #     具身智能
│   │   ├── semiconductor/         #     半导体
│   │   ├── ai-agent/              #     AI Agent
│   │   └── quantum/               #     量子
│   ├── stock/                     #   个股研究
│   └── us_linkage/                #   美股联动分析
├── 03_stock_pool/                 # 股票池
│   ├── watchlist/                 #   观察池（VCR P2对应标的）
│   ├── candidate/                 #   候选池（趋势初现）
│   └── recommended/               #   推荐池（趋势确认+建仓计划）
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
│   ├── data_harvester/            #   A+H行情采集
│   ├── us_signal_harvester/       #   美股信号采集
│   ├── factor_engine/             #   因子计算（轻量级）
│   ├── risk_engine/               #   风控引擎
│   └── backtest/                  #   回测框架
├── 09_runbooks/                   # Runbook
│   ├── scripts/                   #   Python执行脚本
│   ├── skills/                    #   Skill定义
│   └── templates/                 #   模板
└── 10_logs/                       # 运行日志
```

### 4.2 Agent 隔离

SMR 的所有 agent 使用 `smr-` 前缀，与现有 agent 零重叠：

| 现有Agent | SMR Agent | 隔离维度 |
|-----------|-----------|----------|
| lead, knowledge-curator, ... | smr-lead, smr-researcher, ... | ID前缀不同 |
| workspace-lead, workspace-kc, ... | workspace-smr-lead, ... | 目录完全独立 |
| agents/lead/, agents/kc/, ... | agents/smr-lead/, ... | 运行时数据独立 |
| memory/lead.sqlite, ... | memory/smr-lead.sqlite, ... | 向量记忆独立 |
| cron job: agentId=lead, ... | cron job: agentId=smr-lead, ... | 调度独立 |

**关键隔离规则：**
- SMR agent 不与 VCR/MCT agent 互通（`agentToAgent.allow` 独立分组）
- SMR agent 不绑定现有飞书 bot 账号
- SMR 的 cron job 使用 `sessionTarget: "isolated"`

### 4.3 Session / Memory / Cron 隔离

- 每个 SMR agent 有独立的 `agents/smr-{id}/sessions/sessions.json`
- 每个 SMR agent 有独立的 `memory/smr-{id}.sqlite`
- SMR cron job 的 `name` 统一使用 `SMR-` 前缀
- SMR agent 之间通过**共享文件系统**交接，不走 agent-to-agent 消息

---

## 五、Agent 体系设计

### 5.1 Agent 清单

| ID | 角色 | 职责 | 心跳 | 模型 |
|----|------|------|------|------|
| smr-lead | SMR参谋长 | 调度、优先级管理、跨模块协调 | 3h | MiniMax-M2.7 |
| smr-researcher | 行业研究员 | 前沿科技赛道深度研究，产出研报 | 3h | MiniMax-M2.7 |
| smr-analyst | 趋势分析师 | 因子分析、趋势判断、美股联动解读 | 3h | MiniMax-M2.7 |
| smr-advisor | 投资顾问 | 综合研究+趋势结论，产出中长线推荐 | 3h | MiniMax-M2.7 |
| smr-portfolio-mgr | 持仓经理 | 持仓记录、盈亏跟踪、调仓建议 | 3h | MiniMax-M2.7 |
| smr-risk-controller | 风控官 | 风险监控、预警触发、仓位控制 | 1h | MiniMax-M2.7 |
| smr-brief-writer | 简报撰写 | 日报/周报/临时报告撰写与推送 | 3h | MiniMax-M2.7 |

### 5.2 协作拓扑

```
smr-lead（调度中心）
    │
    ├──► smr-researcher ──产出──► 研报 → 02_research/
    │         │
    │         │  ┌── 美股联动信号 ←── us_signal_harvester(Python)
    │         ▼  ▼
    ├──► smr-analyst ──产出──► 趋势判断 → 01_data/factor/
    │                                    │
    │         ┌──────────────────────────┘
    │         ▼
    ├──► smr-advisor ◄──研报+趋势── 产出推荐 → 03_stock_pool/
    │         │
    │         ▼
    ├──► smr-portfolio-mgr ◄──推荐── 产出调仓建议 → 04_portfolio/
    │         │
    │         ▼
    ├──► smr-risk-controller ◄──持仓── 产出预警 → 05_risk/
    │
    └──► smr-brief-writer ◄──全量数据── 产出报告 → 06_reports/
```

### 5.3 Agent Workspace 结构

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

### 5.4 openclaw.json 配置变更

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

---

## 六、数据层设计

### 6.1 数据源选型

| 数据源 | 类型 | 覆盖范围 | 成本 | 用途 |
|--------|------|----------|------|------|
| **AkShare** | Python库 | A+H行情/财务 | 免费 | 主力数据源 |
| **Tushare** | Python库 | A+H全量数据 | 需积分 | 补充数据源 |
| **东方财富** | 网页 | 实时行情/资金流 | 免费 | 盘中数据 |
| **SEC EDGAR** | API | 美股财报/10-K/10-Q | 免费 | 美股基本面 |
| **公司IR页面** | 网页 | 电话会纪要/Earnings Call | 免费 | 美股联动信号 |
| **Yahoo Finance** | API | 美股行情 | 免费 | 美股价格跟踪 |

### 6.2 数据库设计（SQLite）

```sql
-- A+H 日线行情
CREATE TABLE daily_bar (
    ts_code    TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open       REAL, close         REAL,
    high       REAL, low           REAL,
    vol        REAL, amount        REAL,
    pct_chg    REAL,
    turnover   REAL,
    market     TEXT DEFAULT 'A',   -- A/H 标识
    PRIMARY KEY (ts_code, trade_date)
);

-- 美股日线行情（仅跟踪对标标的）
CREATE TABLE us_daily_bar (
    symbol     TEXT NOT NULL,      -- 如 NVDA, TSLA
    trade_date TEXT NOT NULL,
    open       REAL, close         REAL,
    high       REAL, low           REAL,
    vol        REAL, amount        REAL,
    pct_chg    REAL,
    PRIMARY KEY (symbol, trade_date)
);

-- 美股联动信号
CREATE TABLE us_signal (
    signal_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_time TEXT NOT NULL,
    symbol      TEXT NOT NULL,      -- 美股标的
    signal_type TEXT NOT NULL,      -- earnings_call/guidance/analyst_rating/capex
    title       TEXT,
    summary     TEXT,
    ah_impact   TEXT,               -- 对A+H的影响判断
    related_ah  TEXT,               -- 关联A+H标的（逗号分隔）
    source_url  TEXT,
    created_at  TEXT
);

-- 因子数据（轻量级，仅中长线因子）
CREATE TABLE factor_daily (
    ts_code    TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    factor_value REAL,
    PRIMARY KEY (ts_code, trade_date, factor_name)
);

-- 股票池
CREATE TABLE stock_pool (
    pool_type  TEXT NOT NULL,       -- watchlist/candidate/recommended
    ts_code    TEXT NOT NULL,
    sector     TEXT,                -- embodied_ai/semiconductor/ai_agent/quantum
    added_date TEXT NOT NULL,
    added_reason TEXT,
    score      REAL,
    status     TEXT DEFAULT 'active',
    PRIMARY KEY (pool_type, ts_code, added_date)
);

-- 持仓记录
CREATE TABLE position (
    ts_code      TEXT NOT NULL,
    entry_date   TEXT NOT NULL,
    entry_price  REAL,
    shares       INTEGER,
    cost         REAL,
    target_price REAL,              -- 目标价（中长线）
    stop_loss    REAL,              -- 止损价
    thesis       TEXT,              -- 持仓逻辑（为什么买）
    exit_date    TEXT,
    exit_price   REAL,
    pnl          REAL,
    pnl_pct      REAL,
    status       TEXT DEFAULT 'open',
    PRIMARY KEY (ts_code, entry_date)
);

-- 风控预警
CREATE TABLE risk_alert (
    alert_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_time  TEXT NOT NULL,
    alert_type  TEXT NOT NULL,      -- drawdown/position_limit/thesis_broken
    severity    TEXT NOT NULL,      -- info/warning/critical
    ts_code     TEXT,
    message     TEXT,
    action      TEXT,
    acknowledged INTEGER DEFAULT 0
);

-- 研报索引
CREATE TABLE research_index (
    report_id   TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,      -- industry/stock/us_linkage
    sector      TEXT,               -- embodied_ai/semiconductor/ai_agent/quantum
    title       TEXT,
    ts_codes    TEXT,
    created_at  TEXT,
    file_path   TEXT
);

-- 行业板块配置（对齐VCR）
CREATE TABLE sector_config (
    sector_key  TEXT PRIMARY KEY,   -- embodied_ai/semiconductor/ai_agent/quantum
    sector_name TEXT NOT NULL,
    vcr_priority TEXT,              -- P0/P1/P2
    smr_focus   TEXT,               -- core_trade/watch_observe
    ah_universe TEXT,               -- A+H标的列表（逗号分隔）
    us_benchmarks TEXT              -- 美股对标标的（逗号分隔）
);
```

### 6.3 Python 服务设计

#### 6.3.1 A+H行情采集服务（data_harvester）

```python
# 核心职责：采集A股+H股前沿科技赛道标行情和财务数据
# 运行方式：cron 驱动（非常驻进程）
# 采集范围：仅 sector_config 中配置的标的，不采集全市场

# 采集频率：
# - A股日线：每日 15:30（收盘后）
# - H股日线：每日 16:30（港股收盘后）
# - 财务数据：每周六
# - 资金流数据：每日 16:00
```

#### 6.3.2 美股信号采集服务（us_signal_harvester）

```python
# 核心职责：采集美股对标标的的财报、电话会纪要、业绩指引
# 运行方式：cron 驱动 + 事件触发
# 数据来源：SEC EDGAR、公司IR页面、Yahoo Finance

# 采集频率：
# - 美股日线行情：每日 06:00（美股收盘后）
# - 财报发布监控：每日检查（财报季加密）
# - 电话会纪要：财报发布后24小时内
# - 分析师评级变动：每日检查
```

#### 6.3.3 因子计算服务（factor_engine）— 轻量级

```python
# 核心职责：计算中长线趋势因子（不做高频因子）
# 运行方式：cron 驱动
# 计算范围：仅 sector_config 中的标的

# 因子类别（全部面向中长线）：
# - 趋势因子：MA20/60/120, MACD(周线), 趋势强度评分
# - 基本面因子：PE_TTM, PB, ROE, 营收增速(季), 净利增速(季)
# - 资金因子：北向资金净流入(5日/20日), 融资余额变化
# - 产业因子：行业景气度评分（基于研究结论）
# - 联动因子：美股对标标的动量传导强度
# 不做：tick级因子、日内因子、高频因子
```

#### 6.3.4 风控引擎（risk_engine）

```python
# 核心职责：监控组合风险，触发预警
# 运行方式：cron 驱动（每日收盘后运行1次，盘中不运行）
# 适配中长线：风控阈值宽松于短线策略

# 风控规则（中长线适配）：
# - 单票最大仓位：≤25%（中长线可适度集中）
# - 组合最大回撤：≤20%（中长线容忍更大回撤）
# - 单周最大亏损：≤8%
# - 行业集中度：≤50%（前沿科技内部）
# - 逻辑止损：持仓逻辑（thesis）被证伪时无条件止损
# - 技术止损：个股跌破关键趋势线（MA60/120）预警
```

#### 6.3.5 回测框架（backtest）— 轻量级

```python
# 核心职责：验证中长线策略的历史表现
# 运行方式：按需触发
# 框架选型：vectorbt（比backtrader更适合向量化回测）

# 回测参数（中长线适配）：
# - 最短持仓周期：5个交易日
# - 信号频率：周级
# - 滑点假设：0.3%（中长线对滑点不敏感）
# - 评估指标：年化收益、最大回撤、夏普比率、胜率、盈亏比
```

---

## 七、核心流程设计

### 7.1 每日运行时间线

```
06:00  ── 美股信号采集（前日收盘行情+财报/纪要）
08:30  ── A+H数据采集（前日行情）
09:00  ── smr-brief-writer: 盘前简报（含美股联动分析）
09:30  ── 开盘（无盘中自动化操作，中长线不盯盘）
15:00  ── 收盘
15:30  ── A股行情采集
16:00  ── H股行情采集 + 资金流数据
16:30  ── smr-analyst: 因子计算 + 趋势判断
17:30  ── smr-researcher: 深度研究（如有触发）
18:30  ── smr-advisor: 推荐更新
19:30  ── smr-portfolio-mgr: 持仓复盘
20:30  ── smr-brief-writer: 日报撰写
21:00  ── smr-risk-controller: 风控日报
22:00  ── smr-lead: 次日计划
```

**与VCR/MCT的时间错峰**：SMR 的核心运行时段（15:30-22:00）与 MCT 晨间线（06:00-09:00）和 VCR 心跳（分散）不冲突。

### 7.2 研究流程（深度研究驱动）

```
触发源
    │
    ├── VCR一级市场信号（新项目卡/thesis变化）── 非实时，读文件
    ├── 美股对标标的重大事件（财报/指引/评级）
    ├── A+H标的价格突破趋势线
    └── 用户指定
    │
    ▼
smr-researcher 读取触发信息
    │
    ├── 读取 VCR 的 project_cards / thesis_deltas（跨业务线认知复用）
    ├── 读取 01_data/ 中的因子数据
    ├── 读取 us_signals/ 中的美股联动信号
    ├── 搜索公开研报/新闻
    │
    ▼
产出研报 → 02_research/{type}/{report-id}/
    ├── 00_research-card.md      # 研究卡片
    ├── thesis.md                # 核心投资逻辑（为什么看好/看空）
    ├── catalyst.md              # 催化剂分析（什么事件会触发趋势变化）
    ├── risk_assessment.md       # 风险评估
    ├── us_linkage.md            # 美股联动分析（如有）
    └── conclusion.md            # 结论与建议
```

### 7.3 推荐流程（中长线趋势确认）

```
smr-analyst 产出趋势判断
    +
smr-researcher 产出研报
    +
美股联动信号
    │
    ▼
smr-advisor 综合判断
    │
    ├── 读取趋势因子排名
    ├── 读取研报核心逻辑（thesis）
    ├── 读取美股对标标的状态
    ├── 读取当前持仓
    ├── 读取风控状态
    │
    ▼
产出推荐 → 03_stock_pool/recommended/{date}/
    ├── recommendation-card.md   # 推荐卡片
    ├── thesis.md                # 投资逻辑（必须）
    ├── catalyst_timeline.md     # 催化剂时间线
    ├── entry_plan.md            # 建仓计划（分批建仓）
    ├── target_and_stop.md       # 目标价 + 止损价
    ├── holding_period.md        # 预期持仓周期（周/月/季）
    └── disclaimer.md            # 免责声明（必须）
```

### 7.4 持仓管理流程（中长线适配）

```
用户确认买入 → smr-portfolio-mgr 记录持仓
    │
    ├── 写入 position 表（含 thesis、target_price、stop_loss）
    ├── 更新 04_portfolio/positions/
    │
    ▼
每日收盘后检查（非盘中）
    │
    ├── 计算盈亏（Python服务）
    ├── 检查 thesis 是否被证伪（Agent判断）
    ├── 检查是否触及止损/目标价
    ├── 检查美股对标标的是否发生重大变化
    │
    ▼
触发调仓建议（如有）
    │
    ├── thesis证伪 → 建议无条件止损
    ├── 触及止损价 → 建议止损
    ├── 触及目标价 → 建议减仓/止盈
    ├── 美股重大利空 → 建议评估A+H影响
    └── 趋势延续 → 维持持仓
```

---

## 八、合规框架

### 8.1 免责声明（所有推荐类产出必须附带）

```
⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
本系统基于公开数据和深度研究生成分析，不保证数据的完整性和准确性。
中长线趋势判断存在不确定性，市场可能长期偏离基本面逻辑。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
```

### 8.2 合规规则

| 规则 | 实现 |
|------|------|
| 不承诺收益 | 推荐模板中禁止出现"保证"、"稳赚"等词汇 |
| 风险提示 | 每篇推荐必须包含风险提示段 |
| 数据来源标注 | 研报必须标注数据来源 |
| 模型局限性说明 | 趋势判断必须说明假设和局限 |
| 不代客操作 | 系统只提供建议，所有操作需用户确认 |
| 逻辑透明 | 每个推荐必须附带 thesis（投资逻辑），不可无逻辑推荐 |

---

## 九、开发计划

### Phase 0：基础设施搭建（1-2天）

**目标**：建立隔离的目录结构、数据库、Agent workspace

| 任务 | 产出 | 依赖 |
|------|------|------|
| 创建 SMR 根目录结构 | `/Users/apple/Documents/同行资本二级市场部门/二级市场系统/` 全套目录 | 无 |
| 初始化 SQLite 数据库 | `smr.db` + 全部表结构 + sector_config初始数据 | 无 |
| 创建 7 个 Agent workspace | `workspace-smr-{id}/` + 核心文件 | 无 |
| 修改 openclaw.json | 新增 7 个 agent 定义 | 无 |
| 安装 Python 依赖 | akshare, tushare, pandas, numpy, vectorbt | 无 |

**验收标准**：
- `openclaw agent list` 能看到 7 个 smr-* agent
- 每个 smr-* agent 能独立启动 session
- SQLite 数据库可正常读写
- AkShare 能成功拉取测试数据
- sector_config 表已填入4个行业板块配置

### Phase 1：数据管道（2-3天）

**目标**：实现A+H行情采集、美股信号采集和因子计算

| 任务 | 产出 | 依赖 |
|------|------|------|
| A+H日线行情采集脚本 | `08_scripts/data_harvester/ah_daily_bar.py` | Phase 0 |
| H股行情采集脚本 | `08_scripts/data_harvester/hk_daily_bar.py` | Phase 0 |
| 财务数据采集脚本 | `08_scripts/data_harvester/financial.py` | Phase 0 |
| 美股行情采集脚本 | `08_scripts/us_signal_harvester/us_daily_bar.py` | Phase 0 |
| 美股财报/纪要采集 | `08_scripts/us_signal_harvester/earnings_monitor.py` | Phase 0 |
| 趋势因子计算 | `08_scripts/factor_engine/trend.py` | Phase 0 |
| 基本面因子计算 | `08_scripts/factor_engine/fundamental.py` | Phase 0 |
| 联动因子计算 | `08_scripts/factor_engine/us_linkage.py` | Phase 0 |
| 数据采集 cron job | 每日自动采集 | 采集脚本 |
| 因子计算 cron job | 每日自动计算 | 因子脚本 |

**验收标准**：
- 自动采集 A+H 前沿科技赛道标的日线行情（约50-80只）
- 自动采集美股对标标的行情（约15-20只）
- 计算至少 8 个趋势因子 + 5 个基本面因子 + 3 个联动因子
- 美股财报发布后能自动检测并记录信号

### Phase 2：研究与分析（2-3天）

**目标**：实现研究流程和趋势判断逻辑

| 任务 | 产出 | 依赖 |
|------|------|------|
| smr-researcher SOUL + AGENTS | 研究员人格与行为规范 | Phase 0 |
| smr-analyst SOUL + AGENTS | 分析师人格与行为规范 | Phase 0 |
| 行业研究 Skill | `09_runbooks/skills/smr-industry-research/` | Phase 1 |
| 个股研究 Skill | `09_runbooks/skills/smr-stock-research/` | Phase 1 |
| 美股联动分析 Skill | `09_runbooks/skills/smr-us-linkage/` | Phase 1 |
| 趋势判断 Skill | `09_runbooks/skills/smr-trend-analysis/` | Phase 1 |
| 研究产出模板 | `09_runbooks/templates/` | Phase 0 |

**验收标准**：
- smr-researcher 能产出一份完整的行业研报（含 thesis + 催化剂）
- smr-analyst 能基于因子数据产出趋势判断报告
- 美股联动分析能正确映射 NVDA→中际旭创 等供应链关系
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
- smr-advisor 能产出包含 thesis、催化剂时间线、建仓计划、目标价/止损的推荐
- smr-portfolio-mgr 能记录持仓并计算盈亏
- 推荐中包含预期持仓周期（周/月/季）
- 所有推荐附带免责声明

### Phase 4：风控与报告（2-3天）

**目标**：实现风控监控和报告推送

| 任务 | 产出 | 依赖 |
|------|------|------|
| smr-risk-controller SOUL + AGENTS | 风控官人格与行为规范 | Phase 3 |
| smr-brief-writer SOUL + AGENTS | 简报撰写人格与行为规范 | Phase 3 |
| 风控引擎脚本 | `08_scripts/risk_engine/monitor.py` | Phase 1 |
| thesis证伪检测 Skill | `09_runbooks/skills/smr-thesis-check/` | Phase 3 |
| 日报 Skill | `09_runbooks/skills/smr-daily-brief/` | Phase 3 |
| 周报 Skill | `09_runbooks/skills/smr-weekly-brief/` | Phase 3 |
| 微信推送（独立实例） | 复用桥接架构，独立 outbox | Phase 3 |
| 全量 cron job 配置 | 每日运行时间线 | 全部 |

**验收标准**：
- 风控引擎能在回撤超限时触发预警
- thesis证伪检测能识别逻辑变化
- smr-brief-writer 能自动产出日报（含美股联动分析）
- 日报能推送到微信（草稿箱）

### Phase 5：联调与优化（2-3天）

**目标**：端到端联调，优化体验

| 任务 | 产出 | 依赖 |
|------|------|------|
| 端到端联调 | 完整流程跑通 | Phase 4 |
| 性能优化 | 数据采集/因子计算耗时优化 | 联调 |
| 异常处理 | 网络超时、数据缺失、API限流 | 联调 |
| 回测验证 | 至少一个中长线策略的回测报告 | Phase 4 |
| VCR认知复用验证 | 确认能正确读取VCR产出 | 联调 |

**验收标准**：
- 从数据采集到日报推送的完整链路无人工干预
- 连续 3 个交易日稳定运行
- 无数据丢失、无风控误报
- VCR project_cards 变化能触发 SMR 研究

---

## 十、技术选型与依赖

### 10.1 Python 依赖

```
akshare>=1.12          # A+H股数据采集（免费）
tushare>=1.4           # 补充数据源
pandas>=2.0            # 数据处理
numpy>=1.24            # 数值计算
vectorbt>=0.26         # 向量化回测（比backtrader更适合中长线）
matplotlib>=3.7        # 图表生成
jinja2>=3.1            # 模板渲染
yfinance>=0.2          # 美股行情（免费）
beautifulsoup4>=4.12   # 网页解析（IR页面/纪要）
sec-edgar-downloader>=5.0  # SEC财报下载
```

### 10.2 不引入的依赖

| 不使用 | 原因 |
|--------|------|
| Django/Flask | 不需要 Web 服务 |
| Redis | 数据量小，SQLite 足够 |
| Docker | 单机部署 |
| PostgreSQL | SQLite 足够 |
| qlib | 过重，自建因子即可 |
| TA-Lib | 中长线用pandas计算MA/MACD即可，无需TA-Lib |
| 任何高频交易框架 | 不做高频 |

### 10.3 与现有系统的技术栈对比

| 维度 | VCR/MCT | SMR |
|------|---------|-----|
| 数据存储 | Markdown文件 | SQLite + Markdown |
| 脚本语言 | Python 3 | Python 3 |
| 数据源 | RSS/网页抓取 | AkShare/Tushare/yfinance/SEC EDGAR |
| 推送渠道 | 微信公众号 | 微信公众号（独立实例） |
| Agent框架 | OpenClaw | OpenClaw |
| 调度方式 | OpenClaw cron | OpenClaw cron |
| 交易风格 | N/A | 中长线趋势（周~季级持仓） |

---

## 十一、风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| AkShare/Tushare API 限流 | 中 | 数据采集中断 | 多数据源降级 |
| 美股信号采集被反爬 | 中 | 联动分析缺失 | 降低频率+缓存+公开渠道优先 |
| 中长线判断错误 | 高 | 持仓亏损 | 严格thesis+止损，逻辑证伪即止损 |
| 前沿科技赛道波动大 | 高 | 短期大幅回撤 | 风控阈值适配（20%回撤线） |
| 与现有业务线冲突 | 低 | 资源竞争 | 完全隔离设计 |
| VCR认知复用失效 | 低 | 研究质量下降 | SMR有独立研究能力，VCR只是辅助输入 |
| 回测过拟合 | 高 | 策略实盘失效 | 样本外验证，多周期回测 |

---

## 十二、后续扩展方向（Phase 6+）

1. **VCR-SMR双向联动**：SMR二级市场发现→反向输入VCR一级市场判断
2. **ETF策略**：半导体ETF、机器人ETF轮动，降低个股风险
3. **可转债分析**：前沿科技赛道可转债下修博弈
4. **港股IPO跟踪**：VCR关注的一级市场项目赴港IPO时的打新策略
5. **飞书实时推送**：美股盘后重大事件通过飞书推送
6. **产业链图谱**：自动构建美股→A+H的供应链映射图谱
7. **机器学习辅助**：LightGBM因子挖掘（仅辅助，不替代研究判断）

---

## 附录A：SMR Cron Job 清单（规划）

| Job名称 | Agent | 频率 | 说明 |
|---------|-------|------|------|
| SMR-美股行情采集 | smr-analyst | 06:00 | 美股收盘后采集 |
| SMR-A+H行情采集 | smr-analyst | 15:30 | A股收盘后采集 |
| SMR-H股行情采集 | smr-analyst | 16:30 | 港股收盘后采集 |
| SMR-因子计算 | smr-analyst | 16:30 | 趋势+基本面+联动因子 |
| SMR-美股财报监控 | smr-analyst | 08:00 | 检查是否有新财报/纪要 |
| SMR-盘前简报 | smr-brief-writer | 09:00 | 含美股联动分析 |
| SMR-持仓复盘 | smr-portfolio-mgr | 19:30 | 持仓盈亏+thesis检查 |
| SMR-日报撰写 | smr-brief-writer | 20:30 | 每日市场复盘 |
| SMR-周报撰写 | smr-brief-writer | 周六10:00 | 每周总结 |
| SMR-风控日报 | smr-risk-controller | 21:00 | 盘后风控检查 |
| SMR-次日计划 | smr-lead | 22:00 | 次日研究/操作计划 |
| SMR-财务数据更新 | smr-analyst | 周六08:00 | 每周财务数据 |

## 附录B：SMR 与现有系统零交叉检查清单

- [ ] SMR agent ID 全部使用 `smr-` 前缀
- [ ] SMR workspace 路径全部在 `/Users/apple/.openclaw/workspace-smr-*/`
- [ ] SMR 数据目录全部在 `/Users/apple/Documents/同行资本二级市场部门/二级市场系统/`
- [ ] SMR agent 不与 VCR/MCT agent 互通（agentToAgent 独立分组）
- [ ] SMR cron job 的 `name` 全部使用 `SMR-` 前缀
- [ ] SMR 不使用现有飞书 bot 账号
- [ ] SMR 不写入 VCR/MCT 的任何目录（只读 VCR project_cards）
- [ ] SMR 的微信桥接使用独立 outbox 目录
- [ ] SMR 的 SQLite 数据库与 VCR/MCT 完全独立
- [ ] SMR 的 Python 脚本不 import VCR/MCT 的任何模块

## 附录C：SMR 标的宇宙（初始配置）

### A股前沿科技标的（约50只）

**具身智能/机器人**：绿的谐波(688017)、汇川技术(300124)、拓普集团(601689)、三花智控(002050)、鸣志电器(603728)、中大力德(002796)、丰立智能(301368)、奥比中光(688322)、优必选(9880.HK)、领益智造(002600)、卧龙电驱(600580)

**半导体/算力**：海光信息(688041)、寒武纪(688256)、中际旭创(300308)、新易盛(300502)、天孚通信(300394)、光迅科技(002281)、光库科技(300620)、澜起科技(688008)、华大九天(301269)、芯原股份(688521)、兆易创新(603986)、曙光数创(872808)、英维克(002837)

**AI/软件**：科大讯飞(002230)、金山办公(688111)、商汤-W(0020.HK)、泛微网络(603039)

**量子**：国盾量子(688027)

### H股前沿科技标的（约10只）

优必选(9880.HK)、商汤-W(0020.HK)、科大讯飞(002230.HK, 如有)、中芯国际(0981.HK)、华虹半导体(1347.HK)

### 美股对标标的（约15只，仅跟踪不投资）

**GPU/算力**：NVDA、AMD、INTC、AVGO
**光互连**：LITE、MRVL、COHR
**机器人**：TSLA
**量子**：IONQ、RGTI、QBTS
**AI应用**：CRM、NOW、MSFT
**存储**：MU
