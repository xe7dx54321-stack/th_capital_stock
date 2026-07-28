"""
主题候选宇宙构建器（Theme Universe Builder）

功能说明：
    阶段 7 的第一个模块：解决"AI 算力主题里到底有哪些 A 股能买"的问题。
    不需要产业图谱数据库（那是更后面的阶段），只用确定性输入：
    1. 用户提供的主题名 + 一批候选 ticker；
    2. 或本地已配置的静态 peer_sets.json / thematic_universe_config.json。

    输出一个结构化的「候选宇宙」：每只股票对应主题暴露度、
    收入敏感度、排除原因（如果被排除）。

参数说明：
    ThemeCandidate      - 单只候选股的结构体（小白一眼看懂）
    ThemeUniverse       - 整个主题的候选宇宙（含排除清单）
    ThemeUniverseBuilder.build(theme_name, raw_candidates, config) → ThemeUniverse

返回值说明：
    ThemeUniverse 包含：
        - theme_id / theme_name
        - candidates: 入选列表，每条带业务纯度、收入敏感度、行业标签
        - excluded: 排除列表，每条有排除理由（不满足流动性 / 业务不沾边 / ST股 等）
        - created_at

异常处理：
    - raw_candidates 为空时返回空 universe，不抛异常（工作流后续阶段会处理）
    - 单条候选字段缺失 → 自动降级（purity/confidence 打折扣或进入 excluded）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


# ============================================================================
# 数据结构（小白讲解：每个字段是"档案袋上贴的标签"）
# ============================================================================

@dataclass
class ThemeCandidate:
    """
    一只「主题候选股」的档案

    字段说明（小白版）：
        ticker              - 股票代码，例如 "688041.SH"
        name                - 公司中文名，例如 "海光信息"
        business_purity     - 业务纯度 0~1，1 表示 100% 收入都来自该主题
        revenue_sensitivity - 收入弹性 0~1，主题每增长 10% 公司收入增长多少
        industry            - 一级行业标签（半导体 / 光伏 / 通信 ...）
        sub_sector          - 细分赛道（DCU / 光模块 / 逆变器 ...）
        market_cap_yi       - 最新市值（亿元）
        avg_turnover_yi     - 20 日均成交额（亿元，用于流动性过滤）
        confidence          - 信息置信度 0~1（数据全就高，缺字段就低）
        tags                - 主题关键词命中列表（["AI算力", "国产DCU", "运营商集采"]）
        note                - 备注（一句话，例如"国内 x86 CPU 第一"）
        included            - True 表示进入候选池，False 表示被排除
        exclude_reason      - 如果 included=False，这里写为什么被排除（流动性不够 / 业务不纯 / ST ...）
    """
    ticker: str
    name: str = ""
    business_purity: float = 0.0          # 0.0 ~ 1.0
    revenue_sensitivity: float = 0.0      # 0.0 ~ 1.0
    industry: str = ""
    sub_sector: str = ""
    market_cap_yi: Optional[float] = None
    avg_turnover_yi: Optional[float] = None
    confidence: float = 0.0
    tags: list[str] = field(default_factory=list)
    note: str = ""
    included: bool = True
    exclude_reason: str = ""


@dataclass
class ThemeUniverse:
    """
    一整个主题的候选宇宙

    字段说明（小白版）：
        theme_id      - 主题 ID（下划线命名，例如 "ai_computing_infra"）
        theme_name    - 主题中文名，例如 "AI 算力基础设施"
        candidates    - 入选列表（按综合分排好序）
        excluded      - 被排除列表（每只都带 exclude_reason，保证透明度）
        inclusion_rules - 本次使用的入选规则（方便未来审计：为啥某某股票没入选）
        created_at    - 创建时间 ISO 格式
    """
    theme_id: str
    theme_name: str
    candidates: list[ThemeCandidate] = field(default_factory=list)
    excluded: list[ThemeCandidate] = field(default_factory=list)
    inclusion_rules: dict = field(default_factory=dict)
    created_at: str = ""


# ============================================================================
# 默认入选/排除规则
# ============================================================================

DEFAULT_INCLUSION_RULES: dict = {
    "min_avg_turnover_yi": 0.5,       # 20 日成交额小于 0.5 亿直接排除（流动性风险）
    "min_market_cap_yi": 10.0,        # 市值小于 10 亿直接排除（小票流动性差）
    "min_business_purity": 0.15,      # 业务纯度低于 15% 直接排除（只是"蹭概念"）
    "min_confidence": 0.10,           # 信息太少直接排除（没办法打分）
    "block_patterns": [r"\bST\b", r"\*ST"],  # ST / *ST 直接排除
}


# ============================================================================
# 构建器
# ============================================================================

class ThemeUniverseBuilder:
    """
    主题候选宇宙构建器

    小白讲解：
        这是"海选评委"。
        用户报名了一堆公司，评委先看硬门槛（成交额>5000万？是不是 ST？
        业务是不是真沾边？）——没过的进 excluded，过的进 candidates。
        结果会把淘汰理由写清楚，不会有"黑箱"。
    """

    def __init__(self, rules: Optional[dict] = None):
        """
        初始化构建器（可自定义入选规则，不写就用 DEFAULT）

        参数：
            rules - 字典，覆盖 DEFAULT_INCLUSION_RULES 的任意键（比如想严格点，
                    把 min_avg_turnover_yi 调到 2.0 亿）
        """
        self.rules = dict(DEFAULT_INCLUSION_RULES)
        if rules:
            self.rules.update(rules)

    # ------------------------------------------------------------------
    # 对外：build 入口
    # ------------------------------------------------------------------
    def build(
        self,
        theme_name: str,
        raw_candidates: list[dict],
        theme_id: Optional[str] = None,
        keyword_hint_list: Optional[list[str]] = None,
    ) -> ThemeUniverse:
        """
        根据原始候选列表构建主题候选宇宙

        参数：
            theme_name        - 主题中文名（必填）
            raw_candidates    - 原始候选列表，每项是 dict，至少包含 ticker；可选：
                                name / business_purity / revenue_sensitivity /
                                industry / sub_sector / market_cap_yi /
                                avg_turnover_yi / tags / note
            theme_id          - 主题 ID（不填就从 theme_name 自动翻）
            keyword_hint_list - 主题关键词（如 ["AI算力","光模块"]），用于自动打 tags

        返回：
            ThemeUniverse 对象（永远不会是 None）
        """
        universe = ThemeUniverse(
            theme_id=theme_id or self._theme_name_to_id(theme_name),
            theme_name=theme_name,
            inclusion_rules=dict(self.rules),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        if not raw_candidates:
            # 空输入：返回空宇宙（让上层 workflow 去告警）
            return universe

        keywords = [k.strip() for k in (keyword_hint_list or []) if k.strip()]

        for raw in raw_candidates:
            cand = self._normalize_one(raw, keywords)
            cand = self._apply_rules(cand)
            if cand.included:
                universe.candidates.append(cand)
            else:
                universe.excluded.append(cand)

        # 入选列表按"业务纯度 * 0.6 + 收入敏感度 * 0.4"降序
        universe.candidates.sort(
            key=lambda c: (c.business_purity * 0.6 + c.revenue_sensitivity * 0.4),
            reverse=True,
        )
        return universe

    # ------------------------------------------------------------------
    # 内部：单条规范化
    # ------------------------------------------------------------------
    def _normalize_one(self, raw: dict, keywords: list[str]) -> ThemeCandidate:
        """把一条原始 dict 转成 ThemeCandidate，并自动打 tags / 算置信度"""
        ticker = str(raw.get("ticker", "")).strip()
        name = str(raw.get("name", "")).strip()
        industry = str(raw.get("industry", "")).strip()
        sub_sector = str(raw.get("sub_sector", "")).strip()

        def _to_float(v, default=0.0, lo=0.0, hi=1.0):
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return default
            if fv < lo:
                return lo
            if fv > hi:
                return hi
            return fv

        def _to_float_any(v, default=None):
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        purity = _to_float(raw.get("business_purity"), 0.0, 0.0, 1.0)
        sens = _to_float(raw.get("revenue_sensitivity"), 0.0, 0.0, 1.0)
        mcap = _to_float_any(raw.get("market_cap_yi"), None)
        turn = _to_float_any(raw.get("avg_turnover_yi"), None)

        raw_tags = raw.get("tags") or []
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]
        # 关键词命中 → 自动补充 tag（避免用户漏写）
        text_pool = " ".join([name, industry, sub_sector, str(raw.get("note", ""))])
        for kw in keywords:
            if kw and kw in text_pool and kw not in tags:
                tags.append(kw)

        # 置信度：字段越多越完整，置信度越高
        filled = 0
        total = 5
        if name:
            filled += 1
        if purity > 0:
            filled += 1
        if mcap is not None:
            filled += 1
        if turn is not None:
            filled += 1
        if tags:
            filled += 1
        confidence = round(filled / total, 2)

        return ThemeCandidate(
            ticker=ticker,
            name=name,
            business_purity=purity,
            revenue_sensitivity=sens,
            industry=industry,
            sub_sector=sub_sector,
            market_cap_yi=mcap,
            avg_turnover_yi=turn,
            confidence=confidence,
            tags=tags,
            note=str(raw.get("note", "")).strip(),
            included=True,
            exclude_reason="",
        )

    # ------------------------------------------------------------------
    # 内部：规则过滤（硬门槛）
    # ------------------------------------------------------------------
    def _apply_rules(self, cand: ThemeCandidate) -> ThemeCandidate:
        """把硬门槛规则一条一条地过，任何一条不过就进 excluded"""
        if not cand.ticker:
            cand.included = False
            cand.exclude_reason = "缺少 ticker"
            return cand

        # 1. ST / *ST 规则（只看 name 字段）
        for pat in self.rules.get("block_patterns", []):
            if re.search(pat, cand.name or ""):
                cand.included = False
                cand.exclude_reason = f"公司名命中 {pat}"
                return cand

        # 2. 成交额门槛（防止小票买不进去）
        min_turn = self.rules.get("min_avg_turnover_yi")
        if min_turn and cand.avg_turnover_yi is not None and cand.avg_turnover_yi < min_turn:
            cand.included = False
            cand.exclude_reason = (
                f"20日成交额 {cand.avg_turnover_yi:.2f} 亿"
                f" < 门槛 {min_turn} 亿"
            )
            return cand

        # 3. 市值门槛
        min_mcap = self.rules.get("min_market_cap_yi")
        if min_mcap and cand.market_cap_yi is not None and cand.market_cap_yi < min_mcap:
            cand.included = False
            cand.exclude_reason = (
                f"市值 {cand.market_cap_yi:.2f} 亿 < 门槛 {min_mcap} 亿"
            )
            return cand

        # 4. 业务纯度门槛（过滤"沾点边就来凑热闹"的）
        min_pur = self.rules.get("min_business_purity")
        if min_pur and cand.business_purity < min_pur:
            cand.included = False
            cand.exclude_reason = (
                f"业务纯度 {cand.business_purity:.0%} < 门槛 {min_pur:.0%}"
            )
            return cand

        # 5. 置信度门槛（数据太少不进池）
        min_conf = self.rules.get("min_confidence")
        if min_conf and cand.confidence < min_conf:
            cand.included = False
            cand.exclude_reason = (
                f"信息置信度 {cand.confidence:.0%} < 门槛 {min_conf:.0%}"
            )
            return cand

        return cand

    # ------------------------------------------------------------------
    # 工具：中文名 → snake_case 主题 ID
    # ------------------------------------------------------------------
    @staticmethod
    def _theme_name_to_id(name: str) -> str:
        """
        中文名转英文主题 ID（简单版，够用就行）

        例：AI 算力基础设施 → ai_suan_li_ji_chu_she_shi
        """
        # 简单处理：非字母数字字符全换成 _，再压缩多个 _ 为一个
        tmp = re.sub(r"[^0-9A-Za-z]+", "_", name.strip())
        tmp = re.sub(r"_+", "_", tmp).strip("_").lower()
        return tmp or "unknown_theme"
