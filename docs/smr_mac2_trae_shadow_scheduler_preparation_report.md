# SMR-MAC-2 Mac TRAE Shadow Scheduler Preparation Report

## 1. 基本信息

- **任务编号**: SMR-MAC-2
- **任务名称**: Mac TRAE Shadow Scheduler Preparation
- **状态**: DRAFT - 准备完成，待D6.2 main合并后提交
- **生成日期**: 2026-07-07
- **当前分支**: feature/smr-d62c-main-staging (基础)
- **目标分支**: feature/smr-mac2-trae-shadow-scheduler-prep

---

## 2. D6.2 Main Merge 状态

### 2.1 当前状态

| 阶段 | 状态 |
|------|------|
| D6.2b 可见真实数据修复 | ✅ 已完成 |
| D6.2b 验收报告 | ✅ 已生成 |
| D6.2c staging分支 | ✅ 已创建 |
| D6.2c staging验证 | ✅ 119个测试通过 |
| D6.2c PR | ⏳ 待用户合并到main |
| D6.2c main验证 | ⏳ 待合并后执行 |

### 2.2 MAC-2 前置条件

- [x] D6.2b 验收通过
- [x] D6.2c staging验证通过
- [ ] D6.2c 合并到main（待用户操作）
- [ ] main上验证通过
- [x] MAC-1 intake文档已就绪

---

## 3. MAC-1 输入摘要

### 3.1 Mac 现有架构

Mac repo 已具备 scheduler 架构：

| 文件 | 作用 |
|------|------|
| `08_scripts/scheduler/run_smr_schedule_job.py` | 调度任务执行 |
| `08_scripts/scheduler/run_agent_schedule.py` | Agent 调度执行 |
| `08_scripts/scheduler/deploy_agent_launchd.py` | launchd 部署脚本 |
| `08_scripts/scheduler/agent_schedule_registry.json` | 任务注册表 |

### 3.2 迁移来源

- Windows: 16个自动化任务
- Mac: 0个任务（待迁移）
- 迁移策略: 分阶段 shadow-run，观察后再启用

---

## 4. 第一批 Shadow-Run 任务清单

**共 9 个任务，风险等级均为低**

| 序号 | Task ID | 时间 | 执行角色 | 风险 |
|------|---------|------|---------|------|
| 1 | deep_market_scan_morning | 05:00 工作日 | Hermes Research Curator | 低 |
| 2 | morning_us | 06:00 工作日 | OpenClaw Data Exec | 低 |
| 3 | preopen_report | 09:00 工作日 | Hermes Reporting Editor | 低 |
| 4 | afternoon_close | 15:30 工作日 | OpenClaw Data Exec | 低 |
| 5 | afternoon_refresh | 16:30 工作日 | OpenClaw Factor Exec | 低 |
| 6 | deep_market_scan_afternoon | 16:55 工作日 | Hermes Research Curator | 低 |
| 7 | daily_report | 20:30 工作日 | Hermes Reporting Editor | 低 |
| 8 | next_day_plan | 22:00 工作日 | Hermes Reporting Editor | 低 |
| 9 | system_maintenance | 周日 03:00 | OpenClaw System Exec | 低 |

### 4.1 所有任务的 Shadow-Run 配置

每个任务均配置为：

```json
{
  "enabled": false,
  "mode": "shadow_run",
  "observation_only": true,
  "dry_run": true,
  "review_only": true,
  "backend_write_allowed": false,
  "commit_allowed": false,
  "push_allowed": false,
  "production_enabled": false,
  "launchd_load_allowed": false
}
```

---

## 5. 暂缓任务清单

**共 6 个任务，暂缓至 D7**

| Task ID | 风险等级 | 暂缓原因 |
|---------|---------|---------|
| portfolio_review | 中高 | 盈亏计算 + thesis判断 + 调仓建议 |
| risk_review | 中高 | 风控检查 + 风险预警 + 处理建议 |
| investment_analysis | 高 | 投资研究综合报告 |
| report_writing | 高 | 周报包含组合表现 + thesis回顾 |
| risk_governance | 中 | 风险案例库 + playbook更新 |
| report_exec | 中 | 报告分发需确认接收方 |

