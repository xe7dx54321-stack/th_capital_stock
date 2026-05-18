#!/usr/bin/env python3
"""Build table-oriented Eastmoney report snapshots from article/pdf-text sources."""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import persist_external_snapshot, truncate_text
from smr_paths import env_or_project_path, project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import resolve_equity_targets
from smr_wiki import slugify

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")

HEADER_TABLE_TITLES = (
    "盈利预测与估值",
    "预测指标",
    "公司盈利预测",
    "公司盈利预测（百万元）",
)
LABEL_FIRST_TABLE_TITLES = (
    "盈利预测和财务指标",
    "财务数据与估值",
    "附表：盈利预测",
)
TABLE_STOP_MARKERS = (
    "投资要点",
    "风险提示",
    "资料来源",
    "股价走势",
    "市场数据",
    "基础数据",
    "附一：",
    "资产负债表",
    "请阅读最后一页重要免责声明",
    "【投资评等说明】",
)
YEAR_TOKEN_RE = re.compile(r"^20\d{2}[A-Z]?$")
VALUE_TOKEN_RE = re.compile(r"^[+\-]?\d[\d,]*(?:\.\d+)?%?$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CERTIFICATE_RE = re.compile(r"[A-Z]\d{10,18}")
PHONE_RE = re.compile(r"(?:\+?\d{2,4}-\d{6,8}|\d{3,4}-\d{6,8}|\d{7,12})")


def normalize_text(text):
    return " ".join(str(text or "").replace("\u3000", " ").split())


def normalize_lines(text):
    lines = []
    prepared = re.sub(r"(\[Table_[^\]]+\])", r"\n\1\n", str(text or ""))
    prepared = prepared.replace("资料来源：", "\n资料来源：")
    prepared = prepared.replace("注：", "\n注：")
    for raw_line in prepared.splitlines():
        line = normalize_text(raw_line)
        if line:
            lines.append(line)
    return lines


def slug_source_id(provider, ts_code, info_code):
    stable_key = f"{ts_code}_{info_code}"
    return f"external_source__{slugify(provider)}__{slugify(stable_key)[:120]}"


def snapshot_exists_on_disk(ts_code, info_code, source_kind):
    entity_dir = project_path("11_smr_wiki", "raw", "external", "stock", slugify(ts_code))
    if not entity_dir.exists():
        return False
    pattern = f"*/{slugify(info_code)}__{slugify(source_kind)}__*.meta.json"
    return any(entity_dir.glob(pattern))


def snapshot_exists(conn, ts_code, info_code, provider, source_kind):
    row = conn.execute(
        """
        SELECT 1
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND source_id=?
        LIMIT 1
        """,
        (ts_code, slug_source_id(provider, ts_code, info_code)),
    ).fetchone()
    if row is not None:
        return True
    return snapshot_exists_on_disk(ts_code, info_code, source_kind)


def resolve_targets(conn, args):
    return resolve_equity_targets(
        conn,
        explicit_ts_codes=args.ts_code,
        profile_name=args.profile,
        pool_types=args.pool_type,
        allowed_markets=["SZ", "SH", "BJ"],
        limit=args.limit,
    )


def query_external_rows(conn, ts_code, source_kind, limit):
    rows = conn.execute(
        """
        SELECT source_rel_path, metadata_json, created_at, updated_at
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind')=?
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_id DESC
        LIMIT ?
        """,
        (ts_code, source_kind, limit),
    ).fetchall()
    results = []
    for source_rel_path, metadata_json, created_at, updated_at in rows:
        manifest_meta = json.loads(metadata_json or "{}")
        meta_rel_path = manifest_meta.get("meta_rel_path")
        if not meta_rel_path:
            continue
        meta_path = project_path(meta_rel_path)
        source_path = project_path(source_rel_path)
        if (not meta_path.exists()) or (not source_path.exists()):
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["_meta_rel_path"] = meta_rel_path
        meta["_source_rel_path"] = source_rel_path
        meta["_created_at"] = created_at
        meta["_updated_at"] = updated_at
        results.append(meta)
    return results


def is_year_token(token):
    return bool(YEAR_TOKEN_RE.match(normalize_text(token)))


def is_value_token(token):
    return bool(VALUE_TOKEN_RE.match(normalize_text(token).replace(" ", "")))


def parse_numeric_token(token):
    cleaned = normalize_text(token).replace(",", "").replace("%", "")
    return float(cleaned)


def contains_stop_marker(line):
    normalized = normalize_text(line)
    return any(marker in normalized for marker in TABLE_STOP_MARKERS)


def collect_window_after_title(lines, title_index, max_lines=90):
    window = []
    for line in lines[title_index + 1 :]:
        if contains_stop_marker(line):
            break
        window.append(line)
        if len(window) >= max_lines:
            break
    return window


def collect_relaxed_window_after_title(lines, title_index, max_lines=150):
    strong_stop_markers = ("投资要点", "风险提示", "请务必阅读", "证券研究报告", "内容目录", "相关研究")
    window = []
    for line in lines[title_index + 1 :]:
        normalized = normalize_text(line)
        if any(marker in normalized for marker in strong_stop_markers):
            break
        window.append(line)
        if len(window) >= max_lines:
            break
    return window


def build_segments(tokens):
    segments = []
    current_tokens = []
    current_type = None
    for token in tokens:
        token_type = "value" if is_value_token(token) else "label"
        if current_tokens and token_type != current_type:
            segments.append({"type": current_type, "tokens": current_tokens})
            current_tokens = []
        current_type = token_type
        current_tokens.append(token)
    if current_tokens:
        segments.append({"type": current_type, "tokens": current_tokens})
    return segments


def canonicalize_metric_label(raw_label, previous_key=None):
    normalized = normalize_text(raw_label).replace(" ", "")
    normalized_upper = normalized.upper()
    normalized = normalized.replace("(+/-%)", "同比").replace("（+/-%）", "同比")
    if normalized == "Margin" and previous_key and previous_key.startswith("other_ebit"):
        normalized = "EBITMargin"
    if "营业总收入" in normalized or "主营收入" in normalized or "营业收入" in normalized:
        return "revenue_million"
    if "归母净利润" in normalized or "归母净利" in normalized or "纯利" in normalized or "净利润" in normalized:
        return "net_profit_million"
    if "EPS" in normalized or "每股盈余" in normalized or "摊薄每股收益" in normalized:
        return "eps_yuan"
    if "P/E" in normalized or "市盈率" in normalized or normalized == "PE":
        return "pe_multiple"
    if "ROE" in normalized:
        return "roe_percent"
    if "DPS" in normalized or "股利" in normalized:
        return "dps_yuan"
    if "Yield" in normalized or "股息率" in normalized:
        return "yield_percent"
    if "P/B" in normalized or "市净率" in normalized or normalized == "PB":
        return "pb_multiple"
    if "毛利率" in normalized:
        return "gross_margin_percent"
    if "净利率" in normalized:
        return "net_margin_percent"
    if "同比" in normalized or "增长率" in normalized:
        if previous_key == "revenue_million":
            return "revenue_yoy_percent"
        if previous_key == "net_profit_million":
            return "net_profit_yoy_percent"
        if previous_key == "eps_yuan":
            return "eps_yoy_percent"
        return "growth_percent"
    if "YOY" in normalized_upper:
        if previous_key == "revenue_million":
            return "revenue_yoy_percent"
        if previous_key == "net_profit_million":
            return "net_profit_yoy_percent"
        if previous_key == "eps_yuan":
            return "eps_yoy_percent"
        return "growth_percent"
    return f"other_{slugify(normalized)[:40] or 'metric'}"


def normalize_label_sequence(raw_labels):
    normalized = []
    index = 0
    while index < len(raw_labels):
        current = normalize_text(raw_labels[index])
        nxt = normalize_text(raw_labels[index + 1]) if index + 1 < len(raw_labels) else ""
        compact_current = current.replace(" ", "")
        compact_next = nxt.replace(" ", "")
        if compact_current == "EBIT" and compact_next == "Margin":
            normalized.append("EBIT Margin")
            index += 2
            continue
        normalized.append(current)
        index += 1
    return normalized


def make_rows(raw_labels, existing_rows=None):
    existing_rows = existing_rows or []
    raw_labels = normalize_label_sequence(raw_labels)
    rows = []
    seen_keys = {row["metric_key"] for row in existing_rows}
    previous_key = existing_rows[-1]["base_key"] if existing_rows else None
    for raw_label in raw_labels:
        base_key = canonicalize_metric_label(raw_label, previous_key=previous_key)
        metric_key = base_key
        suffix = 2
        while metric_key in seen_keys:
            metric_key = f"{base_key}__{suffix}"
            suffix += 1
        row = {
            "label": raw_label,
            "base_key": base_key,
            "metric_key": metric_key,
            "values": {},
            "filled_years": 0,
        }
        rows.append(row)
        seen_keys.add(metric_key)
        previous_key = base_key
    return rows


def update_row_filled_years(row, years):
    filled = 0
    for year in years:
        if year in row["values"]:
            filled += 1
        else:
            break
    row["filled_years"] = filled


def common_filled_years(rows):
    if not rows:
        return None
    filled_values = {row["filled_years"] for row in rows}
    if len(filled_values) != 1:
        return None
    return next(iter(filled_values))


def assign_row_major(rows, raw_values, years):
    if len(raw_values) != len(rows) * len(years):
        return None
    assignments = []
    index = 0
    for row in rows:
        values = {}
        for year in years:
            values[year] = parse_numeric_token(raw_values[index])
            index += 1
        assignments.append({"row": row, "values": values})
    return assignments


def assign_column_major(rows, raw_values, years):
    if len(raw_values) != len(rows) * len(years):
        return None
    assignments = [{"row": row, "values": {}} for row in rows]
    index = 0
    for year in years:
        for assignment in assignments:
            assignment["values"][year] = parse_numeric_token(raw_values[index])
            index += 1
    return assignments


def merge_assignment_groups(*groups):
    merged = {}
    for group in groups:
        if not group:
            continue
        for assignment in group:
            metric_key = assignment["row"]["metric_key"]
            bucket = merged.setdefault(metric_key, {"row": assignment["row"], "values": {}})
            bucket["values"].update(assignment["values"])
    return list(merged.values())


def score_metric_value(metric_key, value):
    base_key = metric_key.split("__", 1)[0]
    if base_key in {"revenue_million", "net_profit_million"}:
        if abs(value) >= 100 and abs(value) <= 10000000:
            return 3
        return -6
    if base_key in {
        "revenue_yoy_percent",
        "net_profit_yoy_percent",
        "eps_yoy_percent",
        "roe_percent",
        "yield_percent",
        "growth_percent",
        "gross_margin_percent",
        "net_margin_percent",
    }:
        if abs(value) <= 1000:
            return 2
        return -6
    if base_key in {"eps_yuan", "dps_yuan"}:
        if abs(value) <= 300:
            return 3
        return -6
    if base_key == "pe_multiple":
        if 0 <= value <= 1000:
            return 3
        return -6
    if base_key == "pb_multiple":
        if 0 <= value <= 1000:
            return 2
        return -6
    return 0


def is_metric_label_token(token):
    normalized = normalize_text(token)
    if not normalized or is_year_token(normalized) or is_value_token(normalized):
        return False
    if normalized in {"会计年度", "年度截止"}:
        return False
    return not canonicalize_metric_label(normalized).startswith("other_")


def score_assignments(assignments, reference_series=None):
    total = 0
    reference_series = reference_series or {}
    for assignment in assignments or []:
        metric_key = assignment["row"]["metric_key"]
        base_key = assignment["row"]["base_key"]
        for value in assignment["values"].values():
            total += score_metric_value(metric_key, value)
        for year, value in assignment["values"].items():
            reference_value = reference_series.get(base_key, {}).get(year)
            if reference_value is None:
                continue
            diff_ratio = abs(value - reference_value) / max(abs(reference_value), 1.0)
            if diff_ratio <= 0.03:
                total += 10
            elif diff_ratio <= 0.10:
                total += 6
            elif diff_ratio <= 0.25:
                total += 2
            elif diff_ratio >= 0.50:
                total -= 6
    return total


def commit_assignments(assignments, years):
    for assignment in assignments or []:
        row = assignment["row"]
        row["values"].update(assignment["values"])
        update_row_filled_years(row, years)


def choose_best_full_layout(rows, raw_values, years, reference_series=None):
    row_major = assign_row_major(rows, raw_values, years)
    column_major = assign_column_major(rows, raw_values, years)
    candidates = []
    if row_major:
        candidates.append(("row_major", score_assignments(row_major, reference_series=reference_series), row_major))
    if column_major:
        candidates.append(("column_major", score_assignments(column_major, reference_series=reference_series), column_major))
    for split_index in range(1, len(years)):
        prefix_years = years[:split_index]
        suffix_years = years[split_index:]
        prefix_size = len(rows) * len(prefix_years)
        prefix_values = raw_values[:prefix_size]
        suffix_values = raw_values[prefix_size:]

        prefix_column = assign_column_major(rows, prefix_values, prefix_years)
        suffix_row = assign_row_major(rows, suffix_values, suffix_years)
        if prefix_column and suffix_row:
            mixed = merge_assignment_groups(prefix_column, suffix_row)
            candidates.append(
                (
                    f"column_then_row:{split_index}",
                    score_assignments(mixed, reference_series=reference_series),
                    mixed,
                )
            )

        prefix_row = assign_row_major(rows, prefix_values, prefix_years)
        suffix_column = assign_column_major(rows, suffix_values, suffix_years)
        if prefix_row and suffix_column:
            mixed = merge_assignment_groups(prefix_row, suffix_column)
            candidates.append(
                (
                    f"row_then_column:{split_index}",
                    score_assignments(mixed, reference_series=reference_series),
                    mixed,
                )
            )

    for year_prefix in range(1, len(years)):
        leading_years = years[:year_prefix]
        trailing_years = years[year_prefix:]
        leading_size = len(rows) * len(leading_years)
        leading_values = raw_values[:leading_size]
        for row_prefix in range(1, len(rows)):
            middle_size = row_prefix * len(trailing_years)
            trailing_size = (len(rows) - row_prefix) * len(trailing_years)
            middle_start = leading_size
            trailing_start = leading_size + middle_size

            leading_assignments = assign_column_major(rows, leading_values, leading_years)
            middle_assignments = assign_row_major(rows[:row_prefix], raw_values[middle_start:trailing_start], trailing_years)
            trailing_assignments = assign_column_major(rows[row_prefix:], raw_values[trailing_start:], trailing_years)
            if leading_assignments and middle_assignments and trailing_assignments:
                mixed = merge_assignment_groups(leading_assignments, middle_assignments, trailing_assignments)
                candidates.append(
                    (
                        f"column_then_row_prefix_then_column:{year_prefix}:{row_prefix}",
                        score_assignments(mixed, reference_series=reference_series),
                        mixed,
                    )
                )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[1], item[0] == "row_major"), reverse=True)
    return candidates[0]


