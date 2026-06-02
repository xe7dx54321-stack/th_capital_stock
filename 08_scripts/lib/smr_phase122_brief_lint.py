def run_brief_lint():
 import re
 from smr_phase122_markdown_brief import build_markdown_brief
 from smr_phase122_style_rules import load_style_rules
 rules=load_style_rules()
 brief=build_markdown_brief()
 md=brief["phase122_markdown_brief"]["markdown"]
 md_lower=md.lower()
 ft=rules["phase122_style_rules"]["forbidden_terms"]
 fp=rules["phase122_style_rules"]["forbidden_phrases"]
 def word_match(term,text):
  return bool(re.search(r'\b'+re.escape(term)+r'\b',text))
 term_found=[t for t in ft if word_match(t,md_lower)]
 phrase_found=[p for p in fp if p in md_lower]
 system_terms=[t for t in ["pipeline","runner","mock","fixture","dashboard","validator","quality_gate"] if word_match(t,md_lower)]
 trade_terms=[t for t in ["buy","sell","target_price","position_sizing","recommend","overweight","underweight"] if word_match(t,md_lower)]
 violations=len(term_found)+len(phrase_found)+len(system_terms)
 has_boss=md.startswith("# Daily Research Brief")
 has_ticker="Ticker Research Cards" in md
 has_risk="Risk, Gaps" in md
 has_owner="Owner Actions" in md
 return {"phase122_brief_lint":{"overall":"pass" if violations==0 else "fail","violations":violations,"forbidden_terms_found":term_found,"forbidden_phrases_found":phrase_found,"system_terms_found":system_terms,"trade_terms_found":trade_terms,"has_boss_summary":has_boss,"has_ticker_cards":has_ticker,"has_risk_gaps":has_risk,"has_owner_actions":has_owner,"research_only":True,"mock_used":False,"fixture_used":False}}
