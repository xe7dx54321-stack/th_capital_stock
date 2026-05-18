# SMR 下一阶段开发总计划

**更新日期**：2026-04-13  
**适用范围**：同行资本二级市场（SMR）当前项目目录  
**文档定位**：这是接下来正式施工的总计划文档，用来承接现有 `smr-system-patch-plan.md`，并补齐知识沉淀、治理闭环、任务状态承接层、以及类 OpenClaw / 类 Hermes 的协作机制。

---

## 1. 先说结论

SMR 当前已经不是空架子了。

它已经具备：

- 动态股票池
- 研究驱动入池/出池
- 推荐池门禁
- 组合开仓门禁
- 风控巡检
- 日报与调度板
- SQLite + Markdown + Python 脚本这套最小可运行底座

但它还缺一层很关键的东西：

- 研究、日报、风控结论、推荐变化，还没有被持续编译成“可复用知识”
- 执行结果还没有进入“草稿 -> 审核 -> 生效”的治理闭环
- 任务状态和上下游交接还不够可追踪
- 稳定执行类任务与需要判断沉淀的任务，还没有明确拆成两套协作机制

因此，下一阶段不是推翻重做，也不是先造一个“万能 agent 平台”，而是按下面顺序推进：

1. 先把现有底座收口，保证 universe、研究决策、动态池、风控、运行日志口径稳定。
2. 同时把 `OpenClaw` 和 `Hermes` 原版源码作为架构母版，不闭门造车。
3. 再把 `SMR Wiki` 搭起来，让知识开始持续沉淀。
4. 再把知识草稿、审核队列、原因码、导入流程做成治理闭环。
5. 再把任务注册与状态快照补齐。
6. 最后再把基于上游母版的类 OpenClaw / 类 Hermes 协作机制接到现有链路上。

---

## 2. 当前项目的真实基线

### 2.1 已经落地的能力

- `watchlist_registry.md` 已退回到 `seed universe` 角色，不再直接等于实时观察池。
- `stock_pool_current` 已经是当前实时池的主口径。
- `research_decision` / `research_decision_latest` 已经开始承接结构化研究结论。
- `generate_trend_batch.py` 已经能动态挑选强趋势标的并生成研究卡。
- `reconcile_dynamic_pool.py` 已经能基于研究结论 + 因子信号重建 `watchlist / candidate / recommended`。
- `entry.py` 和 `monitor.py` 已经形成基本的推荐池门禁和风险门禁。
- `script_runs.jsonl` 已经开始承接最基础的运行审计。

### 2.2 当前阶段最大的短板

1. **知识没有编译层**
   - 现在高价值内容散落在 `02_research`、`03_stock_pool`、`05_risk`、`06_reports`。
   - 这些内容能看，但复用效率低，也没有统一治理。

2. **没有知识治理闭环**
   - 研究卡写完就直接成为事实口径，缺少：
   - 草稿
   - 审核
   - 原因码
   - 拒绝 / 重开
   - 导入执行记录

3. **任务状态承接不够**
   - 现在有 `script_runs.jsonl`，但还没有统一的 registry 去承接：
   - 这次趋势研究生成了什么
   - 这次动态池重建造成了什么变化
   - 这次日报用了哪些上游对象
   - 这次风控报警后有没有被处理

4. **双 agent 分工还没有真正落地**
   - 目前更多是“脚本 + runbook + 人工/Codex”协作。
   - 还没把稳定执行任务和判断类任务拆成清晰的职责层。

### 2.3 上游参考基线已经到位

这轮新增一个重要变化：

- `OpenClaw` 官方源码已经拉到本地：
  - `/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/12_agent_references/openclaw`
- `Hermes Agent` 官方源码已经拉到本地：
  - `/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/12_agent_references/hermes-agent`

后面的双 agent 施工，不再按“纯自研平台”口径推进，而是按下面的口径推进：

