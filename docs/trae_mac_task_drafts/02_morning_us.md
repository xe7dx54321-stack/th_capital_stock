# TRAE Mac任务草案：晨间美股链

## 1. 任务基本信息

- **schedule_id**: `morning_us`
- **job_id**: `morning_us`
- **执行时间**: 06:00 工作日（周一至周五）
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
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id morning_us --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由数据执行岗牵头，完成美股行情、联动因子、动态池和解释候选刷新。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `morning_us`，命令链（14个命令）：

1. `08_scripts/stock_pool/sync_watchlist.py`
2. `08_scripts/data_harvester/ah_daily_bar.py --days 5 --us-only`
3. `08_scripts/us_signal_harvester/earnings_monitor.py`
4. `08_scripts/factor_engine/us_linkage.py`
5. `08_scripts/stock_pool/reconcile_dynamic_pool.py`
6. `08_scripts/research/build_price_range_forecast_snapshot.py`
7. `08_scripts/reporting/build_data_freshness_snapshot.py`
8. `08_scripts/reporting/build_daily_system_health_report.py`
9. `08_scripts/reporting/build_current_state_snapshot.py`
10. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`
11. `08_scripts/research/build_investment_report_dashboard_snapshot.py --limit 6 --allow-empty`
12. `08_scripts/research/build_investment_evidence_gap_tasks.py --limit 6 --allow-empty`
13. `08_scripts/research/run_investment_evidence_gap_fetch.py --limit 3 --execute --continue-on-error --allow-empty`
14. `08_scripts/research/build_investment_evidence_pack.py --limit 3`

---

## 5. 输出产物

- US 日 K 线
- watchlist 同步
- 美股信号
- 联动因子
- 动态池
- 价格区间预测
- 数据新鲜度/系统健康/current_state 快照
- dispatch 候选
- 投研证据包

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 数据采集 + 因子计算 + 快照生成，无投资建议

---

## 7. 依赖关系

- **上游任务**: deep_market_scan_morning
- **下游任务**: afternoon_close

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

### 8.2 可选环境变量

- HTTP_PROXY/HTTPS_PROXY（如需访问美股数据源）

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: 美股数据采集成功率、因子计算完成度
- 预期输出: 多个快照文件、dispatch候选

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义14个命令
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ 命令链较长，注意观察超时

---

## 11. 启用建议

**建议Shadow-run**: 此任务为数据采集+因子计算类，风险低，但命令链较长，建议在deep_market_scan_morning成功后再启用。

**启用步骤**:
1. 先执行dry-run验证14个命令
2. 观察超时设置是否合理
3. 手动触发一次验证产物数量
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)