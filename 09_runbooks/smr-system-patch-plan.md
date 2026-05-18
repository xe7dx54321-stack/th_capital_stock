# SMR 系统补丁开发计划

## 背景

SMR 已经从“静态架子”进入“可运行状态”，但当前还有几处关键机制会影响长期接管质量：

- 数据层 universe 仍有硬编码
- 研究决策仍有一部分依赖 Markdown 文本解析
- 股票池事件历史还不够可审计
- cron / runbook 还没完全切到动态链路
- 风控和持仓门禁与 runbook 存在落差

本计划的目标，是把系统从“能跑”推进到“可持续运行、可追溯、可扩展”。

## 总体原则

1. 先修底座，再修上层
2. 先消除硬编码和状态歧义，再扩功能
3. 每个补丁都必须有明确验收口径
4. 文档、脚本、数据库口径必须同步

## Patch 顺序

### P0-1 统一 universe 来源

#### 当前状态

- 已启动
- 核心 helper 已落地到 [smr_universe.py](/Users/apple/Documents/同行资本二级市场/08_scripts/lib/smr_universe.py)
- 首批脚本已切换到统一 universe 读取

#### 目标

- 让采集、因子、研究、信号脚本不再各自维护一套股票名单
- 统一改为读取：
  - `watchlist_registry.md` 生成的 `seed`
  - `stock_pool_current`
  - `sector_config`

#### 需要改的模块

- `08_scripts/data_harvester/ah_daily_bar.py`
- `08_scripts/factor_engine/fundamental.py`
- `08_scripts/factor_engine/us_linkage.py`
- `08_scripts/us_signal_harvester/earnings_monitor.py`
- `08_scripts/research/generate_trend_batch.py`

#### 验收标准

- 不再依赖脚本内硬编码 `A_STOCKS / HK_STOCKS / US_BENCHMARKS / LINKAGE_MAP`
- 新加入 `stock_pool_current` 的标的，下一轮脚本可以自动被覆盖
- 同一份 universe helper 被多个脚本复用

---

### P0-2 结构化研究决策 + 股票池事件时间戳

#### 当前状态

- 已启动
- `research_decision / research_decision_latest` 已落库
- 股票池事件已开始写入精确时间戳

#### 目标

- 不再让动态池直接依赖 Markdown 文本解析作为唯一真相
- 让研究决策结构化落库
- 让股票池事件具备精确时间戳，避免同一天多次状态变化互相覆盖

#### 需要改的模块

- 数据库：补结构化 research decision 表
- 股票池：补精确 `event_time`
- 动态池：优先读结构化决策，再回退到解析 Markdown

#### 验收标准

- `recommended > deep_research > initial_trend_card` 的优先级结构化落库
- 同一标的同一天多次状态变化可追溯
- `stock_pool_current` 和 `stock_pool_latest` 的结果不依赖“谁最后写入同一天的同一行”

---

### P1-1 动态链路接入 cron / runbook

#### 当前状态

- 已完成
- runbook 已切到动态链路口径
- cron 部署脚本已更新为动态链路消息
- 本机 8 个 SMR cron 已完成更新

#### 目标

- 把现有动态链路正式纳入日常自动运行
- 避免系统“手动跑是动态的，cron 跑还是老逻辑”

#### 需要改的模块

- `09_runbooks/smr-morning-data-pipeline.md`
- `09_runbooks/smr-afternoon-data-pipeline.md`
- `09_runbooks/smr-daily-brief-workflow.md`
- `08_scripts/_deploy_scripts/deploy_cron.py`

#### 验收标准

- 日常链路明确包含：
  1. `seed sync`
  2. `行情采集`
  3. `因子计算`
  4. `动态趋势研究`
  5. `动态池重建`
  6. `日报/调度板同步`

---

### P1-2 风控与持仓门禁补齐

#### 当前状态

- 已启动
- 开仓脚本已要求 `recommended + confirm`
- 风控脚本已补单票/总暴露/行业集中/周亏损/metadata/止盈止损检查
- dry-run 门禁验证已通过
- [validate_portfolio_gates.py](/Users/apple/Documents/同行资本二级市场/08_scripts/verification/validate_portfolio_gates.py) 已完成沙盒联调验证

#### 目标

- 让“推荐池 -> 持仓 -> 风控”形成真正闭环
- 避免脚本层还能绕过推荐池和风控规则直接开仓

#### 需要改的模块

- `08_scripts/risk_engine/monitor.py`
- `08_scripts/portfolio/entry.py`
- `08_scripts/portfolio/pnl.py`
- `09_runbooks/smr-risk-check.md`
- `09_runbooks/smr-portfolio-review.md`

#### 验收标准

- 开仓默认只能来自 `recommended`
- 行业集中度、weekly loss、thesis 风险能被脚本实际检查
- 风控脚本和风控 runbook 口径一致

---

### P2-1 美股信号和基本面层增强

#### 当前状态

- 已启动
- 美股信号脚本已补去重、A/H 映射和结构化字段写入
- 基本面层已支持 A 股财务摘要与 H 股分析指标
- A 股已补 `revenue / net_profit / ex_profit / gross_margin / debt_asset_ratio` 等字段
- H 股已补 `revenue / gross_profit / holder_profit / revenue_qoq / roa` 等字段
- 研究质量字段已开始结构化落库，并新增质量快照
- 季度/订单层增强待继续

#### 目标

- 让信号层不只看涨跌幅
- 让基本面层逐步从轻量快照走向更可研究

#### 需要改的模块

- `08_scripts/us_signal_harvester/earnings_monitor.py`
- `08_scripts/factor_engine/fundamental.py`

#### 验收标准

- 美股信号支持更清晰的事件分类和去重
- 基本面层具备更好的季度/订单扩展接口

---

### P2-2 历史遗留脚本与运行审计

#### 当前状态

- 已启动
- 危险遗留脚本 `deploy_harvester.py / deploy_scripts.py` 已改成安全版本
- 关键动态链路与部分持仓/风控脚本已开始写入 `10_logs/script_runs.jsonl`

#### 目标

- 避免旧部署脚本误覆盖当前修好的链路
- 让关键脚本具备最低限度的运行审计

#### 需要改的模块

- `08_scripts/_deploy_scripts/deploy_harvester.py`
- `08_scripts/_deploy_scripts/deploy_scripts.py`
- `10_logs/` 相关输出逻辑

#### 验收标准

- 旧错误数据源不再有误触发风险
- 关键脚本执行有统一日志落点

## 当前施工顺序

1. `P0-1` 统一 universe 来源
2. `P0-2` 结构化研究决策 + 股票池事件时间戳
3. `P1-1` 动态链路接入 cron / runbook
4. `P1-2` 风控与持仓门禁补齐
5. `P2-1` 美股信号和基本面层增强
6. `P2-2` 历史遗留脚本与运行审计

## 本轮起始施工范围

- 先完成 `P0-1`
- 紧接着开始 `P0-2`
- 完成后同步 `dispatch_board` 与日报口径