1. 不直接把原版产品壳当成生产环境硬装。
2. 但必须持续参考原版项目结构、原始代码、能力分层。
3. `SMR Agent Runtime` 的角色是“业务适配层”，不是“另起炉灶的平台替代品”。

### 2.4 截至 2026-04-13 已完成的前置落地

这份总计划现在不再只是施工前蓝图，下面这些前置件已经实际落地：

- 本地参考源码已经拉下：
  - `12_agent_references/openclaw`
  - `12_agent_references/hermes-agent`
- 最小 `SMR Agent Runtime` 已建立：
  - `12_smr_agents/profiles/`
  - `12_smr_agents/handoffs/`
  - `12_smr_agents/workspaces/`
- 最小路由与交接链路已建立：
  - `route_task.py`
  - `create_handoff.py`
  - `resolve_handoff.py`
- 两条自动 handoff 已接上：
  - `daily_reporting_snapshot -> hermes_reporting_editor`
  - `review_queue -> hermes_research_curator`
- 更多上下文型 handoff 已接上：
  - `dynamic_pool_snapshot -> hermes_research_curator`
  - `trend_research_batch -> hermes_research_curator`
  - `research_quality_snapshot -> hermes_research_curator`
  - `us_signal_snapshot -> hermes_research_curator`
  - `risk_monitor_snapshot -> hermes_risk_curator`
  - `portfolio_pnl_snapshot -> hermes_risk_curator`
- 下游消费型 handoff 已接上：
  - `research_context_note -> hermes_reporting_editor`
  - `risk_update_candidate -> hermes_reporting_editor`
- 两条治理处理入口已接上：
  - `process_reporting_handoff.py`
  - `process_research_handoff.py`
- 更多上下文处理入口已接上：
  - `process_research_context_handoff.py`
  - `process_risk_handoff.py`
- reporting 消费与汇总入口已接上：
  - `process_reporting_sync_handoff.py`
  - `build_dispatch_packet_candidate.py`
  - `build_dispatch_board_patch_candidate.py`
  - `apply_dispatch_board_patch_candidate.py`

现在下一阶段的重点，不再是“要不要做双 agent”，而是继续把它往更完整的业务对象上扩：

- 把数据采集 / 因子 / 风控 / 日报更多实体接入 registry 和 router
- 把候选产物继续和正式真相层隔离
- 把高判断对象继续压在 review / import 治理闭环里
- 逐步把本地 runtime 做成稳定的 SMR 业务适配层
- 新增的 `业务驱动系统自进化链` 已经开始落地：
  - `build_system_change_request_snapshot.py`
  - `process_system_handoff.py`
  - 当前能把业务缺口编译成系统施工候选
  - 但仍然卡在“候选层 + 人工审核”边界内

---

## 3. 下一阶段目标架构

下一阶段不改变 SMR 的基础方向，仍然坚持：

- 本地优先
- SQLite 优先
- Markdown 优先
- 脚本可跑通优先
- 文档和状态口径优先

但要在现有底座上补 4 层能力。

### 3.1 执行层

保留现有脚本链路作为执行主干：

- 数据采集
- 因子计算
- 美股联动
- 趋势研究生成
- 动态池重建
- 推荐池管理
- 开仓/持仓/风控
- 日报/周报

### 3.2 状态承接层

新增 append-only 的任务状态承接层，用于记录：

- 每次脚本执行创建了什么对象
- 每个对象当前状态是什么
- 它由谁触发
- 它依赖了哪些上游对象
- 它产出了哪些下游对象

### 3.3 知识治理层

新增 `SMR Wiki` 的治理闭环：

- source ingest
- ingest draft
- governance scan
- review queue
- review resolution
- import execution

### 3.4 知识层

新增 `SMR Wiki`，作为 AI 维护的知识编译层。

它不是替代研究卡，而是建立在研究卡、日报、风险复盘、推荐卡之上的“可复用知识层”。

