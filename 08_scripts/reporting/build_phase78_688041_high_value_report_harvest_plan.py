#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"lib"))
from smr_phase78_high_value_report_harvest_plan import build_harvest_plan
def build():return build_harvest_plan()
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
