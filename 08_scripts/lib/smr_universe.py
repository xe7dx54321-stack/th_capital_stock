#!/usr/bin/env python3
"""Shared SMR universe helpers for seed/current pools, portfolio holdings coverage, names, and sector mappings."""

import sqlite3

from smr_paths import project_path

WATCHLIST_PATH = project_path("00_control", "watchlist_registry.md")
PORTFOLIO_HOLDINGS_PATH = project_path("00_control", "portfolio_holdings_registry.md")
AMPLIFICATION_REGISTRY_PATH = project_path("00_control", "research_amplification_registry.md")
DEEP_ANALYSIS_THEME_REGISTRY_PATH = project_path("00_control", "deep_analysis_theme_registry.md")

REGISTRY_SPECS = (
    {"path": WATCHLIST_PATH, "seed_pool_type": "seed", "include_us": True},
    {"path": PORTFOLIO_HOLDINGS_PATH, "seed_pool_type": "portfolio_seed", "include_us": False},
)

DEFAULT_POOL_PRIORITY = (
    "recommended",
    "candidate",
    "watchlist",
    "portfolio_seed",
    "seed",
    "us_benchmark",
)

DEFAULT_RESEARCH_PROFILES = {
    "standard_external": {
        "profile": "standard_external",
        "enabled": True,
        "pool_types": ["recommended", "candidate"],
        "markets": ["SZ", "SH", "BJ"],
        "max_targets": 12,
        "description": "默认外部研究采集口径，优先高信号池。",
    },
    "amplified_external": {
        "profile": "amplified_external",
        "enabled": True,
        "pool_types": ["portfolio_seed", "recommended", "candidate", "watchlist", "seed"],
        "markets": ["SZ", "SH", "BJ"],
        "max_targets": 36,
        "description": "放大量级外部采集口径，覆盖持仓参照层和赛道覆盖层。",
    },
    "amplified_analysis": {
        "profile": "amplified_analysis",
        "enabled": True,
        "pool_types": ["portfolio_seed", "recommended", "candidate", "watchlist"],
        "markets": ["SZ", "SH", "BJ", "HK"],
        "max_targets": 24,
        "description": "放大量级分析口径，用于客观监控和策略跟踪。",
    },
}


def normalize_ah_code(raw_code, market):
    code = raw_code.strip()
    if market == "HK":
        return f"{code}.HK"
    if code.startswith(("0", "3")):
        return f"{code}.SZ"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    return f"{code}.SH"


def split_ts_code(ts_code):
    if "." not in ts_code:
        return ts_code, ""
    code, market = ts_code.split(".", 1)
    return code, market.upper()


def detect_market(ts_code):
    _code, market = split_ts_code(ts_code)
    return market


def relation_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def ordered_unique(values):
    seen = set()
    results = []
    for value in values or []:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        results.append(item)
    return results


def normalize_csv_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = value
    return ordered_unique(raw_items)


def parse_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "enabled", "active"}


def parse_int(value, default=None):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def parse_markdown_table(lines):
    table_lines = []
    in_table = False
    for raw_line in lines or []:
        stripped = raw_line.strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
            in_table = True
            continue
        if in_table:
            break

    if len(table_lines) < 2:
        return []

    headers = [part.strip() for part in table_lines[0].strip("|").split("|")]
    rows = []
    for raw_line in table_lines[2:]:
        if raw_line.startswith("|-"):
            continue
        parts = [part.strip() for part in raw_line.strip("|").split("|")]
        if len(parts) != len(headers):
            continue
        row = {header: part for header, part in zip(headers, parts)}
        if any(value for value in row.values()):
            rows.append(row)
    return rows


