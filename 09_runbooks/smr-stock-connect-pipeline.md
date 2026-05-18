# SMR Stock Connect 事实层管线

**更新日期**：2026-04-16  
**适用范围**：SMR 官方互联互通事实层输入  
**主脚本**：`08_scripts/events/snapshot_stock_connect_flow.py`

---

## 1. 现在接通了什么

当前已经接通：

- `沪股通` 日频成交概况
- `港股通(沪)` 日频成交概况
- `深股通` 日频成交概况
- `港股通(深)` 日频成交概况
- `港股通(沪/深)` 官方持有数量
- `沪股通 / 深股通` 官方持有数量
- SQLite 落库
- Markdown 快照
- `task_registry` 登记
- `runlog` 留痕

当前真实落地对象：

- `stock_connect_market_summary`
- `stock_connect_security_holding`
- `01_data/capital_flow/YYYY-MM-DD_stock_connect_flow_snapshot.md`

---

## 2. 官方来源分布

### 上交所

- `沪股通` 日报：
  - `https://query.sse.com.cn/commonSoaQuery.do`
  - `sqlId=FW_HGTZL_HGTSCSJ_HGTCJGK_MRTJ`
- `港股通(沪)` 日报：
  - `https://query.sse.com.cn/ggt/getQuatationInfo.do`
- `沪股通证券持有数量`：
  - `https://query.sse.com.cn/sseQuery/commonSoaQuery.do`
  - `sqlId=FW_HGTZL_HGTSCSJ_HGTZQCYSL_L`
- `港股通(沪)证券持有数量`：
  - `https://query.sse.com.cn/sseQuery/commonSoaQuery.do`
  - `sqlId=FW_HGTZL_GGTSCSJ_GGTZQCYSL`

### 深交所

- `深股通交易日报`：
  - `CATALOGID=SGT_SGTJYRB`
- `港股通(深)交易日报`：
  - `CATALOGID=SGT_GGTJYRB`
- `深股通证券持有数量`：
  - `CATALOGID=SGT_SGTCGSL`
- `港股通(深)证券持有数量`：
  - `CATALOGID=SGT_GGTCGSL`

深交所这几条都走：

- `https://www.szse.cn/api/report/ShowReport/data`
- `https://www.szse.cn/api/report/ShowReport`

---

## 3. 当前频率边界

这条链最关键的不是“有没有数据”，而是**频率必须诚实**。

当前官方可得频率是：

- `沪股通 / 港股通(沪) / 深股通 / 港股通(深)` 成交概况：`日频`
- `港股通(沪/深)` 证券持有数量：`日频`
- `沪股通 / 深股通` 证券持有数量：`季频`

所以当前脚本的处理原则是：

- 市场汇总部分按 `daily_close（日频收盘后）`
- 证券持有数量部分按官方当前可得频率分别落库
- 快照里必须显式写清楚这两套日期，不能假装都是同一天

---

## 4. 当前业务价值

这条链现在已经能稳定回答几类问题：

- 今天四条互联互通通道各自成交强度多少
- 南向资金里，当前关注的港股被官方持有了多少
- 北向官方口径下，当前关注的 A 股在最近可得季度末被持有了多少

它还不能直接回答的，是：

- 北向日频逐股持有变化
- 北向逐日净买入到个股
- 行业级北向 / 南向日频拆解

---

## 5. 后续建议

下一步建议：

1. 把 `stock_connect_market_summary` 的日度变化压进 `strategy_watch / daily_report`
2. 对 `stock_connect_security_holding` 增加“相对上次披露变化”计算
3. 继续找官方北向逐股日频口径；如果官方没有，再单独登记一条 `experimental` 聚合源，不和官方源混写
