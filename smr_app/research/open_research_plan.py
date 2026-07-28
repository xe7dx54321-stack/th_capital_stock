"""
开放式研究任务规划器（Open Research Plan）

功能说明：
    把用户自然语言式的开放式任务（例如：
    "去查一下海光信息2026年二季度 DCU 出货量进展和主要风险"、
    "德科立 800G 相干认证有没有新消息？泰国工厂进度如何？"
    ）拆成结构化的抓取任务清单：
    1. 关键词搜索查询（给 Firecrawl.search 用）
    2. 每个查询需要多少结果
    3. 每条结果 URL 的权威等级治理（结合 web_source_registry）
    4. 最终输出 OpenResearchTask，方便 FirecrawlProvider 批量抓取

    注意：本模块只做**规划**，不做实际抓取。
    实际抓取在 AcquisitionKernel + FirecrawlResearchProvider 里跑。

参数说明：
    OpenResearchPlanner.plan(
        *, task_description: str,                  # 开放式任务描述
           entity_hints: list[dict] | None = None, # 实体提示（如 [{"ticker":"688041.SH","name":"海光信息"}]）
           data_types: list[str] | None = None,    # 期望抓取的数据类型（catalysts / risks / orders / ...）
           search_queries_limit_per_entity: int = 4,
           max_urls_total: int = 12,
    ) -> OpenResearchPlan

返回值说明：
    OpenResearchPlan 数据类：
    - task_id: 任务 ID
    - description: 原始任务描述
    - search_queries: list[SearchQuery]（要搜索什么关键词，每条预期拿几条结果，优先级）
    - candidate_urls: list[CandidateUrl]（如果调用方有已知 URL 或搜索完成后回填）
    - entity_context: list[dict]（实体提示，原样透传）
    - desired_data_types: list[str]
    - governance_overrides: dict（治理上限：URL 最高权威，硬黑名单等）
    - warnings: list[str]（任务描述太模糊等提示）

异常处理：
    - 描述过短 / 无法提取实体 / 无数据类型时 → 不抛异常，给出 warnings 并生成保守的通用计划
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


# ============================================================================
# 数据结构
# ============================================================================


@dataclass
class SearchQuery:
    """
    一个搜索查询（将传给 Firecrawl.search）

    小白讲解：
        就像你要去搜索引擎找资料时写的搜索词。
        priority 决定先搜哪个。
    """
    query_id: str
    query_text: str
    priority: str = "important"      # "critical" / "important" / "nice_to_have"
    max_results: int = 5
    reason: str = ""                 # 为什么要搜这个（中文解释，便于后续审计）
    desired_data_types: list[str] = field(default_factory=list)


@dataclass
class CandidateUrl:
    """
    一个要抓取的候选 URL

    小白讲解：
        搜完了得到一堆链接，先过一遍治理，决定抓不抓、
        抓到的内容算什么数据类型、最低权威等级是多少。
        真正抓取在 FirecrawlResearchProvider.acquire 里做。
    """
    url: str
    source: str                     # 来源："search_result" / "known_url" / "entity_official_ir"
    priority: str = "important"
    expected_authority_tier: str = "discovery"
    desired_data_types: list[str] = field(default_factory=list)
    matched_search_query_id: str = ""


@dataclass
class OpenResearchPlan:
    """
    开放式研究任务计划（确定性输出，便于复算）

    小白讲解：
        一份"查资料作业指南"：我要找什么（search_queries）、
        已经有哪些确定的网址（candidate_urls）、
        总共要抓多少条、期望的数据类型、
        以及过程中有哪些需要注意的 warnings。
    """
    plan_id: str
    description: str
    entity_context: list[dict] = field(default_factory=list)
    desired_data_types: list[str] = field(default_factory=list)
    search_queries: list[SearchQuery] = field(default_factory=list)
    candidate_urls: list[CandidateUrl] = field(default_factory=list)
    governance_overrides: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    max_urls_total: int = 12
    created_at: str = ""


# ============================================================================
# 关键词 / 数据类型 词典（确定性，不用 LLM）
# ============================================================================


# 数据类型 -> 触发关键词（中文）。任务描述里出现哪个词，就把对应 data_type 加到 desired_data_types
_DATA_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "catalysts": ("催化", "催化剂", "利好", "订单", "集采", "量产", "发布", "新品", "战略合作"),
    "risks":     ("风险", "隐患", "不利", "利空", "诉讼", "处罚", "警告", "坏账", "下行"),
    "orders":    ("订单", "中标", "签约", "合同", "采购", "集采份额", "发货量", "出货量"),
    "factory":   ("工厂", "投产", "产能", "爬坡", "利用率", "新产线", "泰国工厂", "生产基地"),
    "certifications": ("认证", "过会", "注册", "通过", "资质", "CE ", "FCC ", "入网许可", "供应商代码"),
    "competitor": ("竞品", "竞争", "对手", "份额对比", "降价", "对标"),
    "company_web": ("官网", "公司网站", "投资者关系", "IR页", "公告"),
    "industry_research": ("行业", "协会", "报告", "白皮书", "产业数据", "增速", "规模"),
}

# 通用停用词：在生成搜索 query 前从描述里剥离，避免搜出一堆无用结果
_STOP_WORDS = frozenset({
    "去查一下", "查一下", "帮我查", "看看", "有没有", "请问", "目前", "现在", "最近", "最新消息",
    "进展", "怎么样", "如何", "什么", "哪些", "是不是", "有没有", "关于", "对于", "目前的", "一下",
})


# ============================================================================
# 主类
# ============================================================================


class OpenResearchPlanner:
    """
    开放式研究任务规划器

    小白讲解：
        你给它一句自然语言任务 + 几个实体提示，
        它就给你一张结构化的"作业清单"，
        写清楚了先搜什么关键词、后搜什么关键词、每条拿几个结果、
        抓到的内容算 catalysts/risks/... 里的哪种。
    """

    def __init__(
        self,
        *,
        source_registry: Mapping[str, Any] | None = None,
        default_max_results_per_query: int = 5,
        default_max_urls_total: int = 12,
    ) -> None:
        """
        参数:
            source_registry: 可选，web_source_registry.json 内容；这里只看全局默认，不做实际 URL 治理
            default_max_results_per_query: 每条 search query 默认最多几条结果
            default_max_urls_total: 一个任务总共最多抓多少条 URL（防爆开）
        """
        self._source_registry = dict(source_registry or {})
        self._default_max_results = default_max_results_per_query
        self._default_max_urls = default_max_urls_total

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def plan(
        self,
        *,
        task_description: str,
        entity_hints: list[dict] | None = None,
        data_types: list[str] | None = None,
        search_queries_limit_per_entity: int = 4,
        max_urls_total: int | None = None,
        created_at: Optional[str] = None,
    ) -> OpenResearchPlan:
        """
        生成开放式研究任务计划

        参数:
            task_description: 用户的开放式任务描述（中文自然语言）
            entity_hints: 实体提示，如 [{"ticker":"688041.SH","name":"海光信息"}]
            data_types: 调用方明确指定的数据类型；None 时自动从描述推断
            search_queries_limit_per_entity: 每个实体最多生成几条搜索 query
            max_urls_total: 最多允许产生几个 candidate URL（防爆）；None 时用全局默认
            created_at: ISO 时间字符串，None 时用 plan_id 生成时间（这里不引入 datetime 依赖，写 ""）

        返回:
            OpenResearchPlan
        """
        warnings: list[str] = []
        entities = [dict(e) for e in (entity_hints or [])]
        if not entities:
            warnings.append("未提供实体提示（ticker / 公司名）。查询词将仅基于描述生成，召回可能不够精确。")
        if len(task_description or "") < 8:
            warnings.append(f"任务描述过短（{len(task_description or '')} 字符），可能产生过于宽泛的搜索计划。")

        # 1) 推断 desired_data_types
        desired = self._infer_data_types(task_description, data_types)
        if not desired:
            desired = ["catalysts", "risks", "industry_research"]
            warnings.append("未从描述推断出明确的数据类型，默认抓取催化+风险+行业研究。")

        # 2) 生成 search queries（结合实体 + 数据类型）
        queries: list[SearchQuery] = []
        qid_seen: set[str] = set()
        # 先按实体 × 数据类型 的组合生成核心查询
        if entities:
            for ent in entities[:3]:  # 每个任务最多考虑前 3 个实体，防爆
                name = ent.get("name") or ent.get("entity_name") or ""
                ticker = ent.get("ticker") or ent.get("entity_key") or ""
                label = name or ticker
                if not label:
                    continue
                # 对每个 data_type 生成 1 条核心查询
                added = 0
                for dtype in desired:
                    if added >= search_queries_limit_per_entity:
                        break
                    q_text = self._compose_query(label, dtype, task_description)
                    qid = self._qid(q_text)
                    if qid in qid_seen:
                        continue
                    qid_seen.add(qid)
                    queries.append(SearchQuery(
                        query_id=qid,
                        query_text=q_text,
                        priority="critical" if added == 0 else "important",
                        max_results=self._default_max_results,
                        reason=f"围绕 {label} 的 {dtype} 线索",
                        desired_data_types=[dtype],
                    ))
                    added += 1
        # 再基于描述本身生成 1~2 条通用查询（作为补充）
        for extra in self._general_queries_from_description(task_description, desired, up_to=2):
            qid = self._qid(extra["text"])
            if qid in qid_seen:
                continue
            qid_seen.add(qid)
            queries.append(SearchQuery(
                query_id=qid,
                query_text=extra["text"],
                priority="nice_to_have",
                max_results=self._default_max_results,
                reason=extra.get("reason", "描述级通用查询"),
                desired_data_types=list(desired),
            ))

        if not queries:
            warnings.append("没能生成任何搜索查询（描述太通用）。建议补充实体提示或具体关键词。")
            # 保底 1 条：直接把描述当查询
            fallback = task_description.strip() or "A股 最新 产业动态"
            queries.append(SearchQuery(
                query_id=self._qid(fallback),
                query_text=fallback,
                priority="nice_to_have",
                max_results=max(2, self._default_max_results - 2),
                reason="保底兜底查询（描述太宽泛）",
                desired_data_types=list(desired),
            ))

        # 3) governance_overrides：把 registry 的默认限制透传
        gov = self._source_registry.get("deduplication", {}) or {}
        overrides = {
            "maximum_authority_tier_for_unknown": self._source_registry.get(
                "maximum_authority_tier_for_unknown", "discovery"
            ),
            "url_canonicalization": gov.get("url_canonicalization", []),
            "citation_rules": self._source_registry.get("citation_rules", {}),
        }

        # 4) 组装计划
        max_urls = max_urls_total if max_urls_total is not None else self._default_max_urls
        plan_id = self._plan_id(task_description, entities, desired)
        plan = OpenResearchPlan(
            plan_id=plan_id,
            description=task_description,
            entity_context=entities,
            desired_data_types=list(dict.fromkeys(desired)),
            search_queries=queries,
            candidate_urls=[],  # 留给调用方（执行搜索后）回填
            governance_overrides=overrides,
            warnings=warnings,
            max_urls_total=max_urls,
            created_at=created_at or "",
        )
        return plan

    # ------------------------------------------------------------------
    # 内部工具：数据类型推断
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_data_types(description: str, override: list[str] | None) -> list[str]:
        """从任务描述里推断要抓的数据类型（顺序按出现先后）"""
        if override:
            return list(dict.fromkeys(override))
        desc = description or ""
        order: list[str] = []
        seen: set[str] = set()
        # 先按描述里的关键词命中
        for dtype, kws in _DATA_TYPE_KEYWORDS.items():
            for kw in kws:
                if kw in desc:
                    if dtype not in seen:
                        order.append(dtype)
                        seen.add(dtype)
                    break
        # 命中 company_web 时：官网优先
        if any(h in desc for h in ("官网", "IR页", "公司网站", "投资者关系")):
            if "company_web" not in seen:
                order.insert(0, "company_web")
                seen.add("company_web")
        return order

    # ------------------------------------------------------------------
    # 内部工具：构造搜索词（实体 + 数据类型 + 描述里的细节）
    # ------------------------------------------------------------------

    @staticmethod
    def _compose_query(entity_label: str, dtype: str, description: str) -> str:
        """确定性的 query 构造：实体 + 数据类型主题词 + 描述前 100 字符里的关键词"""
        # 主题词：中文（让普通用户看了也知道在搜啥）
        topic_by_type = {
            "catalysts": "催化剂 订单 量产 发布",
            "risks":     "风险 诉讼 处罚 坏账 下行",
            "orders":    "订单 中标 集采 出货量",
            "factory":   "工厂 投产 产能 爬坡 利用率",
            "certifications": "认证 资质 注册 通过 供应商代码",
            "competitor": "竞品 竞争 份额 降价 对标",
            "company_web": "官网 投资者关系 IR 公告",
            "industry_research": "行业 报告 协会 规模 增速",
        }
        topic = topic_by_type.get(dtype, "")
        # 把描述里的实体相关细节（4~12 字符的独立词组）挑出来，作为增强关键词
        details = OpenResearchPlanner._extract_key_details(description, entity_label)
        parts = [entity_label]
        if topic:
            parts.append(topic)
        if details:
            parts.append(details)
        query = " ".join(p for p in parts if p)
        # 去重（按空格切，保持顺序）
        tokens: list[str] = []
        seen_tok: set[str] = set()
        for tok in query.split():
            if tok in seen_tok or tok in _STOP_WORDS:
                continue
            seen_tok.add(tok)
            tokens.append(tok)
        return " ".join(tokens)

    @staticmethod
    def _extract_key_details(text: str, exclude_entity: str) -> str:
        """从描述里摘出数字、大写字母组合、专有名词（2-6 字）做增强关键词，去掉 entity 本身"""
        if not text:
            return ""
        cleaned = text
        for sw in _STOP_WORDS:
            cleaned = cleaned.replace(sw, " ")
        cleaned = cleaned.replace(exclude_entity, " ") if exclude_entity else cleaned
        # 抓：数字 + "万/亿/颗/G/%"、字母大写串（DCU、GPU、Q2 等）、3~6 字中文专有词
        found: list[str] = []
        for pat in (
            r"\d{1,4}(?:万|亿|颗|G|%|MW|GW)",
            r"[A-Z][A-Z0-9]{1,5}",
            r"[\u4e00-\u9fa5]{3,6}",
        ):
            for m in re.findall(pat, cleaned):
                if m in found or (len(m) <= 1):
                    continue
                found.append(m)
        # 最多取 3 个，避免 query 过长
        return " ".join(found[:3])

    # ------------------------------------------------------------------
    # 内部工具：从描述生成通用查询（不依赖实体）
    # ------------------------------------------------------------------

    @staticmethod
    def _general_queries_from_description(description: str,
                                          data_types: list[str],
                                          up_to: int) -> list[dict[str, str]]:
        desc = description.strip()
        if not desc:
            return []
        clean = desc
        for sw in _STOP_WORDS:
            clean = clean.replace(sw, " ")
        clean = re.sub(r"\s+", " ", clean).strip()
        queries: list[dict[str, str]] = []
        # 1) 直接取描述核心（前 60 字符）
        if len(clean) >= 4:
            queries.append({
                "text": clean[:70].rstrip("，。,. "),
                "reason": "基于原始描述的通用查询",
            })
        # 2) 结合数据类型生成一条
        type_labels = {
            "catalysts": "催化 订单",
            "risks": "风险 利空",
            "orders": "出货量 订单 份额",
            "factory": "工厂 投产 产能",
            "certifications": "认证 注册",
            "competitor": "竞争 份额",
            "industry_research": "行业 规模 增速",
        }
        tag = " ".join(type_labels.get(d, "") for d in data_types if d in type_labels).strip()
        if tag and clean[:60]:
            queries.append({
                "text": f"{clean[:40].rstrip('，。,. ')} {tag}",
                "reason": "在描述基础上叠加数据类型标签",
            })
        return queries[:max(0, up_to)]

    # ------------------------------------------------------------------
    # 内部：ID 哈希（确定性）
    # ------------------------------------------------------------------

    @staticmethod
    def _qid(text: str) -> str:
        return "q_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _plan_id(desc: str, entities: list[dict], dtypes: list[str]) -> str:
        payload = {
            "desc": (desc or "")[:120],
            "ent": [(e.get("ticker") or e.get("entity_key") or e.get("name") or "") for e in entities],
            "dtype": dtypes,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        return "orp_" + hashlib.sha256(encoded).hexdigest()[:20]


# ============================================================================
# 便捷：从文件加载 registry（和 web_document_extractor 同名函数一致）
# ============================================================================


def load_source_registry(path: str | Path | None = None) -> dict[str, Any]:
    """
    从 web_source_registry.json 加载；路径为空用项目默认位置
    """
    if path is None:
        path = Path(__file__).resolve().parents[2] / "00_control" / "web_source_registry.json"
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
