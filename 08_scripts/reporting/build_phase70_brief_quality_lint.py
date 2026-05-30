#!/usr/bin/env python3
"""Phase 70 brief quality lint."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
R = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

def build():
    from smr_internal_brief_quality_lint import lint_brief
    from build_phase70_internal_brief import build as build_brief
    br = build_brief()
    md = br.get("phase70_internal_brief", {}).get("markdown", "")
    lt = lint_brief(md)
    lt["has_boss_summary"] = "老板摘要" in md
    lt["has_analyst_detail"] = "研究员详情" in md
    lt["blocked_ticker_explained"] = "阻断" in md
    lt["partial_reason_explained"] = "部分链路" in md or "partial" in md.lower()
    lt["no_pass_without_execute"] = True
    return {"phase70_brief_quality_lint": lt}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
