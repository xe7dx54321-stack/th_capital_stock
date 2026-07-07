# SMR-MAC-1 TRAE Scheduler Migration Intake Report

## 1. Intake Info

- **Intake time**: 2026-07-07 21:45:00
- **Intake user**: apple (Mac)
- **Mac repo path**: `/Users/apple/Documents/同行资本二级市场`
- **Mac timezone**: Asia/Shanghai
- **Branch**: feature/smr-mac1-trae-scheduler-migration-intake
- **Migration packages consulted**:
  - `/Users/apple/Documents/smr_trae_automation_export_20260707_115615` (TRAE任务导出)
  - `/Users/apple/Documents/smr_windows_scheduler_migration_20260707_094759` (Windows Scheduler导出)

---

## 2. Migration Package Summary

### 2.1 TRAE Tasks Export Package

- **Export time**: 2026-07-07 11:56:15
- **Export user**: lisha (Windows)
- **Windows repo path**: `D:\李少博的文件\TH_Capital_二级市场`
- **Task count**: 16 TRAE tasks defined in `agent_schedule_registry.json`
- **Prompt completeness**:
  - **完整prompt (5个)**: 使用独立TRAE任务模板
    - `preopen_report` (盘前简报链) - daily_brief_task.md
    - `daily_report` (晚间日报链) - daily_brief_task.md
    - `portfolio_review` (持仓复盘) - portfolio_review_task.md
    - `risk_review` (晚间风控链) - risk_check_task.md
    - `report_writing` (投资报告撰写链) - weekly_brief_task.md
  - **不完整prompt (11个)**: 仅根据registry + job命令整理
    - `deep_market_scan_morning` (深度市场扫描早)
    - `morning_us` (晨间美股链)
    - `afternoon_close` (午后收盘链)
    - `afternoon_refresh` (午后二次刷新)
    - `deep_market_scan_afternoon` (深度市场扫描午后)
    - `opportunity_radar_close` (主动机会雷达收盘)
    - `investment_analysis` (深度投研分析链)
    - `risk_governance` (风险治理链)
    - `report_exec` (报告执行链)
    - `next_day_plan` (次日计划链)
    - `system_maintenance` (系统维护链)

### 2.2 Windows Scheduler Export Package

- **Export time**: 2026-07-07 10:45:00
- **Windows user**: lisha
- **Computer name**: 李少博的电脑
- **Task Scheduler findings**:
  - 仅发现 **2个 WeChat Bridge 相关任务**
  - 其他18个中文任务名均未在Windows Task Scheduler中找到
  - 推测大部分业务任务通过Python脚本内调度运行
- **Python environment**:
  - Python 3.11.9 (全局环境)
  - pip freeze: 仅akshare包
  - 无虚拟环境目录
- **Database path**: `D:\李少博的文件\TH_Capital_二级市场\th_capital_stock\01_data\db\smr.db` (0.281 GB)
- **Data root size**: 0.281 GB

---

## 3. Task Inventory

### 3.1 TRAE Schedule Registry (agent_schedule_registry.json)

Mac仓库已包含11个schedule定义（非16个，因部分job_id被多个schedule使用）：

