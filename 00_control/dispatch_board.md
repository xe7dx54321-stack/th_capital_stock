# SMR 调度面板

**更新日期**：2026-04-14 00:12:35 CST
**当前阶段**：`动态股票池 + 动态趋势研究 + 推荐池运行`  
**下次更新**：2026-04-15 22:00 CST

---

## 昨日完成状态（2026-04-10）

| 模块 | 状态 | 关键事件 |
|------|------|----------|
| 日报 | ✅ | 晚间版已生成，system_status=0（空仓） |
| 风控 | ✅ | 无预警，集中度/回撤/暴露均安全 |
| 股票池 | ✅ | 新增出池4只（国盾量子/金山办公/商汤/科大讯飞），英维克+6.40%进入观察 |
| 研究层 | ✅ | 5张深度卡完成（光迅/中际旭创/天孚/新易盛/光库），光库降回watchlist |
| 推荐池 | ✅ | 光迅+中际旭创 recommended；新易盛+天孚维持 candidate |

---

## 今日（2026-04-10）收盘关键信号摘要

### 美股隔夜（04-09 → 传到04-10 A/H）

| 方向 | 信号 | 关键标的 |
|------|------|----------|
| 🟢 **强势** | INTC +4.7%、MU +3.6%、MRVL +4.8% | semiconductor_compute |
| 🟢 **超强势** | COHR +10.5%、LITE +9.8% | semiconductor_photonics |
| 🔴 **重挫** | NOW -7.9%（AI Agent） | ai_agent 负向拖累 |
| 🔴 **回撤** | IONQ -3.1%、QBTS -4.8% | quantum 短线走弱 |

### A/H 当日（04-10）

| 标的 | 涨跌幅 | 趋势分 | 结论 |
|------|--------|--------|------|
| 300502.SZ 新易盛 | **+6.63%** | 3 | 进入趋势最强梯队 |
| 300308.SZ 中际旭创 | **+6.01%** | 3 | 推荐标的，领涨 |
| 300394.SZ 天孚通信 | **+3.46%** | 3 | 候选标的，补涨 |
| 300620.SZ 光库科技 | +0.77% | 3 | 已降回watchlist |
| 002281.SZ 光迅科技 | -0.25% | 3 | 推荐标的，小幅回落 |
| 688256.SH 寒武纪 | +1.06% | 2 | 算力链，跟随INTC/MU |
| 688521.SH 芯原股份 | +4.10% | 2 | 算力链，跟随较强 |

---

## 股票池当前状态

### Recommended（推荐池）

| ts_code | name | sector | 质量评分 | 距升级缺口 |
|---------|------|--------|---------|-----------|
| 002281.SZ | 光迅科技 | semiconductor_photonics | 9.00 | 已达建池标准 |
| 300308.SZ | 中际旭创 | semiconductor_photonics | 9.60 | 已达建池标准 |

### Candidate（候选池）

| ts_code | name | sector | 质量评分 | 待补证据 |
|---------|------|--------|---------|---------|
| 300502.SZ | 新易盛 | semiconductor_photonics | 9.66 | 客户结构 + 订单穿透 |
| 300394.SZ | 天孚通信 | semiconductor_photonics | 9.35 | 订单 + 客户扩散证据 |

### Watchlist（动态观察）

| ts_code | name | sector | 当日表现 | 触发点 |
|---------|------|--------|---------|--------|
| 300620.SZ | 光库科技 | semiconductor_photonics | +0.77% | 降级，需重新积累 |
| 688256.SH | 寒武纪 | semiconductor_compute | +1.06% | trend_strength=2，待触发研究 |
| 688521.SH | 芯原股份 | semiconductor_compute | +4.10% | trend_strength=2，跟随INTC/MU |
| 688041.SH | 海光信息 | semiconductor_compute | +2.12% | trend_strength待确认 |
| 688008.SH | 澜起科技 | semiconductor_compute | +3.13% | trend_strength待确认 |
| 002837.SZ | 英维克 | semiconductor_photonics | +6.40% | 新晋观察，trend_strength=1 |

---

## 研究触发检查

