# SMR 施工总表

**更新日期**：2026-04-16  
**适用范围**：同行资本二级市场（SMR）当前项目目录  
**文档定位**：这是 2026-04-15 审计后的最新施工主表，用来统一回答 3 件事：

- 当前项目到底已经跑通了哪些子功能
- 距离目标状态还差哪些硬缺口
- 后续应该按什么顺序施工、每一步怎么做、做到什么算完成

---

## 1. 先说结论

SMR 现在已经有一套真实可跑的本地业务骨架，但还不是完整的“稳定业务系统”。

当前已经比较扎实的部分：

- `Python + SQLite + Markdown + task registry + handoff + dispatch` 底座
- A/H/US 行情采集主链
- 因子计算、趋势研究、动态股票池、日报快照
- 双 agent 最小调度链
- `OpenAI shadow`（OpenAI 受控真实调用）受控扩面验证
- wiki draft（知识草稿）与 review queue（审核队列）治理链

当前离目标状态最远的部分：

- 外部来源主链已经补到公告、公开研报列表、公开研报正文详情页、公开研报 PDF 原件、公开研报 PDF 文本抽取、公开研报基础结构化快照、公开研报首版表格结构化快照、资讯搜索页和资讯正文页，但表格结构化覆盖率、事实校验和更多来源覆盖还没补齐
- 研究来源在当前机器上还不够可复核
- 主项目还没有真实持仓样本，组合与风控只跑了空仓 / 沙盒链
- 模型层还是受控试运行，不是正式业务层
- wiki 正式知识沉淀规模还太小

所以后续施工顺序不能乱，必须按下面这个原则推进：

1. 先补真相层断点。
2. 再补可复核来源链。
3. 再补真实业务样本。
4. 最后再逐步放大模型辅助范围。

---

## 2. 目标状态定义

这份施工表对应的目标状态，不是“代码都写了”，而是下面这些业务口径都成立：

- 行情与因子可以稳定日更
- 外部研报 / 公告 / 新闻可以在当前机器内抓取、留痕、复核
- 研究卡、股票池、日报、风控之间形成完整上游依赖链
- 主项目至少有一套真实可追踪的持仓 / 风控 / 日志样本
- 模型只做解释、压缩、治理建议，不直接改真相层
- wiki 可以持续沉淀，不是每次重新从 0 开始
- 双 agent 可以稳定承接“脚本执行”和“知识治理”两类工作

---

## 3. 当前状态总表

