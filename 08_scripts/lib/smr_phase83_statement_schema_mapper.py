import json
from pathlib import Path
MAP=Path(__file__).resolve().parents[2]/"config"/"phase83_hk_us_statement_metric_mapping.json"
def load_mapping():
    with open(MAP,"r",encoding="utf-8-sig") as f:return json.load(f)
def build_mapping_report():
    m=load_mapping();rows=[]
    for mk,md in m.items():
        dr=md.get("derived_rule","");rows.append({"standard_metric":mk,"hk_aliases":md.get("hk_aliases",[]),"us_aliases":md.get("us_aliases",[]),"derived_rule":dr,"normalization_rule":"value_to_currency_unit"})
    derived=[k for k,md in m.items() if md.get("derived_rule")]
    return {"phase83_statement_schema_mapping":{"metrics_mapped":len(rows),"derived_metrics":derived,"rows":rows,"mock_used":False,"fixture_used":False}}
