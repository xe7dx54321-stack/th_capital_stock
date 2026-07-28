r"""
双标的换仓决策 V1 - 金标准评估脚本（阶段 5 交付物）

功能说明：
    用 master plan 中的金标准案例：把阳光电源（300274.SZ）持仓换成海光信息（688041.SH）
    直接调用 ComparisonMatrixBuilder + ScenarioPlanner，不依赖数据库/工作流/网络。
    运行后会输出 4 个文件到 artifacts_golden/ 目录：
      1. comparison_matrix.json       → 12 维度同口径比较矩阵
      2. decision_scenarios.json      → 四方案决策情景 + 推荐方案 + 用户偏好透明清单
      3. decision_memo.md             → 人类可读的相对决策备忘录（不是两份个股报告的拼接）
      4. monitoring_list.csv          → 领先指标监控清单（CSV，可直接粘进 Excel）

参数说明：
    命令行可选参数：
        --output-dir  指定输出目录（默认 ./artifacts_golden）
        --verbose     打印更多调试信息

返回值说明：
    正常运行结束时打印 "ALL OK (passed=<质量门是否通过>, recommended=<推荐方案>)"
    并通过 sys.exit(0) 退出；若质量门关键错误则 sys.exit(1)。

异常处理：
    异常时打印带行号的 Traceback 并 sys.exit(1)。

小白使用方法：
    ① 打开 PowerShell 或 CMD，cd 到 th_capital_stock_mvp 根目录
    ② 运行：python 08_scripts\dev\evaluate_pair_switch_decision.py
    ③ 打开 artifacts_golden 文件夹就能看到 4 个结果文件
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import traceback
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# 让脚本能直接 import 项目包（小白零配置运行）
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 08_scripts/dev -> 根目录
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.research.comparison_matrix import (  # noqa: E402
    ComparisonInput,
    ComparisonMatrix,
    ComparisonMatrixBuilder,
)
from smr_app.research.decision_scenarios import (  # noqa: E402
    DecisionOutput,
    MonitoringIndicator,
    ScenarioPlanner,
    UserPreference,
)


# ============================================================================
# 工具函数：datetime 可序列化
# ============================================================================

def _json_default(obj: Any) -> Any:
    """处理 dataclass + datetime 等类型的 JSON 序列化"""
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Type {type(obj).__name__} not JSON serializable")


# ============================================================================
# 金标准案例：构造 A=阳光电源、B=海光信息 的 ComparisonInput
# ============================================================================

def build_golden_inputs() -> tuple[ComparisonInput, ComparisonInput, UserPreference]:
    """
    构造金标准案例的输入（不访问数据库，直接填合理的演示值）

    小白讲解：
        这里就是"两位选手的档案袋"。
        数据是演示用的，时间统一用 now - 几小时，保证时点对齐检查通过。
        真实使用时，这些值会从阶段 4 的估值制品和市场快照里读取。
    """
    now = datetime.now(timezone.utc)
    snap_a = (now - timedelta(hours=2)).isoformat()
    snap_b = (now - timedelta(hours=3)).isoformat()

    # ------------------------------------------------------------
    # A 标的：阳光电源 300274.SZ（当前持仓，光伏逆变器龙头 → 成熟期）
    # ------------------------------------------------------------
    a = ComparisonInput(
        ticker="300274.SZ",
        name="阳光电源",
        # 基本面快照（单位：亿元、倍、小数）
        revenue=620.0, net_income=72.0,
        gross_margin=0.25, net_margin=0.116, operating_margin=0.13,
        roe=0.18,
        pe_ttm=22.0, pb=3.6,
        current_price=68.5, market_cap=2050.0, shares_outstanding=30.0,
        free_cash_flow=38.0, operating_cash_flow=85.0,
        # 阶段 4 估值制品
        valuation_target_price=82.0, valuation_target_market_cap=2460.0,
        valuation_irr=0.18, implied_cagr=0.10, implied_net_margin=0.115,
        # 元数据
        snapshot_as_of=snap_a, valuation_as_of=snap_a,
        fundamentals_period="2025A", source_authority_tier=2,
        # 行业与生命周期
        industry="光伏储能", lifecycle_stage="成熟期", industry_position="全球逆变器龙头",
        # 拥挤度与价格
        turnover_rate_20d=0.025,
        short_term_return=-0.08, medium_term_return=-0.15, relative_strength=-0.05,
        # 催化与风险
        catalysts=[
            "2026Q1 海外储能订单同比+40%",
            "美国 30% ITC 补贴延续至 2030 年",
            "1500V 组串逆变器全球份额提升至 32%",
        ],
        risks=[
            "海外贸易壁垒（欧盟 CBAM、美国关税）",
            "硅料价格反弹导致毛利压缩",
            "储能项目坏账率上升 0.8pp",
        ],
        # 持仓约束（仅 A 有值）
        holding_shares=3.0, holding_cost=55.0,
        holding_position_pct=0.20, holding_loss_tolerance=0.15,
        tax_on_short_term=0.005,
    )

    # ------------------------------------------------------------
    # B 标的：海光信息 688041.SH（候选换入方，国产算力 CPU/DCU → 成长期）
    # ------------------------------------------------------------
    b = ComparisonInput(
        ticker="688041.SH",
        name="海光信息",
        # 基本面快照
        revenue=188.0, net_income=52.0,
        gross_margin=0.48, net_margin=0.277, operating_margin=0.31,
        roe=0.22,
        pe_ttm=75.0, pb=12.8,
        current_price=128.0, market_cap=4100.0, shares_outstanding=32.0,
        free_cash_flow=12.0, operating_cash_flow=35.0,
        # 阶段 4 估值制品
        valuation_target_price=185.0, valuation_target_market_cap=5920.0,
        valuation_irr=0.35, implied_cagr=0.28, implied_net_margin=0.28,
        # 元数据
        snapshot_as_of=snap_b, valuation_as_of=snap_b,
        fundamentals_period="2025A", source_authority_tier=2,
        # 行业与生命周期
        industry="半导体算力", lifecycle_stage="成长期", industry_position="国产 x86 CPU + DCU 龙头",
        # 拥挤度与价格
        turnover_rate_20d=0.045,
        short_term_return=+0.12, medium_term_return=+0.28, relative_strength=+0.22,
        # 催化与风险
        catalysts=[
            "2026Q2 DCU 3 号量产，FP8 算力对标 A100",
            "三大运营商智算集采海光份额 45%",
            "深算四号完成生态适配，金融/政务客户放量",
        ],
        risks=[
            "制程工艺受限（先进封装产能不足）",
            "国际竞品降价（NVIDIA H20 对华特供）",
            "大客户应收账款周转率下降",
        ],
        # B 不是当前持仓，约束字段全留空
    )

    # ------------------------------------------------------------
    # 用户偏好（全部"明确表态"，用于验证 preference_used 不为空）
    # ------------------------------------------------------------
    pref = UserPreference(
        holding_horizon_months=36,
        annual_return_target=0.25,
        max_drawdown_tolerance=0.30,
        accept_loss_stock=False,
        accept_high_crowding=False,
        avoid_short_term_tax=True,
        min_switch_ratio=0.10,
        max_switch_ratio=0.70,
        allow_cross_sector=True,
        prefer_industry_leader=True,
        avoid_negative_roe=True,
        min_daily_turnover_yi=3.0,
    )

    return a, b, pref


# ============================================================================
# 独立质量门（复现阶段 5 worklow 里的 quality gate）
# ============================================================================

def run_quality_gate(matrix: ComparisonMatrix, decision: DecisionOutput) -> dict:
    """
    独立质量门：检查 12 维度齐全、四方案成立/失效条件、估值高低≠买卖信号、
    不执行真实交易声明、推荐方案在场景字典中存在等。

    返回 {"passed": bool, "critical_errors": list[str], "warnings": list[str]}
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1) 12 维度齐全
    expected_dims = {
        "lifecycle", "revenue_quality", "cash_flow", "roe", "valuation",
        "implied_growth", "industry_position", "catalysts", "risks",
        "crowding", "price_action", "holding_constraints",
    }
    if set(matrix.rows.keys()) != expected_dims:
        missing = expected_dims - set(matrix.rows.keys())
        extra = set(matrix.rows.keys()) - expected_dims
        errors.append(f"比较矩阵维度不匹配：缺失={missing or '无'}，多余={extra or '无'}")

    # 2) 四方案齐全且每个都有成立与失效条件
    for sid in ("continue_hold", "partial_switch", "full_switch", "hold_and_wait"):
        sc = decision.scenarios.get(sid)
        if sc is None:
            errors.append(f"决策缺少方案：{sid}")
            continue
        if len(sc.valid_conditions) == 0:
            errors.append(f"方案 {sid} 无成立条件")
        if len(sc.invalid_conditions) == 0:
            errors.append(f"方案 {sid} 无失效条件")

    # 3) partial/full 必须有 pacing 与 expected_switch_ratio
    for sid in ("partial_switch", "full_switch"):
        sc = decision.scenarios[sid]
        if sc.expected_switch_ratio is None:
            errors.append(f"方案 {sid} 缺少 expected_switch_ratio")
        if len(sc.pacing) == 0:
            errors.append(f"方案 {sid} 缺少分批节奏 pacing")

    # 4) 推荐方案在 scenarios 里，且不是空字符串
    if not decision.recommended or decision.recommended not in decision.scenarios:
        errors.append(f"推荐方案非法：recommended={decision.recommended!r}")

    # 5) 不执行真实交易声明
    if "不执行" not in decision.execution_warning:
        errors.append("execution_warning 未声明不执行真实交易")

    # 6) 估值高低不等价于买卖信号：检查所有维度 interpretation 里有没有
    #    "估值便宜所以买入" 或 "估值贵所以卖出" 这种直接表述。
    for dim in matrix.all_dimension_ids():
        row = matrix.get_row(dim)
        if row and "买入" in row.relative_description and "便宜" in row.relative_description:
            warnings.append(f"维度 {dim} 可能把估值便宜直接等同于买入信号")
        if row and "卖出" in row.relative_description and "贵" in row.relative_description:
            warnings.append(f"维度 {dim} 可能把估值贵直接等同于卖出信号")

    # 7) 用户偏好透明度：used + skipped 非空
    if len(decision.preference_used) + len(decision.preference_skipped) == 0:
        errors.append("用户偏好透明化失败：used 和 skipped 都为空")

    # 8) 监控清单非空（至少 2 个指标）
    if len(decision.monitoring_indicators) < 2:
        errors.append(f"监控清单指标不足 2 个：实际 {len(decision.monitoring_indicators)}")

    return {
        "passed": len(errors) == 0,
        "critical_errors": errors,
        "warnings": warnings + list(decision.warnings),
    }


