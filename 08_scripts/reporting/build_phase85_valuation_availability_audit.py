import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase85_cn_valuation_adapter import run_cn_valuation_adapter
from smr_phase85_hk_valuation_adapter import run_hk_valuation_adapter
from smr_phase85_us_valuation_adapter import run_us_valuation_adapter
from smr_phase85_valuation_availability_audit import build_availability_audit
def build():
    cn=run_cn_valuation_adapter();hk=run_hk_valuation_adapter();us=run_us_valuation_adapter()
    return build_availability_audit(cn["phase85_cn_valuation_adapter"]["rows"],hk["phase85_hk_valuation_adapter"]["rows"],us["phase85_us_valuation_adapter"]["rows"])
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
