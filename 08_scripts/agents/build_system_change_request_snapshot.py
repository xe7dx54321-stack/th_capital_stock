#!/usr/bin/env python3
"""Build business-driven system change requests from coverage gaps and fetch failures."""

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, ensure_auto_handoff, get_profile, profile_workspace_path
from smr_official_intel import parse_official_intel_target_registry
from smr_paths import project_path, relative_to_project
from smr_public_analyst_signals import parse_public_analyst_signal_target_registry
from smr_public_transcripts import parse_public_transcript_target_registry
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import load_ranked_equity_targets
from smr_wiki import ensure_source_manifest_table, now_ts

SCRIPT_NAME = "build_system_change_request_snapshot.py"
POLICY_PATH = project_path("00_control", "engineering_autonomy_policy.json")
PUBLIC_TRANSCRIPT_REGISTRY_PATH = project_path("00_control", "public_transcript_target_registry.md")
PUBLIC_ANALYST_SIGNAL_REGISTRY_PATH = project_path("00_control", "public_analyst_signal_target_registry.md")
OFFICIAL_INTEL_REGISTRY_PATH = project_path("00_control", "official_intel_target_registry.md")

FETCH_SOURCE_TO_FAMILY = {
    "fetch_public_transcripts_fool.py": "public_transcript",
    "fetch_marketscreener_analyst_signals.py": "public_analyst_signal",
    "fetch_ir_primary_materials.py": "official_material",
    "fetch_sec_official_materials.py": "official_material",
}

FAMILY_CONFIG = {
    "public_transcript": {
        "label": "公开电话会文字稿",
        "registry_rel_path": relative_to_project(PUBLIC_TRANSCRIPT_REGISTRY_PATH),
        "source_kinds": {"public_transcript"},
        "suggested_files": [
            "00_control/public_transcript_target_registry.md",
            "08_scripts/lib/smr_public_transcripts.py",
            "08_scripts/wiki/fetch_public_transcripts_fool.py",
        ],
        "required_work": [
            "核对目标注册表里的匹配关键词、符号映射和 provider 配置。",
            "必要时补深分页、备用匹配规则或替代公开文字稿来源。",
            "把稳定抓取路径沉淀回 fetch 脚本和目标注册表。",
        ],
        "acceptance_checks": [
            "目标注册表配置完整，target_key 和 entity_id 能被脚本正确选中。",
            "单标的重跑 fetch_public_transcripts_fool.py 后，能新增 public_transcript 源文件或明确证明当前源不可得。",
            "build_source_manifest.py 刷新后，source_manifest 能看到对应 public_transcript 记录。",
        ],
    },
    "public_analyst_signal": {
        "label": "公开卖方信号",
        "registry_rel_path": relative_to_project(PUBLIC_ANALYST_SIGNAL_REGISTRY_PATH),
        "source_kinds": {"public_analyst_signal"},
        "suggested_files": [
            "00_control/public_analyst_signal_target_registry.md",
            "08_scripts/lib/smr_public_analyst_signals.py",
            "08_scripts/wiki/fetch_marketscreener_analyst_signals.py",
        ],
        "required_work": [
            "核对共识页 URL、页面结构和字段提取规则。",
            "如果站点结构变化，补 parser 容错和字段回退逻辑。",
            "把成功抓到的摘要继续沉淀回 source_manifest。",
        ],
        "acceptance_checks": [
            "单标的重跑 fetch_marketscreener_analyst_signals.py 后，能稳定抓到评级、目标价区间和覆盖分析师数量。",
            "生成的 external_source_snapshot 在 source_manifest 中可见。",
        ],
    },
    "official_material": {
        "label": "官方一手材料",
        "registry_rel_path": relative_to_project(OFFICIAL_INTEL_REGISTRY_PATH),
        "source_kinds": {
            "ir_landing_page",
            "ir_material_page",
            "ir_material_pdf",
            "sec_filing_document",
            "sec_earnings_material",
            "sec_submissions_json",
        },
        "suggested_files": [
            "00_control/official_intel_target_registry.md",
            "08_scripts/lib/smr_official_intel.py",
            "08_scripts/wiki/fetch_ir_primary_materials.py",
            "08_scripts/wiki/fetch_sec_official_materials.py",
        ],
        "required_work": [
            "补齐目标注册表中的 IR URL，必要时补 SEC Symbol 和关键词配置。",
            "验证 IR 页面或 SEC 路径是否能稳定落 raw external 快照。",
            "把可复用的发现规则沉淀回 official_intel helper。",
        ],
        "acceptance_checks": [
            "单标的重跑 fetch_ir_primary_materials.py 或 fetch_sec_official_materials.py 后，能在 raw external 目录看到官方源快照。",
            "build_source_manifest.py 刷新后，source_manifest 能看到对应 official source 记录。",
        ],
    },
}

