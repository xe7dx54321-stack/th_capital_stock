# SMR TRAE 业务知识库

> 本文档是 TRAE 执行 SMR（二级市场研究自动化系统）业务流程的核心参考手册。
> 包含所有业务逻辑、目录约定、数据库结构、状态传递机制和关键参数。
> **TRAE 在执行任何任务前必须阅读本文档。**

---

## 一、项目概述

### 1.1 SMR 是什么

SMR（Structured Market Research）是同行资本二级市场研究自动化系统，面向前沿科技赛道：
- **A 股**：具身智能/机器人、半导体/算力、光模块/CPO、AI 应用、量子
- **H 股**：阿里巴巴-W、中芯国际、华虹半导体、优必选、商汤
- **美股**：仅作对标跟踪，不直接投资（NVDA/AMD/TSLA/CRM/NOW/MSFT 等）

### 1.2 技术栈

| 维度 | 选型 |
|------|------|
| 数据存储 | SQLite（`01_data/db/smr.db`） |
| 知识载体 | Markdown + YAML frontmatter |
| 行情数据 | akshare（A/H 股）、yfinance（美股） |
| 脚本语言 | Python 3.11+ |
| 项目根目录 | `SMR_ROOT` 环境变量，或 `d:\李少博的文件\TH_Capital_二级市场` |

### 1.3 TRAE 与 SMR 的关系

- **TRAE 是大脑**：负责智能判断任务（写报告、审核 thesis、生成建议）
- **Python 脚本是手脚**：负责确定性任务（采集数据、计算因子、更新盈亏）
- **状态传递靠 SQLite**：所有任务完成后必须通过 `register_snapshot` 写入 `task_registry_entry` 表

---

## 二、目录结构与约定

### 2.1 目录速查表

```
th_capital_stock/
├── 01_data/
│   └── db/smr.db                    # SQLite 主数据库（必须）
├── 02_research/                     # 研究报告
├── 03_stock_pool/                   # 股票池产物
│   └── watchlist/
├── 04_portfolio/                   # 组合产物
│   └── performance/                # 复盘报告
├── 05_risk/                        # 风险告警
│   └── alerts/                     # 风险说明文件
├── 06_reports/                     # 报告产物
│   ├── daily/                      # 日报（命名：YYYY-MM-DD_日报名.md）
│   └── weekly/                     # 周报
├── 08_scripts/                     # 脚本入口
│   ├── lib/                        # 核心库（smr_*.py）
│   ├── portfolio/                  # 组合脚本
│   │   ├── pnl.py                 # 盈亏更新
│   │   └── entry.py                # 建仓
│   ├── risk_engine/
│   │   └── monitor.py              # 风控检查
│   ├── data_harvester/
│   │   └── ah_daily_bar.py         # 行情采集
│   ├── factor_engine/
│   │   ├── trend.py                # 趋势因子
│   │   ├── fundamental.py          # 基本面因子
│   │   └── us_linkage.py           # 美股联动因子
│   ├── registry/
│   │   ├── register_snapshot.py    # 注册快照（必须调用）
│   │   └── query_registry.py       # 查询快照
│   └── jobs/                       # 数据摄入
│       ├── ingest_news.py           # 新闻摄入
│       └── ingest_filings.py       # 公告摄入
├── 09_runbooks/
│   ├── templates/                   # 报告模板
│   └── skills/                     # SKILL 定义
├── 11_smr_wiki/                   # 知识库
│   ├── drafts/ingest/              # 草稿
│   └── wiki/                       # 正式知识页
└── 00_control/                    # 策略配置
    ├── portfolio_policy.json       # 组合风控参数
    ├── data_freshness_rules.json   # 数据新鲜度规则
    └── watchlist_registry.md       # 种子标的
```

### 2.2 文件命名约定

| 产物 | 命名格式 | 示例 |
|------|----------|------|
| 日报 | `YYYY-MM-DD_日报名.md` | `2026-06-18_盘前简报.md` |
| 周报 | `weekly_YYYY-MM-DD.md` | `weekly_2026-06-15.md` |
| 风险说明 | `YYYY-MM-DD_risk_note.md` | `2026-06-18_risk_note.md` |
| 复盘报告 | `daily_YYYY-MM-DD.md` | `daily_2026-06-18.md` |
| Wiki 草稿 | `draft_{date}_{category}.md` | `draft_20260618_stock.md` |

