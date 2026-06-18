# TRAE 持仓复盘任务模板

> 本模板用于 TRAE 执行每日持仓复盘任务。
> **执行时间**：每日 19:30
> **执行前提**：当日行情数据已采集
> **执行前必读**：smr-trae-playbook.md

---

## 任务目标

复盘当日持仓状态，检查 thesis 是否仍然成立，产出调仓建议。

## 执行步骤

### Step 1：更新盈亏

```bash
cd d:\李少博的文件\TH_Capital_二级市场
python th_capital_stock/08_scripts/portfolio/pnl.py
```

### Step 2：读取数据

#### 2.1 查询持仓

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
positions = conn.execute('''
    SELECT p.*, d.close as current_price, d.pct_chg, d.trade_date as price_date
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

#### 2.2 查询持仓 thesis

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
decisions = conn.execute('''
    SELECT d.*, p.ts_code
    FROM research_decision_latest d
    JOIN position p ON d.ts_code = p.ts_code
    WHERE p.status = 'open'
''').fetchall()
print(json.dumps([dict(r) for r in decisions], ensure_ascii=False))
"
```

#### 2.3 查询股票池（用于 sector 信息）

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
pool = conn.execute('''
    SELECT * FROM stock_pool_current
    WHERE status = 'active'
''').fetchall()
print(json.dumps([dict(r) for r in pool], ensure_ascii=False))
"
```

### Step 3：对每笔持仓进行复盘分析

对每笔 open 状态的持仓，完成以下检查：

#### 3.1 盈亏状态

计算：
- 当前盈亏金额 = (当前价 - 成本价) × 股数
- 当前盈亏比例 = (当前价 - 成本价) / 成本价 × 100%
- 持仓天数 = 今天 - 持仓日期

#### 3.2 止损/目标检查

| 触发条件 | 判断 |
|----------|------|
| 触及止损 | 当前价 ≤ 止损价 |
| 触及目标 | 当前价 ≥ 目标价 |
| 接近止损 | 当前价 - 止损价 ≤ 5% |
| 接近目标 | 目标价 - 当前价 ≤ 5% |

#### 3.3 Thesis 检查

对每笔持仓，判断 thesis 状态：

| Thesis 状态 | 条件 | 建议动作 |
|-------------|------|----------|
| INTACT（完好） | 行业趋势符合预期、公司基本面无重大变化 | 继续持有 |
| WEAKENED（减弱） | 行业趋势偏离预期、但未证伪 | 减仓 30-50% |
| BROKEN（证伪） | 核心逻辑被证伪（如竞争格局恶化、管理层变动等） | 无条件止损 |
| PLAYED_OUT（演绎完毕） | 目标已达成，按计划分批退出 | 分批止盈 |

Thesis 检查需要考虑：
1. **行业层面**：行业趋势是否如当初判断？
2. **公司层面**：公司基本面是否有重大负面变化？
3. **美股联动**：美股对标是否有重大事件影响？

#### 3.4 Thesis Breaking 常见场景

| Breaking 场景 | 对应 thesis | 判断 |
|--------------|-------------|------|
| 竞争对手推出颠覆性产品 | 技术领先 | BROKEN |
| 出口管制扩大 | 供应链安全 | BROKEN |
| 大客户流失 | 客户集中度 | BROKEN |
| 毛利率持续下滑 | 竞争格局 | WEAKENED |
| 管理层变动 | 公司治理 | WEAKENED |
| 行业政策转向 | 政策受益 | WEAKENED |
| 美股对标大跌 >10% | 美股联动 | WEAKENED |

### Step 4：检查组合约束

| 约束 | 计算 | 阈值 | 状态 |
|------|------|------|------|
| 单票仓位 | 持仓成本 / 组合资本 | ≤25% | |
| 行业集中度 | 最大行业成本 / 组合资本 | ≤50% | |
| 总暴露 | 所有持仓成本之和 / 组合资本 | ≤90% | |

### Step 5：生成复盘报告

```markdown
---
report_type: portfolio_review
date: {YYYY-MM-DD}
---

# 持仓复盘 — {YYYY-MM-DD}

## 持仓状态汇总

| Stock | Entry | Current | PnL% | PnL(CNY) | Days | Thesis | Status | Action |
|-------|-------|---------|-------|----------|------|--------|--------|--------|
{每笔持仓一行}

**Thesis 状态说明**：
- INTACT：投资逻辑完好，继续持有
- WEAKENED：逻辑减弱，考虑减仓
- BROKEN：逻辑证伪，无条件止损
- PLAYED_OUT：按计划止盈

**Action 说明**：
- HOLD：继续持有
- STOP_LOSS：止损
- PARTIAL_PROFIT：分批止盈
- REDUCE：减仓观察
- EXIT：清仓

## 调仓动作详情

### 建议止损

{如果有触及止损的持仓}
| Stock | 当前价 | 止损价 | 距止损 | 亏损% | 止损理由 |
|-------|--------|--------|--------|-------|----------|
| {代码} | {价} | {价} | {距}% | {亏}% | {理由} |

### 建议止盈

{如果有触及目标的持仓}
| Stock | 当前价 | 目标价 | 盈利% | 建议止盈比例 |
|-------|--------|--------|-------|-------------|
| {代码} | {价} | {价} | {盈}% | {比例}% |

### 建议减仓

{如果有 thesis 减弱的持仓}
| Stock | 当前仓位 | 建议仓位 | 减仓比例 | 减仓理由 |
|-------|----------|----------|----------|----------|
| {代码} | {仓}% | {仓}% | {比}% | {理由} |

### 继续持有

{如果有好持有的持仓}
| Stock | 当前仓位 | 理由 |
|-------|----------|------|
| {代码} | {仓}% | {理由} |

## Thesis 变化记录

{如果有 thesis 状态发生变化的持仓}
| Stock | 原状态 | 新状态 | 变化原因 |
|-------|--------|--------|----------|
| {代码} | {原} | {新} | {原因} |

## 组合约束检查

| 约束 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|
| 单票最大仓位 | {max_pos}% | 25% | {✅/⚠️} |
| 行业最大集中度 | {max_sector}% | 50% | {✅/⚠️} |
| 总暴露 | {total_exp}% | 90% | {✅/⚠️} |

## 明日关注

{基于今日复盘，列出明日需要重点关注的事项}

---
⚠️ 风险提示：本内容仅供研究参考，不构成任何投资建议。
```

### Step 6：写入文件

Write 到 `th_capital_stock/04_portfolio/performance/daily_{YYYY-MM-DD}.md`

### Step 7：注册快照

```bash
python th_capital_stock/08_scripts/registry/register_snapshot.py \
    --entity-type portfolio_review_snapshot \
    --entity-id {YYYYMMDD} \
    --status completed \
    --source TRAE_Portfolio_Review \
    --payload "{\"report_path\": \"th_capital_stock/04_portfolio/performance/daily_{YYYY-MM-DD}.md\", \"actions\": {\"stop_loss\": [{stocks}], \"partial_profit\": [{stocks}], \"reduce\": [{stocks}]}}"
```

---

## 质量检查清单

生成复盘报告后，请检查：

- [ ] 所有 open 持仓都有复盘记录
- [ ] 盈亏计算正确（带正负号）
- [ ] Thesis 状态判断有明确依据
- [ ] 调仓建议有具体价格/比例
- [ ] 组合约束检查完整
- [ ] 包含完整的免责声明
- [ ] frontmatter 完整

## 调仓执行规则

| 条件 | 动作 | 执行要求 |
|------|------|----------|
| thesis 证伪 | 无条件止损 | 立即执行，不等技术确认 |
| 触及止损 | 止损 | 立即执行 |
| thesis 减弱 | 减仓 30-50% | 技术确认后执行 |
| 触及目标 | 分批止盈（30%/40%/30%） | 视情况执行 |
| thesis 完好 | 继续持有 | 不动 |

## 错误处理

- 如果 pnl.py 执行失败：用数据库数据手动计算盈亏
- 如果 thesis 信息缺失：标注"thesis 待确认"，建议人工审核

---

## 输出确认

完成后请确认：
1. 复盘报告已写入正确目录
2. 快照已注册到 registry
3. 如果有调仓建议，提醒用户确认执行
