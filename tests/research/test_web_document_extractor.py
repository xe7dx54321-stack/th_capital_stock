"""
阶段 6 单元测试：Web Document Extractor
覆盖验收点：
    - 主体抽取 + 导航/广告/页脚清洗
    - 发布时间缺失降级
    - 付费墙关键字检测
    - 疑似低质量页面 quality=poor
    - 低质量来源隔离（不是 Extractor 直接治理，但 Extractor 检测付费墙等）
    - 内容哈希幂等
    - URL 规范化工具（canonicalize_url）
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from smr_app.research.web_document_extractor import (
    WebDocumentExtractor,
    canonicalize_url,
    load_source_registry,
)


# 构造一份"充满噪声"的 HTML：导航、广告、页脚、正文
_SAMPLE_HTML = """\
<!doctype html>
<html lang="zh-CN">
<head>
  <title>【产业观察】海光信息 DCU 二号量产进度 - 36氪</title>
  <meta property="og:title" content="海光信息：DCU 二号预计 Q3 量产" />
  <meta name="author" content="产业组记者A" />
  <meta property="article:published_time" content="2026-06-18T09:30:00Z" />
</head>
<body>
  <header class="site-header">
    <nav id="top-nav" class="main-nav">
      <ul>
        <li><a href="/">首页</a></li>
        <li><a href="/tech">科技</a></li>
        <li><a href="/finance">财经</a></li>
      </ul>
    </nav>
  </header>

  <div class="page-layout">
    <aside class="sidebar-left promotion">
      <div class="banner-ad">
        <a href="/ad/summer-promotion">【广告】夏日开户送好礼 - 立即开户</a>
      </div>
      <div class="ad-right-rail">推广：课程优惠仅今天</div>
    </aside>

    <article class="post article-content">
      <h1>海光信息：DCU 二号预计 Q3 量产，运营商集采份额 45%</h1>
      <div class="meta">
        <span class="author">产业组记者A</span>
        <time datetime="2026-06-18T09:30:00Z">发布时间：2026-06-18 09:30</time>
      </div>

      <p>
        从三大运营商 2026 年智算集采开标结果看，国产 x86 架构 DCU 的份额已达到 45%，
        较 2025 年同期提升约 23 个百分点。供应链人士表示，封装产能目前已经排到四季度，
        头部厂商产品良率保持在 85% 以上。
      </p>

      <p>
        海光信息在近日机构调研中表示，其第二代 DCU 产品（深算四号）已完成生态适配，
        预计 Q3 进入量产阶段，初始月产能约 3 万片，届时有望进一步扩大在金融、政务、
        互联网三大客户群的渗透。
      </p>

      <blockquote>
        我们认为 2026 年下半年将是国产算力芯片的关键验证期：
        客户的实际业务负载迁移进度、大模型推理时延、单位算力功耗将决定份额的最终走向。 —— 某头部券商电子分析师
      </blockquote>

      <h2>供应链：先进封装产能紧张</h2>
      <ul>
        <li>CoWoS 封装主要供应商已排产至 2026Q4；</li>
        <li>部分厂商转向 2.5D 封装替代方案；</li>
        <li>HBM 价格上半年环比下降 5%，下半年预计持平。</li>
      </ul>

      <div class="related-recommendation ad-section">
        <h3>猜你喜欢 / 相关推荐</h3>
        <ul>
          <li><a href="/ad/1">广告：手机换电池 5 折</a></li>
          <li><a href="/news/other">另一个无关的 AI 新闻</a></li>
        </ul>
      </div>
    </article>
  </div>

  <footer id="page-footer" class="footer-area">
    <div class="copyright">© 2026 36氪 版权所有 | 京ICP证XXXXXXXX号</div>
    <div class="footer-links">
      <a href="/about">关于我们</a> |
      <a href="/contact">联系方式</a> |
      <a href="/disclaimer">免责声明</a>
    </div>
  </footer>
