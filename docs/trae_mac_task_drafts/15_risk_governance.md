# TRAE Mac任务草案：风险治理链

## 1. 任务基本信息

- **schedule_id**: `risk_governance`
- **job_id**: `risk_governance`
- **执行时间**: 18:00 每周五
- **牵头岗位**: `hermes_risk_curator`
- **参与岗位**: `hermes_risk_curator, openclaw_risk_exec`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ❌ **无Mac registry条目**（TRAE导出包额外记录）

---

## 2. Mac执行路径

### 2.1 手动触发（⚠️ **暂缓执行**）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_smr_schedule_job.py --job risk_governance --dry-run
```

⚠️ **警告**: 此任务为defer_until_d7，暂不建议shadow-run。

---

## 3. 任务目标

由风险知识治理岗牵头，整理风险案例、更新风险 playbook、沉淀风险知识。

---

## 4. 命令链（来源未确认）

⚠️ **注意**: run_smr_schedule_job.py中可能未定义此JobSpec。

**预期命令链**:
1. `08_scripts/risk_engine/build_risk_case_library.py`
2. `08_scripts/risk_engine/update_risk_playbook.py`

---

## 5. 输出产物

- 风险案例库更新
- 风险 playbook 更新

---

## 6. 任务分类

- **分类**: ⚠️ **Defer_until_D7**
- **风险等级**: 中
- **判定依据**: 风险案例库 + playbook更新，不直接产生投资建议

---

## 7. 暂缓原因

1. **风险案例库更新**: 需确认案例库更新逻辑
2. **playbook更新**: 需确认playbook更新内容是否符合Foundation边界
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
- ❌ 风险案例库是否包含投资建议？
- ❌ playbook更新是否包含买入/卖出建议？

**如发现边界违规**:
- 标记为永久defer
- 等待D7阶段foundation输入流集成
- 确保输出符合Foundation边界

---

## 10. 注意事项

- ❌ **Mac registry无此条目**，需手动添加
- ❌ **run_smr_schedule_job.py可能无此JobSpec**，需检查
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ **中风险**: 风险知识沉淀，需审核内容
- ⚠️ **暂缓**: 等待D7阶段启用

---

## 11. 启用建议

**暂不建议Shadow-run**: 此任务为风险知识沉淀类，风险中，需等待D7阶段。

**D7阶段启用步骤**:
1. 检查run_smr_schedule_job.py是否有risk_governance JobSpec
2. 如无，手动添加JobSpec定义
3. 手动添加registry条目
4. 确认Foundation输入流集成状态
5. 手动审核风险案例库和playbook内容
6. 确认边界后正式启用

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)