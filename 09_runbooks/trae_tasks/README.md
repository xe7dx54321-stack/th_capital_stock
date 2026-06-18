# TRAE 任务模板索引

> 本目录包含 TRAE 执行 SMR 业务流程的所有任务模板。
> 每个模板都包含完整的执行步骤、数据查询命令、输出格式和错误处理。
> **执行前请先阅读 `../smr-trae-playbook.md` 了解整体规范。**

---

## 模板列表

| 任务 | 执行时间 | 模板文件 | 描述 |
|------|----------|----------|------|
| 日报撰写 | 每日 20:30 | `daily_brief_task.md` | 生成当日市场简报 |
| 风控检查 | 每日 21:00 | `risk_check_task.md` | 检查持仓风险，生成风险说明 |
| 持仓复盘 | 每日 19:30 | `portfolio_review_task.md` | 复盘持仓状态，产出调仓建议 |
| 周报撰写 | 每周五 20:00 | `weekly_brief_task.md` | 生成周度总结报告 |

---

## 目录结构

```
trae_tasks/
├── README.md                      # 本索引文件
├── daily_brief_task.md            # 日报撰写模板
├── risk_check_task.md             # 风控检查模板
├── portfolio_review_task.md       # 持仓复盘模板
└── weekly_brief_task.md          # 周报撰写模板
```

---

## 使用方法

### 方式一：通过 TRAE Schedule 自动执行

参见 `../smr-trae-schedule.md` 了解如何配置定时任务。

### 方式二：手动触发

在 TRAE 中复制对应模板的完整内容，按步骤执行。

### 方式三：通过命令行

```bash
# 读取任务模板
cat ../smr-trae-playbook.md
cat daily_brief_task.md

# 执行任务
# 1. 更新盈亏
python th_capital_stock/08_scripts/portfolio/pnl.py

# 2. 风控检查
python th_capital_stock/08_scripts/risk_engine/monitor.py

# 3. 查询数据
python -c "import sqlite3,json; conn=sqlite3.connect('th_capital_stock/01_data/db/smr.db'); conn.row_factory=sqlite3.Row; print(json.dumps([dict(r) for r in conn.execute('SELECT * FROM position WHERE status=\"open\"').fetchall()], ensure_ascii=False))"

# 4. 注册快照
python th_capital_stock/08_scripts/registry/register_snapshot.py --entity-type daily_report_candidate --entity-id {date} --status completed --source TRAE_Daily_Brief
```

---

## 输出产物

| 产物 | 目录 | 命名 |
|------|------|------|
| 日报 | `th_capital_stock/06_reports/daily/` | `YYYY-MM-DD_盘前简报.md` |
| 周报 | `th_capital_stock/06_reports/weekly/` | `weekly_YYYY-MM-DD.md` |
| 风控说明 | `th_capital_stock/05_risk/alerts/` | `YYYY-MM-DD_risk_note.md` |
| 复盘报告 | `th_capital_stock/04_portfolio/performance/` | `daily_YYYY-MM-DD.md` |

---

## 模板维护

- 每个模板都应包含：执行前提、步骤、数据查询、输出格式、质量检查清单
- 模板更新后需同步更新 `smr-trae-playbook.md`
- 新增模板需在本索引中登记

---

*最后更新：2026-06-18*