| 模块 | 当前状态 | 结论 |
| --- | --- | --- |
| 行情采集 | A/H/US 已补到 `2026-04-13`，当前只剩 `872808.BJ` 因免费历史源缺口仍是单票告警 | 已跑通，仍有单票缺口 |
| 因子引擎 | `trend / fundamental / us_linkage` 已补到 `2026-04-13`，并已加入 freshness（新鲜度）校验 | 已跑通 |
| 美股信号 | `us_signal=44`，`2026-04-14` 有真实成功样本 | 已跑通 |
| 趋势研究生成 | `generate_trend_batch.py` 有真实运行记录 | 已跑通 |
| 研究索引 | `research_index=20`，旧机器路径已清洗完，当前 `20/20` 都指向本机真实文件 | 已跑通 |
| 官方市场资金流事实层 | 已补 `margin_balance` 与 `stock_connect_flow` 两条官方事实层；`margin_market_summary / margin_security_detail / stock_connect_market_summary / stock_connect_security_holding` 已真实落库，并已生成 `2026-04-16` 快照 | 已跑通，解释层仍待补 |
| 外部来源获取 | A 股 `cninfo` 公告链已通，H 股 `HKEX` 公告链已通，东方财富公开研报列表快照已通，东方财富公开研报正文详情页已通，东方财富公开研报 PDF 原件留痕已通，东方财富公开研报 PDF 文本抽取已通，东方财富公开研报基础结构化快照已通，东方财富公开研报表格结构化快照已扩到 `research_table_structured=8`，当前关注池样本 `8/8` 已跑满；东方财富资讯搜索页快照已通，东方财富资讯正文页快照已通；但事实校验、跨来源比对和更多公开来源仍未补齐 | 半跑通 |
| 股票池 | `stock_pool=786`，`watchlist / candidate / recommended` 已有真实产物 | 已跑通 |
| 标的客观监控 | 新增 `stock_objective_monitor_snapshot` 主链；当前默认优先监控 `portfolio_seed=8`；已经能把行情、因子、外部研究和规则化客观看法压成快照，并自动流到 `research_context_note -> dispatch_sync_candidate` | 已跑通 |
| 标的策略观察卡 | 已补 `strategy_watch_batch` 批次层，能把 `stock_objective_monitor_snapshot` 进一步压成逐票策略观察卡，并继续流到 `research_context_note -> dispatch_sync_candidate -> daily_reporting_snapshot` | 已跑通 |
| 机会发现 / 轮动候选 | 已补 `rotation_candidate_snapshot`，能把 `portfolio_seed`（持仓参照层）和 `recommended / candidate`（机会池）放进同一套规则里，产出调入 / 调出候选与轮动对 | 已跑通 |
| 执行方案草案 | 已补 `rotation_execution_plan_snapshot`，当前在 `reference_only` 模式下可按组合约束给出拟替换金额、门禁状态、执行前检查和结构改善口径；未来有真实 `position` 后可自动切到 `live_positions` | 已跑通 |
| 组合动作建议稿 | 已补 `portfolio_action_memo_snapshot`，能把客观监控、策略观察卡、轮动候选和执行方案草案收敛成优先动作清单，并继续流到 `research_context_note -> dispatch_sync_candidate -> daily_reporting_snapshot` | 已跑通 |
| 持仓与交易 | 主库 `position=0`，但 `04_portfolio/intake/2026-04-15_current_holdings_intake.md` 和 `.json` 已落；`portfolio_seed=8` 已入覆盖层；这 8 只真实持仓的 `daily_bar / factor_daily / external_source_snapshot` 已补出首轮样本；同时已补 `build_live_position_template.py -> validate_live_position_intake.py -> import_live_positions.py` 这条真实持仓最小字段接入底座 | 覆盖层已接住，真实持仓导入底座已就绪，正式持仓主链仍待填字段执行 |
| 风控 | 主库 `risk_alert=0`；空仓巡检通，沙盒风险样本通；`risk_monitor_snapshot` 已补进按持仓聚焦的外部研究摘要载荷，风险 handoff 说明稿也能直接显示研报事实锚点，但真实主项目持仓还没验证 | 半跑通 |
| 日报 / dispatch | `06_reports/daily/` 已有多份真实产物，`daily_reporting_snapshot` 已补进外部研究摘要载荷，日报代理现在能直接读到 `research_table_structured / research_structured` 的最新事实锚点 | 已跑通 |
| 双 agent 调度 | `completed=12`，`cancelled=2`，`active=0` | 已跑通 |
| wiki 草稿治理 | 治理链已工作；本轮已新建 `external_source_snapshot -> wiki_draft -> review_queue` 样本，并完成 `review_queue / wiki_draft` 两条 Anthropic 业务 shadow | 已跑通 |
| wiki 正式沉淀 | `smr_wiki_knowledge_index=4` | 半跑通 |
| OpenAI shadow | 已完成 `live smoke`（实时冒烟）与 7 条业务 shadow：`strategy_watch_batch / rotation_candidate_snapshot / rotation_execution_plan_snapshot / portfolio_action_memo_snapshot / daily_reporting_snapshot / dynamic_pool_snapshot / research_context_note` 全部 `http_status=200` | 已跑通但仍受控 |
| Anthropic / Google | `Anthropic` 已通过 `live smoke`（实时冒烟），并已完成 `review_queue / wiki_draft` 两条真实业务 shadow；`Google` 仍无 provider adapter（供应商适配层） | `Anthropic` 已接上且已进业务，`Google` 未接上 |

---

## 4. 子功能施工表

下面这张表是正式施工顺序的主依据。

