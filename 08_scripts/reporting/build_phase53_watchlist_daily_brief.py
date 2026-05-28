#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_executive_brief_builder import build_executive
from smr_analyst_detail_brief_builder import build_analyst_detail
from smr_brief_forbidden_phrase_checker import build_report as fp_report
from smr_brief_style_lint import build_lint
def build(conn,ticker):
    eb=build_executive(ticker); ad=build_analyst_detail(ticker)
    parts={"executive":eb,"analyst":ad}
    fp=fp_report(parts,ticker); lint=build_lint(json.dumps(eb,ensure_ascii=False))
    return {"ticker":ticker,"watchlist_daily_brief":{"brief_type":"internal_watchlist_tracking_brief","executive_brief":eb.get("executive_brief",{}),"analyst_detail":ad.get("analyst_detail",{}),"style_lint":lint.get("brief_style_lint",{}),"forbidden_phrase_report":fp.get("forbidden_phrase_report",{}),"boundary":{"pending_created":0,"paper_order_created":0,"real_trade_created":0,"promotion_allowed_true":0}}}
def _md(p):
    db=p.get("watchlist_daily_brief",{})
    eb=db.get("executive_brief",{})
    ad=db.get("analyst_detail",{})
    from build_phase53_executive_brief import _md as eb_md
    from build_phase53_analyst_detail_brief import _md as ad_md
    eb_part=eb_md({"ticker":p["ticker"],"executive_brief":eb})
    ad_part=ad_md({"analyst_detail":ad})
    boundary=["\n## 边界","- 本简报仅用于 watchlist tracking。","- 不构成买卖建议。","- 当前不进入 pending，不生成 order，不触发 trade。"]
    return eb_part+"\n"+ad_part+"\n"+"\n".join(boundary)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    r=build(None,args.ticker)
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
