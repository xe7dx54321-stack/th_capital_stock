"""
网页正文抽取与清洗模块（Web Document Extractor）

功能说明：
    从原始 HTML（或 Firecrawl 返回的 markdown/html）中：
    1. 识别标题、作者、发布时间、正文
    2. 剥离导航、广告、推荐阅读、页脚版权等噪声
    3. 输出结构化的 WebExtractedDocument，供后续 EvidenceCandidate 使用
    4. 保留**完整**原文（不再做 substring(0, 2000) 的截断），满足阶段 6 验收

参数说明：
    WebDocumentExtractor.extract(raw_html, *, url, source_registry)
        - raw_html: 原始 HTML 字符串或 Firecrawl 返回的 markdown
        - url: 页面 URL（用于域名识别、来源等级判定、幂等去重）
        - source_registry: 可选，web_source_registry.json 的加载结果

返回值说明：
    WebExtractedDocument 数据类，包含：
    - url, title, author, published_at（页面发布时间）, fetched_at（抓取时间）
    - raw_html / raw_markdown（完整原文，不截断）
    - cleaned_markdown（清洗后正文 markdown，导航/广告等已删）
    - content_blocks（结构化段落列表，用于 EvidenceCandidate 引用片段位置）
    - ads_removed, nav_removed, footer_removed（清洗动作计数）
    - extraction_quality：估计的抽取质量（good/fair/poor）
    - warnings：提取过程中的警告（如发布时间缺失、疑似付费墙等）

异常处理：
    HTML 解析失败时不抛异常，回退为"原文 + 降级标记"，保证 Provider 总能返回可记录的文档。
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional


# ============================================================================
# 数据结构
# ============================================================================


@dataclass
class ContentBlock:
    """
    正文里的一个段落块（供 EvidenceCandidate 引用片段位置时使用）

    小白讲解：
        每一段正文都会编号，之后如果 Agent 说"这段证明了 XXX"，
        我们就能精确回溯到第几个段落的哪几行。
    """
    block_index: int                 # 第几个段落块（从 0 开始）
    block_type: str                  # "heading" / "paragraph" / "list" / "table" / "quote"
    text: str                        # 块内文本（清洗后，不含噪声）
    raw_start_char: int = 0          # 在 cleaned_markdown 中的起始字符位置（用于引用定位）
    raw_end_char: int = 0            # 在 cleaned_markdown 中的结束字符位置
    source_section: str = ""         # 来源位置描述（如 "第2节"、"表格" 等）


@dataclass
class WebExtractedDocument:
    """
    从网页里抽取出来的结构化文档

    小白讲解：
        拿到原始 HTML 后，这个对象就是"洗完的干净文档"。
        重要：raw_html / raw_markdown 永远不截断，
        以后需要复查就看原文，不会丢失证据。
    """
    url: str
    canonical_url: str = ""                          # URL 规范化后的地址（去掉 utm_*、fragment 等）
    title: str = ""
    author: str = ""
    published_at: Optional[str] = None               # 页面发布时间（ISO 字符串），缺失为 None
    fetched_at: str = ""                             # 抓取时间（ISO 字符串）
    lang: str = ""                                   # "zh-CN" / "en" 等，空=未识别
    raw_html: str = ""                               # 完整原始 HTML，**永远不做截断**
    raw_markdown: str = ""                           # Firecrawl 直接给的 markdown（如果有）
    cleaned_markdown: str = ""                       # 清洗后正文 markdown（已去广告/导航/页脚）
    content_blocks: list[ContentBlock] = field(default_factory=list)
    ads_removed: int = 0                             # 删除的广告块数量
    nav_removed: int = 0                             # 删除的导航块数量
    footer_removed: int = 0                          # 删除的页脚块数量
    paywall_detected: bool = False                   # 是否疑似付费墙
    extraction_quality: str = "fair"                 # "good" / "fair" / "poor"
    content_hash: str = ""                           # 正文内容哈希（SHA-256，供幂等去重）
    metadata: Mapping[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ============================================================================
# 常量（噪声标签黑名单，兼顾中英文网站）
# ============================================================================

# CSS class/id 关键字 → 如果标签的 class/id 包含这些词，就判定为噪声
_NAV_KEYWORDS = (
    "nav", "menu", "header", "topbar", "breadcrumb", "side", "sidebar",
    "catalog", "目录", "导航", "菜单栏", "顶部", "面包屑",
)

_AD_KEYWORDS = (
    "ad-", "_ad_", "ads-", "advert", "banner", "promo", "promotion",
    "sponsor", "recommend", "related", "hot-articles", "猜你喜欢",
    "相关推荐", "广告", "推广", "赞助", "热门推荐", "为您推荐",
    "广告位", "banner_ad", "right-rail", "悬浮",
)

_FOOTER_KEYWORDS = (
    "footer", "copyright", "页脚", "版权", "备案", "关于我们", "联系方式",
    "免责声明", "友情链接", "disclaimer", "site-map",
)

# 付费墙关键字（中文常见）
_PAYWALL_KEYWORDS = (
    "订阅", "付费后可", "付费可读", "VIP 专享", "VIP专享",
    "解锁全文", "登录后继续阅读", "成为会员", "会员免费",
    "购买后查看", "扫码阅读全文",
)

# 正文标签（HTML 语义化标签里优先找正文）
_MAIN_CONTENT_TAGS = {
    "article", "main", "section", "div", "content", "post",
    "news-content", "article-content", "detail-content",
}


# ============================================================================
# URL 规范化工具（供幂等去重使用）
# ============================================================================


def canonicalize_url(url: str) -> str:
    """
    URL 规范化：去掉 utm_*、跟踪参数、fragment，强制 https

    小白讲解：
        同一篇文章可能被分享成 N 种 URL（有的带 utm_source=wechat、
        有的带 #comment、有的是 http）。统一成一种形式，
        就不会在数据库里重复存同一篇文章。
    """
    if not url:
        return ""
    try:
        stripped = url.strip()
        parsed = urllib.parse.urlparse(stripped)
        # 小白：如果连 scheme 和 netloc 都没有，并且内容里还有空格或特殊字符，
        # 就认为它不是 URL 而是一段普通文字（比如用户测试输入 "not a url"），
        # 直接原样返回，避免被糊成 "https:///not a url" 这种错误形态。
        has_scheme_or_netloc = bool(parsed.scheme or parsed.netloc)
        looks_like_plain_text = (not has_scheme_or_netloc) and (
            " " in stripped or not parsed.path or not re.search(r"[./]", stripped)
        )
        if looks_like_plain_text:
            return stripped
        scheme = "https" if parsed.scheme in ("http", "https", "") else parsed.scheme
        netloc = parsed.netloc.lower()
        # 过滤查询参数：删除 utm_* 和常见跟踪参数
        filtered_query_pairs: list[tuple[str, str]] = []
        for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
            k_lower = k.lower()
            if (k_lower.startswith("utm_")
                    or k_lower in ("spm", "from", "source", "share", "sharer_sharetime",
                                   "sharer_shareid", "clicktime", "enterid", "timestamp",
                                   "timestamp_ms", "_t", "_bid", "cur_album_id", "appinstall")):
                continue
            filtered_query_pairs.append((k, v))
        query = urllib.parse.urlencode(filtered_query_pairs)
        # path 保留原样，但 // 归一化成 /
        path = re.sub(r"/+", "/", parsed.path or "/")
        rebuilt = urllib.parse.urlunparse((
            scheme, netloc, path,
            "",  # params（不保留 ;type 这种）
            query,
            "",  # fragment 全删
        ))
        return rebuilt
    except Exception:
        # 解析失败就返回去前后空白的原始值（最差情况），绝不抛异常
        return url.strip()


# ============================================================================
# 正文抽取器主类
# ============================================================================


class WebDocumentExtractor:
    """
    网页正文抽取 + 噪声清洗器

    小白讲解：
        交给我一段 HTML（或者 Firecrawl 抓来的 markdown），
        我就能吐出结构化的正文文档，广告、导航、推荐都删掉，
        标题、作者、发布时间尽力识别，找不到就标 None/空。
    """

    def __init__(
        self,
        *,
        source_registry: Mapping[str, Any] | None = None,
        max_chars: int = 200_000,
    ) -> None:
        """
        参数:
            source_registry: web_source_registry.json 映射，用于域名治理
            max_chars: 最多处理的字符数（超过则截断并标降级；注意是 *处理上限* 不是 *截断保存*）
        """
        self._source_registry = source_registry or {}
        self._max_chars = max_chars

    # ------------------------------------------------------------------
    # 主入口：从 HTML 抽取
    # ------------------------------------------------------------------

    def extract(
        self,
        raw: str,
        *,
        url: str,
        fetched_at: datetime | None = None,
        prefer_markdown: bool = False,
    ) -> WebExtractedDocument:
        """
        从原始 HTML 字符串中抽取结构化网页文档

        参数:
            raw: 原始 HTML 文本（或 markdown，如果 prefer_markdown=True）
            url: 页面 URL（用于 canonicalize、域名识别）
            fetched_at: 抓取时间，None 时使用当前 UTC 时间
            prefer_markdown: True 表示 raw 是 markdown，不做 HTML 解析
        """
        fetched = fetched_at or datetime.now(timezone.utc)
        raw_for_processing = raw if len(raw) <= self._max_chars else raw[: self._max_chars]
        doc = WebExtractedDocument(
            url=url,
            canonical_url=canonicalize_url(url),
            fetched_at=fetched.isoformat(),
        )

        if len(raw) > self._max_chars:
            doc.warnings.append(
                f"原始内容 {len(raw):,} 字符超过处理上限 {self._max_chars:,}，"
                f"仅处理前 {self._max_chars:,} 字符，但完整原文仍保存在 raw_html/raw_markdown"
            )

        # 1) 保存完整原文（这两行**不做任何截断**，满足阶段 6 验收："原文完整保存"）
        if prefer_markdown:
            doc.raw_markdown = raw
            doc.raw_html = ""
        else:
            doc.raw_html = raw
            doc.raw_markdown = ""

        # 2) 标题 / 作者 / 发布时间抽取
        try:
            if not prefer_markdown:
                self._extract_meta_from_html(raw_for_processing, doc)
            else:
                self._extract_meta_from_markdown(raw_for_processing, doc)
        except Exception as e:
            doc.warnings.append(f"抽取元数据异常，降级：{e.__class__.__name__}: {e}")

        # 3) 正文抽取 + 清洗
        try:
            if not prefer_markdown:
                cleaned_md = self._html_to_cleaned_markdown(raw_for_processing, doc)
            else:
                cleaned_md = self._clean_markdown_noise(raw_for_processing, doc)
        except Exception as e:
            doc.warnings.append(f"正文清洗异常，回退为原文：{e.__class__.__name__}: {e}")
            cleaned_md = (doc.raw_markdown or doc.raw_html)[: self._max_chars]

        doc.cleaned_markdown = cleaned_md.strip()

        # 4) 切分成 content_blocks（段落块编号，供引用片段位置）
        doc.content_blocks = self._split_into_blocks(doc.cleaned_markdown)

        # 5) 内容哈希（幂等去重使用，对 cleaned_markdown 取 hash）
        doc.content_hash = hashlib.sha256(
            doc.cleaned_markdown.encode("utf-8", errors="ignore")
        ).hexdigest()

        # 6) 质量估计
        doc.extraction_quality = self._estimate_quality(doc)

        # 7) 付费墙检测
        for kw in _PAYWALL_KEYWORDS:
            if kw in doc.cleaned_markdown:
                doc.paywall_detected = True
                doc.warnings.append(f"疑似付费墙：检测到关键字 {kw!r}")
                break

        # 8) 如果发布时间缺失，记警告（阶段 6 测试要求：页面时间缺失可降级）
        if not doc.published_at:
            doc.warnings.append("发布时间缺失：页面 <meta>/<time> 中未找到发布时间")

        return doc

    # ------------------------------------------------------------------
    # 内部：HTML 元数据抽取
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_meta_from_html(html: str, doc: WebExtractedDocument) -> None:
        """从 HTML 的 <title>/<meta>/<time> 抽取标题、作者、发布时间"""

        # 标题：优先 <title>
        m = re.search(r"<title[^>]*>\s*(.*?)\s*</title>", html, flags=re.S | re.I)
        if m:
            doc.title = re.sub(r"\s+", " ", m.group(1)).strip()
        # og:title 可能比 title 更准
        og_title = re.search(
            r"""<meta\s+(?:property|name)\s*=\s*["']og:title["']\s+content\s*=\s*["']([^"']+)""",
            html, flags=re.I,
        )
        if og_title and len(og_title.group(1)) > 4:
            doc.title = og_title.group(1).strip()

        # 作者：<meta name="author">
        m = re.search(
            r"""<meta\s+name\s*=\s*["']author["']\s+content\s*=\s*["']([^"']+)""",
            html, flags=re.I,
        )
        if m:
            doc.author = m.group(1).strip()

        # 发布时间：按优先级尝试多种写法（中文媒体常用）
        candidates: list[str] = []
        # <meta property="article:published_time">
        m = re.search(
            r"""<meta\s+(?:property|name)\s*=\s*["']article:published_time["']\s+content\s*=\s*["']([^"']+)""",
            html, flags=re.I,
        )
        if m:
            candidates.append(m.group(1).strip())
        # <meta name="pubdate" / "publishdate" / "date">
        for key in ("pubdate", "publishdate", "date", "published", "wechat:published_at"):
            m = re.search(
                rf"""<meta\s+name\s*=\s*["']{key}["']\s+content\s*=\s*["']([^"']+)""",
                html, flags=re.I,
            )
            if m:
                candidates.append(m.group(1).strip())
        # <time datetime="...">
        for m in re.finditer(
            r"""<time[^>]+datetime\s*=\s*["']([^"']+)["'][^>]*>""",
            html, flags=re.I,
        ):
            candidates.append(m.group(1).strip())
        # 正文里常见"发布时间：YYYY-MM-DD HH:MM"
        for m in re.finditer(
            r"(发布时间|发布日期|更新时间|发表时间)[:：]\s*"
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?)",
            html,
        ):
            candidates.append(m.group(2).strip())

        for c in candidates:
            normalized = WebDocumentExtractor._normalize_datetime(c)
            if normalized:
                doc.published_at = normalized
                break

        # 语言：<html lang="...">
        m = re.search(r"<html[^>]+lang\s*=\s*[\"']([^\"']+)", html, flags=re.I)
        if m:
            doc.lang = m.group(1).strip()

    @staticmethod
    def _extract_meta_from_markdown(md: str, doc: WebExtractedDocument) -> None:
        """Markdown 模式：从 frontmatter 或首行标题解析元数据"""
        if md.startswith("---"):
            end = md.find("\n---", 3)
            if end > 0:
                fm = md[3:end]
                for line in fm.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k, v = k.strip().lower(), v.strip().strip("'\"")
                        if k in ("title", "标题") and not doc.title:
                            doc.title = v
                        elif k in ("author", "作者") and not doc.author:
                            doc.author = v
                        elif k in ("date", "published_at", "发布时间"):
                            nd = WebDocumentExtractor._normalize_datetime(v)
                            if nd:
                                doc.published_at = nd
        if not doc.title:
            for line in md.splitlines()[:8]:
                if line.startswith("# "):
                    doc.title = line[2:].strip()
                    break

    @staticmethod
    def _normalize_datetime(raw: str) -> str | None:
        """把各种日期字符串统一成 ISO 格式；解析失败返回 None"""
        if not raw:
            return None
        # 把中文 / 转成 ISO 的 -
        s = raw.strip().replace("年", "-").replace("月", "-").replace("日", "")
        s = s.replace("/", "-").replace(".", "-").replace("T", " ")
        s = re.sub(r"\s+", " ", s).strip()
        # 尝试多种格式
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                continue
        # 已经是 ISO 了？直接返回
        if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", s.replace(" ", "T")):
            return s.replace(" ", "T")
        return None

    # ------------------------------------------------------------------
    # 内部：HTML -> 清洗后 Markdown
    # ------------------------------------------------------------------

    def _html_to_cleaned_markdown(self, html: str, doc: WebExtractedDocument) -> str:
        """
        极简 HTML->Markdown 正文抽取：
        1) 删除 <script>/<style>/<nav>/<header>/<footer>/广告 div
        2) 提取 <article> 或 class 含 content/article 的 div
        3) 将 <h1-6>/<p>/<li>/<a>/<strong>/<em> 转成 markdown
        4) 计数删除了多少 nav / ad / footer
        """

        # --- 步骤 1：整页删除 script / style / svg / iframe / noscript ---
        cleaned_html = html
        for tag in ("script", "style", "noscript", "svg", "iframe", "template"):
            cleaned_html, n = re.subn(
                rf"<{tag}\b[^>]*>.*?</{tag}>", " ", cleaned_html,
                flags=re.S | re.I,
            )
            doc.metadata[f"stripped_{tag}_count"] = n

        # --- 步骤 2：删除明确的噪声标签（nav / header / footer / aside）---
        for tag, attr_keywords, counter in (
            ("nav", _NAV_KEYWORDS, "nav_removed"),
            ("header", _NAV_KEYWORDS, "nav_removed"),
            ("footer", _FOOTER_KEYWORDS, "footer_removed"),
            ("aside", _AD_KEYWORDS, "ads_removed"),
        ):
            pattern = rf"<{tag}\b([^>]*)>.*?</{tag}>"
            def _remove_noise_block(match: re.Match[str],
                                    keywords=attr_keywords,
                                    counter_name=counter) -> str:
                attrs = match.group(1) or ""
                if any(k in attrs.lower() for k in keywords):
                    setattr(doc, counter_name, getattr(doc, counter_name) + 1)
                    return " "
                return match.group(0)
            cleaned_html = re.sub(pattern, _remove_noise_block, cleaned_html, flags=re.S | re.I)

        # --- 步骤 3：删除 class/id 命中广告关键字的任意 div ---
        def _remove_ad_div(match: re.Match[str]) -> str:
            inner = match.group(1) + match.group(3)
            if any(k in inner.lower() for k in _AD_KEYWORDS):
                doc.ads_removed += 1
                return " "
            return match.group(0)
        cleaned_html = re.sub(
            r"<div\b([^>]*)>(.*?)</div(\s*)>",
            _remove_ad_div, cleaned_html, flags=re.S | re.I,
        )

        # --- 步骤 4：抽取正文区域（优先 <article>，然后 class=content/article/detail/post 的 div）---
        main_html = ""
        for pattern in (
            r"<article\b[^>]*>(.*?)</article>",
            r"<main\b[^>]*>(.*?)</main>",
            r"<div[^>]+class\s*=\s*[\"'][^\"']*(?:article-?content|post-?content|detail-?content|news-?content|content|detail|post)[^\"']*[\"'][^>]*>(.*?)</div>",
        ):
            m = re.search(pattern, cleaned_html, flags=re.S | re.I)
            if m and len(m.group(1)) > 400:
                main_html = m.group(1)
                break
        if not main_html:
            main_html = cleaned_html  # 没找到就用整个清洗过的 HTML（降级）
            doc.warnings.append("未检测到 <article>/<main>，对全页做正文抽取（降级）")

        # --- 步骤 5：语义标签 -> Markdown ---
        md = self._semantic_html_to_markdown(main_html)
        # 多重空行压缩
        md = re.sub(r"\n{3,}", "\n\n", md)
        return md.strip()

    @staticmethod
    def _semantic_html_to_markdown(html: str) -> str:
        """极简版：只处理 h1~h6、p、a、li、strong、em、blockquote"""
        out = html
        # 标题
        for i in range(6, 0, -1):
            out = re.sub(
                rf"<h{i}\b[^>]*>(.*?)</h{i}>",
                lambda m, level=i: "\n\n" + ("#" * level) + " " + _strip_tags(m.group(1)) + "\n\n",
                out, flags=re.S | re.I,
            )
        # blockquote
        out = re.sub(
            r"<blockquote\b[^>]*>(.*?)</blockquote>",
            lambda m: "\n> " + _strip_tags(m.group(1)).replace("\n", "\n> ") + "\n",
            out, flags=re.S | re.I,
        )
        # 超链接 [text](url)
        out = re.sub(
            r"""<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""",
            lambda m: f"[{_strip_tags(m.group(2))}]({m.group(1)})",
            out, flags=re.S | re.I,
        )
        # 强强调
        out = re.sub(r"<(strong|b)\b[^>]*>(.*?)</\1>",
                     lambda m: "**" + _strip_tags(m.group(2)) + "**",
                     out, flags=re.S | re.I)
        out = re.sub(r"<(em|i)\b[^>]*>(.*?)</\1>",
                     lambda m: "*" + _strip_tags(m.group(2)) + "*",
                     out, flags=re.S | re.I)
        # 列表：<ul>/<ol> + <li>
        def _render_li(match: re.Match[str]) -> str:
            prefix = "- " if match.group(1).lower() == "ul" else "1. "
            items = re.findall(r"<li\b[^>]*>(.*?)</li>", match.group(2), flags=re.S | re.I)
            return "\n" + "\n".join(prefix + _strip_tags(it).strip() for it in items if it.strip()) + "\n"
        out = re.sub(r"<(ul|ol)\b[^>]*>(.*?)</\1>", _render_li, out, flags=re.S | re.I)
        # 段落
        out = re.sub(r"<p\b[^>]*>(.*?)</p>",
                     lambda m: "\n\n" + _strip_tags(m.group(1)).strip() + "\n\n",
                     out, flags=re.S | re.I)
        # <br> -> 换行
        out = re.sub(r"<br\s*/?\s*>", "\n", out, flags=re.I)
        # 所有剩余标签直接去标签（保留内部文本）
        out = _strip_tags(out)
        # HTML 实体解码
        import html as _html
        out = _html.unescape(out)
        # 行尾空白清理
        lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in out.splitlines()]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 内部：Markdown（来自 Firecrawl）噪声清洗
    # ------------------------------------------------------------------

    def _clean_markdown_noise(self, md: str, doc: WebExtractedDocument) -> str:
        """清洗 Firecrawl 返回的 markdown：删导航/页脚/推荐/广告等噪声行"""
        lines = md.splitlines()
        kept: list[str] = []
        in_noise_block = False
        for line in lines:
            stripped = line.strip()
            # 典型导航标志
            if re.match(r"^(首页|关于我们|联系我们|产品中心|新闻中心|加入我们|登录|注册)$", stripped):
                doc.nav_removed += 1
                continue
            # 典型页脚标志
            if re.match(r"^(版权所有|©|Copyright|备案号|ICP备|粤公网安备)", stripped):
                doc.footer_removed += 1
                continue
            # 推荐阅读 / 广告块
            if re.match(r"^(相关推荐|猜你喜欢|热门推荐|为您推荐|精彩推荐|广告|推广|赞助)", stripped):
                in_noise_block = True
                doc.ads_removed += 1
                continue
            if in_noise_block:
                # 推荐块通常由很多短链接组成；遇到标题或空段落 > 2 行退出
                if (stripped.startswith("# ")
                        or stripped.startswith("## ")
                        or (stripped == "" and kept and kept[-1] == "")):
                    in_noise_block = False
                else:
                    doc.ads_removed += 1
                    continue
            kept.append(line)
        return "\n".join(kept)

    # ------------------------------------------------------------------
    # 内部：切分成段落块 + 质量估计
    # ------------------------------------------------------------------

    @staticmethod
    def _split_into_blocks(cleaned_markdown: str) -> list[ContentBlock]:
        blocks: list[ContentBlock] = []
        if not cleaned_markdown:
            return blocks
        cursor = 0
        paragraphs = re.split(r"\n\s*\n", cleaned_markdown)
        idx = 0
        for para in paragraphs:
            text = para.strip()
            if not text:
                continue
            block_type = "paragraph"
            if text.startswith("#"):
                block_type = "heading"
            elif re.match(r"^[-*+]\s+", text, flags=re.M) or re.match(r"^\d+\.\s+", text, flags=re.M):
                block_type = "list"
            elif text.startswith("|") and "|" in text[1:]:
                block_type = "table"
            elif text.startswith(">"):
                block_type = "quote"
            start = cleaned_markdown.find(para, cursor)
            start = max(0, start if start >= 0 else cursor)
            end = start + len(para)
            blocks.append(ContentBlock(
                block_index=idx,
                block_type=block_type,
                text=text,
                raw_start_char=start,
                raw_end_char=end,
            ))
            idx += 1
            cursor = end
        return blocks

    @staticmethod
    def _estimate_quality(doc: WebExtractedDocument) -> str:
        """根据段落数、文本长度、标题是否存在、警告数量，估计抽取质量"""
        body_len = len(doc.cleaned_markdown)
        n_blocks = len(doc.content_blocks)
        paragraphs = sum(1 for b in doc.content_blocks if b.block_type == "paragraph")
        if not doc.title:
            return "poor"
        if body_len < 400 or paragraphs < 2:
            return "poor"
        if body_len > 2000 and paragraphs >= 3 and len(doc.warnings) <= 1:
            return "good"
        return "fair"

    def refresh_quality(self, doc: WebExtractedDocument) -> str:
        """外部元数据回灌标题/作者/时间后，重新计算并写回抽取质量。"""
        doc.extraction_quality = self._estimate_quality(doc)
        return doc.extraction_quality


def _strip_tags(text: str) -> str:
    """纯工具：删除所有剩余 HTML 标签，保留内部文本"""
    return re.sub(r"<[^>]+>", "", text)


# ============================================================================
# 便捷函数：从本地注册表 JSON 加载
# ============================================================================


def load_source_registry(path: str | Path | None = None) -> dict[str, Any]:
    """
    从 web_source_registry.json 加载来源注册表；路径为空则用项目默认位置

    小白讲解：
        读 00_control/web_source_registry.json，返回 dict。
        文件不存在时返回空 dict，Extractor 不会崩溃。
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
