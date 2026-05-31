import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
from smr_phase92_order_text_collector import collect_order_texts
from smr_phase92_order_signal_classifier import classify_order_signals
from smr_phase92_order_evidence_extraction import extract_order_evidence
from smr_phase92_order_quality_gate import run_quality_gate
from smr_phase92_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
from smr_phase92_gap_closeout import build_gap_closeout
from smr_phase92_backlog_update import build_backlog_update
from smr_phase92_order_source_registry import build_order_source_registry
from smr_phase92_ticker_entity_resolver import build_ticker_entity_resolver

def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    
    registry=build_order_source_registry()
    entities=build_ticker_entity_resolver()
    exp=explore_order_sources(mode)
    texts=collect_order_texts(exp)
    sigs=classify_order_signals(texts)
    ev=extract_order_evidence(sigs)
    gate=run_quality_gate(ev)
    guard=run_cannot_conclude_guard(ev,gate)
    matrix=build_order_coverage_matrix(exp)
    closeout=build_gap_closeout(matrix,exp)
    backlog=build_backlog_update()
    
    reg=registry["phase92_order_source_registry"]
    ent=entities["phase92_ticker_entity_resolver"]
    ex=exp["phase92_order_source_exploration"]
    mx=matrix["phase92_order_source_coverage_matrix"]
    ga=gate["phase92_order_quality_gate"]["gate_summary"]
    gu=guard["phase92_cannot_conclude_guard"]
    cl=closeout["phase92_order_hard_data_gap_closeout"]
    bl=backlog["phase92_backlog_update"]
    
    summary={
        "order_sources_registered":reg["order_sources_registered"],
        "tickers_resolved":ent["tickers_resolved"],
        "sources_attempted":ex["sources_attempted"],
        "text_units_collected":ex["text_units_collected"],
        "order_keyword_hits":ex["order_keyword_hits"],
        "order_text_found":mx["order_text_found"],
        "blocked_tickers":mx["blocked"],
        "no_order_text":mx["no_order_text_found"],
        "quality_gate_passed":ga["passed"],
        "quality_gate_review":ga["review_required"],
        "quality_gate_rejected":ga["rejected"],
        "guard_status":gu["overall_status"],
        "gap_fully_closed":cl["fully_closed"],
        "gap_partially_addressed":cl["partially_addressed"],
        "phase93_recommendation":bl["phase93_recommendation"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price_created":0,"position_sizing_created":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        print(f"# Phase 92 Order Hard Source Dashboard\n")
        print(f"- Sources registered: {summary['order_sources_registered']}")
        print(f"- Sources attempted: {summary['sources_attempted']}")
        print(f"- Text units: {summary['text_units_collected']}, Keyword hits: {summary['order_keyword_hits']}")
        print(f"- Order text found: {summary['order_text_found']}/8, Blocked: {summary['blocked_tickers']}")
        print(f"- Quality gate: {summary['quality_gate_passed']} passed, {summary['quality_gate_review']} review, {summary['quality_gate_rejected']} rejected")
        print(f"- Guard: {summary['guard_status']}")
        print(f"- Gap: {summary['gap_fully_closed']} closed, {summary['gap_partially_addressed']} partial")
        print(f"- Phase93: {summary['phase93_recommendation']}")
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