### 3.5 Agent 协作层

按业务性质拆成两类：

- **类 OpenClaw**
  - 处理规则稳定、重复性强、适合脚本化的任务
- **类 Hermes**
  - 处理需要研究积累、复盘、判断、知识沉淀的任务

这一层现在有一个新原则：

- 路由、workspace、session、heartbeat、subagent 协议，优先参考 `OpenClaw`
- memory、skills、delegation、cron、learning loop，优先参考 `Hermes`
- 具体业务状态和知识治理，仍然以 SMR 自己的 `registry + wiki governance` 为真相底座

---

## 4. 目录与数据结构目标

### 4.1 目录目标

建议新增以下目录：

```text
11_smr_wiki/
  raw/
    manifests/
    external/
  wiki/
    sectors/
    stocks/
    theses/
    strategies/
    playbooks/
    risk_cases/
    decisions/
    timelines/
  schema/
    naming_rules.md
    ingest_rules.md
    governance_rules.md
    lint_rules.md
    reason_catalog.md
    page_templates/
  drafts/
    ingest/
    review_exports/
```

同时新增脚本目录：

```text
08_scripts/wiki/
08_scripts/registry/
```

### 4.2 数据结构目标

SQLite 中建议逐步新增：

- `task_registry_entry`
  - 记录任务快照
- `task_registry_entity_latest`
  - registry 的最新状态视图
- `source_manifest`
  - 记录原始资料对象
- `smr_wiki_ingest_draft`
  - 记录知识草稿
- `smr_wiki_import_execution`
  - 记录导入治理与导入审计
- `smr_wiki_review_queue_execution`
  - 记录每次 backlog 扫描
- `smr_wiki_knowledge_index`
  - 记录知识页索引、来源、关联实体、更新时间

### 4.3 数据真相分层

后续必须明确下面这套真相分层：

1. 市场数据真相：
   - `daily_bar`
   - `us_daily_bar`
   - `factor_daily`
   - `us_signal`

2. 当前池状态真相：
   - `stock_pool_current`

3. 当前研究结论真相：
   - `research_decision_latest`

4. 当前持仓与风控真相：
   - `position`
   - `risk_alert`

5. 当前知识层真相：
   - `11_smr_wiki/wiki/`
   - `smr_wiki_knowledge_index`

注意：

- 研究卡、日报、风险预警、推荐卡，在下一阶段仍然是重要来源，但不再直接等于最终知识层。
- 知识层必须建立在来源之上，而不是替代来源。

---

## 5. 类 OpenClaw / 类 Hermes 的任务分工

### 5.1 类 OpenClaw 负责什么

这类任务的特点是：

- 输入输出边界清楚
- 规则稳定
- 重复率高
- 适合脚本执行
- 适合自动化调度

当前 SMR 里，建议归到类 OpenClaw 的任务有：

- `sync_watchlist.py`
- `ah_daily_bar.py`
- `fundamental.py`
- `us_linkage.py`
- `earnings_monitor.py`
- `generate_trend_batch.py`
- `reconcile_dynamic_pool.py`
- `summarize_research_quality.py`
- `monitor.py`
- `pnl.py`
- 日报骨架生成
- lint / backlog / stale 检查

这类任务的主要产物是：

- 数据表更新
- 快照文件
- 运行日志
- task registry entry
- wiki ingest draft

### 5.2 类 Hermes 负责什么

这类任务的特点是：

- 需要判断
- 需要长期积累
- 需要处理矛盾证据
- 需要做复盘和策略抽象
- 需要把执行结果变成知识

当前 SMR 里，建议归到类 Hermes 的任务有：

- 行业主线研究维护
- 个股 thesis 维护
- 推荐升级/降级解释
- thesis 证伪 / 修正
- 风险案例沉淀
- 组合复盘
- 决策记录
- playbook 编写
- wiki 页面编译与更新
- ingest draft 人工审核

