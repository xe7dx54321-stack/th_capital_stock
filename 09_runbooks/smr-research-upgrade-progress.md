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