| 触发条件 | 状态 | 备注 |
|---------|------|------|
| thesis证伪 | 🟡 无 | 推荐标的逻辑未被证伪 |
| 美股重大信号 | ✅ 有 | COHR/LITE/MRVL 持续强势，光通信链支撑强 |
| VCR变化 | 🟢 有 | VCR具身智能策略卡在案，可对接 |
| 用户指定 | — | 无新增 |
| **算力链研究缺口** | ⚠️ 待处理 | 688256.SH、688521.SH 趋势强度2，无研究卡 |
| **光库科技降级** | ⚠️ 待归档 | 已降回watchlist，需写drop研究卡 |

---

## 美股财报日历（近期重点）

> 基于 SMR 覆盖 universe，当前无直接财报发布预警  
> 重点关注：**NVDA、AMD、INTC、MU、AVGO、COHR、LITE、MRVL** 等核心标的财报窗口

- 当前美股信号以 **价格动量** 为主，非财报驱动
- 若未来有财报发布，需在 `us_signal_harvester` 中增加财报事件标签
- **建议**：次周起关注 INTC/MU/AMD 的分析师预期调整（可触发研究更新）

---

## 明日（2026-04-11）优先级

### P0 — 核心主线跟踪

1. **光通信链持续性验证**（最高优先）
   - 今日新易盛+6.63%、中际旭创+6.01%，需观察是否出现短线筹码兑现
   - 美股 COHR/LITE 隔夜走势将直接影响次日 A 股开盘
   - 若无美股负面，002281.SZ/300308.SZ 维持趋势分3，观察缩量横盘

2. **AI Agent 链传导评估**
   - NOW -7.9% 是强负向信号
   - 需确认 688111.SH 明日是否补跌
   - 若 688111.SH/603039.SH 低开但缩量，可能是情绪的一次性释放

### P0 — 研究闭环

3. **补 688256.SH（寒武纪）研究卡**
   - trend_strength=2，但跟随 INTC/MU 强势
   - 需确认：1.6T/算力芯片格局、订单可见性
   - 这是"算力链"进入推荐池的关键候选

4. **光库科技（300620.SZ）降级归档**
   - 完成 drop 研究卡，记录降级原因（强度不足以支撑 candidate）
   - 保持 watchlist 观察

### P1 — 算力链补涨研究

5. **688521.SH（芯原股份）+ 688041.SH（海光信息）+ 688008.SH（澜起科技）**
   - INTC +4.7%、MU +3.6% 已有支撑
   - 趋势分待确认（可能 trend_strength 会上调）
   - 建议先跑趋势快照确认分值，再决定是否进入研究队列

### P1 — 系统增强

6. **北交所数据源决策**
   - 872808.BJ（曙光数创）免费源无历史数据
   - 需确认：是否接入 tushare（需token）、或放弃北交所标的

7. **财报事件监控增强**
   - 当前 us_signal_harvester 无财报标签
   - 建议次周接入简单财报日期表（可从公开日历获取）

### P2 — VCR 协同

8. **具身智能 VCR 策略卡对接**
   - VCR 有具身智能专项策略，可作为 SMR 具身链的 thesis 支撑
   - 中大力德（002796.SZ）趋势分3，需等美股 Figure/Tesla 机器人链确认

---

## 风控状态

| 指标 | 值 | 状态 |
|------|----|------|
| 持仓数量 | 0 | 空仓 |
| 总暴露 | 0% | 安全 |
| 单票暴露 | N/A | — |
| 组合回撤 | 0% | 安全 |
| 单周亏损 | 0% | 安全 |
| 预警 | 0 | 无 |

---

## 待办缺口跟踪

| 项目 | 状态 | 最后更新 |
|------|------|---------|
| 872808.BJ 历史行情 | ⚠️ 待决策 | 2026-04-10 |
| 688256.SH 研究卡 | 🔴 未开始 | 2026-04-10 |
| 光库科技 drop 卡 | 🔴 未开始 | 2026-04-10 |
| 算力链趋势快照 | 🟡 待确认 | 2026-04-10 |
| 财报日历标签 | 🟡 待增强 | 2026-04-10 |

---

## 自动同步候选（2026-04-13）

- source_dispatch_packet_rel_path: `12_smr_agents/workspaces/hermes_reporting_editor/dispatch_packets/2026-04-13__dispatch_packet_candidate.md`
- apply_mode: `review_only`
- 说明：这是一份自动生成的写回候选，只补充新说明，不直接覆盖旧口径。

### 日报 / 知识同步（2026-04-13）

