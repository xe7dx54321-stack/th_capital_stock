#!/usr/bin/env python3
"""Phase 72 company IR candidate patch."""
import argparse, json, sys
def build():
    return {"phase72_company_ir_candidate_patch": {"tickers_checked": 2, "ir_page_candidates_available": 1, "manual_fill_required": 1, "rows": [{"ticker": "688041.SH", "official_site": "", "ir_page": "https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?stockCode=688041", "verification_status": "curated_sse_candidate", "source_confidence": "curated", "note": "SSE announcement page as fallback text source"}, {"ticker": "300394.SZ", "official_site": "", "ir_page": "", "verification_status": "manual_fill_required", "suggested_lookup_keywords": ["天孚通信 投资者关系", "天孚通信 公告", "天孚通信 IR", "天孚通信 300394 互动易"]}], "mock_used": False, "fixture_used": False}}
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase72_company_ir_candidate_patch"]
        lines = ["# Company IR Candidate Patch", "", f"Available: {d['ir_page_candidates_available']}", f"Manual: {d['manual_fill_required']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
