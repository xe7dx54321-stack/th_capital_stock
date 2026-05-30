#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lib'))
from smr_phase80_consistency_config import load_config, validate_config
def build(): cfg=load_config();v=validate_config(cfg); return {'phase80_consistency_config':{'config':cfg,'validation':v}}
def main(): p=argparse.ArgumentParser();p.add_argument('--json',action='store_true');a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()