</body>
</html>
"""


# 页面时间缺失、付费墙的 HTML
_SAMPLE_NO_DATE_PAYWALL_HTML = """\
<!doctype html>
<html lang="zh-CN">
<head><title>一个未知来源网页</title></head>
<body>
  <article>
    <h1>一篇小短文</h1>
    <p>该内容需登录后继续阅读，且需解锁全文方可查看。</p>
    <p>请成为会员/VIP专享用户以获取完整分析。</p>
  </article>
</body>
</html>
"""


class TestCanonicalizeUrl(unittest.TestCase):
    """URL 规范化工具验收：幂等去重关键步骤"""

    def test_strips_utm_and_tracking(self):
        u = canonicalize_url("https://36kr.com/p/12345?utm_source=wechat&utm_medium=share&spm=abc#section2")
        self.assertNotIn("utm_source", u)
        self.assertNotIn("spm=", u)
        self.assertNotIn("#", u)
        self.assertTrue(u.startswith("https://36kr.com/p/12345"))

    def test_http_forced_to_https_and_case_insensitive_host(self):
        u = canonicalize_url("HTTP://WWW.Caixin.com/2026-07-01/demo.html?from=weibo")
        self.assertTrue(u.startswith("https://www.caixin.com"))
        self.assertNotIn("from=weibo", u)

    def test_empty_and_bad_input_safe(self):
        self.assertEqual(canonicalize_url(""), "")
        self.assertEqual(canonicalize_url("not a url"), "not a url")


class TestWebDocumentExtractor(unittest.TestCase):
    """正文抽取与清洗验收"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # ------------------------------------------------------------------
    # 验收 1：主体抽取、导航/广告/页脚清洗、正文不截断
    # ------------------------------------------------------------------
    def test_main_content_extracted_ads_and_navigation_removed(self):
        extractor = WebDocumentExtractor()
        doc = extractor.extract(_SAMPLE_HTML, url="https://36kr.com/p/demo-dcu",
                                fetched_at=datetime(2026, 7, 22, 10, tzinfo=timezone.utc))
        # 广告文本不应出现在清洗后正文
        self.assertNotIn("夏日开户送好礼", doc.cleaned_markdown)
        self.assertNotIn("猜你喜欢", doc.cleaned_markdown)
        # 导航/页脚文本不应出现
        self.assertNotIn("首页", doc.cleaned_markdown[:1000])
        self.assertNotIn("关于我们", doc.cleaned_markdown)
        self.assertNotIn("京ICP证", doc.cleaned_markdown)
        # 但正文关键段落必须存在（原文完整保存的证明）
        self.assertIn("三大运营商 2026 年智算集采", doc.cleaned_markdown)
        self.assertIn("第二代 DCU 产品（深算四号）", doc.cleaned_markdown)
        self.assertIn("2026Q4", doc.cleaned_markdown)
        # 原文 raw_html 必须完整保存（不能 substring）
        self.assertGreater(len(doc.raw_html), 1000)
        self.assertIn("夏日开户送好礼", doc.raw_html)   # 原始 HTML 必须全保留
        # 内容块统计：广告+导航+页脚删除数要>0
        self.assertGreater(doc.nav_removed + doc.ads_removed + doc.footer_removed, 0)
        # 至少有一段 paragraph 和一段 heading、一段 quote/列表
        types = {b.block_type for b in doc.content_blocks}
        self.assertIn("heading", types)
        self.assertIn("paragraph", types)

    # ------------------------------------------------------------------
    # 验收 2：标题、作者、发布时间抽取（og:title > title, article:published_time）
    # ------------------------------------------------------------------
    def test_meta_extracted_title_og_published_time(self):
        extractor = WebDocumentExtractor()
        doc = extractor.extract(_SAMPLE_HTML, url="https://36kr.com/p/demo-dcu")
        self.assertEqual(doc.title, "海光信息：DCU 二号预计 Q3 量产")  # og:title 优先
        self.assertEqual(doc.author, "产业组记者A")
        self.assertIsNotNone(doc.published_at)
        self.assertTrue(doc.published_at.startswith("2026-06-18"),
                        msg=f"published_at={doc.published_at!r}")
        self.assertEqual(doc.lang, "zh-CN")

    # ------------------------------------------------------------------
    # 验收 3：发布时间缺失 → 降级（warnings 里有明确说明）
    # ------------------------------------------------------------------
    def test_publish_date_missing_gives_warning_and_degraded_paywall(self):
        extractor = WebDocumentExtractor()
        doc = extractor.extract(_SAMPLE_NO_DATE_PAYWALL_HTML, url="https://example.com/x")
        self.assertIsNone(doc.published_at)
        date_warns = [w for w in doc.warnings if "发布时间缺失" in w]
        self.assertTrue(date_warns, msg=f"应包含发布时间缺失警告，实际warnings={doc.warnings}")
        # 付费墙检测
        self.assertTrue(doc.paywall_detected)
        pay_warns = [w for w in doc.warnings if "付费墙" in w]
        self.assertTrue(pay_warns, msg=f"应包含付费墙警告，warnings={doc.warnings}")

    # ------------------------------------------------------------------
    # 验收 4：正文极短 → 质量 poor（低质量来源隔离的下游依据）
    # ------------------------------------------------------------------
    def test_short_body_quality_poor(self):
        extractor = WebDocumentExtractor()
        html = "<html><head><title></title></head><body><article><p>就一句话。</p></article></body></html>"
        doc = extractor.extract(html, url="https://low-quality.example/short")
        self.assertEqual(doc.extraction_quality, "poor")

    # ------------------------------------------------------------------
    # 验收 5：内容哈希幂等（同一 HTML 两次抽取 hash 相同）
    # ------------------------------------------------------------------
    def test_content_hash_is_idempotent(self):
        extractor = WebDocumentExtractor()
        d1 = extractor.extract(_SAMPLE_HTML, url="https://36kr.com/p/a")
        d2 = extractor.extract(_SAMPLE_HTML, url="https://36kr.com/p/a")
        self.assertEqual(d1.content_hash, d2.content_hash)
        # 不同 HTML → hash 必须不同
        d3 = extractor.extract("<html><body><p>另一个内容</p></body></html>", url="https://x/y")
        self.assertNotEqual(d1.content_hash, d3.content_hash)

    # ------------------------------------------------------------------
    # 验收 6：load_source_registry 路径缺失安全返回 {}
    # ------------------------------------------------------------------
    def test_load_source_registry_missing_safe(self):
        data = load_source_registry(self.root / "not_exist.json")
        self.assertEqual(data, {})

    # ------------------------------------------------------------------
    # 验收 7：Markdown 模式（Firecrawl 直接给 markdown 的场景）
    # ------------------------------------------------------------------
    def test_markdown_prefer_frontmatter_title_and_date(self):
        md = """\
---
title: 公司官网投资者关系新闻
author: IR
date: 2026-05-20
---
# 公司官网投资者关系新闻

## 业务进展

2026Q2 公司海外订单同比 +50%。
"""
        extractor = WebDocumentExtractor()
        doc = extractor.extract(md, url="https://ir.demo.com/news/20260520", prefer_markdown=True)
        self.assertEqual(doc.title, "公司官网投资者关系新闻")
        self.assertEqual(doc.author, "IR")
        self.assertIsNotNone(doc.published_at)
        self.assertTrue(doc.published_at.startswith("2026-05-20"),
                        msg=f"published_at={doc.published_at!r}")
        self.assertIn("海外订单同比 +50%", doc.cleaned_markdown)
        # raw_markdown 必须完整保存（不做截断）
        self.assertGreater(len(doc.raw_markdown), 20)
        self.assertIn("2026Q2 公司海外订单同比 +50%", doc.raw_markdown)


if __name__ == "__main__":
    unittest.main()