这类任务的主要产物是：

- 研究结论
- wiki 页面
- 审核决议
- reason code
- strategy / playbook / risk case

### 5.3 两类 agent 的协作规则

后续必须遵守下面这条协作原则：

1. 类 OpenClaw 可以产生候选信号、结构化草稿、执行快照。
2. 类 Hermes 负责把高价值信息解释、压缩、治理、沉淀成知识。
3. 高判断密度对象不能由类 OpenClaw 直接写成正式知识。
4. 高风险动作不能由类 Hermes 绕过现有风控门禁直接落库。

---

## 6. 完整施工顺序

下面是正式施工时必须遵守的顺序。

### 阶段 1：先把现有底座收口

### 目标

先把现在这套动态池系统真正收口，保证后面接知识层时不是搭在歪地基上。

### 要做什么

1. 完成 `smr-system-patch-plan.md` 里还没完全收口的底座项。
2. 继续统一 universe 来源，杜绝脚本各自维护名单。
3. 继续收紧结构化研究决策，减少 Markdown 文本解析作为唯一真相。
4. 继续补运行审计，把关键脚本都接到统一日志口径。
5. 补齐动态池、推荐池、组合、风控之间的状态边界说明。

### 怎么做

- 以现有 `smr_universe.py` 为中心继续收口脚本入口。
- 以 `research_decision` / `research_decision_latest` 为中心继续压缩文本解析依赖。
- 把 `reconcile_dynamic_pool.py` 的输出对象与事件时间进一步规范化。
- 把关键脚本统一写 `script_runs.jsonl`，并为后续 registry 留字段。

### 验收标准

- 关键脚本不再使用内部硬编码 universe。
- 动态池变化可以追踪到明确的 research decision 或 factor 触发。
- 推荐池、开仓、风控三层口径一致。
- 日报、调度板和动态池当前状态不打架。

---

### 阶段 2：建立 SMR Wiki 的目录、模板和规则层

### 目标

先把知识层的目录结构、页面类型、命名规范和 ingest 规则定下来。

### 要做什么

1. 建立 `11_smr_wiki/` 目录骨架。
2. 定义页面类型。
3. 定义命名规则。
4. 定义哪些内容是 raw source，哪些内容是 wiki page，哪些内容是治理输出。
5. 定义 page template 和 metadata 规范。

### 页面类型建议

- `sectors/`
  - 行业主线页
- `stocks/`
  - 个股长期定位页
- `theses/`
  - 主题逻辑页
- `strategies/`
  - 中线策略页
- `playbooks/`
  - 操作手册页
- `risk_cases/`
  - 风险案例页
- `decisions/`
  - 关键决策页
- `timelines/`
  - 主题与个股时间线

### 怎么做

- 先用 Markdown 目录，不上数据库 CMS。
- 先只定义模板、frontmatter、引用规则、来源字段、更新时间字段。
- 先手工编 1 个行业页、2 个个股页、1 个 risk case、1 个 decision，验证模板是否够用。

### 验收标准

- Wiki 目录清晰，页面类型不混乱。
- 同一类内容不会同时落到研究卡、日报、wiki 三个地方却没有边界。
- 后续脚本知道什么能写入 raw source，什么只能写 draft。

---

### 阶段 3：建立 source manifest 和历史资料索引层

### 目标

先让系统知道“有哪些原始资料值得进入知识治理”。

### 要做什么

把现有高价值资料编成统一索引：

- `02_research/industry/`
- `02_research/stock/`
- `03_stock_pool/`
- `05_risk/alerts/`
- `06_reports/daily/`
- `04_portfolio/positions/`
- `00_control/dispatch_board.md`

### 怎么做

新增脚本建议：

- `08_scripts/wiki/index_sources.py`
- `08_scripts/wiki/build_source_manifest.py`

建议抽象以下来源类型：

