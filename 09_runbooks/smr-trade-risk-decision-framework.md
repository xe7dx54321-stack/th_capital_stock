# SMR 买卖决策风控框架

**更新时间**：2026-04-21  
**目标**：把现有风控、策略观察、轮动、组合动作，收口成老板真正能拿来参考的买卖决策结论。

---

## 1. 这套逻辑解决什么问题

原来的 `risk_engine/monitor.py` 更像报警器：

- 仓位超了没有
- 止损到了没有
- 组合回撤超线没有

但老板做决策时真正关心的是：

- 今天能不能买
- 如果能买，买谁更合适，应该大仓还是小仓
- 今天该不该卖
- 如果要卖，是直接卖，还是先减仓，还是先观察

所以这次新增了一层：

- `trade_risk_decision_snapshot`（买卖决策风控快照）

它不是替代底层风控，而是在底层风控之上，生成面向老板决策的话。

---

## 2. 当前真实入口

核心脚本：

```text
08_scripts/risk_engine/build_trade_risk_decision_snapshot.py
```

输出目录：

```text
05_risk/decision/
```

当前最新样例：

```text
05_risk/decision/2026-04-19_trade_risk_decision.md
```

看板入口：

```text
http://127.0.0.1:8877/risk
```

---

## 3. 它吃哪些上游输入

### 3.1 组合层风控

- `risk_monitor_snapshot`
- `execution_precheck_snapshot`
- `risk_alert`

这层回答：

- 当前组合是不是已经进入“暂停新增风险”
- 还有没有未确认的 warning / critical 预警
- 执行前检查到底是 `ready / watch_only / blocked`

### 3.2 研究与机会层

- `strategy_watch_batch`
- `portfolio_action_memo_snapshot`

这层回答：

- 哪些票仍然趋势完好
- 哪些票研究锚点够不够新
- 哪些票估值压力已经高了
- 系统当前更想调入谁、调出谁

### 3.3 持仓层

- `position`
- `portfolio_pnl_snapshot`

这层回答：

- 如果已经接了真实持仓，哪些票已经打到止损或目标位
- 哪些真实持仓缺 thesis / stop / target

---

## 4. 决策口径

### 4.1 组合总状态

组合状态只分 3 档：

- `normal`：可以推进，但仍然只能推进过门禁的票
- `cautious`：只能小仓试单或继续观察
- `blocked`：暂停新增风险，先处理风控阻塞项

当前会触发 `cautious` 的典型情况：

- 还没接真实持仓，只能按 `portfolio_seed`（持仓参照层）推演
- 还有未确认的 warning 风险预警
- 执行前检查仍是 `watch_only`

当前会触发 `blocked` 的典型情况：

- 存在未确认的 critical 风险预警
- 执行前检查是 `blocked`

### 4.2 买入侧

买入侧不是简单的“推荐池 = 买”，而是综合以下维度打分：

- 当前门禁是否通过
- 组合状态是不是 `normal`
- 动作优先级是不是 `high`
- 客观看法是不是 `trend_follow / trend_positive`
- 趋势是不是强、是不是已经过热
- 研究新鲜度够不够
- 官方一手材料够不够新
- 卖方公开参照是不是支持
- 当前涨幅是不是已经太快，不适合追

最后落成 4 档结论：

- `buy`：可买入
- `buy_small`：小仓试单
- `watch`：继续观察
- `block`：暂不买入

### 4.3 卖出侧

卖出侧不是只看跌没跌，而是综合以下维度：

- 是否已进入调出腿
- 是否进入持仓复核
- 客观看法是不是掉到 `observe / repair_needed`
- 是否出现未确认风险预警
- 趋势是否明显转弱
- 研究是否开始失真或变旧
- 真实持仓是否打到止损或目标位

最后落成 4 档结论：

- `sell`：优先卖出
- `trim`：建议减仓
- `watch`：持仓观察
- `hold`：继续持有

---

## 5. 当前参数放在哪里

配置文件：

```text
00_control/portfolio_policy.json
```

这次新增了：

```json
"decision_policy": {
  "buy_score_strong": 75,
  "buy_score_probe": 62,
  "buy_score_watch": 52,
  "sell_score_exit": 60,
  "sell_score_trim": 35,
  "sell_score_watch": 18,
  "default_buy_tranche_pct": 0.08,
  "cautious_buy_tranche_pct": 0.04,
  "chase_pct_threshold": 8.0,
  "pullback_pct_threshold": -5.0,
  "take_profit_pct_threshold": 10.0
}
```

意思很简单：

- 强分数才给正式买入
- 谨慎状态下只给小仓试单
- 涨太快不让追
- 有明显利润、估值又高时，会把减仓优先级往前提

---

## 6. 已挂进自动化班表

这次已经把它挂到正式 `risk_review`（晚间风控链）里：

```text
monitor.py
-> build_trade_risk_decision_snapshot.py
-> run_agent_control_loop.py --build-dispatch
```

也就是说，以后晚间风控链跑完，不只是有报警，还会多出一份“老板今天买卖怎么看”的结果。

---

## 7. 当前边界

这套逻辑现在已经能给出业务结论，但还有 2 个明确边界：

- 如果主项目还没正式导入真实持仓，卖出侧仍然主要按 `portfolio_seed`（持仓参照层）推演
- 这套结论现在是“老板决策支持层”，不是“自动下单层”

换句话说：

- 它已经足够支撑人工决策
- 但还不应该直接自动执行买卖
