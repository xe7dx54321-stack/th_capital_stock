import sys; from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT/"08_scripts"/"jobs", ROOT/"08_scripts"/"reporting", ROOT/"08_scripts"/"verification", ROOT/"08_scripts"/"lib", ROOT/"tests"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
from phase50_helpers import make_phase50_active_conn
def make_phase51_conn(): return make_phase50_active_conn()
def make_phase51_fixture_candidates():
    return [{"candidate_id":f"candidate_300308_product_mix_00{i}","variable":"product_mix","source_id":f"real_source_300308_cninfo_{i}","source_url":"https://example.com","source_date":"2026-05-01","source_provider":"cninfo","source_type":"cninfo_annual_report","chunk_id":f"chunk_300308_ir_00{i}","normalized_text_id":f"norm_text_{i}","quoted_span":"Q: 公司目前高端光模块产品占比如何？A: 公司800G及以上产品占比持续提升，预计将继续保持增长趋势。" if i<3 else "关于公司日常经营合同的公告","confidence":"medium" if i<5 else "low","chunk_type":"qa_section" if i<4 else "unknown"} for i in range(9)]