def build_row_series(rows):
    return {row["metric_key"]: row["values"] for row in rows if row["values"]}


def parse_header_table(lines, search_item=None):
    candidates = []
    for title_index, line in enumerate(lines):
        title = next((item for item in HEADER_TABLE_TITLES if item in line), None)
        if not title:
            continue

        window = collect_window_after_title(lines, title_index)
        if not window:
            continue

        years = []
        index = 0
        while index < len(window) and is_year_token(window[index]):
            years.append(window[index])
            index += 1
        if len(years) < 3:
            continue

        reference_series, _ = extract_search_item_metric_series(search_item or {}, years)

        tokens = window[index:]
        segments = build_segments(tokens)
        rows = []
        notes = []

        for segment_index in range(0, len(segments), 2):
            label_segment = segments[segment_index]
            if label_segment["type"] != "label":
                continue
            value_segment = segments[segment_index + 1] if segment_index + 1 < len(segments) else None

            old_rows = list(rows)
            new_rows = make_rows(label_segment["tokens"], existing_rows=rows)
            rows.extend(new_rows)

            if value_segment is None or value_segment["type"] != "value":
                continue

            raw_values = value_segment["tokens"]
            assigned = False

            if not old_rows:
                if len(raw_values) == len(new_rows) * len(years):
                    best = choose_best_full_layout(new_rows, raw_values, years, reference_series=reference_series)
                    if best:
                        notes.append(f"{new_rows[0]['metric_key']}.. full:{best[0]}")
                        commit_assignments(best[2], years)
                        assigned = True
                elif len(raw_values) % len(new_rows) == 0:
                    partial_years = len(raw_values) // len(new_rows)
                    if 0 < partial_years < len(years):
                        assignments = assign_column_major(new_rows, raw_values, years[:partial_years])
                        if assignments:
                            notes.append(f"{new_rows[0]['metric_key']}.. partial:column_major:{partial_years}")
                            commit_assignments(assignments, years)
                            assigned = True
            else:
                filled_years = common_filled_years(old_rows)
                if len(raw_values) == len(new_rows) * len(years):
                    best = choose_best_full_layout(new_rows, raw_values, years, reference_series=reference_series)
                    if best:
                        notes.append(f"{new_rows[0]['metric_key']}.. full:{best[0]}")
                        commit_assignments(best[2], years)
                        assigned = True
                elif filled_years is not None and 0 < filled_years < len(years):
                    special_length = filled_years * len(new_rows) + (len(years) - filled_years) * len(rows)
                    if len(raw_values) == special_length:
                        prefix_assignments = assign_row_major(new_rows, raw_values[: filled_years * len(new_rows)], years[:filled_years])
                        suffix_layout = choose_best_full_layout(
                            rows,
                            raw_values[filled_years * len(new_rows) :],
                            years[filled_years:],
                            reference_series=reference_series,
                        )
                        suffix_assignments = suffix_layout[2] if suffix_layout else None
                        if prefix_assignments and suffix_assignments and suffix_layout:
                            notes.append(f"{new_rows[0]['metric_key']}.. mixed:late_metric:{suffix_layout[0]}")
                            commit_assignments(prefix_assignments, years)
                            commit_assignments(suffix_assignments, years)
                            assigned = True
                    elif len(raw_values) == (len(years) - filled_years) * len(rows):
                        assignments = assign_column_major(rows, raw_values, years[filled_years:])
                        if assignments:
                            notes.append(f"{new_rows[0]['metric_key']}.. remaining:column_major")
                            commit_assignments(assignments, years)
                            assigned = True

            if not assigned:
                notes.append(
                    f"unparsed:{','.join(row['metric_key'] for row in new_rows)}:{len(raw_values)}"
                )

        metric_rows = [
            {"metric_key": row["metric_key"], "base_key": row["base_key"], "label": row["label"], "values": row["values"]}
            for row in rows
            if row["values"]
        ]
        filled_cells = sum(len(row["values"]) for row in rows)
        if not metric_rows:
            continue

        candidates.append(
            {
                "table_title": title,
                "pattern": "header_segmented",
                "years": years,
                "metric_rows": metric_rows,
                "filled_cells": filled_cells,
                "score": sum(score_metric_value(metric_row["metric_key"], value) for metric_row in metric_rows for value in metric_row["values"].values()),
                "raw_window_lines": window[:80],
                "notes": notes,
            }
        )

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["filled_cells"], item["score"]), reverse=True)
    return candidates[0]


