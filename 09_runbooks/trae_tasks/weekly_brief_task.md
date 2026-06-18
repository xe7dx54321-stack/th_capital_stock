# TRAE 周报自动化任务模板

> 本模板用于 TRAE 执行每周周报撰写任务。
> **执行时间**：每周五 20:00
> **执行前提**：本周所有日报已完成
> **执行前必读**：smr-trae-playbook.md

---

## 任务目标

生成周度总结报告，包含本周组合表现、最佳/最差持仓、Thesis 回顾、行业板块轮动、美股联动回顾、研究管线、下周展望七大章节。

## 执行步骤

### Step 1：收集本周数据

#### 1.1 查询本周日报

```bash
# 列出本周所有日报
ls th_capital_stock/06_reports/daily/*.md
```

#### 1.2 查询本周持仓复盘

```bash
# 列出本周所有复盘报告
ls th_capital_stock/04_portfolio/performance/*.md
```

#### 1.3 查询本周风险说明

```bash
# 列出本周所有风险说明
ls th_capital_stock/05_risk/alerts/*.md
```

#### 1.4 查询持仓（计算周收益）

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
positions = conn.execute('''
    SELECT p.*, d.close as current_price
    FROM position p
    LEFT JOIN daily_bar d ON p.ts_code = d.ts_code AND d.trade_date = (
        SELECT MAX(trade_date) FROM daily_bar WHERE ts_code = p.ts_code
    )
    WHERE p.status = 'open'
    ORDER BY p.entry_date DESC
''').fetchall()
print(json.dumps([dict(r) for r in positions], ensure_ascii=False))
"
```

#### 1.5 查询本周 registry 快照

```bash
python -c "
import sqlite3, json
from datetime import datetime, timedelta

conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row

# 本周开始日期（假设周一是本周开始）
today = datetime.now()
week_start = today - timedelta(days=today.weekday())
week_start_str = week_start.strftime('%Y-%m-%d')

entries = conn.execute('''
    SELECT * FROM task_registry_entry
    WHERE created_at >= ?
    ORDER BY created_at DESC
''', (week_start_str,)).fetchall()
print(json.dumps([dict(r) for r in entries], ensure_ascii=False))
"
```

### Step 2：分析数据

#### 2.1 计算周收益

从本周复盘报告和日报中汇总：
- 每日盈亏变化
- 周度总盈亏

#### 2.2 找出最佳/最差持仓

| 类型 | 条件 | 数据来源 |
|------|------|----------|
| 最佳持仓 | 周涨幅最大 | 复盘报告/daily_bar |
| 最差持仓 | 周跌幅最大 | 复盘报告/daily_bar |

#### 2.3 Thesis 状态汇总

从 registry 快照中汇总：
- 有无 thesis 状态变化
- 变化原因

#### 2.4 行业板块表现

汇总本周各板块涨跌，从日报中提取。

#### 2.5 美股联动回顾

从日报中汇总本周美股主要标的涨跌及对 A+H 的影响。

### Step 3：生成周报

```markdown
---
report_type: weekly_brief
week_ending: {YYYY-MM-DD}
created_at: {YYYY-MM-DD HH:MM:SS}
week_number: {week_number}
week_range: {YYYY-MM-DD} 至 {YYYY-MM-DD}
---

# 同行资本二级市场周报 — 第{week_number}周（{YYYY-MM-DD} 至 {YYYY-MM-DD}）

## 一、本周组合表现

| 指标 | 数值 |
|------|------|
| 组合周收益 | {收益}% |
| 同期上证指数 | {上证涨跌幅}% |
| 同期科创50 | {科创50涨跌幅}% |
| 超额收益 | {超额}% |
| 持仓数量 | {N} |
| 本周交易次数 | {N} |

{本周盈亏变化分析}

## 二、最佳/最差持仓