| 优先级 | 子功能 | 当前缺口 | 施工动作 | 前置依赖 | 完成标准 |
| --- | --- | --- | --- | --- | --- |
| P0 | A/H 行情日更 | 主日期已追平到 `2026-04-13`，当前还剩 `872808.BJ` 单票免费源缺口 | 保持晨间 / 午后链稳定运行，并把单票失败显式写入 runlog 与 freshness 报告 | 现有 `ah_daily_bar.py` | A/H/US 都能更新到最近交易日，连续 3 次运行稳定，且缺口只以显式告警存在 |
| P0 | 因子日更 | 主日期已追平到 `2026-04-13`，下一步重点是稳定日更与门禁 | 把 `fundamental.py / trend.py / us_linkage.py` 继续保持串联运行，并坚持 freshness（新鲜度）校验 | 行情新鲜度恢复 | `factor_daily` 日期和行情日期对齐，连续 3 次无人工补救 |
| P0 | 外部来源留痕 | 已有目录规范与 manifest 主链，但外部来源类型还不够丰富 | 继续补专用来源适配器，优先覆盖公告、新闻搜索页、公开研报搜索页 | 原始目录规范已确定 | 任一研究卡都能追到当前机器内的原始来源文件 |
| P0 | 官方市场资金流事实层 | 两融和 stock connect 已接通事实层，但还没把日度变化正式压进 `strategy_watch / risk / daily_report` | 保持官方抓取链稳定运行，并补变化计算与下游消费链 | 现有 `snapshot_margin_balance.py` / `snapshot_stock_connect_flow.py` | 官方资金流输入连续多次稳定运行，且下游链能直接消费变化结果 |
| P0 | 研报 / 公告 / 新闻获取 | A/H 公告链、东方财富公开研报列表、东方财富公开研报正文详情页、东方财富公开研报 PDF 原件、东方财富公开研报 PDF 文本抽取、东方财富公开研报基础结构化快照、东方财富公开研报首版表格结构化快照、东方财富资讯搜索页、东方财富资讯正文页都已通，但表格结构化覆盖率、事实校验和更多公开来源仍缺 | 在现有 `cninfo + HKEX + 东方财富` 基础上，继续扩表格结构化覆盖率，或补更多稳定公开页快照链 | 外部来源留痕链 | 每天至少能稳定落一批原始来源到本地，并写入 source manifest |
| P1 | 研究索引迁移 | 旧路径已经清洗完成，下一步是把研究主链真正改成“强依赖本机来源” | 保持迁移脚本与审计脚本可重复执行，并把研究生成入口改成“无本机来源只出草稿” | 外部来源留痕链 | `research_index` 主用记录保持本机路径，且新研究不再回流旧口径 |
| P1 | 研究生成质量 | 趋势研究入口已接来源门禁，但其他研究入口还没统一改造 | 保持趋势研究入口的来源包协议，并把同类门禁逐步扩到其他研究生成脚本 | 外部研报获取链 | 新生成研究卡都能通过来源复核 |
| P1 | wiki 治理闭环强化 | 现在 review queue 能跑，但正式入库少 | 把 `draft -> review -> import` 的人工审核标准写死到 runbook，并补重复源、来源缺失、结论过时三类硬门禁 | 研究来源链改善 | 新 wiki 导入都带 reason code（原因码）和来源映射 |
| P1 | 股票池解释层 | 池本身已通，但解释层还偏脚本模板 | 继续把 `dynamic_pool_snapshot` 接到模型 shadow，只产出候选解释块，不改池 | OpenAI shadow 基座 | 动态池变化当天能稳定产出解释候选 |
| P1 | 日报增强层 | 日报已能产出，且 `daily_reporting_snapshot` 已补进外部研究摘要，但模型解释层还没正式放大 | 让 `daily_reporting_snapshot` 在现有研究摘要载荷之上接受模型 shadow 增强，产物只写候选层 | OpenAI shadow 基座 | 每份日报都能附带受控增强候选，不污染正式正文 |
| P1 | 标的客观监控层 | `stock_objective_monitor_snapshot` 和 `strategy_watch_batch` 都已落地，但真实组合执行层还没消费这些结论 | 继续把客观监控和策略观察卡压进组合执行前的观察 / 调整 / 复盘环节 | `portfolio_seed` 覆盖层 + 行情/因子/外部来源 | 不录真实仓位时，系统也能持续输出标的级客观监控与策略观察结论 |
| P1 | 机会发现 / 调仓建议层 | `rotation_candidate_snapshot` 已落地，但目前仍是标的级轮动候选，不是资金级执行方案 | 继续把轮动候选接入组合执行前观察层，再逐步叠加真实仓位、仓位约束和预期收益测算 | `portfolio_seed` + `recommended/candidate` + 客观监控 + 策略观察卡 | 系统能稳定输出“调入哪只 / 调出哪只 / 为什么 / 风险是什么 / 结构上改善了什么” |
| P1 | 执行方案草案层 | `rotation_execution_plan_snapshot` 已落地，但当前还是 `reference_only` 执行草案，不是基于真实持仓成本的最终执行单 | 等真实 `position` 补齐后，把这层切到 `live_positions`，再补止损/目标价/仓位比例优化 | `rotation_candidate_snapshot` + 组合约束 + 真实持仓主表 | 系统能稳定输出“建议换多少、门禁是否允许、执行前还差什么” |
| P1 | 组合动作建议层 | `portfolio_action_memo_snapshot` 已落地，但当前仍基于 `reference_only` 口径收敛动作，不是最终交易指令 | 等真实 `position` 补齐后，把 ready / watch / holding review（持仓复核）和真实仓位日志打通 | 客观监控 + 策略观察卡 + 轮动候选 + 执行方案草案 | 系统能稳定输出“今天先做什么、为什么、风险是什么、下一步检查什么” |
| P1 | 风控解释层 | 主项目空仓，真实风险解释不足；不过 `risk_monitor_snapshot` 已能携带按持仓聚焦的外部研究摘要 | 先给主项目补一套最小真实持仓，再跑 `pnl -> monitor -> risk_update_candidate` 主链 | 持仓样本准备 | 主项目非空仓时，风险候选链能稳定产出，且说明稿里能直接看到对应研报锚点 |
| P1 | 持仓 / 股票日志 | 目前只有脚本运行日志，没有真实持仓业务日志 | 明确 `entry / pnl / monitor / review` 的日志归档位置，补 portfolio 状态快照目录 | 最小持仓样本 | `04_portfolio/` 下出现可追踪的真实样本文件 |
| P1 | 持仓导入与覆盖层 | 用户已给出真实持仓名单，但主库还缺成本/股数/止损等字段；同时这批标的大多不在原始主题 universe | 新增 `portfolio_holdings_registry.md` 与 intake 草稿层，先把名单、代码、板块、系统覆盖状态接住，再通过 `build_live_position_template.py -> validate_live_position_intake.py -> import_live_positions.py` 补最小必需字段进入正式持仓 | 用户提供真实持仓名单 | `04_portfolio/intake/` 有最新导入草稿和 live position 模板/校验产物，`stock_pool_current` 能看到 `portfolio_seed` 覆盖层，字段补齐后可安全写入 `position` |
| P2 | OpenAI shadow 扩面 | `strategy_watch / rotation / daily_report / dynamic_pool / research_context_note` 已补通，下一步主要剩 `risk` 与更多 dispatch sync（调度同步）细分链路 | 继续按 `risk -> risk_update_candidate -> 其他 reporting sync` 顺序扩面；每条链先 shadow，再评估，再保留 | P1 真相层稳定 | 高价值实体的 shadow 留痕继续覆盖到研究、风控、日报三大层 |
| P2 | Anthropic 接入 | `live smoke` 和 `review_queue / wiki_draft` 最小业务试跑都已通，下一步还没进入真实治理决策闭环 | 继续把 Anthropic 固定在 second opinion（第二意见）与治理复核位，只输出候选审核建议，不自动审批 | `review_queue / wiki_draft` shadow 已成功 | Anthropic 稳定给出可复核审核建议，且不越权触发正式导入 |
| P2 | Google 接入 | 当前 runtime（运行时）没有 provider 适配层 | 决定是否真的需要 `google`；如果需要，再补 provider adapter（适配层） | OpenAI 稳定后再评估 | `trend_research_batch` 不再停在 `blocked_provider_unsupported` |
| P2 | wiki 正式沉淀扩容 | 现在只有 4 条正式知识页 | 选 3 类高价值对象优先沉淀：主线时间线、核心个股、风险案例 | 治理标准稳定 | 正式知识页数量和质量同步增长，不靠人工一次次重做 |
| P3 | 自动化调度 | 当前主要是手动 / 半手动执行 | 等 P0-P2 稳定后，再决定哪些链适合 cron（定时）或 heartbeat（心跳） | 前面阶段稳定 | 自动化运行后不产生脏数据、不放大错误 |

