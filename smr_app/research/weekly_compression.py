"""
周报压缩 V1（weekly_compression.py）

功能说明（小白版）：
    你连续看了 5 天日报，每天都有 2~3 条草稿。
    如果把 5×3=15 条草稿全都放知识库，会有大量重复信息。
    阶段 8 要求："周报负责把连续几天的结论压缩成更稳定的知识对象"。
    所以本模块做「连续几天的 wiki draft 压缩归并」：

    比如周一周二周三都写了"DCI 需求真实，但叙事竞争强"相关的草稿，
    我们把它们合并成 1 条更稳定的 STRATEGY / THESIS 类型的草稿，并标注：
        支撑了几天？（confidence 更高）
        哪些证据反复出现？
        哪里有矛盾？（如果周一说"价格战"，周五说"ASP 持平"，那就是矛盾点，需要人工 review）

核心类：
    WeekOfDrafts          ：一周的草稿集合
    WeeklyCompressor      ：把一周草稿压缩成"更稳定的知识对象"
    StableKnowledgeObject ：压缩后的结果（可以直接进治理链）
"""

from __future__ import annotations

import re
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

from smr_app.research.daily_signal_integration import (
    WikiDraft,
    ALL_DRAFT_TYPES,
    DRAFT_TYPE_STRATEGY, DRAFT_TYPE_THESIS, DRAFT_TYPE_FACT,
    DRAFT_TYPE_CATALYST, DRAFT_TYPE_RISK_CASE, DRAFT_TYPE_DECISION,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ------------------------------------------------------------------------------
# 稳定知识对象（压缩结果）
# ------------------------------------------------------------------------------
@dataclass
class StableKnowledgeObject:
    """
    压缩后的"稳定知识对象"（可以直接提交给治理链 review → 进 wiki）

    小白参数：
        object_id           唯一
        week_label          "2026-W30" 这种
        draft_type          strategy / thesis / fact ... 同 WikiDraft
        entity_id           标的或主题
        title               压缩版标题
        evidence_robustness 有几天证据支撑？ ≥3 天是强证据
        contradiction_notes 矛盾点（压缩时发现的）
        supporting_draft_ids 用到了哪些原始草稿
        confidence          系统信心
        content_md          压缩后的知识正文（人直接能读）
        governance_priority "high/medium/low"（高优先级先 review）
    """
    object_id: str
    week_label: str
    draft_type: str
    entity_id: str
    title: str
    evidence_robustness_days: int
    contradiction_notes: list[str] = field(default_factory=list)
    supporting_draft_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    content_md: str = ""
    governance_priority: str = "medium"
    created_at: str = field(default_factory=_utc_now)
    candidate_category: str = ""
    tags: list[str] = field(default_factory=list)

    def to_wiki_draft(self) -> WikiDraft:
        """把稳定对象转成 WikiDraft（接治理链）"""
        return WikiDraft(
            draft_id=f"sko_{self.object_id}",
            source_id=f"weekly_compression:{self.week_label}",
            draft_type=self.draft_type,
            entity_type="theme" if self.draft_type in (
                DRAFT_TYPE_STRATEGY, DRAFT_TYPE_THESIS) else (
                    "company" if re.search(r"\d{6}\.(SH|SZ)", self.entity_id) else "system"),
            entity_id=self.entity_id,
            title=self.title,
            summary=self.content_md[:300],
            candidate_category=self.candidate_category or f"周报沉淀/{self.week_label}",
            candidate_tags=[*self.tags, "weekly_compressed", f"week:{self.week_label}"],
            governance_status="review_required",
            approval_status="pending_manual_review",
            confidence=round(self.confidence, 3),
            raw_signal_ref=",".join(self.supporting_draft_ids),
            content_md=self.content_md,
            upstream_refs=[*self.supporting_draft_ids],
            reason_code="" if not self.contradiction_notes else "has_contradiction_needs_human",
        )


# ------------------------------------------------------------------------------
# 压缩器
# ------------------------------------------------------------------------------
class WeeklyCompressor:
    """
    把一周的 WikiDrafts 压缩成几个 StableKnowledgeObject。

    小白版算法（很简单但有效，符合"最小闭环"原则）：
        1. 先按 (draft_type, entity_id) 分桶 → 同一主题/同一类型的放一组
        2. 每一组：
            a. 统计有几天支撑（看原始 daily report 日期去重）
            b. 计算相似度：两两句子比，如果相似度 ≥ 0.6 就算"同一件事重复出现"
            c. 找矛盾点：如果同组里同时出现"上涨+下跌"、"风险+安全"这种关键词冲突
               就写进 contradiction_notes，标记 governance_priority=high
            d. 压缩正文：取最早草稿的 summary 做开头，再附"Day2 补了什么证据"、
               "Day4 补了什么证据"这种时间线
        3. 返回 StableKnowledgeObject 列表（可再转 WikiDraft 接治理链）
    """

    def __init__(
        self,
        *,
        sim_threshold: float = 0.6,
        robustness_day_threshold: int = 3,
    ) -> None:
        self.sim_threshold = sim_threshold
        self.robustness_day_threshold = robustness_day_threshold

    # ------------------------------------------------------------------ 工具
    @staticmethod
    def _similar(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    CONTRADICTION_PAIRS: list[tuple[re.Pattern, re.Pattern, str]] = [
        (re.compile(r"(上涨|上行|看涨|看多|乐观|增持|加仓|调入)"),
         re.compile(r"(下跌|下行|看空|悲观|减持|减仓|调出|止损|风险)"),
         "多空矛盾：同时看多看空同一实体，请人工核实"),
        (re.compile(r"(价格战|ASP.*降|利润率.*降)"),
         re.compile(r"(毛利率持平|毛利率上行|利润率上升|ASP 稳定)"),
         "价格/毛利率证据矛盾"),
        (re.compile(r"(需求不真|集采.*下滑|订单.*减少)"),
         re.compile(r"(需求真实|集采.*增长|订单.*增多|出货同比\+)"),
         "需求/订单信号矛盾"),
    ]

    @staticmethod
    def _extract_day_label(source_id: str) -> str:
        """从 source_id=daily_20260723 抽出 '20260723' 做日标识"""
        m = re.search(r"(20\d{6})", source_id)
        if m:
            return m.group(1)
        return source_id  # 兜底就拿整条

    # ------------------------------------------------------------------ 主入口
    def compress(
        self,
        drafts_of_week: list[WikiDraft],
        *,
        week_label: str = "",
    ) -> list[StableKnowledgeObject]:
        if not week_label:
            week_label = datetime.now().strftime("%Y-W%W")

        # 1. 分桶
        buckets: dict[tuple[str, str], list[WikiDraft]] = defaultdict(list)
        for d in drafts_of_week:
            key = (d.draft_type, d.entity_id)
            buckets[key].append(d)

        results: list[StableKnowledgeObject] = []

        # 2. 每桶处理
        for (dtype, eid), group in buckets.items():
            # a. 天数支撑
            days = {self._extract_day_label(d.source_id) for d in group}
            days_n = len(days)

            # b. 相似度：两两比对，统计有多少条和"首条"一致
            texts = [d.summary or d.title for d in group]
            base = texts[0] if texts else ""
            sim_scores = [self._similar(base, t) for t in texts[1:]]
            repeating = len([s for s in sim_scores if s >= self.sim_threshold]) + (
                1 if base else 0
            )

            # c. 矛盾检查
            contradictions: list[str] = []
            joined = "\n".join(texts)
            for pos_pat, neg_pat, msg in self.CONTRADICTION_PAIRS:
                if pos_pat.search(joined) and neg_pat.search(joined):
                    contradictions.append(msg)

            # 信心度：days_n 越高越自信；有矛盾扣分；重复度高加分
            conf = 0.55
            if days_n >= self.robustness_day_threshold:
                conf += 0.20
            elif days_n >= 2:
                conf += 0.10
            repeat_ratio = repeating / max(1, len(group))
            conf += repeat_ratio * 0.15
            if contradictions:
                conf -= 0.15 * len(contradictions)
            conf = max(0.0, min(1.0, conf))

            priority = "low"
            if days_n >= self.robustness_day_threshold:
                priority = "medium"
            if contradictions:
                priority = "high"
            if dtype in (DRAFT_TYPE_STRATEGY, DRAFT_TYPE_THESIS, DRAFT_TYPE_RISK_CASE):
                # 策略/主题/风险都是高价值，即使 2 天也 medium
                if priority == "low":
                    priority = "medium"

            # d. 压缩正文
            parts = [
                f"# {dtype}：{eid}（第 {week_label} 周压缩沉淀）",
                "",
                f"- **证据天数**：{days_n} 天 / 草稿 {len(group)} 条",
                f"- **支撑草稿**：{', '.join(d.draft_id for d in group)}",
                f"- **重复度**：{repeating}/{len(group)} 条观点相似",
                f"- **系统信心**：{conf:.2f}",
                (f"- **矛盾点**：{'; '.join(contradictions)}" if contradictions else
                 "- **矛盾点**：无，一周内观点一致"),
                "",
                "## 时间线（按草稿顺序）",
                "",
            ]
            for d in group:
                day = self._extract_day_label(d.source_id)
                tag_note = f" [auto_ready]" if d.approval_status == "auto_ready" else ""
                parts.append(f"- **{day}**{tag_note}：{d.title}\n  → {d.summary}")
            parts.append("")
            parts.append("## 合并摘要（压缩版）")
            parts.append("")
            parts.append(group[0].summary if group else "")
            if repeating > 1:
                parts.append(
                    f"\n（本主题在一周内被 {repeating}/{len(group)} 份草稿反复验证，"
                    f"信心度较单日报稿更高）"
                )
            if contradictions:
                parts.append(
                    "\n⚠️ **压缩时发现观点冲突，建议优先人工 review**：\n- " +
                    "\n- ".join(contradictions)
                )
            content_md = "\n".join(parts)

            title = (
                f"[{week_label}] {dtype}/{eid}："
                + (group[0].title[:30] if group else "")
            )
            obj = StableKnowledgeObject(
                object_id=uuid.uuid4().hex[:12],
                week_label=week_label,
                draft_type=dtype,
                entity_id=eid,
                title=title,
                evidence_robustness_days=days_n,
                contradiction_notes=list(contradictions),
                supporting_draft_ids=[d.draft_id for d in group],
                confidence=round(conf, 3),
                content_md=content_md,
                governance_priority=priority,
                tags=[dtype, eid, f"robustness_{days_n}d"],
                candidate_category=f"周报压缩-{priority}优先",
            )
            results.append(obj)

        # 按 governance_priority 排序（high → medium → low），然后按 confidence 降序
        pr_order = {"high": 0, "medium": 1, "low": 2}
        results.sort(key=lambda o: (pr_order.get(o.governance_priority, 3), -o.confidence))
        return results
