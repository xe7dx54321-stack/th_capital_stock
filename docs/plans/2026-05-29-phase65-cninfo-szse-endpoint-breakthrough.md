# Phase 65: CNINFO/SZSE Disclosure Endpoint Parameter Breakthrough v1

## 日期
2026-05-29

## 背景
Phase 64 已修复 connector 框架，但 CNINFO API 返回 totalAnnouncement=0，SZSE API 返回 HTTP 500。
Phase 65 专攻参数突破。

## 发现
- 300308.SZ 已有 curated org_id: 9900022016 (smr_cninfo_source_identity.py)
- CNINFO stock 参数可能需要 orgId 而非纯 stock code
- 已建立参数矩阵实验框架（stock/orgId/plate/column/category/headers）

## 文件清单
### 新增 Lib
- smr_cninfo_stock_identity_resolver.py
- smr_cninfo_announcement_query_matrix.py
- smr_cninfo_pdf_url_extractor.py
- smr_szse_endpoint_explorer.py

### 新增 Reporting
- build_phase65_cninfo_stock_identity_resolver.py
- build_phase65_cninfo_announcement_query_matrix.py
- build_phase65_cninfo_metadata_connector_patch_report.py
- build_phase65_cninfo_pdf_url_inventory.py
- build_phase65_cninfo_pdf_text_validation_report.py
- build_phase65_szse_endpoint_explorer.py
- build_phase65_disclosure_metadata_breakthrough_dashboard.py
- build_phase65_business_evidence_rerun_after_metadata_breakthrough.py

### 新增 Jobs
- run_phase65_cninfo_pdf_text_validation.py
- run_phase65_disclosure_endpoint_breakthrough.py

### 新增 Tests (9 个)
- test_phase65_cninfo_stock_identity_resolver.py
- test_phase65_cninfo_announcement_query_matrix.py
- test_phase65_cninfo_metadata_connector_patch.py
- test_phase65_cninfo_pdf_url_extractor.py
- test_phase65_cninfo_pdf_text_validation.py
- test_phase65_szse_endpoint_explorer.py
- test_phase65_disclosure_metadata_breakthrough_dashboard.py
- test_phase65_business_evidence_rerun_after_metadata_breakthrough.py
- test_phase65_runner.py
