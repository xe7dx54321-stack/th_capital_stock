# Phase174 post-apply board
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase174_coverage_state_registry import build_coverage_state_registry
from smr_phase174_coverage_state_loader import load_coverage_state
from smr_phase174_coverage_cards import build_coverage_cards
from smr_phase174_guard import build_phase174_guard, build_phase174_quality_gate, build_phase174_cannot_conclude_guard

def build_post_apply_board():
    state = load_coverage_state()
    cards = build_coverage_cards()
    guard = build_phase174_guard()
    qg = build_phase174_quality_gate()
    cc = build_phase174_cannot_conclude_guard()

    sections = {"formal_research_coverage":[],"candidate_pending":[],"deferred_review":[],"rejected":[]}
    for card in cards["phase174_coverage_cards"]["cards"]:
        tier = card["coverage_tier"]
        if tier in sections:
            sections[tier].append(card)

    return {"phase174_post_apply_board":{
        "tickers_total":state["phase174_coverage_state_loader"]["coverage_state_count"],
        "sections":{
            "formal_research_coverage":len(sections["formal_research_coverage"]),
            "candidate_pending":len(sections["candidate_pending"]),
            "deferred_review":len(sections["deferred_review"]),
            "rejected":len(sections["rejected"])
        },
        "rows":cards["phase174_coverage_cards"]["cards"],
        "board_not_trade_signal":True,
        "guard":guard["phase174_guard"]["status"],
        "quality_gate":qg["phase174_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase174_cannot_conclude_guard"]["status"],
        "violations":qg["phase174_quality_gate"]["violations"],
        "watch_core_updated":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    args = p.parse_args()
    print(json.dumps(build_post_apply_board(),ensure_ascii=False,indent=2))
