# SMR Task Registry Runbook

## 目标

把“脚本跑过了”升级成“系统里关键对象的状态被持续追踪”。

现在 registry 负责承接两类东西：

- 批次级快照
- Wiki 治理对象快照
- 运营面快照

---

## 当前已接入的实体

### 批次级实体

- `market_data_harvest`
  - `entity_id = 执行日期`
- `trend_factor_snapshot`
  - `entity_id = all_equities / ts_code__xxx`
- `fundamental_factor_snapshot`
  - `entity_id = all_equities / code__xxx`
- `us_linkage_factor_snapshot`
  - `entity_id = 最新 trade_date`
- `us_signal_snapshot`
  - `entity_id = 执行日期`
- `portfolio_pnl_snapshot`
  - `entity_id = 执行日期`
- `risk_monitor_snapshot`
  - `entity_id = 执行日期`
- `daily_reporting_snapshot`
  - `entity_id = 最新日报日期`
- `trend_research_batch`
  - `entity_id = 最新 A 股交易日`
- `dynamic_pool_snapshot`
  - `entity_id = 快照日期`
- `research_quality_snapshot`
  - `entity_id = 快照日期`
- `source_manifest`
  - `entity_id = source_manifest_latest`
- `ingest_draft_batch`
  - `entity_id = all_active / source_type__xxx / source_id__xxx`
- `ingest_draft_scan`
  - `entity_id = all_drafts`
- `review_queue`
  - `entity_id = manual_governance`

### 对象级实体

- `wiki_draft`
  - `entity_id = draft_id`
- `wiki_knowledge_entry`
  - `entity_id = knowledge_id`
- `model_task_packet`
  - `entity_id = handoff_id`
- `model_shadow_execution`
  - `entity_id = handoff_id`

---

## 当前状态语义

### 批次级常见状态

- `generated`
- `updated`
- `harvested`
- `computed`
- `upserted`
- `scanned`
- `queued`
- `reconciled`
- `signals_saved`
- `no_change`
- `clear`
- `recorded`
- `empty`

### Wiki draft 常见状态

- `ready`
- `review_required`
- `duplicate_source`
- `duplicate_thesis`
- `rejected`
- `reopened`
- `imported`

---

## 已接入脚本

### 数据 / 因子 / 风控 / 日报主链

- `08_scripts/data_harvester/ah_daily_bar.py`
- `08_scripts/us_signal_harvester/earnings_monitor.py`
- `08_scripts/factor_engine/trend.py`
- `08_scripts/factor_engine/fundamental.py`
- `08_scripts/factor_engine/us_linkage.py`
- `08_scripts/portfolio/pnl.py`
- `08_scripts/risk_engine/monitor.py`
- `08_scripts/reporting/snapshot_daily_reporting.py`

### 研究与股票池主链

- `08_scripts/research/generate_trend_batch.py`
- `08_scripts/stock_pool/reconcile_dynamic_pool.py`
- `08_scripts/research/summarize_research_quality.py`

### Wiki 治理主链

- `08_scripts/wiki/build_source_manifest.py`
- `08_scripts/wiki/create_ingest_draft.py`
- `08_scripts/wiki/scan_ingest_drafts.py`
- `08_scripts/wiki/build_review_queue.py`
- `08_scripts/wiki/resolve_review.py`
- `08_scripts/wiki/import_wiki_entry.py`

### 模型接入脚手架

- `08_scripts/agents/build_model_task_packet.py`
- `08_scripts/agents/run_model_shadow.py`

### 沙盒验证脚本

- `08_scripts/verification/validate_portfolio_gates.py`
- `08_scripts/verification/validate_risk_alert_agent_chain.py`
- `08_scripts/verification/validate_us_signal_agent_chain.py`

---

## 推荐运行顺序

