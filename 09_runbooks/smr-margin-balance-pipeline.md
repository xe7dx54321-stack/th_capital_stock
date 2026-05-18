# SMR 两融事实层管线

**更新日期**：2026-04-16  
**适用范围**：SMR 官方两融事实层输入  
**主脚本**：`08_scripts/events/snapshot_margin_balance.py`

---

## 1. 这条链现在做到哪了

当前已经接通：

- 上交所两融汇总
- 上交所两融明细
- 深交所两融汇总
- 深交所两融明细
- SQLite 落库
- Markdown 快照
- `task_registry` 登记
- `runlog` 留痕

当前真实落地对象：

- `margin_market_summary`
- `margin_security_detail`
- `01_data/capital_flow/YYYY-MM-DD_margin_balance_snapshot.md`

---

## 2. 来源口径

### 上交所

- 官方接口：`https://query.sse.com.cn/marketdata/tradedata/queryMargin.do`
- 汇总：`beginDate + endDate`
- 明细：`tabType=mxtype + detailsDate`

### 深交所

- 官方汇总 JSON：
  - `https://www.szse.cn/api/report/ShowReport/data`
- 官方明细 xlsx：
  - `https://www.szse.cn/api/report/ShowReport`

---

## 3. 标准化口径

库内统一按下面这套标准存：

- 金额：`元`
- 数量：`股 / 份`
- `trade_date`：`YYYY-MM-DD`

所以：

- 深交所汇总页原本是 `亿元 / 亿股(份)`，入库前会统一换算回 `元 / 股(份)`
- Markdown 快照展示时，再换算成 `亿元 / 万股(份)`，方便人看

---

## 4. 自动回退规则

因为交易所官网不一定在本地收盘数据出来后立刻同步，所以脚本不是死抓“今天”。

实际规则：

1. 先取本地 `daily_bar` 最新 A/H 交易日作为锚点。
2. 对上交所、深交所分别向前回退。
3. 只有“汇总和明细都拿到”才认定该交易所当天可用。
4. 最终在快照顶部显式写出两个交易所各自真正使用的交易日。

---

## 5. 当前边界

当前这条链已经是正式事实层，但还存在边界：

- 上交所明细官方接口不直接给 `融券余额(元)`，所以对应字段可能为空
- 深交所汇总页不给 `融资偿还额 / 融券偿还量`，所以汇总层这两个字段可能为空
- 现在只做事实层快照，不做“异常变化解释”

---

## 6. 后续建议

下一步建议按这个顺序继续接：

1. `stock_connect_flow`
2. `block_trade_feed`
3. 把 `margin_balance` 的日度变化直接压进 `strategy_watch / daily_report / risk`
4. 再补“20日分位 / 行业相对变化 / 持仓标的异常增减”这层解释因子
