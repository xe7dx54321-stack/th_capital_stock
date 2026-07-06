# SMR-D6.1 Dashboard Data Path Audit

## Overview

This document audits the actual data paths used by each Dashboard page to understand what data is being displayed.

## Page Data Paths

### 1. Signal Flow (`/signals`)

| UI 模块 | 当前读取字段 | 来源类型 | data_status | 是否有原文 | 是否有证据包 | 是否可能是 fallback | 问题 |
|---|---|---|---|---|---|---|---|
| 风险提示 | risk.decision.sell_candidates | generated_summary | 无 | 否 | 否 | **是** | 硬编码模板文案 |
| 证据缺口 | current_state.evidence_gaps | real_snapshot_no_evidence | 无 | 否 | 否 | 否 | 明确报告缺口 |
| 重点关注 | strategy_watch.top_focus_items | real_snapshot_with_source | 无 | 部分 | 部分 | 否 | 有来源但证据不全 |
| 机会雷达 | opportunity.markets | real_snapshot_no_evidence | 无 | 否 | 否 | 否 | 无证据链接 |
| 风险监控 | risk.monitor.alerts | real_snapshot_with_source | 无 | 部分 | 部分 | 否 | 部分有证据 |
| 日报摘要 | daily_report.highlights | real_snapshot_with_source | 无 | 部分 | 部分 | 否 | 部分有证据 |

### 2. Today Overview (`/today`)

| UI 模块 | 当前读取字段 | 来源类型 | data_status | 是否有原文 | 是否有证据包 | 是否可能是 fallback | 问题 |
|---|---|---|---|---|---|---|---|
| 今日概览卡片 | overview.* | real_snapshot | real_backend | 否 | 否 | 否 | 聚合数据 |
| 关键事件 | current_state.events | real_snapshot | real_backend | 部分 | 部分 | 否 | 部分有证据 |
| 风险摘要 | risk.decision | generated_summary | real_backend | 否 | 否 | **是** | 生成式风险决策 |
| 机会摘要 | opportunity.* | real_snapshot | real_backend | 否 | 否 | 否 | 无证据链接 |

### 3. Coverage Pool (`/coverage`)

| UI 模块 | 当前读取字段 | 来源类型 | data_status | 是否有原文 | 是否有证据包 | 是否可能是 fallback | 问题 |
|---|---|---|---|---|---|---|---|
| 股票池列表 | watchlist.* | real_snapshot_no_evidence | real_backend | 否 | 否 | 否 | 无证据 |
| 覆盖状态 | source_registry.* | evidence_backed_real | real_backend | 是 | 是 | 否 | 高质量数据 |
| 估值状态 | valuation.* | real_snapshot_no_evidence | real_backend | 否 | 否 | 否 | 无证据 |

### 4. Research Queue (`/research`)

| UI 模块 | 当前读取字段 | 来源类型 | data_status | 是否有原文 | 是否有证据包 | 是否可能是 fallback | 问题 |
|---|---|---|---|---|---|---|---|
| 研究队列 | research_queue.* | real_snapshot | real_backend | 部分 | 部分 | 否 | 部分有证据 |
| 证据缺口 | evidence_gaps.* | real_snapshot_no_evidence | real_backend | 否 | 否 | 否 | 明确报告缺口 |
| 待复核项 | review_queue.* | real_snapshot_no_evidence | real_backend | 否 | 否 | 否 | 无证据 |

### 5. Data Health (`/health`)

| UI 模块 | 当前读取字段 | 来源类型 | data_status | 是否有原文 | 是否有证据包 | 是否可能是 fallback | 问题 |
|---|---|---|---|---|---|---|---|
| 数据完整性 | data_health.* | real_snapshot | real_backend | 否 | 否 | 否 | 元数据 |
| 运行日志 | run_log.* | real_snapshot_no_evidence | real_backend | 否 | 否 | 否 | 无证据 |
| 证据覆盖率 | evidence_coverage.* | real_snapshot | real_backend | 否 | 否 | 否 | 统计数据 |

## Data Truth Assessment Summary

### High Quality Data (evidence_backed_real)
- source_registry entries with URLs
- daily_report entries with source links

### Medium Quality Data (real_snapshot_with_source)
- risk_monitor alerts with source info
- strategy_watch items with source_name

### Low Quality Data (real_snapshot_no_evidence)
- watchlist / universe
- opportunity markets
- run_log

### Generated Data (generated_summary)
- **risk_decision sell_candidates** - THE MAIN PROBLEM
- risk_decision summaries without evidence

### Default Fallback
- View model generated default values
- Missing field fill-ins

### Placeholder
- evidence_gaps (explicitly marked as gaps)

## Issues Found

1. **Signal Flow**: 70%+ of signals are generated_summary or real_snapshot_no_evidence
2. **Risk Decision**: Hardcoded templates generate identical-looking signals
3. **Mechanical Timestamps**: Signals have artificially generated timestamps (now - idx hours)
4. **No Evidence Chain**: Most signals lack source_url, evidence_packet, or original_text
5. **High Priority Mislabeling**: Generated risk signals marked as "高" strength without evidence

## Recommendations

1. **Quality Gate**: Implement quality gate in signal_flow_view_model.py
2. **Evidence Requirement**: Require source_url or evidence_packet for high-priority signals
3. **Timestamp Validation**: Validate timestamps against real data
4. **Data Status Labeling**: Add data_status field to all signals
5. **Filtered Count**: Track and display filtered signal count
