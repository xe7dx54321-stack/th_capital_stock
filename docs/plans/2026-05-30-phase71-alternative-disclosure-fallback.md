# Phase 71: Alternative Disclosure Sources & IRM/SZSE/Company Site Fallback v1

## 日期
2026-05-30

## 背景
Phase 70 确认 CNINFO 单点链路有边际收益下降问题：300394 卡在 org_id，688041 卡在 PDF 下载。Phase 71 建立多源 fallback。

## 覆盖标的
- 300308.SZ: baseline regression
- 688041.SH: CNINFO pdf blocked -> SSE/company site fallback
- 300394.SZ: CNINFO identity blocked -> IRM/SZSE/company site fallback

## 施工内容
### Config (3 files)
- alternative_disclosure_sources.json
- known_disclosure_url_catalog.json
- company_ir_page_candidates.json

### Lib (8 files)
- smr_alternative_disclosure_source_registry.py
- smr_disclosure_fallback_route_engine.py
- smr_known_disclosure_url_catalog.py
- smr_irm_interaction_connector.py
- smr_exchange_disclosure_page_connector.py
- smr_company_ir_page_discovery.py
- smr_fallback_text_fetcher.py
- smr_fallback_text_normalizer.py
- smr_fallback_evidence_extractor.py

### Jobs (5 files)
- run_phase71_irm_interaction_fetch.py
- run_phase71_exchange_disclosure_fetch.py
- run_phase71_company_ir_page_discovery.py
- run_phase71_fallback_text_fetch.py
- run_phase71_write_fallback_evidence_memory.py
- run_phase71_alternative_disclosure_fallback.py (runner)

### Reporting (14 files)
All builders for registry, routes, catalog, connectors, text, evidence, gain, matrix, memory, packet, brief, lint, dashboard

### Tests (16 files)
All modules covered.

## 核心约束
- fallback attempt != pass
- management_commentary != confirmed
- mock/fixture=false, raw/OCR=false
- pending/order/trade=0/0/0
- 不输出交易建议