---

## 5. 正式施工顺序

下面是建议的正式施工阶段，必须按顺序做，不建议跳。

### Phase 0：先把真相层日期和来源口径修平

目标：

- 行情日期别掉队
- 因子日期别掉队
- 研究来源别继续飘在旧机器路径上

具体动作：

1. 复核晨间 / 午后数据管线，补 A/H 数据刷新断点。
2. 把因子计算做成“依赖行情新鲜度”的顺序执行。
3. 设计最小外部来源目录结构与 manifest 字段。
4. 补第一版“公开研报 / 公告 / 新闻”采集脚本。

验收：

- A/H/US 数据日期追平最近交易日。
- `factor_daily` 日期追平。
- 本机落下第一批可复核外部来源。

### Phase 1：把研究链从“能写卡”改成“能复核”

目标：

- 研究卡不再主要依赖旧机器遗产
- 新研究卡都有本机来源支撑
- wiki 导入开始真正有质量门禁

具体动作：

1. 扫描现有 `research_index`，标记可迁移和不可迁移记录。
2. 修改研究生成入口，没有本机来源就只出草稿，不进正式索引。
3. 把 review queue 的驳回原因码固化成标准流程。
4. 把 source manifest、draft、review、import 四层关系写入运行手册。

验收：

- 新研究卡都能追溯到本机来源。
- wiki 新导入对象不再依赖 `/Users/apple/...`。