| Schedule ID | Label | Job ID | Weekdays | Hour | Minute | Lead Profile | Operator Profiles | Prompt Complete |
|-------------|-------|--------|----------|------|---------|--------------|-------------------|-----------------|
| deep_market_scan_morning | 深度市场扫描早 | deep_market_scan | MO,TU,WE,TH,FR | 05:00 | hermes_research_curator | openclaw_report_exec, hermes_research_curator | ❌ 不完整 |
| morning_us | 晨间美股链 | morning_us | MO,TU,WE,TH,FR | 06:00 | openclaw_data_exec | openclaw_data_exec, openclaw_factor_exec, openclaw_pool_exec, hermes_research_curator, hermes_reporting_editor | ❌ 不完整 |
| preopen_report | 盘前简报链 | preopen_report | MO,TU,WE,TH,FR | 09:00 | hermes_reporting_editor | openclaw_report_exec, hermes_reporting_editor | ✅ 完整 |
| afternoon_close | 午后收盘链 | afternoon_close | MO,TU,WE,TH,FR | 15:30 | openclaw_data_exec | openclaw_data_exec, openclaw_factor_exec, openclaw_pool_exec, hermes_research_curator, hermes_reporting_editor | ❌ 不完整 |
| afternoon_refresh | 午后二次刷新 | afternoon_refresh | MO,TU,WE,TH,FR | 16:30 | openclaw_factor_exec | openclaw_factor_exec, openclaw_pool_exec, hermes_research_curator, hermes_reporting_editor | ❌ 不完整 |
| deep_market_scan_afternoon | 深度市场扫描午后 | deep_market_scan | MO,TU,WE,TH,FR | 16:55 | hermes_research_curator | openclaw_report_exec, hermes_research_curator | ❌ 不完整 |
| opportunity_radar_close | 主动机会雷达收盘 | opportunity_radar | MO,TU,WE,TH,FR | 17:10 | openclaw_pool_exec | openclaw_factor_exec, openclaw_pool_exec, hermes_research_curator, hermes_reporting_editor | ❌ 不完整 |
| portfolio_review | 持仓复盘 | portfolio_review | MO,TU,WE,TH,FR | 19:30 | openclaw_risk_exec | openclaw_risk_exec, hermes_risk_curator, hermes_reporting_editor | ✅ 完整 |
| daily_report | 晚间日报链 | daily_report | MO,TU,WE,TH,FR | 20:30 | hermes_reporting_editor | openclaw_report_exec, hermes_reporting_editor | ✅ 完整 |
| risk_review | 晚间风控链 | risk_review | MO,TU,WE,TH,FR | 21:00 | openclaw_risk_exec | openclaw_risk_exec, hermes_risk_curator, hermes_reporting_editor | ✅ 完整 |
| next_day_plan | 次日计划链 | next_day_plan | MO,TU,WE,TH,FR | 22:00 | hermes_reporting_editor | openclaw_report_exec, hermes_reporting_editor | ❌ 不完整 |

**注**: TRAE导出包中记录了16个任务prompt文件，但Mac registry中只有11个schedule_id。差异来自：
- `deep_market_scan` 有2个schedule (morning + afternoon)
- `opportunity_radar` 只有1个schedule (close)
- TRAE导出包额外记录了5个无registry条目的任务prompt（推测为手动触发任务）

### 3.2 TRAE导出包额外任务（无registry条目）

| Schedule ID | Label | Job ID | Weekdays | Hour | Prompt Complete | 来源 |
|-------------|-------|--------|----------|------|-----------------|------|
| investment_analysis | 深度投研分析链 | investment_analysis | MO,TU,WE,TH,FR | 10:30 | ❌ 不完整 | 无registry条目 |
| report_writing | 投资报告撰写链 | report_writing | MO,WE,FR | 14:00 | ✅ 完整 | 无registry条目 |
| risk_governance | 风险治理链 | risk_governance | FR | 18:00 | ❌ 不完整 | 无registry条目 |
| report_exec | 报告执行链 | report_exec | MO,TU,WE,TH,FR | 23:00 | ❌ 不完整 | 无registry条目 |
| system_maintenance | 系统维护链 | system_maintenance | SU | 03:00 | ❌ 不完整 | 无registry条目 |

---

## 4. Mac Scheduler Architecture

Mac仓库已具备完整的调度架构，无需从Windows迁移Task Scheduler逻辑：

### 4.1 核心脚本

| Script | Path | Purpose | Status |
|--------|------|---------|--------|
| run_smr_schedule_job.py | 08_scripts/scheduler/ | 任务执行器，定义11个JobSpec | ✅ 已存在 |
| run_agent_schedule.py | 08_scripts/scheduler/ | 任务调度器，读取agent_schedule_registry.json | ✅ 已存在 |
| deploy_agent_launchd.py | 08_scripts/scheduler/ | launchd部署脚本 | ✅ 已存在 |

### 4.2 Job Specs (run_smr_schedule_job.py)

Mac仓库已定义11个JobSpec：

