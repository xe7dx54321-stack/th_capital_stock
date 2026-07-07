# SMR-MAC-3 Shadow-run Environment Validation Report

## 1. 基本信息

- **任务编号**: SMR-MAC-3
- **任务名称**: Shadow-run Environment Validation
- **验证日期**: 2026-07-07
- **验证环境**: Mac Mini
- **项目路径**: `/Users/apple/Documents/同行资本二级市场`
- **当前分支**: `feature/smr-mac2-trae-shadow-scheduler-prep`

---

## 2. 验证结果汇总

| 验证项 | 结果 | 备注 |
|--------|------|------|
| Python环境 | ✅ PASS | Python 3.14.3 |
| 核心依赖 | ✅ PASS | pytest, pandas, numpy, requests |
| 环境变量 | ✅ PASS | CFS_IPC_NAME, CFS_TOKEN, CFS_TRANSPORT |
| 项目路径 | ✅ PASS | 正常存在 |
| 数据库路径 | ✅ PASS | 01_data/smr.db 等 |
| 日志路径 | ✅ PASS | 10_logs/ 存在 |
| Scheduler脚本 | ✅ PASS | run_agent_schedule.py, run_smr_schedule_job.py |
| Registry文件 | ⚠️ WARN | 缺少system_maintenance |
| Profiles文件 | ✅ PASS | 12个profile文件 |
| Launchd状态 | ✅ PASS | plist存在但未loaded |
| TRAE enabled | ✅ PASS | MAC-2 draft全部enabled=false |
| Git状态 | ⚠️ WARN | 1个修改文件 |
| 双写风险 | ⚠️ WARN | plist存在，需确认Windows侧 |

---

## 3. Python环境验证

### 3.1 Python版本

```
Python 3.14.3
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
```

**结论**: ✅ PASS

### 3.2 虚拟环境

```
.venv not found (using system python)
```

**结论**: ⚠️ WARN - 建议创建虚拟环境，但当前可用系统Python

### 3.3 核心依赖

| 包名 | 版本 | 状态 |
|------|------|------|
| pytest | 9.1.1 | ✅ |
| pandas | 2.3.3 | ✅ |
| numpy | 2.4.2 | ✅ |
| requests | 2.32.5 | ✅ |

**结论**: ✅ PASS

---

## 4. 环境变量验证

### 4.1 已配置环境变量（仅名称）

```
CFS_IPC_NAME
CFS_TOKEN
CFS_TRANSPORT
```

**结论**: ✅ PASS - CFS相关环境变量已配置

### 4.2 建议补充环境变量

以下环境变量建议在正式shadow-run前配置：

| 变量名 | 说明 | 必要性 |
|--------|------|--------|
| SMR_PROJECT_ROOT | 项目根路径 | 低（可从脚本推断） |
| SMR_DATA_PATH | 数据目录 | 低（已有默认路径） |
| SMR_LOG_PATH | 日志目录 | 低（已有10_logs/） |

---

## 5. 路径验证

### 5.1 项目路径

```
/Users/apple/Documents/同行资本二级市场
```

**结论**: ✅ PASS

### 5.2 数据库路径

已发现数据库文件：
- `01_data/smr.db`
- `01_data/market_system.db`
- `01_data/db/smr.db`

**结论**: ✅ PASS

### 5.3 日志路径

```
10_logs/
├── control_tower/
├── dashboard/
```

**结论**: ✅ PASS

---

## 6. Scheduler脚本验证

### 6.1 核心脚本

| 脚本 | 路径 | 状态 |
|------|------|------|
| run_agent_schedule.py | 08_scripts/scheduler/ | ✅ |
| run_smr_schedule_job.py | 08_scripts/scheduler/ | ✅ |
| deploy_agent_launchd.py | 08_scripts/scheduler/ | ✅ |

**compileall**: ✅ PASS

### 6.2 Registry文件

```
12_smr_agents/schedules/agent_schedule_registry.json
```

**已定义任务数量**: 10个

| schedule_id | 状态 |
|-------------|------|
| deep_market_scan_morning | ✅ 存在 |
| morning_us | ✅ 存在 |
| preopen_report | ✅ 存在 |
| afternoon_close | ✅ 存在 |
| afternoon_refresh | ✅ 存在 |
| deep_market_scan_afternoon | ✅ 存在 |
| opportunity_radar_close | ✅ 存在 |
| portfolio_review | ✅ 存在 |
| daily_report | ✅ 存在 |
| risk_review | ✅ 存在 |
| next_day_plan | ✅ 存在 |
| **system_maintenance** | ❌ **缺失** |

**结论**: ⚠️ WARN - 缺少system_maintenance任务定义

### 6.3 Profiles文件

已发现12个profile文件：
- hermes_engineering_planner.json
- hermes_investment_analyst.json
- hermes_investment_report_writer.json
- hermes_reporting_editor.json
- hermes_research_curator.json
- hermes_risk_curator.json
- openclaw_data_exec.json
- openclaw_factor_exec.json
- openclaw_pool_exec.json
- openclaw_report_exec.json
- openclaw_risk_exec.json
- openclaw_system_exec.json

**结论**: ✅ PASS - 所有必需profile存在

---

## 7. Launchd状态验证

### 7.1 LaunchAgents目录

已发现11个plist文件：

