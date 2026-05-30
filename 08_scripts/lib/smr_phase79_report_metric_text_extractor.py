#!/usr/bin/env python3
import re
SMART_UNITS = {
    "元": 1.0, "万元": 10000.0, "亿元": 100000000.0,
    "万": 10000.0, "亿": 100000000.0,
    "万元人民币": 10000.0, "亿元人民币": 100000000.0
}
def normalize_unit(value_raw, unit_hint=None):
    if not value_raw: return (None, None)
    raw_str = str(value_raw).strip()
    if raw_str.endswith("%") or "%" in raw_str:
        num = re.sub(r"[%%, ]", "", raw_str)
        try: return (float(num), "%")
        except: return (None, "%")
    for unit_name, multiplier in sorted(SMART_UNITS.items(), key=lambda x: -len(x[0])):
        if raw_str.endswith(unit_name):
            num_part = raw_str[:-len(unit_name)].strip()
            try:
                num = float(num_part.replace(",", "").replace("，", ""))
                return (num, unit_name)
            except: pass
    try:
        num = float(raw_str.replace(",", "").replace("，", ""))
        return (num, unit_hint or "元")
    except: return (None, unit_hint or "未识别")

def normalize_period(period_text):
    if not period_text: return "unknown"
    p = str(period_text).strip()
    if "2024" in p and ("年度" in p or "年报" in p or "全年" in p):
        return "2024FY"
    if "2023" in p and ("年度" in p or "年报" in p or "全年" in p):
        return "2023FY"
    if "2025" in p and ("三季" in p or "第三季" in p or "Q3" in p or "三季度" in p):
        return "2025Q3_YTD"
    if "2025" in p and ("一季" in p or "第一季" in p or "Q1" in p or "一季度" in p):
        return "2025Q1"
    if "招股" in p or "IPO" in p or "发行" in p:
        return "prospectus_historical"
    return "unknown"

def assign_confidence(extraction_method, has_span_hash, is_table_nearby):
    if extraction_method == "direct_match" and has_span_hash:
        return "high"
    elif extraction_method == "direct_match":
        return "medium"
    elif extraction_method == "context_inferred":
        return "low"
    return "low"

def extract_metrics_from_text(text, metric_aliases, report_title="", report_type=""):
    results = []
    period_label = normalize_period(report_title or report_type)
    for metric_name, aliases in metric_aliases.items():
        for alias in aliases:
            pattern = re.escape(alias)
            m = re.search(pattern, text[:50000])
            if m:
                start = m.end()
                context = text[start:start+200]
                num_match = re.search(r"[-+]?\d[\d,，.]*\s*(?:万?亿?元|%)", context)
                value_raw = num_match.group(0) if num_match else "not_found"
                val, unit = normalize_unit(value_raw)
                span_hash = f"sha256:{alias}"
                confidence = assign_confidence("direct_match", True, False)
                results.append({
                    "metric_name": metric_name,
                    "metric_alias": alias,
                    "value_raw": value_raw,
                    "value_normalized": val,
                    "unit_normalized": unit,
                    "period": period_label,
                    "period_type": "annual" if "FY" in period_label else ("quarterly" if "Q" in period_label else "prospectus_historical"),
                    "source_section": "extracted_from_text",
                    "extraction_confidence": confidence,
                    "span_hash": span_hash
                })
                break
    return results