def parse_header_late_metric_table(lines, search_item=None):
    candidates = []
    for title_index, line in enumerate(lines):
        title = next((item for item in HEADER_TABLE_TITLES if item in line), None)
        if not title:
            continue

        window = collect_window_after_title(lines, title_index)
        if not window:
            continue

        first_year_index = None
        for index, token in enumerate(window):
            if is_year_token(token):
                first_year_index = index
                break
        if first_year_index is None or first_year_index < 2:
            continue

        raw_labels = [token for token in window[:first_year_index] if is_metric_label_token(token)]
        rows = make_rows(raw_labels)
        if len(rows) < 3:
            continue

        years = []
        cursor = first_year_index
        while cursor < len(window) and is_year_token(window[cursor]):
            years.append(window[cursor])
            cursor += 1
        if len(years) < 3:
            continue

        remaining = window[cursor:]
        late_label_positions = [(index, token) for index, token in enumerate(remaining) if is_metric_label_token(token)]
        if len(late_label_positions) != 1:
            continue

        late_index, late_label = late_label_positions[0]
        leading_values = [token for token in remaining[:late_index] if is_value_token(token)]
        trailing_values = [token for token in remaining[late_index + 1 :] if is_value_token(token)]
        late_rows = make_rows([late_label], existing_rows=rows)
        all_rows = rows + late_rows
        reference_series, _ = extract_search_item_metric_series(search_item or {}, years[1:])

        expected_leading = len(rows) + (len(years) - 1) * len(all_rows)
        if len(leading_values) != expected_leading or len(trailing_values) < len(late_rows):
            continue

        assignments = []
        first_year = years[0]
        for row, raw_value in zip(rows, leading_values[: len(rows)]):
            assignments.append({"row": row, "values": {first_year: parse_numeric_token(raw_value)}})
        for row, raw_value in zip(late_rows, trailing_values[: len(late_rows)]):
            assignments.append({"row": row, "values": {first_year: parse_numeric_token(raw_value)}})

        future_values = leading_values[len(rows) :]
        future_layout_name = None
        future_assignments = None

        future_years = years[1:]
        if future_years and len(future_values) == len(future_years) + (len(all_rows) - 1) * len(future_years):
            first_row_assignments = [
                {"row": all_rows[0], "values": {year: parse_numeric_token(raw_value)}}
                for year, raw_value in zip(future_years, future_values[: len(future_years)])
            ]
            tail_layout = choose_best_full_layout(
                all_rows[1:],
                future_values[len(future_years) :],
                future_years,
                reference_series=reference_series,
            )
            if tail_layout:
                future_layout_name = f"row0_then_{tail_layout[0]}"
                future_assignments = merge_assignment_groups(first_row_assignments, tail_layout[2])

        if not future_assignments:
            future_layout = choose_best_full_layout(all_rows, future_values, future_years, reference_series=reference_series)
            if future_layout:
                future_layout_name = future_layout[0]
                future_assignments = future_layout[2]

        if not future_assignments:
            continue
        assignments = merge_assignment_groups(assignments, future_assignments)

        metric_rows = [
            {"metric_key": row["metric_key"], "base_key": row["base_key"], "label": row["label"], "values": assignment["values"]}
            for assignment in assignments
            for row in [assignment["row"]]
        ]
        if not metric_rows:
            continue

        candidates.append(
            {
                "table_title": title,
                "pattern": "header_late_metric",
                "years": years,
                "metric_rows": metric_rows,
                "filled_cells": sum(len(metric_row["values"]) for metric_row in metric_rows),
                "score": sum(score_metric_value(metric_row["metric_key"], value) for metric_row in metric_rows for value in metric_row["values"].values()),
                "raw_window_lines": window[:80],
                "notes": [f"late_metric:{late_label}", f"future_layout:{future_layout_name}", f"future_years:{','.join(years[1:])}"],
            }
        )

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["filled_cells"], item["score"]), reverse=True)
    return candidates[0]


