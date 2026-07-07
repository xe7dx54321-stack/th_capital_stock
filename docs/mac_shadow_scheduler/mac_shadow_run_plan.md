# Mac Shadow-Run Plan

## 1. 概述

本文档定义Mac侧TRAE自动化任务的shadow-run观察计划。

**状态**: DRAFT - 仅供审阅，不得启用
**生效时间**: 待D7阶段及用户明确批准后
**当前阶段**: SMR-MAC-2 准备阶段

---

## 2. 目标

1. 在Mac侧验证调度系统功能完整性
2. 验证Windows/Mac数据一致性
3. 逐步启用低风险任务，观察3-5个交易日
4. 确认无冲突后再考虑生产启用

---

## 3. 第一批 Shadow-Run 任务（9个）

| 序号 | Task ID | 时间 | 风险等级 | 状态 |
|------|---------|------|---------|------|
| 1 | deep_market_scan_morning | 05:00 工作日 | 低 | 待启用 |
| 2 | morning_us | 06:00 工作日 | 低 | 待启用 |
| 3 | preopen_report | 09:00 工作日 | 低 | 待启用 |
| 4 | afternoon_close | 15:30 工作日 | 低 | 待启用 |
| 5 | afternoon_refresh | 16:30 工作日 | 低 | 待启用 |
| 6 | deep_market_scan_afternoon | 16:55 工作日 | 低 | 待启用 |
| 7 | daily_report | 20:30 工作日 | 低 | 待启用 |
| 8 | next_day_plan | 22:00 工作日 | 低 | 待启用 |
| 9 | system_maintenance | 03:00 周日 | 低 | 待启用 |

### 3.1 启用顺序建议

按依赖关系从前往后启用，每个任务观察1-2天后再启用下一个：

```
第1天: deep_market_scan_morning
第2天: morning_us
第3天: preopen_report
第4-5天: afternoon_close + afternoon_refresh + deep_market_scan_afternoon
第6天: daily_report + next_day_plan
第2周周日: system_maintenance
```

---

## 4. 暂缓任务（6个）

| Task ID | 风险等级 | 暂缓原因 | 预计启用阶段 |
|---------|---------|---------|-------------|
| portfolio_review | 中高 | 盈亏计算 + thesis判断 + 调仓建议 | D7 |
| risk_review | 中高 | 风控检查 + 风险预警 + 处理建议 | D7 |
| investment_analysis | 高 | 投资研究综合报告 | D7 |
| report_writing | 高 | 周报包含组合表现 + thesis回顾 | D7 |
| risk_governance | 中 | 风险案例库 + playbook更新 | D7 |
| report_exec | 中 | 报告分发需确认接收方 | D7 |

---

## 5. 人工审核任务（1个）

| Task ID | 风险等级 | 审核原因 |
|---------|---------|---------|
| opportunity_radar_close | 中 | 包含攻防推演 + 纸面复盘，输出可能接近投资建议 |

**审核要点**:
- 攻防推演是否包含买入/卖出建议？
- 纸面复盘是否包含仓位建议？
- 机会雷达是否包含目标价？

---

## 6. Shadow-Run 模式说明

### 6.1 Shadow-Run 模式特征

```
enabled: false                 # 默认不启用
mode: shadow_run               # 影子运行模式
observation_only: true         # 仅观察
dry_run: true                  # 干运行，不写数据库
review_only: true              # 仅人工审阅
backend_write_allowed: false   # 禁止写后台
commit_allowed: false          # 禁止git commit
push_allowed: false            # 禁止git push
production_enabled: false      # 非生产模式
launchd_load_allowed: false    # 禁止加载launchd
```

### 6.2 System Maintenance 特殊限制

system_maintenance任务在shadow-run期间**只允许**:
1. `git status` - 检查状态
2. `disk usage` - 磁盘使用量
3. `db file size` - 数据库文件大小
4. `quarantine size` - 隔离区大小
5. `recent log presence` - 检查近期日志是否存在
6. `scheduler config validation` - 配置文件语法校验

**严格禁止**:
- ❌ 删除任何文件
- ❌ VACUUM数据库
- ❌ 清理主数据库
- ❌ 操作.git目录
- ❌ 永久删除quarantine文件
- ❌ 任何自动修复操作

---

## 7. Windows/Mac 并行风险

### 7.1 风险场景

如果Mac和Windows同时运行同一任务：
- **数据库并发写入**: 可能导致数据损坏
- **文件冲突**: 同一输出目录两边同时写入
- **结果不一致**: 两边输出不同步

### 7.2 缓解措施

1. **Shadow-run期间禁用Windows侧调度**
2. **使用相同数据库文件**（路径映射一致）
3. **观察期内每天对比输出**
4. **确认无冲突后再考虑双活模式**

### 7.3 验证步骤

启用任何任务前必须：
1. 确认Windows侧对应任务已暂停
2. 手动触发一次Mac任务
3. 检查输出目录是否有新文件
4. 确认数据完整性
5. 人工审核输出内容

---

## 8. 观察期计划（3-5个交易日）

### 8.1 每日检查清单

- [ ] 任务是否按时触发
- [ ] 日志是否正常输出
- [ ] 数据库文件大小是否正常
- [ ] 输出目录是否有新文件
- [ ] 与Windows侧输出对比是否一致
- [ ] 有无异常报错

### 8.2 观察指标

| 指标 | 预期 |
|------|------|
| 任务按时启动率 | 100% |
| 任务成功率 | > 95% |
| 数据一致性 | > 99% |
| 异常报错数 | 0 |

### 8.3 通过标准

连续3-5个交易日后，如满足以下条件则认为shadow-run通过：
1. 所有已启用任务按时成功执行
2. 输出数据与Windows侧一致
3. 无异常报错或数据损坏
4. 用户审核通过输出内容

---

## 9. 正式启用前置条件

1. ✅ D6.2 Dashboard真实数据验收通过
2. ✅ D6.2 合并main
3. ⏳ 3-5个交易日shadow-run观察通过
4. ⏳ Windows侧调度确认暂停
5. ⏳ 用户明确批准启用
6. ⏳ Mac侧环境变量配置完成
7. ⏳ 敏感变量（CFS_TOKEN等）配置完成

---

## 10. 回滚方案

如shadow-run期间发现问题：
1. 立即停止launchd任务：`launchctl unload ...`
2. 检查数据库完整性
3. 恢复Windows侧调度
4. 分析问题原因
5. 修复后重新观察

---

**Document Status**: DRAFT
**Last Updated**: 2026-07-07
**Next Review**: After D6.2 main merge
