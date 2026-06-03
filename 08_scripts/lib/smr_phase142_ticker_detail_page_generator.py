def generate_ticker_detail_page(ticker_data, css_extension):
    t = ticker_data
    cc = {"high":"conf-high","medium":"conf-med","low":"conf-low"}.get(t["confidence"],"conf-med")
    mc = {"CN_A":"CN_A","HK":"HK","US":"US"}.get(t["market"],"")
    L = chr(60); R = chr(62); A = chr(38)
    th = ""
    for e in t.get("thesis_timeline",[]):
        th += L+"div class=timeline-entry"+R+L+"span class=timeline-date"+R+e["date"]+L+"/span"+R+L+"span class=timeline-event"+R+e["event"]+L+"/span"+R+L+"span class=timeline-status"+R+e["status"]+L+"/span"+R+L+"/div"+R
    ev = ""
    for e in t.get("evidence_chain",[]):
        ev += L+"div class=evidence-link"+R+L+"strong"+R+e["type"]+": "+L+"/strong"+R+" "+e["claim"]+L+"br"+R+L+"span class=meta"+R+"Source: "+e["source"]+" | Strength: "+e["strength"]+L+"/span"+R+L+"/div"+R
    dd = ""
    for d in t.get("deep_dives",[]):
        dd += L+"div class=dd-entry"+R+L+"strong"+R+d["id"]+L+"/strong"+R+" ("+d["date"]+") - "+d["scope"]+" ["+d["status"]+"]"+L+"/div"+R
    if not t.get("deep_dives"): dd = L+"p class=meta"+R+"No deep dive sessions recorded yet."+L+"/p"+R
    fin = t.get("financial_snapshot",{})
    fh = L+"div class=fin-snapshot"+R+L+"table"+R
    for k,v in fin.items():
        if k not in ("valuation_note","note"): fh += L+"tr"+R+L+"td"+R+k+L+"/td"+R+L+"td"+R+str(v)+L+"/td"+R+L+"/tr"+R
    fh += L+"/table"+R
    if fin.get("valuation_note"): fh += L+"p class=meta"+R+"Note: "+fin["valuation_note"]+L+"/p"+R
    if fin.get("note"): fh += L+"p class=meta"+R+"Note: "+fin["note"]+L+"/p"+R
    fh += L+"/div"+R
    sh = L+"ul class=source-limits"+R
    for s in t.get("source_limitations",[]): sh += L+"li"+R+s+L+"/li"+R
    sh += L+"/ul"+R
    gh = L+"div class=gaps"+R
    for g in t.get("gaps",[]):
        st = "tag-warn" if g["severity"]=="high" else "tag-info"
        gh += L+"div class=gap-item"+R+L+"span class=tag "+st+""+R+g["severity"]+L+"/span"+R+" "+g["gap"]+L+"/div"+R
    if not t.get("gaps"): gh += L+"p class=meta"+R+"No active gaps."+L+"/p"+R
    gh += L+"/div"+R
    ah = L+"div class=actions"+R
    for a in t.get("owner_actions",[]):
        pt = "tag-warn" if a["priority"]=="high" else ("tag-info" if a["priority"]=="medium" else "tag-pass")
        ah += L+"div class=action-item"+R+L+"span class=tag "+pt+""+R+a["priority"]+L+"/span"+R+" "+a["action"]+L+"/div"+R
    ah += L+"/div"+R
    ar = L+"ul class=artifact-links"+R
    for a in t.get("related_artifacts",[]): ar += L+"li"+R+L+"code"+R+a+L+"/code"+R+L+"/li"+R
    if not t.get("related_artifacts"): ar += L+"li class=meta"+R+"No related artifacts."+L+"/li"+R
    ar += L+"/ul"+R
    tpl = L+"!DOCTYPE html"+R+"\n"+L+"html lang=en"+R+"\n"+L+"head"+R+"\n"+L+"meta charset=UTF-8"+R+"\n"+L+"meta name=viewport content=width=device-width,initial-scale=1.0"+R+"\n"+L+"title"+R+"__T__ - __N__ | TH Capital Research"+L+"/title"+R+"\n"+L+"style"+R+"__CSS__"+L+"/style"+R+"\n"+L+"/head"+R+"\n"+L+"body class=detail-page"+R+"\n"+L+"header class=detail-header"+R+"\n"+L+"a href=phase141_research_console.html class=back-link"+R+A+"larr; Research Console"+L+"/a"+R+"\n"+L+"h1"+R+"__T__ - __N__"+L+"/h1"+R+"\n"+L+"div class=detail-meta"+R+"\n"+L+"span class=market-tag __MC__"+R+"__MK__"+L+"/span"+R+"\n"+L+"span class=__CC__"+R+"Thesis: __ST__ (__CF__)"+L+"/span"+R+"\n"+L+"span"+R+"Currency: __CU__"+L+"/span"+R+"\n"+L+"/div"+R+"\n"+L+"/header"+R+"\n"+L+"main class=detail-main"+R+"\n"+L+"section id=thesis-summary"+R+L+"h2"+R+"Core Thesis"+L+"/h2"+R+L+"p"+R+"__TH__"+L+"/p"+R+L+"p"+R+"Status: "+L+"span class=__CC__"+R+"__ST__"+L+"/span"+R+" | Confidence: "+L+"span class=__CC__"+R+"__CF__"+L+"/span"+R+L+"/p"+R+L+"/section"+R+"\n"+L+"section id=thesis-timeline"+R+L+"h2"+R+"Thesis Timeline"+L+"/h2"+R+"__TL__"+L+"/section"+R+"\n"+L+"section id=evidence-chain"+R+L+"h2"+R+"Evidence Chain"+L+"/h2"+R+"__EV__"+L+"/section"+R+"\n"+L+"section id=deep-dive-history"+R+L+"h2"+R+"Deep Dive History"+L+"/h2"+R+"__DD__"+L+"/section"+R+"\n"+L+"section id=financial-snapshot"+R+L+"h2"+R+"Financial Snapshot"+L+"/h2"+R+"__FH__"+L+"/section"+R+"\n"+L+"section id=source-limitations"+R+L+"h2"+R+"Source Limitations"+L+"/h2"+R+"__SH__"+L+"/section"+R+"\n"+L+"section id=gaps-risks"+R+L+"h2"+R+"Gaps "+A+"amp; Risks"+L+"/h2"+R+"__GH__"+L+"/section"+R+"\n"+L+"section id=owner-actions"+R+L+"h2"+R+"Owner Actions"+L+"/h2"+R+"__AH__"+L+"/section"+R+"\n"+L+"section id=related-artifacts"+R+L+"h2"+R+"Related Artifacts"+L+"/h2"+R+"__AR__"+L+"/section"+R+"\n"+L+"/main"+R+"\n"+L+"footer class=detail-footer"+R+L+"p"+R+"Research-only detail page. No trade recommendations, target prices, or position sizing."+L+"/p"+R+L+"/footer"+R+"\n"+L+"/body"+R+"\n"+L+"/html"+R
    page = tpl.replace("__T__",t["ticker"]).replace("__N__",t["name"]).replace("__MK__",t["market"]).replace("__MC__",mc).replace("__CC__",cc).replace("__ST__",t["thesis_status"]).replace("__CF__",t["confidence"]).replace("__CU__",t["currency"]).replace("__TH__",t["thesis"]).replace("__CSS__",css_extension).replace("__TL__",th).replace("__EV__",ev).replace("__DD__",dd).replace("__FH__",fh).replace("__SH__",sh).replace("__GH__",gh).replace("__AH__",ah).replace("__AR__",ar)
    return page