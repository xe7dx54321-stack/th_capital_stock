#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lib'))
from smr_phase80_structured_financial_metric_loader import load_structured_metrics
def build(): return load_structured_metrics()
def main(): p=argparse.ArgumentParser();p.add_argument('--json',action='store_true');a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()