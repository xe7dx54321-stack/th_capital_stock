import json,os
def build_health_board(heartbeat, staleness, reliability):
    hb=heartbeat.get("phase98_heartbeat_probe",{})
    st=staleness.get("phase98_source_staleness",{})
    rd=reliability.get("phase98_reliability_decay",{})
    rows=[]
    for s in ["yfinance_financials","akshare_sina_financial","eastmoney_financial","sec_edgar_companyfacts","cninfo_disclosure","szse_disclosure","irm_news"]:
        h_status="healthy"
        for r in hb.get("results",[]):
            if r["source"]==s:
                h_status=r["heartbeat_status"]
                break
        st_status="fresh"
        for r in st.get("fresh_sources",[]):
            if r["source"]==s: st_status="fresh"
        for r in st.get("stale_sources",[]):
            if r["source"]==s: st_status="stale"
        for r in st.get("expired_sources",[]):
            if r["source"]==s: st_status="expired"
        r_score=1.0
        for r in rd.get("rows",[]):
            if r["source"]==s: r_score=r["reliability_score"]
        overall="healthy" if h_status=="healthy" and st_status=="fresh" and r_score>0.8 else ("warning" if h_status in ("blocked","skipped") or st_status=="stale" else "critical")
        rows.append({"source":s,"heartbeat":h_status,"staleness":st_status,"reliability":r_score,"overall_health":overall})
    return {"phase98_health_board":{"sources":len(rows),"healthy":sum(1 for r in rows if r["overall_health"]=="healthy"),"warning":sum(1 for r in rows if r["overall_health"]=="warning"),"critical":sum(1 for r in rows if r["overall_health"]=="critical"),"rows":rows,"mock_used":False,"fixture_used":False}}