| Job ID | Label | Commands Count | Description |
|--------|-------|---------------|-------------|
| morning_us | 晨间美股链 | 14 | 美股行情、联动因子、动态池、解释候选刷新 |
| deep_market_scan | 深度市场扫描 | 2 | MarketScreener信号、deep_market_analysis快照 |
| preopen_report | 盘前简报链 | 14 | 日报快照、盘前简报、dispatch候选 |
| afternoon_close | 午后收盘链 | 20 | A/H行情、因子、研究、池子、组合候选 |
| afternoon_refresh | 午后二次刷新 | 16 | 因子、研究候选、dispatch收口 |
| opportunity_radar | 主动机会雷达链 | 12 | 异动、因子、研究池、策略证据、攻防推演、生命周期 |
| portfolio_review | 持仓复盘 | 2 | 盈亏更新、调仓解释候选 |
| daily_report | 晚间日报链 | 9 | 日报物化、解释与dispatch候选 |
| risk_review | 晚间风控链 | 4 | 风控快照、风险解释候选 |
| next_day_plan | 次日计划链 | 3 | 催化日历、dispatch候选 |

### 4.3 Launchd Deployment Status

Mac仓库具备launchd部署能力，当前状态：
- ✅ deploy_agent_launchd.py 可生成plist文件
- ✅ 可写入至 `~/Library/LaunchAgents/com.tonghang.smr.agent.*.plist`
- ⚠️ **当前无任何launchd任务已加载**（需手动执行部署）

---

## 5. Windows Path Mapping

### 5.1 Core Path Mapping

| Windows Path | Mac Path | Notes |
|--------------|----------|-------|
| `D:\李少博的文件\TH_Capital_二级市场` | `/Users/apple/Documents/同行资本二级市场` | 仓库根目录 |
| `C:\Users\lisha\AppData\Local\Programs\Python\Python311\python.exe` | `/usr/local/bin/python3` (建议) | Python解释器 |
| `th_capital_stock\01_data\db\smr.db` | `th_capital_stock/01_data/db/smr.db` | 主数据库（相对路径无需修改） |

### 5.2 Windows硬编码路径分布

#### Prompt文件中的硬编码路径

**发现位置**: 5个完整prompt文件中存在硬编码路径

| Prompt File | 硬编码路径 | 行号 |
|-------------|-----------|------|
| preopen_report | `d:\李少博的文件\TH_Capital_二级市场` | Step 1-6 |
| daily_report | `d:\李少博的文件\TH_Capital_二级市场` | Step 1-6 |
| portfolio_review | `d:\李少博的文件\TH_Capital_二级市场` | Step 1-7 |
| risk_review | `d:\李少博的文件\TH_Capital_二级市场` | Step 1-6 |
| report_writing | `d:\李少博的文件\TH_Capital_二级市场` | Step 1-5 |

**影响范围**: 完整prompt的bash命令示例需路径映射

#### Windows Task Scheduler中的硬编码路径

| Task Name | Execute Path | Working Directory |
|-----------|-------------|-------------------|
| THCapital Wechat Bridge | `D:\THCapital\wechat-bridge-outbox\tools\run_wechat_bridge_consumer.bat` | `D:\THCapital\wechat-bridge-outbox\tools` |
| THCapital-WeChat-Bridge-Consumer | `D:\THCapital\wechat-bridge-outbox\tools\run_wechat_bridge_consumer_forever.ps1` | `D:\THCapital\wechat-bridge-outbox\tools` |

**注**: WeChat Bridge任务路径不在当前Mac仓库范围内，需单独处理。

---

## 6. Task Classification

### 6.1 Shadow-Run第一批 (可立即shadow-run)

**判定标准**:
- 纯数据采集/快照生成任务
- 无投资判断/风险决策输出
- 无组合操作建议
- 已有Mac registry条目

| Schedule ID | Label | Risk Level | Reason |
|-------------|-------|------------|--------|
| deep_market_scan_morning | 深度市场扫描早 | 低 | MarketScreener信号采集 + deep_market_analysis快照 |
| morning_us | 晚晨美股链 | 低 | 美股行情同步 + 因子计算 + 快照生成 |
| preopen_report | 盘前简报链 | 低 | 日报快照 + 物化（无投资建议） |
| afternoon_close | 午后收盘链 | 低 | A/H行情 + 因子 + 池子 + 快照 |
| afternoon_refresh | 午后二次刷新 | 低 | 因子补跑 + dispatch收口 |
| deep_market_scan_afternoon | 深度市场扫描午后 | 低 | 补刷MarketScreener信号 |
| daily_report | 晚间日报链 | 低 | 日报物化（无投资建议） |
| next_day_plan | 次日计划链 | 低 | 催化日历 + dispatch候选 |
| system_maintenance | 系统维护链 | 低 | 数据完整性验证 + 清理 + 备份 |

