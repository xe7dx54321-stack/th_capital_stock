"""
Wiki 知识沉淀 V1 治理链（wiki_knowledge_base.py）

功能说明（小白版）：
    阶段 10 补的是"知识沉淀正式落地"的 4 步治理链：

        SourceManifest → IngestDraft → ReviewQueue → WikiEntry（正式页）
           │                  │              │
           │ 来源登记，不扫盘    │ 候选草稿         │ 人工审核队列
           │ (阶段 3)           │ (阶段 4)           │ (阶段 5)
           ▼                   ▼                  ▼

    为什么要做？因为如果脚本直接改 Wiki 正式页，很容易：
        - 同一个东西重复写 3 遍（脏）
        - 写错了没人发现（没审核）
        - 研究已经更新了，但旧知识还躺着（冲突）。
    所以我们强制"所有正式知识都必须经过治理链 → 再 import 正式页"。

对应 Master Plan 阶段 3、4、5、10：
    阶段 3 SourceManifest：登记所有研究产物来源，不用每次扫盘
    阶段 4 IngestDraft ：研究卡/风险预警/日报→draft
    阶段 5 ReviewQueue ：治理协议 + scan/review/resolve/import
    阶段 10 沉淀：draft 变正式 WikiEntry（支持反向链接、来源、过期状态）

核心类：
    SourceSourceManifest     → 来源登记（阶段 3）
    IngestDraft            → 候选草稿（阶段 4）
    ReviewQueue            → 审核队列（阶段 5）
    WikiEntry              → 正式 Wiki 页
    WikiGovernanceService  → 对外统一接口（一站式 scan/review/import）

治理协议（Master Plan 阶段 5 要求）：
    governance_status 3 态：ready / review_required / blocked
    approval_status 5 态：auto_ready / pending_manual_review / approved / rejected / reopened
    reason_code（拒绝原因）：
        duplicate_source / duplicate_thesis / insufficient_evidence /
        conflicts_with_latest_research / outdated_conclusion / needs_human_judgement /
        format_incomplete / source_not_reliable / has_contradiction_needs_human
"""

from __future__ import annotations

import re
import sqlite3
import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from smr_app.research.daily_signal_integration import WikiDraft, ALL_DRAFT_TYPES


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ------------------------------------------------------------------------------
# 常量
# ------------------------------------------------------------------------------
GOVERNANCE_STATUS_READY = "ready"
GOVERNANCE_STATUS_REVIEW_REQUIRED = "review_required"
GOVERNANCE_STATUS_BLOCKED = "blocked"

APPROVAL_AUTO_READY = "auto_ready"
APPROVAL_PENDING = "pending_manual_review"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_REOPENED = "reopened"

REASON_CODES = (
    "duplicate_source",
    "duplicate_thesis",
    "insufficient_evidence",
    "conflicts_with_latest_research",
    "outdated_conclusion",
    "needs_human_judgement",
    "format_incomplete",
    "source_not_reliable",
    "has_contradiction_needs_human",
)

WIKI_STATUS_ACTIVE = "active"
WIKI_STATUS_STALE = "stale"          # 长期未更新
WIKI_STATUS_DEPRECATED = "deprecated"  # 被新知识覆盖/已经失效


# ------------------------------------------------------------------------------
# 阶段 3：SourceManifest
# ------------------------------------------------------------------------------
@dataclass
class SourceManifestEntry:
    """登记一份来源文件/研究产物（小白版："图书馆目录卡"，知道哪本书在哪）"""
    source_id: str
    source_type: str              # research_card / recommendation_card / daily_report / risk_alert / weekly_brief / other
    entity_type: str              # company / theme / portfolio / system
    entity_id: str                # 688041.SH / DCI / portfolio_01
    source_path: str              # 磁盘路径或 URL
    title: str                    # 文件名 / 标题
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    upstream_refs: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    ingested: bool = False        # 是否已被 ingest 成 draft？