```bash
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --a-only
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --hk-only
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --us-only
python3 08_scripts/us_signal_harvester/earnings_monitor.py
python3 08_scripts/factor_engine/trend.py
python3 08_scripts/factor_engine/fundamental.py
python3 08_scripts/factor_engine/us_linkage.py
python3 08_scripts/research/generate_trend_batch.py
python3 08_scripts/stock_pool/reconcile_dynamic_pool.py
python3 08_scripts/research/summarize_research_quality.py
python3 08_scripts/portfolio/pnl.py
python3 08_scripts/risk_engine/monitor.py
python3 08_scripts/reporting/snapshot_daily_reporting.py
python3 08_scripts/reporting/materialize_daily_report.py
python3 08_scripts/reporting/snapshot_daily_reporting.py
python3 08_scripts/wiki/build_source_manifest.py
python3 08_scripts/wiki/create_ingest_draft.py --limit 100 --include-existing
python3 08_scripts/wiki/scan_ingest_drafts.py --limit 200
python3 08_scripts/wiki/build_review_queue.py --include-blocked --include-rejected --limit 100
```

说明：

- `ah_daily_bar.py` 和 `fundamental.py` 会访问外部数据源，适合在正常行情更新窗口执行。
- `materialize_daily_report.py` 会把候选稿编译成正式日报，再次执行 `snapshot_daily_reporting.py` 可以让日报快照切回 `recorded`。
- 其余脚本可直接基于本地已有数据库做状态快照。

如果要验证正式导入链路，可以再执行一条自动 ready draft：

```bash
python3 08_scripts/wiki/import_wiki_entry.py \
  --draft-id 'draft__pool_snapshot__2026-04-13_dynamic_watchlist'
```

---

## 怎么查

### 看最新快照

```bash
python3 08_scripts/registry/query_registry.py --limit 20
```

### 查某个批次对象历史

```bash
python3 08_scripts/registry/query_registry.py \
  --entity-type dynamic_pool_snapshot \
  --entity-id 2026-04-13 \
  --show-payload
```

```bash
python3 08_scripts/registry/query_registry.py \
  --entity-type trend_research_batch \
  --entity-id 2026-04-10 \
  --show-payload
```

### 查某个 draft 生命周期

```bash
python3 08_scripts/registry/query_registry.py \
  --entity-type wiki_draft \
  --entity-id 'draft__pool_snapshot__2026-04-13_dynamic_watchlist' \
  --show-payload
```

### 查某个正式知识页

```bash
python3 08_scripts/registry/query_registry.py \
  --entity-type wiki_knowledge_entry \
  --entity-id 'timelines__pool_snapshot_2026_04_13_dynamic_watchlist' \
  --show-payload
```

### 查风控 / 日报 / 因子快照

```bash
python3 08_scripts/registry/query_registry.py \
  --entity-type risk_monitor_snapshot \
  --entity-id 2026-04-13 \
  --show-payload
```

```bash
python3 08_scripts/registry/query_registry.py \
  --entity-type daily_reporting_snapshot \
  --entity-id 2026-04-13 \
  --show-payload
```

```bash
python3 08_scripts/registry/query_registry.py \
  --entity-type trend_factor_snapshot \
  --entity-id all_equities \
  --show-payload
```

---

## 当前这层解决了什么问题

- 能看到一条批次任务到底产出了哪些关键文件
- 能看到某个 wiki draft 是怎么从 `create -> scan -> import` 演进的
- 能把“今天股票池为什么变成这样”落成结构化快照
- 能把“今天因子有没有跑、风险是不是清空、日报面现在长什么样”落成结构化快照
- 后面接双 agent 协作时，handoff 就不用只靠日志和口头描述

---

## 当前还没做的事

- 日报生成本体仍然主要靠 agent / 人工，当前接入的是 `reporting snapshot`，不是完整 report compiler
- 开仓尝试、持仓变更、用户确认动作还没统一接进 registry
- 还没有做面向 registry 的统一 dashboard
- 还没有基于 registry 做自动重跑、失败恢复、依赖追踪
- 双 agent handoff 契约还没正式落表，下一步看：
  - [smr-dual-agent-architecture.md](/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/09_runbooks/smr-dual-agent-architecture.md)
