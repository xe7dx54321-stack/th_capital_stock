# SMR 放大量级研究覆盖注册表

> 这份注册表不直接改 `stock_pool` 真相层。
> 它只定义“信息采集 / 跟踪 / 分析”在不同阶段应该覆盖哪些池、哪些市场、以及大概拉到多大范围。
> 目标是让系统从“只盯少数候选票”升级到“按配置放大覆盖”，但仍然保持边界清楚、口径统一。

## Coverage Profiles

| Profile | Enabled | Pool Types | Markets | Max Targets | Description |
|---------|---------|------------|---------|-------------|-------------|
| standard_external | yes | recommended,candidate | SZ,SH,BJ | 12 | 默认外部研究采集口径，优先高信号池，保持成本可控。 |
| amplified_external | yes | portfolio_seed,recommended,candidate,watchlist,seed | SZ,SH,BJ | 36 | 放大量级外部采集口径，既覆盖当前持仓参照层，也覆盖赛道覆盖层。 |
| amplified_analysis | yes | portfolio_seed,recommended,candidate,watchlist | SZ,SH,BJ,HK | 24 | 放大量级分析口径，用于客观监控、策略观察和更宽范围 follow（跟踪）。 |

## Sector Radar

| Sector | Priority | Target Coverage | Notes |
|--------|----------|-----------------|-------|
| semiconductor_photonics | 1 | 10 | 当前组合、轮动候选和产业主线高度相关，优先保持高密度跟踪。 |
| semiconductor_compute | 1 | 10 | 继续跟踪算力、芯片设计、存储和设备联动。 |
| embodied_ai | 2 | 8 | 作为中期赛道池，保持持续扫描，但不必一开始全量深挖。 |
| ai_agent | 2 | 6 | 兼顾应用侧和平台型机会，和海外映射一起看。 |
| quantum | 3 | 4 | 主题弹性大，但稳定性弱，适合中低频跟踪。 |

## 使用原则

- `standard_external`
  - 适合日常低成本巡检。
- `amplified_external`
  - 适合进入“放大量级”后的信息采集批次。
- `amplified_analysis`
  - 适合客观监控和策略观察扩大覆盖面时使用。
- 如果要临时改池范围，优先用脚本参数 `--pool-type` 覆盖，不要直接改脚本逻辑。
- 如果未来要继续扩赛道或扩个股，优先先补 `watchlist_registry.md` / `portfolio_holdings_registry.md`，再由这里控制采集强度。
