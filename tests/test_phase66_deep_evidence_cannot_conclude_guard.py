import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(R) not in sys.path: sys.path.insert(0,str(R))

FORBIDDEN_RULES=[
    {"forbidden":"800G 提及 = 800G 收入占比确认","pattern":["800G revenue share confirmed","800G收入占比确认","800G 收入占比确认"],"allowed_rewrite":"真实披露文本支持 800G 相关产品进展，但不能确认 800G 收入占比。"},
    {"forbidden":"1.6T 提及 = 1.6T 大规模放量","pattern":["1.6T mass production confirmed","1.6T大规模放量","1.6T 放量确认"],"allowed_rewrite":"真实披露文本支持 1.6T 相关进展，但不能确认大规模放量。"},
    {"forbidden":"订单能见度好 = 具体订单金额确认","pattern":["order amount confirmed","订单金额确认","具体订单金额"],"allowed_rewrite":"订单能见度好不能等同于具体订单金额确认。"},
    {"forbidden":"产能扩张 = 订单已锁定","pattern":["order locked confirmed","订单锁定确认"],"allowed_rewrite":"产能扩张计划不能确认订单已锁定。"},
]

def run_guard(claims,evidence):
    violations=[]
    claims_text_json=json.dumps(claims,ensure_ascii=False).lower()
    for rule in FORBIDDEN_RULES:
        for pat in rule["pattern"]:
            if pat.lower() in claims_text_json:
                violations.append({"forbidden_claim":rule["forbidden"],"matched_pattern":pat,"allowed_rewrite":rule["allowed_rewrite"]})
    guard_status="pass" if len(violations)==0 else "fail"
    return {"claims_checked":len(claims),"violations":len(violations),"guard_status":guard_status,"blocked_claim_examples":violations[:5]}

class TestCannotConcludeGuard(unittest.TestCase):
    def test_fixture_passes_guard(self):
        claims=[{"claim":"800G_signal_supported","claim_status":"supported","limitation":"支持 800G 方向，但不确认收入占比。"}]
        gr=run_guard(claims,[])
        self.assertEqual(gr["guard_status"],"pass")
    def test_800G_revenue_share_violation(self):
        claims=[{"claim":"800G_revenue_share_confirmed","claim_status":"confirmed","limitation":"800G 收入占比确认。"}]
        gr=run_guard(claims,[])
        self.assertEqual(gr["guard_status"],"fail")
    def test_1_6T_mass_production_violation(self):
        claims=[{"claim":"1.6T_mass_production_confirmed","claim_status":"confirmed","limitation":"1.6T大规模放量确认。"}]
        gr=run_guard(claims,[])
        self.assertEqual(gr["guard_status"],"fail")

if __name__=="__main__":unittest.main()
