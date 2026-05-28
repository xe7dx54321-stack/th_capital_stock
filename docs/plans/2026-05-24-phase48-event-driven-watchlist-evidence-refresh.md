# Phase 48 Event-driven Watchlist Evidence Refresh v1 Implementation Plan

**Goal:** Add event-driven refresh capability. When new events (IR records, earnings, announcements, etc.)
trigger, the system auto-detects them, generates refresh tasks, executes research-only evidence refresh,
and revalidates thesis strength.

**Architecture:** Phase 48 adds event trigger schema, detector, refresh task generation, executor,
tracking variable refresh, revalidation validator, thesis update, audit, packet, and dashboard.

**Tech Stack:** Python 3.11, SQLite, 08_scripts/lib|jobs|reporting|verification, unittest.

### Task 1: Event Trigger Schema
- 08_scripts/lib/smr_watchlist_event_trigger.py
- 08_scripts/reporting/build_phase48_event_trigger_schema.py
- 15 event types; always_forbidden_actions = [create_pending, create_paper_order, create_trade]

### Task 2: Event Trigger Detector
- 08_scripts/lib/smr_watchlist_event_detector.py
- 08_scripts/reporting/build_phase48_event_trigger_detector.py
- Detects from sample fixtures + existing watchlist state

### Task 3: Event Refresh Tasks
- 08_scripts/lib/smr_event_driven_refresh_task.py
- 08_scripts/reporting/build_phase48_event_refresh_tasks.py
- Maps events to REFRESH_TRACKING_VARIABLE, REVALIDATE_THESIS, etc.

### Task 4: Event Evidence Refresh Executor
- 08_scripts/jobs/run_phase48_event_evidence_refresh.py
- dry-run / execute modes with audit writing

### Task 5: Tracking Variable Refresh
- 08_scripts/lib/smr_event_tracking_variable_refresh.py
- 08_scripts/reporting/build_phase48_tracking_variable_refresh.py

### Task 6: Event-driven Revalidation
- 08_scripts/verification/validate_phase48_event_driven_revalidation.py

### Task 7: Event Thesis Strength Update
- 08_scripts/reporting/build_phase48_event_thesis_strength_update.py

### Task 8: Event Trigger Audit
- 08_scripts/lib/smr_event_trigger_audit.py
- 08_scripts/reporting/build_phase48_event_trigger_audit.py

### Task 9: Event Revalidation Packet
- 08_scripts/reporting/build_phase48_event_revalidation_packet.py

### Task 10: Event Watchlist Dashboard
- 08_scripts/reporting/build_phase48_event_watchlist_dashboard.py

### Task 11: Windows Unicode-safe Output Fix
- 08_scripts/lib/smr_safe_output.py
- safe_print / safe_print_json with UnicodeEncodeError fallback

### Guardrails
- event trigger != pending; new evidence != order; thesis strengthened != buy
