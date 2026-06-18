# TRAE 风控检查任务模板

> 本模板用于 TRAE 执行每日风控检查任务。
> **执行时间**：每日 21:00
> **执行前提**：当日持仓数据已更新（建议在日报流程后执行）
> **执行前必读**：smr-trae-playbook.md

---

## 任务目标

检查持仓风险，生成风险说明，确保组合在安全边界内运行。

## 执行步骤

### Step 1：执行风控检查脚本

```bash
cd d:\李少博的文件\TH_Capital_二级市场
python th_capital_stock/08_scripts/risk_engine/monitor.py
```

### Step 2：读取数据

#### 2.1 查询持仓

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

#### 2.2 查询风险告警

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
alerts = conn.execute('''
    SELECT * FROM risk_alert
    WHERE acknowledged = 0
    ORDER BY alert_time DESC
''').fetchall()
print(json.dumps([dict(r) for r in alerts], ensure_ascii=False))
"
```

#### 2.3 查询股票池（用于计算行业集中度）

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

### Step 3：按风控参数检查

#### 3.1 组合风控参数（来自 portfolio_policy.json）

| 参数 | 阈值 | 类型 |
|------|------|------|
| max_single_position_pct | 25% | 单票仓位 |
| max_sector_concentration_pct | 50% | 行业集中度 |
| max_total_exposure_pct | 90% | 总暴露 |
| max_drawdown_pct | 20% | 最大回撤 |
| max_weekly_loss_pct | 8% | 单周亏损 |

#### 3.2 检查清单

对每笔持仓检查：

| 检查项 | 方法 | 阈值 |
|--------|------|------|
| 单票仓位 | 持仓成本 / 组合资本 | ≤25% |
| 止损触发 | 当前价 ≤ 止损价 | 是/否 |
| 目标触发 | 当前价 ≥ 目标价 | 是/否 |
| Thesis 状态 | 根据持仓 thesis 判断 | INTACT/WEAKENED/BROKEN |

对组合整体检查：

| 检查项 | 方法 | 阈值 |
|--------|------|------|
| 总暴露 | 所有持仓成本之和 / 组合资本 | ≤90% |
| 行业集中度 | 最大行业持仓 / 组合资本 | ≤50% |
| 回撤 | 从最高点到当前 | ≤20% |
| 单周亏损 | 本周亏损 / 组合资本 | ≤8% |

### Step 4：生成风险说明

#### 情况 A：无预警

如果所有检查都通过：

```markdown
---
report_type: risk_note
date: {YYYY-MM-DD}
severity: none
---

# 风控检查报告 — {YYYY-MM-DD}

## 检查结论

**各指标均在安全范围内，无预警。**

## 详细检查结果

| 检查项 | 当前值 | 阈值 | 状态 |
|--------|--------|------|------|
| 单票最大仓位 | {max_position}% | 25% | ✅ PASS |
| 行业最大集中度 | {max_sector}% | 50% | ✅ PASS |
| 总暴露 | {total_exposure}% | 90% | ✅ PASS |
| 当前回撤 | {drawdown}% | 20% | ✅ PASS |
| 单周亏损 | {weekly_loss}% | 8% | ✅ PASS |

## 止损/目标触发检查

{如有持仓接近止损/目标，列出}

## 下次检查时间

明日 21:00

---
⚠️ 风险提示：本内容仅供研究参考，不构成投资建议。
```

#### 情况 B：有 warning 预警

如果触发 warning 阈值：

```markdown
---
report_type: risk_note
date: {YYYY-MM-DD}
severity: warning
---

# 风控预警 — {YYYY-MM-DD}

## 预警概要

**发现 {N} 个 warning 级别预警，需在 24 小时内处理。**

## 详细预警

### 预警 1：{预警类型}
- **标的**：{股票代码}
- **当前值**：{当前数值}%
- **阈值**：{阈值}%
- **超出幅度**：{超出}%
- **影响分析**：{分析该预警对组合的影响}
- **建议动作**：{具体建议}
- **处理期限**：{明日 21:00} 前

### 预警 2：{...}

## 详细检查结果

| 检查项 | 当前值 | 阈值 | 状态 |
|--------|--------|------|------|
| 单票最大仓位 | {max_position}% | 25% | {✅ PASS/⚠️ WARNING} |
| 行业最大集中度 | {max_sector}% | 50% | {✅ PASS/⚠️ WARNING} |
| 总暴露 | {total_exposure}% | 90% | {✅ PASS/⚠️ WARNING} |
| 当前回撤 | {drawdown}% | 20% | {✅ PASS/⚠️ WARNING} |
| 单周亏损 | {weekly_loss}% | 8% | {✅ PASS/⚠️ WARNING} |

## Thesis 状态检查

{如果有持仓 thesis 发生变化}

## 处理建议汇总

{汇总所有预警的处理建议}

---
⚠️ 风险提示：本内容仅供研究参考，不构成投资建议。请在 24 小时内处理上述预警。
```

#### 情况 C：有 critical 预警

如果触发 critical 阈值（回撤 >15% 或单周亏损 >8%）：

```markdown
---
report_type: risk_note
date: {YYYY-MM-DD}
severity: critical
---

# 🚨 紧急风控预警 — {YYYY-MM-DD}

## 预警概要

**发现 critical 级别预警，需在 4 小时内处理。**

{所有 critical 预警详情}

## 紧急处理建议

{按优先级列出紧急处理动作}

---
⚠️ 风险提示：紧急预警，请立即处理。
```

### Step 5：写入文件

Write 到 `th_capital_stock/05_risk/alerts/{YYYY-MM-DD}_risk_note.md`

### Step 6：注册快照

```bash
python th_capital_stock/08_scripts/registry/register_snapshot.py \
    --entity-type risk_update_candidate \
    --entity-id {YYYYMMDD} \
    --status completed \
    --source TRAE_Risk_Check \
    --payload "{\"report_path\": \"th_capital_stock/05_risk/alerts/{YYYY-MM-DD}_risk_note.md\", \"severity\": \"{none/warning/critical}\", \"alert_count\": {N}}"
```

---

## 质量检查清单

生成风控报告后，请检查：

- [ ] 所有持仓都检查了止损/目标状态
- [ ] 组合整体指标计算正确
- [ ] 预警级别判断正确（none/warning/critical）
- [ ] 包含处理期限
- [ ] 包含完整的免责声明
- [ ] frontmatter 完整（report_type、date、severity）

## 升级规则

| 当前状态 | 时间未处理 | 升级为 |
|----------|------------|--------|
| warning | 24 小时 | critical |
| critical | 4 小时 | 重新发送告警 |

## 错误处理

- 如果 monitor.py 执行失败：用数据库数据手动检查各指标，标注"系统检查失败，手动检查"
- 如果数据缺失：标注"数据待补"，不影响其他检查项

---

## 输出确认

完成后请确认：
1. 风控报告已写入正确目录
2. 快照已注册到 registry
3. 如果有预警，提醒用户处理期限
