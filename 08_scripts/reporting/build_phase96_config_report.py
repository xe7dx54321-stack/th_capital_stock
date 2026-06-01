import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase96_config import load_config

def build():
    cfg = load_config()
    return {
        "phase96_config": {
            "phase": cfg["phase"],
            "strategy": cfg["strategy"],
            "categories": cfg["hard_data_categories"],
            "peer_groups": list(cfg["peer_groups"].keys()),
            "db_path_ignored": cfg["db"]["gitignored"],
            "safety": cfg["safety"]
        }
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");args=p.parse_args()
    r=build()
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
