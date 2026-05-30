#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase73_irm_endpoint_repair import repair_irm
def build():
 rows=[repair_irm(t) for t in ["300308.SZ","688041.SH","300394.SZ"]]
 return {"phase73_irm_endpoint_repair_report":{"tickers_checked":len(rows),"rows":rows,"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 if a.markdown:
  for row in r["phase73_irm_endpoint_repair_report"]["rows"]:
   print(row["ticker"] + ": " + row.get("repair_status","?"))
 else:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
