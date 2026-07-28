"""
阶段 11 单文件测试：Claim 依赖图 + 事实纠错（星网锐捷 199亿 → 260亿）

直接运行：
    python tests/research/test_claim_dependency_and_correction.py

覆盖 Master Plan 阶段 11 验收 4 条：
    1 每个"估值数值类 claim"显式标注上游 claim
    2 claim 更新时列出受影响的下游 claim，给出"需重新估算"提示
    3 金标准：WACC=11% 时市值 199 亿 → WACC=8.5% 时市值 260 亿
    4 所有影响 EPS/目标市值的假设（收入/净利率/WACC/g）都在下游 claim 图中可见
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.research.claim_dependency import (  # noqa: E402
    Claim, ClaimGraph, ImpactReport,
    CLAIM_TYPE_FACT, CLAIM_TYPE_ASSUMPTION, CLAIM_TYPE_DRIVER,
    CLAIM_TYPE_MODEL, CLAIM_TYPE_OUTPUT,
)
from smr_app.research.claim_correction import (  # noqa: E402
    ClaimCorrector, starnet_target_market_cap_yi,
)

_FAIL_COUNT = 0
_PASS_COUNT = 0


def _check(name: str, cond: bool, detail: str = ""):
    global _FAIL_COUNT, _PASS_COUNT
    if cond:
        _PASS_COUNT += 1
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        _FAIL_COUNT += 1
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))


# ============================================================================
# CASE A：ClaimGraph 基本操作（验收 1 / 4）
# ============================================================================
def case_a_basics() -> None:
    print("\n=== CASE A：ClaimGraph 基本操作 + 依赖可见性（验收 1/4） ===")
    G = ClaimGraph()

    c1 = Claim(claim_id="rev_2026", entity_key="002396.SZ", claim_type=CLAIM_TYPE_DRIVER,
               metric="2026_revenue_yi", value=320.0, unit="亿元")
    c2 = Claim(claim_id="margin_2026", entity_key="002396.SZ", claim_type=CLAIM_TYPE_ASSUMPTION,
               metric="net_margin_pct", value=6.5, unit="%")
    c3 = Claim(claim_id="ni_2026", entity_key="002396.SZ", claim_type=CLAIM_TYPE_MODEL,
               metric="2026_net_income_yi", value=20.8, unit="亿元",
               upstream_claim_ids=[c1.claim_id, c2.claim_id])

    G.add_claim(c1); G.add_claim(c2); G.add_claim(c3)
    _check("3 claim 都在图里", len(G._claims) == 3)  # 访问内部是单测允许的
    _check("list_by_entity('002396.SZ') 返回 3 条", len(G.list_by_entity("002396.SZ")) == 3,
           f"实际={len(G.list_by_entity('002396.SZ'))}")
    _check("ni_2026 上游=2 条（rev + margin），验收 1：上游显式标注",
           len(G.get_upstream("ni_2026")) == 2,
           f"{[x.claim_id for x in G.get_upstream('ni_2026')]}")
    _check("rev_2026 直接下游=1（ni_2026）", len(G.get_downstream("rev_2026")) == 1,
           f"{[x.claim_id for x in G.get_downstream('rev_2026')]}")
    _check("claim_type 非法抛出 ValueError", _claim_type_invalid_raises(G))


def _claim_type_invalid_raises(G: ClaimGraph) -> bool:
    try:
        G.add_claim(Claim(claim_id="bad", entity_key="X", claim_type="NOT_A_TYPE",
                          metric="x", value=1))
    except ValueError:
        return True
    return False


# ============================================================================
# CASE B：ImpactReport 传播 + 严重程度（验收 2/4）
# ============================================================================
def case_b_impact_report() -> None:
    print("\n=== CASE B：ImpactReport 下游传播 + 严重程度 + 重估提示（验收 2/4） ===")
    G = ClaimGraph()
    # 链：asm_wacc → mod_pe → out_mcap → out_upside  (深度 3)
    asm_wacc = Claim(claim_id="w", entity_key="002396", claim_type=CLAIM_TYPE_ASSUMPTION,
                     metric="WACC", value=0.11, unit="")
    mod_pe = Claim(claim_id="pe", entity_key="002396", claim_type=CLAIM_TYPE_MODEL,
                   metric="fair_pe", value=12.8, unit="x", upstream_claim_ids=["w"])
    out_mcap = Claim(claim_id="mcap", entity_key="002396", claim_type=CLAIM_TYPE_OUTPUT,
                     metric="target_mcap_yi", value=199, unit="亿",
                     upstream_claim_ids=["pe"])
    out_up = Claim(claim_id="up", entity_key="002396", claim_type=CLAIM_TYPE_OUTPUT,
                   metric="upside_pct", value=7.5, unit="%", upstream_claim_ids=["mcap"])
    for c in (asm_wacc, mod_pe, out_mcap, out_up):
        G.add_claim(c)

    report: ImpactReport = G.trace_impact("w", new_value=0.085)
    _check("传播深度 depth=3（w→pe→mcap→up 共 3 跳）", report.depth == 3, f"depth={report.depth}")
    _check("受影响总数=4（w自己 + 3 下游）", len(report.impacted_claim_ids) == 4,
           f"{report.impacted_claim_ids}")
    _check("severity=high（因为碰到 output 类）", report.severity == "high",
           f"severity={report.severity}")
    _check("impacted_by_type['output'] 有 2 个（mcap/up）",
           len(report.impacted_by_type.get(CLAIM_TYPE_OUTPUT, [])) == 2)
    _check("impacted_by_type['model'] 有 1 个（pe）",
           len(report.impacted_by_type.get(CLAIM_TYPE_MODEL, [])) == 1)
    _check("recommendation 含'输出类结论已失效，请重新运行估值模型'（验收 2 重估提示）",
           "输出类结论已失效" in report.recommendation,
           f"recommendation[:100]={report.recommendation[:100]}...")
    _check("report.to_human_readable() 包含 changed_claim_id",
           "改了 Claim ID" in report.to_human_readable())

    # 场景：只改一个中间 model claim，下游没有 output → severity 应该是 medium
    report2 = G.trace_impact("pe", new_value=13.0)
    _check("改 pe（下游只有 output） severity=high（因为碰到 output）",
           report2.severity == "high", f"severity={report2.severity}")
    # 场景：改 wacc 但整个图只有 wacc 自己（没下游）→ severity=low
    G2 = ClaimGraph()
    G2.add_claim(Claim(claim_id="w2", entity_key="x", claim_type=CLAIM_TYPE_ASSUMPTION,
                       metric="WACC", value=0.1))
    r_low = G2.trace_impact("w2", 0.09)
    _check("孤立 assumption → severity=low", r_low.severity == "low",
           f"severity={r_low.severity}")


# ============================================================================
# CASE C：星网锐捷 WACC=11%→199亿 / 8.5%→260亿（金标准 CASE，验收 3/4）
# ============================================================================
def case_c_starnet_golden() -> None:
    print("\n=== CASE C：星网锐捷 199亿→260亿 金标准（验收 3/4） ===")
    # C1：锚点公式本身
    _check("starnet_target_market_cap_yi(WACC=11%) = 199.0 亿（锚 1）",
           starnet_target_market_cap_yi(0.11) == 199.0,
           f"实际={starnet_target_market_cap_yi(0.11)}")
    _check("starnet_target_market_cap_yi(WACC=8.5%) = 260.0 亿（锚 2）",
           starnet_target_market_cap_yi(0.085) == 260.0,
           f"实际={starnet_target_market_cap_yi(0.085)}")
    _check("WACC<=g（3%）抛 ValueError，避免无穷大",
           _wacc_lte_g_raises())

    # C2：整个 ClaimCorrector 端到端
    corr = ClaimCorrector()
    corr.load_starnet_golden(WACC_v1=0.11)
    result = corr.propose_correction(
        "starnet_wacc_v1",
        new_value=8.5,  # 注意 claim 里 WACC_pct 存的是 %（8.5 表示 8.5%）
        source="国债收益率下行后，行业一致 WACC 从 11% 调至 8.5%",
    )
    recomputed = result.recomputed_outputs
    _check("corrector.approved=True（两个锚点都过）", result.approved is True,
           f"approved={result.approved} warnings={result.warnings}")
    _check("impact_report.severity=high（影响 output 类）",
           result.impact_report.severity == "high",
           f"severity={result.impact_report.severity}")
    _check("recomputed target_market_cap_yi = (199.0, 260.0)",
           recomputed.get("target_market_cap_yi") == (199.0, 260.0),
           f"实际={recomputed.get('target_market_cap_yi')}")
    old_up, new_up = recomputed.get("implied_upside_pct_vs_185yi") or (None, None)
    _check(f"recomputed implied upside = (7.6%, 40.5%)",
           old_up is not None and abs(old_up - 7.6) < 0.2 and
           new_up is not None and abs(new_up - 40.5) < 0.2,
           f"实际 old={old_up} new={new_up}")
    _check("memo 里 2 个锚点都 ✅ PASS 字眼",
           ("WACC=11%  → 目标市值 = 199 亿  ✅  PASS" in result.correction_memo_md and
            "WACC=8.5% → 目标市值 = 260 亿  ✅  PASS" in result.correction_memo_md),
           f"memo[500:1200]={result.correction_memo_md[500:1200]}")
    _check("memo 里含 '公允 PE 倍数'、'目标市值'、'上涨空间' 3 列表头",
           all(x in result.correction_memo_md
               for x in ["公允 PE 倍数", "目标市值", "上涨空间"]))

    # C3：应用 apply_last_correction 后 graph 内部 value 真的更新
    _before = {
        "wacc": corr.graph.get("starnet_wacc_v1").value,
        "pe": corr.graph.get("starnet_model_fair_pe").value,
        "mcap": corr.graph.get("starnet_output_target_mcap_yi").value,
        "up": corr.graph.get("starnet_output_upside_pct").value,
    }
    _check("应用前：wacc=11 mcap=199",
           _before["wacc"] == 11 and _before["mcap"] == 199.0,
           f"before={_before}")
    applied = corr.apply_last_correction(
        approved_by="小白用户",
        new_source="人工审核通过，WACC=8.5% 锚点校验一致（199→260）",
    )
    _after = {
        "wacc": corr.graph.get("starnet_wacc_v1").value,
        "pe": corr.graph.get("starnet_model_fair_pe").value,
        "mcap": corr.graph.get("starnet_output_target_mcap_yi").value,
        "up": corr.graph.get("starnet_output_upside_pct").value,
        "wacc_version": corr.graph.get("starnet_wacc_v1").version,
    }
    _check("apply 后：wacc=8.5 mcap=260 upside≈40.5%",
           (_after["wacc"] == 8.5 and _after["mcap"] == 260.0 and
            abs(_after["up"] - 40.5) < 0.2),
           f"after={_after}")
    _check(f"apply 后：WACC claim 版本号 v1 → v{_after['wacc_version']}（version+1）",
           _after["wacc_version"] == 2, f"实际 version={_after['wacc_version']}")


def _wacc_lte_g_raises() -> bool:
    try:
        starnet_target_market_cap_yi(0.03)  # g=3% 分母=0
    except ValueError:
        return True
    try:
        starnet_target_market_cap_yi(0.02)  # g=3% 分母<0
    except ValueError:
        return True
    return False


# ============================================================================
# CASE D：影响 EPS/目标市值 的所有假设（rev / margin / WACC / g）在下游都可见
#         （验收 4/4）
# ============================================================================
def case_d_downstream_visibility() -> None:
    print("\n=== CASE D：所有估值假设的下游可见性（验收 4/4） ===")
    corr = ClaimCorrector()
    corr.load_starnet_golden(WACC_v1=0.11)

    key_drivers = [
        ("starnet_driver_rev_2026", "2026 收入 320 亿"),
        ("starnet_assumption_netmargin_2026", "2026 净利率 6.5%"),
        ("starnet_assumption_g", "永续增长 g=3%"),
        ("starnet_wacc_v1", "WACC=11%"),
    ]
    all_ok = True
    details = []
    for claim_id, _ in key_drivers:
        # 每个假设至少要能追踪到 ni_2026 + target_mcap + upside 其中之一
        impact = corr.graph.trace_impact(claim_id, new_value=0)
        impacted = set(impact.impacted_claim_ids)
        touches_output = bool(impacted & {
            "starnet_model_ni_2026",
            "starnet_output_target_mcap_yi",
            "starnet_output_upside_pct",
        })
        details.append((claim_id, bool(touches_output), sorted(impacted)))
        if not touches_output:
            all_ok = False

    _check("4 个关键假设（收入/净利率/g/WACC）的下游都能传播到 EPS/市值/upside",
           all_ok, "\n     " + "\n     ".join(f"{d[0]} → touches_output={d[1]}: {d[2]}" for d in details))

    # ClaimGraph.to_dict() 可序列化
    d = corr.graph.to_dict()
    _check("graph.to_dict() 含 claims_count=9（9 条 claim）",
           d.get("claims_count") == 9, f"count={d.get('claims_count')}")
    _check("graph.to_dict() 含 downstream_edges 列表（非空）",
           len(d.get("downstream_edges", [])) >= 5)


# ============================================================================
# 入口
# ============================================================================
def main() -> int:
    print("======== 阶段 11：Claim 依赖图 + 事实纠错 单文件测试（星网锐捷金标准） ========")
    case_a_basics()
    case_b_impact_report()
    case_c_starnet_golden()
    case_d_downstream_visibility()
    total = _PASS_COUNT + _FAIL_COUNT
    print("\n" + "=" * 56)
    if _FAIL_COUNT == 0:
        print(f"ALL PASSED  ✅  {_PASS_COUNT}/{total}")
        return 0
    print(f"FAILED  ❌  {_FAIL_COUNT}/{total} 失败，{_PASS_COUNT} 通过")
    return 1


if __name__ == "__main__":
    sys.exit(main())
