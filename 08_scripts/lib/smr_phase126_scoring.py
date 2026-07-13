import re
import sqlite3
from smr_paths import env_or_project_path

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")


def _extract_signal_source(rec_id):
    """
    【功能】从 recommendation_id 中提取信号源前缀，用于按信号源分组统计。

    【参数】
    - rec_id: recommendation_id 字符串，如 "phase14_thesis_aware__NVDA__ai_infrastructure_demand"

    【返回值】信号源前缀字符串，如 "phase14_thesis"

    【异常处理】无（纯字符串操作，不会抛异常）

    【用小白的话术讲解】
    recommendation_id 就像一条决策记录的"身份证号"，前缀部分（如 phase14_thesis）
    代表这条决策是哪个信号源产出的。这个函数就是把身份证号的前缀抠出来，方便
    按信号源分组统计准确率。
    """
    m = re.match(r'^(phase\d+_[a-z0-9]+)', str(rec_id))
    return m.group(1) if m else str(rec_id).split('_')[0]


def build_scoring():
    """
    【功能】
    Phase 126 信号有效性复盘的打分与推荐生成函数。
    读取 decision_ledger 表中决策的实际 outcome 表现（thesis_confirmed /
    outcome_status / outcome_price 等），从三个维度动态评估各信号源的
    有效性，并生成动态推荐（如某信号源预测准确率低→降低权重）。

    用小白的话术讲解：
    想象你是投资经理，每个月要复盘："我之前推荐的股票，哪些逻辑被验证了？
    哪些被打脸了？哪些信号源靠谱？哪些要降权？"这个函数就是帮你自动做这件事。
    它会从数据库里把所有决策记录捞出来，分三个维度算一算，然后给出建议。

    【参数】无

    【返回值】
    dict，结构与原 build_scoring() 一致（避免破坏调用方）：
    {
        "phase126_scoring": {
            "recommendations": [...],       # 动态生成的推荐列表
            "recommendations_created": int, # 推荐总数
            "trade_actions": 0,             # 始终为 0（research_only 模式）
            "no_trade_adjustment": True,    # 始终为 True（不触发交易）
            "mock_used": False,
            "fixture_used": False
        }
    }
    每条推荐的结构：{"type": ..., "item": ..., "direction": ..., "reason": ...}

    【异常处理】
    - 数据库连接失败：返回一条"数据库不可用"的推荐，不抛异常
    - 表查询失败：返回一条"表查询失败"的推荐，不抛异常
    - 数据不足（thesis_confirmed 全为 NULL 等）：返回一条"数据不足"的推荐
    - 任何异常都不会传播到调用方，保证 phase126 管道不被 scoring 步骤中断
    """
    # 默认返回结构（保持与原 build_scoring 一致，避免破坏调用方）
    result = {
        "phase126_scoring": {
            "recommendations": [],
            "recommendations_created": 0,
            "trade_actions": 0,
            "no_trade_adjustment": True,
            "mock_used": False,
            "fixture_used": False,
        }
    }

    # --- 第 0 步：连接数据库 ---
    # 用小白的话术：先试着连上数据库，连不上就返回"数据库不可用"的提示
    try:
        conn = sqlite3.connect(str(DB_PATH))
    except Exception:
        result["phase126_scoring"]["recommendations"].append({
            "type": "data_availability",
            "item": "decision_ledger_db",
            "direction": "unavailable",
            "reason": "数据库不可用，暂无法评估信号有效性"
        })
        result["phase126_scoring"]["recommendations_created"] = 1
        return result

    # --- 第 1 步：读取 decision_ledger 全量数据 ---
    # 用小白的话术：把所有决策记录都捞出来，准备做统计
    try:
        rows = conn.execute(
            """
            SELECT recommendation_id, status, thesis_confirmed, outcome_status,
                   outcome_price_1m, outcome_price_3m, reference_price, outcome_price_1d
            FROM decision_ledger
            """
        ).fetchall()
    except Exception:
        result["phase126_scoring"]["recommendations"].append({
            "type": "data_availability",
            "item": "decision_ledger_table",
            "direction": "unavailable",
            "reason": "decision_ledger 表查询失败，暂无法评估信号有效性"
        })
        result["phase126_scoring"]["recommendations_created"] = 1
        return result
    finally:
        # 无论查询成功还是失败，都关闭数据库连接（好习惯，避免连接泄漏）
        try:
            conn.close()
        except Exception:
            pass

    recommendations = []
    total_records = len(rows)

    # --- 维度 1：信号源准确率 ---
    # 用小白的话术：按信号源分组，看每个信号源"猜对了几次、猜错了几次"。
    # 准确率 = 猜对次数 / (猜对次数 + 猜错次数)
    # 准确率 < 50% → 建议降低该信号源权重（不靠谱）
    # 准确率 > 70% → 建议提升该信号源权重（很靠谱）
    source_stats = {}  # {source: {"confirmed": int, "failed": int, "total": int}}
    for rec_id, _status, thesis_confirmed, _outcome_status, _p1m, _p3m, _ref, _p1d in rows:
        source = _extract_signal_source(rec_id)
        if source not in source_stats:
            source_stats[source] = {"confirmed": 0, "failed": 0, "total": 0}
        source_stats[source]["total"] += 1
        if thesis_confirmed == 1:
            source_stats[source]["confirmed"] += 1
        elif thesis_confirmed == 0:
            source_stats[source]["failed"] += 1

    for source, stats in source_stats.items():
        judged = stats["confirmed"] + stats["failed"]
        if judged == 0:
            # 该信号源暂无已判定数据（thesis_confirmed 全为 NULL），跳过
            continue
        accuracy = stats["confirmed"] / judged
        if accuracy < 0.5:
            recommendations.append({
                "type": "source_weight",
                "item": source,
                "direction": "decrease",
                "reason": f"准确率 {accuracy:.0%}（{stats['confirmed']}/{judged}），建议降低该信号源权重"
            })
        elif accuracy > 0.7:
            recommendations.append({
                "type": "source_weight",
                "item": source,
                "direction": "increase",
                "reason": f"准确率 {accuracy:.0%}（{stats['confirmed']}/{judged}），建议提升该信号源权重"
            })

    # --- 维度 2：outcome_status 分布 ---
    # 用小白的话术：看所有决策的最终结果分布——多少成功、多少失败、多少还在观察。
    # 失败占比 > 30% → 建议加强风控筛选（亏太多了）
    # 确认占比 > 50% → 建议扩大该类信号应用（赚得不错）
    status_counts = {"confirmed": 0, "failed": 0, "partially_confirmed": 0, "open": 0}
    for _rec_id, _status, _thesis, outcome_status, _p1m, _p3m, _ref, _p1d in rows:
        if outcome_status in status_counts:
            status_counts[outcome_status] += 1
        else:
            status_counts[outcome_status] = status_counts.get(outcome_status, 0) + 1

    if total_records > 0:
        failed_ratio = status_counts.get("failed", 0) / total_records
        confirmed_ratio = status_counts.get("confirmed", 0) / total_records
        if failed_ratio > 0.3:
            recommendations.append({
                "type": "risk_control",
                "item": "global",
                "direction": "strengthen",
                "reason": f"失败占比 {failed_ratio:.0%}（{status_counts['failed']}/{total_records}），建议加强风控筛选"
            })
        if confirmed_ratio > 0.5:
            recommendations.append({
                "type": "signal_application",
                "item": "global",
                "direction": "expand",
                "reason": f"确认占比 {confirmed_ratio:.0%}（{status_counts['confirmed']}/{total_records}），建议扩大该类信号应用"
            })

    # --- 维度 3：平均收益率 ---
    # 用小白的话术：对有 1 个月价格数据的决策，算一下平均涨跌幅。
    # 平均收益率 < 0 → 建议重新评估选股逻辑（选的股票整体在跌）
    # 平均收益率 > 5% → 建议维持当前选股策略（选得不错，继续）
    return_rates = []
    for _rec_id, _status, _thesis, _outcome_status, p1m, _p3m, ref, p1d in rows:
        if p1m is None:
            continue
        # 参考价：优先用 reference_price，没有则回退到 outcome_price_1d
        base_price = ref if (ref is not None and ref > 0) else p1d
        if base_price is None or base_price <= 0:
            continue
        return_rates.append((p1m - base_price) / base_price)

    if return_rates:
        avg_return = sum(return_rates) / len(return_rates)
        if avg_return < 0:
            recommendations.append({
                "type": "selection_logic",
                "item": "global",
                "direction": "reassess",
                "reason": f"平均 1m 收益率 {avg_return:.2%}（{len(return_rates)} 条），建议重新评估选股逻辑"
            })
        elif avg_return > 0.05:
            recommendations.append({
                "type": "selection_logic",
                "item": "global",
                "direction": "maintain",
                "reason": f"平均 1m 收益率 {avg_return:.2%}（{len(return_rates)} 条），建议维持当前选股策略"
            })

    # --- 兜底规则：数据不足时返回"数据不足"推荐 ---
    # 用小白的话术：如果三个维度都没产出任何推荐（比如所有决策都还在观察期，
    # thesis_confirmed 全是 NULL，outcome_price_1m 也都没有），就返回一条
    # "数据不足"的提示，而不是返回硬编码的假推荐。
    if not recommendations:
        recommendations.append({
            "type": "data_availability",
            "item": "decision_ledger_outcome",
            "direction": "insufficient",
            "reason": (
                f"decision_ledger 共 {total_records} 条记录，但 thesis_confirmed/outcome_status "
                f"均为待观察状态，outcome_price_1m 数据不足，暂无法生成有效性评估推荐"
            )
        })

    result["phase126_scoring"]["recommendations"] = recommendations
    result["phase126_scoring"]["recommendations_created"] = len(recommendations)
    return result