### Phase 2：补主项目真实业务样本

目标：

- 主项目不再只有空仓
- 持仓、PnL、风控、日报能出现真实样本联动

具体动作：

1. 设计一套最小模拟持仓或真实观察仓样本。
2. 运行 `entry.py` 门禁，确认推荐池和仓位规则口径一致。
3. 运行 `pnl.py`、`monitor.py`，让主项目出现真实 portfolio（组合）状态。
4. 补 `04_portfolio/` 下的快照与日志落盘。

验收：

- 主库出现可追踪的 `position` 样本。
- 风控输出不再只靠沙盒验证。

### Phase 3：把模型层从“单点成功”扩到“多链受控成功”

目标：

- 模型继续只做候选层
- 不碰正式真相层
- 先扩 OpenAI，再看 Anthropic / Google

具体动作：

1. 先扩 `risk_monitor_snapshot`。
2. 再扩 `us_signal_snapshot`。
3. 再扩 `daily_reporting_snapshot`。
4. 再扩 `dynamic_pool_snapshot`。
5. 每条链都建立 shadow 结果评估口径。

验收：

- 至少 4 条实体稳定通过 shadow。
- 没有模型直接写正式真相层。

### Phase 4：把知识沉淀从“草稿治理”推进到“持续复利”

目标：

- wiki 不只是有流程
- 而是真的开始积累长期可复用知识

具体动作：

1. 优先沉淀主线 timeline（时间线）。
2. 优先沉淀核心个股页。
3. 优先沉淀风险案例页。
4. 把这些沉淀反哺到研究、日报和风控解释层。

验收：

- wiki 正式页数量明显增长。
- 新任务可以复用旧知识，而不是从 0 开始。

### Phase 5：把系统从“收口可跑”推进到“放大量级”

目标：

- 信息采集不再只盯 `candidate / recommended` 这 4 只活跃票
- 外部研究抓取、资讯抓取、公告抓取进入配置化扩容
- 客观监控可以额外生成“放大量级观察稿”，不覆盖正式日报主链