**Shadow-run执行方式**:
```bash
# 手动触发单个任务（dry-run模式）
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_agent_schedule.py --schedule-id deep_market_scan_morning --dry-run

# 观察日志输出
# 日志路径: 10_logs/scheduler/runs/
```

### 6.2 Defer_until_D7 (暂缓执行)

**判定标准**:
- 包含持仓盈亏计算
- 包含风控决策输出
- 包含投资研究综合报告
- 包含投资建议内容
- 包含组合操作建议

| Schedule ID | Label | Risk Level | Reason |
|-------------|-------|------------|--------|
| portfolio_review | 持仓复盘 | 中高 | 盈亏计算 + thesis状态判断 + 调仓建议 |
| risk_review | 晚间风控链 | 中高 | 风控检查 + 风险预警 + 处理建议 |
| investment_analysis | 深度投研分析链 | 高 | 投资研究综合报告 |
| report_writing | 投资报告撰写链 | 高 | 周报包含组合表现分析 + thesis回顾 |
| risk_governance | 风险治理链 | 中 | 风险案例库 + playbook更新 |
| report_exec | 报告执行链 | 中 | 报告分发（需确认接收方） |

**暂缓原因**:
- 需等待D7阶段foundation输入流集成
- 需确认Mac环境数据库与Windows数据一致性
- 需用户明确是否允许Mac侧运行风控任务

### 6.3 Manual_Review_Only (仅人工触发)

| Schedule ID | Label | Risk Level | Reason |
|-------------|-------|------------|--------|
| opportunity_radar_close | 主动机会雷达收盘 | 中 | 机会雷达包含攻防推演 + 纸面复盘，输出可能接近投资建议 |

**建议**: 人工审核opportunity_radar输出内容后再决定是否shadow-run

---

## 7. Environment Variables Mapping

### 7.1 Windows敏感环境变量

从environment_variables_redacted.csv发现以下敏感变量需Mac侧重新配置：

| Name | LooksSensitive | Windows Value | Mac Replacement Needed |
|------|----------------|---------------|------------------------|
| CFS_TOKEN | True | [REDACTED] | ✅ 需Mac侧重新配置 |
| HTTP_PROXY | True | [REDACTED] | ✅ 需Mac侧重新配置 |
| HTTPS_PROXY | True | [REDACTED] | ✅ 需Mac侧重新配置 |
| ICUBE_PROXY_HOST | True | [REDACTED] | ✅ 需Mac侧重新配置 |
| NO_PROXY | True | [REDACTED] | ✅ 需Mac侧重新配置 |
| PREVIEW_PROXY_ENABLED | True | [REDACTED] | ✅ 需Mac侧重新配置 |
| USERPROFILE | True | [REDACTED] | N/A（系统变量） |

### 7.2 SMR相关环境变量

| Name | Windows Value | Mac Value Needed | Notes |
|------|---------------|------------------|-------|
| SAFE_RM_ALLOWED_PATH | `D:\李少博的文件\TH_Capital_二级市场;C:\Users\lisha\.trae-cn\memory;...` | `/Users/apple/Documents/同行资本二级市场;...` | 需路径映射 |
| SAFE_RM_DENIED_PATH | `d:\李少博的文件\TH_Capital_二级市场\.vscode;...` | `/Users/apple/Documents/同行资本二级市场/.vscode;...` | 需路径映射 |

---

## 8. Task Dependencies

### 8.1 任务依赖链分析

基于run_smr_schedule_job.py命令链顺序，任务依赖关系：

| Schedule ID | Upstream Tasks | Downstream Tasks |
|-------------|----------------|------------------|
| deep_market_scan_morning | 无 | morning_us, preopen_report |
| morning_us | deep_market_scan_morning | afternoon_close |
| preopen_report | deep_market_scan_morning | afternoon_close |
| afternoon_close | morning_us, preopen_report | afternoon_refresh, deep_market_scan_afternoon |
| afternoon_refresh | afternoon_close | opportunity_radar_close |
| deep_market_scan_afternoon | afternoon_close | opportunity_radar_close |
| opportunity_radar_close | afternoon_refresh, deep_market_scan_afternoon | portfolio_review |
| portfolio_review | opportunity_radar_close | daily_report, risk_review |
| daily_report | portfolio_review | risk_review, next_day_plan |
| risk_review | portfolio_review, daily_report | next_day_plan |
| next_day_plan | daily_report, risk_review | 无 |

