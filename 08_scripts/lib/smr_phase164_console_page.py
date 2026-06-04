def build_console_page_html():
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Candidate Hydration Console</title><link rel="stylesheet" href="phase164_hydration_console.css"></head>
<body><div class="console-container">
<header><h1>Candidate Hydration Console</h1><p class="subtitle">13-Candidate Snapshot Status | Agent Loop Integration | Activation Readiness</p></header>
<nav class="console-nav"><a href="#summary">Summary</a><a href="#cards">Cards</a><a href="#details">Details</a><a href="#freshness">Freshness</a><a href="#limitations">Limitations</a><a href="#monitoring">Monitoring</a><a href="#feed">Feed</a><a href="#queue">Queue</a><a href="#daily">Daily</a><a href="#activation">Activation</a></nav>
<div id="summary" class="section"><div id="summary-content"></div></div>
<div id="cards" class="section"><div id="cards-content"></div></div>
<div id="details" class="section"><div id="details-content"></div></div>
<div id="freshness" class="section"><div id="freshness-content"></div></div>
<div id="limitations" class="section"><div id="limitations-content"></div></div>
<div id="monitoring" class="section"><div id="monitoring-content"></div></div>
<div id="feed" class="section"><div id="feed-content"></div></div>
<div id="queue" class="section"><div id="queue-content"></div></div>
<div id="daily" class="section"><div id="daily-content"></div></div>
<div id="activation" class="section"><div id="activation-content"></div></div>
<footer><p>Research only. Not investment advice. No Watch/Core updates. No trades executed. No target prices. Execution blocked.</p></footer>
</div></body></html>"""
    return {"phase164_console_page": {"page_html": html, "page_generated": True, "static_html": True, "external_js": False, "mock_used": False, "fixture_used": False}}

def build_nav_integration():
    return {"phase164_nav_integration": {"integrated": True, "nav_items": 10, "mock_used": False, "fixture_used": False}}

def build_css_extension():
    css = ".console-container{max-width:1200px;margin:0 auto;padding:20px;font-family:system-ui,sans-serif}.hydration-card{padding:15px;margin:10px;border:1px solid #e5e7eb;border-radius:8px;display:inline-block;width:280px;vertical-align:top}.hydration-card.deferred{border-left:4px solid #d97706;background:#fffbeb}.hydration-card.live{border-left:4px solid #16a34a;background:#f0fdf4}.safety-label,.safety-note{color:#d97706;font-weight:bold}.limitation{color:#dc2626}.not-target-price,.not-trade-signal,.not-rating,.not-buy-sell,.no-trade,.no-watch-update{color:#2563eb;font-weight:bold;font-style:italic}.console-nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}.console-nav a{color:#2563eb;text-decoration:none;padding:4px 8px;border:1px solid #2563eb;border-radius:4px;font-size:.85em}.section{margin-bottom:20px;padding:15px;border:1px solid #e5e7eb;border-radius:8px}footer{text-align:center;color:#666;font-size:.85em;padding:20px;border-top:1px solid #e5e7eb;margin-top:30px}table{border-collapse:collapse;width:100%}td,th{padding:6px;border:1px solid #e5e7eb;text-align:left}"
    return {"phase164_css_extension": {"css": css, "static_only": True, "mock_used": False, "fixture_used": False}}