---

## 三、数据库结构

### 3.1 核心表速查

| 表名 | 主键 | 用途 |
|------|------|------|
| `daily_bar` | `(ts_code, trade_date)` | A/H 股日 K 线 |
| `us_daily_bar` | `(symbol, trade_date)` | 美股日 K 线 |
| `position` | `(ts_code, entry_date)` | 持仓 |
| `risk_alert` | `alert_id` | 风险告警 |
| `stock_pool` | `(pool_type, ts_code, added_date)` | 股票池事件（append-only） |
| `research_decision` | `report_id` | 研究决策 |
| `factor_daily` | `(ts_code, trade_date, factor_name)` | 日频因子 |
| `us_signal` | `signal_id` | 美股信号 |

### 3.2 关键视图

| 视图名 | 用途 |
|--------|------|
| `stock_pool_current` | 当前活跃股票池（status='active'） |
| `stock_pool_latest` | 按标的取最新池状态 |
| `task_registry_entity_latest` | 所有实体的最新快照 |

### 3.3 TRAE 读取数据的标准方式

```python
# 通过 RunCommand 执行 SQL 查询
python -c "
import sqlite3, json
conn = sqlite3.connect('01_data/db/smr.db')
conn.row_factory = sqlite3.Row

# 查询持仓
positions = conn.execute('''
    SELECT * FROM position 
    WHERE status = 'open'
    ORDER BY entry_date DESC
''').fetchall()
print(json.dumps([dict(r) for r in positions], ensure_ascii=False))

# 查询风险告警
alerts = conn.execute('''
    SELECT * FROM risk_alert 
    WHERE acknowledged = 0 
    ORDER BY alert_time DESC
''').fetchall()
print(json.dumps([dict(r) for r in alerts], ensure_ascii=False))
"
```

---

## 四、组合风控参数（必须遵守）

来自 `00_control/portfolio_policy.json`：

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_single_position_pct` | 25% | 单票最大仓位 |
| `max_sector_concentration_pct` | 50% | 行业最大集中度 |
| `max_total_exposure_pct` | 90% | 总最大暴露 |
| `max_drawdown_pct` | 20% | 最大回撤 |
| `max_weekly_loss_pct` | 8% | 单周最大亏损 |
| `buy_score_strong` | 75 | 强买入评分阈值 |
| `buy_score_probe` | 62 | 试探买入评分阈值 |
| `sell_score_exit` | 60 | 卖出评分阈值 |

### 4.1 风险等级

| 等级 | 触发条件 | 处理要求 |
|------|----------|----------|
| warning | 超过任一参数阈值 | 24 小时内处理 |
| critical | 回撤 >15%、单周亏损 >8% | 4 小时内处理 |

---

## 五、状态传递机制

### 5.1 核心原则

**每个任务完成后必须调用 `register_snapshot.py` 写入状态。这是流程不中断的关键。**

### 5.2 register_snapshot 标准调用

```bash
python 08_scripts/registry/register_snapshot.py \
    --entity-type daily_report_candidate \
    --entity-id 20260618 \
    --status completed \
    --source TRAE_daily_Brief \
    --payload '{"report_path": "06_reports/daily/2026-06-18_盘前简报.md", "entities_covered": 5}'
```

### 5.3 常用 entity_type

| entity_type | 含义 | 通常的下一个消费者 |
|-------------|------|------------------|
| `daily_reporting_snapshot` | 日报快照 | 日报撰写 |
| `daily_report_candidate` | 日报候选 | 人工确认/发布 |
| `risk_monitor_snapshot` | 风控快照 | 风控检查 |
| `portfolio_pnl_snapshot` | 盈亏快照 | 持仓复盘 |
| `research_decision_snapshot` | 研究决策快照 | 股票池更新 |
| `wiki_draft` | Wiki 草稿 | 人工审核 |

### 5.4 TRAE 读取状态的流程

```
1. RunCommand 查询 SQLite：
   python -c "
   from smr_registry import get_entity_snapshot
   import sqlite3
   conn = sqlite3.connect('01_data/db/smr.db')
   snapshot = get_entity_snapshot(conn, 'daily_reporting_snapshot', limit=1)
   print(snapshot)
   "

