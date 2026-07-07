# TRAE Mac任务草案：次日计划链

## 1. 任务基本信息

- **schedule_id**: `next_day_plan`
- **job_id**: `next_day_plan`
- **执行时间**: 22:00 工作日（周一至周五）
- **牵头岗位**: `hermes_reporting_editor`
- **参与岗位**: `openclaw_report_exec, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ✅ 已在Mac registry定义

---

## 2. Mac执行路径

### 2.1 手动触发（Shadow-run）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id next_day_plan --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由日报与调度知识岗牵头，抽取未来催化日历并生成次日 dispatch 候选。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `next_day_plan`，命令链（3个命令）：

1. `08_scripts/events/build_upcoming_event_calendar.py`
2. `08_scripts/agents/build_dispatch_packet_candidate.py`
3. `08_scripts/agents/build_dispatch_board_patch_candidate.py`

---

## 5. 输出产物

- 未来催化日历
- dispatch packet candidate
- dispatch board patch candidate

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 催化日历抽取 + dispatch候选生成，无投资建议

---

## 7. 依赖关系

- **上游任务**: daily_report, risk_review
- **下游任务**: 无（当日最后一个任务）

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: 催化日历生成、dispatch候选数量
- 预期输出: upcoming_event_calendar、dispatch候选

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义3个命令（最短）
- ⚠️ Prompt不完整，需手动补充任务说明

---

## 11. 启用建议

**建议Shadow-run**: 此任务为催化日历抽取类，风险低，命令链最短，可优先测试。

**启用步骤**:
1. 先执行dry-run验证3个命令
2. 观察催化日历生成是否成功
3. 手动触发一次验证dispatch候选
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)