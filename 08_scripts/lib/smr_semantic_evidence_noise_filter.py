#!/usr/bin/env python3
"""Noise detection for semantic evidence candidates.

The filter is intentionally conservative: it only decides whether a candidate
is safe to persist. It never mutates the source text cache or semantic chunks.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


NOISE_TYPES = {
    "table_fragment",
    "ppt_title_only",
    "toc_fragment",
    "page_header_footer",
    "disclaimer",
    "legal_boilerplate",
    "financial_table_row_only",
    "numeric_fragment_only",
    "source_metadata_only",
    "short_span",
    "repeated_template",
    "unknown_noise",
}

REJECT_TYPES = {
    "table_fragment",
    "ppt_title_only",
    "toc_fragment",
    "page_header_footer",
    "disclaimer",
    "legal_boilerplate",
    "financial_table_row_only",
    "numeric_fragment_only",
    "source_metadata_only",
}


def _candidate_span(candidate: dict[str, Any] | str | None) -> str:
    if isinstance(candidate, str):
        return candidate
    if not candidate:
        return ""
    return str(candidate.get("quoted_span") or "")


def _source_title(candidate: dict[str, Any] | None) -> str:
    if not isinstance(candidate, dict):
        return ""
    payload = candidate.get("payload") or {}
    metadata = payload.get("source_metadata") or {}
    return str(metadata.get("title") or "")


def _section_type(candidate: dict[str, Any] | None) -> str:
    if not isinstance(candidate, dict):
        return ""
    payload = candidate.get("payload") or {}
    metadata = payload.get("source_metadata") or {}
    return str(metadata.get("section_type") or "")


def _cjk_or_alpha_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z\u4e00-\u9fff]", text))


def _digit_count(text: str) -> int:
    return len(re.findall(r"\d", text))


def _has_sentence_context(text: str) -> bool:
    stripped = text.strip()
    if re.search(r"[。！？!?；;]", stripped):
        return True
    if len(stripped) >= 28 and _cjk_or_alpha_count(stripped) >= 16:
        return True
    return False


def _is_ppt_like_title(title: str) -> bool:
    lowered = title.lower()
    return "ppt" in lowered or "演示" in title or "说明会" in title or "附件" in title


def _looks_like_slogan_or_title(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return False
    if re.fullmatch(r"([\w\u4e00-\u9fff]{1,8}\s*){1,4}", text):
        return True
    slogan_terms = ("使命", "愿景", "价值观", "解放生产力", "释放想象力", "美好世界")
    has_slogan_term = any(term in compact for term in slogan_terms)
    return has_slogan_term and len(compact) <= 34 and not re.search(r"[，,；;：:]", text)


def detect_noise(candidate: dict[str, Any] | str | None) -> dict[str, Any]:
    """Detect obvious non-evidence fragments in a candidate quoted span."""

    span = _candidate_span(candidate)
    text = re.sub(r"\s+", " ", span).strip()
    raw_lines = [line.strip() for line in span.splitlines() if line.strip()]
    title = _source_title(candidate if isinstance(candidate, dict) else None)
    section_type = _section_type(candidate if isinstance(candidate, dict) else None)

    noise_types: list[str] = []
    reasons: list[str] = []
    length = len(text)
    cjk_alpha = _cjk_or_alpha_count(text)
    digits = _digit_count(text)
    digit_ratio = digits / max(1, len(re.sub(r"\s+", "", text)))
    short_line_ratio = sum(1 for line in raw_lines if len(line) <= 12) / max(1, len(raw_lines))

    if not text:
        noise_types.append("source_metadata_only")
        reasons.append("quoted_span is missing or empty")
    if 0 < length < 12:
        noise_types.append("short_span")
        reasons.append("quoted_span is too short to support a grounded claim")
    if text and cjk_alpha < 4 and digits > 0:
        noise_types.append("numeric_fragment_only")
        reasons.append("quoted_span is mostly numeric with little language context")
    if len(raw_lines) >= 3 and short_line_ratio >= 0.65 and (digit_ratio >= 0.18 or any("%" in line for line in raw_lines)):
        noise_types.append("table_fragment")
        reasons.append("quoted_span appears to be a table row fragment without complete sentence context")
    if re.search(r"(毛利|收入|净利|利润|EPS|ROE|ROIC)", text, re.IGNORECASE) and len(raw_lines) >= 2 and not _has_sentence_context(text):
        noise_types.append("financial_table_row_only")
        reasons.append("financial metric fragment lacks explanatory context")
    if re.search(r"^(目录|目\s*录|contents?)\b", text, re.IGNORECASE) or re.search(r"\.{3,}\s*\d+$", text):
        noise_types.append("toc_fragment")
        reasons.append("quoted_span looks like a table of contents fragment")
    if re.search(r"(第\s*\d+\s*页|page\s*\d+|证券代码|公告编号)", text, re.IGNORECASE) and length < 80:
        noise_types.append("page_header_footer")
        reasons.append("quoted_span looks like page header/footer metadata")
    if re.search(r"(免责声明|风险提示|不构成投资建议|forward-looking statements?|safe harbor)", text, re.IGNORECASE):
        noise_types.append("disclaimer")
        reasons.append("quoted_span is a disclaimer or risk boilerplate")
    if re.search(r"(版权所有|保留所有权利|未经许可|法律声明)", text, re.IGNORECASE):
        noise_types.append("legal_boilerplate")
        reasons.append("quoted_span is legal boilerplate")
    if _is_ppt_like_title(title) and length < 35 and not _has_sentence_context(text):
        noise_types.append("ppt_title_only")
        reasons.append("PPT-like short title without complete statement context")
    if _is_ppt_like_title(title) and _looks_like_slogan_or_title(text) and section_type != "qa_section":
        noise_types.append("ppt_title_only")
        reasons.append("PPT-like span looks like a standalone title or slogan")
    elif _looks_like_slogan_or_title(text) and not _has_sentence_context(text) and section_type != "qa_section":
        noise_types.append("ppt_title_only")
        reasons.append("quoted_span looks like a standalone title or slogan")
    if len(raw_lines) >= 4 and len(set(raw_lines)) <= max(1, len(raw_lines) // 2):
        noise_types.append("repeated_template")
        reasons.append("quoted_span repeats template text")

    noise_types = list(dict.fromkeys(noise_types))
    reject_hits = [item for item in noise_types if item in REJECT_TYPES]
    if reject_hits:
        action = "reject"
    elif "short_span" in noise_types or "repeated_template" in noise_types:
        action = "review_required"
    else:
        action = "keep"
    severity = 0.0
    for item in noise_types:
        severity += 0.22 if item in REJECT_TYPES else 0.12
    noise_score = round(min(1.0, severity), 2)
    return {
        "evidence_id": (candidate.get("evidence_id") if isinstance(candidate, dict) else None),
        "noise_detected": bool(noise_types),
        "noise_types": noise_types,
        "noise_score": noise_score,
        "recommended_action": action,
        "reason": "; ".join(reasons) if reasons else "no obvious noise detected",
    }


def annotate_chunk_noise(chunk: dict[str, Any]) -> dict[str, Any]:
    """Attach chunk-level noise hints while preserving the original chunk text."""

    result = detect_noise(str(chunk.get("text") or ""))
    metadata = dict(chunk.get("metadata") or {})
    metadata["chunk_noise_types"] = result.get("noise_types") or []
    metadata["chunk_noise_action"] = result.get("recommended_action")
    updated = dict(chunk)
    updated["metadata"] = metadata
    return updated


def summarize_noise(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    for item in assessments:
        counter.update(item.get("noise_types") or [])
    return dict(counter)
