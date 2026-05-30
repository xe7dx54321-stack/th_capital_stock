#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase73_szse_endpoint_diagnostics import diagnose_szse
def build():
 row=diagnose_szse("300394.SZ")
 return {"phase73_szse_endpoint_diagnostics_report":{"ticker":"300394.SZ",**row}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