def parse_research_amplification_registry():
    result = {"profiles": {}, "sector_radar": []}
    if not AMPLIFICATION_REGISTRY_PATH.exists():
        return result

    sections = {}
    current_section = None
    current_lines = []
    for line in AMPLIFICATION_REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current_section is not None:
                sections[current_section] = current_lines
            current_section = line[3:].strip()
            current_lines = []
            continue
        if current_section is not None:
            current_lines.append(line)
    if current_section is not None:
        sections[current_section] = current_lines

    for row in parse_markdown_table(sections.get("Coverage Profiles", [])):
        profile = str(row.get("Profile") or "").strip()
        if not profile:
            continue
        result["profiles"][profile] = {
            "profile": profile,
            "enabled": parse_bool(row.get("Enabled")),
            "pool_types": normalize_csv_list(row.get("Pool Types")),
            "markets": [item.upper() for item in normalize_csv_list(row.get("Markets"))],
            "max_targets": parse_int(row.get("Max Targets")),
            "description": str(row.get("Description") or "").strip(),
        }

    for row in parse_markdown_table(sections.get("Sector Radar", [])):
        sector = str(row.get("Sector") or "").strip()
        if not sector:
            continue
        result["sector_radar"].append(
            {
                "sector": sector,
                "priority": parse_int(row.get("Priority"), default=99),
                "target_coverage": parse_int(row.get("Target Coverage"), default=0),
                "notes": str(row.get("Notes") or "").strip(),
            }
        )

    return result


def parse_deep_analysis_theme_registry():
    result = {"themes": {}, "targets": []}
    if not DEEP_ANALYSIS_THEME_REGISTRY_PATH.exists():
        return result

    sections = {}
    current_section = None
    current_lines = []
    for line in DEEP_ANALYSIS_THEME_REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current_section is not None:
                sections[current_section] = current_lines
            current_section = line[3:].strip()
            current_lines = []
            continue
        if current_section is not None:
            current_lines.append(line)
    if current_section is not None:
        sections[current_section] = current_lines

    for row in parse_markdown_table(sections.get("Themes", [])):
        theme_id = str(row.get("Theme") or "").strip()
        if not theme_id:
            continue
        result["themes"][theme_id] = {
            "theme": theme_id,
            "label": str(row.get("Label") or theme_id).strip(),
            "priority": parse_int(row.get("Priority"), default=99),
            "cadence_hours": parse_int(row.get("Cadence Hours"), default=12),
            "description": str(row.get("Description") or "").strip(),
        }

    for row in parse_markdown_table(sections.get("Targets", [])):
        ts_code = str(row.get("Ts Code") or "").strip()
        if not ts_code:
            continue
        result["targets"].append(
            {
                "ts_code": ts_code,
                "name": str(row.get("Name") or ts_code).strip(),
                "themes": normalize_csv_list(row.get("Themes")),
                "market": str(row.get("Market") or "").strip().upper(),
                "sector": str(row.get("Sector") or "").strip(),
                "role": str(row.get("Role") or "").strip(),
                "notes": str(row.get("Notes") or "").strip(),
            }
        )
    return result


def load_research_profile_map():
    profiles = {name: dict(config) for name, config in DEFAULT_RESEARCH_PROFILES.items()}
    parsed = parse_research_amplification_registry()
    for name, config in parsed.get("profiles", {}).items():
        merged = dict(profiles.get(name, {}))
        for key, value in config.items():
            if value is None:
                continue
            if key in {"pool_types", "markets"} and not value:
                continue
            if key == "description" and not value:
                continue
            merged[key] = value
        merged.setdefault("profile", name)
        profiles[name] = merged
    return profiles


def get_research_profile(profile_name=None):
    profiles = load_research_profile_map()
    requested_name = profile_name or "standard_external"
    profile = dict(profiles.get(requested_name, profiles["standard_external"]))
    profile.setdefault("profile", requested_name)
    profile.setdefault("enabled", True)
    profile.setdefault("pool_types", ["recommended", "candidate"])
    profile.setdefault("markets", ["SZ", "SH", "BJ"])
    profile.setdefault("max_targets", None)
    profile.setdefault("description", "")
    return profile