- `industry_research`
- `stock_research`
- `recommendation_card`
- `daily_report`
- `dispatch_snapshot`
- `risk_alert_snapshot`
- `portfolio_review`
- `pool_snapshot`

每个 source manifest 至少记录：

- `source_id`
- `source_type`
- `entity_type`
- `entity_id`
- `source_path`
- `created_at`
- `updated_at`
- `upstream_refs`
- `tags`

### 验收标准

- 系统能列出“当前有哪些历史资料对象”。
- 后续 ingest draft 不用再直接全盘扫描文件系统。
- 至少把现有核心研究卡、日报、风险预警、推荐卡都纳入 manifest。

---

### 阶段 4：建立知识草稿层（ingest draft）

### 目标

把“执行结果”和“研究产物”先转换成知识草稿，而不是直接进入正式知识层。

### 要做什么

新增 `smr_wiki_ingest_draft`，让下列来源都能产出 draft：

- 新生成的研究卡
- 推荐升级/降级
- 风险预警与处理结果
- 日报里确认过的高价值结论
- 周报和组合复盘
- 主题判断变化

### 怎么做

新增脚本建议：

- `08_scripts/wiki/create_ingest_draft.py`
- `08_scripts/wiki/list_ingest_drafts.py`
- `08_scripts/wiki/export_draft_markdown.py`

draft 至少要有这些字段：

- `draft_id`
- `source_id`
- `draft_type`
- `entity_type`
- `entity_id`
- `title`
- `summary`
- `candidate_category`
- `candidate_tags`
- `governance_status`
- `approval_status`
- `created_at`

### 当前阶段的原则

- draft 只是一份候选知识，不等于正式结论。
- 类 OpenClaw 任务可以自动产 draft。
- draft 默认不直接写正式 wiki。

### 验收标准

- 至少能从 1 张行业研究卡、1 张个股深度卡、1 条风险预警、1 篇日报，自动生出 draft。
- draft 能回溯到来源文件。

---

### 阶段 5：建立治理层（scan / review queue / resolution / import）

### 目标

把知识草稿的治理流程做成固定协议，而不是做成口头流程。

### 要做什么

1. 先做 draft scan。
2. 再做 review queue。
3. 再做 review resolution。
4. 最后做 import execution。

### 治理状态建议

- `ready`
- `review_required`
- `blocked`

### 审批状态建议

- `auto_ready`
- `pending_manual_review`
- `approved`
- `rejected`
- `reopened`

### reason code 目录建议

至少先做下面几类：

- `duplicate_source`
- `duplicate_thesis`
- `insufficient_evidence`
- `conflicts_with_latest_research`
- `outdated_conclusion`
- `needs_human_judgement`
- `format_incomplete`
- `source_not_reliable`

### 怎么做

新增脚本建议：

- `08_scripts/wiki/scan_ingest_drafts.py`
- `08_scripts/wiki/build_review_queue.py`
- `08_scripts/wiki/resolve_review.py`
- `08_scripts/wiki/import_wiki_entry.py`

治理规则优先从最小集合开始：

1. 同一个来源不能重复导入。
2. 同一实体同一主题若已有较新知识页，默认进入 review。
3. 高风险对象默认人工审核。
4. 只有通过治理的 draft 才能进入 `11_smr_wiki/wiki/`。
5. 每次审核和导入都必须落审计记录。

### 验收标准

- 至少跑通一次：
  - draft -> ready -> import
- 至少跑通一次：
  - draft -> review_required -> approved -> import
- 至少跑通一次：
  - draft -> rejected -> reopened -> approved

---

### 阶段 6：建立 task registry 承接层

### 目标

把当前“脚本跑完只留结果”的模式，升级成“脚本跑完会留下可追踪的任务快照”。

### 要做什么

对下列对象补 registry 快照：

- 数据采集任务
- 因子计算任务
- 美股信号任务
- 趋势研究生成任务
- 动态池重建任务
- 推荐生成任务
- 风控检查任务
- 开仓尝试
- PnL 更新
- 日报生成
- wiki draft scan / import / review queue