def parse_year_block_rows(rows, year_blocks):
    committed = []
    for year, raw_values in year_blocks:
        if len(raw_values) != len(rows):
            continue
        assignments = []
        for row, raw_value in zip(rows, raw_values):
            assignments.append({"row": row, "values": {year: parse_numeric_token(raw_value)}})
        committed.append((year, assignments))
    return committed


def parse_label_first_row_then_year_blocks(rows, remaining):
    if len(remaining) < 4 or (not is_year_token(remaining[0])):
        return None

    first_year = remaining[0]
    cursor = 1
    first_year_values = []
    while cursor < len(remaining) and (not is_year_token(remaining[cursor])):
        if is_value_token(remaining[cursor]):
            first_year_values.append(remaining[cursor])
        cursor += 1

    future_years = []
    while cursor < len(remaining) and is_year_token(remaining[cursor]):
        future_years.append(remaining[cursor])
        cursor += 1

    tail_values = [token for token in remaining[cursor:] if is_value_token(token)]
    if len(future_years) < 2:
        return None

    expected = len(future_years) + (len(rows) - 1) * len(future_years)
    if len(tail_values) != expected:
        return None

    assignments = []
    leading_row = rows[0]
    for year, raw_value in zip(future_years, tail_values[: len(future_years)]):
        assignments.append({"row": leading_row, "values": {year: parse_numeric_token(raw_value)}})

    offset = len(future_years)
    for year_index, year in enumerate(future_years):
        block_start = offset + year_index * (len(rows) - 1)
        block_end = block_start + (len(rows) - 1)
        block_values = tail_values[block_start:block_end]
        for row, raw_value in zip(rows[1:], block_values):
            assignments.append({"row": row, "values": {year: parse_numeric_token(raw_value)}})

    return {
        "first_year": first_year,
        "first_year_values": first_year_values,
        "future_years": future_years,
        "assignments": merge_assignment_groups(assignments),
    }


def parse_label_first_table(lines, search_item=None):
    candidates = []
    for title_index, line in enumerate(lines):
        title = next((item for item in HEADER_TABLE_TITLES + LABEL_FIRST_TABLE_TITLES if item in line), None)
        if not title:
            continue

        window = collect_relaxed_window_after_title(lines, title_index)
        if not window:
            continue

        first_year_index = None
        for index, token in enumerate(window):
            if is_year_token(token):
                first_year_index = index
                break
        if first_year_index is None or first_year_index < 2:
            continue

        raw_labels = [token for token in window[:first_year_index] if (not is_value_token(token)) and (not contains_stop_marker(token))]
        rows = make_rows(raw_labels)
        if len(rows) < 3:
            continue

        reference_series, _ = extract_search_item_metric_series(search_item or {}, [])
        remaining = window[first_year_index:]

        year_list = []
        list_cursor = 0
        while list_cursor < len(remaining) and is_year_token(remaining[list_cursor]):
            year_list.append(remaining[list_cursor])
            list_cursor += 1

        notes = []
        if len(year_list) >= 3:
            value_tokens = [token for token in remaining[list_cursor:] if is_value_token(token)]
            if len(value_tokens) == len(rows) * len(year_list):
                best = choose_best_full_layout(rows, value_tokens, year_list, reference_series=reference_series)
                if best:
                    notes.append(f"{rows[0]['metric_key']}.. label_first_full:{best[0]}")
                    commit_assignments(best[2], year_list)

        if not any(row["values"] for row in rows):
            mixed_layout = parse_label_first_row_then_year_blocks(rows, remaining)
            if mixed_layout:
                notes.append(
                    f"{rows[0]['metric_key']}.. label_first_row_then_year_blocks:{','.join(mixed_layout['future_years'])}"
                )
                commit_assignments(mixed_layout["assignments"], mixed_layout["future_years"])

        if not any(row["values"] for row in rows):
            year_blocks = []
            index = 0
            while index < len(remaining):
                token = remaining[index]
                if not is_year_token(token):
                    index += 1
                    continue
                year = token
                index += 1
                block_values = []
                while index < len(remaining) and (not is_year_token(remaining[index])):
                    if contains_stop_marker(remaining[index]):
                        break
                    if is_value_token(remaining[index]):
                        block_values.append(remaining[index])
                    index += 1
                year_blocks.append((year, block_values))

            committed = parse_year_block_rows(rows, year_blocks)
            for year, assignments in committed:
                notes.append(f"{year}:label_first_year_block")
                commit_assignments(assignments, [year])

        metric_rows = [
            {"metric_key": row["metric_key"], "base_key": row["base_key"], "label": row["label"], "values": row["values"]}
            for row in rows
            if row["values"]
        ]
        if not metric_rows:
            continue

        candidates.append(
            {
                "table_title": title,
                "pattern": "label_first",
                "years": sorted({year for metric_row in metric_rows for year in metric_row["values"]}),
                "metric_rows": metric_rows,
                "filled_cells": sum(len(row["values"]) for row in rows),
                "score": sum(score_metric_value(metric_row["metric_key"], value) for metric_row in metric_rows for value in metric_row["values"].values()),
                "raw_window_lines": window[:100],
                "notes": notes,
            }
        )

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["filled_cells"], item["score"]), reverse=True)
    return candidates[0]