def build_pool_priority(pool_types=None):
    ordered = ordered_unique([*(pool_types or []), *DEFAULT_POOL_PRIORITY])
    return {pool_type: index for index, pool_type in enumerate(ordered)}


def parse_registry_file(path, seed_pool_type="seed", include_us=True):
    if not path.exists():
        return []

    current_market = None
    rows = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "## A股标的":
            current_market = "A"
            continue
        if stripped == "## H股标的":
            current_market = "HK"
            continue
        if stripped == "## 美股对标（仅跟踪，不投资）":
            current_market = "US"
            continue
        if not stripped.startswith("|"):
            continue
        if "Code" in stripped or "Symbol" in stripped or stripped.startswith("|------"):
            continue

        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if current_market == "US":
            if not include_us:
                continue
            if len(parts) != 4:
                continue
            symbol, name, sector, registry_added = parts
            rows.append(
                {
                    "pool_type": "us_benchmark",
                    "ts_code": symbol,
                    "name": name,
                    "sector": sector,
                    "market": "US",
                    "registry_added": registry_added,
                }
            )
            continue

        if len(parts) != 5 or current_market not in {"A", "HK"}:
            continue

        raw_code, name, sector, _pool_label, registry_added = parts
        rows.append(
            {
                "pool_type": seed_pool_type,
                "ts_code": normalize_ah_code(raw_code, current_market),
                "name": name,
                "sector": sector,
                "market": current_market,
                "registry_added": registry_added,
            }
        )

    return rows


def parse_registry_rows():
    rows = []
    for spec in REGISTRY_SPECS:
        rows.extend(
            parse_registry_file(
                spec["path"],
                seed_pool_type=spec["seed_pool_type"],
                include_us=spec["include_us"],
            )
        )
    return rows


def registry_name_map():
    return {row["ts_code"]: row["name"] for row in parse_registry_rows()}


def registry_equity_map():
    return {
        row["ts_code"]: row
        for row in parse_registry_rows()
        if row["pool_type"] in {"seed", "portfolio_seed"}
    }


def registry_us_benchmarks():
    return {
        row["ts_code"]: row
        for row in parse_registry_rows()
        if row["pool_type"] == "us_benchmark"
    }


def research_name_map(conn):
    if not relation_exists(conn, "research_index"):
        return {}

    rows = conn.execute(
        """
        SELECT ts_codes, title
        FROM research_index
        WHERE report_type IN ('stock', 'recommendation')
          AND instr(ts_codes, ',') = 0
        ORDER BY datetime(created_at) DESC
        """
    ).fetchall()

    names = {}
    for ts_code, title in rows:
        if not ts_code or ts_code in names or not title:
            continue
        names[ts_code] = title.split()[0]
    return names


def combined_name_map(conn=None):
    names = registry_name_map()
    if conn is not None:
        names.update({k: v for k, v in research_name_map(conn).items() if k not in names})
    return names


def build_target_sort_key(item):
    score = item.get("score")
    return (
        item.get("pool_rank", 999),
        score is None,
        -(score or 0.0),
        item.get("ts_code") or "",
    )


def finalize_ranked_targets(universe, priority_map):
    results = []
    for item in universe.values():
        ordered_pool_types = sorted(
            ordered_unique(item.get("pool_types") or []),
            key=lambda value: priority_map.get(value, 999),
        )
        item["pool_types"] = ordered_pool_types
        item["source_pool_types"] = ordered_pool_types
        item["primary_pool_type"] = ordered_pool_types[0] if ordered_pool_types else None
        if item.get("pool_rank") in (None, 999):
            item["pool_rank"] = priority_map.get(item.get("primary_pool_type"), 999)
        results.append(item)
    results.sort(key=build_target_sort_key)
    return results


