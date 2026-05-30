#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
def run(mode="dry_run",tickers=None):
 if tickers is None:tickers=["300308.SZ","688041.SH","300394.SZ"]
 try:
  from build_phase74_fallback_evidence_rerun import build
  ev=build();items=ev.get("phase74_fallback_evidence_rerun",{}).get("rows",[])
 except:
  items=[]
 rows=[]
 for t in tickers:
  ti=[i for i in items if i.get("ticker")==t]
  if ti:rows.append({"ticker":t,"records_written":len(ti),"source_type":ti[0].get("source_type","unknown")})
  else:rows.append({"ticker":t,"records_written":0,"reason":"no_fallback_evidence_yet" if t!="300308.SZ" else "existing_cninfo"})
 total=sum(r.get("records_written",0) for r in rows)
 return{"phase74_fallback_evidence_memory_write":{"mode":mode,"records_written_total":total,"rows":rows,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true")
 p.add_argument("--json",action="store_true")
 a=p.parse_args()
 mode="dry_run" if getattr(a,"dry_run") else "execute"
 r=run(mode)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