2. 解析 payload 获取下游需要的信息
3. 执行任务
4. 调用 register_snapshot 写入结果
5. 下一个任务自动接续
```

---

## 六、五大业务流程（TRAE 核心执行范围）

### 6.1 日报流程（每日 20:30）

**目标**：生成当日市场简报

**步骤**：
1. RunCommand: `python 08_scripts/portfolio/pnl.py`（更新盈亏）
2. RunCommand: `python 08_scripts/risk_engine/monitor.py`（风控检查）
3. 查询 SQLite 获取最新数据（行情、持仓、告警、研究）
4. 按模板撰写日报（六大章节）
5. Write 写入 `06_reports/daily/{date}_盘前简报.md`
6. RunCommand: register_snapshot（entity_type=`daily_report_candidate`）

**输出格式**：见 `09_runbooks/templates/daily_brief.md`

### 6.2 风控检查（每日 21:00）

**目标**：检查持仓风险，生成风险说明

**步骤**：
1. RunCommand: `python 08_scripts/risk_engine/monitor.py`（生成告警）
2. 查询 SQLite 获取 risk_alert 和 position 数据
3. 按风控参数检查（单票 25%、回撤 20%、行业 50% 等）
4. 判断是否有 warning/critical 告警：
   - 有：生成详细风险说明 + 建议动作
   - 无：确认各指标在安全范围内
5. Write 写入 `05_risk/alerts/{date}_risk_note.md`
6. RunCommand: register_snapshot（entity_type=`risk_update_candidate`）

**重要**：warning 需 24 小时内处理，critical 需 4 小时内处理。

### 6.3 持仓复盘（每日 19:30）

**目标**：复盘当日持仓，产出调仓建议

**步骤**：
1. RunCommand: `python 08_scripts/portfolio/pnl.py`（更新盈亏）
2. 查询 SQLite 获取所有 open 状态的持仓
3. 对每笔持仓检查：
   - 当前盈亏是否触及止损/目标
   - Thesis 是否仍然成立（行业/公司/美股联动）
4. 产出调仓建议：
   - thesis 证伪 → 无条件止损
   - 触及止损 → 止损
   - 触及目标 → 分批止盈
   - thesis 减弱 → 减仓观察
   - thesis 完好 → 维持
5. 检查组合约束（单票 ≤25%、行业 ≤50%、总暴露 ≤90%）
6. Write 写入 `04_portfolio/performance/daily_{date}.md`
7. RunCommand: register_snapshot（entity_type=`portfolio_review_snapshot`）

### 6.4 周报流程（每周五 20:00）

**目标**：生成周度总结

**步骤**：
1. 收集本周所有日报、复盘报告、风险说明
2. 汇总本周数据：
   - 组合周收益 vs 上证/科创50
   - 最佳/最差持仓
   - Thesis 状态变化
   - 行业板块轮动
   - 美股联动回顾
3. 按模板撰写周报（七大章节）
4. Write 写入 `06_reports/weekly/weekly_{date}.md`
5. RunCommand: register_snapshot（entity_type=`weekly_report_candidate`）

**输出格式**：见 `09_runbooks/templates/weekly_brief.md`

### 6.5 Thesis 检查（每日开盘前）

**目标**：检查持仓 thesis 是否仍然成立

**步骤**：
1. 查询 SQLite 获取所有 open 持仓
2. 对每笔持仓检查：
   - 行业层面：行业趋势是否如预期？
   - 公司层面：基本面是否有重大变化？
   - 美股联动：美股对标是否有重大事件？
3. 判断 thesis 状态：
   - INTACT（完好）：继续持有
   - WEAKENED（减弱）：减仓 30-50%
   - BROKEN（证伪）：立即退出
   - PLAYED_OUT（演绎完毕）：按计划止盈
4. 如有状态变化，Write 写入 `04_portfolio/performance/thesis_review_{date}.md`
5. RunCommand: register_snapshot

---

## 七、TRAEE 执行规范

### 7.1 标准工作流

```
1. 【读取状态】用 RunCommand + SQL 查询当前系统状态
2. 【执行脚本】用 RunCommand 调用确定性 Python 脚本
3. 【生成内容】基于模板生成报告/建议
4. 【写入文件】用 Write 工具写入正确目录
5. 【注册状态】用 RunCommand 调用 register_snapshot.py
6. 【交接下游】流程自动流转到下一个工序
```

### 7.2 禁止事项

- ❌ 禁止跳过 register_snapshot
- ❌ 禁止写入非约定目录
- ❌ 禁止直接修改 SQLite（只能用 register_snapshot）
- ❌ 禁止删除已有文件（只新增，不覆盖）

### 7.3 错误处理

- 如果 RunCommand 失败：记录错误，重试 1 次，仍失败则跳过该步骤并在报告中注明
- 如果数据缺失：在报告中标注"数据待补"，不影响其他内容生成
- 如果生成失败：立即通知，并保留错误日志

### 7.4 质量要求

- 所有报告必须包含风险提示与免责声明
- 数据必须有来源（注明数据表或脚本名称）
- 判断必须有依据（说明判断理由）
- 调仓建议必须量化（目标价格、仓位比例）

---

## 八、报告模板

### 8.1 日报模板

见 `09_runbooks/templates/daily_brief.md`

### 8.2 周报模板

见 `09_runbooks/templates/weekly_brief.md`

### 8.3 风险说明模板

```markdown
---
report_type: risk_note
date: {date}
severity: warning/critical
---

