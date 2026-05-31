import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase85b_closeout_config import load_config
def build(): return {"phase85b_closeout_config": {"strategy": load_config()["strategy"], "problem_tickers": len(load_config()["problem_tickers"]), "preserved_blocked": load_config()["preserved_blocked"], "fallback_sources": sum(len(pt["fallback_priority"]) for pt in load_config()["problem_tickers"]), "mock_used": False, "fixture_used": False}}
def main(): p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true"); a = p.parse_args(); b = build(); print(json.dumps(b, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
