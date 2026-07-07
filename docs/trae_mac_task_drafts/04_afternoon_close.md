# TRAE Mac任务草案：午后收盘链

## 1. 任务基本信息

- **schedule_id**: `afternoon_close`
- **job_id**: `afternoon_close`
- **执行时间**: 15:30 工作日（周一至周五）
- **牵头岗位**: `openclaw_data_exec`
- **参与岗位**: `openclaw_data_exec, openclaw_factor_exec, openclaw_pool_exec, hermes_research_curator, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ✅ 已在Mac registry定义

---

## 2. Mac执行路径

### 2.1 手动触发（Shadow-run）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id afternoon_close --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由数据执行岗牵头，完成 A/H 收盘行情、因子、研究、池子与组合动作候选刷新。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `afternoon_close`，命令链（20个命令）：

1. `08_scripts/stock_pool/sync_watchlist.py`
2. `08_scripts/data_harvester/ah_daily_bar.py --days 5 --a-only`
3. `08_scripts/data_harvester/ah_daily_bar.py --days 5 --hk-only`
4. `08_scripts/factor_engine/trend.py`
5. `08_scripts/factor_engine/fundamental.py`
6. `08_scripts/factor_engine/us_linkage.py`
7. `08_scripts/research/generate_trend_batch.py`
8. `08_scripts/stock_pool/reconcile_dynamic_pool.py`
9. `08_scripts/research/snapshot_stock_objective_monitor.py`
10. `08_scripts/research/build_strategy_watch_cards.py`
11. `08_scripts/research/build_price_range_forecast_snapshot.py`
12. `08_scripts/portfolio/build_rotation_candidates.py`
13. `08_scripts/portfolio/build_rotation_execution_plan.py`
14. `08_scripts/portfolio/build_portfolio_action_memo.py`
15. `08_scripts/research/build_investment_evidence_pack.py --limit 3`
16. `08_scripts/reporting/build_data_freshness_snapshot.py`
17. `08_scripts/reporting/build_daily_system_health_report.py`
18. `08_scripts/reporting/build_current_state_snapshot.py`
19. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`

---

## 5. 输出产物

- A/H 日 K 线
- 趋势/基本面/美股联动因子
- 趋势批次
- 动态池
- 标的监控
- 策略观察卡
- 价格区间预测
- 轮动候选/执行计划/组合动作备忘录
- 证据包
- 数据新鲜度/系统健康/current_state 快照
- dispatch 候选

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 数据采集 + 因子计算 + 快照生成，无投资建议

---

## 7. 依赖关系

- **上游任务**: morning_us, preopen_report
- **下游任务**: afternoon_refresh, deep_market_scan_afternoon

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: A/H数据采集成功率、因子计算完成度
- 预期输出: 多个快照文件、轮动候选

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义20个命令
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ 命令链最长（20个），注意观察超时

---

## 11. 启用建议

**建议Shadow-run**: 此任务为数据采集+因子计算类，风险低，但命令链最长，建议在morning_us成功后再启用。

**启用步骤**:
1. 先执行dry-run验证20个命令
2. 观察超时设置是否合理（可能需调整至2700秒）
3. 手动触发一次验证产物数量
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)