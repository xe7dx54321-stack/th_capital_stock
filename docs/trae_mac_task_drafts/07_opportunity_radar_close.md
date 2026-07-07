# TRAE Mac任务草案：主动机会雷达收盘

## 1. 任务基本信息

- **schedule_id**: `opportunity_radar_close`
- **job_id**: `opportunity_radar`
- **执行时间**: 17:10 工作日（周一至周五）
- **牵头岗位**: `openclaw_pool_exec`
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
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id opportunity_radar_close --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由研究与池子执行岗牵头，收盘后把异动、因子、研究池、策略证据、攻防推演、生命周期和纸面复盘收敛成机会闭环。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `opportunity_radar`，命令链（12个命令）：

1. `08_scripts/reporting/build_market_flow_anomaly_snapshot.py`
2. `08_scripts/opportunity/build_opportunity_radar_snapshot.py`
3. `08_scripts/opportunity/build_strategy_evidence_snapshot.py --limit 16`
4. `08_scripts/opportunity/build_thesis_attack_defense_snapshot.py --limit 12`
5. `08_scripts/opportunity/build_paper_trade_watchlist.py --limit 8`
6. `08_scripts/opportunity/build_opportunity_lifecycle_snapshot.py`
7. `08_scripts/opportunity/build_paper_watch_performance_snapshot.py`
8. `08_scripts/reporting/build_data_freshness_snapshot.py`
9. `08_scripts/reporting/build_daily_system_health_report.py`
10. `08_scripts/reporting/build_current_state_snapshot.py`
11. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`

---

## 5. 输出产物

- 异动快照
- 机会雷达快照
- 策略证据快照
- 攻防推演快照
- 纸面交易观察列表
- 生命周期快照
- 纸面复盘表现快照
- 数据新鲜度/系统健康/current_state 快照
- dispatch 候选

---

## 6. 任务分类

- **分类**: ⚠️ **Manual_Review_Only**
- **风险等级**: 中
- **判定依据**: 机会雷达包含攻防推演 + 纸面复盘，输出可能接近投资建议

---

## 7. 依赖关系

- **上游任务**: afternoon_refresh, deep_market_scan_afternoon
- **下游任务**: portfolio_review

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: 攻防推演、纸面复盘输出内容
- 预期输出: 多个机会快照文件

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义12个命令
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ **输出内容需人工审核**：攻防推演、纸面复盘可能包含投资建议

---

## 11. 启用建议

**建议Manual_Review**: 此任务包含攻防推演和纸面复盘，输出内容需人工审核是否符合Foundation边界。

**审核步骤**:
1. 先执行dry-run验证命令链
2. 手动触发一次生成机会快照
3. **人工审核输出内容**：检查是否有投资建议
4. 确认边界后决定是否shadow-run
5. 如有投资建议内容，标记为defer_until_d7

---

## 12. Foundation边界检查

**检查项**:
- ❌ 攻防推演是否包含买入/卖出建议？
- ❌ 纸面复盘是否包含仓位建议？
- ❌ 机会雷达是否包含目标价？

**如发现边界违规**:
- 标记为defer_until_d7
- 等待D7阶段foundation输入流集成
- 确保输出符合Foundation边界

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)