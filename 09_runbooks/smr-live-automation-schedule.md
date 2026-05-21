# SMR 持续自动运营班表

**更新时间**：2026-05-19  
**适用项目**：同行资本二级市场  
**当前结论**：Codex 只作为开发/排障工具，不承接日常运营调度。日常班表由项目内 agent runtime 注册，并由 macOS `launchd` 触发。

## 1. 当前真实调度边界

不再使用 Codex automation 跑日常运营链。

当前链路是：

```text
launchd
  -> 08_scripts/scheduler/run_agent_schedule.py
  -> 08_scripts/scheduler/run_smr_schedule_job.py
  -> 各 OpenClaw-like 执行岗脚本
  -> 08_scripts/agents/run_agent_control_loop.py
  -> Hermes-like 知识治理岗候选产物
```

Codex 的角色：

- 代码开发
- 排障
- 人工触发验证
- 架构/配置维护

Codex 不负责：

- 日常行情刷新
- 日常日报/风控/池子链
- 定时运营班表触发

## 2. 当前配置文件

agent 班表注册表：

```text
12_smr_agents/schedules/agent_schedule_registry.json
```

agent 调度入口：

```text
08_scripts/scheduler/run_agent_schedule.py
```

launchd 部署脚本：

```text
08_scripts/scheduler/deploy_agent_launchd.py
```

统一业务链执行器：

```text
08_scripts/scheduler/run_smr_schedule_job.py
```

当前作战状态面板：

```text
00_control/current_state.md
```

运行日志：

```text
10_logs/scheduler/runs/
10_logs/launchd/
```

## 3. 当前 agent 班表

| 班表 ID | 时间 | job | lead agent | 参与岗位 |
| --- | --- | --- | --- | --- |
| `deep_market_scan_morning` | 工作日 05:00 | `deep_market_scan` | `hermes_research_curator` | `openclaw_report_exec`, `hermes_research_curator` |
| `morning_us` | 工作日 06:00 | `morning_us` | `openclaw_data_exec` | `openclaw_data_exec`, `openclaw_factor_exec`, `openclaw_pool_exec`, `hermes_research_curator`, `hermes_reporting_editor` |
| `preopen_report` | 工作日 09:00 | `preopen_report` | `hermes_reporting_editor` | `openclaw_report_exec`, `hermes_reporting_editor` |
| `afternoon_close` | 工作日 15:30 | `afternoon_close` | `openclaw_data_exec` | `openclaw_data_exec`, `openclaw_factor_exec`, `openclaw_pool_exec`, `hermes_research_curator`, `hermes_reporting_editor` |
| `afternoon_refresh` | 工作日 16:30 | `afternoon_refresh` | `openclaw_factor_exec` | `openclaw_factor_exec`, `openclaw_pool_exec`, `hermes_research_curator`, `hermes_reporting_editor` |
| `deep_market_scan_afternoon` | 工作日 16:55 | `deep_market_scan` | `hermes_research_curator` | `openclaw_report_exec`, `hermes_research_curator` |
| `opportunity_radar_close` | 工作日 17:10 | `opportunity_radar` | `openclaw_pool_exec` | `openclaw_factor_exec`, `openclaw_pool_exec`, `hermes_research_curator`, `hermes_reporting_editor` |
| `portfolio_review` | 工作日 19:30 | `portfolio_review` | `openclaw_risk_exec` | `openclaw_risk_exec`, `hermes_risk_curator`, `hermes_reporting_editor` |
| `daily_report` | 工作日 20:30 | `daily_report` | `hermes_reporting_editor` | `openclaw_report_exec`, `hermes_reporting_editor` |
| `risk_review` | 工作日 21:00 | `risk_review` | `openclaw_risk_exec` | `openclaw_risk_exec`, `hermes_risk_curator`, `hermes_reporting_editor` |
| `next_day_plan` | 工作日 22:00 | `next_day_plan` | `hermes_reporting_editor` | `openclaw_report_exec`, `hermes_reporting_editor` |

## 4. 运维命令

列出 agent 班表：

```bash
python3 08_scripts/scheduler/run_agent_schedule.py --list
```

验证注册表：

```bash
python3 08_scripts/scheduler/run_agent_schedule.py --validate
```

干跑单个班表：

```bash
python3 08_scripts/scheduler/run_agent_schedule.py --schedule-id next_day_plan --dry-run
```

安装并加载 launchd 班表：

```bash
python3 08_scripts/scheduler/deploy_agent_launchd.py --install --load
```

查看 launchd 加载状态：

```bash
python3 08_scripts/scheduler/deploy_agent_launchd.py --status
```

卸载 launchd 班表：

```bash
python3 08_scripts/scheduler/deploy_agent_launchd.py --unload
```

## 5. 审计口径

每次 agent 班表触发后，`run_smr_schedule_job.py` 会在运行摘要中写入：

- `trigger`
- `schedule_id`
- `lead_profile_id`
- `operator_profile_ids`

当前重点闭环：

- `opportunity_radar` 会额外生成证据缺口、新鲜度和 current_state。
- `morning_us`、`preopen_report`、`afternoon_close`、`afternoon_refresh` 会刷新 current_state。
- 当 `dispatch_board.md` 仍停留在旧口径时，先看 `00_control/current_state.md`。

这能保证后续看日志时可以区分：

- 人工开发/排障触发
- 项目 agent 日常运营触发
- 具体由哪个 agent 岗位牵头

正式真相层仍受原有脚本和 review gate 保护。日常 agent 班表默认生成快照、候选和 handoff，不代表自动越权写仓位、风控真相或正式调度板。
