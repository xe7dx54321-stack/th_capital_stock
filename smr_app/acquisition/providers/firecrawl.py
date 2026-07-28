"""
Firecrawl Research Provider — 受治理的开放式网页抓取 Provider（阶段 6 核心）

功能说明：
    把 Firecrawl 从旧的新闻正文补充器迁入受治理的 Acquisition Kernel：
    1. 正式的 Provider 接口（acquire(request) -> AcquisitionBatch）
    2. 来源等级治理（用 00_control/web_source_registry.json）
    3. 原文完整保存（不再做 substring(0, 2000) 截断）
    4. 内容哈希幂等去重
    5. 转载去重（优先权威源）
    6. 低质量来源隔离（股吧、自媒体、付费墙检测并降级）
    7. Firecrawl 不可用时 → 明确错误记录 + 局部降级，不阻塞正式公告/财务流程

参数说明：
    FirecrawlResearchProvider(
        *, api_key: str | None = None,        # FIRECRAWL_API_KEY，None 时自动 fallback 到 FakeTransport
           base_url: str = "https://api.firecrawl.dev",
           cache_root: Path | None = None,    # 原始抓取缓存目录
           source_registry: Mapping | None = None,  # web_source_registry.json 加载结果
           transport: FirecrawlTransport | None = None,  # 测试用 FakeTransport 注入点
    )
    .acquire(request: AcquisitionRequest) -> AcquisitionBatch

返回值说明：
    AcquisitionBatch 包含：
    - documents: tuple[SourceDocument]  —— 原始文档（raw_text=完整正文 markdown，raw_payload={raw_html, ...}）
    - facts: tuple[NormalizedFact] —— 阶段 6 不直接产生 normalized fact（需 cross-validate）
    - evidence_candidates: tuple[EvidenceCandidate] —— 仅从"已保存原文"切片产生，不能凭空编造
    - quality_status：文档完整时是 "usable"，数据不足或来源隔离时是 "degraded"

异常处理：
    - Firecrawl 不可用 / 超时 / HTTP 非 200：返回空 AcquisitionBatch + errors metadata，不抛异常阻断 Kernel
    - 来源命中硬黑名单：直接标记为 blocked，不沉淀文档（但会写入 state 说明被 block）
    - 内容哈希已存在于 cache：命中缓存直接返回，不二次抓取
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Optional, Protocol
from urllib.parse import urlparse

from smr_app.acquisition.contracts import (
    AcquisitionBatch,
    AcquisitionMode,
    AcquisitionRequest,
    AuthorityTier,
    DataRequirement,
    EvidenceCandidate,
    SourceDocument,
    authority_meets,
    utc_now,
)
from smr_app.research.web_document_extractor import (
    WebDocumentExtractor,
    WebExtractedDocument,
    canonicalize_url,
    load_source_registry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE_ROOT = PROJECT_ROOT / "01_data" / "acquisition_raw" / "firecrawl"
PARSER_VERSION = "firecrawl-v1.0"

# Firecrawl 支持的数据类型：网页/开放式补证（和交易所/公告的 official_filings 明确分开）
FIRECRAWL_DATA_TYPES = frozenset({
    "web_page", "news", "industry_research", "company_web", "competitor",
    "certifications", "factory", "orders", "catalysts", "risks",
    "open_research", "news_research",
})

FIRECRAWL_MARKETS = frozenset({"A", "CN", "GLOBAL"})


# ============================================================================
# Transport 协议 + Fake（无 API Key 也能跑测试/烟测）
# ============================================================================


class FirecrawlTransport(Protocol):
    """Firecrawl 网络传输层（真实 / Fake 实现同一个协议）"""

    def scrape_url(
        self,
        url: str,
        *,
        formats: list[str],
        only_main_content: bool,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        """
        抓取单个 URL，返回 Firecrawl scrape 响应格式（至少含 markdown/html）。
        失败时抛 Exception（Provider 捕获并降级）。
        """
        ...

    def search(
        self,
        query: str,
        *,
        limit: int,
        timeout_seconds: int,
    ) -> list[dict[str, Any]]:
        """
        搜索关键词，返回 Firecrawl search 响应（每条至少含 url/title）。
        """
        ...


class HttpFirecrawlTransport:
    """真实 Firecrawl HTTP 传输层（通过 requests）"""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "http://127.0.0.1:3002",
        user_agent: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        hostname = (urlparse(self.base_url).hostname or "").lower()
        local_hosts = {"127.0.0.1", "localhost", "host.docker.internal"}
        if not api_key and hostname not in local_hosts:
            raise ValueError("cloud Firecrawl requires FIRECRAWL_API_KEY")
        self.api_key = api_key or ""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": user_agent or "TH-Capital-Research-Bot/1.0",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def scrape_url(
        self,
        url: str,
        *,
        formats: list[str],
        only_main_content: bool,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        # 延迟 import requests：没有 API Key 的开发机不需要装 requests 也能跑测试
        import requests  # type: ignore
        payload = {
            "url": url,
            "formats": formats,
            "onlyMainContent": only_main_content,
        }
        resp = requests.post(
            f"{self.base_url}/v1/scrape",
            headers=self.headers,
            json=payload,
            timeout=timeout_seconds,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Firecrawl scrape HTTP {resp.status_code}: {resp.text[:200]}"
            )
        # 本地 Firecrawl 某些版本返回 application/json 但不带 charset。
        # requests 会按 ISO-8859-1 猜测，最终把中文正文永久写成乱码缓存。
        # JSON API 的线协议统一按 UTF-8 解码。
        resp.encoding = "utf-8"
        data = resp.json()
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            return data["data"]
        return data if isinstance(data, dict) else {}

    def search(
        self,
        query: str,
        *,
        limit: int,
        timeout_seconds: int,
    ) -> list[dict[str, Any]]:
        import requests  # type: ignore
        payload = {"query": query, "limit": limit}
        resp = requests.post(
            f"{self.base_url}/v1/search",
            headers=self.headers,
            json=payload,
            timeout=timeout_seconds,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Firecrawl search HTTP {resp.status_code}: {resp.text[:200]}"
            )
        resp.encoding = "utf-8"
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
            return list(items) if isinstance(items, list) else []
        return []


class FakeFirecrawlTransport:
    """
    Fake 传输层（测试/演示用，不访问网络）

    小白讲解：
        没有 Firecrawl API Key 也能跑 Provider。
        它会根据 URL 返回一份预制的"模拟网页正文"。
    """

    def __init__(self) -> None:
        self.scrape_calls: list[dict[str, Any]] = []
        self.search_calls: list[dict[str, Any]] = []

    # ---- 预制模拟正文 ----
    @staticmethod
    def _sample_markdown(url: str) -> str:
        hostname = urlparse(url).netloc.lower()
        if "cninfo" in hostname or "szse" in hostname or "sse" in hostname:
            return (
                "# 2025 年年度报告\n\n"
                "发布时间：2026-03-31\n\n"
                "## 第一节 重要提示\n\n"
                "本公司董事会、监事会及董事、监事、高级管理人员保证年度报告内容的真实、准确、完整，"
                "不存在虚假记载、误导性陈述或重大遗漏，并承担个别和连带的法律责任。\n\n"
                "## 第二节 公司简介\n\n"
                "公司名称：演示上市公司。\n"
                "主营业务：AI 算力芯片、光伏逆变器、新能源汽车零部件。\n"
                "报告期内，公司实现营业收入 1,200,000 万元，同比增长 15.3%；"
                "实现归属于母公司股东的净利润 86,000 万元，同比增长 22.1%。\n\n"
                "## 第三节 经营情况讨论与分析\n\n"
                "2025 年，行业总体需求稳步增长，公司在 DCU 产品线和海外储能业务上取得突破："
                "DCU 产品全年出货量 45 万颗，同比增长 108%；海外储能订单同比增长 40%。"
                "公司将继续加大研发投入，2026 年研发费用预计不低于营收的 12%。\n"
            )
        if "caixin" in hostname or "36kr" in hostname or "jiemian" in hostname:
            return (
                "# 产业快讯 | 算力需求持续攀升，国产 DCU 厂商订单饱和\n\n"
                "作者：产业组记者\n"
                "发布时间：2026-06-20 09:00\n\n"
                "从三大运营商 2026 年智算集采开标结果看，国产 x86 架构 DCU 的份额已提升至 45%，"
                "较去年同期上升 23 个百分点。供应链人士透露，头部厂商 DCU 封装产能已排至 Q4。\n\n"
                "与此同时，光伏产业链价格出现分化：硅料环节小幅反弹 3%，组件环节仍承压。\n"
                "分析人士指出，二季度海外储能项目交付节奏加快，逆变器厂商 Q2 业绩有望环比改善。\n"
            )
        # 默认：通用公司官网新闻
        return (
            f"# 演示网页：{url}\n\n"
            "发布时间：2026-07-01\n\n"
            "## 业务概览\n\n"
            "公司主营高速光通信模块、光器件与相关解决方案，产品服务于云计算、人工智能基础设施、"
            "相干传输和移动通信网络。公司在研发、制造与供应链方面建立全球化布局，持续投入高速率、"
            "低功耗和高可靠性的光互连技术，并以正式公告和投资者关系材料披露经营进展。\n\n"
            "## 最新动态\n\n"
            "公司新闻中心公布了产品迭代、信息披露评价和供应链 ESG 等最新动态。相关内容只用于"
            "建立研究线索，涉及营收、利润、订单和客户等定量判断时，仍需回到交易所公告、定期报告"
            "或公司正式投资者关系记录进行核验，不能把宣传性文字直接外推为财务预测。\n\n"
            "## 研究边界\n\n"
            "该页面属于公司官方信息入口，可用于确认公司自述的业务范围、官方新闻标题和投资者关系"
            "链接。对市场份额、竞争优势、未来需求和估值的判断，需要结合同行数据、行业资料与独立"
            "媒体报道交叉验证。页面中未提供报告期、口径或单位的数字，不应进入确定性计算。\n"
        )

    def scrape_url(
        self,
        url: str,
        *,
        formats: list[str],
        only_main_content: bool,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        self.scrape_calls.append({
            "url": url, "formats": list(formats),
            "only_main_content": only_main_content, "timeout": timeout_seconds,
        })
        md = self._sample_markdown(url)
        result: dict[str, Any] = {
            "markdown": md,
            "metadata": {
                "title": md.splitlines()[0].lstrip("# ").strip(),
                "author": "Fake Author",
                "ogTitle": md.splitlines()[0].lstrip("# ").strip(),
                "description": "FakeFirecrawlTransport 生成的演示正文",
                "publishedDate": "2026-06-30T10:00:00Z",
            },
        }
        if "html" in formats:
            result["html"] = (
                "<!doctype html><html><head><title>"
                + result["metadata"]["title"]
                + "</title></head><body><article>"
                + "<p>"
                + "</p><p>".join(md.splitlines())
                + "</p></article></body></html>"
            )
        time.sleep(0.01)  # 模拟网络延迟（极短）
        return result

    def search(
        self,
        query: str,
        *,
        limit: int,
        timeout_seconds: int,
    ) -> list[dict[str, Any]]:
        self.search_calls.append({"query": query, "limit": limit, "timeout": timeout_seconds})
        samples = [
            {"url": "https://www.cnstock.com/commonDetail/fixture-article",
             "title": f"上证报报道：{query} — 算力需求"},
            {"url": "https://www.stcn.com/article/detail/fixture-article.html",
             "title": f"证券时报报道：{query} 的产业进展"},
            {"url": "https://www.jiemian.com/article/fixture-article.html",
             "title": f"界面新闻：{query} 相关动态"},
        ]
        return samples[:limit]


# ============================================================================
# 来源治理（基于 web_source_registry.json 的域名匹配）
# ============================================================================


@dataclass
class SiteGovernanceResult:
    """对单个 URL 的来源治理结果"""
    hostname: str
    authority_tier: AuthorityTier
    allowed: bool = True
    blocked_reason: str = ""
    block_type: str = ""              # "hard" / "soft_discovery_only" / ...
    site_name: str = ""
    data_types: list[str] = field(default_factory=list)
    matched_pattern: str = ""


class SourceGovernor:
    """
    来源治理器：按 web_source_registry.json 决定 URL 的 authority / blocked 状态
    """

    def __init__(self, registry: Mapping[str, Any] | None = None) -> None:
        self.registry = dict(registry or {})
        self.default_authority = AuthorityTier(
            self.registry.get("default_authority_tier", "reputable_secondary")
        )
        self.unknown_max_tier = AuthorityTier(
            self.registry.get("maximum_authority_tier_for_unknown", "discovery")
        )

    @staticmethod
    def _hostname(url: str) -> str:
        try:
            return (urlparse(url).netloc or "").lower()
        except Exception:
            return ""

    @staticmethod
    def _match(pattern: str, hostname: str) -> bool:
        """
        通配符 hostname 匹配（确定性实现，小白讲解：
            "*.36kr.com" → 匹配 www.36kr.com  AND  36kr.com
            "*toutiao.com" → 匹配 www.toutiao.com  AND  toutiao.com
            "miit.gov.cn" → 精确匹配
        ）
        """
        if not pattern or not hostname:
            return False
        pat = pattern.lower()
        hn = hostname
        if pat == hn:
            return True
        # 通用前缀通配：*xxxx
        if pat.startswith("*"):
            suffix = pat[1:]
            # 规范化：去掉 suffix 开头的点（便于统一比较）
            suffix_clean = suffix.lstrip(".")            # "36kr.com" / "toutiao.com"
            return (
                hn == suffix_clean
                or hn.endswith("." + suffix_clean)
            )
        return False

    def govern(self, url: str) -> SiteGovernanceResult:
        """对 URL 做治理：返回 authority_tier + 是否允许抓取"""
        hn = self._hostname(url)
        # 先查 hard/soft block
        for entry in self.registry.get("blocked_sites", []):
            if self._match(entry.get("hostname_pattern", ""), hn):
                bt = entry.get("block_type", "hard")
                if bt == "hard":
                    return SiteGovernanceResult(
                        hostname=hn,
                        authority_tier=AuthorityTier.DISCOVERY,
                        allowed=False,
                        blocked_reason=entry.get("reason", "硬黑名单命中"),
                        block_type="hard",
                        matched_pattern=entry.get("hostname_pattern", ""),
                    )
                if bt == "soft_discovery_only":
                    return SiteGovernanceResult(
                        hostname=hn,
                        authority_tier=AuthorityTier.DISCOVERY,
                        allowed=True,
                        block_type="soft_discovery_only",
                        site_name="软屏蔽：仅允许 discovery 级线索",
                        matched_pattern=entry.get("hostname_pattern", ""),
                    )
                if bt == "search_result_only":
                    return SiteGovernanceResult(
                        hostname=hn,
                        authority_tier=AuthorityTier.DISCOVERY,
                        allowed=False,
                        blocked_reason=entry.get("reason", "仅允许用作搜索入口，不可抓取正文"),
                        block_type="search_result_only",
                        matched_pattern=entry.get("hostname_pattern", ""),
                    )
                # restrict_authority_to_reputable 等：先允许，再限 authority
        # 再查 allowed_sites
        for entry in self.registry.get("allowed_sites", []):
            if self._match(entry.get("hostname_pattern", ""), hn):
                tier = AuthorityTier(entry.get("authority_tier", self.default_authority.value))
                return SiteGovernanceResult(
                    hostname=hn,
                    authority_tier=tier,
                    allowed=True,
                    site_name=entry.get("site_name", ""),
                    data_types=list(entry.get("data_types", [])),
                    matched_pattern=entry.get("hostname_pattern", ""),
                )
        # 未知来源：按最大未知上限（通常是 DISCOVERY）
        return SiteGovernanceResult(
            hostname=hn,
            authority_tier=self.unknown_max_tier,
            allowed=True,
            site_name="未知来源：按最大未知上限治理",
        )


# ============================================================================
# Firecrawl Research Provider 主类
# ============================================================================


class FirecrawlResearchProvider:
    """
    Firecrawl 受治理网页抓取 Provider（阶段 6 核心）

    小白讲解：
        你给它一个 AcquisitionRequest（要求：data_type=web_page、
        metadata.urls=[要抓的网址]），它就：
        ① 先查来源注册表决定每个网址的权威等级和是否被屏蔽
        ② 命中缓存就直接复用，不再重复抓
        ③ 通过 Firecrawl 抓取 → 清洗 → 生成 SourceDocument + EvidenceCandidate
        ④ 如果 Firecrawl 崩了，也会把错误记到 AcquisitionResult.errors，
          不会把交易所 Provider 的正式流程搞挂。
    """

    provider_id = "firecrawl_research"
    priority = 80                          # 低于交易所官方（95+），高于二次猜测
    authority_tier = AuthorityTier.REPUTABLE_SECONDARY
    data_types = FIRECRAWL_DATA_TYPES
    markets = FIRECRAWL_MARKETS

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        cache_root: str | Path = DEFAULT_CACHE_ROOT,
        source_registry: Mapping[str, Any] | None = None,
        transport: FirecrawlTransport | None = None,
        extractor: WebDocumentExtractor | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        # 生产默认连接本地自托管 Firecrawl。Fake 只能通过测试显式注入，绝不静默伪造正文。
        if transport is not None:
            self._transport: FirecrawlTransport = transport
            self._transport_mode = "explicit"
        else:
            key = api_key if api_key is not None else os.environ.get("FIRECRAWL_API_KEY")
            resolved_base_url = (
                base_url
                or os.environ.get("FIRECRAWL_BASE_URL")
                or "http://127.0.0.1:3002"
            )
            self._transport = HttpFirecrawlTransport(api_key=key, base_url=resolved_base_url)
            hostname = (urlparse(resolved_base_url).hostname or "").lower()
            self._transport_mode = (
                "local_http"
                if hostname in {"127.0.0.1", "localhost", "host.docker.internal"}
                else "cloud_http"
            )
        self._cache_root = Path(cache_root)
        self._source_registry = dict(source_registry or load_source_registry())
        self._governor = SourceGovernor(self._source_registry)
        self._extractor = extractor or WebDocumentExtractor(
            source_registry=self._source_registry,
        )
        self._clock = clock

    def _timeout_seconds(self) -> int:
        configured = int(os.environ.get("FIRECRAWL_TIMEOUT_SECONDS") or 10)
        registry_timeout = int(
            self._source_registry.get("global_defaults", {}).get("timeout_seconds", configured)
        )
        return max(2, min(configured, registry_timeout, 30))

    # ------------------------------------------------------------------
    # 缓存管理：基于 canonical_url + content_hash
    # ------------------------------------------------------------------

    def _cache_path(self, canonical_url: str) -> Path:
        safe = re.sub(r"[^a-zA-Z0-9.-]", "_", canonical_url)[:120]
        h = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:12]
        return self._cache_root / f"{safe}_{h}.json"

    def _read_cached_doc(self, url: str) -> Optional[WebExtractedDocument]:
        """命中缓存且 url + hash 一致，返回 WebExtractedDocument；否则 None"""
        p = self._cache_path(canonicalize_url(url))
        if not p.exists():
            return None
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            # 弱约束：key 对得上就算命中
            if obj.get("canonical_url") == canonicalize_url(url):
                return self._dict_to_doc(obj)
        except Exception:
            return None
        return None

    def _write_cached_doc(self, doc: WebExtractedDocument) -> None:
        p = self._cache_path(doc.canonical_url or canonicalize_url(doc.url))
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self._doc_to_dict(doc), ensure_ascii=False, indent=2),
                         encoding="utf-8")
        except Exception:
            # 缓存写入失败不影响主流程
            pass

    @staticmethod
    def _doc_to_dict(doc: WebExtractedDocument) -> dict[str, Any]:
        return {
            "url": doc.url,
            "canonical_url": doc.canonical_url,
            "title": doc.title,
            "author": doc.author,
            "published_at": doc.published_at,
            "fetched_at": doc.fetched_at,
            "lang": doc.lang,
            "raw_html": doc.raw_html,
            "raw_markdown": doc.raw_markdown,
            "cleaned_markdown": doc.cleaned_markdown,
            "content_blocks": [
                {
                    "block_index": b.block_index,
                    "block_type": b.block_type,
                    "text": b.text,
                    "raw_start_char": b.raw_start_char,
                    "raw_end_char": b.raw_end_char,
                }
                for b in doc.content_blocks
            ],
            "ads_removed": doc.ads_removed,
            "nav_removed": doc.nav_removed,
            "footer_removed": doc.footer_removed,
            "paywall_detected": doc.paywall_detected,
            "extraction_quality": doc.extraction_quality,
            "content_hash": doc.content_hash,
            "metadata": dict(doc.metadata),
            "warnings": list(doc.warnings),
        }

    @staticmethod
    def _dict_to_doc(obj: Mapping[str, Any]) -> WebExtractedDocument:
        from smr_app.research.web_document_extractor import ContentBlock
        blocks = [
            ContentBlock(
                block_index=int(b.get("block_index", i)),
                block_type=str(b.get("block_type", "paragraph")),
                text=str(b.get("text", "")),
                raw_start_char=int(b.get("raw_start_char", 0)),
                raw_end_char=int(b.get("raw_end_char", 0)),
            )
            for i, b in enumerate(obj.get("content_blocks", []))
        ]
        return WebExtractedDocument(
            url=str(obj.get("url", "")),
            canonical_url=str(obj.get("canonical_url", "")),
            title=str(obj.get("title", "")),
            author=str(obj.get("author", "")),
            published_at=obj.get("published_at"),
            fetched_at=str(obj.get("fetched_at", "")),
            lang=str(obj.get("lang", "")),
            raw_html=str(obj.get("raw_html", "")),
            raw_markdown=str(obj.get("raw_markdown", "")),
            cleaned_markdown=str(obj.get("cleaned_markdown", "")),
            content_blocks=blocks,
            ads_removed=int(obj.get("ads_removed", 0)),
            nav_removed=int(obj.get("nav_removed", 0)),
            footer_removed=int(obj.get("footer_removed", 0)),
            paywall_detected=bool(obj.get("paywall_detected", False)),
            extraction_quality=str(obj.get("extraction_quality", "fair")),
            content_hash=str(obj.get("content_hash", "")),
            metadata=dict(obj.get("metadata", {})),
            warnings=list(obj.get("warnings", [])),
        )

    # ------------------------------------------------------------------
    # 主入口：acquire()
    # ------------------------------------------------------------------

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        req_meta: MutableMapping[str, Any] = dict(request.requirement.metadata or {})
        urls = self._extract_urls(request, req_meta)
        search_errors: list[str] = []
        search_queries_used: list[str] = []
        search_candidate_count = 0
        if not urls:
            configured_queries = req_meta.get("search_queries")
            primary_query = str(
                req_meta.get("search_query")
                or req_meta.get("query")
                or f"{request.requirement.entity_key} 最新公告 经营进展 风险"
            ).strip()
            queries = list(dict.fromkeys(
                [primary_query]
                + (
                    [str(item).strip() for item in configured_queries if str(item).strip()]
                    if isinstance(configured_queries, list)
                    else []
                )
            ))
            requested_limit = max(1, min(int(req_meta.get("search_limit") or 4), 8))
            combined_items: list[dict[str, Any]] = []
            for query in queries[:6]:
                search_queries_used.append(query)
                try:
                    items = self._transport.search(
                        query,
                        # 先多取候选，再做文章页/相关性过滤，避免前四条全是行情页。
                        limit=max(12, requested_limit * 4),
                        timeout_seconds=self._timeout_seconds(),
                    )
                    combined_items.extend(items)
                except Exception as exc:
                    search_errors.append(
                        f"Firecrawl search 失败 ({query[:80]}): "
                        f"{exc.__class__.__name__}: {str(exc)[:300]}"
                    )
            search_candidate_count = len(combined_items)
            urls = self._extract_search_urls(
                combined_items,
                relevance_terms=[
                    str(term).lower()
                    for term in (req_meta.get("relevance_terms") or [])
                    if str(term).strip()
                ],
                allowed_domains=[
                    str(domain).lower().strip()
                    for domain in (req_meta.get("preferred_domains") or [])
                    if str(domain).strip()
                ],
            )[:requested_limit]
        batch_docs: list[SourceDocument] = []
        batch_evs: list[EvidenceCandidate] = []
        # provider 级别 metadata（给 AcquisitionResult.errors/补充信息看）
        batch_meta: dict[str, Any] = {
            "transport_mode": self._transport_mode,
            "governed_urls": [],
            "blocked_urls": [],
            "firecrawl_errors": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "search_queries": search_queries_used,
            "search_candidate_count": search_candidate_count,
            "accepted_search_urls": list(urls),
        }
        batch_meta["firecrawl_errors"].extend(search_errors)

        quality_status = "usable"
        is_complete = True
        if search_errors or not urls:
            quality_status = "degraded"
            is_complete = False
        required_fields_present: list[str] = []

        for u in urls:
            # 1) 来源治理
            gov = self._governor.govern(u)
            batch_meta["governed_urls"].append({
                "url": u, "hostname": gov.hostname,
                "authority_tier": gov.authority_tier.value,
                "allowed": gov.allowed, "matched_pattern": gov.matched_pattern,
            })
            if not gov.allowed:
                batch_meta["blocked_urls"].append({
                    "url": u, "reason": gov.blocked_reason or "来源不允许",
                    "block_type": gov.block_type,
                })
                # 被 block 的 URL：不全额取消整个 batch，只把整体质量降到 degraded
                quality_status = "degraded"
                is_complete = False
                continue
            # 2) 最小权威门：请求要求 minimum_authority 时，不满足的也跳过但给 degraded
            if not authority_meets(gov.authority_tier, request.requirement.minimum_authority):
                batch_meta["firecrawl_errors"].append(
                    f"URL {u} 实际权威 {gov.authority_tier.value} "
                    f"< 请求要求最低 {request.requirement.minimum_authority.value}，降级为仅线索"
                )
                quality_status = "degraded"
                is_complete = False
                continue
            # 3) 缓存命中
            cached = None
            if request.mode != AcquisitionMode.FORCE_REFRESH:
                cached = self._read_cached_doc(u)
            if cached is not None:
                batch_meta["cache_hits"] += 1
                extracted = cached
            else:
                batch_meta["cache_misses"] += 1
                # 4) 真正抓取（Firecrawl）
                try:
                    scrape_result = self._transport.scrape_url(
                        u,
                        formats=["markdown", "html"],
                        # 新闻研究需要正文，不应把站点导航、行情组件和页脚当作证据。
                        only_main_content=True,
                        timeout_seconds=self._timeout_seconds(),
                    )
                except Exception as e:
                    msg = f"Firecrawl scrape 失败 {u}: {e.__class__.__name__}: {e}"
                    batch_meta["firecrawl_errors"].append(msg)
                    quality_status = "degraded"
                    is_complete = False
                    continue
                md = scrape_result.get("markdown") or ""
                htm = scrape_result.get("html") or ""
                src_meta = scrape_result.get("metadata") or {}
                # 5) 抽取 + 清洗（WebDocumentExtractor）
                try:
                    prefer_md = bool(md) and len(md) > 100
                    extracted = self._extractor.extract(
                        md if prefer_md else htm,
                        url=u,
                        fetched_at=self._clock(),
                        prefer_markdown=prefer_md,
                    )
                except Exception as e:
                    msg = f"正文抽取失败 {u}: {e.__class__.__name__}: {e}"
                    batch_meta["firecrawl_errors"].append(msg)
                    quality_status = "degraded"
                    is_complete = False
                    continue
                # 元数据回灌：Firecrawl metadata 里若有更准的 title/published_at，用它
                if src_meta:
                    t = src_meta.get("title") or src_meta.get("ogTitle")
                    if t and not extracted.title:
                        extracted.title = str(t)
                    pd = src_meta.get("publishedDate") or src_meta.get("date")
                    if pd and not extracted.published_at:
                        extracted.published_at = str(pd)
                    au = src_meta.get("author")
                    if au and not extracted.author:
                        extracted.author = str(au)
                    # Firecrawl 的标题常在 metadata，而 markdown 本身没有一级标题。
                    # 质量估计发生在抽取阶段，必须在元数据回灌后重算，否则正文完整的
                    # 官方页面会因为“抽取时无标题”被永久误判为 poor。
                    self._extractor.refresh_quality(extracted)
                # HTML 原文保留：如果有就塞进 raw_html
                if htm and not extracted.raw_html:
                    extracted.raw_html = htm
                # 6) 写入缓存
                self._write_cached_doc(extracted)

            # 7) 生成 SourceDocument
            src_id = f"firecrawl:{gov.hostname}:{extracted.content_hash[:16]}"
            # 实际权威等级 = 来源治理等级（不是 provider 自身的 authority_tier）
            authority_for_doc = gov.authority_tier
            doc = SourceDocument.build(
                source_id=src_id,
                entity_key=request.requirement.entity_key,
                data_type=request.requirement.data_type,
                source_type="web_page",
                authority_tier=authority_for_doc,
                title=extracted.title or f"网页：{gov.hostname}",
                fetched_at=self._clock(),
                source_url=extracted.url,
                published_at=extracted.published_at,
                raw_text=extracted.cleaned_markdown,
                raw_payload={
                    "extraction_quality": extracted.extraction_quality,
                    "governance": {
                        "hostname": gov.hostname,
                        "matched_pattern": gov.matched_pattern,
                        "authority_tier": authority_for_doc.value,
                        "site_name": gov.site_name,
                    },
                    "canonical_url": extracted.canonical_url,
                    "content_blocks": [self._doc_to_dict(extracted)],  # 小冗余，便于回溯
                    "warnings": extracted.warnings,
                },
                parser_version=PARSER_VERSION,
                metadata={
                    "raw_markdown_size": len(extracted.raw_markdown),
                    "raw_html_size": len(extracted.raw_html),
                    "cleaned_markdown_size": len(extracted.cleaned_markdown),
                    "content_hash": extracted.content_hash,
                    "author": extracted.author,
                    "lang": extracted.lang,
                    "paywall_detected": extracted.paywall_detected,
                    "ads_removed": extracted.ads_removed,
                    "nav_removed": extracted.nav_removed,
                    "footer_removed": extracted.footer_removed,
                    "cache_hit": cached is not None,
                    "transport_mode": self._transport_mode,
                },
            )
            batch_docs.append(doc)

            # 8.1) 低质量文档来源/付费墙 → 整个 Batch 质量降级（但仍保留文档作为线索）
            if extracted.paywall_detected:
                quality_status = "degraded"
                is_complete = False
                batch_meta.setdefault("low_quality_flags", []).append(
                    f"{u}: PAYWALL 付费墙"
                )
            if extracted.extraction_quality == "poor" or authority_for_doc == AuthorityTier.DISCOVERY:
                quality_status = "degraded"
                is_complete = False
                batch_meta.setdefault("low_quality_flags", []).append(
                    f"{u}: quality={extracted.extraction_quality} authority={authority_for_doc.value}"
                )

            # 9) 产生 EvidenceCandidate（阶段 6：只能从已保存原文切片，不能凭空生成 claim）
            for ev in self._build_evidence_candidates(
                request, doc, extracted, authority_for_doc
            ):
                batch_evs.append(ev)

        # 可选：把 content_hash / cleaned_markdown 凑够了标成 required_fields
        if batch_docs:
            required_fields_present.append("raw_document")
            required_fields_present.append("source_url")
            required_fields_present.append("cleaned_markdown")
            required_fields_present.append("content_hash")
        if batch_evs:
            required_fields_present.append("evidence_candidates")

        return AcquisitionBatch(
            documents=tuple(batch_docs),
            facts=(),            # 阶段 6 不直接产生 NormalizedFact（需 cross-validate）
            evidence_candidates=tuple(batch_evs),
            required_fields_present=tuple(dict.fromkeys(required_fields_present)),
            quality_status=quality_status,
            is_complete=is_complete,
            metadata=batch_meta,
        )

    @staticmethod
    def _extract_search_urls(
        items: list[dict[str, Any]],
        *,
        relevance_terms: list[str] | None = None,
        allowed_domains: list[str] | None = None,
    ) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        terms = [term for term in (relevance_terms or []) if term]
        domains = [domain.lstrip(".") for domain in (allowed_domains or []) if domain]
        non_article_path_markers = (
            "/quotes/",
            "/notices/stock/",
            "/corp/go.php",
            "allmemorddetail",
        )
        for item in items:
            raw = item.get("url") if isinstance(item, dict) else None
            if not isinstance(raw, str) or not raw.startswith(("http://", "https://")):
                continue
            parsed = urlparse(raw)
            hostname = (parsed.hostname or "").lower()
            if domains and not any(
                hostname == domain or hostname.endswith(f".{domain}")
                for domain in domains
            ):
                continue
            path_and_query = f"{parsed.path}?{parsed.query}".lower()
            if any(marker in path_and_query for marker in non_article_path_markers):
                continue
            searchable = " ".join(
                str(item.get(key) or "")
                for key in ("title", "description", "url")
            ).lower()
            if terms and not any(term in searchable for term in terms):
                continue
            canonical = canonicalize_url(raw)
            if canonical in seen:
                continue
            seen.add(canonical)
            urls.append(raw)
        return urls

    # ------------------------------------------------------------------
    # 辅助：从 request 里拿 URLs（支持 metadata.urls / metadata.url）
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_urls(
        request: AcquisitionRequest, meta: MutableMapping[str, Any]
    ) -> list[str]:
        urls: list[str] = []
        for key in ("urls", "url_list"):
            v = meta.get(key)
            if isinstance(v, list):
                for u in v:
                    if isinstance(u, str) and u:
                        urls.append(u)
        u = meta.get("url")
        if isinstance(u, str) and u:
            urls.append(u)
        if not urls:
            # 如果 requirement 没传 URL，也允许把 entity_key 当关键词来 search（走 search）
            # 但这里先不做搜索式，避免把抓取规模搞太大；记空列表让调用方自行判断
            pass
        # 去重（按原始 URL 顺序保留第一个）
        seen: set[str] = set()
        result: list[str] = []
        for u in urls:
            c = canonicalize_url(u)
            if c in seen:
                continue
            seen.add(c)
            result.append(u)
        return result

    # ------------------------------------------------------------------
    # 辅助：基于已保存正文，生成 EvidenceCandidate（确定性，非 LLM）
    # ------------------------------------------------------------------

    def _build_evidence_candidates(
        self,
        request: AcquisitionRequest,
        doc: SourceDocument,
        extracted: WebExtractedDocument,
        authority: AuthorityTier,
    ) -> list[EvidenceCandidate]:
        """
        基于保存的原文生成 EvidenceCandidate（确定性切分）：
        每个 content_block 的 paragraph/heading/quote 都产生一个候选，
        明确 source_document_ids=[doc.document_id]，并且在 metadata 里写 block_index。
        """
        out: list[EvidenceCandidate] = []
        min_chars = int(
            (self._source_registry.get("reputation_checks", {}) or {}).get("minimum_text_length_chars", 200)
        )
        for block in extracted.content_blocks:
            if len(block.text) < max(40, min_chars // 5):
                continue
            try:
                ev = EvidenceCandidate.build(
                    entity_key=request.requirement.entity_key,
                    data_type=request.requirement.data_type,
                    claim_type=f"excerpt:{block.block_type}",
                    text=block.text,
                    source_document_ids=(doc.document_id,),
                    authority_tier=authority,
                    occurred_at=extracted.published_at,
                    usable_for=("context",),  # 仅可用于上下文，不可直接当事实
                    status="pending_validation",
                    metadata={
                        "block_index": block.block_index,
                        "block_type": block.block_type,
                        "char_range": [block.raw_start_char, block.raw_end_char],
                        "content_hash_prefix": extracted.content_hash[:16],
                    },
                )
                out.append(ev)
            except Exception:
                # 单个 block 构造失败不影响其他
                continue
        # 最多保留 25 个（防止一篇超长网页产生几百个候选撑爆空间）
        return out[:25]


# ============================================================================
# 默认单例（可选 import，不强制创建 HTTP 连接）
# ============================================================================


def default_firecrawl_provider() -> FirecrawlResearchProvider:
    return FirecrawlResearchProvider()