---

## 6. Manual Review 任务

**共 1 个任务，需人工审核后再决定**

| Task ID | 风险等级 | 审核原因 |
|---------|---------|---------|
| opportunity_radar_close | 中 | 包含攻防推演 + 纸面复盘，输出可能接近投资建议 |

---

## 7. Shadow-Run 配置草案路径

### 7.1 文档清单

| 文档 | 路径 | 状态 |
|------|------|------|
| Shadow Run Plan | `docs/mac_shadow_scheduler/mac_shadow_run_plan.md` | ✅ DRAFT |
| Task Registry Draft | `docs/mac_shadow_scheduler/mac_trae_shadow_task_registry.draft.json` | ✅ DRAFT |
| Launchd Plist Drafts | `docs/mac_shadow_scheduler/launchd_plist_drafts.md` | ✅ DRAFT |
| Shadow Run Checklist | `docs/mac_shadow_scheduler/shadow_run_checklist.md` | ✅ DRAFT |

### 7.2 MAC-2 总报告

本文档: `docs/smr_mac2_trae_shadow_scheduler_preparation_report.md`

---

## 8. Launchd 草案路径

- **文档**: `docs/mac_shadow_scheduler/launchd_plist_drafts.md`
- **状态**: 纯文档，无实际 plist 文件
- **命名约定**: `com.tonghang.smr.agent.{schedule_id}.plist`
- **目标目录**: `~/Library/LaunchAgents/` (尚未创建)

**重要**:
- ❌ 未创建任何 plist 文件
- ❌ 未执行 `launchctl load`
- ❌ 未执行 `launchctl bootstrap`
- ❌ 未执行 `deploy_agent_launchd.py --load`
- ✅ 所有任务 `Disabled: true`
- ✅ 所有任务 `RunAtLoad: false`

---

## 9. 为什么不启用 Launchd

### 9.1 主要原因

1. **D6.2 尚未合并 main** - 真实数据功能需要在main上验证
2. **Windows/Mac 并行写入风险** - 两边同时写数据库/输出目录可能导致数据损坏
3. **需要观察期** - 3-5个交易日的shadow-run观察是必要的
4. **安全边界** - 不启用调度是最安全的准备方式
5. **用户批准** - 需要用户明确批准后才能启用

### 9.2 启用前置条件

1. D6.2 合并 main 并验证通过
2. Windows 侧调度确认暂停
3. 3-5个交易日 shadow-run 观察通过
4. 用户明确批准启用
5. Mac 侧环境变量配置完成
6. 敏感变量安全存储

---

## 10. Windows/Mac 重复写入风险

### 10.1 风险分析

| 风险点 | 严重程度 | 缓解措施 |
|--------|---------|---------|
| 数据库并发写入 | 高 | Shadow-run期间暂停Windows侧 |
| 输出目录文件冲突 | 中 | 使用相同路径，避免双写 |
| 结果不一致 | 中 | 每天人工对比输出 |
| 定时任务时间冲突 | 低 | 错开时间或暂停一边 |

### 10.2 缓解策略

1. **Shadow-run 阶段**: Mac shadow-run，Windows侧暂停对应任务
2. **过渡阶段**: 确认Mac稳定后，逐步切换，中间过渡期双系统只读验证
3. **生产阶段**: 根据最终方案决定单活或双活

---

## 11. 正式启用前置条件

### 11.1 技术条件

- [ ] D6.2 合并 main 并验证通过
- [ ] Mac 侧 Python 环境完整
- [ ] 所有依赖包已安装
- [ ] 数据库路径映射正确
- [ ] 输出目录结构一致

### 11.2 安全条件

- [ ] Windows 侧调度确认暂停
- [ ] 敏感变量（CFS_TOKEN等）安全配置
- [ ] 日志目录已创建且在.gitignore中
- [ ] 后台写入权限已确认（当前禁止）