class SourceManifest:
    """来源注册表（Master Plan 阶段 3，避免每次全盘扫文件系统）"""

    def __init__(self) -> None:
        self._entries: dict[str, SourceManifestEntry] = {}

    def register(self, entry: SourceManifestEntry) -> SourceManifestEntry:
        if entry.source_id in self._entries:
            raise ValueError(f"source_id 已存在：{entry.source_id}（要更新请 update）")
        self._entries[entry.source_id] = entry
        return entry

    def list(self, *, entity_id: str | None = None, source_type: str | None = None
             ) -> list[SourceManifestEntry]:
        out = list(self._entries.values())
        if entity_id is not None:
            out = [x for x in out if x.entity_id == entity_id]
        if source_type is not None:
            out = [x for x in out if x.source_type == source_type]
        out.sort(key=lambda x: x.created_at, reverse=True)
        return out

    def mark_ingested(self, source_id: str) -> None:
        if source_id in self._entries:
            self._entries[source_id].ingested = True
            self._entries[source_id].updated_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "count": len(self._entries),
            "entries": [self._entry_to_dict(e) for e in self._entries.values()],
        }

    @staticmethod
    def _entry_to_dict(e: SourceManifestEntry) -> dict[str, Any]:
        return {
            "source_id": e.source_id, "source_type": e.source_type,
            "entity_type": e.entity_type, "entity_id": e.entity_id,
            "source_path": e.source_path, "title": e.title,
            "created_at": e.created_at, "updated_at": e.updated_at,
            "upstream_refs": list(e.upstream_refs), "tags": list(e.tags),
            "ingested": e.ingested,
        }


# ------------------------------------------------------------------------------
# 阶段 4：IngestDraft（统一治理版本，和 WikiDraft 兼容，加治理链状态）
# ------------------------------------------------------------------------------
@dataclass
class IngestDraft:
    """IngestDraft（统一治理链版本，WikiDraft 可以直接 transform 过来）"""
    draft_id: str
    source_id: str
    draft_type: str
    entity_type: str
    entity_id: str
    title: str
    summary: str
    content_md: str
    candidate_category: str = ""
    candidate_tags: list[str] = field(default_factory=list)
    governance_status: str = GOVERNANCE_STATUS_REVIEW_REQUIRED
    approval_status: str = APPROVAL_PENDING
    confidence: float = 0.0
    reason_code: str = ""
    rejection_reason: str = ""
    review_comments: list[str] = field(default_factory=list)
    upstream_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    imported_wiki_entry_id: str = ""

    @classmethod
    def from_wiki_draft(cls, wd: WikiDraft) -> "IngestDraft":
        return cls(
            draft_id=wd.draft_id, source_id=wd.source_id, draft_type=wd.draft_type,
            entity_type=wd.entity_type, entity_id=wd.entity_id, title=wd.title,
            summary=wd.summary, content_md=wd.content_md,
            candidate_category=wd.candidate_category, candidate_tags=list(wd.candidate_tags),
            governance_status=wd.governance_status, approval_status=wd.approval_status,
            confidence=wd.confidence, reason_code=wd.reason_code,
            upstream_refs=list(wd.upstream_refs),
        )


# ------------------------------------------------------------------------------
# 阶段 5：ReviewQueue + WikiEntry（正式 Wiki）
# ------------------------------------------------------------------------------
@dataclass
class WikiEntry:
    """正式 Wiki 页（只有 approved 的 draft 才能进来）"""
    wiki_id: str
    entity_id: str
    entity_type: str
    title: str
    content_md: str
    category: str
    tags: list[str] = field(default_factory=list)
    source_draft_ids: list[str] = field(default_factory=list)  # 来源 draft（可追溯）
    backlink_ids: list[str] = field(default_factory=list)        # 反向链接（其他 wiki 引用我）
    confidence: float = 0.0
    status: str = WIKI_STATUS_ACTIVE
    first_published_at: str = field(default_factory=_utc_now)
    last_reviewed_at: str = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


