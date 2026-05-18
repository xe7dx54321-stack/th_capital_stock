# SMR 动态股票池运行说明

## 目标

SMR 的股票池分成两层：

1. `seed`
   - 来自 [watchlist_registry.md](/Users/apple/Documents/同行资本二级市场/00_control/watchlist_registry.md)
   - 作用是定义基础覆盖 universe
   - 不等于实时 `watchlist`

2. 实时池
   - `watchlist / candidate / recommended`
   - 由最新研究结论和最新因子共同驱动
   - 支持持续入池和持续出池

## 当前脚本链路

1. `python3 08_scripts/stock_pool/sync_watchlist.py`
   - 把注册表同步为 `seed`
   - 自动维护 `stock_pool_latest` / `stock_pool_current` 视图

2. `python3 08_scripts/research/generate_trend_batch.py`
   - 不再硬编码个股
   - 从最新 `factor_daily` 动态挑选强趋势标的
   - 自动生成行业趋势卡和个股初始趋势卡

3. `python3 08_scripts/stock_pool/reconcile_dynamic_pool.py`
   - 读取最新研究卡中的 `Suggested Pool`
   - 读取推荐卡
   - 读取最新 `trend_strength`
   - 重建当前有效的 `watchlist / candidate / recommended`
   - 自动生成 [动态池快照](/Users/apple/Documents/同行资本二级市场/03_stock_pool/watchlist/2026-04-10_dynamic_watchlist.md)

## 业务逻辑

### 入池逻辑

- 最新研究卡若给出 `watchlist / candidate / recommended`，研究结论优先。
- 若没有明确研究结论，但最新 `trend_strength >= 1`，则可保留或进入动态 `watchlist`。
- `generate_trend_batch.py` 生成的新趋势卡会把强趋势股推入研究链路，再由动态池脚本落库。
- `recommended` 额外要求通过研究质量门槛：
  - `research_quality_score >= 8.0`
  - `order_evidence` 不能是 `weak/unknown`
  - `commercialization_evidence` 不能是 `weak/unknown`

### 出池逻辑

- 最新研究卡若给出 `drop`，则从实时池移出。
- 若没有研究支持，且最新 `trend_strength < 1`，则从动态 `watchlist` 移出。
- 若最新结论从 `recommended` 降为 `candidate/watchlist/drop`，推荐池会自动失活。
- 若最新结论从 `candidate` 升为 `recommended`，候选池会自动失活。

## 当前约定

- `watchlist_registry.md` 只负责“覆盖哪些方向”，不负责“今天到底盯哪些票”。
- `stock_pool_current` 才是当前有效池。
- `stock_pool` 原表保留事件历史；最新状态通过视图读取。
- 研究质量快照可查看：
  - `/Users/apple/Documents/同行资本二级市场/02_research/summary/2026-04-10_research_quality_snapshot.md`

## 推荐读取口径

- 当前池状态：查 `stock_pool_current`
- 最新状态含 inactive：查 `stock_pool_latest`
- 历史事件：查 `stock_pool`

## 后续可继续增强

- 给 `drop` 增加更细的出池原因分类
- 给不同 sector 配置不同的 watchlist keepalive 阈值
- 加入“研究过期”规则，让长期无人更新的 `candidate` 自动回到 `watchlist`
