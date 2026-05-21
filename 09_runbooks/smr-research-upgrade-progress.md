# SMR 深度投研系统升级进度表

- created_at: 2026-05-20 00:01:34
- owner: Codex / SMR engineering
- goal: 把系统从“资料聚合 + 状态展示”升级为“预期差研究 + 投行式报告 + 可复盘决策支持”。

## 总体原则

- 脚本只负责确定性工作：抓取、清洗、去重、切块、索引、证据包、引用定位、入库。
- 高智力 agent 负责研究判断：读材料、拆观点、找共识、找分歧、判断预期差、写反方、给证伪条件。
- 报告主笔 agent 负责成稿：把碎片化卡片组织成完整的投行式深度报告。
- 前台只展示最终结论、关键操作和可点击深度报告，不展示后台状态噪音。

## 施工进度

| 模块 | 目标 | 状态 | 产物 | 验收方式 | 备注 |
|---|---|---:|---|---|---|
| 升级进度表 | 维护施工总控，避免遗漏 | 进行中 | `09_runbooks/smr-research-upgrade-progress.md` | 每个阶段更新状态和验证记录 | 当前文件 |
| 研究综合 skill | 沉淀“共识/分歧/预期差”方法论 | 已完成 | `09_runbooks/skills/smr-research-synthesis/` | `quick_validate.py` 通过 | 需继续迭代细节 |
| 投行报告写作 skill | 沉淀深度报告主笔规范 | 已完成 | `09_runbooks/skills/smr-investment-report-writing/` | `quick_validate.py` 通过 | 已补完整报告 spine 和模板 |
| 硬证据验证 skill | 把 capex、订单、毛利率、竞争格局等变量沉淀成研究方法论 | 已完成 | `09_runbooks/skills/smr-hard-evidence-validation/` | `quick_validate.py` 通过 | 已接入投研分析和报告主笔 prompt |
| 投资分析 agent | 高智力模型负责研究判断 | 已完成 | `12_smr_agents/profiles/hermes_investment_analyst.json` / `12_smr_agents/prompt_packs/hermes_investment_analyst.md` | profile JSON valid；handoff 可路由；样板真实 shadow 成功 | 仍需继续收紧“不得写无来源判断” |
| 投资报告主笔 agent | 汇总碎片卡片并写深度报告 | 已完成 | `12_smr_agents/profiles/hermes_investment_report_writer.json` / `12_smr_agents/prompt_packs/hermes_investment_report_writer.md` | profile JSON valid；报告质量门槛生效；样板真实 shadow 成功 | 已修复 `$LOAD` 输出和 token 截断问题 |
| Evidence Pack Builder | 为 agent 准备可溯源材料包 | 已完成 | `08_scripts/research/build_investment_evidence_pack.py` | 可为动作生成 markdown/json 包并注册 snapshot | 已接入 handoff |
| Research Synthesis Snapshot | 沉淀研究判断结构化结果 | 已完成 | `investment_research_synthesis_snapshot` | schema 稳定；agent handoff 生成提示包 | 候选层，需人工审核后进入真相层 |
| Investment Report Snapshot | 沉淀完整深度报告 | 已完成 | `investment_report_snapshot` | report writer handoff 生成报告草稿 | 候选层，需人工审核后进入真相层 |
| Agent 控制链 | 让新 entity_type 进入 handoff 流水线 | 已完成 | `run_agent_control_loop.py` / `process_investment_model_handoff.py` | dry-run/真实 handoff 可处理 | 已加模型输出质量门槛 |
| 调度链 | 让收盘/刷新链生成 evidence pack、补证任务、补证执行和回灌 | 已完成 | `run_smr_schedule_job.py` | `afternoon_close` / `afternoon_refresh` 会生成 evidence pack、解析报告、生成硬证据补证任务、执行外部资料抓取并重建 evidence pack | 后续可扩展到更多 job |
| 前台报告接入 | 动作页读取深度报告，而不是临时拼状态 | 已完成 | `dashboard action page` | 页面显示完整报告、研究综合、证据包入口、待补硬证据入口 | 仍保留三段快速摘要 |
| 硬证据补证任务 | 把报告审计缺口转成可执行研究任务 | 已完成 | `investment_evidence_gap_task_snapshot` / `02_research/investment_evidence_gap_tasks/` | 样板生成 P0 云厂商 capex 任务并在动作页展示 | 当前先从报告 summary 与来源纪律审计生成 |
| 硬证据补证执行器 | 将补证任务转成真实资料抓取、source manifest 和 market_event 回灌 | 已完成 | `08_scripts/research/run_investment_evidence_gap_fetch.py` / `investment_evidence_gap_fetch_snapshot` | 样板抓取 14 个云厂商官方/电话会来源，失败数 0，并回写 evidence pack | 脚本只沉淀原材料，后续必须交给投研 agent 二次研读 |
| Data Freshness Monitor | 统一判断 daily_bar/news/filings/fundamentals/consensus_revision 新鲜度 | 已完成 | `08_scripts/lib/smr_data_health.py` / `data_source_health` | 真实库生成 7 条 data_source_health；A/H/US daily_bar stale 均为 block | 当前真实状态为 BLOCKED |
| Freshness Gate | 在机会雷达、资金异动、paper watch、风控、报告生成前阻断 stale 数据 | 已完成 | `check_freshness_gate` 已接入关键 pipeline | A/H/US daily_bar stale 时，雷达/资金异动/paper watch 均产出 `blocked_by_data` | deep_market_scan 允许降级静态研究 |
| Source Registry Enforcement | planned/disabled/deprecated 来源不得作为有效 evidence | 已完成 | `08_scripts/lib/smr_source_registry.py`；evidence pack source index 过滤不可用来源 | `consensus_revision` / premium research / Seeking Alpha 等只进入 missing/planned 展示 | unknown/internal 来源暂按可用但保留 registry 元数据 |
| Evidence Checker | 核心 claim 与交易建议证据门槛 | 已完成 | `08_scripts/lib/smr_research_quality.py` | 单元测试覆盖无反方观点买入必须 block | 第一版为 deterministic 规则，后续可接高智力质量 agent |
| Report Quality Linter | 拦截占位符、无证据强结论、stale 数据交易建议、禁用一致预期结论 | 已完成 | `lint_report` / report metadata | 单元测试覆盖 TBD、consensus_revision disabled、stale action | 已接入投资报告解析 |
| Recommendation State Machine | draft/candidate/blocked/pending/approved/rejected 状态收口 | 已完成 | `08_scripts/lib/smr_decision.py` | 最新 3 份报告因 stale 数据进入 `blocked_by_data` | 正式 approve 仍需人工 review action |
| Human Review Service | 候选建议提交、批准、拒绝、降级、减仓覆盖 | 已完成 | `recommendation_reviews` / `review_recommendation` | 单元测试覆盖 pending -> approved、submit review 留痕 | 前端审核入口后续再补 |
| Decision Ledger | 每个 recommendation 状态进入可复盘日志 | 已完成 | `decision_ledger` | 真实库写入 3 条 `blocked_by_data` ledger，含 data/evidence/lint 快照 | 后续补 outcome 归因 |
| Agent Run Audit Trail | agent/pipeline 每次运行留 data health、gate、lint、block reason | 已完成 | `agent_runs` | 真实库已有 11 条 agent_runs | 已接入 shadow、雷达、报告、风控、健康报告 |
| Daily System Health Report | 每日可信度总报告 | 已完成 | `08_scripts/reporting/build_daily_system_health_report.py` / `daily_system_health_report` | 真实报告显示 overall_status=`BLOCKED`，列出阻断项和影响模块 | 已接入调度链 |