具体动作：

1. 新增 `research_amplification_registry.md`，把 `standard_external / amplified_external / amplified_analysis` 三档覆盖策略固化下来。
2. 把外部采集脚本统一改成支持 `--profile / --pool-type / --limit`。
3. 先用 `amplified_external` 放大 A 股采集范围，再按需继续扩到更多赛道标的。
4. 在搜索页快照和正文页抓取之间，明确插入 `build_source_manifest.py`，避免下游读不到新来源。
5. 给 `stock_objective_monitor_snapshot` 加 `--profile / --label / --skip-handoff`，允许产出单独的放大量级观察稿。

验收：

- `standard_external` 当前解析到 `4` 只 A 股。
- `amplified_external` 当前解析到 `34` 只 A 股。
- `amplified_analysis` 当前解析到 `24` 只 A/H 标的。
- 不改脚本代码，只改配置或命令参数，就能切换轻量 / 放大量级范围。
- 放大量级观察稿不会覆盖现有正式 `2026-04-15_stock_objective_monitor.md` 主链文件。

---

## 6. 接下来 12 个具体施工动作

这部分是最近一轮应该逐条执行的动作清单。

1. 按 `research_amplification_registry.md` 先把外部采集切到 `amplified_external`，让信息覆盖从 `4` 只活跃票放大到 `34` 只 A 股。
2. 把“搜索页快照 -> build_source_manifest -> 正文 / PDF / 结构化”这条中间清单更新步骤写死进 runbook，避免下游漏读新来源。
3. 在现有 `cninfo + HKEX + 东方财富公开研报列表 + 东方财富公开研报正文详情页 + 东方财富公开研报 PDF 原件 + 东方财富公开研报 PDF 文本抽取 + 东方财富公开研报基础结构化快照 + 东方财富公开研报首版表格结构化快照 + 东方财富资讯搜索页 + 东方财富资讯正文页` 基础上，继续扩表格结构化覆盖率并评估事实校验清洗链。
4. 把 `margin_balance / stock_connect_flow` 的变化计算正式压进 `strategy_watch / risk / daily_report`。
5. 把趋势研究入口的来源门禁协议扩到其他研究生成入口。
6. 把 `source_manifest -> draft -> review -> import` 的硬门禁写进 runbook。
7. 补 portfolio 快照目录与日志规则。
8. 新增持仓覆盖注册表和持仓 intake 草稿层，先接住真实持仓名单并补行情/因子覆盖。
9. 给主项目准备一套最小持仓样本，跑主链风控。
10. 把 `risk_monitor_snapshot / daily_reporting_snapshot` 接入受控 OpenAI shadow。
11. 补 wiki 正式沉淀优先级清单，先从 timeline 和核心个股页开始。
12. 针对 `872808.BJ` 单票缺口，评估是否引入更稳的数据源，并继续给 H 股来源链补“重复抓取跳过”和“无结果统计”。

---

## 7. 本阶段严格规则

后面施工过程中，下面这些规则不应被打破：

- 不自动批准真实研究 draft。
- 不让模型直接写正式 wiki。
- 不让模型直接改股票池、持仓、风控真相。
- 不为了“尽快接模型”去绕开当前脚本门禁。
- 不把旧机器路径当成当前机器可复核来源。
- 不把疑似错码的 H 股静默纠正或静默入库，必须显式暴露。
- 不在主项目上直接放开全局真实模型调用。

---

## 8. 与现有文档的关系

这份文档是当前执行主表，和下面这些文档配合使用：

- `09_runbooks/smr-next-stage-development-plan.md`
  - 负责解释大方向和总架构
- `09_runbooks/smr-script-to-model-roadmap.md`
  - 负责解释哪些链应该脚本先行、哪些链适合模型接入
- `09_runbooks/smr-dual-agent-architecture.md`
  - 负责解释类 OpenClaw / 类 Hermes 的分工方式
- `09_runbooks/smr-model-shadow-live-test-runbook.md`
  - 负责解释真实 shadow 如何安全测试

如果后面文档之间出现冲突，以这份施工总表和最新审计结论为准。
