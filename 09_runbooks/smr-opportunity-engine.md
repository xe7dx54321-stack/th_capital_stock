# SMR 主动机会引擎

## Boundary

- Codex 只作为开发工具，不参与日常运营。
- 日常运行由项目内 agent schedule 触发。
- 当前机会引擎固定为 `paper_only`，不连接券商，不生成真实下单指令。
- 所有真实组合动作仍然走既有组合动作、执行前检查和风控门禁。

## Borrowed Patterns

本模块吸收了几个开源项目中适合 SMR 的能力，但不直接把外部系统整包并入：

- QuantDinger: idea -> strategy -> backtest -> attack/defense -> paper monitor 的闭环，以及 paper-only 默认边界。
- Qlib: 因子和截面排序思路，用于把覆盖库里的标的主动排出优先级。
- vectorbt: 批量回测和参数扫描的思想；当前先落成轻量历史证据，后续可替换为真正的 vectorized backtest。
- vn.py: 事件驱动和执行隔离思想；当前只做事件/信号监控，不接真实 gateway。

## Runtime Chain

主动机会链由 `opportunity_radar` job 执行：

1. `08_scripts/reporting/build_market_flow_anomaly_snapshot.py`
2. `08_scripts/opportunity/build_opportunity_radar_snapshot.py`
3. `08_scripts/opportunity/build_strategy_evidence_snapshot.py`
4. `08_scripts/opportunity/build_thesis_attack_defense_snapshot.py`
5. `08_scripts/opportunity/build_paper_trade_watchlist.py`
6. `08_scripts/agents/run_agent_control_loop.py --research-governance-mode skip --build-dispatch`

正式 schedule:

- `opportunity_radar_close`
- 时间：工作日 17:10 Asia/Shanghai
- 牵头岗位：`openclaw_pool_exec`
- 协作岗位：`openclaw_factor_exec`, `hermes_research_curator`, `hermes_reporting_editor`

## Snapshot Types

- `opportunity_radar_snapshot`: 主动机会雷达，输出价格/量能/因子/研究池/事件综合候选。
- `strategy_evidence_snapshot`: 策略证据，输出轻量历史回测结果和证据标签。
- `thesis_attack_defense_snapshot`: 攻防推演，输出 defense、attack、kill triggers 和 verdict。
- `paper_trade_watchlist_snapshot`: 纸面观察单，输出 paper-only ticket。

## Policy

策略边界文件位于 `00_control/opportunity_engine_policy.json`。

关键约束：

- `mode=paper_only`
- `live_trading_enabled=false`
- 任何脚本不得放置真实订单，也不得输出可直接发送给券商的委托指令。

## Dashboard

控制塔 `/opportunities` 页面新增四层：

- 主动机会雷达
- 策略证据
- 攻防推演
- 纸面观察单

这些内容和原有“深度市场分析”并列展示：前者偏动态机会发现，后者偏主题研究和低估候选。
