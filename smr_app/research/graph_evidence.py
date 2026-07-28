"""
图谱证据（Graph Evidence）- 证据 ID 生命周期 + 事实/推断区分管理器

功能说明：
    阶段 7「产业图谱与前瞻数据增强」的证据治理模块。
    解决的问题：图谱里的一条"海光 ↔ 寒武纪 竞争"关系到底是从哪里来的？
    有没有过硬证据？什么时候开始生效？信心度多少？

    核心职责：
    1. 统一管理 evidence_id 的生成、校验、查重（避免"同一份证据出现两个 ID"）
    2. 为每条边生成规范化的 GraphEvidence 对象（含 valid_from/confidence/source_tier）
    3. 明确区分事实边（fact）vs 推断边（inferred）的最小证据要求
    4. 提供内容哈希幂等（同一份原文多次沉淀不会重复入库）

参数说明：
    EvidenceSource    - 证据来源元数据（原文 URL / 标题 / 发布时间 / 权威等级）
    GraphEvidence     - 完整证据对象（evidence_id + source + 引用片段 + 有效期 + 信心）
    EvidenceRegistry  - 存储器：存/查/查重/按类型列出

返回值说明：
    - EvidenceRegistry.register() → (evidence_id, is_new) is_new=False 表示命中幂等
    - EvidenceRegistry.validate_for_edge(evidence, edge_kind) → (ok, reasons) 告诉
      你这条证据够不够资格支撑 fact / inferred 边
    - 永远不抛异常（输入非法返回 (False, 原因列表)）

异常处理：
    - 任意缺失字段 / 类型错 / 格式错 → 不抛异常，返回 False + 详细原因
    - 网络/磁盘读写错 → 捕获并降级到内存存储
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional
import json


# ============================================================================
# 权威等级（source_tier，数字越小越权威）
# ============================================================================

TIER_OFFICIAL = 1    # 1 级：巨潮/港交所/SEC 公告、公司官网 IR 页、招股书、定期报告
TIER_SEMI = 2        # 2 级：协会/产业白皮书、知名券商深度、政府公开数据
TIER_NEWS = 3        # 3 级：高质量媒体、财经自媒体 TOP
TIER_UNVERIFIED = 4  # 4 级：社交媒体/传闻/未知来源

TIER_LABELS = {
    TIER_OFFICIAL: "官方公告/官网",
    TIER_SEMI: "半官方/券商/协会",
    TIER_NEWS: "权威媒体",
    TIER_UNVERIFIED: "未验证来源",
}

VALID_SOURCE_TIERS = frozenset({TIER_OFFICIAL, TIER_SEMI, TIER_NEWS, TIER_UNVERIFIED})


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class EvidenceSource:
    """
    证据来源元数据

    小白讲解：
        这条证据从哪儿来的？
        - url: 原文链接（例：巨潮某公告链接）
        - title: 标题（例："海光信息 2025 年年度报告"）
        - source_name: 来源名（例：巨潮资讯）
        - published_at: 原文发布时间 ISO（例：2026-03-18T22:00:00+08:00）
        - source_tier: 1~4 级权威等级（1 最权威）
    """
    url: str = ""
    title: str = ""
    source_name: str = ""
    published_at: str = ""
    source_tier: int = TIER_UNVERIFIED
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.source_tier not in VALID_SOURCE_TIERS:
            self.source_tier = TIER_UNVERIFIED


@dataclass
class GraphEvidence:
    """
    完整的证据对象

    小白讲解：
        证据 = 来源 + 引用片段 + 有效时间 + 信心度。
        每条证据都有一个全局唯一的 evidence_id（由内容哈希生成，保证幂等）。

        关键属性：
        - evidence_id：像"ev_20260318a3f2..."这种 ID，全库唯一
        - snippet：引用的原文片段（例："2025 年 DCU 出货 12 万颗，同比+150%"）
        - valid_from / valid_until：证据代表的时间段（例：这份年报只代表 2025 年）
        - confidence：0~1 信心度（官方公告 = 1.0，媒体传闻 ≈ 0.3）
        - supports_fact：能不能拿来当"事实边"？（至少 2 级 + 明确片段才可以）
    """
    evidence_id: str
    source: EvidenceSource
    snippet: str = ""
    valid_from: str = ""
    valid_until: str = ""
    confidence: float = 0.5
    content_hash: str = ""
    created_at: str = ""
    supports_fact: bool = False
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.confidence < 0:
            self.confidence = 0.0
        if self.confidence > 1:
            self.confidence = 1.0
        # 判断能不能支撑 fact 边：至少半官方 + 有引用片段 + 信心 >= 0.8
        if not self.supports_fact:
            self.supports_fact = (
                self.source.source_tier <= TIER_SEMI
                and bool(self.snippet.strip())
                and self.confidence >= 0.8
            )
        if not self.created_at:
            self.created_at = _utc_now_iso()


class EvidenceRegistry:
    """
    证据注册表

    小白讲解：
        就像一个"证据档案柜"。
        注册证据时：先查内容哈希，命中了就复用（幂等，不会同一份证据存两遍）；
        没命中就生成新 ID 入库。
        同时可以验证："这条证据够资格当 fact 边的支撑吗？"
    """

    def __init__(self, persist_path: Optional[str | Path] = None):
        self._ev_by_id: dict[str, GraphEvidence] = {}
        self._hash_to_id: dict[str, str] = {}  # 内容哈希 → evidence_id（做幂等）
        self._persist_path: Optional[Path] = Path(persist_path) if persist_path else None
        if self._persist_path and self._persist_path.is_file():
            self._load_from_file()

    # ------------------------------------------------------------------
    # 对外核心接口
    # ------------------------------------------------------------------

    def compute_content_hash(
        self,
        *,
        source_url: str,
        snippet: str,
        published_at: str = "",
    ) -> str:
        """
        计算证据内容哈希（幂等的关键：相同原文+片段只会得到同一个哈希）

        小白讲解：
            把 URL + 发布时间 + 引用片段拼成字符串，取 SHA-256 前 16 位。
            只要原文不变，无论谁调用多少次，哈希都一样 → 不会重复入库。
        """
        payload = f"{source_url.strip().lower()}|{published_at.strip()}|{snippet.strip()}"
        return sha256(payload.encode("utf-8")).hexdigest()[:16]

    def register(
        self,
        *,
        source: EvidenceSource,
        snippet: str = "",
        valid_from: str = "",
        valid_until: str = "",
        confidence: Optional[float] = None,
        tags: Optional[list[str]] = None,
    ) -> tuple[str, bool]:
        """
        注册一条证据

        参数:
            source: 证据来源元数据
            snippet: 引用的原文片段（fact 边必填）
            valid_from / valid_until: 有效期
            confidence: 信心度（None 时自动根据权威等级推荐）
            tags: 标签列表（例：["DCU", "2025年报"]）

        返回:
            (evidence_id, is_new)
            - is_new = True：新注册的
            - is_new = False：命中内容哈希幂等，复用了已有 ID
        """
        # 1. 先算内容哈希 → 查幂等
        content_hash = self.compute_content_hash(
            source_url=source.url, snippet=snippet, published_at=source.published_at,
        )
        if content_hash in self._hash_to_id:
            ev_id = self._hash_to_id[content_hash]
            # 命中但扩展一下 tags
            existing = self._ev_by_id.get(ev_id)
            if existing and tags:
                existing.tags = sorted(set(existing.tags) | set(tags))
            return ev_id, False

        # 2. 没命中 → 自动推信心度（用户没指定就用权威等级估）
        if confidence is None:
            confidence = {
                TIER_OFFICIAL: 0.98,
                TIER_SEMI: 0.85,
                TIER_NEWS: 0.55,
                TIER_UNVERIFIED: 0.25,
            }.get(source.source_tier, 0.4)

        # 3. 生成 evidence_id（ev_ + 日期 + 哈希前 8）
        date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
        ev_id = f"ev_{date_tag}_{content_hash[:8]}"

        # 4. 构建对象入库
        evidence = GraphEvidence(
            evidence_id=ev_id,
            source=source,
            snippet=snippet,
            valid_from=valid_from,
            valid_until=valid_until,
            confidence=confidence,
            content_hash=content_hash,
            tags=list(tags) if tags else [],
        )
        self._ev_by_id[ev_id] = evidence
        self._hash_to_id[content_hash] = ev_id

        # 5. 持久化（如果配置了路径）
        if self._persist_path is not None:
            self._save_to_file()

        return ev_id, True

    def get(self, evidence_id: str) -> Optional[GraphEvidence]:
        """按 ID 取证据，找不到返回 None"""
        return self._ev_by_id.get(evidence_id)

    def validate_for_edge(
        self,
        evidence_id: str,
        edge_kind: str,
    ) -> tuple[bool, list[str]]:
        """
        验证一条证据"够不够格"支撑某种边

        小白讲解：
        - inferred（推断边）：只要证据 ID 存在就 OK（哪怕是 4 级传闻也行）
        - fact（事实边）：必须满足 3 点 → 至少 2 级 + 有引用片段 + supports_fact=True
          任何一点不满足都会返回"不够格 + 原因列表"

        参数:
            evidence_id: 证据 ID
            edge_kind: "fact" 或 "inferred"

        返回:
            (ok_bool, reasons_list)
            reasons 里是小白能看懂的中文解释
        """
        reasons: list[str] = []

        # inferred 边要求低：只要 ID 存在就行
        if edge_kind == "inferred":
            if evidence_id in self._ev_by_id:
                return True, []
            # 允许 evidence_id 暂时为空（之后补证据），不强制
            if not evidence_id:
                return True, ["evidence_id 为空，后续补充正式证据即可支撑推断边"]
            reasons.append(f"evidence_id={evidence_id} 不在注册表中")
            return False, reasons

        # fact 边要求高
        if edge_kind != "fact":
            reasons.append(f"未知的 edge_kind={edge_kind}（应为 fact/inferred）")
            return False, reasons

        evidence = self._ev_by_id.get(evidence_id)
        if evidence is None:
            if not evidence_id:
                reasons.append("fact 边必须有 evidence_id（不能空）")
            else:
                reasons.append(f"evidence_id={evidence_id} 不存在，无法支撑 fact 边")
            return False, reasons

        if evidence.source.source_tier > TIER_SEMI:
            reasons.append(
                f"来源权威等级是 {evidence.source.source_tier} 级「{TIER_LABELS[evidence.source.source_tier]}」，"
                f"fact 边至少需要 2 级「{TIER_LABELS[TIER_SEMI]}」以上"
            )

        if not evidence.snippet.strip():
            reasons.append("fact 边必须有引用片段（snippet），不能空口说白话")

        if not evidence.supports_fact:
            reasons.append(
                f"综合评分未通过 fact 门槛（supports_fact=False）："
                f"信心度={evidence.confidence:.2f}，要求 ≥ 0.8 且来源 1~2 级且有片段"
            )

        return (len(reasons) == 0), reasons

    def list_by_tier(self, min_tier: int = TIER_SEMI) -> list[GraphEvidence]:
        """列出所有 ≤ 指定等级的证据（例：min_tier=2 只看 1~2 级权威）"""
        return sorted(
            [
                ev for ev in self._ev_by_id.values()
                if ev.source.source_tier <= min_tier
            ],
            key=lambda e: (e.source.source_tier, -e.confidence),
        )

    def count(self) -> dict:
        """返回统计概览（总数/各权威等级数/幂等命中）"""
        tiers: dict[int, int] = {}
        for ev in self._ev_by_id.values():
            tiers[ev.source.source_tier] = tiers.get(ev.source.source_tier, 0) + 1
        return {
            "total": len(self._ev_by_id),
            "by_tier": {
                f"tier_{t}_{TIER_LABELS[t]}": tiers.get(t, 0)
                for t in (TIER_OFFICIAL, TIER_SEMI, TIER_NEWS, TIER_UNVERIFIED)
            },
            "content_hash_indexed": len(self._hash_to_id),
        }

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------

    def _save_to_file(self) -> None:
        try:
            if self._persist_path is None:
                return
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "schema_version": "1.0",
                "saved_at": _utc_now_iso(),
                "evidences": [
                    {
                        "evidence_id": e.evidence_id,
                        "source": {
                            "url": e.source.url,
                            "title": e.source.title,
                            "source_name": e.source.source_name,
                            "published_at": e.source.published_at,
                            "source_tier": e.source.source_tier,
                            "extra": e.source.extra,
                        },
                        "snippet": e.snippet,
                        "valid_from": e.valid_from,
                        "valid_until": e.valid_until,
                        "confidence": e.confidence,
                        "content_hash": e.content_hash,
                        "created_at": e.created_at,
                        "supports_fact": e.supports_fact,
                        "tags": e.tags,
                    }
                    for e in self._ev_by_id.values()
                ],
            }
            self._persist_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
            )
        except OSError:
            # 持久化失败不影响内存态，静默吞
            pass

    def _load_from_file(self) -> None:
        try:
            if self._persist_path is None or not self._persist_path.is_file():
                return
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            for ed in data.get("evidences", []):
                src = EvidenceSource(
                    url=ed.get("source", {}).get("url", ""),
                    title=ed.get("source", {}).get("title", ""),
                    source_name=ed.get("source", {}).get("source_name", ""),
                    published_at=ed.get("source", {}).get("published_at", ""),
                    source_tier=int(ed.get("source", {}).get("source_tier", TIER_UNVERIFIED)),
                    extra=ed.get("source", {}).get("extra", {}),
                )
                ev = GraphEvidence(
                    evidence_id=ed.get("evidence_id", ""),
                    source=src,
                    snippet=ed.get("snippet", ""),
                    valid_from=ed.get("valid_from", ""),
                    valid_until=ed.get("valid_until", ""),
                    confidence=float(ed.get("confidence", 0.5)),
                    content_hash=ed.get("content_hash", ""),
                    created_at=ed.get("created_at", ""),
                    supports_fact=bool(ed.get("supports_fact", False)),
                    tags=list(ed.get("tags", [])),
                )
                self._ev_by_id[ev.evidence_id] = ev
                if ev.content_hash:
                    self._hash_to_id[ev.content_hash] = ev.evidence_id
        except (json.JSONDecodeError, OSError):
            # 加载失败不抛，保持空
            self._ev_by_id = {}
            self._hash_to_id = {}


# ============================================================================
# 工具
# ============================================================================

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