def load_ranked_equity_targets(conn, pool_types=None, allowed_markets=None, limit=None):
    names = combined_name_map(conn)
    fallback = registry_equity_map()
    selected_pool_types = ordered_unique(pool_types or ["recommended", "candidate", "watchlist"])
    allowed_market_set = {market.upper() for market in (allowed_markets or []) if market}
    priority_map = build_pool_priority(selected_pool_types)
    universe = {}

    if relation_exists(conn, "stock_pool_current") and selected_pool_types:
        placeholders = ",".join("?" for _ in selected_pool_types)
        rows = conn.execute(
            f"""
            SELECT pool_type, ts_code, sector, score
            FROM stock_pool_current
            WHERE pool_type IN ({placeholders})
            """,
            selected_pool_types,
        ).fetchall()

        for pool_type, ts_code, sector, score in rows:
            market = detect_market(ts_code)
            if allowed_market_set and market not in allowed_market_set:
                continue

            fallback_meta = fallback.get(ts_code, {})
            entry = universe.setdefault(
                ts_code,
                {
                    "ts_code": ts_code,
                    "code": split_ts_code(ts_code)[0],
                    "market": market,
                    "name": names.get(ts_code, fallback_meta.get("name", split_ts_code(ts_code)[0])),
                    "sector": sector or fallback_meta.get("sector"),
                    "score": score,
                    "pool_types": [],
                    "pool_rank": priority_map.get(pool_type, 999),
                },
            )
            if sector and not entry.get("sector"):
                entry["sector"] = sector
            if score is not None and (entry.get("score") is None or score > entry["score"]):
                entry["score"] = score
            entry["pool_types"].append(pool_type)
            entry["pool_rank"] = min(entry.get("pool_rank", 999), priority_map.get(pool_type, 999))

        if universe:
            results = finalize_ranked_targets(universe, priority_map)
            return results[:limit] if limit is not None else results

    results = []
    for ts_code, meta in fallback.items():
        if selected_pool_types and meta["pool_type"] not in selected_pool_types:
            continue
        if allowed_market_set and meta["market"] not in allowed_market_set:
            continue
        results.append(
            {
                "ts_code": ts_code,
                "code": split_ts_code(ts_code)[0],
                "market": meta["market"],
                "name": names.get(ts_code, meta["name"]),
                "sector": meta["sector"],
                "score": None,
                "pool_types": [meta["pool_type"]],
                "source_pool_types": [meta["pool_type"]],
                "primary_pool_type": meta["pool_type"],
                "pool_rank": priority_map.get(meta["pool_type"], 999),
            }
        )

    results.sort(key=build_target_sort_key)
    return results[:limit] if limit is not None else results


def resolve_equity_targets(conn, explicit_ts_codes=None, profile_name=None, pool_types=None, allowed_markets=None, limit=None):
    profile = get_research_profile(profile_name)
    selected_pool_types = ordered_unique(pool_types or profile.get("pool_types") or [])
    selected_markets = [market.upper() for market in ordered_unique(allowed_markets or profile.get("markets") or [])]
    names = combined_name_map(conn)
    fallback = registry_equity_map()

    if explicit_ts_codes:
        meta_pool_types = selected_pool_types or list(DEFAULT_POOL_PRIORITY)
        meta_rows = load_ranked_equity_targets(
            conn,
            pool_types=meta_pool_types,
            allowed_markets=selected_markets,
            limit=None,
        )
        meta_map = {item["ts_code"]: item for item in meta_rows}
        priority_map = build_pool_priority(meta_pool_types)
        targets = []
        seen = set()
        for raw_ts_code in explicit_ts_codes:
            ts_code = str(raw_ts_code or "").strip()
            if not ts_code or ts_code in seen:
                continue
            seen.add(ts_code)
            code, market = split_ts_code(ts_code)
            if selected_markets and market.upper() not in selected_markets:
                continue
            if ts_code in meta_map:
                targets.append(dict(meta_map[ts_code]))
            else:
                fallback_meta = fallback.get(ts_code, {})
                pool_type = fallback_meta.get("pool_type")
                targets.append(
                    {
                        "ts_code": ts_code,
                        "code": code,
                        "market": market.upper(),
                        "name": names.get(ts_code, fallback_meta.get("name", code)),
                        "sector": fallback_meta.get("sector"),
                        "score": None,
                        "pool_types": ordered_unique([pool_type]) if pool_type else [],
                        "source_pool_types": ordered_unique([pool_type]) if pool_type else [],
                        "primary_pool_type": pool_type,
                        "pool_rank": priority_map.get(pool_type, 999),
                    }
                )
            if limit is not None and len(targets) >= limit:
                break
        return targets

    effective_limit = limit if limit is not None else profile.get("max_targets")
    return load_ranked_equity_targets(
        conn,
        pool_types=selected_pool_types,
        allowed_markets=selected_markets,
        limit=effective_limit,
    )


