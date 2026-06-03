def load_pending_candidates():
    return [{"ticker":t,"name":n,"market":"US","admission_score":4.2,"onboarding_status":"ready_for_owner_approval","decision":"pending_owner_review"} for t,n in [("MRVL","Marvell Technology"),("AMAT","Applied Materials"),("LRCX","Lam Research"),("KLAC","KLA Corporation"),("INTC","Intel"),("SNPS","Synopsys"),("CDNS","Cadence Design Systems"),("CRM","Salesforce")]]

def load_phase157_workflow():
    return {"owner_input_present":False,"pending":8,"approved":0,"simulation_only":True,"execution_blocked":True}

def load_phase141_console():
    return {"console_exists":True,"console_path":"09_runbooks/generated/phase141_console.html","static_html":True}
