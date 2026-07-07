# TRAE Mac任务草案：盘前简报链

## 1. 任务基本信息

- **schedule_id**: `preopen_report`
- **job_id**: `preopen_report`
- **执行时间**: 09:00 工作日（周一至周五）
- **牵头岗位**: `hermes_reporting_editor`
- **参与岗位**: `openclaw_report_exec, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ✅ **完整**（使用模板 daily_brief_task.md）
- **Registry状态**: ✅ 已在Mac registry定义

---

## 2. Mac执行路径

### 2.1 手动触发（Shadow-run）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id preopen_report --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由日报与调度知识岗牵头，刷新日报快照、物化正式盘前简报，并同步 dispatch 候选。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `preopen_report`，命令链（14个命令）：

1. `08_scripts/reporting/build_market_flow_anomaly_snapshot.py`
2. `08_scripts/research/build_price_range_forecast_snapshot.py`
3. `08_scripts/reporting/snapshot_daily_reporting.py`
4. `08_scripts/reporting/materialize_daily_report.py`
5. `08_scripts/reporting/snapshot_daily_reporting.py`
6. `08_scripts/reporting/build_data_freshness_snapshot.py`
7. `08_scripts/reporting/build_daily_system_health_report.py`
8. `08_scripts/reporting/build_current_state_snapshot.py`
9. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`
10. `08_scripts/research/build_investment_report_dashboard_snapshot.py --limit 6 --allow-empty`
11. `08_scripts/research/build_investment_evidence_gap_tasks.py --limit 6 --allow-empty`
12. `08_scripts/research/run_investment_evidence_gap_fetch.py --limit 3 --execute --continue-on-error --allow-empty`
13. `08_scripts/research/build_investment_evidence_pack.py --limit 3`

---

## 5. 输出产物

- 日报快照
- 盘前简报（物化文件）
- dispatch 候选

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 日报快照 + 物化，无投资建议内容

---

## 7. 依赖关系

- **上游任务**: deep_market_scan_morning
- **下游任务**: afternoon_close

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Prompt路径映射

### 原始Prompt（Windows路径）

```bash
cd d:\李少博的文件\TH_Capital_二级市场
python th_capital_stock/08_scripts/portfolio/pnl.py
```

### Mac映射Prompt

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/portfolio/pnl.py  # 实际命令在run_smr_schedule_job.py中定义
```

---

## 10. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: 日报物化成功率
- 预期输出: `06_reports/daily/YYYY-MM-DD_盘前简报.md`

---

## 11. 注意事项

- ✅ Prompt完整，有详细执行模板
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义14个命令
- ⚠️ Prompt文件中bash示例有Windows硬编码路径，需手动替换为Mac路径
- ⚠️ Prompt模板中提及的投资建议内容需确认是否符合Foundation边界

---

## 12. 启用建议

**建议Shadow-run**: 此任务为日报物化类，Prompt完整，但需注意Prompt模板中的投资建议边界。

**启用步骤**:
1. 先执行dry-run验证14个命令
2. 手动检查Prompt模板是否符合Foundation边界
3. 手动触发一次验证日报文件生成
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)