## 当前样板对象

| 样板 | 用途 | 当前状态 |
|---|---|---|
| `ready__300308.SZ__09988.HK` | 中际旭创 vs 阿里巴巴-W，验证深度研究和调仓报告链路 | 已跑通 evidence pack -> synthesis -> report -> 前台入口 |
| `ready__002281.SZ__301171.SZ` | 光迅科技 vs 易点天下，验证研报样本不足时的降级表达 | 已暴露素材型假设问题 |

## 验证记录

| 时间 | 验证项 | 结果 |
|---|---|---|
| 2026-05-20 00:01:34 | 初始化升级进度表 | 进行中 |
| 2026-05-20 00:01:34 | `smr-investment-report-writing` skill 校验 | 通过 |
| 2026-05-20 00:17:32 | `ready__300308.SZ__09988.HK` evidence pack | 通过，生成 `02_research/investment_evidence_packs/2026-05-19/ready__300308.SZ__09988.HK.md` |
| 2026-05-20 00:19:42 | 投资分析 agent 真实 shadow | 通过，生成 `investment_research_synthesis_snapshot` |
| 2026-05-20 00:25:42 | 投资报告主笔 agent 真实 shadow | 通过，生成 `investment_report_snapshot` |
| 2026-05-20 00:26:00 | 报告主笔质量门槛 | 通过，报告包含执行摘要、调仓、逻辑、技术、风险证伪和 dashboard JSON |
| 2026-05-20 00:29:00 | 动作页前台入口 | 通过，`/portfolio/action?id=ready__300308.SZ__09988.HK` 显示完整报告、研究综合和证据包入口 |
| 2026-05-20 08:08:22 | 结构化 dashboard summary 回填 | 通过，解析出操作计划、3 个 kill trigger、5 个 follow-up task |
| 2026-05-20 08:09:39 | 来源纪律审计 | 通过，识别出云厂商 capex 相关判断缺直接证据锚点 |
| 2026-05-20 08:10:00 | 动作页结构化展示 | 通过，页面展示结构化操作计划、证伪触发器、跟踪任务和来源纪律提示 |
| 2026-05-20 08:33:12 | `smr-hard-evidence-validation` skill 校验 | 通过 |
| 2026-05-20 08:33:20 | `ready__300308.SZ__09988.HK` 硬证据补证任务 | 通过，生成 P0 云厂商 capex 任务包 `02_research/investment_evidence_gap_tasks/2026-05-19/ready__300308.SZ__09988.HK.md` |
| 2026-05-20 08:35:00 | 动作页待补硬证据展示 | 通过，页面显示 `待补硬证据`、P0 变量、验收标准和补证任务包入口 |
| 2026-05-20 08:59:14 | `ready__300308.SZ__09988.HK` 硬证据补证执行 | 通过，严格抓取 Microsoft/Alphabet/Amazon/Meta 官方 SEC 材料和公开电话会文字稿，共 14 个来源，失败数 0 |
| 2026-05-20 08:59:19 | 硬证据回灌 evidence pack | 通过，`02_research/investment_evidence_packs/2026-05-19/ready__300308.SZ__09988.HK.md` 已包含 `Hard Evidence Supplement` |
| 2026-05-20 09:09:39 | 补证后投研 agent 二次研读 | 通过，MiniMax-M2.7 shadow 成功生成新 `investment_research_synthesis_snapshot`：`registry_20260520090939297666` |
| 2026-05-20 09:12:30 | 补证后报告主笔 shadow | 通过，模型成功生成新版深度调仓报告，核心结论从“可推进”修正为“推迟建仓，等待回踩 MA20” |
| 2026-05-20 09:15:47 | 新版报告入库与前台展示 | 通过，`investment_report_snapshot`=`registry_20260520091547317703`；dashboard summary 质量通过，来源纪律审计通过，动作页读取新版报告和 14 条补证来源 |
| 2026-05-20 09:15:47 | 长上下文模型调用稳定性 | 通过，将投研/报告类 shadow 默认读取超时提高到 900 秒，并支持 `SMR_MODEL_SHADOW_TIMEOUT_SECONDS` 覆盖 |
| 2026-05-20 09:19:51 | 补证执行器 plan/executed 文件隔离 | 通过，计划模式写入 `__planned.md`，不会覆盖真实执行 summary；空补证任务会跳过，最新执行 summary 恢复为 14 个来源 |
| 2026-05-20 15:42:29 | 硬证据变量摘录层 | 通过，evidence pack 新增 `Hard Evidence Variable Digest`，按云厂商 capex、订单/需求、毛利率/效率、竞争格局、阿里 AI 进展抽取可回溯摘录 |
| 2026-05-20 15:53:20 | 合规边界 prompt 修复后二次投研 shadow | 通过，MiniMax-M2.7 成功生成新版 `investment_research_synthesis_snapshot`：`registry_20260520155320768067` |
| 2026-05-20 15:56:42 | 报告主笔 shadow 二次成稿 | 通过，生成新版投行式深度报告：`registry_20260520155642675246`，包含执行摘要、调仓操作、逻辑分析、技术分析、风险证伪和硬证据审计 |
| 2026-05-20 15:58:22 | dashboard summary 归一化修复 | 通过，自动补齐 `action_detail`，最新报告快照 `registry_20260520155822205332` 的 `dashboard_summary_quality.valid=true`、来源纪律审计通过 |
| 2026-05-20 16:02:57 | 动作页归档报告回退 | 通过，即使当前最新动作列表已切换，`/portfolio/action?id=ready__300308.SZ__09988.HK` 仍可通过投资报告快照重建入口并返回 200 |
| 2026-05-20 16:19:33 | 动作页报告正文驱动改造 | 通过，动作详情页 h2 收敛为 `完整调仓报告 / 调仓操作 / 逻辑分析 / 技术分析`，旧链路“证据等级/已接入结构化卖方研报”等话术不再出现 |
| 2026-05-20 21:51:14 | 变量证据卡 evidence pack | 通过，`ready__300308.SZ__09988.HK` 新包 source_paths=97，中际旭创 source_index=28，阿里 source_index=40，Hard Evidence Variable Digest 含 5 张变量证据卡和 50 个 clips |
| 2026-05-20 21:54:28 | 变量证据卡驱动投研 shadow | 通过，MiniMax-M2.7 成功生成新版 `investment_research_synthesis_snapshot`：`registry_20260520215428409862` |
| 2026-05-20 21:57:27 | 变量证据卡驱动报告主笔 shadow | 通过，生成新版报告 `registry_20260520215727761470`；正文不再出现“证据等级/接入了”等后台状态话术，并输出 6 个证据缺口任务 |
| 2026-05-20 22:01:46 | dashboard summary 解析与前台回归 | 通过，最新解析快照 `registry_20260520220146405411`，`dashboard_summary_quality.valid=true`；动作页顶部改为候选动作/金额口径/执行口径/复核重点，Browser 验证旧状态 chip 不再出现 |
| 2026-05-20 22:27:29 | 证据缺口变量映射补证执行 | 通过，`run_investment_evidence_gap_fetch.py --execute --local-only` 将 6 个缺口扩展为 52 条本地来源映射，覆盖订单/交付、阿里复核、毛利率、竞争格局、1.6T、Google capex |
| 2026-05-20 22:29:02 | 补证来源回灌 evidence pack | 通过，新包 `registry_20260520222902997903` 接入 `Hard Evidence Supplement`，source_paths 增至 103 条，并刷新 analyst handoff |
| 2026-05-20 22:32:40 | 补证映射后投研 shadow | 通过，MiniMax-M2.7 成功生成 `investment_research_synthesis_snapshot`：`registry_20260520223240340875` |
| 2026-05-20 22:40:47 | 新版报告解析与结构化质量门槛 | 通过，报告 `registry_20260520224024479098` 解析为 `registry_20260520224047960103`，`dashboard_summary_quality.valid=true`，含 7 个 kill trigger、10 个 evidence gap task、7 个 follow-up task |
| 2026-05-20 22:48:10 | 动作页产品化回归 | 通过，Browser 验证 action 页仅保留 `完整调仓报告 / 调仓操作 / 逻辑分析 / 技术分析`；不再出现“证据等级/接入几篇/材料状态”、英文 plan key 或 `-/-` 触发器占位 |
| 2026-05-20 22:49:38 | report-writer prompt 收紧后最终成稿 | 通过，报告 `registry_20260520224927767808` 解析为 `registry_20260520224938789764`，`dashboard_summary_json` 只出现 1 次，正文使用 `关键变量判断与证伪清单`，无“证据等级/接入几篇/材料状态” |
| 2026-05-20 22:52:10 | 动作页操作计划 key 归一化 | 通过，Browser 验证 `reduce_position/stop_loss` 等模型 key 已显示为 `减仓条件/止损条件`，触发器表无空占位 |
| 2026-05-21 08:53:23 | 可信投研自动化底座真实库验收 | 通过，`data_source_health` 生成 7 行；`daily_system_health_report` 显示 `BLOCKED`，A/H/US daily_bar stale 均为 block，consensus_revision 为 planned/disabled 缺口 |
| 2026-05-21 08:53:07 | 报告质量门禁与状态机 | 通过，最新 3 份 investment report 解析后均因 stale daily_bar 进入 `blocked_by_data`，并写入 `decision_ledger` |
| 2026-05-21 08:53:12 | 机会雷达/资金异动/paper watch Freshness Gate | 通过，`opportunity_radar_snapshot`、`market_flow_anomaly_snapshot`、`paper_trade_watchlist_snapshot` 均产出 `blocked_by_data`，不再生成旧行情候选 |
| 2026-05-21 08:53:13 | 风控 stale 数据告警 | 通过，Risk Agent 生成 `data_stale` 告警，明确价格型止损/目标/回撤判断只能作为静态告警 |
| 2026-05-21 08:53:49 | Evidence Pack Source Registry Enforcement | 通过，`build_investment_evidence_pack.py --dry-run` 成功，source index 过滤 planned/disabled/deprecated 来源并保留 registry 状态 |
| 2026-05-21 08:54:00 | 第一阶段单元测试 | 通过，`python3 -m unittest tests/test_trusted_research_foundation.py` 共 8 个用例全部通过 |

