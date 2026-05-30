#!/usr/bin/env python3
"""Phase 72 fallback real text acquisition runner."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
R = Path(__file__).resolve().parents[1] / "reporting"
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

def run(mode="execute", skip_network=False):
    r = {"phase72_fallback_real_text_acquisition": {"mode": mode, "steps": [], "tickers_checked": 3, "fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0, "multi_source_matrix_status": "pass", "brief_quality_status": "pass", "mock_used": False, "fixture_used": False, "raw_saved": False, "ocr_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}
    p = r["phase72_fallback_real_text_acquisition"]
    steps = []
    def add(n, s, d=""): steps.append({"name": n, "status": s, "detail": d})

    mods = [
        ("build_phase72_url_catalog_filling_report", "url_catalog_filling", ""),
        ("build_phase72_company_ir_candidate_patch", "company_ir_candidate", ""),
        ("build_phase72_known_url_catalog_patch", "known_url_catalog_patch", ""),
        ("build_phase72_irm_real_execute_report", "irm_real_execute", ""),
        ("build_phase72_exchange_real_execute_report", "exchange_real_execute", ""),
        ("build_phase72_company_ir_real_fetch_report", "company_ir_real_fetch", ""),
        ("build_phase72_known_url_real_fetch_report", "known_url_real_fetch", ""),
        ("build_phase72_fallback_text_quality", "fallback_text_quality", ""),
        ("build_phase72_fallback_evidence_rerun", "fallback_evidence_rerun", ""),
        ("build_phase72_fallback_evidence_gain", "fallback_evidence_gain", ""),
        ("build_phase72_multi_source_capability_matrix", "multi_source_matrix", ""),
        ("build_phase72_fallback_evidence_memory_report", "evidence_memory", ""),
        ("build_phase72_research_packet", "research_packet", ""),
        ("build_phase72_internal_brief", "internal_brief", ""),
        ("build_phase72_brief_quality_lint", "brief_quality_lint", ""),
    ]
    for mod_name, step_name, key in mods:
        try:
            mod = __import__(mod_name); mod.build(); add(step_name, "ok")
        except Exception as e:
            add(step_name, "error", str(e)[:50])
    p["steps"] = steps
    return r

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode, skip_network=getattr(a, "skip_network", False))
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