def collect_fragmented_table_window(lines, title_index, max_lines=100):
    stop_markers = ("财务报表预测和估值数据汇总", "分析师承诺：")
    window = []
    for line in lines[title_index + 1 :]:
        normalized = normalize_text(line)
        if any(marker in normalized for marker in stop_markers):
            break
        window.append(line)
        if len(window) >= max_lines:
            break
    return window


def parse_fragmented_year_blocks_table(lines):
    candidates = []
    for title_index, line in enumerate(lines):
        title = next((item for item in LABEL_FIRST_TABLE_TITLES if item in line), None)
        if not title:
            continue

        window = collect_fragmented_table_window(lines, title_index)
        if not window:
            continue

        metric_labels = [token for token in window if is_metric_label_token(token)]
        rows = make_rows(metric_labels)
        if len(rows) < 5:
            continue

        notes = []
        for index, token in enumerate(window):
            if not is_year_token(token):
                continue

            years = [token]
            cursor = index + 1
            while cursor < len(window) and is_year_token(window[cursor]):
                years.append(window[cursor])
                cursor += 1

            value_tokens = []
            while cursor < len(window) and (not is_year_token(window[cursor])):
                current = window[cursor]
                if is_value_token(current):
                    value_tokens.append(current)
                    cursor += 1
                    continue
                if value_tokens:
                    break
                cursor += 1

            expected = len(rows) * len(years)
            if expected <= 0 or len(value_tokens) != expected:
                continue

            assignments = assign_column_major(rows, value_tokens, years)
            if not assignments:
                continue
            commit_assignments(assignments, years)
            notes.append(f"{','.join(years)}:fragmented_year_block")

        metric_rows = [
            {"metric_key": row["metric_key"], "base_key": row["base_key"], "label": row["label"], "values": row["values"]}
            for row in rows
            if row["values"]
        ]
        if not metric_rows:
            continue

        candidates.append(
            {
                "table_title": title,
                "pattern": "fragmented_year_blocks",
                "years": sorted({year for metric_row in metric_rows for year in metric_row["values"]}),
                "metric_rows": metric_rows,
                "filled_cells": sum(len(metric_row["values"]) for metric_row in metric_rows),
                "score": sum(score_metric_value(metric_row["metric_key"], value) for metric_row in metric_rows for value in metric_row["values"].values()),
                "raw_window_lines": window[:100],
                "notes": notes,
            }
        )

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["filled_cells"], item["score"]), reverse=True)
    return candidates[0]


def choose_footer_slice(rows, raw_values, year):
    row_count = len(rows)
    value_count = len(raw_values)
    if not rows or value_count > row_count:
        return None

    candidates = []
    for start in range(0, row_count - value_count + 1):
        selected_rows = rows[start : start + value_count]
        assignments = []
        for row, raw_value in zip(selected_rows, raw_values):
            assignments.append({"row": row, "values": {year: parse_numeric_token(raw_value)}})
        score = score_assignments(assignments)
        candidates.append((score, start, assignments))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0]


def parse_footer_table(lines):
    heading_index = None
    for index, line in enumerate(lines):
        if line.startswith("年度截止"):
            heading_index = index
            break
    if heading_index is None:
        return None

    label_start = heading_index + 1
    label_end = label_start
    while label_end < len(lines):
        line = lines[label_end]
        if contains_stop_marker(line) or line.startswith("评等定义"):
            break
        label_end += 1

    raw_labels = lines[label_start:label_end]
    if len(raw_labels) < 3:
        return None

    raw_rows = make_rows(raw_labels)
    max_value_count = 0
    year_blocks = []
    index = max(0, heading_index - 120)
    while index < heading_index:
        token = lines[index]
        if not is_year_token(token):
            index += 1
            continue
        year = token
        value_tokens = []
        cursor = index + 1
        while cursor < heading_index and not is_year_token(lines[cursor]):
            if is_value_token(lines[cursor]):
                value_tokens.append(lines[cursor])
            elif value_tokens:
                break
            cursor += 1
        if value_tokens:
            year_blocks.append({"year": year, "values": value_tokens, "position": index})
            max_value_count = max(max_value_count, len(value_tokens))
        index = cursor

    if len(year_blocks) < 3:
        return None

    value_rows = list(raw_rows)
    if max_value_count == len(raw_rows) - 1:
        pe_rows = [row for row in value_rows if row["base_key"] == "pe_multiple"]
        if pe_rows:
            value_rows = [row for row in value_rows if row["metric_key"] != pe_rows[0]["metric_key"]]

    notes = []
    for year_block in year_blocks:
        choice = choose_footer_slice(value_rows, year_block["values"], year_block["year"])
        if not choice:
            notes.append(f"unparsed:{year_block['year']}:{len(year_block['values'])}")
            continue
        notes.append(f"{year_block['year']}:slice:{choice[1]}")
        commit_assignments(choice[2], [year_block["year"]])

    metric_rows = [
        {"metric_key": row["metric_key"], "base_key": row["base_key"], "label": row["label"], "values": row["values"]}
        for row in raw_rows
        if row["values"]
    ]
    if not metric_rows:
        return None

    years = [item["year"] for item in year_blocks]
    return {
        "table_title": "年度截止表",
        "pattern": "footer_year_blocks",
        "years": years,
        "metric_rows": metric_rows,
        "filled_cells": sum(len(row["values"]) for row in raw_rows),
        "score": sum(score_metric_value(metric_row["metric_key"], value) for metric_row in metric_rows for value in metric_row["values"].values()),
        "raw_window_lines": lines[max(0, heading_index - 70) : min(len(lines), label_end + 2)],
        "notes": notes,
    }


