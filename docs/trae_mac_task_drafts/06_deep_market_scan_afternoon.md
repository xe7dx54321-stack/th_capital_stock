# TRAE Mac任务草案：深度市场扫描午后

## 1. 任务基本信息

- **schedule_id**: `deep_market_scan_afternoon`
- **job_id**: `deep_market_scan`
- **执行时间**: 16:55 工作日（周一至周五）
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
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id deep_market_scan_afternoon --dry-run
```

### 2.2 launchd部署（未来启用）

```bash
python 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
python 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

---

## 3. 任务目标

由研究知识治理岗牵头，午后补刷公开信息与市场主题扫描。

---

## 4. 命令链（来自run_smr_schedule_job.py）

Job ID为 `deep_market_scan`，命令链：

1. `08_scripts/wiki/fetch_marketscreener_analyst_signals.py`
2. `08_scripts/research/build_deep_market_analysis_snapshot.py`

---

## 5. 输出产物

- MarketScreener 分析师信号快照（补刷）
- deep_market_analysis 快照（补刷）

---

## 6. 任务分类

- **分类**: ✅ **Shadow-Run第一批**
- **风险等级**: 低
- **判定依据**: 数据采集补刷，无投资判断

---

## 7. 依赖关系

- **上游任务**: afternoon_close
- **下游任务**: opportunity_radar_close

---

## 8. Mac环境要求

### 8.1 必需环境变量

- `SMR_ROOT`: `/Users/apple/Documents/同行资本二级市场`
- `PATH`: `/usr/local/bin:/usr/bin:/bin`

---

## 9. Shadow-run观察点

- 日志路径: `10_logs/scheduler/runs/`
- 观察重点: MarketScreener数据补刷成功率
- 预期输出: deep_market_analysis快照更新

---

## 10. 注意事项

- ✅ 无Windows硬编码路径，使用相对路径
- ✅ Mac registry已包含schedule定义
- ✅ JobSpec已定义（与morning共用）
- ⚠️ Prompt不完整，需手动补充任务说明

---

## 11. 启用建议

**建议Shadow-run**: 此任务为数据采集补刷类，风险低，命令链短，可优先测试。

**启用步骤**:
1. 先执行dry-run验证命令链
2. 观察补刷数据是否成功
3. 手动触发一次验证快照更新
4. 观察3-5天后正式启用launchd

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)