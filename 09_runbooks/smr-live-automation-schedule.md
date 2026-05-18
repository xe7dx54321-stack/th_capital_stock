# SMR 持续自动运营班表

**更新时间**：2026-04-21  
**适用项目**：同行资本二级市场  
**当前结论**：当前真正生效的持续自动运营，已经切到 `Codex automation`（Codex 自动化）+ 本地统一调度脚本；不再依赖旧的 `OpenClaw cron jobs.json` 方案。

---

## 1. 当前真实生效的调度入口

统一调度脚本：

```text
08_scripts/scheduler/run_smr_schedule_job.py
```

作用：

- 把 8 个固定业务岗位统一收口到一个入口
- 每个岗位按预定义命令链顺序执行
- 自带锁文件，避免同一岗位重复并发运行
- 自动把每次运行写入结构化日志目录

运行日志目录：

```text
10_logs/scheduler/runs/
```

锁文件目录：

```text
10_logs/scheduler/locks/
```

---

## 2. 当前真实生效的自动化班表

这 8 个自动化已经在本机注册为 `ACTIVE`（启用）状态，工作区统一指向：

```text
/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场
```

| 自动化 ID | 名称 | 时间 | 频率 | 对应 job | 主要做什么 |
| --- | --- | --- | --- | --- | --- |
| `smr` | SMR 晨间美股链 | 工作日 06:00 | 每天 1 次 | `morning_us` | 同步美股行情、美股信号、动态池，并刷新 dispatch 候选 |
| `smr-2` | SMR 盘前简报链 | 工作日 09:00 | 每天 1 次 | `preopen_report` | 刷新日报快照，物化盘前简报，并同步 dispatch 候选 |
| `smr-3` | SMR 午后收盘链 | 工作日 15:30 | 每天 1 次 | `afternoon_close` | 刷新 A/H 行情、因子、研究、股票池、轮动和组合动作候选 |
| `smr-4` | SMR 午后二次刷新 | 工作日 16:30 | 每天 1 次 | `afternoon_refresh` | 补跑因子和研究候选，做收盘后第二轮收口 |
| `smr-5` | SMR 持仓复盘 | 工作日 19:30 | 每天 1 次 | `portfolio_review` | 更新持仓盈亏，并推动风险/调仓解释候选刷新 |
| `smr-6` | SMR 晚间日报链 | 工作日 20:30 | 每天 1 次 | `daily_report` | 物化正式日报，并同步日报解释和 dispatch 候选 |
| `smr-7` | SMR 晚间风控链 | 工作日 21:00 | 每天 1 次 | `risk_review` | 刷新风控快照，并推动风险解释候选刷新 |
| `smr-8` | SMR 次日计划链 | 工作日 22:00 | 每天 1 次 | `next_day_plan` | 生成未来催化日历，并刷新次日 dispatch 候选 |

---

## 3. 每个岗位对应的命令链

### 3.1 `morning_us`

```bash
python3 08_scripts/stock_pool/sync_watchlist.py
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --us-only
python3 08_scripts/us_signal_harvester/earnings_monitor.py
python3 08_scripts/factor_engine/us_linkage.py
python3 08_scripts/stock_pool/reconcile_dynamic_pool.py
python3 08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch
```

### 3.2 `preopen_report`

```bash
python3 08_scripts/reporting/snapshot_daily_reporting.py
python3 08_scripts/reporting/materialize_daily_report.py
python3 08_scripts/reporting/snapshot_daily_reporting.py
python3 08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch
```

### 3.3 `afternoon_close`

```bash
python3 08_scripts/stock_pool/sync_watchlist.py
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --a-only
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --hk-only
python3 08_scripts/factor_engine/trend.py
python3 08_scripts/factor_engine/fundamental.py
python3 08_scripts/factor_engine/us_linkage.py
python3 08_scripts/research/generate_trend_batch.py
python3 08_scripts/stock_pool/reconcile_dynamic_pool.py
python3 08_scripts/research/snapshot_stock_objective_monitor.py
python3 08_scripts/research/build_strategy_watch_cards.py
python3 08_scripts/portfolio/build_rotation_candidates.py
python3 08_scripts/portfolio/build_rotation_execution_plan.py
python3 08_scripts/portfolio/build_portfolio_action_memo.py
python3 08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch
```

### 3.4 `afternoon_refresh`

```bash
python3 08_scripts/factor_engine/trend.py
python3 08_scripts/factor_engine/fundamental.py
python3 08_scripts/factor_engine/us_linkage.py
python3 08_scripts/research/generate_trend_batch.py
python3 08_scripts/stock_pool/reconcile_dynamic_pool.py
python3 08_scripts/research/snapshot_stock_objective_monitor.py
python3 08_scripts/research/build_strategy_watch_cards.py
python3 08_scripts/portfolio/build_rotation_candidates.py
python3 08_scripts/portfolio/build_rotation_execution_plan.py
python3 08_scripts/portfolio/build_portfolio_action_memo.py
python3 08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch
```

### 3.5 `portfolio_review`

```bash
python3 08_scripts/portfolio/pnl.py
python3 08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch
```

### 3.6 `daily_report`

```bash
python3 08_scripts/reporting/snapshot_daily_reporting.py
python3 08_scripts/reporting/materialize_daily_report.py
python3 08_scripts/reporting/snapshot_daily_reporting.py
python3 08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch
```

### 3.7 `risk_review`

```bash
python3 08_scripts/risk_engine/monitor.py
python3 08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch
```

### 3.8 `next_day_plan`

```bash
python3 08_scripts/events/build_upcoming_event_calendar.py
python3 08_scripts/agents/build_dispatch_packet_candidate.py
python3 08_scripts/agents/build_dispatch_board_patch_candidate.py
```

---

## 4. 现在怎么判断它是不是正常在跑

看这里：

```text
10_logs/scheduler/runs/
```

每次岗位运行都会生成一个目录，例如：

```text
10_logs/scheduler/runs/20260421_120321__next_day_plan/
```

目录里至少会有两份文件：

- `run.md`：逐步记录每条命令、返回码、标准输出和错误输出
- `summary.json`：结构化摘要，便于后续总控台或审计脚本读取

---

## 5. 已完成的首轮验证

2026-04-21 已完成以下验证：

- `run_smr_schedule_job.py --list` 正常
- `run_smr_schedule_job.py --job morning_us --dry-run` 正常
- `run_smr_schedule_job.py --job next_day_plan` 真跑成功

真实成功样本：

```text
10_logs/scheduler/runs/20260421_120321__next_day_plan/
```

---

## 6. 旧方案说明

以下脚本暂时不应继续作为“当前真实调度入口”使用：

```text
08_scripts/_deploy_scripts/deploy_cron.py
```

原因：

- 它仍然写死旧机器路径 `/Users/apple/...`
- 它对接的是 `OpenClaw jobs.json` 口径，不是当前本机实际在跑的 Codex automation
- 继续使用容易把“规划里的旧方案”和“当前真实生效方案”混在一起

结论：

- 当前真实调度，以 `Codex automation` + `08_scripts/scheduler/run_smr_schedule_job.py` 为准
- 旧 `deploy_cron.py` 只保留作历史参考，不作为当前生产入口