### 怎么做

新增：

- `08_scripts/registry/register_snapshot.py`
- `08_scripts/registry/query_registry.py`

建议 registry 字段：

- `id`
- `entity_type`
- `entity_id`
- `status`
- `source`
- `relationships`
- `payload`
- `snapshot_index`
- `created_at`

### 为什么这一阶段放在治理层后面

因为我们先要知道系统里有哪些对象值得被追踪，再去做稳定的 registry 边界。

### 验收标准

- 至少能追一条完整链路：
  - 美股信号 -> 趋势研究 -> 研究卡 -> 动态池更新 -> 日报 -> draft
- 至少能追一条风险链路：
  - 持仓 / 风控 -> alert -> draft / risk case

---

### 阶段 7：基于上游原版做 SMR Agent Runtime，并把双 agent 协作真正接到业务链路

### 目标

不是去造一个通用 agent 框架，也不是直接部署原版产品壳，而是以上游原版源码为母版，把 SMR 里的任务分发边界、交接协议和沉淀机制做出来。

详细落地方案见：

- [smr-dual-agent-architecture.md](/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/09_runbooks/smr-dual-agent-architecture.md)

### 要做什么

1. 把 `OpenClaw` 的 route / workspace / session / subagent 思路翻译成 SMR 可用的 profile 和 lane。
2. 把 `Hermes` 的 memory / skills / delegation / cron 思路翻译成 SMR 可用的 knowledge 协议。
3. 明确哪些任务默认走类 OpenClaw。
4. 明确哪些任务默认走类 Hermes。
5. 明确两类任务的输入输出契约。
6. 明确 handoff 对象和状态。

### 最小交付建议

建议这一阶段先补下面这些本地对象：

- `12_smr_agents/profiles/`
  - 对应 OpenClaw 风格的 agent profile / workspace / allowlist
- `12_smr_agents/handoffs/`
  - 对应 Hermes 风格的 delegation / review / resolution 契约
- `08_scripts/agents/route_task.py`
- `08_scripts/agents/create_handoff.py`
- `08_scripts/agents/list_handoffs.py`
- `08_scripts/agents/resolve_handoff.py`

### 建议的协作链

#### 链路 A：趋势驱动研究

1. 类 OpenClaw 发现强趋势标的。
2. 自动生成初始研究任务和 source manifest。
3. 自动生成 research ingest draft。
4. 类 Hermes 完成研究结论、补证据、决定池子建议。
5. 动态池脚本再根据结构化结论重建池状态。

#### 链路 B：推荐升级/降级

1. 类 OpenClaw 检测到研究质量、因子、风险条件变化。
2. 生成升级/降级候选。
3. 类 Hermes 给出解释、补充 reason code 和 thesis 变更说明。
4. 审核通过后写 recommendation / decision / wiki。

#### 链路 C：风险与复盘

1. 类 OpenClaw 生成 alert。
2. 类 Hermes 解释 alert 背后的 thesis 风险或组合问题。
3. 处理结果沉淀为 risk case / playbook / decision。

### 验收标准

- 至少有一条行业研究链路完成双 agent handoff。
- 至少有一条推荐升级或降级链路完成双 agent handoff。
- 至少有一条风险复盘链路完成双 agent handoff。
- 至少有一组 profile / handoff 对象能明确映射到上游设计，而不是只剩名字借鉴。

---

### 阶段 8：把日常工作流接到知识闭环

### 目标

让系统每天不是“重新开始”，而是在旧知识上继续推进。

### 要做什么

把下面这些日常流程接到知识闭环：

- 盘前简报
- 日报
- 周报
- 推荐池复盘
- 组合复盘
- 风险复盘

### 怎么做

规则建议：