# 风险说明 — {date}

## 风险类型
{类型：单票集中度/回撤/行业集中度/Thesis证伪}

## 当前状态
{描述当前状态}

## 阈值对比
| 指标 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|

## 影响分析
{分析风险对组合的影响}

## 建议动作
{具体建议}

## 处理期限
{warning: 24小时 / critical: 4小时}

---
⚠️ 风险提示：本内容仅供研究参考，不构成投资建议。
```

### 8.4 复盘报告模板

```markdown
---
report_type: portfolio_review
date: {date}
---

# 持仓复盘 — {date}

## 持仓状态汇总

| Stock | Entry | Current | PnL% | Thesis | Status | Action |
|-------|-------|---------|-------|--------|--------|--------|

## 调仓动作

### 建议止损
{股票} — {理由} — {价格}

### 建议止盈
{股票} — {理由} — {目标价}

### 建议减仓
{股票} — {理由} — {目标仓位}

## 组合约束检查

| 约束 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|

## 下日关注

- 

---
⚠️ 风险提示：本内容仅供研究参考，不构成投资建议。
```

---

## 九、快捷命令参考

```bash
# 更新盈亏
python 08_scripts/portfolio/pnl.py

# 风控检查
python 08_scripts/risk_engine/monitor.py

# 行情采集
python 08_scripts/data_harvester/ah_daily_bar.py --days 5

# 查询持仓
python -c "import sqlite3,json; conn=sqlite3.connect('01_data/db/smr.db'); print(json.dumps([dict(r) for r in conn.execute('SELECT * FROM position WHERE status=\"open\"').fetchall()], ensure_ascii=False))"

# 查询告警
python -c "import sqlite3,json; conn=sqlite3.connect('01_data/db/smr.db'); print(json.dumps([dict(r) for r in conn.execute('SELECT * FROM risk_alert WHERE acknowledged=0').fetchall()], ensure_ascii=False))"

# 查询股票池
python -c "import sqlite3,json; conn=sqlite3.connect('01_data/db/smr.db'); print(json.dumps([dict(r) for r in conn.execute('SELECT * FROM stock_pool_current').fetchall()], ensure_ascii=False))"

# 注册快照
python 08_scripts/registry/register_snapshot.py --entity-type {type} --entity-id {id} --status completed --source TRAE_{task}
```

---

*文档版本：1.0*
*最后更新：2026-06-18*
