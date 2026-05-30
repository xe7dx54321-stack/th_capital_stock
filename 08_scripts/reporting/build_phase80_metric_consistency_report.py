#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"lib"))
from smr_phase80_report_metric_loader import load_report_metrics
from smr_phase80_structured_financial_metric_loader import load_structured_metrics
from smr_phase80_metric_reconciliation import reconcile_metrics
from smr_phase80_metric_consistency_checker import check_consistency
def build():
    rm=load_report_metrics()["phase80_report_metric_loader"]["rows"]
    sm=load_structured_metrics()["phase80_structured_metric_loader"]["rows"]
    rec=reconcile_metrics(rm,sm)
    return check_consistency(rec["phase80_metric_reconciliation"]["rows"])
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