def build_inline_pattern(metric_aliases, years):
    value_pattern = r"([+\-]?\d[\d,]*(?:\.\d+)?%?)"
    alias_pattern = "|".join(metric_aliases)
    return re.compile(
        rf"(?:{alias_pattern})\s+" + r"\s+".join([value_pattern] * len(years)),
        flags=re.IGNORECASE,
    )


def parse_inline_table(raw_text):
    candidates = []
    for tag_name in ("Table_Finance", "Table_FinanceDetail"):
        match = re.search(rf"\[{tag_name}\](.+?)(?:资料来源[:：]|\[Table_|\Z)", str(raw_text or ""), flags=re.S)
        if not match:
            continue
        segment = normalize_text(re.sub(r"\[Table_[^\]]+\]", " ", match.group(1)))
        years = []
        for token in re.findall(r"20\d{2}[A-Z]?", segment):
            if token not in years:
                years.append(token)
        if len(years) < 3:
            continue

        metric_specs = [
            ("revenue_million", "营业收入(百万元)", [r"营业收入\(百万元\)", r"营业总收入\(百万元\)", r"主营收入\(百万元\)"]),
            ("revenue_yoy_percent", "收入同比(%)", [r"收入同比\(%\)", r"营业收入\(%\)", r"营业收入增长率\(%\)", r"增长率\(%\)"]),
            ("net_profit_million", "归母净利润(百万元)", [r"归母净利润\(百万元\)", r"归属母公司净利润", r"净利润"]),
            ("net_profit_yoy_percent", "归母净利润同比(%)", [r"归母净利润同比\(%\)", r"归属母公司净利润\(%\)"]),
            ("roe_percent", "ROE(%)", [r"ROE\(%\)"]),
            ("eps_yuan", "每股收益(元)", [r"每股收益\(元\)", r"EPS（元）", r"EPS\(元\)", r"每股收益\(最新摊薄\)", r"每股收益"]),
            ("pe_multiple", "市盈率(P/E)", [r"市盈率\(P/E\)", r"P/E"]),
            ("pb_multiple", "市净率(PB)", [r"市净率\(PB\)", r"P/B"]),
        ]

        metric_rows = []
        for metric_key, label, aliases in metric_specs:
            pattern = build_inline_pattern(aliases, years)
            metric_match = pattern.search(segment)
            if not metric_match:
                continue
            values = {year: parse_numeric_token(raw_value) for year, raw_value in zip(years, metric_match.groups())}
            metric_rows.append(
                {
                    "metric_key": metric_key,
                    "base_key": metric_key,
                    "label": label,
                    "values": values,
                }
            )

        if not metric_rows:
            continue

        candidates.append(
            {
                "table_title": f"[{tag_name}]",
                "pattern": "inline_table_tag",
                "years": years,
                "metric_rows": metric_rows,
                "filled_cells": sum(len(metric_row["values"]) for metric_row in metric_rows),
                "score": sum(score_metric_value(metric_row["metric_key"], value) for metric_row in metric_rows for value in metric_row["values"].values()),
                "raw_window_lines": [truncate_text(segment, limit=2000)],
                "notes": [f"{tag_name}:regex_rows"],
            }
        )

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["filled_cells"], item["score"]), reverse=True)
    return candidates[0]


def choose_best_table(lines, raw_text=None, search_item=None):
    candidates = [
        candidate
        for candidate in (
            parse_inline_table(raw_text),
            parse_header_late_metric_table(lines, search_item=search_item),
            parse_header_table(lines, search_item=search_item),
            parse_label_first_table(lines, search_item=search_item),
            parse_fragmented_year_blocks_table(lines),
            parse_footer_table(lines),
        )
        if candidate
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["filled_cells"], item["score"]), reverse=True)
    return candidates[0]


def extract_search_item_metric_series(search_item, years):
    forecast_years = [year for year in years if year.endswith("E")]
    if not forecast_years and len(years) >= 3:
        forecast_years = years[-3:]

    metric_series = {"eps_yuan": {}, "pe_multiple": {}}
    metric_sources = {"eps_yuan": {}, "pe_multiple": {}}

    eps_values = [
        (key, search_item.get(key))
        for key in ("predictThisYearEps", "predictNextYearEps", "predictNextTwoYearEps")
        if search_item.get(key) not in (None, "")
    ]
    pe_values = [
        (key, search_item.get(key))
        for key in ("predictThisYearPe", "predictNextYearPe", "predictNextTwoYearPe")
        if search_item.get(key) not in (None, "")
    ]

    for year, (eps_key, eps_value) in zip(forecast_years, eps_values):
        try:
            metric_series["eps_yuan"][year] = float(eps_value)
            metric_sources["eps_yuan"][year] = f"search_item:{eps_key}"
        except ValueError:
            pass

    for year, (pe_key, pe_value) in zip(forecast_years, pe_values):
        try:
            metric_series["pe_multiple"][year] = float(pe_value)
            metric_sources["pe_multiple"][year] = f"search_item:{pe_key}"
        except ValueError:
            pass
    return metric_series, metric_sources


def merge_metric_series(table_candidate, search_item):
    table_series = {}
    metric_sources = {}
    for metric_row in table_candidate.get("metric_rows", []):
        table_series[metric_row["metric_key"]] = metric_row["values"]
        for year in metric_row["values"]:
            metric_sources.setdefault(metric_row["metric_key"], {})[year] = "forecast_table"

    fallback_series, fallback_sources = extract_search_item_metric_series(search_item, table_candidate.get("years", []))
    for metric_key, values in fallback_series.items():
        for year, value in values.items():
            if year not in table_series.get(metric_key, {}):
                table_series.setdefault(metric_key, {})[year] = value
                metric_sources.setdefault(metric_key, {})[year] = fallback_sources[metric_key][year]

    return table_series, metric_sources


def normalize_metric_series(metric_series):
    return {
        "revenue_billion": {year: round(value / 100.0, 4) for year, value in metric_series.get("revenue_million", {}).items()},
        "net_profit_billion": {year: round(value / 100.0, 4) for year, value in metric_series.get("net_profit_million", {}).items()},
        "eps_yuan": metric_series.get("eps_yuan", {}),
        "pe_multiple": metric_series.get("pe_multiple", {}),
        "roe_percent": metric_series.get("roe_percent", {}),
        "dps_yuan": metric_series.get("dps_yuan", {}),
        "yield_percent": metric_series.get("yield_percent", {}),
        "revenue_yoy_percent": metric_series.get("revenue_yoy_percent", {}),
        "net_profit_yoy_percent": metric_series.get("net_profit_yoy_percent", {}),
        "eps_yoy_percent": metric_series.get("eps_yoy_percent", {}),
    }


def parse_target_price_from_text(text):
    match = re.search(r"目标价[^\d]{0,8}([0-9]+(?:\.[0-9]+)?)", text or "")
    if not match:
        return None
    return float(match.group(1))


