# TRAE Mac任务草案：持仓复盘

## 1. 任务基本信息

- **schedule_id**: `portfolio_review`
- **job_id**: `portfolio_review`
- **执行时间**: 19:30 工作日（周一至周五）
- **牵头岗位**: `openclaw_risk_exec`
- **参与岗位**: `openclaw_risk_exec, hermes_risk_curator, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ✅ **完整**（使用模板 portfolio_review_task.md）
- **Registry状态**: ✅ 已在Mac registry定义

---

## 2. Mac执行路径

### 2.1 手动触发（⚠️ **暂缓执行**）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id portfolio_review --dry-run
```

⚠️ **警告**: 此任务为defer_until_d7，暂不建议shadow-run。

---

## 3. 任务目标

由组合与风控执行岗牵头，更新持仓盈亏并推动可能出现的风险/调仓解释候选。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `portfolio_review`，命令链（2个命令）：

1. `08_scripts/portfolio/pnl.py`
2. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`

---

## 5. 输出产物

- 持仓盈亏更新
- 调仓解释候选

---

## 6. 任务分类

- **分类**: ⚠️ **Defer_until_D7**
- **风险等级**: 中高
- **判定依据**: 包含盈亏计算 + thesis状态判断 + 调仓建议

---

## 7. 依赖关系

- **上游任务**: opportunity_radar_close
- **下游任务**: daily_report, risk_review

---

## 8. 暂缓原因

1. **包含盈亏计算**: 需确认Mac数据库与Windows数据一致性
2. **包含thesis状态判断**: 需确认thesis判断逻辑是否符合Foundation边界
3. **包含调仓建议**: 需确认调仓建议不包含目标价/买入卖出建议
4. **需等待D7**: Foundation输入流集成后才能保证数据一致性

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

## 10. Foundation边界检查

**检查项**:
- ❌ Thesis状态判断是否包含投资建议？
- ❌ 调仓建议是否包含买入/卖出/仓位建议？
- ❌ 复盘报告是否包含目标价？

**如发现边界违规**:
- 标记为永久defer
- 等待D7阶段foundation输入流集成
- 需用户明确是否允许Mac侧运行风控任务

---

## 11. D7阶段启用条件

**条件1**: Mac数据库与Windows数据一致性验证通过

**条件2**: Foundation输入流集成完成

**条件3**: 用户明确允许Mac侧运行风控任务

**条件4**: Thesis判断逻辑符合Foundation边界

---

## 12. 注意事项

- ✅ Prompt完整，有详细执行模板
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义2个命令
- ⚠️ Prompt文件中bash示例有Windows硬编码路径，需手动替换为Mac路径
- ⚠️ **高风险**: 包含盈亏计算和调仓建议，需严格审核
- ⚠️ **暂缓**: 等待D7阶段启用

---

## 13. 启用建议

**暂不建议Shadow-run**: 此任务包含盈亏计算和调仓建议，风险中高，需等待D7阶段。

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