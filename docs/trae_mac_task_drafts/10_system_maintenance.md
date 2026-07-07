# TRAE Mac任务草案：系统维护链

## 1. 任务基本信息

- **schedule_id**: `system_maintenance`
- **job_id**: `system_maintenance`
- **执行时间**: 03:00 每周日
- **牵头岗位**: `openclaw_system_exec`
- **参与岗位**: `openclaw_system_exec`
- **超时时间**: 3600 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ❌ **无Mac registry条目**（TRAE导出包额外记录）

---

## 2. Mac执行路径

### 2.1 手动触发（Shadow-run）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_smr_schedule_job.py --job system_maintenance --dry-run
```

### 2.2 需添加Registry条目

此任务无Mac registry条目，需手动添加至agent_schedule_registry.json：

```json
{
  "schedule_id": "system_maintenance",
  "label": "系统维护链",
  "job_id": "system_maintenance",
  "lead_profile_id": "openclaw_system_exec",
  "operator_profile_ids": ["openclaw_system_exec"],
  "weekdays": ["SU"],
  "hour": 3,
  "minute": 0,
  "continue_on_error": true,
  "timeout_seconds": 3600,
  "purpose": "由系统执行岗牵头，执行系统级维护任务：验证数据完整性、清理过期数据、备份重要文件。"
}
```

---

## 3. 任务目标

由系统执行岗牵头，执行系统级维护任务：验证数据完整性、清理过期数据、备份重要文件。

---

## 4. 命令链（来自run_smr_schedule_job.py）

⚠️ **注意**: run_smr_schedule_job.py中可能未定义此JobSpec，需检查或手动添加。

**预期命令链**:
1. `08_scripts/maintenance/validate_data_integrity.py`
2. `08_scripts/maintenance/cleanup_expired_data.py`
3. `08_scripts/maintenance/backup_system_files.py`

---

## 5. 输出产物

- 数据完整性验证报告
- 过期数据清理结果
- 系统文件备份

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 系统维护任务，无投资决策，无业务逻辑

---

## 7. 依赖关系

- **上游任务**: 无（周末独立任务）
- **下周影响**: 为下周一的数据完整性提供保障

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: 数据完整性验证结果、清理文件数量、备份文件大小
- 预期输出: 维护报告文件

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ❌ **Mac registry无此条目**，需手动添加
- ❌ **run_smr_schedule_job.py可能无此JobSpec**，需检查
- ⚠️ Prompt不完整，需手动补充任务说明
- ⚠️ 超时时间3600秒（最长），需确认是否合理

---

## 11. 启用建议

**建议Shadow-run**: 此任务为系统维护类，风险低，但需先添加registry条目和检查JobSpec。

**启用步骤**:
1. 检查run_smr_schedule_job.py是否有system_maintenance JobSpec
2. 如无，手动添加JobSpec定义
3. 手动添加registry条目
4. 先执行dry-run验证命令链
5. 观察维护任务执行结果
6. 观察3-5周后正式启用launchd

---

## 12. Registry添加建议

**添加时机**: Intake阶段完成后，手动添加至agent_schedule_registry.json

**添加位置**: schedules数组末尾

**验证**: 运行 `python 08_scripts/scheduler/run_agent_schedule.py --validate`

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)