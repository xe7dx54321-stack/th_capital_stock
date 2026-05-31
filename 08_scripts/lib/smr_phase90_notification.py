from smr_phase90_config import get_notification
def build_notification_status():
    n=get_notification()
    adapters=[]
    for k in["email","webhook","feishu","wechat_work"]:
        a=n.get(k,{})
        adapters.append({"adapter":k,"enabled":a.get("enabled",False),"status":a.get("status","disabled_by_config"),"reason":"not configured" if not a.get("enabled") else "pending configuration","note":"External delivery is disabled by default. Enable explicitly in config to activate."})
    return {"phase90_notification_adapters":{"adapters_defined":len(adapters),"enabled":sum(1 for a in adapters if a["enabled"]),"disabled":sum(1 for a in adapters if not a["enabled"]),"rows":adapters,"mock_used":False,"fixture_used":False}}
