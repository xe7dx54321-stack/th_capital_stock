def load_pending_candidates():
    return [{"ticker":t,"name":n,"market":"US"} for t,n in [("MRVL","Marvell Technology"),("AMAT","Applied Materials"),("LRCX","Lam Research"),("KLAC","KLA Corporation"),("INTC","Intel"),("SNPS","Synopsys"),("CDNS","Cadence Design Systems"),("CRM","Salesforce")]]

def load_allowed_decisions():
    return ["approve_research_activation","defer_to_next_review","request_more_evidence","request_identity_confirmation","request_source_route_confirmation","reject_for_now"]

def load_forbidden_terms():
    return ["buy","sell","short","add","reduce","target_price","position_sizing","trade_action","broker","order","position","pnl","return","profit","loss"]
