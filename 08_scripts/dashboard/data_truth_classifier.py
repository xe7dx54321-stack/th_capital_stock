"""Data truth classification for Dashboard signals.

Classifies data sources into truth categories to gate low-confidence
signals from entering the main signal flow.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class DataTruthStatus(Enum):
    EVIDENCE_BACKED_REAL = "evidence_backed_real"
    REAL_SNAPSHOT_WITH_SOURCE = "real_snapshot_with_source"
    REAL_SNAPSHOT_NO_EVIDENCE = "real_snapshot_no_evidence"
    GENERATED_SUMMARY = "generated_summary"
    DEFAULT_FALLBACK = "default_fallback"
    PLACEHOLDER = "placeholder"
    HISTORICAL_RESIDUAL = "historical_residual"
    UNKNOWN = "unknown"


TRUTH_STATUS_LABELS = {
    DataTruthStatus.EVIDENCE_BACKED_REAL: "有证据支撑的真实数据",
    DataTruthStatus.REAL_SNAPSHOT_WITH_SOURCE: "有来源的真实快照",
    DataTruthStatus.REAL_SNAPSHOT_NO_EVIDENCE: "无证据的真实快照",
    DataTruthStatus.GENERATED_SUMMARY: "生成式摘要",
    DataTruthStatus.DEFAULT_FALLBACK: "默认兜底数据",
    DataTruthStatus.PLACEHOLDER: "占位数据",
    DataTruthStatus.HISTORICAL_RESIDUAL: "历史残留数据",
    DataTruthStatus.UNKNOWN: "未知",
}


def _has_evidence_indicator(item: dict[str, Any]) -> bool:
    evidence_keys = [
        "source_url",
        "original_url",
        "report_path",
        "evidence_packet_id",
        "evidence_id",
        "filing_url",
        "pdf_path",
        "source_rel_path",
        "source_refs",
        "evidence_url",
    ]
    for key in evidence_keys:
        value = item.get(key)
        if value:
            if isinstance(value, list):
                if any(v for v in value if v):
                    return True
            elif isinstance(value, str) and value.strip():
                return True
    return False


def _has_timestamp(item: dict[str, Any]) -> bool:
    timestamp_keys = [
        "published_at",
        "observed_at",
        "generated_at",
        "created_at",
        "alert_time",
        "event_time",
        "trade_date",
        "publish_time",
    ]
    for key in timestamp_keys:
        value = item.get(key)
        if value:
            if isinstance(value, str) and value.strip():
                return True
    return False


def _has_source_info(item: dict[str, Any]) -> bool:
    source_keys = [
        "source_name",
        "source_type",
        "source_label",
        "provider",
        "org_name",
        "source_kind",
        "source_url",
        "original_url",
    ]
    for key in source_keys:
        value = item.get(key)
        if value:
            if isinstance(value, str) and value.strip():
                return True
    return False


def _is_generated_summary(item: dict[str, Any]) -> bool:
    generated_indicators = [
        "summary",
        "verdict",
        "reason",
        "rationale",
        "judgment",
        "analysis",
        "conclusion",
        "assessment",
        "recommendation",
    ]
    has_generated_field = any(item.get(key) for key in generated_indicators)
    has_no_evidence = not _has_evidence_indicator(item)
    return has_generated_field and has_no_evidence


def _is_fallback(item: dict[str, Any]) -> bool:
    fallback_indicators = [
        "暂无原文",
        "暂无证据",
        "系统检测",
        "自动生成",
        "默认值",
        "placeholder",
        "fallback",
    ]
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    reason = str(item.get("reason") or "")
    text = (title + summary + reason).lower()
    for indicator in fallback_indicators:
        if indicator.lower() in text:
            return True
    return False


def _is_placeholder(item: dict[str, Any]) -> bool:
    placeholder_indicators = [
        "待接入",
        "示例",
        "sample",
        "demo",
        "test",
        "mock",
        "placeholder",
        "待补充",
        "待定",
    ]
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    source_label = str(item.get("source_label") or "")
    text = (title + summary + source_label).lower()
    for indicator in placeholder_indicators:
        if indicator.lower() in text:
            return True
    return False


def _is_historical_residual(item: dict[str, Any]) -> bool:
    residual_indicators = [
        "historical",
        "archive",
        "legacy",
        "old_",
        "_old",
        "backup",
        "_bak",
    ]
    source = str(item.get("source") or "")
    entity_id = str(item.get("entity_id") or "")
    text = (source + entity_id).lower()
    for indicator in residual_indicators:
        if indicator.lower() in text:
            return True
    return False


def classify_data_truth(item: dict[str, Any]) -> dict[str, Any]:
    has_evidence = _has_evidence_indicator(item)
    has_timestamp = _has_timestamp(item)
    has_source = _has_source_info(item)
    is_generated = _is_generated_summary(item)
    is_fallback = _is_fallback(item)
    is_placeholder = _is_placeholder(item)
    is_residual = _is_historical_residual(item)

    data_status = str(item.get("data_status") or "")
    is_placeholder_status = data_status in ("placeholder", "default")

    if is_placeholder or is_placeholder_status:
        status = DataTruthStatus.PLACEHOLDER
        reason = "明确的占位或待接入数据"
    elif is_fallback:
        status = DataTruthStatus.DEFAULT_FALLBACK
        reason = "默认兜底或系统生成的填充数据"
    elif is_residual:
        status = DataTruthStatus.HISTORICAL_RESIDUAL
        reason = "历史归档或遗留数据"
    elif is_generated:
        status = DataTruthStatus.GENERATED_SUMMARY
        reason = "生成式摘要，仅有判断句无原始证据"
    elif has_evidence and has_timestamp and not is_generated:
        status = DataTruthStatus.EVIDENCE_BACKED_REAL
        reason = "有证据包/来源URL和时间戳的真实数据"
    elif has_source:
        status = DataTruthStatus.REAL_SNAPSHOT_WITH_SOURCE
        reason = "有来源信息但缺少完整证据包"
    elif has_timestamp:
        status = DataTruthStatus.REAL_SNAPSHOT_NO_EVIDENCE
        reason = "来自真实快照但无原文和证据包"
    else:
        status = DataTruthStatus.UNKNOWN
        reason = "无法判断数据来源"

    return {
        "truth_status": status.value,
        "truth_reason": reason,
        "has_source": has_source,
        "has_evidence_packet": has_evidence,
        "is_generated_summary": status == DataTruthStatus.GENERATED_SUMMARY,
        "is_default_fallback": status == DataTruthStatus.DEFAULT_FALLBACK,
    }


def should_enter_main_signal_flow(item: dict[str, Any], include_low_confidence: bool = False) -> bool:
    classification = classify_data_truth(item)
    status = DataTruthStatus(classification["truth_status"])

    allowed_statuses = [
        DataTruthStatus.EVIDENCE_BACKED_REAL,
        DataTruthStatus.REAL_SNAPSHOT_WITH_SOURCE,
    ]

    if include_low_confidence:
        allowed_statuses.append(DataTruthStatus.REAL_SNAPSHOT_NO_EVIDENCE)

    return status in allowed_statuses
