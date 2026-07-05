# SMR-D0 Dashboard 数据映射表

> **更新记录（D1 补充）**
> - 2026-05 / SMR-D1：Page 1「今日总览」已基于现有数据源完成首轮施工。
> - 实际映射见 [smr_d1_dashboard_today_overview_report.md §7 数据来源映射](./smr_d1_dashboard_today_overview_report.md#7-数据来源映射)。
> - 本文档为 D0 原始映射表，不做改写；D1 实际落地情况仅作为补充信息。
> - 其余 4 页（覆盖池 / 信号流 / 研究队列 / 数据健康）尚未施工，数据映射仍以本文档为准。

## 说明

本文档映射新 Dashboard 5 个页面的数据需求与现有数据源的对应关系，识别差距，并标注未来 opc-foundation 的接入点。

## 数据映射总表

| dashboard_page | module | data_needed | existing_source_path | existing_status | missing_gap | future_foundation_input | priority | notes |
|---|---|---|---|---|---|---|---|---|
| 今日总览 | 今日最重要变化 | 今日重大变化摘要、变化类型、关联对象 | `current_state_snapshot.p0_actions` + `daily_reporting_snapshot` | 部分可用 | 需要重新聚合"最重要变化"的逻辑，当前分散在多个模块 | EvidencePacket（新证据触发变化） | P0 | 当前有 P0 actions，但不是投研视角的"最重要变化" |
| 今日总览 | 公司重大动态 | 有重大变化的公司列表、变化摘要 | `opportunity_radar_snapshot` + `current_state_snapshot.top_opportunities` | 部分可用 | 需要按"变化程度"排序，而非按机会评分 | SourceObservation（公司级新观察） | P0 | 当前有置顶机会，但不是"今日变化"视角 |
| 今日总览 | 行业主题变化 | 行业/主题热度变化、催化剂 | `deep_market_analysis_snapshot.theme_radar` | 可用 | 变化方向和原因需要更清晰的提炼 | EvidencePacket（主题级证据） | P1 | 主题雷达已有，需要提炼"今日变化" |
| 今日总览 | 投行观点/外部观点变化 | 最新外部研报观点、评级变化 | `daily_reporting_snapshot.public_analyst_signal_digest` + `external_research_snapshots` | 可用 | 观点变化的提炼不够聚焦 | ExtractedDocument（研报提取） | P1 | 已有外部研报摘要，需要"变化"视角 |
| 今日总览 | 风险提示 | 高风险事项、风险等级 | `risk_monitor_snapshot` + `trade_risk_decision_snapshot.sell_candidates` | 可用 | 需要投研化的风险描述，而非技术风险码 | EvidencePacket（风险证据） | P0 | 已有风险监控，需要面向投研的呈现 |
| 今日总览 | 待人工判断事项 | 待审核、待确认事项列表 | `review_queue` + `investment_evidence_gap_task_snapshot` | 部分可用 | 审核队列独立，未汇总到首页 | - | P0 | 审核队列已有，需要在首页摘要展示 |
| 今日总览 | 数据健康简要 | 关键数据源新鲜度状态灯 | `data_freshness_snapshot` | 可用 | 需要提炼 3-4 个关键指标，而非全部 | SourceHealth | P1 | 数据新鲜度快照已有 |
| 覆盖池 | 公司覆盖池 | 覆盖公司列表、状态、证据完整度 | `strategy_watch_batch` + `pool_counts` + `opportunity_radar_snapshot` | 部分可用 | 缺少统一的"证据完整度"指标，分散在各模块 | EvidencePacket（按公司聚合） | P1 | watchlist 数据在多个模块，需要聚合 |
| 覆盖池 | 行业主题覆盖池 | 覆盖主题列表、热度、关联公司 | `deep_market_analysis_snapshot.theme_radar` | 可用 | 主题覆盖清单需要更系统化 | EvidencePacket（按主题聚合） | P2 | 主题雷达已有，可直接用 |
| 覆盖池 | 每个对象最新状态 | 公司/主题的最新状态标记 | `current_state_snapshot.status_counts` + 各模块状态 | 部分可用 | 状态定义不统一，各模块有自己的状态码 | - | P1 | 需要统一状态定义 |
| 覆盖池 | 证据完整度 | 每个对象的证据覆盖情况 | `investment_evidence_pack_snapshot` + `strategy_evidence_snapshot` | 部分可用 | 证据完整度没有统一的评分/进度条 | EvidencePacket（证据清单） | P1 | 有证据包，但缺少"完整度"指标 |
| 覆盖池 | 最近更新时间 | 每个对象最后更新时间 | 各快照的 `created_at` 字段 | 可用 | 需要统一的"最后活动时间" | SourceObservation.timestamp | P2 | 各快照都有时间戳 |
| 覆盖池 | 研究优先级 | 研究优先级排序 | `opportunity_radar_snapshot` 评分 | 可用 | 优先级定义偏交易，需要偏研究的优先级 | - | P2 | 可复用机会雷达评分逻辑 |
| 覆盖池 | 是否需要补证据 | 证据缺口标记 | `opportunity_evidence_gap_snapshot` + `investment_evidence_gap_task_snapshot` | 可用 | 缺口分类需要更面向投研 | EvidenceGap（Foundation 侧） | P1 | 证据缺口已有，需要优化呈现 |
| 信号流 | 时间线 | 按时间倒序的证据列表 | `market_event_snapshot` + `daily_reporting_snapshot` 各 digest | 部分可用 | 缺少统一的证据时间线，分散在多个 digest | EvidencePacket（统一证据格式） | P0 | 当前没有统一的信号流时间线 |
| 信号流 | 来源类型 | 公告/研报/新闻/IR/电话会等分类 | `input_source_registry_snapshot` + 各证据模块 | 部分可用 | 来源分类不统一，各模块自己定义 | SourceObservation.source_type | P0 | 需要统一来源类型体系 |
| 信号流 | 关联公司/行业 | 证据关联的对象 | 各快照 relationships + payload 中的 ts_code | 部分可用 | 关联关系不统一，部分证据缺少关联 | EvidencePacket.entity_relations | P0 | 关联关系需要标准化 |
| 信号流 | 证据强度 | 强/中/弱标记 | `strategy_evidence_snapshot.items` 部分有 | 部分可用 | 大部分证据没有强度评分 | EvidencePacket.confidence | P1 | 证据强度需要统一算法 |
| 信号流 | 时间戳可信度 | 时间戳质量标记 | - | 缺失 | 当前没有时间戳可信度概念 | SourceObservation.timestamp_confidence | P2 | Foundation 侧已有，未来接入 |
| 信号流 | cannot_conclude 标记 | 无法得出结论的证据标记 | - | 缺失 | 当前没有此标记 | EvidencePacket.cannot_conclude | P2 | Foundation 侧已有，未来接入 |
| 信号流 | 原始来源入口 | 查看原始证据的链接 | 各快照 relationships 中的 rel_path | 可用 | 原始入口分散，需要统一展示 | SourceObservation.source_url | P0 | artifact 查看已有，可复用 |
| 信号流 | 人工审核状态 | 已审核/待审核/已驳回 | `review_queue` + `evidence_review_*` 模块 | 部分可用 | 审核状态没有关联到每条证据 | - | P1 | 审核工作流已有，需要关联展示 |
| 研究队列 | 待深挖主题 | 建议研究的主题/公司列表 | `opportunity_evidence_gap_snapshot` + `investment_evidence_gap_task_snapshot` | 部分可用 | 缺少"研究优先级"的统一排序 | RoutePlan（研究路径建议） | P1 | 证据缺口可转化为研究队列 |
| 研究队列 | 关联公司/行业 | 研究主题关联的对象 | 缺口快照中的 entity 关联 | 部分可用 | 关联关系需要更清晰 | EvidencePacket.entity_relations | P1 | 可复用现有关联 |
| 研究队列 | 为什么重要 | 研究理由摘要 | `thesis_attack_defense_snapshot` + 机会雷达理由 | 部分可用 | 研究理由需要更面向问题导向，而非机会导向 | - | P1 | 现有逻辑偏交易机会，需要调整为研究视角 |
| 研究队列 | 已有证据 | 已收集的证据清单 | `investment_evidence_pack_snapshot` | 可用 | 需要按研究主题聚合展示 | EvidencePacket（按主题聚合） | P1 | 证据包已有 |
| 研究队列 | 缺失证据 | 还缺什么证据 | `opportunity_evidence_gap_snapshot` + `investment_evidence_gap_task_snapshot` | 可用 | 缺口描述需要更投研化 | EvidenceGap（缺口描述） | P1 | 证据缺口已有 |
| 研究队列 | 下一步建议动作 | 建议的研究动作 | `investment_evidence_gap_fetch_snapshot` | 部分可用 | 动作描述偏技术，需要面向投研人员 | RoutePlan（研究路径） | P1 | 获取任务已有，需要优化呈现 |
| 研究队列 | 人工操作 | 通过/驳回/补证据/暂缓 | `smr_decision.review_recommendation` + 审核流程 | 部分可用 | 审核逻辑偏推荐审核，不是研究队列审核 | - | P0 | 可复用现有审核框架 |
| 数据健康 | 行情数据 freshness | A股/港股/美股最新交易日 + 延迟 | `overview` 中的 trade_date + lag_days | 可用 | 展示方式需要优化 | - | P0 | 已有完整数据 |
| 数据健康 | 公告/IR/PDF/新闻源状态 | 各数据源最后成功时间 + 状态 | `data_freshness_snapshot.items` + `input_source_registry_snapshot` | 部分可用 | 数据新鲜度有，但数据源清单不完整 | SourceHealth | P0 | 数据新鲜度已有，需要补充源清单 |
| 数据健康 | Evidence pipeline 状态 | 证据处理 pipeline 各阶段状态 | `data_freshness_snapshot` + 运行日志 | 部分可用 | pipeline 状态没有统一聚合 | - | P1 | 需要从运行日志聚合 |
| 数据健康 | Foundation 输入流状态 | Foundation 连接、同步状态 | - | 缺失（占位） | 当前未接入 | SourceHealth + 同步状态 | P2 | 未来接入，当前占位 |
| 数据健康 | 最近一次成功运行时间 | 各 pipeline 最后成功时间 | `data_freshness_snapshot` + `scheduler_run_summary` | 可用 | 需要统一展示 | - | P1 | 各模块都有时间戳 |
| 数据健康 | Blocking issue | 阻塞问题列表 | `data_freshness_snapshot` problem 项 | 部分可用 | 问题分级不清晰 | - | P0 | 数据新鲜度中有 problem_count |
| 数据健康 | Degraded issue | 降级问题列表 | `data_freshness_snapshot` 次级问题 | 部分可用 | 缺少明确的分级标准 | - | P1 | 需要定义分级标准 |

## 按页面汇总

### Page 1：今日总览（数据可用性：60%）

**已有数据**：
- 风险提示（risk_monitor + trade_risk_decision）
- 市场概览（overview）
- 外部研报摘要（daily_reporting）
- 数据新鲜度（data_freshness）

**需要补充/改造**：
- "今日最重要变化"的聚合逻辑（当前分散）
- 公司重大动态的"变化量"计算
- 行业主题变化摘要
- 待人工判断事项汇总

**Foundation 接入点**：
- 新 EvidencePacket 可触发"今日变化"
- SourceObservation 提供原始证据时间线

### Page 2：覆盖池（数据可用性：65%）

**已有数据**：
- 公司 watchlist（strategy_watch_batch + opportunity_radar）
- 主题雷达（deep_market_analysis）
- 证据缺口（evidence_gap）
- 各对象状态（分散在各模块）

**需要补充/改造**：
- 统一的公司/主题覆盖清单
- 证据完整度评分
- 统一的状态定义
- 最后活动时间聚合

**Foundation 接入点**：
- EvidencePacket 按公司/主题聚合后更新证据完整度
- SourceHealth 更新数据源状态

### Page 3：信号流（数据可用性：40%）

**已有数据**：
- 各类证据 digest（研报、公告、新闻等）
- 市场事件（market_event_snapshot）
- 原始来源查看（artifact 路由）

**需要补充/改造**：
- 统一的证据时间线（最大缺口）
- 统一的来源类型分类
- 统一的关联关系
- 证据强度评分
- 人工审核状态关联

**Foundation 接入点**：
- EvidencePacket 是统一证据格式的最佳载体
- SourceObservation 提供原始观察
- ExtractedDocument 提供提取后的文档

### Page 4：研究队列（数据可用性：50%）

**已有数据**：
- 证据缺口（evidence_gap snapshots）
- 证据包（investment_evidence_pack）
- 审核工作流（review_recommendation）
- 攻防推演（attack_defense）

**需要补充/改造**：
- "研究主题"的概念（当前是证据缺口视角）
- 研究优先级排序（偏研究而非偏交易）
- 研究理由的问题导向描述
- 研究队列的人工操作（通过/驳回/补证据/暂缓）

**Foundation 接入点**：
- RoutePlan 提供研究路径建议
- EvidenceGap 提供结构化缺口
- EvidencePacket 提供已有证据

### Page 5：数据健康（数据可用性：70%）

**已有数据**：
- 数据新鲜度（data_freshness_snapshot）
- 行情延迟（overview.lag_days）
- 调度器运行状态（scheduler）
- 输入源注册（input_source_registry）

**需要补充/改造**：
- 投研化的健康状态摘要（不是工程日志）
- Blocking / Degraded 分级
- 各数据源状态的统一展示
- Foundation 占位（未来接入）

**Foundation 接入点**：
- SourceHealth 提供 Foundation 侧源健康
- 同步状态监控

## 关键数据缺口总结

### P0 缺口（必须解决）
1. **统一证据时间线** - 信号流页面的核心，当前完全没有统一的时间线
2. "今日最重要变化"聚合逻辑 - 首页的核心，当前分散在多个模块
3. **研究队列工作流** - 研究队列页面的核心操作

### P1 缺口（应该解决）
1. 证据完整度评分 - 覆盖池的核心指标
2. 统一的状态定义 - 各模块状态码不统一
3. 来源类型统一分类 - 信号流的基础
4. 证据强度统一算法 - 信号流的重要维度
5. 投研化的健康状态摘要 - 数据健康的核心呈现

### P2 缺口（可以后补）
1. 时间戳可信度 - Foundation 已有，当前不需要
2. cannot_conclude 标记 - Foundation 已有，当前不需要
3. 主题覆盖系统化 - 主题雷达可先用着
4. Foundation 输入流状态 - 未接入，占位即可

## 现有可直接复用的模块

| 模块 | 复用方式 | 所在文件 |
|---|---|---|
| SQLite 快照架构 | 数据层完全复用 | `smr_dashboard.py` |
| `build_dashboard_state` | 数据聚合逻辑复用，增加新的聚合函数 | `smr_dashboard.py` |
| artifact 查看路由 | 原始证据查看直接复用 | `run_control_tower.py` |
| 审核工作流框架 | 研究队列审核可复用此框架 | `smr_decision.py` |
| 数据新鲜度检查 | 数据健康页直接复用 | `data_freshness_snapshot` |
| 个股详情页 | 覆盖池 → 公司详情直接复用 | `render_research_detail_page` |
| 动作详情页 | 研究队列 → 动作详情可参考 | `render_action_detail_page` |

## 数据流向图（当前）

```
各数据 Pipeline
    ↓
SQLite (task_registry_entity_latest)  ← 58 种快照
    ↓
smr_dashboard.build_dashboard_state()  ← 聚合为 state dict
    ↓
run_control_tower.py  ← 渲染 HTML
    ↓
浏览器展示
```

## 数据流向图（未来 + Foundation）

```
opc-foundation
    ↓ (EvidencePacket / SourceObservation / RoutePlan / SourceHealth)
th_capital_stock 接收层（未来新增）
    ↓
SQLite (新增 Foundation 相关表 / 复用现有快照表)
    ↓
smr_dashboard.build_dashboard_state()  ← 增强：包含 Foundation 数据
    ↓
新 Dashboard 5 页面
    ↓
浏览器展示
```
