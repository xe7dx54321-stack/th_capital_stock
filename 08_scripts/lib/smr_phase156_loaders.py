def load_ready_for_owner_candidates():
    return [{"ticker":t,"name":n,"market":"US"} for t,n in [("MRVL","Marvell Technology"),("AMAT","Applied Materials"),("LRCX","Lam Research"),("KLAC","KLA Corporation"),("INTC","Intel"),("SNPS","Synopsys"),("CDNS","Cadence Design Systems"),("CRM","Salesforce")]]

def load_phase155_owner_digest():
    return {"pending_items":8,"digest_items":[{"ticker":t,"loop_status":"completed","action_required":"owner_review"} for t in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM"]]}

def load_phase153_onboarding_packets():
    return [{"ticker":t,"judge_decision":"ready_for_owner_approval","identity_status":"verified","source_route_ready":True} for t in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM"]]

def load_phase152_scores():
    return [{"ticker":t,"composite_score":4.2} for t in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM"]]

def load_phase150_tiers():
    return {"tier_counts":{"core":3,"watch":5,"candidate":5}}
