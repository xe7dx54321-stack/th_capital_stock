# Phase 64: A-share Disclosure Source Connector Repair v1

## 日期
2026-05-29

## 背景
Phase 63b 真实网络验证结果显示：
- CNINFO metadata API 超时 / disclosure page HTTP 500
- SZSE 主页可达但 API endpoint 返回 HTTP 500
- IRM 返回 HTML 非 JSON
- 真实业务证据增量为 0

Phase 64 的任务是修复这些披露源连接器。

## 发现
1. CNINFO 使用 HTTPS（非 HTTP）可以连接，hisAnnouncement/query 返回 JSON 但 totalAnnouncement = 0
2. SZSE 披露 API (annList) 在 GET/POST_JSON/POST_FORM 下全部返回 HTTP 500
3. IRM 问答 GET 返回 HTML，可通过 HTML parsing 提取 QA

## 文件清单
### 新增
- config/a_share_disclosure_source_endpoints.json
- 08_scripts/lib/smr_a_share_disclosure_endpoint_registry.py
- 08_scripts/lib/smr_cninfo_endpoint_diagnostics.py
- 08_scripts/lib/smr_szse_disclosure_connector.py
- 08_scripts/lib/smr_irm_interactive_qa_connector.py
- 08_scripts/lib/smr_disclosure_source_fallback_router.py
- 08_scripts/lib/smr_small_controlled_source_fetch.py
- 08_scripts/reporting/build_phase64_disclosure_endpoint_registry.py
- 08_scripts/reporting/build_phase64_cninfo_endpoint_diagnostics.py
- 08_scripts/reporting/build_phase64_szse_disclosure_inventory.py
- 08_scripts/reporting/build_phase64_irm_qa_inventory.py
- 08_scripts/reporting/build_phase64_disclosure_source_fallback_router.py
- 08_scripts/reporting/build_phase64_connector_health_dashboard.py
- 08_scripts/reporting/build_phase64_small_controlled_source_fetch_report.py
- 08_scripts/reporting/build_phase64_business_evidence_rerun_after_connector_repair.py
- 08_scripts/jobs/run_phase64_szse_disclosure_fetch.py
- 08_scripts/jobs/run_phase64_irm_qa_fetch.py
- 08_scripts/jobs/run_phase64_small_controlled_source_fetch.py
- 08_scripts/jobs/run_phase64_disclosure_connector_repair.py
- 09_runbooks/smr-research-upgrade-progress.md
- tests/test_phase64_disclosure_endpoint_registry.py
- tests/test_phase64_cninfo_endpoint_diagnostics.py
- tests/test_phase64_szse_disclosure_connector.py
- tests/test_phase64_irm_qa_connector.py
- tests/test_phase64_disclosure_source_fallback_router.py
- tests/test_phase64_connector_health_dashboard.py
- tests/test_phase64_small_controlled_source_fetch.py
- tests/test_phase64_business_evidence_rerun_after_connector_repair.py
- tests/test_phase64_runner.py
- tests/test_phase64_dashboard.py
