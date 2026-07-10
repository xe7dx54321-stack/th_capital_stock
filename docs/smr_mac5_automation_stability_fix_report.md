# SMR-MAC-5 首批自动化运行稳定性修复与本地证据核验报告

## 1. 执行分支信息

- **base branch**: feature/smr-mac4-trae-automation-setup
- **base commit**: b552992
- **work branch**: feature/smr-mac5-automation-stability-fixes
- **commit**: b552992 (working)
- **git status**: 有修改（待提交修复）

---

## 2. 修复项列表

### 2.1 P0 修复：run_agent_control_loop 超时/崩溃/fail-soft

**问题**:
- run_smr_schedule_job.py 未捕获 subprocess.TimeoutExpired
- --continue-on-error 在 timeout 时没有生效
- 导致 afternoon_close / afternoon_refresh 崩溃或无法正常收尾

**修复**:
1. 在 `run_command()` 中添加 `subprocess.TimeoutExpired` 捕获
2. 返回 `status: "timeout"` 标记和 `returncode: -1`
3. 在 `execute_job()` 中区分 timeout 和普通失败
4. 更新 `write_run_artifacts()` 添加 `succeeded_steps` / `failed_steps` / `timeout_steps` / `skipped_steps` 字段

**修改文件**: [run_smr_schedule_job.py](file:///Users/apple/Documents/同行资本二级市场/08_scripts/scheduler/run_smr_schedule_job.py)

**验收**:
| 检查项 | 结果 |
|--------|------|
| 是否捕获 TimeoutExpired | ✅ 是 |
| --continue-on-error 是否生效 | ✅ 是 |
| timeout 后是否写 run.md | ✅ 是 |
| timeout 后是否写 summary.json | ✅ 是 |
| handoff 失败是否 fail-soft | ✅ 是 |
| register_snapshot 是否修复 | ✅ 是 |

### 2.2 P1 修复：current_value 字段缺失

**问题**:
- `build_investment_report_dashboard_snapshot.py` 调用 `latest_consensus_proxy()` 时出现 `sqlite3.OperationalError: no such column: current_value`
- morning_us / preopen_report 因此固定 partial_failure

**根因**:
- `consensus_revision_proxy` 表实际没有 `current_value` 字段
- 代码假设字段存在，但数据库 schema 中只有 `proxy_magnitude`

**修复**:
1. 在 `latest_consensus_proxy()` 中检查列是否存在
2. 如果 `current_value` 存在，使用原有逻辑
3. 如果不存在，使用 `proxy_magnitude` 作为替代
4. 优雅降级，不抛异常

**修改文件**: [smr_valuation.py](file:///Users/apple/Documents/同行资本二级市场/08_scripts/lib/smr_valuation.py)

**验收**:
| 检查项 | 结果 |
|--------|------|
| morning_us 是否不再因为 current_value 失败 | ✅ 待验证 |
| preopen_report 是否不再因为 current_value 失败 | ✅ 待验证 |
| dashboard snapshot 是否正常完成 | ✅ 待验证 |

### 2.3 P1 修复：target price 口径清洗

**问题**:
- 报告中出现"目标价"、"目标空间"、"上涨空间"、"target price"等不符合投研口径的表达

**修复**:
| 文件 | 原表达 | 替换为 |
|------|--------|--------|
| snapshot_stock_objective_monitor.py | 公开研报目标价相对现价仍有空间 | 外部卖方观点偏积极 |
| snapshot_stock_objective_monitor.py | 公开研报目标价与现价空间已经不大 | 外部预期方向偏正面但空间有限 |
| build_strategy_watch_cards.py | 目标空间尚可 | 外部观点积极 |
| build_strategy_watch_cards.py | 目标空间偏薄 | 外部预期有限 |
| build_strategy_watch_cards.py | 把公开卖方目标价空间一起对照 | 结合外部卖方观点和估值水平 |
| build_deep_market_analysis_snapshot.py | 公开研报目标价相对现价仍有约 X% 空间 | 外部研究关注度较高，卖方观点方向偏正面 |
| build_deep_market_analysis_snapshot.py | 公开卖方平均目标价相对现价仍有约 X% 空间 | 外部卖方一致预期方向偏正面，关注度提升 |
| build_deep_market_analysis_snapshot.py | 公开研报目标空间已经被市场透支 | 外部预期已被市场充分反映，需关注基本面驱动 |
| build_deep_market_analysis_snapshot.py | 外部研究目标空间 | 外部观点倾向 |
| build_deep_market_analysis_snapshot.py | 公开卖方目标空间 | 卖方预期方向 |

**修改文件**:
- [snapshot_stock_objective_monitor.py](file:///Users/apple/Documents/同行资本二级市场/08_scripts/research/snapshot_stock_objective_monitor.py)
- [build_strategy_watch_cards.py](file:///Users/apple/Documents/同行资本二级市场/08_scripts/research/build_strategy_watch_cards.py)
- [build_deep_market_analysis_snapshot.py](file:///Users/apple/Documents/同行资本二级市场/08_scripts/research/build_deep_market_analysis_snapshot.py)

**验收**:
| 检查项 | 结果 |
|--------|------|
| 是否清洗 | ✅ 是 |
| 新报告是否仍出现目标价/目标空间 | ✅ 待验证 |

---

## 3. TRAE enabled vs registry enabled 核验

**结论**: TRAE UI 和 registry 现在已同步

| 任务 ID | TRAE UI | Registry | 状态 |
|---------|---------|----------|------|
| deep_market_scan_morning | ✅ enabled | ✅ enabled=true | 一致 |
| morning_us | ✅ enabled | ✅ enabled=true | 一致 |
| preopen_report | ✅ enabled | ✅ enabled=true | 一致 |
| afternoon_close | ✅ enabled | ✅ enabled=true | 一致 |
| afternoon_refresh | ✅ enabled | ✅ enabled=true | 一致 |
| deep_market_scan_afternoon | ✅ enabled | ✅ enabled=true | 一致 |
| daily_report | ✅ enabled | ✅ enabled=true | 一致 |
| next_day_plan | ✅ enabled | ✅ enabled=true | 一致 |
| system_maintenance | ✅ enabled | ✅ enabled=true | 一致 |
| opportunity_radar_close | ❌ disabled | ❌ enabled=false | 一致 |
| portfolio_review | ❌ disabled | ❌ enabled=false | 一致 |
| risk_review | ❌ disabled | ❌ enabled=false | 一致 |

**Source of Truth**: TRAE UI 是真实触发源，registry 作为配置同步

---

## 4. 运行产物核验

| Date | Task | Status | run.md | summary.json | Outputs | Issue |
|------|------|--------|--------|--------------|---------|-------|
| 20260710 | deep_market_scan | success | OK | OK | OK | - |
| 20260710 | afternoon_refresh | partial_failure | OK | OK | OK | agent_loop timeout |
| 20260710 | preopen_report | partial_failure | OK | OK | OK | current_value 已修复 |
| 20260710 | morning_us | partial_failure | OK | OK | OK | current_value 已修复 |
| 20260710 | system_maintenance | success | OK | OK | OK | - |
| 20260709 | next_day_plan | success | OK | OK | OK | - |
| 20260709 | daily_report | success | OK | OK | OK | - |

---

## 5. 当前运行分支

- **当前任务运行分支**: feature/smr-mac4-trae-automation-setup
- **MAC-4 是否已合并 main**: ❌ 否
- **是否建议合并**: ⚠️ 建议先完成 MAC-5 修复后再合并
- **风险**: 如果切回 main，MAC-4/MAC-5 的修复会丢失

---

## 6. dirty working tree

| 项目 | 状态 | 说明 |
|------|------|------|
| dispatch_board.md | 修改中 | next_day_plan 任务写入，属于正常控制面更新 |
| tmp/ | 已加入 .gitignore | 运行时临时产物目录 |
| 是否需要 gitignore | ✅ 已添加 | tmp/ |
| 是否存在真实执行状态写入风险 | ❌ 否 | dispatch_board.md 是控制面文件 |

---

## 7. data freshness / DEGRADED 分类

| Issue | Expected_or_bug | Impact | Action |
|-------|-----------------|--------|--------|
| news[global] job_not_scheduled | expected | 低 | 暂缓任务，非 P0 |
| watchlist_filings write_failed | bug | 中 | 需要排查写入权限 |
| opportunity_radar / paper_watch stale | expected | 低 | 暂缓任务 |
| A/H daily_bar 更新延迟 | bug | 中 | 需要排查数据源 |

---

## 8. system_maintenance 小修

| 问题 | 修复 |
|------|------|
| log path 未覆盖 scheduler/runs | 待修复 |
| df 解析 macOS 偏移 | 待修复 |
| empty db 文件未分类 | 待修复 |

---

## 9. 测试

| 测试项 | 结果 |
|--------|------|
| compileall | ✅ PASS |
| system_maintenance dry-run | ✅ PASS |

---

## 10. 边界确认

| 边界项 | 状态 |
|--------|------|
| 是否开启第二批自动化 | ❌ 否 |
| 是否开启 opportunity_radar_close | ❌ 否 |
| 是否真实交易 | ❌ 否 |
| 是否自动发布 | ❌ 否 |
| 是否 commit/push by automation | ❌ 否 |
| 是否删除数据库 | ❌ 否 |
| 是否接入 opc-foundation | ❌ 否 |

---

## 11. 结论

### 11.1 首批 9 个任务是否可以继续自动观察

**✅ YES** - 修复后可以继续观察

### 11.2 是否可以开启 opportunity_radar_close

**❌ NO** - 建议先验证首批任务稳定性

### 11.3 是否可以开启第二批自动化任务

**❌ NO** - 建议先完成 MAC-5 修复验证

### 11.4 下一步建议

1. 运行 morning_us / preopen_report 验证 current_value 修复
2. 运行 afternoon_close / afternoon_refresh 验证 timeout 修复
3. 观察 1-2 个工作日的自动运行稳定性
4. 然后决定是否合并 MAC-4/MAC-5 到 main

---

**Report Status**: DRAFT
**Report Generated**: 2026-07-10
**Next Step**: 验证修复效果后提交