import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase134_ticker_card_builder import build_ticker_cards
from smr_phase134_market_section_builder import build_market_sections
from smr_phase134_research_priority_builder import build_research_priority
from smr_phase134_owner_action_center import build_owner_action_center
from smr_phase134_system_health_snapshot import build_system_health_snapshot
from smr_phase134_console_quality_gate import run_console_quality_gate
def main():
 tc=build_ticker_cards()["phase134_ticker_card_builder"]
 ms=build_market_sections()["phase134_market_section_builder"]
 rp=build_research_priority()["phase134_research_priority_builder"]
 oa=build_owner_action_center()["phase134_owner_action_center"]
 sh=build_system_health_snapshot()["phase134_system_health_snapshot"]
 gq=run_console_quality_gate()["phase134_console_quality_gate"]
 md=[]
 md.append("# Personal Research Console v1")
 md.append("")
 md.append("## System Health")
 md.append(f"- Status: {sh['health']['system_status']}")
 md.append(f"- Quality Gate: {gq['overall']} (violations={gq['violations']})")
 md.append(f"- Mock: {sh['health']['safety_checks']['mock']} | Fixture: {sh['health']['safety_checks']['fixture']}")
 md.append(f"- Pending/Order/Trade: {sh['health']['trade_checks']['pending']}/{sh['health']['trade_checks']['paper_order']}/{sh['health']['trade_checks']['real_trade']}")
 md.append("")
 md.append("## Research Priority")
 md.append("|Rank|Ticker|Market|Reason|Action|")
 md.append("|---|---|---|---|---|")
 for p in rp["priorities"]:
  md.append(f"|{p['rank']}|{p['ticker']}|{p['market']}|{p['reason']}|{p['action']}|")
 md.append("")
 md.append("## Ticker Cards")
 for c in tc["cards"]:
  md.append(f"### {c['ticker']} - {c['name']}")
  md.append(f"- Market: {c['market']} | Sector: {c['sector']} | Currency: {c['currency']}")
  md.append(f"- Coverage: financial={'Y' if c['financial_covered'] else 'N'} valuation={'Y' if c['valuation_covered'] else 'N'}")
  md.append(f"- Watchlist: {c['watchlist_status']}")
  if c.get("blocker"): md.append(f"- Blocker: {c['blocker']}")
  if c.get("coverage_note"): md.append(f"- Note: {c['coverage_note']}")
  md.append("")
 md.append("## Market Sections")
 for mk, mv in ms["sections"].items():
  md.append(f"### {mk} ({mv['currency']})")
  md.append(f"- Tickers: {', '.join(mv['tickers'])} ({mv['count']})")
  md.append(f"- Sectors: {', '.join(mv['sectors'])}")
  md.append("")
 md.append("## Owner Action Center")
 for a in oa["actions"]:
  md.append(f"- [{a['priority']}] {a['action_id']}: {a['action']} ({a['ticker']}, {a['type']})")
 md.append("")
 md.append("---")
 md.append("*Research-only console. No trade recommendations, target prices, or position sizing.*")
 out="\n".join(md)
 if "--json" in sys.argv:
  import json; print(json.dumps({"phase134_console_markdown_report":{"markdown":out,"mock_used":False,"fixture_used":False}},ensure_ascii=False))
 elif "--markdown" in sys.argv:
  print(out)
 else:
  print(out)
if __name__=="__main__":main()