1. 日报只写“今天发生了什么”。
2. 高价值结论自动产出 wiki draft。
3. 周报负责把连续几天的结论压缩成更稳定的知识对象。
4. 组合与风险复盘优先沉淀 `risk_cases/` 和 `playbooks/`。
5. 过期 thesis、过期 candidate、过期 recommendation，要进入 lint backlog。

### 验收标准

- 连续跑完 1 个完整交易日后，系统能新增可审核的知识草稿。
- 连续跑完 1 周后，系统能生成至少一条新的 strategy / decision / risk case。

---

### 阶段 9：补 lint、过期治理和知识体检

### 目标

防止 wiki 和研究层一起变成脏仓库。

### 要做什么

新增体检脚本，扫描以下问题：

- 长期未更新的 thesis
- 长期停留在 `candidate` 的标的
- 已失效但仍未下线的 recommendation
- 与最新研究冲突的旧知识页
- 没有反向链接的孤儿页
- 缺少来源的知识页
- 风险案例里没有后续处置结论的条目

### 怎么做

新增脚本建议：

- `08_scripts/wiki/lint_wiki.py`
- `08_scripts/wiki/report_stale_knowledge.py`

### 验收标准

- 能稳定产出 backlog 清单。
- backlog 结果能写回调度板或 review queue。

---

## 7. 每个阶段的统一施工要求

所有阶段都必须遵守下面这套要求：

1. **先做最小闭环，不做大而全**
   - 先本地
   - 先 SQLite
   - 先 Markdown
   - 先脚本

2. **所有新增逻辑都要可回溯**
   - 有来源
   - 有状态
   - 有时间
   - 有 reason

3. **高判断密度内容一律先走 draft**
   - 不允许脚本直接把高判断内容写成正式 wiki 真相

4. **当前动态池和风控门禁不能被旁路**
   - 新机制必须接在现有链路上，而不是另起一套平行系统

5. **文档、模板、脚本、数据库口径同步**
   - 每一阶段完成时都要同步更新相关 runbook 和模板

---

## 8. 当前明确不做的事

下一阶段明确不做下面这些事：

1. 不先上 Mongo / Redis / RabbitMQ / 调度 worker。
2. 不先做向量数据库和复杂检索平台。
3. 不先做通用多平台 agent runtime。
4. 不允许推荐、开仓、风控绕过现有门禁体系。
5. 不直接把旧研究卡整体搬成 wiki，而不做治理。
6. 不把日报当 wiki。

---

## 9. 正式施工时的推荐执行顺序

正式进入施工后，按下面顺序一项一项推进：

1. 继续完成底座收口
2. 建 `11_smr_wiki/` 和 schema 规则
3. 做 source manifest
4. 做 ingest draft
5. 做 review queue / resolution / import
6. 做 task registry
7. 做双 agent handoff
8. 做日报/周报/风险复盘接入
9. 做 lint 和过期治理

这 9 步里，前 5 步优先级最高。

---

## 10. 本计划对应的第一施工批次

正式开工后，第一批只做下面这些：

### 第一批范围

- 完成底座收口里的未完项
- 建 `11_smr_wiki/` 目录和 schema
- 建 source manifest
- 建 ingest draft 最小闭环

### 第一批暂不碰

- 双 agent 深度协作自动化
- 大规模 review queue 扩展
- 复杂 lint 报表
- 更重的基础设施

### 第一批完成的标志

如果第一批结束时满足下面几点，就说明方向走对了：

- 现有动态池系统没有被破坏
- 新知识层已经有目录、模板和规则
- 至少一批现有研究/日报/风险对象已经能进入 ingest draft
- draft 能回溯来源
- 后续可以自然进入治理和导入阶段

---

## 11. 一句话执行原则

SMR 下一阶段的核心，不是“再造一个更大的脚本系统”，而是把当前已经跑起来的研究与交易支持系统，升级成一个**会持续积累知识、会治理结论、会记录状态、会分工协作**的长期系统。
