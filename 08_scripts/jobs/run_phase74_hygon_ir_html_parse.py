#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_hygon_ir_html_parser import parse_hygon_ir
def run(mode="execute"):
 sn=mode=="skip_network"
 r=parse_hygon_ir(skip_network=sn)
 return{"phase74_hygon_ir_html_parse":r}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true")
 p.add_argument("--json",action="store_true")
 a=p.parse_args()
 mode="dry_run" if getattr(a,"dry_run") else "execute"
 r=run(mode)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
