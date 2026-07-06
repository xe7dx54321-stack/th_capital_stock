# SMR-D6 Dashboard 后台数据源审计报告

## 1. 审计时间

2026-07-06

## 2. 审计范围

- 仓库路径：`/Users/apple/Documents/同行资本二级市场`
- 分支：`feature/smr-d6-dashboard-backend-integration`
- Base Commit：`c56d365`
- 审计目标：识别当前项目中可供 Dashboard 5 页前台使用的真实后台数据入口

## 3. 已发现的真实后台数据源

| 数据源 | 路径/入口 | 类型 | 可用字段 | 对应 Dashboard 页面 | 接入状态 | 接入阶段 |
|---|---|---|---|---|---|---|
| Dashboard State Snapshot | `smr_dashboard.build_dashboard_state()` | SQLite + Python dict | overview, risk, strategy_watch, opportunity_engine, current_state, evidence_gaps, source_registry, run_log, daily_report, pools, positions | 全部 5 页 | 已接入 | D6 |
| SQLite Database | `01_data/db/smr.db` | SQLite DB | 58 种 snapshot entity types | 全部 5 页 | 间接接入（通过 build_dashboard_state） | D6 |
| Risk Monitor | `state.risk` | dict | decision.sell_candidates, monitor.alerts | 今日总览、信号流、数据健康 | 已接入 | D6 |
| Strategy Watch | `state.strategy_watch` | dict | top_focus_items, priority_counts | 今日总览、覆盖池、研究队列 | 已接入 | D6 |
| Opportunity Engine | `state.opportunity_engine` | dict | radar.top_candidates, radar.markets | 今日总览、覆盖池、信号流 | 已接入 | D6 |
| Evidence Gaps | `state.current_state.evidence_gaps` | list | entity, gap_type, description | 今日总览、覆盖池、研究队列、信号流 | 已接入 | D6 |
| Daily Report | `state.daily_report` | dict | highlights, themes, summary_items | 今日总览、信号流、研究队列 | 已接入 | D6 |
| Source Registry | `state.source_registry` | dict | sources, counts_by_status, source_count | 数据健康、信号流 | 已接入 | D6 |
| Data Freshness / Overview | `state.overview` | dict | generated_at, lag_days, market_lag_days | 今日总览、数据健康 | 已接入 | D6 |
| Run Log / Operations | `state.operations` / `state.run_log` | dict | scheduler.today_status_counts, failed, successful | 数据健康 | 已接入 | D6 |
| Coverage Pools | `state.pools` | dict | watchlist, candidate, recommended | 覆盖池 | 已接入 | D6 |
| Positions | `state.positions` | dict | current positions, pnl | 覆盖池 | 已接入 | D6 |
| Market Events | `state.events` | dict | recent_market_events | 今日总览、信号流 | 已接入 | D6 |
| Foundation InputStream | N/A | 外部系统 | N/A | 全部 5 页 | 待接入 | D7 |

## 4. 数据源详细说明

### 4.1 Dashboard State Snapshot（主数据源）

- **读取方式**：`smr_dashboard.build_dashboard_state()`
- **数据类型**：Python dict
- **生成方式**：从 SQLite DB (`01_data/db/smr.db`) 读取各种 snapshot 实体，聚合成统一的 state dict
- **可用字段**：
  - `overview`：总览数据（生成时间、行情延迟等）
  - `risk`：风险监控（决策结果、告警列表）
  - `strategy_watch`：策略观察（重点关注项、优先级统计）
  - `opportunity_engine`：机会引擎（雷达、候选标的）
  - `current_state`：当前状态（证据缺口等）
  - `daily_report`：日报数据（摘要、主题）
  - `source_registry`：信息源注册表
  - `operations` / `run_log`：运行日志（调度状态）
  - `pools`：覆盖池（观察池、候选池、推荐池）
  - `positions`：持仓数据
  - `events`：市场事件
- **风险**：DB 文件可能缺失，schema 可能随 phase 变化
- **本阶段接入**：是，通过 backend_data_provider 统一封装

### 4.2 SQLite Database

- **路径**：`01_data/db/smr.db`
- **数据类型**：关系型数据库
- **可用表**：58 种 snapshot entity types
- **读取方式**：通过 `smr_dashboard.build_dashboard_state()` 间接读取
- **风险**：DB 文件可能不存在，表结构可能变化
- **本阶段接入**：间接接入（通过 build_dashboard_state）

### 4.3 Foundation InputStream

- **状态**：未接入
- **原因**：D6 阶段目标是只读接入现有后台数据，不接入 opc-foundation
- **计划接入阶段**：SMR-D7
- **预留接口**：所有 view model 的 `pending_integrations` 中均包含 `foundation_input_stream`

## 5. 数据状态定义

| 状态 | 含义 | 当前使用场景 |
|---|---|---|
| `real_snapshot` | 来自已有后台真实快照 / DB / 报告，字段相对完整 | DB 可用且字段完整时 |
| `partial_snapshot` | 来自真实后台，但字段不完整，需要 view model 做轻量补齐 | DB 可用但部分字段缺失时 |
| `lightweight_mapping` | 来自已有状态的二次轻量映射，不能视为真实业务闭环 | 默认回退、数据不完整时 |
| `empty_state` | 没有可用数据，页面展示空态 | DB 不可用且无数据时 |
| `pending_backend_integration` | 该模块设计上存在，但本阶段未接入 | Foundation 输入流 |

## 6. 风险评估

| 风险项 | 等级 | 说明 | 缓解措施 |
|---|---|---|---|
| DB 文件缺失 | 中 | smr.db 可能不存在或路径不对 | fail-soft 设计，缺 DB 返回 empty/partial 状态 |
| Schema 不稳定 | 中 | phase 推进可能导致表结构变化 | 所有字段访问使用 _safe_get，缺字段回退 |
| 数据 stale | 低 | 快照数据可能不是最新的 | 显示 updated_at 时间戳 |
| 敏感数据泄露 | 低 | DB 中可能包含敏感配置 | 只读访问，不输出 secrets/tokens |

## 7. 未接入原因说明

### 7.1 Foundation InputStream

- **未接入原因**：D6 阶段目标是只读接入现有后台数据，明确不接入 opc-foundation
- **后续计划**：D7 阶段 Foundation Evidence Inflow

### 7.2 实时写入接口

- **未接入原因**：D6 是只读后台接入，不创建任何写入接口
- **后续计划**：待后续阶段评估是否需要

## 8. 后续建议

1. **D6.1 深化**：进一步细化各模块的数据状态标记，增加更多真实数据源字段映射
2. **D7 准备**：为 Foundation 输入流预留干净接口，确保 D7 可以平滑接入
3. **Coverage Store**：考虑是否需要独立的 coverage object store
4. **Research Task Store**：考虑是否需要独立的 research task 状态存储
5. **健康检查细化**：增加更多真实健康指标的接入（如抓取成功率、延迟分布等）
