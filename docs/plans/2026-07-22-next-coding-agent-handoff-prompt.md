# 可直接复制给下一位 Coding Agent 的项目交接 Prompt

下面代码块内的内容可完整复制到新的 Coding Agent 会话中。

```text
你现在接手一个已经连续开发多轮的本地个人投研 Agent 项目。请不要从零设计，也不要凭 README 的旧描述猜测现状。你的任务是先完整理解当前仓库、保护已有开发成果，然后严格按照已确定的总体计划，一个阶段一个阶段地继续施工、真实测试和验收。

【项目位置】
D:\李少博的文件\TH_Capital_二级市场\th_capital_stock_mvp

【产品目标】
这是一个本地优先、自用的二级市场研究 MVP。用户通过自然语言和聊天机器人交互，系统应自动理解问题、选择对应研究工作流、从本地数据库与实时网络按需补证、完成确定性分析与 LLM 综合、生成真正可读且可追溯的研究制品，并把资料和候选记忆伴随沉淀。

它不是券商交易系统，不执行真实交易；不是全市场高频数据平台；不是多人 SaaS。不要引入微服务、消息队列、云数据仓库、Kubernetes 或无目标全量定时抓取。

【首先必须完整阅读，按顺序】
1. README.md
2. docs/plans/2026-07-22-research-agent-system-master-plan.md
3. docs/plans/2026-07-22-knevo-session-workflow-gap-and-roadmap.md
4. docs/plans/2026-07-22-on-demand-acquisition-implementation.md
5. docs/plans/2026-07-21-stock-deep-dive-v3-spec.md
6. docs/adr/0003-stock-deep-dive-v3-staged-governed-synthesis.md
7. docs/adr/0004-natural-language-intent-routing.md
8. docs/adr/0005-stock-v3-stage-observability.md
9. docs/adr/0006-on-demand-write-through-acquisition.md
10. docs/adr/0007-task-shaped-conversational-research-graphs.md
11. 09_runbooks/smr-local-operations.md

必须亲自阅读这些文件，不要只让子 Agent 总结。

【当前架构】
- React/Vite 前台：src/
- Express API、意图和 Node 工作流：api/
- Python 受治理运行时与研究能力：smr_app/
- 采集内核：smr_app/acquisition/
- 控制数据库：01_data/db/smr.db
- 默认真实研究源库：../th_capital_stock/01_data/db/smr.db
- 数据库迁移：migrations/
- 测试：tests/
- 运维：scripts/ 和 09_runbooks/
- 历史资产：08_scripts/、config/phase*.json、legacy/ 等；它们大多已冻结，但不能未经清单审核直接删除。

【当前最重要的已完成能力】
1. 个股深度研究 V3 已有 27 个真实阶段和 15 章中文长报告。
2. 巨潮资讯与深交所正式公告、年报 PDF 和核心财务字段已跑通。
3. 深交所行情、腾讯实时行情/估值、百度历史估值和同行同口径比较已跑通。
4. Acquisition Kernel 已实现 cache_only、refresh_if_stale、force_refresh、Provider 路由、原文/事实/候选证据、冲突隔离、审计和 write-through 沉淀。
5. Research Packet、Claim Compiler、引用校验、隔离字段、报告质量门已落地。
6. 前台已经区分外层意图编排与内层研究主流程，报告正文不会再混入系统状态。
7. 受治理记忆已经具备 candidate/approved/rejected/archived、证据链接、版本和审核日志。

这些能力是基线，不得回退，不得用旧 V1/V2 或通用 LLM 文本替换 V3。

【Knevo 复盘得到的目标能力】
我们在 Knevo 今日会话中观察到六种连续任务：
1. 阳光电源换海光信息：双标的换仓；
2. 海光信息 2026—2028：经营驱动估值；
3. 超节点方向：主题预期差筛选；
4. 星网锐捷市值错误：事实纠错；
5. DCI 很久没有催化：产业因果解释；
6. 德科立认证/泰国工厂/建仓信号：公司信号计划。

Knevo 的长处是按问题形态选择不同工作流、连续复用短期/长期记忆、只获取当前问题需要的数据、输出模型/矩阵/解释/信号清单等不同制品。

但不要照抄它的缺点：它曾把星网锐捷市值写成约 199 亿，实际约 260 亿，并把控股折价错误放大；估值沙箱失败后改为手工计算。我们的系统必须通过跨源校验、确定性计算和依赖重算做到更可靠。

【当前最关键缺陷】
api/services/workflow-engine.js 会在 LLM 路由前通过 isFollowUpQuestion() 把“继续、刚才、上面”等追问直接降级为 chat → analyze_with_llm。这会丢失上轮标的、假设、数据、制品和待验证问题。

当前 intent 粒度也不够，缺少：
- operating_driver_valuation
- pair_switch_decision
- theme_expectation_gap
- industry_causal_explainer
- company_signal_plan
- claim_correction

当前 Firecrawl 还在 api/services/chinese-news-service.js 中作为旧新闻正文补充器，正文被截到 2000 字，尚未进入受治理 Acquisition Kernel。

【工作区安全要求】
- 当前分支是 refactor/personal-research-mvp。
- 当前工作区存在大量已修改和未跟踪文件，它们包含最近开发成果，不是可丢弃垃圾。
- 禁止 git reset --hard。
- 禁止 git checkout -- 覆盖文件。
- 禁止批量删除、清理或移动未知文件。
- 删除候选必须经过 tools/inventory_repository.py、引用检查和人工确认。
- 未经用户明确要求，不提交、不推送、不创建 PR。
- 不输出 .env 或任何凭证值。
- 修改文件使用安全的补丁方式，保留无关改动。

【测试基线，2026-07-22】
- npm.cmd run check:quick：通过；
- Python runtime：33/33；
- Python workflows：45/45；
- Python self-discovery：132/132；
- Express API：74 通过、0 失败、1 个有意跳过；
- React UI：9/9；
- npm.cmd run check:full 当前只在 repository inventory audit 阻断，因为最近新增/修改文件尚未同步 legacy_manifest；业务测试没有失败。

Windows PowerShell 下使用 npm.cmd，不要直接使用 npm，避免 npm.ps1 ExecutionPolicy 错误。

【必须采用的开发顺序】
阶段 0：基线冻结、资产清单同步、check:full 全通过
阶段 1：ResearchTaskEnvelope + ResearchSessionState
阶段 2：Conversation Task Router V2 + Task Graph Registry
阶段 3：共享金融工具门面 + DataRequirementPlanner
阶段 4：经营驱动估值 V1
阶段 5：双标的换仓决策 V1
阶段 6：Firecrawl Research Provider
阶段 7：产业图谱与前瞻数据增强
阶段 8：主题预期差筛选 V1
阶段 9：产业因果解释 V1
阶段 10：公司信号计划 V1
阶段 11：ClaimDependencyGraph + 事实纠错
阶段 12：统一四层记忆
阶段 13：多态制品前台
阶段 14：六轮全链路回放、故障注入和仓库收口

不要跳阶段。每一阶段必须测试通过、真实样本质量达标后，才能开始下一阶段。

【你当前要立即开始的工作】
只开始阶段 0 和阶段 1，不要提前开发后续功能。

第一步：只读审查
1. 运行 git branch --show-current、git status --short、git log -5 --oneline。
2. 阅读上述所有文档。
3. 阅读以下当前实现：
   - api/services/intent-engine.js
   - api/services/workflow-engine.js
   - api/services/chat-enhanced-service.js
   - api/services/session-service.js
   - smr_app/runtime/registry.py
   - smr_app/workflows/stock_deep_dive.py
   - smr_app/acquisition/contracts.py
   - smr_app/acquisition/kernel.py
   - smr_app/adapters/memory.py
4. 运行快速基线和各测试组，记录结果。
5. 不要在完成审查前改代码。

第二步：完成阶段 0
1. 使用仓库自带 inventory 工具重新同步 manifest。
2. 确保所有 DELETE_CANDIDATE 仍 approved=false。
3. 运行 --verify-manifest。
4. 运行 npm.cmd run check:full。
5. 如果失败，先定位真实原因，不允许跳过门禁。

第三步：阶段 1 测试先行
1. 新增 ResearchTaskEnvelope 契约测试。
2. 新增 ResearchSessionState 持久化和恢复测试。
3. 为以下追问写失败测试：
   - 继续
   - 那第二个呢
   - 你刚才说海光已经很贵，那超节点还有谁
   - 星网锐捷市值是 260 亿，不是 199 亿
4. 确认测试因当前追问降级逻辑而失败。
5. 再实现最小代码。

ResearchTaskEnvelope 至少包含：
- task_type
- entities[] 及 role
- topic
- decision_goal
- time_horizon
- requested_artifact
- relation_to_previous: continue/derive/correct/new_task
- parent_task_id
- constraints
- confidence
- needs_clarification

ResearchSessionState 至少包含：
- current_topic
- entities
- confirmed_facts
- data_snapshot_refs
- model_assumptions
- artifact_refs
- open_questions
- user_corrections
- current_task_id

必须把消息历史和研究任务状态分开。不要把一段截断 Markdown 当作任务状态。

【阶段 1 验收】
- “继续”不再直接降级为通用聊天；
- 能识别 continue/derive/correct/new_task；
- 刷新会话后任务状态恢复；
- 新会话不污染旧会话；
- 临时假设不会写入正式记忆；
- 路由结果保存 routing_source、confidence 和 correction_reason；
- 模型不可用时不假装理解复杂追问；
- 原有个股深研 V3 路由和所有现有回归不受影响；
- npm.cmd run check:full 通过。

【数据与事实底线】
- 正式公告、财报、行情和估值优先使用确定性 Provider。
- Firecrawl 只用于网页运输和开放式研究，不替代正式财务事实。
- 新来源必须记录权威等级、日期语义、限流、原文保存和降级顺序。
- 同字段、同口径、同日期冲突时隔离，不覆盖。
- 任何核心数值都要保留单位、币种、报告期和 as_of。
- LLM 不能创造证据 ID。
- 数值计算必须由确定性引擎完成，失败时不得手算兜底。
- 用户纠错只触发重新验证，不能未经核验直接覆盖事实。

【工作方法】
- 一次只做一个阶段。
- 先写失败测试，确认失败原因，再实现。
- 聚焦测试通过后跑相关回归，再跑 quick/full。
- 真实网络测试与确定性 fixture 测试分开。
- 真实测试记录 run ID、来源、时点和制品路径。
- 发现问题要修复根因，不能只调整提示词掩盖数据或路由错误。
- 不为了前台视觉效果虚构步骤、工具调用或子 Agent。
- 不在一个阶段顺便重构无关代码。

【每阶段完成后的汇报格式】
1. 阶段目标与是否完成；
2. 修改文件列表；
3. 新增/修改契约；
4. 测试命令与精确结果；
5. 真实任务 run ID 和制品；
6. 发现并修复的问题；
7. 仍存在的限制；
8. 是否满足验收门槛；
9. 下一阶段建议；
10. git status 摘要，确认未覆盖已有改动。

现在开始：先做只读审查和基线汇报，然后完成阶段 0；阶段 0 全部通过后再进入阶段 1。不要在没有证据的情况下宣称“全部完成”或“质量达标”。
```
