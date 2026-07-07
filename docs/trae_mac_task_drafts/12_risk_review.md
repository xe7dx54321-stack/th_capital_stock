# TRAE Mac任务草案：晚间风控链

## 1. 任务基本信息

- **schedule_id**: `risk_review`
- **job_id**: `risk_review`
- **执行时间**: 21:00 工作日（周一至周五）
- **牵头岗位**: `openclaw_risk_exec`
- **参与岗位**: `openclaw_risk_exec, hermes_risk_curator, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ✅ **完整**（使用模板 risk_check_task.md）
- **Registry状态**: ✅ 已在Mac registry定义

---

## 2. Mac执行路径

### 2.1 手动触发（⚠️ **暂缓执行**）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id risk_review --dry-run
```

⚠️ **警告**: 此任务为defer_until_d7，暂不建议shadow-run。

---

## 3. 任务目标

由组合与风控执行岗牵头，刷新风控快照并推动风险解释候选。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `risk_review`，命令链（4个命令）：

1. `08_scripts/risk_engine/monitor.py`
2. `08_scripts/risk_engine/build_trade_risk_decision_snapshot.py`
3. `08_scripts/reporting/build_daily_system_health_report.py`
4. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`

---

## 5. 输出产物

- 风控快照
- 风险解释候选

---

## 6. 任务分类

- **分类**: ⚠️ **Defer_until_D7**
- **风险等级**: 中高
- **判定依据**: 包含风控检查 + 风险预警 + 处理建议

---

## 7. 依赖关系

- **上游任务**: portfolio_review, daily_report
- **下游任务**: next_day_plan

---

## 8. 暂缓原因

1. **包含风控检查**: 需确认Mac数据库与Windows数据一致性
2. **包含风险预警**: 需确认预警逻辑是否符合Foundation边界
3. **包含处理建议**: 需确认处理建议不包含目标价/买入卖出建议
4. **需等待D7**: Foundation输入流集成后才能保证数据一致性

---

## 9. Prompt路径映射

### 原始Prompt（Windows路径）

```bash
cd d:\李少博的文件\TH_Capital_二级市场
python th_capital_stock/08_scripts/risk_engine/monitor.py
```

### Mac映射Prompt

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/risk_engine/monitor.py  # 实际命令在run_smr_schedule_job.py中定义
```

---

## 10. Foundation边界检查

**检查项**:
- ❌ 风控检查是否包含投资建议？
- ❌ 风险预警是否包含买入/卖出建议？
- ❌ 处理建议是否包含仓位建议？

**如发现边界违规**:
- 标记为永久defer
- 等待D7阶段foundation输入流集成
- 需用户明确是否允许Mac侧运行风控任务

---

## 11. D7阶段启用条件

**条件1**: Mac数据库与Windows数据一致性验证通过

**条件2**: Foundation输入流集成完成

**条件3**: 用户明确允许Mac侧运行风控任务

**条件4**: 风控逻辑符合Foundation边界

---

## 12. 注意事项

- ✅ Prompt完整，有详细执行模板
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义4个命令
- ⚠️ Prompt文件中bash示例有Windows硬编码路径，需手动替换为Mac路径
- ⚠️ **高风险**: 包含风控检查和处理建议，需严格审核
- ⚠️ **暂缓**: 等待D7阶段启用

---

## 13. 启用建议

**暂不建议Shadow-run**: 此任务包含风控检查和处理建议，风险中高，需等待D7阶段。

**D7阶段启用步骤**:
1. 确认Mac数据库数据一致性
2. 确认Foundation输入流集成状态
3. 手动审核Prompt模板是否符合边界
4. 用户明确是否允许Mac侧运行风控任务
5. 先执行dry-run验证命令链
6. 手动触发一次审核输出内容
7. 确认边界后正式启用

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)