PRIORITY_RANK = {"高": 0, "中": 1, "低": 2}
POOL_PRIORITY_RANK = {"portfolio_seed": 0, "recommended": 1, "candidate": 2, "watchlist": 3, "seed": 4}


def active_registry_rows():
    return {
        "public_transcript": [row for row in parse_public_transcript_target_registry() if row.get("enabled")],
        "public_analyst_signal": [row for row in parse_public_analyst_signal_target_registry() if row.get("enabled")],
        "official_material": [row for row in parse_official_intel_target_registry() if row.get("enabled")],
    }


def target_maps(registry_rows):
    maps = {}
    for family, rows in registry_rows.items():
        by_key = {row["target_key"]: row for row in rows}
        by_entity = defaultdict(list)
        for row in rows:
            by_entity[row["entity_id"]].append(row)
        maps[family] = {"by_key": by_key, "by_entity": by_entity}
    return maps


def load_universe(conn):
    rows = load_ranked_equity_targets(
        conn,
        pool_types=["portfolio_seed", "recommended", "candidate", "watchlist"],
        allowed_markets=["SH", "SZ", "BJ", "HK", "US"],
        limit=64,
    )
    return {row["ts_code"]: row for row in rows}


def load_source_coverage(conn):
    ensure_source_manifest_table(conn)
    coverage = defaultdict(lambda: defaultdict(int))
    rows = conn.execute(
        """
        SELECT entity_id, json_extract(metadata_json, '$.source_kind') AS source_kind, COUNT(*)
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
        GROUP BY entity_id, source_kind
        """
    ).fetchall()
    for entity_id, source_kind, count in rows:
        if not entity_id or not source_kind:
            continue
        coverage[str(entity_id)][str(source_kind)] = int(count or 0)
    return coverage


def latest_fetch_failures(conn):
    placeholders = ",".join("?" for _ in FETCH_SOURCE_TO_FAMILY)
    rows = conn.execute(
        f"""
        SELECT source, entity_type, entity_id, payload_json, created_at
        FROM task_registry_entry
        WHERE source IN ({placeholders})
        ORDER BY datetime(created_at) DESC, id DESC
        """,
        tuple(FETCH_SOURCE_TO_FAMILY.keys()),
    ).fetchall()

    latest_by_source = {}
    for source, entity_type, entity_id, payload_json, created_at in rows:
        if source in latest_by_source:
            continue
        payload = json.loads(payload_json or "{}")
        latest_by_source[source] = {
            "source": source,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload": payload,
            "created_at": created_at,
        }
    return latest_by_source


def family_coverage_count(coverage, family, entity_id):
    source_kinds = FAMILY_CONFIG[family]["source_kinds"]
    entity_counts = coverage.get(str(entity_id), {})
    return sum(entity_counts.get(source_kind, 0) for source_kind in source_kinds)


def pool_rank(pool_types):
    ordered = [POOL_PRIORITY_RANK.get(pool_type, 99) for pool_type in (pool_types or [])]
    return min(ordered) if ordered else 99


def build_registry_onboarding_requests(universe, registry_rows):
    requests = []
    official_entity_ids = {row["entity_id"] for row in registry_rows["official_material"]}
    for item in universe.values():
        if item.get("market") not in {"HK", "US"}:
            continue
        entity_id = item["ts_code"]
        if entity_id in official_entity_ids:
            continue
        primary_pool = item.get("primary_pool_type") or ""
        priority = "高" if primary_pool in {"portfolio_seed", "recommended"} else "中"
        requests.append(
            {
                "task_key": f"official_material__{entity_id}__registry_onboarding_gap",
                "entity_id": entity_id,
                "ts_code": entity_id,
                "name": item.get("name") or entity_id,
                "family": "official_material",
                "family_label": FAMILY_CONFIG["official_material"]["label"],
                "gap_type": "registry_onboarding_gap",
                "priority": priority,
                "priority_rank": PRIORITY_RANK[priority],
                "pool_rank": pool_rank(item.get("pool_types")),
                "summary": (
                    f"{item.get('name') or entity_id} 已经进入当前股票池，但还没进入官方高价值信息源目标注册表，"
                    "系统暂时无法按统一口径去拉 IR / SEC 一手材料。"
                ),
                "suggested_files": list(FAMILY_CONFIG["official_material"]["suggested_files"]),
                "required_work": list(FAMILY_CONFIG["official_material"]["required_work"]),
                "acceptance_checks": list(FAMILY_CONFIG["official_material"]["acceptance_checks"]),
                "evidence": [
                    {
                        "type": "pool_membership",
                        "market": item.get("market"),
                        "pool_types": item.get("pool_types") or [],
                        "sector": item.get("sector"),
                        "score": item.get("score"),
                    },
                    {
                        "type": "registry_state",
                        "registry_rel_path": FAMILY_CONFIG["official_material"]["registry_rel_path"],
                        "covered": False,
                    },
                ],
            }
        )
    return requests