def load_active_equity_universe(conn, include_seed=True):
    names = combined_name_map(conn)
    fallback = registry_equity_map()

    if not relation_exists(conn, "stock_pool_current"):
        return {
            ts_code: {
                "name": meta["name"],
                "sector": meta["sector"],
                "market": meta["market"],
                "source_pool_types": [meta["pool_type"]],
            }
            for ts_code, meta in fallback.items()
        }

    pool_types = ["watchlist", "candidate", "recommended"]
    if include_seed:
        pool_types.extend(["seed", "portfolio_seed"])
    placeholders = ",".join("?" for _ in pool_types)
    rows = conn.execute(
        f"""
        SELECT pool_type, ts_code, sector
        FROM stock_pool_current
        WHERE pool_type IN ({placeholders})
        """,
        pool_types,
    ).fetchall()

    universe = {}
    for pool_type, ts_code, sector in rows:
        market = detect_market(ts_code)
        universe.setdefault(
            ts_code,
            {
                "name": names.get(ts_code, ts_code),
                "sector": sector or fallback.get(ts_code, {}).get("sector"),
                "market": market,
                "source_pool_types": [],
            },
        )
        universe[ts_code]["source_pool_types"].append(pool_type)

    if not universe:
        return {
            ts_code: {
                "name": meta["name"],
                "sector": meta["sector"],
                "market": meta["market"],
                "source_pool_types": [meta["pool_type"]],
            }
            for ts_code, meta in fallback.items()
        }

    return universe


def load_active_us_benchmarks(conn):
    names = combined_name_map(conn)
    fallback = registry_us_benchmarks()

    if not relation_exists(conn, "stock_pool_current"):
        return {
            symbol: {
                "name": meta["name"],
                "sector": meta["sector"],
                "market": "US",
            }
            for symbol, meta in fallback.items()
        }

    rows = conn.execute(
        """
        SELECT ts_code, sector
        FROM stock_pool_current
        WHERE pool_type='us_benchmark'
        """
    ).fetchall()

    benchmarks = {}
    for symbol, sector in rows:
        benchmarks[symbol] = {
            "name": names.get(symbol, fallback.get(symbol, {}).get("name", symbol)),
            "sector": sector or fallback.get(symbol, {}).get("sector"),
            "market": "US",
        }

    if not benchmarks:
        return {
            symbol: {
                "name": meta["name"],
                "sector": meta["sector"],
                "market": "US",
            }
            for symbol, meta in fallback.items()
        }

    return benchmarks


def load_sector_benchmark_map(conn):
    if relation_exists(conn, "sector_config"):
        rows = conn.execute(
            """
            SELECT sector_key, us_benchmarks
            FROM sector_config
            """
        ).fetchall()
        return {
            sector_key: [symbol.strip() for symbol in (us_benchmarks or "").split(",") if symbol.strip()]
            for sector_key, us_benchmarks in rows
        }

    result = {}
    for symbol, meta in registry_us_benchmarks().items():
        result.setdefault(meta["sector"], []).append(symbol)
    return result


def load_sector_equity_map(conn, include_seed=True):
    sector_map = {}
    for ts_code, meta in load_active_equity_universe(conn, include_seed=include_seed).items():
        sector_map.setdefault(meta["sector"], {})[ts_code] = meta
    return sector_map