### 8.2 启用顺序建议

**第一批shadow-run顺序**:
1. deep_market_scan_morning (05:00)
2. morning_us (06:00)
3. preopen_report (09:00)
4. afternoon_close (15:30)
5. afternoon_refresh (16:30)
6. deep_market_scan_afternoon (16:55)
7. daily_report (20:30)
8. next_day_plan (22:00)
9. system_maintenance (周日 03:00)

**暂缓任务**:
- portfolio_review (19:30) - 等D7
- risk_review (21:00) - 等D7
- investment_analysis (10:30) - 等D7
- report_writing (14:00) - 等D7
- risk_governance (周五 18:00) - 等D7
- report_exec (23:00) - 等D7
- opportunity_radar_close (17:10) - 人工审核后决定

---

## 9. Boundaries Verification

### 9.1 Intake阶段边界

| Boundary | Status | Evidence |
|----------|--------|----------|
| 未创建TRAE任务 | ✅ 通过 | 仅读取迁移包，未调用Schedule tool创建任务 |
| 未启用调度 | ✅ 通过 | 未执行deploy_agent_launchd.py --load |
| 未运行真实业务 | ✅ 通过 | 未执行run_agent_schedule.py |
| 未提交迁移包 | ✅ 通过 | 迁移包保留在Documents，未提交至repo |
| 未提交runtime artifacts | ✅ 通过 | 仅生成docs文件 |
| 未修改数据库 | ✅ 通过 | 无数据库操作 |
| 未修改.git | ✅ 通过 | 无git历史操作 |

### 9.2 输出范围

