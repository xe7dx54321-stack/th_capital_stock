# TRAE Mac任务草案：深度投研分析链

## 1. 任务基本信息

- **schedule_id**: `investment_analysis`
- **job_id**: `investment_analysis`
- **执行时间**: 10:30 工作日（周一至周五）
- **牵头岗位**: `hermes_investment_analyst`
- **参与岗位**: `hermes_investment_analyst, openclaw_report_exec`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ❌ **无Mac registry条目**（TRAE导出包额外记录）

---

## 2. Mac执行路径

### 2.1 手动触发（⚠️ **暂缓执行**）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_smr_schedule_job.py --job investment_analysis --dry-run
```

⚠️ **警告**: 此任务为defer_until_d7，暂不建议shadow-run。

---

## 3. 任务目标

由深度投研分析岗牵头，对重点标的进行深度研究分析，输出投资研究综合报告。

---

## 4. 命令链（来源未确认）

⚠️ **注意**: run_smr_schedule_job.py中可能未定义此JobSpec。

**预期命令链**:
1. `08_scripts/research/build_investment_evidence_pack.py --limit 6`
2. `08_scripts/research/build_investment_research_synthesis_snapshot.py --limit 6`
3. `08_scripts/research/build_investment_report_snapshot.py --limit 4`

---

## 5. 输出产物

- 投资研究证据包
- 投研综合报告快照

---

## 6. 任务分类

- **分类**: ⚠️ **Defer_until_D7**
- **风险等级**: 高
- **判定依据**: 包含投资研究综合报告，可能包含投资建议

---

## 7. 暂缓原因

1. **包含投资研究综合报告**: 需确认报告内容是否符合Foundation边界
2. **可能包含投资建议**: 需严格审核报告内容
3. **无Mac registry条目**: 需手动添加registry定义
4. **需等待D7**: Foundation输入流集成后才能保证数据一致性

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Foundation边界检查

**检查项**:
- ❌ 投研综合报告是否包含目标价？
- ❌ 投研综合报告是否包含买入/卖出建议？
- ❌ 投研综合报告是否包含仓位建议？

**如发现边界违规**:
- 标记为永久defer
- 等待D7阶段foundation输入流集成
- 确保输出符合Foundation边界

---

## 10. 注意事项

- ❌ **Mac registry无此条目**，需手动添加
- ❌ **run_smr_schedule_job.py可能无此JobSpec**，需检查
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ **高风险**: 包含投资研究综合报告，需严格审核
- ⚠️ **暂缓**: 等待D7阶段启用

---

## 11. 启用建议

**暂不建议Shadow-run**: 此任务包含投资研究综合报告，风险高，需等待D7阶段。

**D7阶段启用步骤**:
1. 检查run_smr_schedule_job.py是否有investment_analysis JobSpec
2. 如无，手动添加JobSpec定义
3. 手动添加registry条目
4. 确认Foundation输入流集成状态
5. 手动审核投研报告内容是否符合边界
6. 用户明确是否允许Mac侧运行投研任务
7. 确认边界后正式启用

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)