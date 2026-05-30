import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
def build():
    from smr_phase81_time_series_signal_loader import load_signals
    from smr_phase81_time_series_baseline_builder import build_baselines
    from smr_phase81_signal_delta_detector import detect_delta
    from smr_phase81_monitoring_config import load_config
    s=load_signals()["phase81_signal_loader"]["rows"];b=build_baselines(s);c=load_config();return detect_delta(b,c)
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