def parse_rating_block(lines, article_meta):
    search_item = article_meta.get("search_item") or {}
    rating_current = article_meta.get("rating_name") or search_item.get("emRatingName") or ""
    rating_action = ""
    raw_line = ""
    header_lines = lines[:20]
    for line in header_lines:
        if not any(token in line for token in ("买入", "买进", "增持", "推荐", "中性", "减持", "卖出", "Buy", "Neutral", "Trading Buy", "Strong Buy")):
            continue
        raw_line = line
        action_match = re.search(r"[（(]([^()（）]{1,8})[)）]", line)
        if action_match:
            rating_action = action_match.group(1)
        if not rating_current:
            rating_current = line
        break

    target_price = parse_target_price_from_text("\n".join(header_lines))
    if target_price is None:
        for key in ("indvAimPriceT", "indvAimPriceL"):
            value = search_item.get(key)
            if value not in (None, ""):
                try:
                    target_price = float(value)
                    break
                except ValueError:
                    pass

    return {
        "current": rating_current,
        "action": rating_action,
        "target_price_yuan": target_price,
        "raw_line": raw_line,
    }


def parse_analysts(lines):
    analysts = []
    current = None

    def flush():
        nonlocal current
        if not current:
            return
        if current.get("name") or current.get("email") or current.get("certificate_no"):
            analysts.append(current)
        current = None

    for index, line in enumerate(lines[:140]):
        email_match = EMAIL_RE.search(line)
        certificate_match = CERTIFICATE_RE.search(line)
        phone_match = PHONE_RE.search(line)
        if certificate_match and certificate_match.group(0) in line:
            phone_match = None

        name = None
        if line.startswith("证券分析师"):
            name = normalize_text(line.replace("证券分析师", ""))
        elif line.startswith("分析师："):
            name = normalize_text(line.split("：", 1)[1])
        elif index <= 5 and re.fullmatch(r"[\u4e00-\u9fff]{2,4}", line):
            name = line

        if name:
            flush()
            current = {"name": name, "certificate_no": "", "email": "", "phone": ""}
            continue

        if not current and (email_match or certificate_match or phone_match):
            current = {"name": "", "certificate_no": "", "email": "", "phone": ""}

        if current:
            if certificate_match and not current["certificate_no"]:
                current["certificate_no"] = certificate_match.group(0)
            if email_match and not current["email"]:
                current["email"] = email_match.group(0)
            if phone_match and not current["phone"]:
                current["phone"] = phone_match.group(0)

    flush()

    deduped = []
    seen = set()
    for analyst in analysts:
        signature = (
            analyst.get("name") or "",
            analyst.get("certificate_no") or "",
            analyst.get("email") or "",
        )
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(analyst)
    return deduped


def build_payload(target, article_meta, pdf_text_meta, lines, table_candidate):
    search_item = article_meta.get("search_item") or {}
    metric_series, metric_sources = merge_metric_series(table_candidate, search_item)
    rating = parse_rating_block(lines, article_meta)
    analysts = parse_analysts(lines)

    document = {
        "info_code": article_meta.get("info_code"),
        "ts_code": target["ts_code"],
        "stock_name": target["name"],
        "title": search_item.get("title") or article_meta.get("title") or "",
        "published_at": article_meta.get("published_at") or "",
        "org_name": article_meta.get("org_name") or "",
        "rating_name": article_meta.get("rating_name") or search_item.get("emRatingName") or "",
        "industry_name": search_item.get("indvInduName") or search_item.get("industryName") or "",
    }

    return {
        "schema_version": "smr_report_table_structured_v1",
        "provider": "eastmoney_report_table_structured",
        "document": document,
        "rating": rating,
        "analysts": analysts,
        "table_parse": {
            "table_title": table_candidate.get("table_title"),
            "pattern": table_candidate.get("pattern"),
            "years": table_candidate.get("years", []),
            "filled_cells": table_candidate.get("filled_cells", 0),
            "score": table_candidate.get("score", 0),
            "notes": table_candidate.get("notes", []),
            "raw_window_lines": table_candidate.get("raw_window_lines", []),
        },
        "forecast_table": {
            "metric_rows": table_candidate.get("metric_rows", []),
            "metric_series": metric_series,
            "metric_sources": metric_sources,
            "normalized_metrics": normalize_metric_series(metric_series),
        },
        "source_refs": {
            "article_markdown_rel_path": article_meta.get("_source_rel_path"),
            "article_meta_rel_path": article_meta.get("_meta_rel_path"),
            "pdf_text_markdown_rel_path": pdf_text_meta.get("_source_rel_path"),
            "pdf_text_meta_rel_path": pdf_text_meta.get("_meta_rel_path"),
            "pdf_text_raw_rel_path": pdf_text_meta.get("_raw_rel_path"),
            "detail_url": article_meta.get("source_url") or article_meta.get("requested_url") or "",
            "pdf_url": pdf_text_meta.get("source_url") or article_meta.get("attach_url") or "",
        },
    }


def build_body_text(payload):
    document = payload["document"]
    rating = payload["rating"]
    table_parse = payload["table_parse"]
    normalized = payload["forecast_table"]["normalized_metrics"]

    lines = [
        f"证券代码：{document['ts_code']}",
        f"证券简称：{document['stock_name']}",
        f"研报编号：{document['info_code']}",
        f"报告标题：{document['title']}",
        f"发布时间：{document['published_at'] or '-'}",
        f"发布机构：{document['org_name'] or '-'}",
        f"投资评级：{document['rating_name'] or '-'}",
        f"评级动作：{rating['action'] or '-'}",
        f"目标价：{rating['target_price_yuan'] if rating['target_price_yuan'] is not None else '-'}",
        f"表格模式：{table_parse['pattern'] or '-'}",
        f"表格标题：{table_parse['table_title'] or '-'}",
        f"年份：{', '.join(table_parse['years']) or '-'}",
    ]

    if payload["analysts"]:
        analyst_lines = []
        for analyst in payload["analysts"]:
            parts = [analyst.get("name") or "-"]
            if analyst.get("certificate_no"):
                parts.append(f"证书:{analyst['certificate_no']}")
            if analyst.get("email"):
                parts.append(f"邮箱:{analyst['email']}")
            if analyst.get("phone"):
                parts.append(f"电话:{analyst['phone']}")
            analyst_lines.append(" / ".join(parts))
        lines.extend(["", "分析师：", "\n".join(analyst_lines)])

    for title, metric_key in (
        ("营收预测(亿元)", "revenue_billion"),
        ("净利润预测(亿元)", "net_profit_billion"),
        ("营收同比(%)", "revenue_yoy_percent"),
        ("净利润同比(%)", "net_profit_yoy_percent"),
        ("EPS预测(元)", "eps_yuan"),
        ("PE预测(倍)", "pe_multiple"),
        ("ROE(%)", "roe_percent"),
        ("DPS(元)", "dps_yuan"),
        ("股息率(%)", "yield_percent"),
    ):
        series = normalized.get(metric_key, {})
        if series:
            lines.append(f"{title}：{json.dumps(series, ensure_ascii=False)}")

    if table_parse["notes"]:
        lines.extend(["", "解析备注：", "；".join(table_parse["notes"][:12])])

    return truncate_text("\n".join(lines), limit=12000)


