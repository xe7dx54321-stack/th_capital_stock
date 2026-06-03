def build_navigation_css():
    css = '''
.breadcrumb{display:flex;gap:8px;padding:12px 0;font-size:13px;color:var(--muted);flex-wrap:wrap}
.breadcrumb a{color:var(--accent);text-decoration:none}
.breadcrumb a:hover{text-decoration:underline}
.breadcrumb .sep{color:var(--muted)}
.site-map{max-width:800px;margin:0 auto;padding:24px}
.site-map h2{color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:8px;margin-bottom:16px;font-size:17px}
.site-map ul{list-style:none;padding:0}
.site-map li{margin-bottom:8px}
.site-map a{color:var(--accent);text-decoration:none;font-size:14px}
.site-map a:hover{text-decoration:underline}
.site-map .type-tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;margin-left:8px}
.type-tag.dashboard{background:var(--accent);color:#000}
.type-tag.detail{background:var(--green);color:#000}
.type-tag.index{background:var(--orange);color:#000}
.cross-ref{font-size:13px;color:var(--muted);margin-top:4px}
.cross-ref a{color:var(--accent)}
.ticker-grid-section .ticker-card a{color:var(--accent);text-decoration:none;font-size:12px;display:inline-block;margin-top:8px}
'''
    return {"phase143_navigation_css": {"css": css, "ready": True, "mock_used": False, "fixture_used": False}}
