# TRAE Mac任务草案：深度市场扫描早

## 1. 任务基本信息

- **schedule_id**: `deep_market_scan_morning`
- **job_id**: `deep_market_scan`
- **执行时间**: 05:00 工作日（周一至周五）
- **牵头岗位**: `hermes_research_curator`
- **参与岗位**: `openclaw_report_exec, hermes_research_curator`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ❌ 不完整（仅命令链整理）
- **Registry状态**: ✅ 已在Mac registry定义

---

## 2. Mac执行路径

### 2.1 手动触发（Shadow-run）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id deep_market_scan_morning --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由研究知识治理岗牵头，早间刷新全网公开信息与深度市场机会扫描。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `deep_market_scan`，命令链：

1. `08_scripts/wiki/fetch_marketscreener_analyst_signals.py`
2. `08_scripts/research/build_deep_market_analysis_snapshot.py`

---

## 5. 输出产物

- MarketScreener 分析师信号快照
- deep_market_analysis 快照

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 纯数据采集任务，无投资判断，无风险决策

---

## 7. 依赖关系

- **上游任务**: 无
- **下游任务**: morning_us, preopen_report

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

### 8.2 可选环境变量

- HTTP_PROXY/HTTPS_PROXY（如需访问外网）

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: MarketScreener数据采集成功率
- 预期输出: deep_market_analysis快照文件

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义命令链
- ⚠️ Prompt不完整，需手动补充任务说明

---

## 11. 启用建议

**建议立即Shadow-run**: 此任务为数据采集类，风险低，可作为第一个shadow-run任务测试Mac调度能力。

**启用步骤**:
1. 先执行dry-run验证命令链
2. 观察日志输出确认路径正确
3. 手动触发一次验证产物生成
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)