### 11.3 流程条件

- [ ] 3-5个交易日 shadow-run 观察通过
- [ ] 用户审核通过输出内容
- [ ] 用户明确批准启用
- [ ] 回滚方案已确认

---

## 12. 3-5 个交易日 Observation 计划

### 12.1 观察周期

**预计 1 周（5个工作日 + 1个周日维护）**

### 12.2 启用顺序

```
Day 1 (Mon):  deep_market_scan_morning
Day 2 (Tue):  morning_us
Day 3 (Wed):  preopen_report
Day 4 (Thu):  afternoon_close + afternoon_refresh + deep_market_scan_afternoon
Day 5 (Fri):  daily_report + next_day_plan
Week 2 Sun:   system_maintenance
```

### 12.3 每日检查项

1. 任务是否按时触发
2. 日志是否正常输出
3. 数据库文件大小是否正常
4. 输出目录是否有新文件
5. 有无异常报错
6. 人工审核输出内容

### 12.4 通过标准

- 任务按时启动率: 100%
- 任务成功率: > 95%
- 异常报错数: 0
- 数据一致性: > 99%
- 用户审核: 通过

---

## 13. 系统维护链特别限制

### 13.1 允许操作（只读）

1. ✅ `git status` - 检查状态
2. ✅ `disk usage` - 磁盘使用量检查
3. ✅ `db file size` - 数据库文件大小检查
4. ✅ `quarantine size` - 隔离区大小检查
5. ✅ `recent log presence` - 近期日志存在性检查
6. ✅ `scheduler config validation` - 配置文件语法校验

### 13.2 禁止操作

1. ❌ 删除任何文件
2. ❌ VACUUM 数据库
3. ❌ 清理主数据库
4. ❌ 操作 .git 目录
5. ❌ 永久删除 quarantine
6. ❌ 任何自动修复操作

---

## 14. 边界确认

| 边界项 | 状态 |
|--------|------|
| 是否运行真实任务 | ❌ 否 |
| 是否写后台 | ❌ 否 |
| 是否创建启用状态任务 | ❌ 否 |
| 是否启用 launchd | ❌ 否 |
| 是否执行 deploy_agent_launchd.py --load | ❌ 否 |
| 是否接入 opc-foundation | ❌ 否 |
| 是否进入 D7 | ❌ 否 |
| 是否联网抓数据 | ❌ 否 |
| 是否修改投资逻辑 | ❌ 否 |
| 是否提交 data/db/runtime | ❌ 否 |
| 是否提交 migration_intake | ❌ 否 |
| 是否打 tag | ❌ 否 |
| 是否 merge main | ❌ 否（MAC-2分支不合并） |

---

## 15. Gate 3 检查清单

| Gate 3 检查项 | 结果 |
|--------------|------|
| 不执行 deploy_agent_launchd.py --load | ✅ PASS |
| 不创建真实启用状态的 launchd | ✅ PASS |
| 不启用 TRAE 自动化任务 | ✅ PASS |
| 不运行真实业务链 | ✅ PASS |
| 不写后台状态 | ✅ PASS |
| 不让 Mac 和 Windows 同时写同一输出目录 | ✅ PASS（已识别风险，计划中） |

**Gate 3 状态**: ✅ PASS

---

## 16. 下一步建议

1. **合并 D6.2 PR 到 main** - 需用户在GitHub操作
2. **main 上验证** - 合并后跑测试和HTTP smoke
3. **创建 MAC-2 分支** - 从 main 创建 `feature/smr-mac2-trae-shadow-scheduler-prep`
4. **提交 MAC-2 文档** - 4个shadow-scheduler文档 + 本报告
5. **等待用户批准 shadow-run**
6. **如批准，按checklist逐步启用**

---

**Report Status**: DRAFT - 待D6.2 main合并后提交
**Report Generated**: 2026-07-07
**Report Author**: TRAE Agent (GLM-5)