# ============================================================================
# 人类可读备忘录渲染
# ============================================================================

def render_memo_md(matrix: ComparisonMatrix, decision: DecisionOutput, qg: dict) -> str:
    """
    输出 Markdown 格式的相对决策备忘录（不是两份个股报告的拼接）
    """
    # ------------------------------------------------------------------
    # 【小白也能看懂】智能数字格式化
    # 为什么要做这一层？
    #   - 比较矩阵里为了"确定性计算"，百分比全部存成小数（0.18 = 18%），
    #     金额都存成亿元（620.0 = 620 亿元）。但小白看 0.18% 会以为是 0.18 个百分点，
    #     看 revenue=620.0 不知道是万元还是亿元。所以显示时要"再翻译一遍"。
    #   - 字典 cell 的每个 key 含义不一样，不能一刀切。
    # ------------------------------------------------------------------
    _PERCENT_KEYS = {
        "net_margin", "gross_margin", "operating_margin",
        "implied_cagr", "implied_net_margin",
        "position_pct", "loss_tolerance", "short_term_tax",
        "turnover_20d", "return_1m", "return_3m", "relative_strength",
        "upside_potential",
    }
    _YI_KEYS = {
        "revenue", "net_income", "operating_cf", "free_cf", "market_cap",
    }
    _MULTIPLIER_KEYS = {"pe_ttm", "pb", "cf_to_ni"}
    _YUAN_PER_SHARE_KEYS = {"target_price", "current_price", "cost_per_share"}
    _WAN_SHARES_KEYS = {"shares_wan"}

    def _fmt_scalar(key: str | None, value: Any, unit_hint: str = "") -> str:
        """
        单个数值的"人类友好格式化"。

        参数：
            key       - 字典 key，用来判含义（net_margin → 百分比，revenue → 亿元）
            value     - 原始值（小数 0.18 / 亿元 620.0 / 文本 / 列表 ...）
            unit_hint - cell 的整体 unit 字符串（兜底用）

        返回：
            小白一眼能懂的字符串，比如 "18%"、"620.0 亿元"、"55.00 元/股"
        """
        if value is None:
            return "N/A"
        # --- 非数值直接转字符串 ---
        if isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value) + (f" {unit_hint}" if unit_hint and unit_hint not in ("文本", "文本列表", "N/A", "") else "")
        if not isinstance(value, (int, float)):
            return str(value)
        # --- 数值类，按 key 含义格式化 ---
        k = (key or "").lower()
        # 百分比：存的是小数（0.18），显示成 "18.0%"
        if k in _PERCENT_KEYS or (unit_hint == "%" and abs(value) <= 1.5):
            return f"{value * 100.0:.1f}%"
        # 每股价格/成本：带两位小数
        if k in _YUAN_PER_SHARE_KEYS:
            return f"{value:.2f} 元/股"
        # 万股：直接加单位
        if k in _WAN_SHARES_KEYS:
            return f"{value:.1f} 万股"
        # 倍数：加"倍"
        if k in _MULTIPLIER_KEYS:
            return f"{value:.1f} 倍"
        # 亿元级金额
        if k in _YI_KEYS:
            return f"{value:.1f} 亿元"
        # 兜底：一般小数保留两位，整数原样
        if isinstance(value, float):
            # 如果特别大或特别小（科学计数法风险），先格式化成普通小数
            if abs(value) < 0.001 and value != 0:
                return f"{value:.8f}"
            if abs(value) >= 10000:
                return f"{value:,.0f}"
            return f"{value:.2f}"
        return str(value)

    lines: list[str] = []
    a_name = f"{matrix.a_name}（{matrix.a_ticker}）"
    b_name = f"{matrix.b_name}（{matrix.b_ticker}）"
    rec = decision.scenarios.get(decision.recommended)

    lines.append(f"# 双标的换仓决策备忘录：{a_name} → {b_name}")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"> 时点差：{matrix.temporal_alignment_hours:.1f} h（阈值 72 h，"
                 f"{'通过' if matrix.temporal_alignment_pass else '未通过'}）  ")
    lines.append(f"> 数据完整度：{matrix.overall_completeness:.0%}；降级维度 {matrix.degraded_dimension_count}/12  ")
    lines.append(f"> 推荐方案：**{rec.name if rec else decision.recommended}**（置信度 {decision.confidence_level}）  ")
    lines.append(f"> 【重要免责】{decision.execution_warning}")
    lines.append("")

    # 1. 摘要：推荐方案 + 成立条件 TOP 3
    lines.append("## 1. 一页纸摘要")
    lines.append("")
    if rec:
        lines.append(f"- **结论**：{rec.rationale}")
        lines.append(f"- **换仓比例建议**："
                     f"{(rec.expected_switch_ratio if rec.expected_switch_ratio is not None else 0) * 100:.0f}%")
        lines.append(f"- **成立条件（TOP 3）**：")
        for c in (rec.valid_conditions[:3]):
            met_mark = "✅" if c.met else ("⚠️" if c.met is None else "❌")
            lines.append(f"  - {met_mark} {c.description}")
        lines.append(f"- **失效条件（一旦触发就推翻此方案）**：")
        for c in (rec.invalid_conditions[:3]):
            met_mark = "❌（已触发，需紧急复核）" if c.met else "🔍（未触发）"
            lines.append(f"  - {met_mark}：{c.description}")
    lines.append("")

    # 2. 12 维度同口径对比
    lines.append("## 2. 12 维度同口径对比矩阵")
    lines.append("")
    lines.append("| 维度 | A：当前持仓 | B：候选标的 | 相对描述（B - A） | 降级? |")
    lines.append("|---|---|---|---|---|")
    for dim_id in matrix.all_dimension_ids():
        row = matrix.get_row(dim_id)
        if row is None:
            continue
        def _cell_str(cell):
            if cell.degraded:
                return f"*缺失：{cell.degradation_reason or '降级'}*"
            v = cell.value
            if v is None:
                return cell.unit if cell.unit and cell.unit != "N/A" else "—"
            if isinstance(v, dict):
                # 【关键修复】每个字段按含义智能格式化（百分比 *100，金额 + 亿元 ...）
                parts = []
                for k, val in list(v.items())[:5]:
                    pretty = _fmt_scalar(k, val, cell.unit or "")
                    parts.append(f"{k}={pretty}")
                return " / ".join(parts)
            # 非 dict：ROE 这种单个百分比值
            return _fmt_scalar(None, v, cell.unit or "")
        deg_mark = "⚠️" if (row.a.degraded or row.b.degraded or row.data_conflict) else ""
        lines.append(
            f"| {row.dimension_label} | {_cell_str(row.a)} | {_cell_str(row.b)} |"
            f" {row.relative_description or '-'} | {deg_mark} |"
        )
    lines.append("")

    # 3. 四方案并排对比
    lines.append("## 3. 四方案决策并排对比")
    lines.append("")
    lines.append("| 方案 ID | 中文名称 | 打分 | 置信度 | 数据降级? | 换仓比例 | 推荐 |")
    lines.append("|---|---|---:|---:|---|---:|---|")
    for sid, sc in decision.scenarios.items():
        ratio_pct = f"{sc.expected_switch_ratio * 100:.0f}%" if sc.expected_switch_ratio is not None else "-"
        rec_mark = "⭐" if sid == decision.recommended else ""
        deg_mark = "⚠️ 是" if sc.degraded else "否"
        lines.append(
            f"| {sid} | {sc.name} | {sc.score} | {sc.confidence:.0%} |"
            f" {deg_mark} | {ratio_pct} | {rec_mark} |"
        )
    lines.append("")

    # 4. 分批节奏（只展示推荐方案）
    if rec and rec.pacing:
        lines.append(f"## 4. 推荐方案「{rec.name}」的分批节奏")
        lines.append("")
        lines.append("| 步序 | 占总换仓比例 | 触发条件 | 监控指标 | 原因 |")
        lines.append("|---:|---:|---|---|---|")
        for step in rec.pacing:
            lines.append(
                f"| {step.step_index} | {step.ratio * 100:.0f}% |"
                f" {step.trigger} | {step.indicator or '-'} | {step.rationale or '-'} |"
            )
        lines.append("")

    # 5. 用户偏好透明清单
    lines.append("## 5. 用户偏好透明化")
    lines.append("")
    lines.append("### 5.1 已明确、并参与决策的偏好")
    lines.append("")
    for item in decision.preference_used or ["（空）"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### 5.2 未表态、按中性跳过的偏好")
    lines.append("")
    for item in decision.preference_skipped or ["（空）"]:
        lines.append(f"- {item}")
    lines.append("")

    # 6. 领先指标监控清单（百分比值也做 *100 格式化）
    lines.append("## 6. 需要持续跟踪的领先指标（红绿灯）")
    lines.append("")
    lines.append("| 指标 ID | 名称 | 为什么重要 | 频率 | 当前值 | 预警阈值 | 影响方案 |")
    lines.append("|---|---|---|---|---|---|---|")
    for mi in decision.monitoring_indicators:
        cur = mi.current_value
        unit = mi.unit or ""
        pretty_cur = "-"
        if cur is not None:
            # 监控指标也做同样的："%" 开头或者值是 <=1.5 的小数且 unit 带"%/CAGR"，按百分比处理
            if ("%" in unit or "CAGR" in unit or "百分比" in unit) and isinstance(cur, (int, float)) and abs(cur) <= 1.5:
                pretty_cur = f"{cur * 100.0:.1f}%"
            elif isinstance(cur, float):
                if abs(cur) < 0.001 and cur != 0:
                    pretty_cur = f"{cur:.8f}"
                else:
                    pretty_cur = f"{cur:.3f}"
            else:
                pretty_cur = str(cur)
        # 阈值如果是元组/列表做字符串化
        thr = mi.warn_threshold
        if isinstance(thr, (tuple, list)):
            thr = "(" + ", ".join(str(x) for x in thr) + ")"
        lines.append(
            f"| {mi.indicator_id} | {mi.name} | {mi.why_it_matters} |"
            f" {mi.frequency or '-'} | {pretty_cur} |"
            f" {thr or '-'}（{mi.direction or '-'}）|"
            f" {', '.join(mi.applies_to_scenarios) or '-'} |"
        )
    lines.append("")

    # 7. 质量门与警告
    lines.append("## 7. 独立质量门 & 数据缺口")
    lines.append("")
    lines.append(f"- **质量门总评**：{'✅ 通过' if qg['passed'] else '❌ 不通过'}")
    if qg["critical_errors"]:
        lines.append("- **关键错误**：")
        for e in qg["critical_errors"]:
            lines.append(f"  - ❌ {e}")
    if qg["warnings"]:
        lines.append("- **警告项**：")
        for w in qg["warnings"]:
            lines.append(f"  - ⚠️ {w}")
    if decision.data_gaps:
        lines.append("- **数据缺口**（建议补齐后再评估）：")
        for g in decision.data_gaps:
            lines.append(f"  - 🔲 {g}")
    lines.append("")

    lines.append("---")
    lines.append("*本备忘录由「确定性计算」产出：所有数字可追溯来源；估值高低≠买卖信号；系统不执行任何真实交易。*")
    return "\n".join(lines)


# ============================================================================
# 监控清单 CSV 输出
# ============================================================================

def write_monitoring_csv(path: Path, indicators: list[MonitoringIndicator]) -> None:
    """把监控清单写成 CSV，直接能粘到 Excel"""
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "indicator_id", "name", "why_it_matters", "frequency",
            "current_value", "unit", "warn_threshold", "direction",
            "applies_to_scenarios",
        ])
        for mi in indicators:
            writer.writerow([
                mi.indicator_id,
                mi.name,
                mi.why_it_matters,
                mi.frequency,
                "" if mi.current_value is None else mi.current_value,
                mi.unit,
                "" if mi.warn_threshold is None else mi.warn_threshold,
                mi.direction,
                " | ".join(mi.applies_to_scenarios),
            ])


