from smr_phase90_config import get_preflight
import sys,os,json
from pathlib import Path

def run_preflight():
    cfg=get_preflight();results=[]
    # Python version
    v=sys.version_info
    py_ok=v.major>=3 and v.minor>=8
    results.append({"check":"python_version","passed":py_ok,"detail":f"{v.major}.{v.minor}.{v.micro}","required":">=3.8"})
    # Required modules
    mods=["json","pathlib","argparse","unittest","yfinance","akshare"]
    for m in mods:
        try:__import__(m);results.append({"check":f"module_{m}","passed":True,"detail":"importable"})
        except:results.append({"check":f"module_{m}","passed":False,"detail":"not_importable"})
    # Config files
    cfgs=["config/phase89_unified_daily_intelligence.json","config/phase90_scheduled_automation_delivery.json"]
    for c in cfgs:
        exists=Path(c).exists()
        results.append({"check":f"config_{Path(c).name}","passed":exists,"detail":"exists" if exists else "missing"})
    # Writable dirs
    for d in ["09_runbooks/generated"]:
        dp=Path(d)
        if not dp.exists():
            try:dp.mkdir(parents=True,exist_ok=True);results.append({"check":f"dir_{d}","passed":True,"detail":"created"})
            except:results.append({"check":f"dir_{d}","passed":False,"detail":"cannot_create"})
        else:
            try:
                test_f=dp/"__preflight_test__";test_f.write_text("test");test_f.unlink()
                results.append({"check":f"dir_{d}","passed":True,"detail":"writable"})
            except:results.append({"check":f"dir_{d}","passed":False,"detail":"not_writable"})
    # Lock check
    lock=Path("09_runbooks/generated/phase90_run.lock")
    if lock.exists():
        results.append({"check":"no_existing_lock","passed":False,"detail":"lock_exists"})
    else:
        results.append({"check":"no_existing_lock","passed":True,"detail":"no_lock"})
    all_pass=all(r["passed"] for r in results if r["check"]!="network_connectivity_optional")
    return {"phase90_preflight":{"overall":"pass" if all_pass else "fail","checks_count":len(results),"passed_count":sum(1 for r in results if r["passed"]),"failed_count":sum(1 for r in results if not r["passed"]),"rows":results,"mock_used":False,"fixture_used":False}}
