# Phase 72: Fallback Source Real Text Acquisition & URL Catalog Filling v1

## 日期
2026-05-30

## 背景
Phase 71 完成多源 fallback 架构但 fallback_texts_usable=0。Phase 72 将架构压实到真实取数：URL catalog filling、各 connector real execute hardening、text quality classifier。

## 覆盖标的
- 300308.SZ: baseline regression
- 688041.SH: SSE page candidate registered
- 300394.SZ: IRM + SZSE connectors ready, company IR URL manual

## 施工内容
### Lib (2 files)
- smr_fallback_url_catalog_filling.py
- smr_fallback_text_quality_classifier.py

### Jobs (5 files)
- run_phase72_irm_real_execute.py
- run_phase72_exchange_real_execute.py
- run_phase72_company_ir_real_fetch.py
- run_phase72_known_url_real_fetch.py
- run_phase72_write_fallback_evidence_memory.py
- run_phase72_fallback_real_text_acquisition.py (runner)

### Reporting (15 files)
All builders + brief + lint + dashboard

### Tests (17 files)
All modules covered.

## 核心约束
- fallback attempt != pass
- management_commentary != confirmed
- company_context != strong_direct
- mock/fixture=false, raw/OCR=false
- pending/order/trade=0/0/0