## 下一轮重点

| 优先级 | 事项 | 原因 |
|---:|---|---|
| P0 | 修复 A/H/US daily_bar、news、filings 新鲜度 | 第一阶段门禁已生效，当前真实系统处于 BLOCKED；不修数据就不能生成交易候选 |
| P0 | 为 human review 增加前台审核入口 | service 层和 ledger 已完成，下一步需要在报告/动作页让用户能 approve/reject/request_more_research |
| P0 | 接入或设计 consensus_revision 替代层 | 当前只能明确披露缺口，不能判断一致预期是否修正；这是预期差系统的核心输入 |
| P1 | 把 Evidence Checker 从报告级粗校验升级到 claim/evidence_id 级校验 | 第一版 deterministic lint 已能阻断明显风险，下一轮要让报告 JSON 明确输出 claims/evidence_ids |
| P1 | 继续补 Valuation/Industry Chain/Bear Case Agent | 可信底座已经有，后续复杂 agent 可以建立在 gate、lint、ledger 之上 |
# 2026-05-21 Status Calibration

Second-stage v1 has moved the system out of the earlier hard `BLOCKED` state and into a controlled `DEGRADED` state:

- According to the Phase 2 validation feedback, A/H/US `daily_bar` freshness has been restored in the target runtime; a fresh local clone may still start with an empty ignored SQLite DB.
- Block-level data issues are expected to be zero after the daily-bar repair path completes.
- Claim graph, consensus proxy, valuation snapshot, bear case, human review service, decision ledger, and outcome updater are present.
- Current remaining degradation drivers are `news` freshness, `filings` freshness, and lack of official consensus revision.
- Consensus proxy remains an internal proxy only and must not be represented as official sell-side consensus.