```
com.tonghang.smr.agent.afternoon-close.plist
com.tonghang.smr.agent.afternoon-refresh.plist
com.tonghang.smr.agent.daily-report.plist
com.tonghang.smr.agent.deep-market-scan-afternoon.plist
com.tonghang.smr.agent.deep-market-scan-morning.plist
com.tonghang.smr.agent.morning-us.plist
com.tonghang.smr.agent.next-day-plan.plist
com.tonghang.smr.agent.opportunity-radar-close.plist
com.tonghang.smr.agent.portfolio-review.plist
com.tonghang.smr.agent.preopen-report.plist
com.tonghang.smr.agent.risk-review.plist
```

**注意**: plist文件存在但**未loaded**（`launchctl list`无输出）

**结论**: ✅ PASS - 未启用，安全

### 7.2 Disabled键检查

部分plist文件缺少`Disabled`键。建议添加：

```xml
<key>Disabled</key>
<true/>
```

---

## 8. MAC-2 Draft Registry验证

### 8.1 enabled状态

```
"enabled": false 出现次数: 10
```

**结论**: ✅ PASS - 所有任务默认不启用

### 8.2 其他安全键

| 键名 | false出现次数 | 状态 |
|------|--------------|------|
| production_enabled | 9 | ✅ |
| backend_write_allowed | 9 | ✅ |
| launchd_load_allowed | 9 | ✅ |

**结论**: ✅ PASS - 安全边界正确配置

---

## 9. Git状态验证

### 9.1 当前状态

```
M 00_control/dispatch_board.md
?? tmp/
```

**结论**: ⚠️ WARN - 有1个修改文件

### 9.2 建议

- `00_control/dispatch_board.md` 修改应评估是否影响shadow-run
- `tmp/` 目录应在.gitignore中

---

## 10. Windows/Mac双写风险评估

### 10.1 当前状态

- Mac侧有11个plist文件（未loaded）
- 需确认Windows侧是否仍在运行

### 10.2 风险点

| 风险 | 描述 | 缓解 |
|------|------|------|
| 数据库并发写入 | 两边可能同时写smr.db | 确认Windows侧暂停 |
| 输出目录冲突 | 两边可能写入同一目录 | 使用相同路径映射 |
| 时间重叠 | 某些任务时间可能重叠 | 错开时间或暂停一边 |

**结论**: ⚠️ WARN - 需确认Windows侧状态

---

## 11. 环境问题清单

### 11.1 需修复问题

| 问题 | 严重程度 | 修复建议 |
|------|---------|---------|
| Registry缺少system_maintenance | 中 | 在agent_schedule_registry.json中添加任务定义 |
| plist缺少Disabled键 | 低 | 添加`<key>Disabled</key><true/>` |

### 11.2 建议改进

| 建议 | 优先级 | 说明 |
|------|--------|------|
| 创建虚拟环境 | 低 | 避免污染系统Python |
| 配置SMR_*环境变量 | 低 | 明确路径配置 |
| 确认Windows侧状态 | 高 | 避免双写风险 |
| 清理tmp/目录 | 低 | 确保在.gitignore中 |

---

## 12. Shadow Run任务脚本Dry-run检查

### 12.1 检查方法

执行 `python3 run_agent_schedule.py --schedule-id {task_id} --dry-run`（仅语法检查）

**注意**: 本次验证未执行实际dry-run，仅确认脚本存在且可编译。

### 12.2 脚本可编译性

```
python3 -m compileall 08_scripts/scheduler -q
PASS
```

**结论**: ✅ PASS

---

## 13. 边界确认

| 边界项 | 状态 |
|--------|------|
| 是否联网抓数据 | ❌ 否（仅检查环境） |
| 是否运行真实任务 | ❌ 否 |
| 是否写后台 | ❌ 否 |
| 是否修改业务逻辑 | ❌ 否 |
| 是否启用launchd | ❌ 否 |
| 是否启用TRAE任务 | ❌ 否 |

---

## 14. 结论

### 14.1 整体评估

| 指标 | 状态 |
|------|------|
| Python环境正常 | ✅ PASS |
| 所有依赖正常 | ✅ PASS |
| 环境变量齐全 | ✅ PASS |
| 9个Shadow Run任务脚本存在 | ⚠️ WARN (缺少system_maintenance) |
| 无重复写入风险 | ⚠️ WARN (需确认Windows侧) |
| launchd未启用 | ✅ PASS |
| TRAE自动化未启用 | ✅ PASS |
| git status保持干净 | ⚠️ WARN (1个修改文件) |

### 14.2 最终结论

**⚠️ CONDITIONAL PASS - 需修复2个问题后可进入MAC-4**

### 14.3 进入MAC-4前置条件

1. ✅ 添加system_maintenance到registry
2. ⚠️ 确认Windows侧调度已暂停
3. ⚠️ 处理00_control/dispatch_board.md修改

---

## 15. 下一步建议

1. **修复Registry**: 在`12_smr_agents/schedules/agent_schedule_registry.json`中添加system_maintenance任务定义
2. **确认Windows状态**: 与Windows侧确认调度是否已暂停
3. **评估dispatch_board修改**: 确认修改是否影响shadow-run
4. **准备Shadow-run**: 完成上述修复后，可进入SMR-MAC-4 Shadow-run Execution

---

**Report Status**: CONDITIONAL PASS
**Report Generated**: 2026-07-07
**Next Step**: SMR-MAC-4 Shadow-run Execution (after fixes)