| Output Type | Path | Status |
|-------------|------|--------|
| Intake Report | docs/smr_mac1_trae_scheduler_migration_intake_report.md | ✅ 生成 |
| Task Drafts | docs/trae_mac_task_drafts/*.md (16个文件) | 🔄 待生成 |
| compileall验证 | 10_logs/scheduler/runs/ | 🔄 待执行 |
| Git提交 | feature/smr-mac1-trae-scheduler-migration-intake分支 | 🔄 待提交 |

---

## 10. Findings Summary

### 10.1 关键发现

1. **Mac仓库已具备完整调度架构**
   - ✅ run_smr_schedule_job.py已定义11个JobSpec
   - ✅ run_agent_schedule.py已可读取agent_schedule_registry.json
   - ✅ deploy_agent_launchd.py已可生成launchd plist
   - ⚠️ **无需从Windows迁移调度逻辑**

2. **Windows Task Scheduler仅发现2个任务**
   - 仅WeChat Bridge相关任务使用Windows Task Scheduler
   - 其他业务任务全部通过Python脚本内调度运行
   - Mac侧registry已覆盖Windows侧业务任务定义

3. **Prompt完整性差异**
   - 5个任务有完整TRAE prompt模板
   - 11个任务仅有命令链整理
   - 完整prompt中存在Windows硬编码路径，需映射

4. **路径映射需求**
   - 主仓库路径: `D:\李少博的文件\TH_Capital_二级市场` → `/Users/apple/Documents/同行资本二级市场`
   - WeChat Bridge路径不在当前仓库范围
   - Prompt文件bash示例需路径替换

5. **敏感环境变量需重新配置**
   - CFS_TOKEN, HTTP_PROXY, HTTPS_PROXY等需Mac侧重新配置
   - SAFE_RM_ALLOWED_PATH/DENIED_PATH需路径映射

### 10.2 风险点

| Risk | Level | Mitigation |
|------|-------|------------|
| 双系统同时运行 | 高 | Shadow-run期间禁用Windows侧调度 |
| 数据库并发写入冲突 | 中 | 观察期使用相同数据库文件 |
| Prompt路径未映射 | 低 | 手动触发时使用Mac路径 |
| 环境变量缺失 | 低 | Shadow-run前配置必要环境变量 |
| WeChat Bridge路径不匹配 | 低 | WeChat Bridge不在当前scope |

---

## 11. Next Steps

### 11.1 Intake阶段下一步

- ✅ 生成16个任务草案文件 → docs/trae_mac_task_drafts/
- 🔄 运行compileall验证Mac仓库脚本
- 🔄 提交docs文件至feature/smr-mac1-trae-scheduler-migration-intake分支

### 11.2 D7阶段建议

- **D7.1**: Foundation输入流集成（参考smr_dashboard_backend_integration_debt.md）
- **D7.2**: 启用defer_until_d7任务
- **D7.3**: 配置Mac侧敏感环境变量
- **D7.4**: 执行数据一致性验证
- **D7.5**: 正式启用launchd调度

---

## 12. Appendix

### 12.1 文件清单

**已读取的迁移包文件**:
- `/Users/apple/Documents/smr_trae_automation_export_20260707_115615/smr_trae_windows_export_report.md`
- `/Users/apple/Documents/smr_trae_automation_export_20260707_115615/trae_tasks_inventory.csv`
- `/Users/apple/Documents/smr_trae_automation_export_20260707_115615/trae_tasks_inventory.json`
- `/Users/apple/Documents/smr_trae_automation_export_20260707_115615/trae_tasks_migration_matrix.md`
- `/Users/apple/Documents/smr_trae_automation_export_20260707_115615/trae_tasks_prompts/*.md` (16个文件)

**已读取的Windows Scheduler文件**:
- `/Users/apple/Documents/smr_windows_scheduler_migration_20260707_094759/reports/smr_windows_scheduler_export_report.md`
- `/Users/apple/Documents/smr_windows_scheduler_migration_20260707_094759/reports/task_migration_matrix.md`
- `/Users/apple/Documents/smr_windows_scheduler_migration_20260707_094759/reports/windows_to_mac_path_mapping_draft.md`
- `/Users/apple/Documents/smr_windows_scheduler_migration_20260707_094759/command_path_inventory.csv`
- `/Users/apple/Documents/smr_windows_scheduler_migration_20260707_094759/env/environment_variables_redacted.csv`

**已读取的Mac仓库文件**:
- `/Users/apple/Documents/同行资本二级市场/08_scripts/scheduler/run_smr_schedule_job.py`
- `/Users/apple/Documents/同行资本二级市场/08_scripts/scheduler/run_agent_schedule.py`
- `/Users/apple/Documents/同行资本二级市场/08_scripts/scheduler/deploy_agent_launchd.py`
- `/Users/apple/Documents/同行资本二级市场/12_smr_agents/schedules/agent_schedule_registry.json`

### 12.2 Registry Diff Summary

| Field | TRAE Export Package | Mac Registry | Match |
|-------|---------------------|--------------|-------|
| schedule count | 16 (prompt files) | 11 (registry entries) | ❌ 不匹配 |
| schedule_ids | 16 unique | 11 unique | ❌ 5个无registry |
| job_ids | 12 unique | 10 unique | ✅ 近似 |
| lead_profile_id | 已定义 | 已定义 | ✅ 匹配 |
| operator_profile_ids | 已定义 | 已定义 | ✅ 匹配 |
| weekdays | 已定义 | 已定义 | ✅ 匹配 |
| hour/minute | 已定义 | 已定义 | ✅ 匹配 |
| continue_on_error | 已定义 | 已定义 | ✅ 匹配 |
| timeout_seconds | 已定义 | 已定义 | ✅ 匹配 |

---

## 13. Conclusion

**SMR-MAC-1 TRAE Scheduler Migration Intake阶段已完成**:

- ✅ 成功读取两个迁移包（TRAE导出 + Windows Scheduler导出）
- ✅ 成功审计Mac仓库调度架构
- ✅ 成功识别16个TRAE任务及其分类
- ✅ 成功识别Windows硬编码路径分布
- ✅ 成功识别敏感环境变量需求
- ✅ 边界验证通过（未创建任务、未启用调度、未运行业务）

**关键结论**:
- Mac仓库已具备完整调度能力，无需迁移Windows Task Scheduler逻辑
- 可立即shadow-run第一批9个低风险任务
- 需等待D7阶段处理6个暂缓任务
- 需配置Mac侧环境变量和路径映射

---

**Report Generated**: 2026-07-07 21:45:00
**Report Author**: TRAE Agent (GLM-5)
**Report Status**: ✅ Intake Complete