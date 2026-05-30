#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
from run_phase74_irm_html_qa_parse import run
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=run("execute")
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