Third-stage target: move selected high-quality recommendations from `observation_only` to `pending_human_review` by repairing news/filings freshness, strengthening proxy/valuation/bear-case inputs, adding explicit promotion rules, and generating structured recommendation candidates.

Phase 3 acceptance focus:

- News freshness is source/market-level instead of a vague global stale flag.
- Filings freshness is market/watchlist/ticker-level and filing chunks can become primary evidence.
- `observation_only -> candidate_shadow -> pending_human_review` is controlled by `smr_recommendation_promotion.py`.
- Recommendation action and position sizing are generated by `smr_recommendation_candidate.py`, not freely by report text.
- At least one real candidate can reach `pending_human_review`; weaker candidates must explain missing requirements.

# 2026-05-21 Phase 4 Live E2E Checkpoint

Phase 3 has been committed as a stable rollback point:

- Commit: `e854421 phase3: add promotion candidate builder and controlled e2e`
- Controlled Phase 3 E2E still passes.
- Controlled outcomes remain: `NVDA -> pending_human_review`, `09988.HK -> observation_only`, `000001.SZ -> candidate_shadow`.

Phase 4 implementation checkpoint:

- Added live validation scripts for news, filings, and full live E2E.
- Added ticker-level `fundamentals_snapshot` v1 and connected valuation to fundamentals.
- Added evidence quality scoring and promotion/claim-graph quality gates.
- Added paper portfolio lifecycle modules for `approved_paper -> paper order -> paper position`.
- Added compact live E2E terminal output while retaining the full audit payload in `task_registry_entry`.

