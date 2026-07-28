"""
日报 → 高价值结论抽提 + 自动 Wiki Draft（daily_signal_integration.py）

功能说明（小白版）：
    你每天收盘后会跑一份日报，里面可能写了几十条内容。
    阶段 8 要求："高价值结论自动产出 wiki draft"，也就是说：
    不能把整份日报都塞进知识库（脏），得先筛选：
        哪些结论值得沉淀？（长期影响的 / 对策略有影响的 / 风险提醒型）
        哪些只是当天流水账？（"今日北向资金流出 20 亿"就不该沉淀）
    本模块就是做这个：把一份日报，拆成若干条「SignalEntry」（信号条目），
    再打分，选「高分条目」自动变成 wiki_draft（知识草稿），
    其他低分的就只留在日报里，不进 knowledge loop。

核心类：
    SignalEntry        : 1 条从日报/研报/外部新闻里抽出来的结论
    SignalClassifier   : 给 1 条 SignalEntry 打「重要度分 + 分类」
    DailyDraftEngine   : 输入一份日报（dict / markdown 文本），输出：
                           - 一堆 SignalEntry（每条带分）
                           - 一堆 WikiDraft（高分条目生成的候选草稿）
WikiDraft（这里定义的是数据结构，真正导入到知识库要走治理链）：
    - draft_id            唯一 ID，例 "wd_20260723_dci_catalyst"
    - draft_type          "strategy/decision/risk_case/fact/thesis 之一
    - confidence          系统对这条 draft 的信心（0~1）
    - status              "pending_review/ready/blocked"
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ------------------------------------------------------------------------------
# 常量：信号分类（决定 draft 进入哪个分类）
# ------------------------------------------------------------------------------
DRAFT_TYPE_STRATEGY = "strategy"       # 策略类："AI 算力 > DCI，资金分流" 这类宏观判断
DRAFT_TYPE_DECISION = "decision"       # 决策类："买入 X 标的 / 加仓 Y 行业"
DRAFT_TYPE_RISK_CASE = "risk_case"     # 风险案例："持仓 Z 触发止损线，处置流程 V2"
DRAFT_TYPE_FACT = "fact"               # 事实类："海光信息 DCU 2026Q1 出货同比+210%"
DRAFT_TYPE_THESIS = "thesis"           # 主题类："DCI 长期需求真实，但 A 股映射不纯 + 叙事竞争导致行情滞后"
DRAFT_TYPE_CATALYST = "catalyst"       # 催化观察："观察光模块 H2 追加招标"
DRAFT_TYPE_PLAYBOOK = "playbook"       # 操作手册："当 WACC 调降 > 200bp 时，先重估再上报"

ALL_DRAFT_TYPES = (
    DRAFT_TYPE_STRATEGY,
    DRAFT_TYPE_DECISION,
    DRAFT_TYPE_RISK_CASE,
    DRAFT_TYPE_FACT,
    DRAFT_TYPE_THESIS,
    DRAFT_TYPE_CATALYST,
    DRAFT_TYPE_PLAYBOOK,
)


# ------------------------------------------------------------------------------
# 关键信号词（小白版：不用 AI 模型，先规则打分，可扩展）
# ------------------------------------------------------------------------------
HIGH_VALUE_PATTERNS: list[tuple[re.Pattern, str, float]] = [
    # 模式                  → draft_type          → 基础加分
    (re.compile(r"目标市值|估值|目标价|上行空间|重估|公允"), DRAFT_TYPE_FACT, 0.70),
    (re.compile(r"DCI|AI 算力|算力基础设施|光模块|海光|中际|新易盛|天孚|DCU|GPU|液冷|交换机|CPO"),
     DRAFT_TYPE_THESIS, 0.65),
    (re.compile(r"催化|观察清单|首单|招标|集采|1\.6T|800G|400G|追加|下单|观察.*招标|观察.*首单"),
     DRAFT_TYPE_CATALYST, 0.68),
    (re.compile(r"风险|止损|预警|警示|暴雷|解禁|价格战|利润率.*(下|降)|低于预期"),
     DRAFT_TYPE_RISK_CASE, 0.70),
    (re.compile(r"加仓|减仓|买入|增持|调仓|换仓|调入|调出|观察池|推荐池"),
     DRAFT_TYPE_DECISION, 0.75),
    (re.compile(r"策略|轮动|(强|弱)于大盘|资金分流|吸金|叙事|拥挤|主题轮动"),
     DRAFT_TYPE_STRATEGY, 0.65),
    (re.compile(r"同比\s*\+?\d+%|环比\s*\+?\d+%|\+\s*\d+\s*%"),
     DRAFT_TYPE_FACT, 0.55),
    (re.compile(r"年报|季报|半年报|财报|业绩快报|预告|分部|披露"),
     DRAFT_TYPE_FACT, 0.55),
]

LOW_VALUE_STOPWORDS = [
    "今日", "昨日", "本周", "下周", "昨天", "今天", "早盘", "尾盘",
    "北向资金", "南向资金", "外资", "成交额", "换手率", "沪指", "深指", "创业板指",
    "大盘", "指数", "涨", "跌", "收盘", "开盘",
]


# ------------------------------------------------------------------------------
# Data classes
# ------------------------------------------------------------------------------
@dataclass
class SignalEntry:
    """
    从日报/外部研究抽出来的 1 条信号（小白版："一条值得进一步看的结论"）

    参数说明：
        entry_id          唯一 ID
        source_report_id  来源日报/周报 ID，例 "daily_20260723"
        source_type       "daily/weekly/research_card/recommendation_card/risk_alert" 等
        entity_key        关联标的/主题，例 "002396.SZ"、"688041.SH"、"DCI"
        text              原始文本（原始句子或小结）
        evidence_ids      证据 ID 列表（可选）
        author            谁写的 / 哪个模块生成，例 "openclaw_brief_agent"
        created_at        生成时间
        raw_metadata      想塞的其他信息
    """
    entry_id: str
    source_report_id: str
    source_type: str
    entity_key: str
    text: str
    evidence_ids: list[str] = field(default_factory=list)
    author: str = "daily_engine_v1"
    created_at: str = field(default_factory=_utc_now)
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    # 打分后会填的字段
    score: float = 0.0
    draft_type: str = "fact"
    keywords_hit: list[str] = field(default_factory=list)


@dataclass
class WikiDraft:
    """
    一条知识草稿（等治理链 review → 然后导入 wiki 正式页）

    小白版字段说明（对应 master plan 阶段 4 的 ingest_draft）：
        draft_id           唯一
        source_id          来源（日报 id、研究卡 id）
        draft_type         strategy / decision / risk_case / fact / thesis / catalyst / playbook
        entity_type        "company / theme / portfolio / system"
        entity_id          具体标的或主题 ID
        title              草稿标题
        summary            草稿摘要（1~3 句）
        candidate_category 草稿分类，例 "行业研究 / 公司研究 / 风险案例 / 催化观察"
        candidate_tags     标签列表
        governance_status  "ready / review_required / blocked"
        approval_status    "auto_ready / pending_manual_review / approved / rejected / reopened"
        confidence         系统对这条草稿的信心 0~1
        raw_signal_ref     对应的 SignalEntry.entry_id
        content_md         草稿正文（如果需要详细内容）
        upstream_refs      上游引用（论文、研报、公告）
    """
    draft_id: str
    source_id: str
    draft_type: str
    entity_type: str
    entity_id: str
    title: str
    summary: str
    candidate_category: str = ""
    candidate_tags: list[str] = field(default_factory=list)
    governance_status: str = "review_required"
    approval_status: str = "pending_manual_review"
    confidence: float = 0.0
    raw_signal_ref: str = ""
    content_md: str = ""
    upstream_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    reason_code: str = ""   # 治理规则拒绝时填：duplicate_source / insufficient_evidence ...

    def __post_init__(self):
        if self.draft_type not in ALL_DRAFT_TYPES:
            raise ValueError(f"draft_type={self.draft_type} 非法，必须 {ALL_DRAFT_TYPES}")


# ------------------------------------------------------------------------------
# 分类打分引擎
# ------------------------------------------------------------------------------
class SignalClassifier:
    """
    给 SignalEntry 打分 + 判断是否值得沉淀为 wiki draft。

    小白版规则：
        1）先看 HIGH_VALUE_PATTERNS，命中的按最高 priority 给出 draft_type + 基础分
        2）再看如果句子里充满了 LOW_VALUE_STOPWORDS（只是今天流水账）就降分
        3）含实体（A 股代码、6 数字代码、数字代码 SH/SZ、中文主题名）加分
        4）含数字百分比/同比/环比 加分
        5）最后 score >= 0.6 → 变成 pending_review draft；>= 0.8 → auto_ready
    """

    def __init__(self,
                 *,
                 threshold_for_draft: float = 0.60,
                 threshold_auto_ready: float = 0.80) -> None:
        self.threshold_for_draft = threshold_for_draft
        self.threshold_auto_ready = threshold_auto_ready

    def classify(self, entry: SignalEntry) -> None:
        """原地改 entry.score、entry.draft_type、entry.keywords_hit，不返回新对象"""
        text = entry.text
        score_base = 0.0
        type_selected = DRAFT_TYPE_FACT
        hits: list[str] = []

        for regex, dtype, weight in HIGH_VALUE_PATTERNS:
            if regex.search(text):
                if weight > score_base:
                    score_base = weight
                    type_selected = dtype
                hits.append(f"{dtype}:+{weight:.2f}")

        # 流水账惩罚（如果 80% 词都是今日/北向/大盘/指数这类，说明没长期价值）
        sw_count = sum(1 for w in LOW_VALUE_STOPWORDS if w in text)
        if sw_count >= 3:
            score_base -= 0.25
            hits.append("流水账惩罚 -0.25")

        # 有明确股票代码/主题名 → +0.1
        has_entity = bool(entry.entity_key and entry.entity_key.strip() and entry.entity_key not in ("MKT", "ALL"))
        if has_entity:
            score_base += 0.10
            hits.append("实体命中 +0.10")

        # 有证据 ID +0.1
        if entry.evidence_ids:
            score_base += 0.10
            hits.append(f"有 {len(entry.evidence_ids)} 条证据 +0.10")

        # 限制 0~1
        score_final = max(0.0, min(1.0, score_base))

        entry.score = round(score_final, 3)
        entry.draft_type = type_selected
        entry.keywords_hit = hits

    def should_make_draft(self, entry: SignalEntry) -> bool:
        return entry.score >= self.threshold_for_draft

    def is_auto_ready(self, entry: SignalEntry) -> bool:
        return entry.score >= self.threshold_auto_ready


# ------------------------------------------------------------------------------
# 日报 → 信号 → Wiki Draft 引擎
# ------------------------------------------------------------------------------
class DailyDraftEngine:
    """
    阶段 8 主入口：吃一份日报，吐出 SignalEntries + WikiDrafts。

    小白用例：
        engine = DailyDraftEngine()
        result = engine.ingest_daily_report({
            "report_id": "daily_20260723",
            "sections": {
                "市场复盘": "...",
                "持仓盈亏": "...",
                "研究结论": [
                    {"entity_key":"DCI","text":"DCI 需求真实，但 A 股映射不纯 + AI 算力吸金 → 行情滞后"},
                    {"entity_key":"688041.SH","text":"海光 DCU 2026 Q1 出货同比 +210%"},
                ],
                "风险提醒": [{"entity_key":"300394.SZ","text":"光模块价格战风险，ASP -12%"}],
            }
        })
        print(f"抽到 {len(result['signals'])} 条信号，产出 {len(result['drafts'])} 条 draft")
    """

    def __init__(self, classifier: SignalClassifier | None = None) -> None:
        self.classifier = classifier or SignalClassifier()

    # ------------------------------------------------------------------ 抽条目
    def _flatten_to_entries(self, daily_report: dict[str, Any]) -> list[SignalEntry]:
        """从日报结构里把所有"条目"抽平成 SignalEntry 列表（兼容 dict/markdown 文本）"""
        entries: list[SignalEntry] = []
        report_id = daily_report.get("report_id") or f"daily_auto_{uuid.uuid4().hex[:8]}"
        entity_key_default = daily_report.get("theme") or ""

        # Case A：structured 结构 sections 研究结论 / 风险 / 催化都是条目
        sections: dict[str, Any] = daily_report.get("sections") or {}
        for section_name, items in sections.items():
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict):
                        t = item.get("text") or item.get("content") or ""
                        if not t.strip():
                            continue
                        ek = item.get("entity_key") or item.get("ticker") or entity_key_default
                        evids = item.get("evidence_ids") or item.get("evidences") or []
                        entries.append(SignalEntry(
                            entry_id=f"{report_id}_{section_name}_{i}",
                            source_report_id=report_id,
                            source_type="daily",
                            entity_key=str(ek),
                            text=str(t),
                            evidence_ids=[str(x) for x in evids],
                            author=f"daily_section:{section_name}",
                            raw_metadata={"section": section_name, "index": i},
                        ))
                    elif isinstance(item, str):
                        if item.strip():
                            entries.append(SignalEntry(
                                entry_id=f"{report_id}_{section_name}_{i}",
                                source_report_id=report_id,
                                source_type="daily",
                                entity_key=entity_key_default,
                                text=item.strip(),
                                author=f"daily_section:{section_name}",
                                raw_metadata={"section": section_name},
                            ))

        # Case B：没给 sections，但给了 markdown_text，就按句子/列表项拆分（兜底）
        md_text = daily_report.get("markdown_text") or ""
        if md_text and not entries:
            sentences = re.split(r"(?<=[。！？；\n])", md_text)
            for i, s in enumerate(sentences):
                s = s.strip()
                if len(s) < 10:
                    continue
                entries.append(SignalEntry(
                    entry_id=f"{report_id}_md_{i}",
                    source_report_id=report_id,
                    source_type="daily",
                    entity_key=entity_key_default,
                    text=s,
                    author="daily_markdown_splitter",
                ))
        return entries

    # ------------------------------------------------------------------ 生成 draft
    def _make_draft_from_entry(self, entry: SignalEntry) -> WikiDraft:
        score = entry.score
        auto = self.classifier.is_auto_ready(entry)
        entity_type = "company" if (re.search(r"\d{6}\.(SH|SZ|HK)", entry.entity_key)) else (
            "portfolio" if "持仓" in entry.text else (
                "risk" if entry.draft_type == DRAFT_TYPE_RISK_CASE else "theme"
            )
        )
        category = {
            DRAFT_TYPE_STRATEGY: "策略观察",
            DRAFT_TYPE_DECISION: "投资决策",
            DRAFT_TYPE_RISK_CASE: "风险案例",
            DRAFT_TYPE_FACT: "公司研究",
            DRAFT_TYPE_THESIS: "行业主题",
            DRAFT_TYPE_CATALYST: "催化观察",
            DRAFT_TYPE_PLAYBOOK: "操作手册",
        }.get(entry.draft_type, "未分类")

        title_raw = (entry.text[:28] + "…") if len(entry.text) > 28 else entry.text
        approval = "auto_ready" if auto else "pending_manual_review"
        gs = "ready" if auto else "review_required"
        return WikiDraft(
            draft_id=f"wd_{uuid.uuid4().hex[:10]}",
            source_id=entry.source_report_id,
            draft_type=entry.draft_type,
            entity_type=entity_type,
            entity_id=entry.entity_key,
            title=title_raw,
            summary=entry.text,
            candidate_category=category,
            candidate_tags=[entry.draft_type, entry.entity_key, entry.author],
            governance_status=gs,
            approval_status=approval,
            confidence=round(score, 3),
            raw_signal_ref=entry.entry_id,
            content_md=f"# {title_raw}\n\n来源：{entry.source_report_id}（{entry.author}）\n\n{entry.text}\n\n命中：{entry.keywords_hit}",
            upstream_refs=list(entry.evidence_ids),
        )

    # ------------------------------------------------------------------ 主入口
    def ingest_daily_report(self, daily_report: dict[str, Any]) -> dict[str, Any]:
        """
        处理一份日报

        返回（dict）：
            "signals" → list[SignalEntry] 所有抽出来的信号
            "drafts"  → list[WikiDraft]     筛选得分≥threshold 的自动生成草稿
            "by_draft_type" → dict[str, int] 每类 draft 几条，便于日报面板展示
            "auto_ready_count" → int 多少条直接 ready，多少条需人工
            "manual_review_count" → int
        """
        entries = self._flatten_to_entries(daily_report)
        for e in entries:
            self.classifier.classify(e)

        drafts: list[WikiDraft] = []
        for e in entries:
            if self.classifier.should_make_draft(e):
                drafts.append(self._make_draft_from_entry(e))

        by_type: dict[str, int] = {}
        for d in drafts:
            by_type[d.draft_type] = by_type.get(d.draft_type, 0) + 1
        auto_ready = sum(1 for d in drafts if d.approval_status == "auto_ready")
        return {
            "report_id": daily_report.get("report_id", ""),
            "signals": entries,
            "drafts": drafts,
            "by_draft_type": by_type,
            "auto_ready_count": auto_ready,
            "manual_review_count": len(drafts) - auto_ready,
        }
