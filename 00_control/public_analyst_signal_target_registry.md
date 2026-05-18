# SMR 公开卖方信号目标注册表

> 这份表定义的是“值得长期跟踪公开卖方信号摘要的公司 / 实体”。
> 当前正式生产只接 `MarketScreener` 这类公开可访问、结构相对稳定的摘要页。
> `Status` 表示当前建设状态：`live`（已纳入正式建设）、`experimental`（已验证但还在磨稳定性）、`planned`（计划中）。

## Targets

| Target Key | Entity Type | Entity ID | Company | Market | Symbol | Provider | Consensus URL | Status | Enabled | Notes |
|------------|-------------|-----------|---------|--------|--------|----------|---------------|--------|---------|-------|
| nvda_marketscreener | stock | NVDA | NVIDIA Corporation | US | NVDA | marketscreener | https://www.marketscreener.com/quote/stock/NVIDIA-CORPORATION-57355629/consensus/ | live | yes | 已验证可直接抓到共识评级、分析师覆盖数、目标价区间和相对现价空间。 |
| amd_marketscreener | stock | AMD | AMD (Advanced Micro Devices) | US | AMD | marketscreener | https://www.marketscreener.com/quote/stock/ADVANCED-MICRO-DEVICES-IN-19475876/consensus/ | live | yes | 已验证页面结构稳定，适合作为算力 / 芯片主线公开卖方信号入口。 |
| msft_marketscreener | stock | MSFT | Microsoft Corporation | US | MSFT | marketscreener | https://www.marketscreener.com/quote/stock/MICROSOFT-CORPORATION-4835/consensus/ | live | yes | 用于云和 AI 基建主线的大盘对标。 |
| mrvl_marketscreener | stock | MRVL | Marvell Technology Group Ltd | US | MRVL | marketscreener | https://www.marketscreener.com/quote/stock/MARVELL-TECHNOLOGY-GROUP--4934/consensus/ | live | yes | 已确认旧链接会失效，当前这条 Nasdaq（纳斯达克）页能返回完整共识数据。 |
| lite_marketscreener | stock | LITE | Lumentum Holdings Inc. | US | LITE | marketscreener | https://www.marketscreener.com/quote/stock/LUMENTUM-HOLDINGS-INC-23132759/consensus/ | live | yes | 已验证可抓，适合作为光通信映射链的公开卖方信号补充。 |
| avgo_marketscreener | stock | AVGO | Broadcom Inc. | US | AVGO | marketscreener | https://www.marketscreener.com/quote/stock/BROADCOM-INC-42668543/consensus/ | live | yes | 适合作为算力互连和交换芯片主线的公开卖方摘要入口。 |
| mu_marketscreener | stock | MU | Micron Technology, Inc. | US | MU | marketscreener | https://www.marketscreener.com/quote/stock/MICRON-TECHNOLOGY-INC-13639/consensus/ | live | yes | 已确认旧的 `13659` 会跳错页面，当前这条才是正确的 Micron 共识页。 |
| nvda_marketbeat | stock | NVDA | NVIDIA Corporation | US | NVDA | marketbeat | https://www.marketbeat.com/stocks/NASDAQ/NVDA/price-target/ | planned | yes | 预留 MarketBeat（市场节拍）公开评级摘要接入位，当前 Cloudflare（反爬拦截）限制较重。 |
| amd_marketbeat | stock | AMD | AMD (Advanced Micro Devices) | US | AMD | marketbeat | https://www.marketbeat.com/stocks/NASDAQ/AMD/price-target/ | planned | yes | 预留算力芯片主线公开卖方摘要补充位。 |
| mrvl_marketbeat | stock | MRVL | Marvell Technology, Inc. | US | MRVL | marketbeat | https://www.marketbeat.com/stocks/NASDAQ/MRVL/price-target/ | planned | yes | 预留光通信 / 互连映射链公开卖方摘要补充位。 |
| avgo_marketbeat | stock | AVGO | Broadcom Inc. | US | AVGO | marketbeat | https://www.marketbeat.com/stocks/NASDAQ/AVGO/price-target/ | planned | yes | 预留交换芯片 / 定制算力链公开卖方摘要补充位。 |
| mu_marketbeat | stock | MU | Micron Technology, Inc. | US | MU | marketbeat | https://www.marketbeat.com/stocks/NASDAQ/MU/price-target/ | planned | yes | 预留存储链公开卖方摘要补充位。 |