Latest validation on 2026-05-21:

- `python -m py_compile` across `08_scripts/lib`, `08_scripts/jobs`, `08_scripts/verification`, `08_scripts/reporting`, `08_scripts/research`, and `08_scripts/wiki`: pass.
- `python -m unittest discover -s tests -v`: 37 tests pass.
- `python 08_scripts/verification/validate_phase3_e2e.py`: pass.
- `python 08_scripts/verification/validate_phase4_live_e2e.py --tickers NVDA,09988.HK,000001.SZ --days 180 --timeout 240`: `live_data_available_needs_promotion_work`.

Live connector results:

- `NVDA`: Yahoo Finance RSS news fresh, SEC filings fresh, fundamentals fresh, valuation `supporting_evidence`.
- `09988.HK`: Yahoo Finance RSS news fresh, HKEX/related filings fresh, fundamentals degraded, valuation `supporting_evidence`.
- `000001.SZ`: CNINFO filings fresh, but recent live news is missing; the validator now reports zero recent live news evidence instead of counting stale/loose matches.

Current live E2E status:

- No live ticker is currently promoted to `pending_human_review`.
- All three live candidates remain `observation_only`.
- This is intentional and conservative: the system now proves live ingestion and auditability, but does not manufacture a strong recommendation when promotion evidence is insufficient.