class ReviewQueue:
    """治理队列（scan/review/resolve/import 4 步，Master Plan 阶段 5）"""

    def __init__(self) -> None:
        self._queue: dict[str, IngestDraft] = {}
        # 治理规则最小集合（Master Plan 要求）
        self._dup_source = set()

    # --------------------- add
    def add(self, d: IngestDraft) -> IngestDraft:
        self._queue[d.draft_id] = d
        return d

    # --------------------- 1. scan（批量：去重 + 冲突检测 + 状态切分）
    def scan(self, wiki_entries: Iterable[WikiEntry] | None = None
             ) -> dict[str, list[IngestDraft]]:
        """
        批量扫队列，按治理规则切 ready / review_required / blocked
        返回 {"ready": [...], "review_required": [...], "blocked": [...]}
        """
        by_entity_title: dict[tuple[str, str, str], IngestDraft] = {}
        wiki: dict[str, WikiEntry] = {w.wiki_id: w for w in (wiki_entries or ())}
        # 合并正式页：同一 (entity, title, category) 如果已有正式页，也要查是否冲突
        existing_titles = {(w.entity_id, w.category, w.title): w for w in wiki.values()}

        ready, review, blocked = [], [], []
        for d in list(self._queue.values()):
            # Rule 1：同 source_id 重复导入 → duplicate_source
            if d.source_id in self._dup_source and not d.reason_code:
                d.governance_status = GOVERNANCE_STATUS_BLOCKED
                d.reason_code = "duplicate_source"
                d.approval_status = APPROVAL_REJECTED
                blocked.append(d); continue
            self._dup_source.add(d.source_id)

            # Rule 2：格式不完整（缺 title/summary/draft_type）→ format_incomplete
            if not (d.title.strip() and d.summary.strip() and d.draft_type in ALL_DRAFT_TYPES):
                d.governance_status = GOVERNANCE_STATUS_BLOCKED
                d.reason_code = "format_incomplete"
                d.approval_status = APPROVAL_REJECTED
                blocked.append(d); continue

            # Rule 3：confidence 太低 < 0.5 → needs_human_judgement / review_required
            if d.confidence < 0.50:
                d.governance_status = GOVERNANCE_STATUS_REVIEW_REQUIRED
                d.reason_code = "needs_human_judgement"
                d.approval_status = APPROVAL_PENDING
                review.append(d); continue

            # Rule 4：同一实体同一主题（(entity, category, title)） 已有新知识 → duplicate_thesis → review
            key = (d.entity_id, d.candidate_category, d.title)
            if key in by_entity_title:
                d.governance_status = GOVERNANCE_STATUS_REVIEW_REQUIRED
                d.reason_code = "duplicate_thesis"
                d.approval_status = APPROVAL_PENDING
                review.append(d); continue
            by_entity_title[key] = d

            # Rule 5：has_contradiction_needs_human（阶段 10 周报压缩里带的标记）
            if d.reason_code == "has_contradiction_needs_human":
                d.governance_status = GOVERNANCE_STATUS_REVIEW_REQUIRED
                d.approval_status = APPROVAL_PENDING
                review.append(d); continue

            # Rule 6：auto_ready → ready 自动通过
            if d.approval_status == APPROVAL_AUTO_READY:
                d.governance_status = GOVERNANCE_STATUS_READY
                ready.append(d); continue

            # 默认 → review
            d.governance_status = GOVERNANCE_STATUS_REVIEW_REQUIRED
            d.approval_status = APPROVAL_PENDING
            review.append(d)

        return {GOVERNANCE_STATUS_READY: ready,
                GOVERNANCE_STATUS_REVIEW_REQUIRED: review,
                GOVERNANCE_STATUS_BLOCKED: blocked}

    # --------------------- 2. review（人工给一条 draft 一个 approval 结果）
    def review(self, draft_id: str, decision: str, *,
               reviewer: str = "human",
               comment: str = "",
               reason_code: str = "") -> IngestDraft:
        d = self._get(draft_id)
        if decision == "approve":
            d.approval_status = APPROVAL_APPROVED
            d.governance_status = GOVERNANCE_STATUS_READY
        elif decision == "reject":
            d.approval_status = APPROVAL_REJECTED
            d.governance_status = GOVERNANCE_STATUS_BLOCKED
            d.reason_code = reason_code or "rejected_by_human"
            d.rejection_reason = comment
        elif decision == "reopen":
            d.approval_status = APPROVAL_REOPENED
            d.governance_status = GOVERNANCE_STATUS_REVIEW_REQUIRED
        else:
            raise ValueError(f"decision={decision!r} 非法：approve/reject/reopen")
        if comment:
            d.review_comments.append(f"[{reviewer} @ {_utc_now()}] {comment}")
        d.updated_at = _utc_now()
        return d

    # --------------------- 3. resolve + import：审核通过的 draft → WikiEntry 正式页
    def import_approved(
        self,
        existing_wiki_store: dict[str, WikiEntry] | None = None,
    ) -> list[WikiEntry]:
        """Master Plan 验收：draft(ready|approved) → WikiEntry；返回新导入 WikiEntry 列表"""
        store: dict[str, WikiEntry] = existing_wiki_store if existing_wiki_store is not None else {}
        newly: list[WikiEntry] = []
        for d in self._queue.values():
            if d.approval_status != APPROVAL_APPROVED and d.approval_status != APPROVAL_AUTO_READY:
                continue
            if d.imported_wiki_entry_id:
                continue  # 已导入过
            # 如果正式库里已有相同 title+entity，追加 backlink + 更新 content
            existing = self._find_existing(store, d)
            if existing is not None:
                existing.content_md += (
                    f"\n\n---\n\n## 来源补充（{d.draft_id} @ {d.created_at}）\n"
                    f"{d.summary}\n"
                )
                existing.source_draft_ids.append(d.draft_id)
                existing.last_reviewed_at = _utc_now()
                if d.candidate_tags:
                    for t in d.candidate_tags:
                        if t not in existing.tags:
                            existing.tags.append(t)
                d.imported_wiki_entry_id = existing.wiki_id
                d.updated_at = _utc_now()
                newly.append(existing)
                continue
            # 新的 WikiEntry
            wiki = WikiEntry(
                wiki_id=f"wiki_{uuid.uuid4().hex[:10]}",
                entity_id=d.entity_id, entity_type=d.entity_type,
                title=d.title, content_md=d.content_md,
                category=d.candidate_category or "未分类",
                tags=list(d.candidate_tags),
                source_draft_ids=[d.draft_id],
                confidence=d.confidence,
                status=WIKI_STATUS_ACTIVE,
            )
            d.imported_wiki_entry_id = wiki.wiki_id
            d.updated_at = _utc_now()
            store[wiki.wiki_id] = wiki
            newly.append(wiki)
        return newly

    # --------------------- 工具
    def status_counts(self) -> dict[str, int]:
        counts = {APPROVAL_AUTO_READY: 0, APPROVAL_PENDING: 0,
                  APPROVAL_APPROVED: 0, APPROVAL_REJECTED: 0, APPROVAL_REOPENED: 0}
        for d in self._queue.values():
            counts[d.approval_status] = counts.get(d.approval_status, 0) + 1
        return counts

    def list_pending(self) -> list[IngestDraft]:
        return sorted(
            [d for d in self._queue.values() if d.approval_status in (
                APPROVAL_PENDING, APPROVAL_REOPENED, APPROVAL_AUTO_READY)],
            key=lambda x: -x.confidence,
        )

    def _get(self, draft_id: str) -> IngestDraft:
        if draft_id not in self._queue:
            raise KeyError(f"draft_id={draft_id} 不在队列中")
        return self._queue[draft_id]

    @staticmethod
    def _find_existing(store: dict[str, WikiEntry], d: IngestDraft) -> WikiEntry | None:
        for w in store.values():
            if w.entity_id == d.entity_id and w.title == d.title:
                return w
        return None


