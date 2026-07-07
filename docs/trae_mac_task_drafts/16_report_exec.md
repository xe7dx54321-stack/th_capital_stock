# TRAE Mac任务草案：报告执行链

## 1. 任务基本信息

- **schedule_id**: `report_exec`
- **job_id**: `report_exec`
- **执行时间**: 23:00 工作日（周一至周五）
- **牵头岗位**: `openclaw_report_exec`
- **参与岗位**: `openclaw_report_exec, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ❌ **无Mac registry条目**（TRAE导出包额外记录）

---

## 2. Mac执行路径

### 2.1 手动触发（⚠️ **暂缓执行**）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_smr_schedule_job.py --job report_exec --dry-run
```

⚠️ **警告**: 此任务为defer_until_d7，暂不建议shadow-run。

---

## 3. 任务目标

由报告执行岗牵头，执行报告分发、归档和版本管理任务。

---

## 4. 命令链（来源未确认）

⚠️ **注意**: run_smr_schedule_job.py中可能未定义此JobSpec。

**预期命令链**:
1. `08_scripts/reporting/archive_reports.py`
2. `08_scripts/reporting/distribute_reports.py`

---

## 5. 输出产物

- 报告归档
- 报告分发记录

---

## 6. 任务分类

- **分类**: ⚠️ **Defer_until_D7**
- **风险等级**: 中
- **判定依据**: 报告分发（需确认接收方）

---

## 7. 暂缓原因

1. **报告分发**: 需确认分发接收方是否符合安全要求
2. **报告归档**: 需确认归档路径是否正确
3. **无Mac registry条目**: 需手动添加registry定义
4. **需等待D7**: 确认报告分发逻辑安全性

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Foundation边界检查

**检查项**:
- ❌ 报告分发接收方是否安全？
- ❌ 报告归档路径是否正确？
- ❌ 报告分发是否包含敏感数据？

**如发现边界违规**:
- 标记为永久defer
- 等待D7阶段确认分发逻辑安全性
- 确保报告分发符合安全边界

---

## 10. 注意事项

- ❌ **Mac registry无此条目**，需手动添加
- ❌ **run_smr_schedule_job.py可能无此JobSpec**，需检查
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ **中风险**: 报告分发需确认接收方
- ⚠️ **暂缓**: 等待D7阶段启用

---

## 11. 启用建议

**暂不建议Shadow-run**: 此任务为报告分发类，风险中，需等待D7阶段确认分发逻辑。

**D7阶段启用步骤**:
1. 检查run_smr_schedule_job.py是否有report_exec JobSpec
2. 如无，手动添加JobSpec定义
3. 手动添加registry条目
4. 确认报告分发接收方安全性
5. 确认报告归档路径正确
6. 确认边界后正式启用

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)