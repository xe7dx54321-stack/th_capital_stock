# SMR-D6.1 Backend Interface Inventory

## Overview

This document inventories all backend data interfaces used by the Dashboard and their data quality assessment.

## Interface Inventory

| 接口/函数/文件 | 类型 | 读取路径 | 是否真实数据 | 是否生成摘要 | 是否含原文/证据 | 当前 Dashboard 使用页面 | 建议处理 |
|---|---|---|---|---|---|---|---|
| `build_dashboard_state()` | 聚合入口 | `08_scripts/lib/smr_dashboard.py` | 是 | 部分 | 部分 | 全部 5 页 | 保持核心入口 |
| `build_trade_risk_decision_snapshot.py` | Snapshot | `08_scripts/risk_engine/` | 否 | 是 | 否 | 信号流 | **标记为 generated_summary** |
| `build_risk_monitor_snapshot.py` | Snapshot | `08_scripts/risk_engine/` | 部分 | 部分 | 部分 | 信号流 | 需验证证据完整性 |
| `build_strategy_watch_snapshot.py` | Snapshot | `08_scripts/` | 是 | 否 | 部分 | 信号流 | 标记为 real_snapshot |
| `build_daily_report_snapshot.py` | Snapshot | `08_scripts/reporting/` | 是 | 是 | 部分 | 今日概览 | 需验证证据链接 |
| `build_opportunity_snapshot.py` | Snapshot | `08_scripts/opportunity/` | 是 | 否 | 部分 | 信号流 | 标记为 real_snapshot |
| `build_source_registry_snapshot.py` | Snapshot | `08_scripts/registry/` | 是 | 否 | 是 | 覆盖池 | 标记为 evidence_backed_real |
| `build_evidence_gaps_snapshot.py` | Snapshot | `08_scripts/` | 是 | 否 | 否 | 研究队列 | 标记为 real_snapshot_no_evidence |
| `build_watchlist_snapshot.py` | Snapshot | `08_scripts/stock_pool/` | 是 | 否 | 否 | 覆盖池 | 标记为 real_snapshot_no_evidence |
| `build_universe_snapshot.py` | Snapshot | `08_scripts/stock_pool/` | 是 | 否 | 否 | 覆盖池 | 标记为 real_snapshot_no_evidence |
| `build_run_log_snapshot.py` | Snapshot | `08_scripts/scheduler/` | 是 | 否 | 否 | 数据健康 | 标记为 real_snapshot_no_evidence |
| `backend_data_provider.py` | View Model | `08_scripts/dashboard/` | 聚合 | 否 | 聚合 | 全部 5 页 | 保持数据适配 |

## Key Findings

### High Quality Interfaces
1. **build_source_registry_snapshot**: Contains source URLs and evidence references
2. **build_daily_report_snapshot**: Contains published reports with source links
3. **build_strategy_watch_snapshot**: Contains real thesis data

### Low Quality / Generated Interfaces
1. **build_trade_risk_decision_snapshot**: Contains hardcoded summary templates without evidence
   - "卖出优先级已经足够高，应该先处理风险，再谈进攻。"
   - "还没到必须清仓，但更适合先做减仓或降权。"
   - "先盯紧，不急着做大动作。"
   - "当前没有足够强的卖出信号。"

### Evidence Gaps
1. **build_evidence_gaps_snapshot**: Explicitly reports missing evidence - should NOT enter main signal flow

### Snapshot Schema
The `build_dashboard_state()` function reads 58 types of snapshot entities from SQLite:
- risk_decision, risk_monitor, risk_alerts
- strategy_watch, top_focus_items
- daily_report, highlights
- opportunity, markets
- source_registry, evidence_sources
- evidence_gaps, evidence_memory
- watchlist, universe
- run_log, operations, pipeline_summary

## Data Flow

```
SQLite (smr.db)
    ↓
build_dashboard_state()
    ↓
backend_data_provider.py
    ↓
view_model.py (5 pages)
    ↓
HTML Renderer
```

## Recommendations

1. **Immediately**: Filter `trade_risk_decision` generated summaries from main signal flow
2. **Short-term**: Add evidence verification to all snapshot sources
3. **Medium-term**: Implement evidence packet requirements for high-priority signals
4. **Long-term**: Integrate Foundation evidence inflow for full evidence chain