- 对应日报：`06_reports/daily/2026-04-13_盘前简报.md`
- 日报标题：📋 SMR 盘前简报 | 2026-04-13
- 日报摘要：**撰写时间**：09:25 上海 | **数据截止**：2026-04-10 美股收盘
- 建议动作：
  - 把今日最重要的 1-3 个观察动作补进调度面板。
  - 把需要持续追踪的主题保留在时间线（timeline，时间线）或日报类知识草稿中。
  - 不直接覆盖原结论，优先用“新增说明”方式补充。

### 研究上下文同步（dynamic_pool_snapshot）

- handoff_id: `handoff_20260413232410432088`
- source_entry_id: `registry_20260413151308251470`
- snapshot_rel_path: `03_stock_pool/watchlist/2026-04-13_dynamic_watchlist.md`
- event_time: `2026-04-13 15:13:08`
- structured_decisions: `17`
- live_code_count: `31`
- watchlist_count: `19`
- candidate_count: `2`
- recommended_count: `2`
- recommended: `002281.SZ, 300308.SZ`
- candidate: `300394.SZ, 300502.SZ`
- watchlist: `002050.SZ, 002281.SZ, 002600.SZ, 002796.SZ, 002837.SZ, 300124.SZ, 300308.SZ, 300394.SZ, 300502.SZ, 300620.SZ ...`
- 处理原则：优先补充解释，不直接覆盖旧结论。
- 若该上下文会影响次日优先级，把它折叠到 P0 / P1 任务区。

### 研究上下文同步（trend_research_batch）

- handoff_id: `handoff_20260414001220671357`
- source_entry_id: `registry_20260414001220669572`
- latest_us_date: `2026-04-10`
- latest_factor_date: `2026-04-10`
- top_sector: `semiconductor_photonics`
- target_count: `5`
- target_ts_codes: `002281.SZ, 300308.SZ, 300502.SZ, 300620.SZ, 300394.SZ`
- target_sectors: `semiconductor_photonics`
- summary_rel_path: `01_data/factor/trend_analysis_2026-04-10.md`
- industry_card_rel_path: `02_research/industry/semiconductor/2026-04-10_semiconductor_photonics_trend_snapshot/00_research-card.md`
- stock_card_count: `5`
- 抽出本批次最值得持续跟踪的 1-3 个主线。
- 把行业卡和个股卡里的重复论点压缩成统一口径。
- 处理原则：优先补充解释，不直接覆盖旧结论。
- 若该上下文会影响次日优先级，把它折叠到 P0 / P1 任务区。

### 研究上下文同步（research_quality_snapshot）

- handoff_id: `handoff_20260413232601172368`
- source_entry_id: `registry_20260413232601171027`
- output_rel_path: `02_research/summary/2026-04-13_research_quality_snapshot.md`
- row_count: `4`
- counts_by_pool: `{'candidate': 2, 'recommended': 2}`
- ts_codes: `300308.SZ, 002281.SZ, 300502.SZ, 300394.SZ`
- 优先标记研究空缺最多、但池子级别最高的标的。
- 如果同一批标的长期重复缺口，把问题沉淀成 playbook 或 review checklist。
- 不直接改研究卡原文，先给出治理和补强建议。
- 处理原则：优先补充解释，不直接覆盖旧结论。
- 若该上下文会影响次日优先级，把它折叠到 P0 / P1 任务区。

### 风险上下文同步（risk_monitor_snapshot）

- handoff_id: `handoff_20260413232430246123`
- source_entry_id: `registry_20260413162848795992`
- alert_count: `0`
- counts_by_severity: `{}`
- counts_by_type: `{}`
- alert_file_rel_path: ``
- 当前无新增预警，不追加风险动作。
- 保留这条候选仅用于说明“今天风险面清空”。
- 后续只有在重新出现真实预警时再升级为治理动作。
- 处理原则：风险说明优先补到调度板，不直接替代交易动作。
- 若当前是 clear 快照，只保留占位说明，不把它升级成伪风险任务。

## 备注

明日无盘前（09:00前）交易操作计划。当前空仓，等待趋势确认后的建仓信号。  
美股无重大风险事件（A/H 主线光通信链支撑仍然清晰）。

---

*📝 SMR 调度面板 | 同行资本二级市场研究 | 2026-04-14 00:12:35 CST*
