def build_markdown_brief():
 from datetime import datetime
 from smr_phase122_ticker_cards import build_ticker_cards
 from smr_phase122_opportunity_section import build_opportunity_section
 from smr_phase122_risk_gap_section import build_risk_gap_section
 from smr_phase122_owner_actions import build_owner_actions
 from smr_phase122_evidence_digest import build_evidence_digest
 cards=build_ticker_cards()
 opp=build_opportunity_section()
 risk=build_risk_gap_section()
 owner=build_owner_actions()
 ev=build_evidence_digest()
 today=datetime.now().strftime("%Y-%m-%d")
 L=[]
 L.append("# Daily Research Brief")
 L.append("## "+today)
 L.append("")
 L.append("## Today's Observations")
 L.append("### Top Changes")
 signals=[c for c in cards["phase122_ticker_cards"]["cards"] if c["signal"]=="strengthened"]
 for s in signals:
  L.append("- "+s["ticker"]+" ("+s["market"]+"): "+s["top_metric"]+" strengthened")
 L.append("")
 L.append("### Multi-Source Evidence Digest")
 for r in ev["phase122_evidence_digest"]["rows"]:
  cnt=len(r.get("tickers",[])) or r.get("sources_pending","N/A")
  tag=" [not yet verified]" if r["status"]=="partially_integrated" else ""
  L.append("- "+r["source_type"]+": "+r["status"]+" ("+str(cnt)+")"+tag)
 L.append("")
 L.append("## Ticker Research Cards")
 for c in cards["phase122_ticker_cards"]["cards"]:
  L.append("### "+c["ticker"]+" ("+c["market"]+")")
  L.append("- Signal: "+c["signal"])
  L.append("- Top: "+c["top_metric"]+" ("+c["currency"]+")")
  L.append("- Sources: "+str(c["sources"])+" (risk level: "+c["source_risk"]+")")
  if c.get("partial"): L.append("- NOTE: "+c["partial"]+" partial")
  L.append("")
 L.append("## Opportunity & Catalyst")
 for cat in opp["phase122_opportunity"]["active_catalysts"]: L.append("- ACTIVE: "+cat)
 for mon in opp["phase122_opportunity"]["monitoring"]: L.append("- Monitor: "+mon)
 L.append("")
 L.append("## Risk, Gaps & Unverified Sources")
 for r in risk["phase122_risk_gap"]["risks"]:
  L.append("- ["+r["severity"]+"] "+r["ticker"]+": "+r["detail"])
 L.append("- Sources not yet verified: "+str(risk["phase122_risk_gap"]["pending_sources"]))
 L.append("")
 L.append("## Owner Actions")
 for a in owner["phase122_owner_actions"]["actions"]:
  L.append("- ["+a["priority"]+"] "+a["action"]+": "+a["detail"])
 L.append("")
 L.append("---")
 L.append("*Research-only brief. No investment advice. No trading signals.*")
 import os as _os
 md=_os.linesep.join(L)
 return {"phase122_markdown_brief":{"generated":True,"sections":8,"lines":len(L),"markdown":md,"research_only":True,"mock_used":False,"fixture_used":False}}