def build_source_coverage_requests(registry_rows, coverage, suppressed_keys):
    requests = []
    for family, rows in registry_rows.items():
        for target in rows:
            entity_id = target["entity_id"]
            if (family, entity_id) in suppressed_keys:
                continue
            if family_coverage_count(coverage, family, entity_id) > 0:
                continue
            priority = "高" if target.get("status") == "live" else "中"
            requests.append(
                {
                    "task_key": f"{family}__{entity_id}__source_coverage_gap",
                    "entity_id": entity_id,
                    "ts_code": entity_id,
                    "name": target.get("company_name") or entity_id,
                    "family": family,
                    "family_label": FAMILY_CONFIG[family]["label"],
                    "gap_type": "source_coverage_gap",
                    "priority": priority,
                    "priority_rank": PRIORITY_RANK[priority],
                    "pool_rank": 50,
                    "summary": (
                        f"{target.get('company_name') or entity_id} 已经进入 {FAMILY_CONFIG[family]['label']} 目标注册表，"
                        "但 source_manifest 里还没有任何落地源，说明抓取链还没有真正打通。"
                    ),
                    "suggested_files": list(FAMILY_CONFIG[family]["suggested_files"]),
                    "required_work": list(FAMILY_CONFIG[family]["required_work"]),
                    "acceptance_checks": list(FAMILY_CONFIG[family]["acceptance_checks"]),
                    "evidence": [
                        {
                            "type": "registry_target",
                            "target_key": target.get("target_key"),
                            "registry_rel_path": FAMILY_CONFIG[family]["registry_rel_path"],
                            "status": target.get("status"),
                            "enabled": bool(target.get("enabled")),
                        },
                        {
                            "type": "manifest_state",
                            "covered_count": 0,
                            "source_kinds": sorted(FAMILY_CONFIG[family]["source_kinds"]),
                        },
                    ],
                }
            )
    return requests


def build_fetch_failure_requests(latest_failures, coverage, target_lookup):
    requests = []
    suppressed_keys = set()
    for source, result in latest_failures.items():
        family = FETCH_SOURCE_TO_FAMILY[source]
        failures = result["payload"].get("failures") or []
        for failure in failures:
            entity_id = str(failure.get("entity_id") or "").strip()
            if not entity_id:
                continue
            covered_count = family_coverage_count(coverage, family, entity_id)
            error_text = str(failure.get("error") or "").strip()
            if "no_transcript_found_within_" in error_text and covered_count > 0:
                continue
            target = target_lookup[family]["by_key"].get(failure.get("target_key")) or (
                target_lookup[family]["by_entity"].get(entity_id) or [{}]
            )[0]
            priority = "高" if target.get("status") == "live" or covered_count == 0 else "中"
            requests.append(
                {
                    "task_key": f"{family}__{entity_id}__fetch_failure",
                    "entity_id": entity_id,
                    "ts_code": entity_id,
                    "name": target.get("company_name") or entity_id,
                    "family": family,
                    "family_label": FAMILY_CONFIG[family]["label"],
                    "gap_type": "fetch_failure",
                    "priority": priority,
                    "priority_rank": PRIORITY_RANK[priority],
                    "pool_rank": 20,
                    "summary": (
                        f"{target.get('company_name') or entity_id} 最近一次 {FAMILY_CONFIG[family]['label']} 抓取失败，"
                        "需要系统侧排查匹配规则、入口稳定性或抓取路径。"
                    ),
                    "suggested_files": list(FAMILY_CONFIG[family]["suggested_files"]),
                    "required_work": list(FAMILY_CONFIG[family]["required_work"]),
                    "acceptance_checks": list(FAMILY_CONFIG[family]["acceptance_checks"]),
                    "evidence": [
                        {
                            "type": "fetch_failure",
                            "source_script": source,
                            "created_at": result["created_at"],
                            "target_key": failure.get("target_key"),
                            "error": error_text,
                            "url": failure.get("url") or failure.get("article_url"),
                        },
                        {
                            "type": "manifest_state",
                            "covered_count": covered_count,
                            "source_kinds": sorted(FAMILY_CONFIG[family]["source_kinds"]),
                        },
                    ],
                }
            )
            suppressed_keys.add((family, entity_id))
    return requests, suppressed_keys


def sort_requests(requests):
    return sorted(
        requests,
        key=lambda item: (
            item.get("priority_rank", 99),
            item.get("pool_rank", 99),
            item.get("family", ""),
            item.get("ts_code", ""),
        ),
    )


