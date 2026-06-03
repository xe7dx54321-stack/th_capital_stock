import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase134_ticker_card_builder import build_ticker_cards
from smr_phase134_console_quality_gate import run_console_quality_gate
def main():
 tc=build_ticker_cards()["phase134_ticker_card_builder"]
 gq=run_console_quality_gate()["phase134_console_quality_gate"]
 cards_html=[]
 for c in tc["cards"]:
  cards_html.append(f"""<div class=\"ticker-card\" data-market=\"{c['market']}\">
 <h3>{c['ticker']} - {c['name']}</h3>
 <p>Market: {c['market']} | Sector: {c['sector']} | Currency: {c['currency']}</p>
 <p>Coverage: full | Watchlist: {c['watchlist_status']}</p>
</div>""")
 html=f"""<!DOCTYPE html>
<html lang=\"en\">
<head><meta charset=\"UTF-8\"><title>Personal Research Console v1</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1200px;margin:0 auto;padding:20px;background:#f8f9fa;color:#212529}}
.console-header{{background:#1a1a2e;color:#e0e0e0;padding:20px;border-radius:8px;margin-bottom:20px}}
.console-header h1{{margin:0}}
.health-bar{{display:flex;gap:20px;margin-top:10px;font-size:14px}}
.health-bar .pass{{color:#4caf50}}.health-bar .fail{{color:#f44336}}
.market-section{{background:#fff;border-radius:8px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}}
.ticker-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.ticker-card{{background:#fff;border-left:4px solid #2196f3;border-radius:8px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}}
.ticker-card[data-market=\"CN_A\"]{{border-left-color:#f44336}}
.ticker-card[data-market=\"HK\"]{{border-left-color:#ff9800}}
.ticker-card[data-market=\"US\"]{{border-left-color:#2196f3}}
.ticker-card h3{{margin:0 0 8px 0}}
.ticker-card p{{margin:4px 0;font-size:14px;color:#666}}
.footer{{text-align:center;padding:20px;color:#888;font-size:12px}}
</style></head>
<body>
<div class=\"console-header\">
<h1>Personal Research Console v1</h1>
<div class=\"health-bar\">
<span>Quality Gate: <span class=\"{'pass' if gq['overall']=='pass' else 'fail'}\">{gq['overall']}</span></span>
<span>Violations: {gq['violations']}</span>
<span>Research Only</span>
</div>
</div>
<div class=\"market-section\"><h2>Ticker Cards ({tc['ticker_cards_created']})</h2>
<div class=\"ticker-grid\">
{''.join(cards_html)}
</div></div>
<div class=\"footer\">Research-only console. No trade recommendations, target prices, or position sizing.</div>
</body></html>"""
 if "--json" in sys.argv:
  import json; print(json.dumps({"phase134_console_html_skeleton":{"html":html,"mock_used":False,"fixture_used":False}},ensure_ascii=False))
 else:
  print(html)
if __name__=="__main__":main()
