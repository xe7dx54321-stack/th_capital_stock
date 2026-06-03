def load_phase156_activation_queue():
    return {"candidates":["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM"],"all_pending":True}

def load_ready_candidates():
    return [{"ticker":t,"name":n,"market":"US"} for t,n in [("MRVL","Marvell Technology"),("AMAT","Applied Materials"),("LRCX","Lam Research"),("KLAC","KLA Corporation"),("INTC","Intel"),("SNPS","Synopsys"),("CDNS","Cadence Design Systems"),("CRM","Salesforce")]]

def load_phase152_scores():
    return [{"ticker":t,"composite_score":4.2} for t in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM"]]

def load_phase150_tiers():
    return {"tier_counts":{"core":3,"watch":5,"candidate":5}}