| 类型 | 股票 | 周涨跌 | 原因 |
|------|------|--------|------|
| 最佳 | {代码} | {涨}% | {原因} |
| 最差 | {代码} | {跌}% | {原因} |

{最佳/最差持仓详细分析}

## 三、Thesis回顾

| 股票 | Thesis | 状态 | 变化 |
|------|--------|------|------|
{每笔持仓一行}

### 本周Thesis变化详情

{如果有 thesis 状态发生变化的持仓，详细说明：
- 变化前后的状态
- 变化原因
- 对持仓的影响}

{如果没有变化，说明"本周各持仓 thesis 均维持 INTACT 状态"}

## 四、行业板块轮动

| 板块 | 本周涨跌 | 趋势判断 | 下周展望 |
|------|---------|---------|---------|
| 具身智能 | {涨}% | {趋势} | {展望} |
| 半导体/算力 | {涨}% | {趋势} | {展望} |
| 光模块/CPO | {涨}% | {趋势} | {展望} |
| AI应用 | {涨}% | {趋势} | {展望} |
| 量子 | {涨}% | {趋势} | {展望} |

{各板块本周表现分析}

## 五、美股联动回顾

| 美股标的 | 本周涨跌 | 对A+H影响 |
|---------|---------|-----------|
| NVDA | {涨}% | {影响} |
| TSLA | {涨}% | {影响} |
| AMD | {涨}% | {影响} |
| MSFT | {涨}% | {影响} |

{本周美股表现及对组合的影响分析}

## 六、研究管线

### 本周完成的研究

{从 registry 中汇总本周完成的研究}
- {研究名称}（{YYYY-MM-DD}）

### 进行中的研究

{从 registry 中汇总进行中的研究}
- {研究名称}（预计完成：{日期}）

### 待触发的研究

{从 registry 中汇总待触发的研究}
- {研究名称}

## 七、下周展望

### 关键事件日历

| 日期 | 事件 | 影响标的 |
|------|------|---------|
| {日期} | {事件} | {标的} |

### 研究优先级

1. {优先级1}
2. {优先级2}
3. {优先级3}

### 持仓调整考虑

{基于本周复盘和下周展望，列出持仓调整考虑：
1. 哪些持仓需要重点关注
2. 是否有新的调仓计划
3. 风险防范重点}

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
```

### Step 4：写入文件

Write 到 `th_capital_stock/06_reports/weekly/weekly_{YYYY-MM-DD}.md`

### Step 5：注册快照

```bash
python th_capital_stock/08_scripts/registry/register_snapshot.py \
    --entity-type weekly_report_candidate \
    --entity-id {YYYYMMDD} \
    --status completed \
    --source TRAE_Weekly_Brief \
    --payload "{\"report_path\": \"th_capital_stock/06_reports/weekly/weekly_{YYYY-MM-DD}.md\", \"week_range\": \"{YYYY-MM-DD} 至 {YYYY-MM-DD}\", \"entities_covered\": \"daily_reports,reviews,risk_notes\"}"
```

---

## 质量检查清单

生成周报后，请检查：

- [ ] 本周所有日期都有日报引用
- [ ] 收益计算正确（带正负号）
- [ ] 最佳/最差持仓有涨跌数据
- [ ] Thesis 回顾覆盖所有持仓
- [ ] 行业板块有具体涨跌数据
- [ ] 下周展望有具体内容
- [ ] 包含完整的免责声明
- [ ] frontmatter 完整（report_type、week_ending、created_at、week_number、week_range）

## 错误处理

- 如果某日日报缺失：在周报中标注"部分数据缺失"，不影响其他内容
- 如果无法计算收益：用已有数据估算，标注"估算值"
- 如果 thesis 信息缺失：标注"thesis 待确认"

---

## 输出确认

完成后请确认：
1. 周报文件已写入正确目录
2. 快照已注册到 registry
3. 周报命名符合约定（`weekly_YYYY-MM-DD.md`）
