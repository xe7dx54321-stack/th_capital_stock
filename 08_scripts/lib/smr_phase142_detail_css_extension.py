def build_detail_css_extension():
    css = '''
:root{--bg:#0d1117;--card-bg:#161b22;--border:#30363d;--text:#c9d1d9;--accent:#58a6ff;--green:#3fb950;--orange:#d2991d;--red:#f85149;--muted:#8b949e}
*{box-sizing:border-box;margin:0;padding:0}
body.detail-page{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
.detail-header{background:var(--card-bg);border-bottom:1px solid var(--border);padding:20px 24px}
.back-link{color:var(--accent);text-decoration:none;font-size:14px;display:inline-block;margin-bottom:12px}
.back-link:hover{text-decoration:underline}
.detail-header h1{font-size:20px;color:var(--accent);margin:0}
.detail-meta{display:flex;gap:16px;margin-top:8px;font-size:13px;color:var(--muted);flex-wrap:wrap}
.market-tag{padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600}
.market-tag.CN_A{background:var(--red);color:#000}.market-tag.HK{background:var(--orange);color:#000}.market-tag.US{background:var(--accent);color:#000}
.conf-high{color:var(--green)}.conf-med{color:var(--orange)}.conf-low{color:var(--red)}
.detail-main{max-width:960px;margin:0 auto;padding:24px}
.detail-main section{margin-bottom:28px}
.detail-main h2{font-size:17px;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:12px}
.timeline{display:flex;flex-direction:column;gap:8px}
.timeline-entry{display:flex;gap:12px;padding:8px 12px;background:var(--card-bg);border:1px solid var(--border);border-radius:6px;font-size:13px}
.timeline-date{color:var(--accent);min-width:70px;font-weight:600}
.timeline-event{flex:1}
.timeline-status{color:var(--muted);font-style:italic}
.evidence-chain{display:flex;flex-direction:column;gap:8px}
.evidence-link{background:var(--card-bg);border:1px solid var(--border);border-radius:6px;padding:10px 14px;font-size:13px}
.deep-dives .dd-entry{background:var(--card-bg);border:1px solid var(--border);border-radius:6px;padding:10px 14px;font-size:13px;margin-bottom:6px}
.fin-snapshot table{width:100%;border-collapse:collapse;font-size:13px}
.fin-snapshot td{padding:6px 10px;border-bottom:1px solid var(--border)}
.fin-snapshot td:first-child{color:var(--accent);font-weight:600;width:160px}
.source-limits{list-style:disc;padding-left:20px;font-size:13px}
.source-limits li{margin-bottom:4px}
.gaps .gap-item{padding:8px 12px;background:var(--card-bg);border:1px solid var(--border);border-radius:6px;font-size:13px;margin-bottom:6px}
.actions .action-item{padding:8px 12px;background:var(--card-bg);border:1px solid var(--border);border-radius:6px;font-size:13px;margin-bottom:6px}
.artifact-links{list-style:none;font-size:13px}
.artifact-links li{margin-bottom:4px}
.artifact-links code{background:var(--card-bg);padding:2px 6px;border-radius:3px;font-size:12px}
.tag{display:inline-block;padding:2px 6px;border-radius:3px;font-size:11px;margin-right:4px}
.tag-warn{background:var(--orange);color:#000}.tag-info{background:var(--accent);color:#000}.tag-pass{background:var(--green);color:#000}
.meta{color:var(--muted);font-size:12px}
.detail-footer{text-align:center;padding:20px;font-size:12px;color:var(--muted);border-top:1px solid var(--border);margin-top:40px}
.detail-nav{display:flex;gap:12px;padding:16px 24px;background:var(--card-bg);border-bottom:1px solid var(--border);flex-wrap:wrap;justify-content:center}
.detail-nav a{color:var(--accent);text-decoration:none;font-size:13px;padding:4px 8px;border-radius:4px}
.detail-nav a:hover{background:var(--border)}
.detail-nav a.active{background:var(--accent);color:#000}
'''
    return {"phase142_detail_css_extension": {"css": css, "ready": True, "mock_used": False, "fixture_used": False}}
