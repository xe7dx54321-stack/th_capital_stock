# SMR 种子标的注册表

> 这里定义的是 SMR 的基础覆盖 universe，不等于实时 `watchlist`。
> 实时 `watchlist / candidate / recommended` 由研究结论和最新因子共同驱动，落库到 `stock_pool`。

> **种子层（Seed Tier）语义澄清（SPEC 2）**：
> 本文件 = SMR 的"种子层"（Seed Tier），定义了系统启动时默认覆盖的核心标的。
> 系统上线后，自主发现管线会在"主题边界"内扫描新标的，
> 新标的不会自动写入此文件——需通过"发现→VFM评分→人工确认→入池"流程进入 stock_pool 表。
> 本文件仅维护人工指定的"必须覆盖"的核心锚点。

## A股标的

### 具身智能/机器人

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 688017 | 绿的谐波 | embodied_ai | watchlist | 2026-04-09 |
| 300124 | 汇川技术 | embodied_ai | watchlist | 2026-04-09 |
| 601689 | 拓普集团 | embodied_ai | watchlist | 2026-04-09 |
| 002050 | 三花智控 | embodied_ai | watchlist | 2026-04-09 |
| 603728 | 鸣志电器 | embodied_ai | watchlist | 2026-04-09 |
| 002796 | 中大力德 | embodied_ai | watchlist | 2026-04-09 |
| 301368 | 丰立智能 | embodied_ai | watchlist | 2026-04-09 |
| 688322 | 奥比中光 | embodied_ai | watchlist | 2026-04-09 |
| 002600 | 领益智造 | embodied_ai | watchlist | 2026-04-09 |
| 600580 | 卧龙电驱 | embodied_ai | watchlist | 2026-04-09 |

### 半导体/算力

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 688041 | 海光信息 | semiconductor_compute | watchlist | 2026-04-09 |
| 688256 | 寒武纪 | semiconductor_compute | watchlist | 2026-04-09 |
| 688008 | 澜起科技 | semiconductor_compute | watchlist | 2026-04-09 |
| 301269 | 华大九天 | semiconductor_compute | watchlist | 2026-04-09 |
| 688521 | 芯原股份 | semiconductor_compute | watchlist | 2026-04-09 |
| 603986 | 兆易创新 | semiconductor_compute | watchlist | 2026-04-09 |

### 光模块/CPO

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 300308 | 中际旭创 | semiconductor_photonics | watchlist | 2026-04-09 |
| 300502 | 新易盛 | semiconductor_photonics | watchlist | 2026-04-09 |
| 300394 | 天孚通信 | semiconductor_photonics | watchlist | 2026-04-09 |
| 002281 | 光迅科技 | semiconductor_photonics | watchlist | 2026-04-09 |
| 300620 | 光库科技 | semiconductor_photonics | watchlist | 2026-04-09 |
| 872808 | 曙光数创 | semiconductor_photonics | watchlist | 2026-04-09 |
| 002837 | 英维克 | semiconductor_photonics | watchlist | 2026-04-09 |

### AI应用

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 002230 | 科大讯飞 | ai_agent | watchlist | 2026-04-09 |
| 688111 | 金山办公 | ai_agent | watchlist | 2026-04-09 |
| 603039 | 泛微网络 | ai_agent | watchlist | 2026-04-09 |

### 量子

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 688027 | 国盾量子 | quantum | watchlist | 2026-04-09 |

## H股标的

| Code | Name | Sector | Pool | Added |
|------|------|--------|------|-------|
| 09980 | 优必选 | embodied_ai | watchlist | 2026-04-09 |
| 00020 | 商汤-W | ai_agent | watchlist | 2026-04-09 |
| 00981 | 中芯国际 | semiconductor_compute | watchlist | 2026-04-09 |
| 01347 | 华虹半导体 | semiconductor_compute | watchlist | 2026-04-09 |

## 美股对标（仅跟踪，不投资）

| Symbol | Name | Sector | Added |
|--------|------|--------|-------|
| NVDA | 英伟达 | semiconductor_compute | 2026-04-09 |
| AMD | 超微半导体 | semiconductor_compute | 2026-04-09 |
| INTC | 英特尔 | semiconductor_compute | 2026-04-09 |
| AVGO | 博通 | semiconductor_compute | 2026-04-09 |
| LITE | Lumentum | semiconductor_photonics | 2026-04-09 |
| MRVL | Marvell | semiconductor_photonics | 2026-04-09 |
| COHR | Coherent | semiconductor_photonics | 2026-04-09 |
| VRT | Vertiv | semiconductor_photonics | 2026-04-09 |
| TSLA | 特斯拉 | embodied_ai | 2026-04-09 |
| IONQ | IonQ | quantum | 2026-04-09 |
| RGTI | Rigetti | quantum | 2026-04-09 |
| QBTS | D-Wave | quantum | 2026-04-09 |
| CRM | Salesforce | ai_agent | 2026-04-09 |
| NOW | ServiceNow | ai_agent | 2026-04-09 |
| MSFT | 微软 | ai_agent | 2026-04-09 |
| MU | 美光 | semiconductor_compute | 2026-04-09 |
| SNPS | Synopsys | semiconductor_compute | 2026-04-09 |
| CDNS | Cadence | semiconductor_compute | 2026-04-09 |