# ============================================================================
# 主流程
# ============================================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="双标的换仓决策 V1 - 金标准评估")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "artifacts_golden"),
                        help="制品输出目录（默认 ./artifacts_golden）")
    parser.add_argument("--verbose", action="store_true", help="打印调试信息")
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] 构造金标准输入：阳光电源 → 海光信息")
    a, b, pref = build_golden_inputs()
    if args.verbose:
        print(f"  A 基本面：rev={a.revenue} 亿, ni={a.net_income} 亿, roe={a.roe:.1%}")
        print(f"  B 基本面：rev={b.revenue} 亿, ni={b.net_income} 亿, roe={b.roe:.1%}")

    print(f"[2/5] 构建 12 维度同口径比较矩阵")
    builder = ComparisonMatrixBuilder()
    matrix = builder.build(a, b, common_as_of=datetime.now(timezone.utc).isoformat())
    print(f"  维度数 = {len(matrix.rows)}；完整度 = {matrix.overall_completeness:.0%}；"
          f" 降级维度 = {matrix.degraded_dimension_count}；"
          f" 时点差 = {matrix.temporal_alignment_hours:.1f} h")

    print(f"[3/5] 生成四方案决策情景")
    planner = ScenarioPlanner()
    decision = planner.generate_scenarios(matrix, pref)
    print(f"  方案数 = {len(decision.scenarios)}；"
          f" 推荐 = {decision.recommended}（{decision.confidence_level}置信）；"
          f" 监控指标 = {len(decision.monitoring_indicators)}")

    print(f"[4/5] 运行独立质量门")
    qg = run_quality_gate(matrix, decision)
    if qg["passed"]:
        print("  ✅ 独立质量门通过")
    else:
        print("  ❌ 独立质量门未通过：")
        for e in qg["critical_errors"]:
            print(f"     - {e}")
    for w in qg["warnings"]:
        print(f"     ⚠️ {w}")

    print(f"[5/5] 写出 4 个制品文件到 {out_dir}")
    cm_path = out_dir / "comparison_matrix.json"
    ds_path = out_dir / "decision_scenarios.json"
    md_path = out_dir / "decision_memo.md"
    csv_path = out_dir / "monitoring_list.csv"
    cm_path.write_text(
        json.dumps(matrix, default=_json_default, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ds_path.write_text(
        json.dumps(decision, default=_json_default, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(render_memo_md(matrix, decision, qg), encoding="utf-8")
    write_monitoring_csv(csv_path, decision.monitoring_indicators)
    repo_root = PROJECT_ROOT.parent  # 可能输出目录在项目外（如 ../artifacts_golden）
    for p in (cm_path, ds_path, md_path, csv_path):
        try:
            rel = p.relative_to(PROJECT_ROOT)
        except ValueError:
            try:
                rel = p.relative_to(repo_root)
            except ValueError:
                rel = p
        print(f"  - {rel}  ({p.stat().st_size:,} bytes)")

    print("")
    print("=" * 64)
    print(f"ALL OK (passed={qg['passed']}, recommended={decision.recommended}, "
          f"confidence={decision.confidence_level})")
    print("=" * 64)
    return 0 if qg["passed"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