def unique_requests(requests, limit):
    seen = set()
    results = []
    for item in requests:
        if item["task_key"] in seen:
            continue
        seen.add(item["task_key"])
        results.append(item)
        if limit is not None and len(results) >= limit:
            break
    return results


def render_summary(snapshot_date, generated_at, policy_rel_path, requests):
    lines = [
        f"# 系统施工请求快照：{snapshot_date}",
        "",
        f"- generated_at: `{generated_at}`",
        f"- batch_date: `{snapshot_date}`",
        f"- request_count: `{len(requests)}`",
        "- focus_strategy: `业务驱动 + 受控自进化`",
        f"- policy_rel_path: `{policy_rel_path}`",
        "",
        "## 当前结论",
        "",
    ]
    if not requests:
        lines.extend(
            [
                "- 当前没有发现需要升级成系统施工单的业务缺口。",
                "- 这不代表系统已经完美，只表示本轮没有触发受控工程链。",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"- 本轮共识别出 `{len(requests)}` 个系统施工请求，优先处理高优先级和持仓参照层相关缺口。",
            "- 这些请求现在只会进入候选层，不会直接自动改真相层代码。",
            "",
            "## 请求清单",
            "",
        ]
    )
    for index, item in enumerate(requests, start=1):
        lines.extend(
            [
                f"### {index}. {item['name']} / {item['ts_code']}",
                "",
                f"- family: `{item['family']}` / `{item['family_label']}`",
                f"- gap_type: `{item['gap_type']}`",
                f"- priority: `{item['priority']}`",
                f"- summary: {item['summary']}",
                "",
                "#### 建议改动文件",
                "",
            ]
        )
        for rel_path in item.get("suggested_files") or []:
            lines.append(f"- `{rel_path}`")
        lines.extend(
            [
                "",
                "#### 必要施工",
                "",
            ]
        )
        for text in item.get("required_work") or []:
            lines.append(f"- {text}")
        lines.extend(
            [
                "",
                "#### 验收检查",
                "",
            ]
        )
        for text in item.get("acceptance_checks") or []:
            lines.append(f"- {text}")
        lines.extend(
            [
                "",
                "#### 证据",
                "",
            ]
        )
        for evidence in item.get("evidence") or []:
            lines.append(f"- `{evidence.get('type')}`: {json.dumps(evidence, ensure_ascii=False, sort_keys=True)}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build system_change_request snapshot")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    registry_rows = active_registry_rows()
    target_lookup = target_maps(registry_rows)
    coverage = load_source_coverage(conn)
    universe = load_universe(conn)
    failure_requests, suppressed_keys = build_fetch_failure_requests(
        latest_fetch_failures(conn),
        coverage,
        target_lookup,
    )
    requests = [
        *failure_requests,
        *build_registry_onboarding_requests(universe, registry_rows),
        *build_source_coverage_requests(registry_rows, coverage, suppressed_keys),
    ]
    requests = unique_requests(sort_requests(requests), args.limit)

    profile = get_profile("hermes_engineering_planner")
    workspace = profile_workspace_path(profile)
    request_dir = workspace / "requests"
    summary_path = request_dir / f"{args.date}__system_change_request.md"
    summary_rel_path = relative_to_project(summary_path)
    policy_rel_path = relative_to_project(POLICY_PATH)
    generated_at = now_ts()

    entry_payload = {
        "request_count": len(requests),
        "focus_strategy": "business_driven_guarded_evolution",
        "summary_rel_path": summary_rel_path,
        "policy_rel_path": policy_rel_path,
        "requests": requests,
    }

    if args.dry_run:
        print(json.dumps(entry_payload, ensure_ascii=False, indent=2))
        conn.close()
        return

    request_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        render_summary(args.date, generated_at, policy_rel_path, requests) + "\n",
        encoding="utf-8",
    )

    entry = register_snapshot(
        conn,
        entity_type="system_change_request",
        entity_id=args.date,
        status="open" if requests else "clear",
        source=SCRIPT_NAME,
        relationships={
            "summary_rel_path": summary_rel_path,
            "policy_rel_path": policy_rel_path,
        },
        payload=entry_payload,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        entry,
        note="检测到业务驱动系统缺口，转交系统施工执行代理生成候选施工方案。",
        created_by=SCRIPT_NAME,
    )
    conn.commit()
    conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "system change request snapshot built",
        {
            "date": args.date,
            "request_count": len(requests),
            "summary_rel_path": summary_rel_path,
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"System change request snapshot: {summary_path}")
    print(f"  request_count={len(requests)}")
    print(f"  registry_entry_id={entry['id']}")
    if handoff_result["handoff"]:
        print(
            f"  handoff={handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"  handoff={handoff_result['reason']}")


if __name__ == "__main__":
    main()
