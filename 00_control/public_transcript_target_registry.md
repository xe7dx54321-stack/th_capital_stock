# SMR 公开电话会文字稿目标注册表

> 这份表定义的是“值得长期跟踪公开电话会文字稿的公司 / 实体”。
> 当前正式生产先接 `The Motley Fool` 这类公开可访问、结构相对稳定的电话会文字稿页面。
> `Status` 表示当前建设状态：`live`（已纳入正式建设）、`experimental`（已验证但还在磨稳定性）、`planned`（计划中）。

## Targets

| Target Key | Entity Type | Entity ID | Company | Market | Symbol | Provider | Match Keywords | Status | Enabled | Notes |
|------------|-------------|-----------|---------|--------|--------|----------|----------------|--------|---------|-------|
| mrvl_fool | stock | MRVL | Marvell Technology | US | MRVL | fool | MRVL,Marvell | live | yes | 已确认 2026-03-05 的 `Q4 2026` 电话会文字稿页面可直接抓到正文。 |
| mu_fool | stock | MU | Micron Technology | US | MU | fool | MU,Micron | live | yes | 作为存储链海外映射对象，优先接公开电话会文字稿。 |
| avgo_fool | stock | AVGO | Broadcom Inc. | US | AVGO | fool | AVGO,Broadcom | live | yes | 适合作为交换芯片 / 定制算力链的电话会文字入口。 |
| amd_fool | stock | AMD | Advanced Micro Devices | US | AMD | fool | AMD,Advanced Micro Devices | live | yes | 适合作为算力芯片主线的公开电话会文字入口。 |
| nvda_fool | stock | NVDA | NVIDIA Corporation | US | NVDA | fool | NVDA,NVIDIA | experimental | yes | 预期可命中，但需要验证分页深度和更新频率。 |
| msft_fool | stock | MSFT | Microsoft Corporation | US | MSFT | fool | MSFT,Microsoft | experimental | yes | 作为云 / AI 基建大盘对标，保留公开电话会文字入口。 |
| googl_fool | stock | GOOGL | Alphabet Inc. | US | GOOGL | fool | GOOGL,GOOG,Alphabet,Google | experimental | yes | 作为 GCP / 云厂商 capex 与 AI 基建投入的公开电话会文字入口。 |
| amzn_fool | stock | AMZN | Amazon.com Inc. | US | AMZN | fool | AMZN,Amazon,AWS | experimental | yes | 作为 AWS capex 与 AI 数据中心投入的公开电话会文字入口。 |
| meta_fool | stock | META | Meta Platforms | US | META | fool | META,Meta Platforms,Facebook | experimental | yes | 作为 Meta AI / 数据中心 capex 的公开电话会文字入口。 |
| aapl_fool | stock | AAPL | Apple Inc. | US | AAPL | fool | AAPL,Apple | experimental | yes | 适合作为大盘科技电话会源的稳定性验证对象。 |
| baba_fool | stock | 09988.HK | Alibaba Group | HK | BABA | fool | BABA,Alibaba | experimental | yes | 如果能命中 ADR（美国存托凭证）电话会文字稿，可反哺港股主线。 |
| mrvl_seekingalpha | stock | MRVL | Marvell Technology | US | MRVL | seekingalpha | MRVL,Marvell | planned | yes | 预留 Seeking Alpha（寻求阿尔法）电话会文本接入位，当前先不纳入正式生产。 |
| mu_seekingalpha | stock | MU | Micron Technology | US | MU | seekingalpha | MU,Micron | planned | yes | 预留存储链一手电话会文本补充位。 |
| avgo_seekingalpha | stock | AVGO | Broadcom Inc. | US | AVGO | seekingalpha | AVGO,Broadcom | planned | yes | 预留交换芯片 / AI 互连主线电话会文本补充位。 |
| amd_seekingalpha | stock | AMD | Advanced Micro Devices | US | AMD | seekingalpha | AMD,Advanced Micro Devices | planned | yes | 预留算力芯片主线电话会文本补充位。 |
| nvda_seekingalpha | stock | NVDA | NVIDIA Corporation | US | NVDA | seekingalpha | NVDA,NVIDIA | planned | yes | 预留龙头标的电话会文本补充位；当前存在验证码 / Access denied（拒绝访问）风险。 |
| baba_seekingalpha | stock | 09988.HK | Alibaba Group | HK | BABA | seekingalpha | BABA,Alibaba | planned | yes | 预留港股互联网主线电话会文本补充位。 |