def persist_table_structured_snapshot(target, article_meta, payload, fetched_at):
    info_code = article_meta["info_code"]
    published_at = normalize_text(article_meta.get("published_at"))
    bucket_date = (published_at[:10] if published_at else fetched_at[:10]) or fetched_at[:10]
    title = f"{target['ts_code']} 东方财富研报表格结构化 {payload['document']['title'] or info_code}"
    raw_bytes = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="research_table_structured",
        source_url=payload["source_refs"]["detail_url"] or payload["source_refs"]["pdf_url"],
        source_domain="data.eastmoney.com",
        content_type="application/json",
        raw_bytes=raw_bytes,
        raw_extension=".json",
        note=f"table-structured eastmoney report payload for {target['name']}",
        tags=["eastmoney", "public_research", "report_table_structured"],
        body_text=build_body_text(payload),
        metadata={
            "info_code": info_code,
            "published_at": published_at,
            "org_name": payload["document"]["org_name"],
            "rating_name": payload["document"]["rating_name"],
            "target_price_yuan": payload["rating"]["target_price_yuan"],
            "table_pattern": payload["table_parse"]["pattern"],
            "table_years": payload["table_parse"]["years"],
            "metric_keys": list(payload["forecast_table"]["metric_series"].keys()),
            "source_refs": payload["source_refs"],
        },
        extra_frontmatter={
            "provider": "eastmoney_report_table_structured",
            "announcement_id": f"{target['ts_code']}_{info_code}",
            "published_at": published_at,
            "org_name": payload["document"]["org_name"],
            "rating_name": payload["document"]["rating_name"],
            "info_code": info_code,
        },
        stable_key=info_code,
        bucket_date=bucket_date,
    )


def load_article_map(conn, ts_code, limit):
    rows = query_external_rows(conn, ts_code, "research_article", limit)
    mapping = {}
    for meta in rows:
        info_code = meta.get("info_code")
        if info_code:
            mapping[info_code] = meta
    return mapping


def load_pdf_text_rows(conn, ts_code, limit):
    rows = query_external_rows(conn, ts_code, "research_pdf_text", limit)
    results = []
    for meta in rows:
        raw_rel_path = meta.get("_raw_rel_path") or meta.get("raw_rel_path")
        if raw_rel_path:
            meta["_raw_rel_path"] = raw_rel_path
        results.append(meta)
    return results


def main():
    parser = argparse.ArgumentParser(description="Build table-structured Eastmoney report snapshots from existing article/pdf-text sources")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument("--report-limit", type=int, default=2, help="Maximum table-structured reports to build for each symbol")
    parser.add_argument("--force", action="store_true", help="Build even if the table-structured snapshot already exists")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    persisted = []
    skipped = []
    empty = []
    failed = []

    for target in targets:
        article_map = load_article_map(conn, target["ts_code"], args.report_limit * 4)
        pdf_rows = load_pdf_text_rows(conn, target["ts_code"], args.report_limit * 3)
        if not pdf_rows:
            empty.append({"ts_code": target["ts_code"], "reason": "missing_research_pdf_text_snapshot"})
            continue

        built_count = 0
        for pdf_text_meta in pdf_rows:
            if built_count >= args.report_limit:
                break

            info_code = pdf_text_meta.get("info_code") or ""
            if not info_code:
                failed.append({"ts_code": target["ts_code"], "error": "missing_info_code"})
                continue

            if (not args.force) and snapshot_exists(
                conn,
                target["ts_code"],
                info_code,
                provider="eastmoney_report_table_structured",
                source_kind="research_table_structured",
            ):
                skipped.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "already_exists"})
                continue

            article_meta = article_map.get(info_code)
            if not article_meta:
                failed.append({"ts_code": target["ts_code"], "info_code": info_code, "error": "missing_research_article_snapshot"})
                continue

            try:
                raw_rel_path = pdf_text_meta.get("_raw_rel_path")
                if not raw_rel_path:
                    raise ValueError("missing_pdf_text_raw_rel_path")
                raw_path = project_path(raw_rel_path)
                raw_text = raw_path.read_text(encoding="utf-8")
                lines = normalize_lines(raw_text)
                table_candidate = choose_best_table(
                    lines,
                    raw_text=raw_text,
                    search_item=article_meta.get("search_item") or {},
                )
                if not table_candidate:
                    empty.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "table_not_found"})
                    continue

                payload = build_payload(target, article_meta, pdf_text_meta, lines, table_candidate)
                snapshot = persist_table_structured_snapshot(target, article_meta, payload, fetched_at)
                persisted.append(
                    {
                        "ts_code": target["ts_code"],
                        "info_code": info_code,
                        "title": snapshot["title"],
                        "markdown_rel_path": snapshot["markdown_rel_path"],
                        "raw_rel_path": snapshot["raw_rel_path"],
                        "table_pattern": payload["table_parse"]["pattern"],
                        "filled_cells": payload["table_parse"]["filled_cells"],
                    }
                )
                built_count += 1
            except Exception as exc:
                failed.append({"ts_code": target["ts_code"], "info_code": info_code, "error": str(exc)})

    register_snapshot(
        conn,
        entity_type="eastmoney_report_table_structured_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="extract_eastmoney_report_table_structured.py",
        relationships={
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "report_limit": args.report_limit,
            "force": args.force,
        },
        payload={
            "persisted_count": len(persisted),
            "skipped_count": len(skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "skipped": skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "extract_eastmoney_report_table_structured.py",
        "success" if not failed else "warning",
        "eastmoney report table-structured snapshots built",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "report_limit": args.report_limit,
            "persisted_count": len(persisted),
            "skipped_count": len(skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "skipped": skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )

    print(f"Eastmoney report table-structured snapshots: {len(persisted)}")
    for item in persisted[:20]:
        print(f"- {item['ts_code']} | {item['info_code']} | {item['table_pattern']} -> {item['markdown_rel_path']}")
    if skipped:
        print("Skipped:")
        for item in skipped[:20]:
            print(f"- {item['ts_code']} | {item['info_code']}: {item['reason']}")
    if empty:
        print("Empty:")
        for item in empty[:20]:
            info_code = item.get("info_code", "-")
            print(f"- {item['ts_code']} | {info_code}: {item['reason']}")
    if failed:
        print("Failures:")
        for item in failed[:20]:
            print(f"- {item['ts_code']} | {item.get('info_code', '-')}: {item['error']}")


if __name__ == "__main__":
    main()
