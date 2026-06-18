# TRAE 日报自动化任务模板

> 本模板用于 TRAE 执行每日日报撰写任务。
> **执行时间**：每日 20:30
> **执行前提**：当日行情数据已采集完成（参考 smr-daily-brief-workflow.md）
> **执行前必读**：smr-trae-playbook.md

---

## 任务目标

生成当日市场简报，包含美股隔夜动态、A+H 市场概况、持仓盈亏、风控状态、研究进展、明日关注六大章节。

## 执行步骤

### Step 1：执行数据脚本

```bash
# 更新盈亏
cd d:\李少博的文件\TH_Capital_二级市场
python th_capital_stock/08_scripts/portfolio/pnl.py
```

### Step 2：执行风控检查

```bash
# 风控检查
python th_capital_stock/08_scripts/risk_engine/monitor.py
```

### Step 3：读取数据

#### 3.1 查询持仓

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
positions = conn.execute('''
    SELECT p.*, d.close as current_price, d.pct_chg
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

#### 3.2 查询风险告警

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
alerts = conn.execute('''
    SELECT * FROM risk_alert
    WHERE acknowledged = 0
    ORDER BY alert_time DESC
    LIMIT 10
''').fetchall()
print(json.dumps([dict(r) for r in alerts], ensure_ascii=False))
"
```

#### 3.3 查询股票池

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
pool = conn.execute('''
    SELECT * FROM stock_pool_current
    WHERE pool_type IN ('recommended', 'candidate')
    ORDER BY score DESC
''').fetchall()
print(json.dumps([dict(r) for r in pool], ensure_ascii=False))
"
```

#### 3.4 查询最新美股信号

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
signals = conn.execute('''
    SELECT * FROM us_signal
    ORDER BY signal_time DESC
    LIMIT 20
''').fetchall()
print(json.dumps([dict(r) for r in signals], ensure_ascii=False))
"
```

### Step 4：生成日报内容

基于以上数据，按以下模板生成日报（请用实际数据替换 {} 中的内容）：

```markdown
---
report_type: daily_brief
date: {YYYY-MM-DD}
created_at: {YYYY-MM-DD HH:MM:SS}
---

# 同行资本二级市场日报 — {YYYY-MM-DD}

## 一、美股隔夜动态

### 核心标的变动

| Symbol | Close | Chg% | Key Signal |
|--------|-------|------|------------|
| NVDA | {收盘价} | {涨跌幅} | {关键信号} |
| TSLA | {收盘价} | {涨跌幅} | {关键信号} |
| AMD | {收盘价} | {涨跌幅} | {关键信号} |
| MSFT | {收盘价} | {涨跌幅} | {关键信号} |

### 对A+H影响预判

{基于美股表现，分析对A股和港股相关标的的影响。重点关注：
1. 具身智能板块：TSLA 表现对 A 股机器人板块的影响
2. 半导体板块：NVDA/AMD 表现对 A 股半导体的影响
3. 光模块板块：相关美股表现对 CPO/光模块板块的影响}

## 二、A股+H股市场概况

### 主要指数

| Index | Close | Chg% |
|-------|-------|------|
| 上证指数 | {收盘} | {涨跌幅} |
| 科创50 | {收盘} | {涨跌幅} |
| 恒生科技 | {收盘} | {涨跌幅} |

### SMR关注板块表现

| Sector | Chg% | Leading Stock | Notes |
|--------|------|---------------|-------|
| 具身智能 | {涨跌} | {领涨股} | {简评} |
| 半导体/算力 | {涨跌} | {领涨股} | {简评} |
| 光模块/CPO | {涨跌} | {领涨股} | {简评} |
| AI应用 | {涨跌} | {领涨股} | {简评} |
| 量子 | {涨跌} | {领涨股} | {简评} |

## 三、持仓盈亏

| Stock | Entry | Current | PnL% | Thesis Status |
|-------|-------|---------|------|---------------|
{每笔持仓一行，根据数据库数据填写}

## 四、风控状态

- 组合回撤: {回撤比例}%
- 仓位分布: {各标的仓位}
- 预警: {无/有 - 描述预警内容}

{如果有关键预警，详细说明}

## 五、研究进展

{根据 stock_pool_current 和 registry 中的研究记录，总结当日研究进展：
1. 是否有新的推荐/降级
2. 是否有 thesis 状态变化
3. 是否有新的研究发现}

## 六、明日关注

{基于当日分析，列出明日需要重点关注的事项：
1. 重要事件（日历）
2. 重点持仓调整考虑
3. 潜在机会/风险点}

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
```

### Step 5：写入文件

Write 到 `th_capital_stock/06_reports/daily/{YYYY-MM-DD}_盘前简报.md`

### Step 6：注册快照

```bash
python th_capital_stock/08_scripts/registry/register_snapshot.py \
    --entity-type daily_report_candidate \
    --entity-id {YYYYMMDD} \
    --status completed \
    --source TRAE_Daily_Brief \
    --payload "{\"report_path\": \"th_capital_stock/06_reports/daily/{YYYY-MM-DD}_盘前简报.md\", \"entities_covered\": \"positions,alerts,pool,us_signals\"}"
```

---

## 质量检查清单

生成日报后，请检查：

- [ ] 所有表格都有数据（无空白单元格）
- [ ] 涨跌数据有正负号（跌用负数）
- [ ] 持仓盈亏有正负号（亏用负数）
- [ ] 风控状态明确（有/无预警）
- [ ] 明日关注有具体内容
- [ ] 包含完整的免责声明
- [ ] frontmatter 完整（report_type、date、created_at）

## 错误处理

- 如果 pnl.py 或 monitor.py 执行失败：记录错误，继续生成日报，在报告中注明"部分数据待补"
- 如果数据库查询失败：用已获取的数据生成报告，标注"部分数据缺失"
- 如果生成失败：发送通知，保留错误日志

---

## 输出确认

完成后请确认：
1. 日报文件已写入正确目录
2. 快照已注册到 registry
3. 文件命名符合约定（`YYYY-MM-DD_盘前简报.md`）
