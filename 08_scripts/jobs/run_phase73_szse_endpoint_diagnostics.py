#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase73_szse_endpoint_diagnostics import diagnose_szse
def run(mode="execute",tickers=None):
 if tickers is None:tickers=["300394.SZ"]
 sn=mode=="skip_network"
 rows=[diagnose_szse(t,skip_network=sn) for t in tickers]
 return {"phase73_szse_endpoint_diagnostics":{"mode":mode,"tickers_checked":len(tickers),"rows":rows,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true")
 p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true")
 a=p.parse_args()
 mode="skip_network" if a.skip_network else ("dry_run" if getattr(a,"dry_run") else "execute")
 r=run(mode)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
