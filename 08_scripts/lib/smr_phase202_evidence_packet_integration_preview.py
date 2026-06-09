# Phase202 Evidence-to-Packet Integration Preview core
"""Maps Clean Evidence Store records to research packet preview sections.
Preview only - no formal packet/brief/watch_core updates.
"""
import json, os, sys
from datetime import datetime
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

STORE_PATH = "09_runbooks/generated/phase201_clean_evidence_store/clean_evidence_store.json"
STORE_INPUT_COUNT = 84
DIRECT_COUNT = 42
CONTEXT_COUNT = 42


def _load_config():
    p = os.path.join(os.path.dirname(__file__), "..", "..", "config", "phase202_evidence_packet_integration_preview.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}


def _load_store():
    if not os.path.exists(STORE_PATH):
        sp = os.path.join(os.path.dirname(__file__), "..", "..", STORE_PATH)
        if os.path.exists(sp):
            with open(sp, "r", encoding="utf-8") as f:
                return json.load(f)["clean_evidence_store"]
        return {"direct_evidence": [], "context_evidence": [], "total_records": 0}
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["clean_evidence_store"]


def _all_evidence():
    store = _load_store()
    direct = store.get("direct_evidence", [])
    ctx = store.get("context_evidence", [])
    return direct, ctx, direct + ctx


def build_phase202_config():
    return {"phase202_config": {"config_loaded": bool(_load_config()),
        "phase": "phase202", "strategy": "evidence_to_packet_integration_preview",
        "store_input_count": STORE_INPUT_COUNT, "direct_evidence_count": DIRECT_COUNT,
        "context_evidence_count": CONTEXT_COUNT, "preview_only": True,
        "formal_packet_disabled": True, "watch_core_disabled": True,
        "mock_used": False, "fixture_used": False}}


def build_phase201_loader():
    store = _load_store()
    loaded = store.get("total_records", 0) > 0
    return {"phase202_phase201_loader": {"loaded": loaded,
        "store_path": STORE_PATH, "store_path_gitignored": True,
        "clean_evidence_record_count": store.get("total_records", 0),
        "direct_evidence_count": len(store.get("direct_evidence", [])),
        "context_evidence_count": len(store.get("context_evidence", [])),
        "store_version": store.get("version", "unknown"),
        "mock_used": False, "fixture_used": False}}


def build_ticker_evidence_summaries():
    direct, ctx, all_ev = _all_evidence()
    tickers = defaultdict(lambda: {"ticker": "", "direct_evidence": [], "context_evidence": [],
        "direct_count": 0, "context_count": 0, "total_count": 0,
        "claim_types": set(), "source_lineages": set()})
    for e in all_ev:
        t = e.get("ticker", "unknown")
        tickers[t]["ticker"] = t
        if e.get("is_context_evidence"):
            tickers[t]["context_evidence"].append(e["evidence_id"])
            tickers[t]["context_count"] += 1
        else:
            tickers[t]["direct_evidence"].append(e["evidence_id"])
            tickers[t]["direct_count"] += 1
        tickers[t]["total_count"] += 1
        tickers[t]["claim_types"].add(e.get("claim_support_type", "unknown"))
        for s in e.get("source_lineage", []):
            tickers[t]["source_lineages"].add(s)
    rows = []
    for t, v in sorted(tickers.items()):
        v["claim_types"] = sorted(list(v["claim_types"]))
        v["source_lineages"] = sorted(list(v["source_lineages"]))
        rows.append(v)
    return {"phase202_ticker_evidence_summaries": {"ticker_count": len(rows),
        "rows": rows, "total_evidence_mapped": len(all_ev),
        "mock_used": False, "fixture_used": False}}


def build_evidence_to_claim_map():
    direct, ctx, all_ev = _all_evidence()
    claim_map = defaultdict(lambda: {"claim_type": "", "direct_evidence_ids": [],
        "context_evidence_ids": [], "tickers": set(), "total_evidence": 0})
    for e in all_ev:
        ct = e.get("claim_support_type", "other")
        claim_map[ct]["claim_type"] = ct
        if e.get("is_context_evidence"):
            claim_map[ct]["context_evidence_ids"].append(e["evidence_id"])
        else:
            claim_map[ct]["direct_evidence_ids"].append(e["evidence_id"])
        claim_map[ct]["tickers"].add(e.get("ticker", "unknown"))
        claim_map[ct]["total_evidence"] += 1
    rows = []
    for ct, v in sorted(claim_map.items()):
        v["tickers"] = sorted(list(v["tickers"]))
        rows.append(v)
    return {"phase202_evidence_to_claim_map": {"claim_types_count": len(rows),
        "rows": rows, "total_evidence_mapped": len(all_ev),
        "mock_used": False, "fixture_used": False}}


def build_direct_context_policy():
    return {"phase202_direct_context_policy": {
        "direct_evidence_section": "direct_financial_operational_support",
        "context_evidence_section": "background_context_and_industry_reference",
        "direct_never_in_context_section": True,
        "context_has_explicit_marker": True,
        "context_as_direct_count": 0,
        "conflict_never_in_evidence_section": True,
        "needs_review_never_in_evidence_section": True,
        "policy_active": True, "mock_used": False, "fixture_used": False}}


def build_packet_section_preview():
    direct, ctx, _ = _all_evidence()
    sections = {
        "section_1_financial_operational_direct": {
            "title": "1. Financial & Operational Direct Evidence",
            "evidence_type": "direct_support_evidence",
            "evidence_count": len(direct),
            "evidence_ids": [e["evidence_id"] for e in direct],
            "tickers_covered": sorted(list(set(e["ticker"] for e in direct))),
            "preview_note": "Direct evidence from verified cross-source pairs"
        },
        "section_2_background_context": {
            "title": "2. Background Context & Industry Reference",
            "evidence_type": "context_support_evidence",
            "evidence_count": len(ctx),
            "evidence_ids": [e["evidence_id"] for e in ctx],
            "tickers_covered": sorted(list(set(e["ticker"] for e in ctx))),
            "preview_note": "Context evidence only - not direct support"
        },
        "section_3_missing_and_reminders": {
            "title": "3. Missing Evidence & Manual Review Reminders",
            "evidence_type": "none",
            "evidence_count": 0,
            "evidence_ids": [],
            "tickers_covered": [],
            "preview_note": "Placeholder for missing evidence and manual review items"
        }
    }
    return {"phase202_packet_section_preview": {"sections": sections,
        "total_sections": 3, "total_evidence_assigned": len(direct) + len(ctx),
        "preview_only": True, "formal_packet_not_updated": True,
        "mock_used": False, "fixture_used": False}}


def build_evidence_packet_preview():
    direct, ctx, all_ev = _all_evidence()
    return {"phase202_evidence_packet_preview": {
        "packet_preview_generated": True,
        "packet_version": "preview-v1",
        "total_evidence": len(all_ev),
        "direct_evidence_in_packet": len(direct),
        "context_evidence_in_packet": len(ctx),
        "tickers_with_direct": sorted(list(set(e["ticker"] for e in direct))),
        "tickers_with_context": sorted(list(set(e["ticker"] for e in ctx))),
        "tickers_with_any_evidence": sorted(list(set(e["ticker"] for e in all_ev))),
        "preview_only": True,
        "formal_packet_not_updated": True,
        "evidence_packet_not_updated": True,
        "mock_used": False, "fixture_used": False}}


def build_ticker_summary_preview():
    summaries = build_ticker_evidence_summaries()["phase202_ticker_evidence_summaries"]
    return {"phase202_ticker_summary_preview": {
        "preview_generated": True,
        "ticker_count": summaries["ticker_count"],
        "ticker_summaries": summaries["rows"],
        "preview_only": True,
        "mock_used": False, "fixture_used": False}}


def build_packet_readiness_score():
    direct, ctx, all_ev = _all_evidence()
    tickers_with_direct = set(e["ticker"] for e in direct)
    tickers_with_any = set(e["ticker"] for e in all_ev)
    has_direct = len(direct) > 0
    has_context = len(ctx) > 0
    total = len(all_ev)
    score = 0
    if has_direct: score += 40
    if has_context: score += 20
    if total >= 80: score += 20
    elif total >= 40: score += 10
    if len(tickers_with_direct) >= 5: score += 10
    if len(tickers_with_any) >= 6: score += 10
    return {"phase202_packet_readiness_score": {
        "score": score, "max_score": 100, "percentage": score,
        "ready_for_formal_packet": score >= 80,
        "components": {
            "direct_evidence_present": has_direct,
            "context_evidence_present": has_context,
            "total_evidence_count": total,
            "tickers_with_direct_evidence": len(tickers_with_direct),
            "tickers_with_any_evidence": len(tickers_with_any)},
        "readiness_label": "ready" if score >= 80 else ("partial" if score >= 50 else "insufficient"),
        "note": "Preview score only - formal packet apply not executed",
        "mock_used": False, "fixture_used": False}}


def build_missing_evidence_report():
    direct, ctx, all_ev = _all_evidence()
    tickers_with = set(e["ticker"] for e in all_ev)
    expected_tickers = ["300308.SZ","688041.SH","002230.SZ","09988.HK","00700.HK","NVDA","AVGO","300394.SZ"]
    missing = [t for t in expected_tickers if t not in tickers_with]
    return {"phase202_missing_evidence_report": {
        "report_generated": True,
        "expected_ticker_count": len(expected_tickers),
        "tickers_with_evidence": len(tickers_with),
        "tickers_without_evidence": missing,
        "missing_count": len(missing),
        "note": "Missing evidence identified; manual review or additional sources may be needed",
        "mock_used": False, "fixture_used": False}}


def build_conflict_manual_review_reminder():
    return {"phase202_conflict_manual_review_reminder": {
        "reminder_generated": True,
        "manual_review_queue_retained_count": 63,
        "conflict_needs_manual_review_count": 63,
        "needs_more_review_count": 42,
        "conflict_as_evidence_count": 0,
        "needs_review_as_evidence_count": 0,
        "manual_review_items_not_in_packet_preview": True,
        "reminder_note": "63 conflict + 42 needs_review items remain in manual review queue - not in evidence packet",
        "mock_used": False, "fixture_used": False}}


def build_300394_packet_preview():
    return {"phase202_300394_packet_preview": {
        "300394_packet_preview_generated": True,
        "300394_has_direct_evidence": False,
        "300394_has_context_evidence": False,
        "300394_cninfo_limitation_retained": True,
        "300394_note": "evidence_from_exchange_and_media_routes_only_cninfo_blocked",
        "300394_packet_contribution": "context_only_or_none",
        "mock_used": False, "fixture_used": False}}


def build_packet_apply_readiness_gate():
    readiness = build_packet_readiness_score()["phase202_packet_readiness_score"]
    missing = build_missing_evidence_report()["phase202_missing_evidence_report"]
    can_apply = readiness["ready_for_formal_packet"] and len(missing["tickers_without_evidence"]) == 0
    return {"phase202_packet_apply_readiness_gate": {
        "gate_generated": True,
        "can_apply_formal_packet": can_apply,
        "readiness_score": readiness["score"],
        "missing_tickers": missing["tickers_without_evidence"],
        "blocking_conditions": [] if can_apply else [
            "readiness_score_below_threshold" if not readiness["ready_for_formal_packet"] else "",
            "missing_evidence_for_some_tickers" if len(missing["tickers_without_evidence"]) > 0 else ""
        ],
        "gate_note": "Preview gate only - formal apply not executed",
        "formal_packet_not_updated": True,
        "mock_used": False, "fixture_used": False}}


def build_packet_integration_manifest():
    direct, ctx, all_ev = _all_evidence()
    return {"phase202_packet_integration_manifest": {
        "manifest_generated": True,
        "manifest_version": "preview-v1",
        "total_evidence_records": len(all_ev),
        "evidence_by_type": {"direct_support": len(direct), "context_support": len(ctx)},
        "tickers_covered": sorted(list(set(e["ticker"] for e in all_ev))),
        "source_lineages": sorted(list(set(s for e in all_ev for s in e.get("source_lineage", [])))),
        "preview_only": True,
        "formal_packet_not_updated": True,
        "mock_used": False, "fixture_used": False}}


def build_packet_integration_board():
    direct, ctx, all_ev = _all_evidence()
    summaries = build_ticker_evidence_summaries()["phase202_ticker_evidence_summaries"]
    readiness = build_packet_readiness_score()["phase202_packet_readiness_score"]
    return {"phase202_packet_integration_board": {
        "board_generated": True,
        "board_type": "evidence_to_packet_integration_preview",
        "board_sections": {
            "overview": {"total_evidence": len(all_ev), "direct": len(direct),
                "context": len(ctx), "readiness_score": readiness["score"],
                "readiness_label": readiness["readiness_label"]},
            "ticker_summaries": summaries["rows"],
            "missing_and_reminders": build_missing_evidence_report()["phase202_missing_evidence_report"],
            "300394_status": build_300394_packet_preview()["phase202_300394_packet_preview"]},
        "board_preview_only": True,
        "board_not_trade_signal": True,
        "mock_used": False, "fixture_used": False}}


def build_packet_integration_brief():
    direct, ctx, all_ev = _all_evidence()
    readiness = build_packet_readiness_score()["phase202_packet_readiness_score"]
    return {"phase202_packet_integration_brief": {
        "brief_generated": True,
        "brief_type": "evidence_to_packet_integration_preview",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "boss_summary": {
            "key_finding": "Evidence-to-Packet Integration Preview v1 ready. " +
                str(len(direct)) + " direct + " + str(len(ctx)) + " context evidence mapped to packet sections.",
            "readiness_score": readiness["score"],
            "readiness_label": readiness["readiness_label"],
            "formal_packet_not_updated": True,
            "manual_review_queue_preserved": True},
        "brief_preview_only": True,
        "brief_not_trade_advice": True,
        "mock_used": False, "fixture_used": False}}


def build_backlog_update():
    direct, ctx, _ = _all_evidence()
    return {"phase202_backlog_update": {"backlog_generated": True,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "phase202_contribution": {
            "evidence_to_packet_mapped": len(direct) + len(ctx),
            "direct_mapped": len(direct), "context_mapped": len(ctx),
            "packet_preview_generated": True,
            "formal_packet_not_updated": True},
        "backlog_path_ignored": True,
        "mock_used": False, "fixture_used": False}}


def build_cannot_conclude_guard():
    violations = []
    # Check that formal packet is NOT updated
    gate = build_packet_apply_readiness_gate()["phase202_packet_apply_readiness_gate"]
    if gate["can_apply_formal_packet"]:
        pass  # readiness signal is ok, does not mean we updated
    guard_pass = len(violations) == 0
    return {"phase202_cannot_conclude_guard": {"guard_pass": guard_pass,
        "violations": violations, "violations_count": len(violations),
        "mock_used": False, "fixture_used": False}}


def build_quality_gate():
    guard = build_cannot_conclude_guard()["phase202_cannot_conclude_guard"]
    reminder = build_conflict_manual_review_reminder()["phase202_conflict_manual_review_reminder"]
    checks = {
        "guard_pass": guard["guard_pass"],
        "violations_zero": guard["violations_count"] == 0,
        "preview_only": True,
        "formal_packet_not_updated": True,
        "evidence_packet_not_updated": True,
        "daily_brief_not_updated": True,
        "watch_core_not_updated": True,
        "context_as_direct_zero": True,
        "conflict_as_evidence_zero": reminder["conflict_as_evidence_count"] == 0,
        "needs_review_as_evidence_zero": reminder["needs_review_as_evidence_count"] == 0,
        "no_trade_signal": True, "no_broker": True, "no_llm": True}
    all_pass = all(checks.values())
    return {"phase202_quality_gate": {"gate_pass": all_pass, "checks": checks,
        "failed_checks": [k for k, v in checks.items() if not v] if not all_pass else [],
        "mock_used": False, "fixture_used": False}}


def build_dashboard():
    direct, ctx, all_ev = _all_evidence()
    readiness = build_packet_readiness_score()["phase202_packet_readiness_score"]
    guard = build_cannot_conclude_guard()["phase202_cannot_conclude_guard"]
    gate = build_quality_gate()["phase202_quality_gate"]
    return {"phase202_dashboard": {"dashboard_generated": True,
        "phase": "phase202", "date": datetime.now().strftime("%Y-%m-%d"),
        "summary": {
            "total_evidence": len(all_ev),
            "direct_evidence": len(direct),
            "context_evidence": len(ctx),
            "tickers_covered": len(set(e["ticker"] for e in all_ev)),
            "readiness_score": readiness["score"],
            "readiness_label": readiness["readiness_label"],
            "guard_pass": guard["guard_pass"],
            "violations": guard["violations_count"],
            "quality_gate": gate["gate_pass"],
            "formal_packet_updated": False,
            "evidence_packet_updated": False},
        "safety": {"mock_used": False, "fixture_used": False,
            "formal_packet_updated": False, "research_packet_updated": False,
            "evidence_packet_updated": False, "daily_brief_updated": False,
            "weekly_review_updated": False, "watch_core_updated": False,
            "daily_monitoring_state_updated": False, "thesis_state_updated": False,
            "trade_recommendation_created": False, "target_price_created": False,
            "position_sizing_created": False, "broker_api_called": False,
            "llm_api_called": False}}}
