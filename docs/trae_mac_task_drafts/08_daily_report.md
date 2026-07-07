# TRAE Mac任务草案：晚间日报链

## 1. 任务基本信息

- **schedule_id**: `daily_report`
- **job_id**: `daily_report`
- **执行时间**: 20:30 工作日（周一至周五）
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
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id daily_report --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由日报与调度知识岗牵头，物化正式日报并同步日报解释与 dispatch 候选。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `daily_report`，命令链（9个命令）：

1. `08_scripts/reporting/build_market_flow_anomaly_snapshot.py`
2. `08_scripts/research/build_price_range_forecast_snapshot.py`
3. `08_scripts/reporting/snapshot_daily_reporting.py`
4. `08_scripts/reporting/materialize_daily_report.py`
5. `08_scripts/reporting/snapshot_daily_reporting.py`
6. `08_scripts/reporting/build_data_freshness_snapshot.py`
7. `08_scripts/reporting/build_daily_system_health_report.py`
8. `08_scripts/reporting/build_current_state_snapshot.py`
9. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`

---

## 5. 输出产物

- 日报快照
- 正式日报（物化文件）
- dispatch 候选

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 日报物化，无投资建议内容

---

## 7. 依赖关系

- **上游任务**: portfolio_review
- **下游任务**: risk_review, next_day_plan

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
- 预期输出: `06_reports/daily/YYYY-MM-DD_日报.md`

---

## 11. 注意事项

- ✅ Prompt完整，有详细执行模板
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义9个命令
- ⚠️ Prompt文件中bash示例有Windows硬编码路径，需手动替换为Mac路径
- ⚠️ Prompt模板中提及的投资建议内容需确认是否符合Foundation边界

---

## 12. 启用建议

**建议Shadow-run**: 此任务为日报物化类，Prompt完整，但需注意Prompt模板中的投资建议边界。

**启用步骤**:
1. 先执行dry-run验证9个命令
2. 手动检查Prompt模板是否符合Foundation边界
3. 手动触发一次验证日报文件生成
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)