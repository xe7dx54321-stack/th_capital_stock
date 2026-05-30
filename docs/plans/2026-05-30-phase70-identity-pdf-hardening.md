# Phase 70: Ticker Identity & PDF Extraction Hardening v1

## 日期
2026-05-30

## 背景
Phase 69b 暴露了两个硬卡点：
1. 688041.SH PDF text 仍为 0
2. 300394.SZ CNINFO identity 仍未找到

Phase 70 专门修复这两个卡点。

## 覆盖标的
- 300308.SZ: baseline regression
- 688041.SH: PDF URL 诊断 + PDF download/text hardening
- 300394.SZ: org_id discovery（扩展至9个备选）+ curated identity patch

## 施工内容
### Lib (2 files)
- smr_phase70_pdf_url_diagnostics.py
- smr_phase70_cninfo_orgid_discovery.py

### Jobs (5 files)
- run_phase70_688041_pdf_download_hardening.py
- run_phase70_688041_pdf_text_extraction_hardening.py
- run_phase70_300394_real_execute.py
- run_phase70_write_evidence_memory_update.py
- run_phase70_identity_and_pdf_hardening.py (runner)

### Reporting (10 files)
- 688041 PDF URL diagnostics / download hardening / text extraction reports
- 688041 generic_hard_tech evidence rerun
- 300394 orgid discovery / curated identity patch / real execute
- real capability matrix / evidence memory / research packet / internal brief / quality lint / dashboard

### Tests (14 files)
All modules covered with proper assertions.

## 核心约束
- no_pass_without_execute=true
- mock/fixture=false, raw/OCR=false
- pending/order/trade=0/0/0
- 不复用其他 ticker org_id
- 不硬套 AI 光模块变量
- 不输出交易建议
