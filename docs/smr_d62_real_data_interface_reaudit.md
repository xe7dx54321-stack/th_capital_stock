# SMR-D6.2 真实数据接口复核审计

## 概述

本文件记录 SMR-D6.2 阶段对系统内真实可用数据接口的系统性复核结果。

复核原则：
- 有来源才展示，有证据优先展示
- 无证据生成摘要不进主信号流
- 默认占位不冒充真实数据
- 所有进入页面的数据都要有 provenance
- 不写后台，只读展示
- 不接 opc-foundation

## 接口复核结果

| 接口 | 路径 | 数据类型 | 是否真实 | 是否有来源 | 是否有证据 | 可接入页面 | 优先级 | 处理方式 |
|---|---|---|---|---|---|---|---|---|
| source_registry | backend_state.dashboard_state.source_registry | 信息源注册表 | 是 | 是 | 部分 | coverage, signals, health | P0 | 全量接入，作为覆盖池和数据健康的核心数据源 |
| daily_report | backend_state.dashboard_state.daily_report | 日报快照 | 是 | 是 | 部分 | today, signals, research | P0 | 接入今日总览 highlights 和信号流，带 source_url/report_path |
| evidence_gaps | backend_state.dashboard_state.evidence_gaps | 证据缺口 | 是 | 是 | 是 | signals, research, coverage | P0 | 接入研究队列和信号流，作为研究候选来源 |
| strategy_watch | backend_state.dashboard_state.strategy_watch | 策略观察 | 是 | 是 | 部分 | today, coverage, research | P0 | 接入今日总览 top_focus 和覆盖池 |
| overview | backend_state.dashboard_state.overview | 总览状态 | 是 | 是 | 部分 | today, health | P0 | 接入今日总览和数据健康的新鲜度 |
| run_log | backend_state.dashboard_state.operations.run_log | 运行日志 | 是 | 是 | 否 | health | P0 | 接入数据健康的运行状态 |
| opportunity_engine | backend_state.dashboard_state.opportunity | 机会引擎 | 是 | 是 | 部分 | signals, research | P1 | 有 source 的机会接入研究队列候选 |
| market_events | backend_state.dashboard_state.market_events | 市场事件 | 是 | 是 | 部分 | signals, today | P1 | 有 source 的事件接入信号流 |
| risk_monitor | backend_state.dashboard_state.risk.monitor | 风险监控 | 是 | 部分 | 低 | signals, health | P2 | 仅 source-backed 风险提示可进入低可信候选区 |
| risk_decision | backend_state.dashboard_state.risk.decision | 风险决策 | 是 | 部分 | 低 | signals | P2 | 机械式风险模板过滤，不进入主信号流 |
| foundation_input_stream | N/A | Foundation 输入流 | 否 | 否 | 否 | N/A | pending | 待 D7 接入，当前标记 pending_integration |

## P0 级接口详细说明

### 1. source_registry
- **数据类型**: 信息源注册表快照
- **真实度**: evidence_backed_real
- **可用字段**: sources, source_count, health_status
- **接入页面**: 覆盖池、信号流、数据健康
- **provenance**: 高 - 每个 source 都有 source_type/source_name/source_url
- **处理方式**: 全量接入，作为覆盖池对象的真实来源统计

### 2. daily_report
- **数据类型**: 日报快照
- **真实度**: real_snapshot_with_source
- **可用字段**: highlights, themes, published_at, report_path
- **接入页面**: 今日总览、信号流、研究队列
- **provenance**: 中高 - 有 report_path 和 published_at 的为高可信
- **处理方式**: highlights 接入今日总览和信号流，带 source badge

### 3. evidence_gaps
- **数据类型**: 证据缺口列表
- **真实度**: evidence_backed_real
- **可用字段**: entity, gap_type, source_ref, evidence_id
- **接入页面**: 信号流、研究队列、覆盖池
- **provenance**: 高 - 有 evidence_id 和 source_ref
- **处理方式**: 接入研究队列作为待研究项，带证据缺口来源

### 4. strategy_watch
- **数据类型**: 策略观察列表
- **真实度**: real_snapshot_with_source
- **可用字段**: top_focus_items, thesis, watch_items
- **接入页面**: 今日总览、覆盖池、研究队列
- **provenance**: 中 - 有 source_name，缺完整 evidence packet
- **处理方式**: top_focus_items 接入今日总览，watch_items 接入覆盖池

### 5. overview
- **数据类型**: 总览状态
- **真实度**: real_snapshot_with_source
- **可用字段**: market_status, freshness, summary_stats
- **接入页面**: 今日总览、数据健康
- **provenance**: 中 - 后台快照，有来源标记
- **处理方式**: 接入今日总览摘要和数据健康新鲜度

### 6. run_log
- **数据类型**: 运行日志
- **真实度**: real_snapshot_no_evidence
- **可用字段**: recent_runs, today_count, status_counts
- **接入页面**: 数据健康
- **provenance**: 低 - 真实快照但缺 source_url/evidence
- **处理方式**: 接入数据健康的运行状态展示

## P1 级接口详细说明

### 7. opportunity_engine
- **数据类型**: 机会引擎
- **真实度**: real_snapshot_with_source
- **可用字段**: watchlist_signals, opportunity_candidates
- **接入页面**: 信号流、研究队列
- **provenance**: 中 - 有 source_type/source_name
- **处理方式**: 有 source 的机会接入研究队列候选，不进入主信号流

### 8. market_events
- **数据类型**: 市场事件
- **真实度**: real_snapshot_with_source
- **可用字段**: upcoming_events, recent_events
- **接入页面**: 今日总览、信号流
- **provenance**: 中 - 有 event_source 和 event_time
- **处理方式**: 有 source 的事件接入信号流低可信区

## P2 级接口详细说明

### 9. risk_monitor
- **数据类型**: 风险监控
- **真实度**: real_snapshot_no_evidence
- **可用字段**: alerts, blocking_issues
- **接入页面**: 信号流、数据健康
- **provenance**: 低 - 缺 source_url 和 evidence_packet
- **处理方式**: 仅 source-backed 风险提示可进入低可信候选区，generated/default/placeholder 过滤

### 10. risk_decision
- **数据类型**: 风险决策
- **真实度**: mixed
- **可用字段**: sell_candidates, risk_level
- **接入页面**: 信号流
- **provenance**: 低 - 机械式风险模板，缺 evidence
- **处理方式**: 全部过滤，不进入主信号流

## 待接入接口

### 11. foundation_input_stream
- **状态**: pending_integration
- **计划**: D7 阶段接入
- **当前处理**: 在 real_data_inventory 中标记为 pending_integrations
- **页面显示**: "Foundation 输入流待接入

## 真实数据覆盖统计

- **总接口数**: 11
- **P0 可用**: 6
- **P1 可用**: 2
- **P2 部分可用**: 2
- **待接入**: 1 (foundation_input_stream)

## 过滤规则：
1. evidence_backed_real → 主信号流
2. real_snapshot_with_source → 主信号流
3. real_snapshot_no_evidence → 低可信候选区
4. generated_summary → 过滤
5. default_fallback → 过滤
6. placeholder → 过滤
7. historical_residual → 过滤
8. unknown → 过滤
