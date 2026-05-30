# SMR Research Upgrade Progress

## Phase 65b: CNINFO Working Parameter Solidification & Real Disclosure Evidence Rerun v1

### 状态
- 日期: 2026-05-29
- 状态: 完成

### 核心突破
- 300308.SZ CNINFO working parameter confirmed: stock=300308,9900022016, org_id=9900022016, plate=sz, column=szse
- CNINFO metadata API -> PDF URL -> PDF download -> PDF text extraction 全链路已真实跑通
- Phase 65 already verified: metadata_sources_found=2645, pdf_text_ok=3

### Phase 65b 目标
- 固化 working parameter 到 identity map
- connector 自动使用正确 identity
- 小规模 metadata/PDF URL/PDF text 提取
- 文本质量分类
- 重跑业务证据
- 更新 watchlist intelligence
- 输出真实披露证据简报

## Phase 67b: IR/Report High-value PDF Execute & Evidence Rerun v1

### 状态
- 日期: 2026-05-29
- Commit: 49a5a2b
- 状态: 验收通过

### 核心结果
- 14/15 高价值 PDF 下载+提取成功
- 行政/法律公告排除: 58 份
- deep evidence: 23 条
- evidence_gain_delta: +7
- claims supported: 7
- claims unconfirmed: 3
- guard_status: pass
- mock/fixture: false, raw/OCR: false, pending/order/trade: 0/0/0

## Phase 68: Evidence Memory & Internal Research Brief Upgrade v1

### 状态
- 日期: 2026-05-29
- 状态: 进行中

### 目标
- 将 Phase 67b 的 23 条真实 deep evidence 写入 evidence memory
- 建立 source trace index
- 建立 evidence-to-claim linkage
- 建立 claim state memory
- 生成 evidence-backed watchlist packet
- 输出 observed-first 内部投研跟踪简报
- 建立 brief evidence citation map 和 quality lint

### 核心边界
- evidence strengthened 不等于买入
- supported 不等于 confirmed
- ASP / 客户份额 / 具体订单量仍不能确认
- 不输出交易建议、目标价、仓位建议
- 不出现系统后台词、教学式提醒
- 不使用 mock/fixture
- 不提交 generated evidence memory

## Phase 69: Multi-ticker Disclosure Pipeline Generalization v1

### 状态
- 日期: 2026-05-30
- 状态: 完成

### 目标
- 从 300308.SZ 单票链路扩展为多标的披露证据链路
- 覆盖 300308.SZ / 688041.SH / 300394.SZ
- 多标的 identity resolver（复用 curated identities）
- 多标的 metadata/high-value/PDF/deep evidence/evidence memory
- capability matrix + research packet + internal brief

### 核心结果
- 300308.SZ: full_chain_available（baseline 不回退）
- 688041.SH: partial_chain_available（identity 已配置）
- 300394.SZ: blocked（identity 缺失）
- pending/order/trade = 0/0/0
- mock/fixture = false

## Phase 69b: Multi-ticker Real Execute & Identity Repair v1

### 状态
- 日期: 2026-05-30
- 状态: 完成

### 目标
- 压实 Phase 69 的多标的泛化，从配置泛化推进到真实执行泛化
- 对 688041.SH 执行真实 metadata/PDF/text/evidence 链路
- 修复 300394.SZ CNINFO identity
- 对 300394.SZ 执行真实 metadata/PDF/text/evidence 链路（若 identity repaired）
- 更新真实 capability matrix，消除 pass 但待验证的口径冲突
- 输出 generic vs ticker-specific report
- 输出多标的 research packet 和 internal brief

### 核心结果
- 300308.SZ: full_chain_available（baseline regression pass）
- 688041.SH: partial_chain_available（identity pass, metadata 执行通过, PDF/text 链路待网络执行）
- 300394.SZ: blocked（org_id 未在 curated identities 中发现，需手动补充）
- identity repair 框架就绪：candidate org_ids 尝试 + metadata 验证
- capability matrix: no_pass_without_execute=true
- 不硬套 AI 光模块变量到 generic_hard_tech
- brief quality lint: pass

### 核心边界
- 没有 execute 不能写 pass
- blocked 必须有 blocker，partial 必须有 partial_reason
- 不复用 300308 org_id 到其他 ticker
- 不硬套 AI 光模块变量
- 不用 mock / fixture
- 不保存 raw / 不 OCR
- 不生成 pending/order/trade
- 不提交 generated/raw/cache/log 文件

## Phase 70: Ticker Identity & PDF Extraction Hardening v1

### 状态
- 日期: 2026-05-30
- 状态: 完成

### 目标
- 修复 688041.SH PDF 下载与文本提取链路
- 诊断 688041.SH PDF URL 问题
- 查找并验证 300394.SZ CNINFO org_id（扩展查找范围至9个备选）
- 固化 300394.SZ curated identity（如找到）
- 对 300394.SZ 执行真实 metadata/PDF/text/evidence 链路
- 更新三票真实 capability matrix

### 核心结果
- 300308.SZ: full_chain_available（baseline 不回退）
- 688041.SH: PDF URL 诊断完成（55条PDF链接，格式正常），download/text 硬化代码就绪
- 300394.SZ: 扩展9个备选org_id查找，均未通过CNINFO metadata验证，需手动从CNINFO页面提取

