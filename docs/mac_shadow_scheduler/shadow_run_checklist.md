# Shadow-Run Checklist

> **状态**: DRAFT - 仅供审阅
> **用途**: Mac TRAE shadow-run 启用前检查清单

---

## Phase 0: 前置条件（当前阶段）

- [x] D6.2 Dashboard 真实数据验收通过
- [x] D6.2 合并 main
- [x] MAC-1 迁移 intake 完成
- [x] MAC-2 shadow-run 配置草案完成
- [ ] 用户批准shadow-run计划
- [ ] Mac侧环境变量配置完成
- [ ] Windows侧调度确认暂停

---

## Phase 1: 单任务测试（第1天）

### deep_market_scan_morning

- [ ] 确认Windows侧 `deep_market_scan_morning` 已暂停
- [ ] 手动执行 dry-run:
  ```bash
  cd /Users/apple/Documents/同行资本二级市场
  python3 08_scripts/scheduler/run_agent_schedule.py \
    --schedule-id deep_market_scan_morning --dry-run
  ```
- [ ] 检查日志输出
- [ ] 确认无异常报错
- [ ] 确认数据库文件未损坏
- [ ] 人工审核输出内容
- [ ] 加载launchd任务（仅一个）
- [ ] 等待下一次自动触发
- [ ] 验证自动触发成功
- [ ] 观察1天，无问题后进入下一个任务

---

## Phase 2: 早间链（第2-3天）

### morning_us

- [ ] 确认Windows侧已暂停
- [ ] 手动执行 dry-run
- [ ] 检查日志输出
- [ ] 确认美股数据采集正常
- [ ] 人工审核输出
- [ ] 加载launchd任务
- [ ] 观察1天

### preopen_report

- [ ] 确认Windows侧已暂停
- [ ] 手动执行 dry-run
- [ ] 检查日报生成
- [ ] 确认无投资建议内容
- [ ] 加载launchd任务
- [ ] 观察1天

---

## Phase 3: 午后链（第4-5天）

### afternoon_close

- [ ] 确认Windows侧已暂停
- [ ] 手动执行 dry-run
- [ ] 检查行情/因子/池子数据
- [ ] 确认数据完整性
- [ ] 加载launchd任务

### afternoon_refresh

- [ ] 手动执行 dry-run
- [ ] 检查因子补跑结果
- [ ] 加载launchd任务

### deep_market_scan_afternoon

- [ ] 手动执行 dry-run
- [ ] 检查MarketScreener数据
- [ ] 加载launchd任务

- [ ] 观察1-2天，午后链全部稳定

---

## Phase 4: 晚间链（第6天）

### daily_report

- [ ] 手动执行 dry-run
- [ ] 检查日报物化文件
- [ ] 确认无投资建议内容
- [ ] 加载launchd任务

### next_day_plan

- [ ] 手动执行 dry-run
- [ ] 检查次日计划输出
- [ ] 加载launchd任务

---

## Phase 5: 系统维护（第2周周日）

### system_maintenance

**⚠️ 严格限制模式**

- [ ] 确认维护脚本只执行只读操作
- [ ] 检查脚本中无删除命令
- [ ] 检查脚本中无VACUUM
- [ ] 手动执行 dry-run
- [ ] 验证输出只有状态检查
- [ ] 确认无文件被修改
- [ ] 确认数据库未被修改
- [ ] 确认.git目录未被修改
- [ ] 确认quarantine未被修改
- [ ] 加载launchd任务
- [ ] 周日凌晨观察执行结果

---

## Phase 6: 观察期总结

### 3-5个交易日后

- [ ] 所有已启用任务按时执行
- [ ] 任务成功率 > 95%
- [ ] 日志无异常报错
- [ ] 数据库文件大小正常
- [ ] 输出目录文件正常
- [ ] 与Windows侧输出对比一致（如适用）
- [ ] 用户审核通过所有输出
- [ ] 无数据损坏迹象

---

## 紧急情况处理

### 发现问题时

- [ ] 立即卸载问题任务的launchd
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.tonghang.smr.agent.{task_id}.plist
  ```
- [ ] 检查数据库完整性
- [ ] 分析错误日志
- [ ] 评估影响范围
- [ ] 如需，恢复Windows侧调度
- [ ] 记录问题并修复
- [ ] 修复后重新观察

### 全部回滚

- [ ] 卸载所有launchd任务
- [ ] 确认所有任务已停止
- [ ] 检查系统状态
- [ ] 恢复Windows侧调度
- [ ] 编写回滚报告

---

## 正式生产启用条件

全部shadow-run通过后，还需满足：

- [ ] D7 Foundation输入流集成完成
- [ ] defer_until_d7任务边界审核通过
- [ ] 所有环境变量配置完成
- [ ] 敏感变量（CFS_TOKEN等）安全存储
- [ ] 用户明确批准生产启用
- [ ] 双活或切换方案确认
- [ ] 监控告警配置完成

---

**Checklist Version**: 1.0 (DRAFT)
**Last Updated**: 2026-07-07
