# TRAE Mac任务草案：午后二次刷新

## 1. 任务基本信息

- **schedule_id**: `afternoon_refresh`
- **job_id**: `afternoon_refresh`
- **执行时间**: 16:30 工作日（周一至周五）
- **牵头岗位**: `openclaw_factor_exec`
- **参与岗位**: `openclaw_factor_exec, openclaw_pool_exec, hermes_research_curator, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ✅ 已在Mac registry定义

---

## 2. Mac执行路径

### 2.1 手动触发（Shadow-run）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id afternoon_refresh --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由因子与信号执行岗牵头，做收盘后第二轮因子、研究候选和 dispatch 收口。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `afternoon_refresh`，命令链（16个命令）：

1. `08_scripts/factor_engine/trend.py`
2. `08_scripts/factor_engine/fundamental.py`
3. `08_scripts/factor_engine/us_linkage.py`
4. `08_scripts/research/generate_trend_batch.py`
5. `08_scripts/stock_pool/reconcile_dynamic_pool.py`
6. `08_scripts/research/snapshot_stock_objective_monitor.py`
7. `08_scripts/research/build_strategy_watch_cards.py`
8. `08_scripts/research/build_price_range_forecast_snapshot.py`
9. `08_scripts/portfolio/build_rotation_candidates.py`
10. `08_scripts/portfolio/build_rotation_execution_plan.py`
11. `08_scripts/portfolio/build_portfolio_action_memo.py`
12. `08_scripts/research/build_investment_evidence_pack.py --limit 3`
13. `08_scripts/reporting/build_data_freshness_snapshot.py`
14. `08_scripts/reporting/build_daily_system_health_report.py`
15. `08_scripts/reporting/build_current_state_snapshot.py`
16. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`

---

## 5. 输出产物

- 趋势/基本面/美股联动因子（补跑）
- 趋势批次
- 动态池（补刷）
- 标的监控
- 策略观察卡
- 价格区间预测
- 轮动候选/执行计划/组合动作备忘录
- 证据包
- 数据新鲜度/系统健康/current_state 快照
- dispatch 候选（收口）

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 因子补跑 + dispatch收口，无投资建议

---

## 7. 依赖关系

- **上游任务**: afternoon_close
- **下游任务**: opportunity_radar_close

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: 因子补跑成功率、dispatch收口完成度
- 预期输出: 快照文件更新、dispatch候选更新

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义16个命令
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ 命令链较长（16个），注意观察超时

---

## 11. 启用建议

**建议Shadow-run**: 此任务为因子补跑类，风险低，建议在afternoon_close成功后启用。

**启用步骤**:
1. 先执行dry-run验证16个命令
2. 观察因子补跑是否成功
3. 手动触发一次验证快照更新
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)