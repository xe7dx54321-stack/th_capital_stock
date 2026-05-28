# Phase 49 Real Source Event Monitor Pilot v1

**Goal:** Move watchlist event triggers from sample events to real CNINFO/IR/filing metadata monitoring.

### Tasks
1. Real Source Monitor Schema
2. CNINFO Source Metadata Connector
3. Real Source Event Classifier
4. Metadata-to-Watchlist Event Adapter
5. Event Deduplication
6. Real Source Event Refresh Integration
7. Real Source Monitor Audit
8. Real Source Event Dashboard
9. Safe Output Full Wiring

### New Files
- lib/: smr_real_source_monitor_schema.py, smr_cninfo_source_metadata_connector.py, smr_real_source_event_classifier.py, smr_metadata_to_watchlist_event_adapter.py, smr_real_source_event_dedup.py, smr_real_source_monitor_audit.py
- reporting/: build_phase49_*.py (6 files)
- jobs/: run_phase49_*.py (2 files)
- verification/: validate_phase49_*.py (1 file)
- tests/: test_phase49_*.py (9 files)
- Modified: validate_phase6_multi_ticker_live.py, validate_phase14_thesis_aware_multi_ticker_live.py (safe output wiring)