# ------------------------------------------------------------------------------
# 阶段 9：Wiki 体检（补 lint/过期治理，把 backlog 生成出来 + 写回 ReviewQueue）
# ------------------------------------------------------------------------------
class WikiLinter:
    """
    Wiki 体检（阶段 9 文档要求）：扫描正式 wiki
        - 长期未更新 thesis（默认 30 天） → stale
        - 孤儿页（没人引用、无 backlink）
        - 缺来源的知识页
        - 风险案例没后续处置结论的条目
    返回 LintBacklog（可写回 ReviewQueue 或 调度板）
    """

    def __init__(self, *, stale_days: int = 30) -> None:
        self.stale_days = stale_days

    def lint(self, entries: list[WikiEntry]) -> list[dict[str, Any]]:
        backlog: list[dict[str, Any]] = []
        now_ts = datetime.now(timezone.utc)
        for w in entries:
            # 1. 长期未更新 → stale
            try:
                last = datetime.fromisoformat(w.last_reviewed_at.replace("Z", "+00:00"))
            except ValueError:
                last = now_ts
            days_old = (now_ts - last).days
            if days_old >= self.stale_days:
                backlog.append({"wiki_id": w.wiki_id, "severity": "medium",
                                "issue": "stale_entry", "title": w.title,
                                "detail": f"已 {days_old} 天未 review，建议标 stale 或重新复核"})
                w.status = WIKI_STATUS_STALE
            # 2. 孤儿页：无 backlink + 无 tag 且 content 小于 120 字
            if len(w.backlink_ids) == 0 and (not w.tags or len(w.content_md) < 120):
                backlog.append({"wiki_id": w.wiki_id, "severity": "low",
                                "issue": "orphan_page", "title": w.title,
                                "detail": "没有反向链接，可能是孤儿页"})
            # 3. 缺来源
            if not w.source_draft_ids:
                backlog.append({"wiki_id": w.wiki_id, "severity": "medium",
                                "issue": "missing_source", "title": w.title,
                                "detail": "没有来源 draft，不可追溯"})
            # 4. 风险案例没处置
            cat_matches = "风险案例" in w.category
            content_matches = ("处置" in w.content_md) or ("后续" in w.content_md)
            if cat_matches and not content_matches:
                backlog.append({"wiki_id": w.wiki_id, "severity": "high",
                                "issue": "risk_case_no_resolution", "title": w.title,
                                "detail": "风险案例条目没有后续处置结论，请补充"})
        backlog.sort(key=lambda b: ({"high": 0, "medium": 1, "low": 2}.get(b["severity"], 3)))
        return backlog


