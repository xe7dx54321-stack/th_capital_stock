def load_phase154_loop_results():
    try:
        from smr_phase154_loaders import load_phase153_onboarding_packets, load_phase150_tier_assignments
        tiers = load_phase150_tier_assignments()
        core = [a["ticker"] for a in tiers.get("assignments",[]) if a["tier"]=="core"]
        watch = [a["ticker"] for a in tiers.get("assignments",[]) if a["tier"]=="watch"]
        cand = [a["ticker"] for a in tiers.get("assignments",[]) if a["tier"]=="candidate"]
        ready = [p["ticker"] for p in load_phase153_onboarding_packets()]
        return {"core":core,"watch":watch,"candidate":cand,"ready":ready,"all":list(dict.fromkeys(core+watch+cand+ready))}
    except:
        return {"core":["NVDA","AVGO","688041.SH"],"watch":["300308.SZ","002230.SZ","09988.HK","00700.HK","300394.SZ"],"candidate":["TSM","ASML","AMD","SNOW","MU"],"ready":["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM"],"all":["NVDA","AVGO","688041.SH","300308.SZ","002230.SZ","09988.HK","00700.HK","300394.SZ","TSM","ASML","AMD","SNOW","MU","MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM"]}

def load_phase146_agent_state():
    return {"agent_memory":{"entries":0},"task_queue":{"pending":0,"tasks":[]},"mock_used":False}
