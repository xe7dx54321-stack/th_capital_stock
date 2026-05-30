import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
def build():from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;from smr_phase82_multi_ticker_baseline_builder import build_multi_baselines;from smr_phase82_multi_ticker_delta_detector import detect_multi_delta;from smr_phase82_multi_ticker_threshold_engine import run_multi_threshold;from smr_phase82_multi_ticker_monitoring_evidence import build_multi_monitoring_evidence;m=load_multi_ticker_metrics();s=build_time_series(m);b=build_multi_baselines(s);d=detect_multi_delta(b);t=run_multi_threshold(d);return build_multi_monitoring_evidence(d,t)
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