# ------------------------------------------------------------------------------
# 统一服务（对外一站式）
# ------------------------------------------------------------------------------
class WikiGovernanceService:
    """把上面所有组件粘起来，小白最常用：用这个类的方法"""

    def __init__(self) -> None:
        self.manifest = SourceManifest()
        self.review_queue = ReviewQueue()
        self.wiki_store: dict[str, WikiEntry] = {}

    # ---------- 常见流水线：register_source → ingest_draft → scan → review → import
    def register_source(self, entry: SourceManifestEntry) -> SourceManifestEntry:
        return self.manifest.register(entry)

    def ingest_wiki_draft(self, wd: WikiDraft) -> IngestDraft:
        d = IngestDraft.from_wiki_draft(wd)
        return self.review_queue.add(d)

    def scan_queue(self) -> dict[str, Any]:
        """扫描治理队列 + 返回 counts + backlog 摘要"""
        buckets = self.review_queue.scan(self.wiki_store.values())
        return {
            "counts_ready": len(buckets[GOVERNANCE_STATUS_READY]),
            "counts_review": len(buckets[GOVERNANCE_STATUS_REVIEW_REQUIRED]),
            "counts_blocked": len(buckets[GOVERNANCE_STATUS_BLOCKED]),
            "approval_counts": self.review_queue.status_counts(),
            "pending": self.review_queue.list_pending(),
            "buckets": buckets,
        }

    def review_draft(self, draft_id: str, decision: str, **kwargs) -> IngestDraft:
        return self.review_queue.review(draft_id, decision, **kwargs)

    def import_approved(self) -> list[WikiEntry]:
        newly = self.review_queue.import_approved(self.wiki_store)
        for w in newly:
            self.wiki_store[w.wiki_id] = w
        # 反向链接：在内容里找 [[other_wiki_id]] 这种格式，建立 backlink
        self._rebuild_backlinks()
        return newly

    def run_lint(self, **kwargs) -> list[dict[str, Any]]:
        return WikiLinter(**kwargs).lint(list(self.wiki_store.values()))

    # ------------------------------ 工具
    def export_wiki_to_json(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "generated_at": _utc_now(),
            "wiki_count": len(self.wiki_store),
            "wiki_entries": [
                {
                    "wiki_id": w.wiki_id, "entity_id": w.entity_id, "entity_type": w.entity_type,
                    "title": w.title, "category": w.category, "tags": list(w.tags),
                    "status": w.status, "confidence": w.confidence,
                    "source_draft_ids": list(w.source_draft_ids),
                    "backlink_ids": list(w.backlink_ids),
                    "last_reviewed_at": w.last_reviewed_at,
                    "content_md": w.content_md,
                }
                for w in self.wiki_store.values()
            ],
            "review_queue": {
                "total": len(self.review_queue._queue),
                "approval_counts": self.review_queue.status_counts(),
            },
            "source_manifest": self.manifest.to_dict(),
        }

    def _rebuild_backlinks(self) -> None:
        """扫描所有 wiki 内容里的 [[wiki_id]] 模式，建立反向链接"""
        pattern = re.compile(r"\[\[([\w\-]+)\]\]")
        all_ids = set(self.wiki_store.keys())
        # 先清
        for w in self.wiki_store.values():
            w.backlink_ids = []
        # 再建
        for src_w in self.wiki_store.values():
            for m in pattern.findall(src_w.content_md):
                target = m.strip()
                if target in all_ids and target != src_wiki_id:
                    target_w = self.wiki_store[target]
                    if src_w.wiki_id not in target_w.backlink_ids:
                        target_w.backlink_ids.append(src_w.wiki_id)
