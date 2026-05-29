# Phase 68: Evidence Memory & Internal Research Brief Upgrade v1

## 日期
2026-05-29

## 前置阶段
Phase 67b (commit 49a5a2b)

## 目标
- 建立真实 evidence memory，沉淀 Phase 67b 23 条 deep evidence
- 建立 source trace index，每条 evidence 可追溯
- 建立 evidence-to-claim linkage，每个 supported claim 有证据支撑
- 建立 claim state memory，记录状态变化
- 生成 evidence-backed watchlist packet
- 输出 observed-first 内部投研跟踪简报
- 建立 brief quality lint，确保简报无系统后台词/教学式提醒/交易建议

## 核心边界
- supported != confirmed
- ASP/客户份额/具体订单量仍不能确认
- 不输出交易建议
- 不出现系统后台词
- 不出现教学式提醒
- 不使用 mock/fixture
- 不提交 generated evidence memory