### 阻塞点
- 688041.SH: PDF下载/text提取需稳定网络环境执行
- 300394.SZ: verified org_id 未找到（扩展后仍失败），需手动查找

### 核心边界
- no pass without execute
- candidate org_id 未验证不得写 verified
- 不复用其他 ticker org_id
- 不硬套行业变量
- 不用 mock / fixture
- 不保存 raw / 不 OCR
- 不生成 pending/order/trade

## Phase 71: Alternative Disclosure Sources & IRM/SZSE/Company Site Fallback v1

### 状态
- 日期: 2026-05-30
- 状态: 完成

### 目标
- 从 CNINFO 单点扩展到多源 fallback（5个替代源）
- 建立 alternative source registry、fallback route engine、known URL catalog
- 接入 IRM 互动易、SZSE/SSE 交易所披露页、公司 IR 页
- 建立 fallback text fetch / normalize / evidence extraction
- 输出 multi-source capability matrix 和 fallback evidence gain

### 核心结果
- 300308.SZ: CNINFO full_chain_available，fallback optional
- 688041.SH: CNINFO metadata pass/pdf blocked，SSE page 已配置为 fallback
- 300394.SZ: CNINFO identity blocked，IRM + SZSE page 已配置为 fallback
- 5 个替代源 registry 完成，fallback route engine 完成
- Known URL catalog 和 company IR page 需手动填写 URL
- brief quality lint: pass

### 阻塞点
- company IR page URL 需手动查找填写
- known source URL catalog 需手动补充
- IRM 和交易所页面的真实文本提取需网络环境执行

### 核心边界
- fallback attempt 不等于 pass
- management commentary 不等于 confirmed
- 公司官网文案不等于强证据
- 不使用 mock / fixture
- 不保存 raw / 不 OCR
- 不生成 pending/order/trade

## Phase 72: Fallback Source Real Text Acquisition & URL Catalog Filling v1

### 状态
- 日期: 2026-05-30
- 状态: 完成

### 目标
- 从 fallback 架构推进到 fallback 真实取数
- 建立 URL catalog filling helper、company IR candidate patch、known URL catalog patch
- 对 IRM / exchange / company IR / known URL 执行真实 execute hardening
- 建立 fallback text quality classifier
- 执行 fallback evidence rerun
- 统计 fallback evidence gain

### 核心结果
- URL catalog filling: 688041 SSE candidate URL registered
- Company IR patch: 688041 SSE page candidate, 300394 manual required
- IRM real execute: framework ready, 300394 SZ market supported
- Exchange real execute: framework ready for SSE/SZSE
- Source-level blockers identified for each source
- brief quality lint: pass

### 阻塞点
- 688041: SSE page candidate registered, network execution pending
- 300394: IRM QA + SZSE page need network execution; company IR URL manual
- fallback_texts_usable = 0 (waiting for network execution)

### 核心边界
- fallback attempt != pass
- management commentary != confirmed
- company context != strong_direct
- metadata-only 不当正文
- 不使用 mock / fixture
- 不保存 raw / 不 OCR
- 不生成 pending/order/trade

## Phase 73: Fallback Source Endpoint Repair & Manual URL Seeding v1

### 目标
- 修复 IRM HTTP 405：8 个端点变量
- 修复 SSE HTTP 404：8 个 URL 变量
- 诊断 SZSE HTTP 500：8 个端点组合
- 688041 补入 Hygon 官网和 IR 页面 URL
- 300394 company IR 标记 manual_fill_required_after_attempt

### 产出
- py_compile: 0 errors
- unittest: 64/64
- Phase 72 未回退
- 新文件: 43 个

### 核心边界
- fallback attempt != pass
- management commentary != confirmed
- company context != strong_direct
- 不使用 mock / fixture
- 不生成 pending/order/trade

## Phase 74: Fallback HTML Parsing & Text Extraction v1

### 目标
- 通用HTML解析工具：visible text, link extraction, PDF detection, boilerplate removal
- IRM HTML QA解析器：正则匹配问/答模式
- SSE HTML公告解析器：链接和PDF提取
- Hygon IR HTML解析器：三页面文本抽取
- HTML文本质量分类器
- fallback evidence extraction / gain / memory

### 产出
- py_compile: 0 errors
- unittest: 57/57
- Phase 73 未回退
- 新文件: 40 个

### 核心边界
- HTML link metadata != 正文
- management commentary != confirmed
- company context != strong_direct
- 不使用 mock / fixture
- 不保存 raw / 不 OCR

## Phase 75: Fallback HTML Real Execute & Evidence Breakthrough v1

### 目标
- 真实执行 IRM HTML QA parser
- 真实执行 SSE HTML disclosure parser
- 真实执行 Hygon IR HTML parser
- 真实执行 seeded URL HTML text extractor
- 合并 fallback text pool
- 执行 quality classification
- 执行 fallback evidence extraction
- 写入 evidence memory
- 更新 multi-source capability matrix
- 输出 research packet 和 internal brief

### 核心边界
- HTML link metadata != 正文
- management commentary != confirmed
- company context != strong_direct
- metadata-only 不当正文
- 不使用 mock / fixture
- 不保存 raw / 不 OCR
- 不生成 pending/order/trade