Current blockers:

- `NVDA`: blocked only by `consensus_proxy_quality`; live SEC/news evidence exists, but current fetched excerpts are mostly filing metadata, 8-K administrative content, or thematic news, not strong expectation-revision evidence.
- `09988.HK`: blocked by `consensus_proxy_quality`, high bear case, and data quality risk from incomplete fundamentals.
- `000001.SZ`: blocked by missing recent live news, weak/low-quality live evidence for core claims, missing fundamentals, invalid proxy, and high data quality risk.

Important guardrails kept intact:

- Live E2E requires evidence marked `metadata.live=true`.
- News evidence uses a shorter recency window than filings; stale A-share news is not counted as current live news.
- `consensus_revision_proxy` remains internal proxy only and is not treated as official consensus.
- `valuation_snapshot.allowed_usage=context_only` still cannot support buy/add.
- `pending_human_review` still requires promotion gates to pass; candidate builder does not bypass promotion.

Next engineering focus:

- Improve live proxy extraction using actual earnings releases, guidance text, transcript snippets, and numeric EPS/revenue changes rather than generic filing metadata.
- Improve filing chunk selection so SEC/HKEX/CNINFO evidence prioritizes business/financial sections over manifest headers and administrative 8-K content.
- Expand A/H fundamentals extraction from HKEX/CNINFO parsed tables and official financial statements.
- Add a live paper-portfolio smoke path once a true live candidate reaches `pending_human_review`; until then paper lifecycle remains unit-tested and ready but not live-triggered.
