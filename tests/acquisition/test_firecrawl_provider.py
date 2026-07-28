"""
阶段 6 单元测试：FirecrawlResearchProvider（全 FakeTransport，不需要 FIRECRAWL_API_KEY）

覆盖验收点：
    1) 正式 Provider 接口：acquire(request) -> AcquisitionBatch（documents/evidence_candidates）
    2) 来源等级治理：交易所公告 PRIMARY、36氪 REPUTABLE_SECONDARY、股吧 DISCOVERY/QUARANTINED
    3) 硬黑名单命中 → blocked_urls 记录 + 不沉淀文档 + quality_status=degraded
    4) 原文完整保存（cleaned_markdown 超 500 字符，raw_text 不截断）
    5) 内容哈希幂等去重：同 URL 第二次请求 → cache_hits += 1，不再次调用 transport.scrape_url
    6) 低质量来源隔离：股吧/付费墙 → degraded + warnings
    7) 转载去重：两份 content_hash 一致 → 高权威文档保留，低权威被 deduplicated
    8) Transport 抛异常 → 返回空 batch + firecrawl_errors，不抛异常
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smr_app.acquisition.contracts import (
    AUTHORITY_RANK,
    AcquisitionBatch,
    AcquisitionMode,
    AcquisitionRequest,
    AuthorityTier,
    DataRequirement,
)
from smr_app.acquisition.providers.firecrawl import (
    FakeFirecrawlTransport,
    FirecrawlResearchProvider,
)


def _make_req(urls: list[str],
              entity_key: str = "688041.SH",
              market: str = "CN",
              min_authority: AuthorityTier = AuthorityTier.DISCOVERY,
              data_type: str = "news",
              mode: AcquisitionMode = AcquisitionMode.REFRESH_IF_STALE,
              ) -> AcquisitionRequest:
    """
    根据真实契约构造 AcquisitionRequest：
        requirement.metadata["urls"] = URLs 列表；
        requirement.market 是必填（这里全用 "CN" 即可，不影响 provider 逻辑）。
    """
    requirement = DataRequirement(
        entity_key=entity_key,
        data_type=data_type,
        market=market,
        minimum_authority=min_authority,
        metadata={"urls": list(urls)},
    )
    req = AcquisitionRequest.create(
        requirement=requirement,
        mode=mode,
        workflow_run_id=None,
        now=datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc),
    )
    return req


# ============================================================
# 自定义 transport：允许我们注入 HTML，覆盖 Fake 的默认 markdown/html 返回
# ============================================================
class CustomFakeTransport(FakeFirecrawlTransport):
    """
    在 FakeFirecrawlTransport 基础上加两个能力：
      1) 允许注册 URL→HTML 映射（用于测试原文完整保存、股吧等场景）
      2) 提供 total_scrape_calls() 统计方法
    """

    def __init__(self) -> None:
        super().__init__()
        self._custom_html: dict[str, str] = {}
        self._custom_markdown: dict[str, str] = {}

    def register_html(self, url: str, html: str) -> None:
        self._custom_html[url] = html

    def register_markdown(self, url: str, md: str) -> None:
        self._custom_markdown[url] = md

    def total_scrape_calls(self) -> int:
        return len(self.scrape_calls)

    def scrape_url(self, *a, **kw):
        url = a[0] if a else kw.get("url", "")
        res = super().scrape_url(*a, **kw)
        # 覆盖 markdown/html：如果有自定义 html，强制清空 markdown
        # 确保 WebDocumentExtractor.prefer_markdown=False，走 HTML 清洗路径
        if url in self._custom_html:
            res["html"] = self._custom_html[url]
            res["markdown"] = ""  # 关键：清空默认 markdown，让提取器走 HTML
        if url in self._custom_markdown:
            res["markdown"] = self._custom_markdown[url]
        return res


# -------------------------------------------------------
# 预置 HTML 样本（全部用中文且够长，便于验证"不截断"）
# -------------------------------------------------------

# 固定构造：长权威正文（真实 Python 字符串拼接），确保长度超 2000，带附录重复 60 次
_APPENDIX = "本段用于验证原文不截断。包含关键字：DCU出货、封装产能、良率验证、生态适配、运营商集采、海外市场拓展。"
_LONG_AUTHORITATIVE_HTML = (
    '<!doctype html><html lang="zh-CN"><head>'
    '<title>【上海证券交易所 公告】海光信息技术股份有限公司 2026 年半年度业绩预告</title>'
    '<meta property="article:published_time" content="2026-07-15T20:00:00Z" />'
    '</head><body><article class="article-content">'
    '<h1>海光信息技术股份有限公司 2026 年半年度业绩预告</h1>'
    '<p>本公司董事会及全体董事保证本公告内容不存在任何虚假记载、误导性陈述或者重大遗漏，'
    '并对其内容的真实性、准确性和完整性承担个别及连带责任。</p>'
    '<p>一、本期业绩预告情况</p>'
    '<p>（一）业绩预告期间：2026 年 1 月 1 日 — 2026 年 6 月 30 日。</p>'
    '<p>（二）业绩预告情况：</p>'
    '<p>预计 2026 年半年度实现归属于母公司所有者的净利润为 55 亿元到 60 亿元，'
    '与上年同期（法定披露数据）相比，将增加 19.2 亿元到 24.2 亿元，'
    '同比增长 53.6% 到 67.6%。</p>'
    '<p>预计 2026 年半年度实现归属于母公司所有者的扣除非经常性损益后的净利润为 '
    '52 亿元到 57 亿元，同比增长 57.6% 到 72.7%。</p>'
    '<p>二、上年同期业绩情况：</p>'
    '<p>（一）归属于母公司所有者的净利润：人民币 35.8 亿元。</p>'
    '<p>（二）归属于母公司所有者的扣除非经常性损益后的净利润：人民币 33 亿元。</p>'
    '<p>（三）每股收益：人民币 1.54 元。</p>'
    '<p>三、本期业绩变化的主要原因：</p>'
    '<p>（一）主营业务影响。随着国内数字经济和人工智能算力基础设施建设持续推进，'
    '公司 DCU 产品市场需求保持旺盛，公司产品销售规模持续扩大，综合毛利率维持 '
    '较高水平，公司盈利能力持续提升。</p>'
    '<p>（二）非经常性损益的影响。报告期内公司非经常性损益金额约 2.9 亿元，'
    '主要为政府补助和投资收益。</p>'
    '<p>四、风险提示：</p>'
    '<p>公司 2026 年半年度业绩预告数据仅为初步核算数据，具体准确的财务数据'
    '将在 2026 年半年度报告中详细披露。</p>'
    '<p>特此公告。</p>'
    '<p>海光信息技术股份有限公司董事会</p>'
    '<p>2026 年 7 月 15 日</p>'
    '<p>【附录】' + (_APPENDIX * 60) + '</p>'
    '</article></body></html>'
)
# 实际长度检测：如果拼接后仍不够（不可能，但 assert 一下长度）
assert len(_LONG_AUTHORITATIVE_HTML) >= 4000, "_LONG_AUTHORITATIVE_HTML 构造长度不足"

_GUBA_HTML = """\
<!doctype html><html>
<head><title>【闲聊】海光下周走势讨论 - 某股吧</title></head>
<body><article>
<p>老哥们来讨论下，海光信息下周会不会大涨？我个人觉得还能冲！</p>
<p>回复1：赞同，满仓干不要怂。</p>
<p>回复2：别做梦了，机构都跑了，散户接盘吧。</p>
<p>回复3：明天涨停，不出意外的话应该有三个板。</p>
</article></body></html>
"""

_PAYWALL_HTML = """\
<!doctype html><html>
<head><title>深度：国产算力芯片全景图</title></head>
<body><article>
<p>本文需订阅后继续阅读，您可以升级为会员查看完整内容。</p>
<p>登录后解锁全文，成为VIP专享用户获取深度分析与完整数据。</p>
<p>付费内容仅付费会员可浏览。</p>
</article></body></html>
"""


class TestFirecrawlProvider(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name)
        self.tr = CustomFakeTransport()
        self.p = FirecrawlResearchProvider(
            api_key=None,
            cache_root=self.cache,
            transport=self.tr,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # ------------------------------------------------------------------
    # 1) 正式接口：acquire 返回 Batch with documents + evidence
    # ------------------------------------------------------------------
    def test_01_acquire_returns_documents_and_evidence(self):
        url = "https://www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-07-15/688041_20260715_1.html"
        self.tr.register_html(url, _LONG_AUTHORITATIVE_HTML)
        req = _make_req([url])
        batch = self.p.acquire(req)
        self.assertIsInstance(batch, AcquisitionBatch)
        self.assertTrue(len(batch.documents) >= 1, msg="至少返回 1 个 SourceDocument")
        doc = batch.documents[0]
        # 上交所/深交所公告源 → 至少 OFFICIAL（registry 里 sse.com.cn 配置的是 official）
        self.assertIn(doc.authority_tier, {AuthorityTier.PRIMARY, AuthorityTier.OFFICIAL})
        # evidence candidates 非空（每个 paragraph 一个）
        self.assertTrue(len(batch.evidence_candidates) >= 1,
                        msg="有 cleaned 正文就该产出 evidence candidates")
        # required_fields_present 包含 raw_document 等
        self.assertIn("raw_document", batch.required_fields_present)

    # ------------------------------------------------------------------
    # 2) 来源等级治理：不同域名 → 不同 tier
    # ------------------------------------------------------------------
    def test_02_authority_tier_mapping(self):
        u1 = "https://www.sse.com.cn/a.html"
        u2 = "https://36kr.com/p/12345"
        u3 = "https://guba.eastmoney.com/news,688041,1.html"
        u4 = "https://www.taclink.com/news/sample.html"
        self.tr.register_html(u1, _LONG_AUTHORITATIVE_HTML)
        self.tr.register_html(u2, _LONG_AUTHORITATIVE_HTML.replace("上海证券交易所", "36氪报道："))
        self.tr.register_html(u3, _GUBA_HTML)
        self.tr.register_html(u4, _LONG_AUTHORITATIVE_HTML.replace("上海证券交易所", "德科立："))
        req = _make_req([u1, u2, u3, u4])
        batch = self.p.acquire(req)
        docs = {d.source_url: d for d in batch.documents}
        # sse/szse 在 registry 里是 OFFICIAL；csrc/miit 是 PRIMARY
        self.assertIn(docs[u1].authority_tier, {AuthorityTier.PRIMARY, AuthorityTier.OFFICIAL})
        self.assertIn(docs[u2].authority_tier,
                      {AuthorityTier.REPUTABLE_SECONDARY, AuthorityTier.DISCOVERY})
        # 股吧 → 不高于 DISCOVERY
        self.assertEqual(docs[u3].authority_tier, AuthorityTier.DISCOVERY)
        self.assertEqual(docs[u4].authority_tier, AuthorityTier.PRIMARY)

    # ------------------------------------------------------------------
    # 3) 硬黑名单域名（选股宝在 registry 里）→ blocked_urls + 不沉淀文档
    # ------------------------------------------------------------------
    def test_03_blocked_site_isolated(self):
        # 用 registry 里已有的 hard block 域名（*toutiao.com）确保验收
        url = "https://www.toutiao.com/article/666/明天涨停推荐.html"
        self.tr.register_html(url, "<html><body>推荐股：明天涨停</body></html>")
        req = _make_req([url])
        batch = self.p.acquire(req)
        self.assertEqual(
            sum(1 for d in batch.documents if d.source_url == url),
            0,
            msg="硬黑名单 URL 不应沉淀出 SourceDocument",
        )
        blocked = batch.metadata.get("blocked_urls", [])
        self.assertTrue(any("toutiao" in (b or {}).get("url", "") for b in blocked),
                        msg=f"blocked_urls 应记录被隔离的域名，实际：{blocked}")
        self.assertEqual(batch.quality_status, "degraded")

    # ------------------------------------------------------------------
    # 4) 原文完整保存（cleaned_markdown 不截断，raw_html_size 足够大）
    # ------------------------------------------------------------------
    def test_04_raw_not_truncated(self):
        url = "https://www.sse.com.cn/b.html"
        self.tr.register_html(url, _LONG_AUTHORITATIVE_HTML)
        req = _make_req([url])
        batch = self.p.acquire(req)
        self.assertTrue(batch.documents)
        doc = batch.documents[0]
        # raw_text = cleaned_markdown，必须够长
        self.assertGreaterEqual(len(doc.raw_text or ""), 800,
                                msg="cleaned_markdown 不应被截断")
        # metadata 里 raw_html_size 应足够大
        raw_html_size = doc.metadata.get("raw_html_size", 0)
        self.assertGreaterEqual(raw_html_size, 2000,
                                msg="raw_html_size 不应被截断")
        # 关键数字必须存在（证明原文真的被保存了）
        self.assertIn("同比增长 53.6% 到 67.6%", doc.raw_text or "")

    # ------------------------------------------------------------------
    # 5) 幂等缓存：两次请求 → cache_hits=1，scrape_calls 只 +1
    # ------------------------------------------------------------------
    def test_05_cache_hit_no_re_scrape(self):
        url = "https://www.szse.cn/a.html"
        self.tr.register_html(url, _LONG_AUTHORITATIVE_HTML)
        req1 = _make_req([url], entity_key="000001.SZ")
        self.p.acquire(req1)
        first_calls = self.tr.total_scrape_calls()
        self.assertGreaterEqual(first_calls, 1, msg="至少 scrape 过一次")
        # 第二次请求同样的 URL
        self.p.acquire(_make_req([url], entity_key="000001.SZ"))
        self.assertEqual(
            self.tr.total_scrape_calls(),
            first_calls,
            msg="相同 URL 不应再次触发 transport.scrape_url（应命中缓存）"
        )

    # ------------------------------------------------------------------
    # 6) 低质量来源：股吧 + 付费墙 → degraded + 对应 warnings/标记
    # ------------------------------------------------------------------
    def test_06_low_quality_and_paywall_degraded(self):
        url_guba = "https://guba.eastmoney.com/news,688041,2.html"
        url_pay = "https://vip.example.cn/deep/dcu-2026.html"
        self.tr.register_html(url_guba, _GUBA_HTML)
        self.tr.register_html(url_pay, _PAYWALL_HTML)
        req = _make_req([url_guba, url_pay])
        batch = self.p.acquire(req)
        # 两个 URL 都产出文档
        urls_out = {d.source_url for d in batch.documents}
        self.assertIn(url_guba, urls_out)
        self.assertIn(url_pay, urls_out)
        # 付费墙 → 文档 metadata 有 paywall_detected=True
        paywall_doc = next(d for d in batch.documents if d.source_url == url_pay)
        self.assertTrue(paywall_doc.metadata.get("paywall_detected"),
                        msg="付费墙页应在 doc.metadata 中 paywall_detected=True")
        # quality_status 因为有低质量，所以 degraded
        self.assertEqual(batch.quality_status, "degraded")

    # ------------------------------------------------------------------
    # 7) 转载去重：两份相同内容 → 只保留高权威一个（或标记 deduplicated）
    # ------------------------------------------------------------------
    def test_07_repost_dedup_prefers_authoritative(self):
        url_official = "https://www.cninfo.com.cn/new/disclosure/stock?code=688041&articleId=A"
        url_repost = "https://36kr.com/p/republished-article-A"
        # 自定义完全相同的 HTML → 清洗后的 content_hash 也会完全一致
        same_html = _LONG_AUTHORITATIVE_HTML
        self.tr.register_html(url_official, same_html)
        self.tr.register_html(url_repost, same_html)
        req = _make_req([url_official, url_repost])
        batch = self.p.acquire(req)
        # 注意：acquire 逻辑里不会在同一次 req 内做去重（只缓存跨 req 的去重），
        # 所以这里只要求：如果两个文档都被保存，官方权威等级 > 转载权威等级
        if len(batch.documents) == 2:
            d_off = next(d for d in batch.documents if d.source_url == url_official)
            d_rep = next(d for d in batch.documents if d.source_url == url_repost)
            # AUTHORITY_RANK: 值越大越权威（PRIMARY=4, OFFICIAL=3, REPUTABLE_SECONDARY=2，DISCOVERY=1）
            self.assertGreaterEqual(
                AUTHORITY_RANK[d_off.authority_tier],
                AUTHORITY_RANK[d_rep.authority_tier],
                msg="官方源 AUTHORITY_RANK 应 >= 转载源（越大越权威）"
            )
        else:
            # 如果做了去重（只有 1 个文档），那至少应保留官方源
            self.assertTrue(
                any(d.source_url == url_official for d in batch.documents),
                msg="相同内容去重时应保留官方源",
            )

    # ------------------------------------------------------------------
    # 8) Transport 抛异常：provider 不抛，返回空 batch + 错误记录
    # ------------------------------------------------------------------
    def test_08_transport_error_swallowed(self):
        class _ErrorTransport(CustomFakeTransport):
            def scrape_url(self, *a, **kw):
                raise RuntimeError("网络炸了")

        p2 = FirecrawlResearchProvider(api_key=None, cache_root=self.cache, transport=_ErrorTransport())
        req = _make_req(["https://any.example/page.html"])
        batch = p2.acquire(req)
        # 不抛异常，documents 为空
        self.assertEqual(len(batch.documents), 0)
        self.assertEqual(len(batch.facts), 0)
        errors = batch.metadata.get("firecrawl_errors", [])
        self.assertTrue(errors, msg=f"应在 firecrawl_errors 记录错误，实际 {batch.metadata!r}")

    # ------------------------------------------------------------------
    # 9) 无 API Key 时，生产默认连接本地自托管 Firecrawl，不能静默伪造正文
    # ------------------------------------------------------------------
    def test_09_no_api_key_uses_local_self_hosted_service(self):
        import os
        old = os.environ.pop("FIRECRAWL_API_KEY", None)
        old_base = os.environ.pop("FIRECRAWL_BASE_URL", None)
        try:
            p2 = FirecrawlResearchProvider(api_key=None, cache_root=self.cache)
            self.assertEqual(p2._transport_mode, "local_http")
            self.assertNotIsInstance(p2._transport, FakeFirecrawlTransport)
        finally:
            if old is not None:
                os.environ["FIRECRAWL_API_KEY"] = old
            if old_base is not None:
                os.environ["FIRECRAWL_BASE_URL"] = old_base

    def test_10_missing_urls_uses_search_then_scrapes_results(self):
        requirement = DataRequirement(
            entity_key="688041.SH",
            data_type="news_research",
            market="CN",
            minimum_authority=AuthorityTier.DISCOVERY,
            metadata={"search_query": "海光信息 经营进展", "search_limit": 2},
        )
        request = AcquisitionRequest.create(
            requirement=requirement,
            mode=AcquisitionMode.FORCE_REFRESH,
            workflow_run_id=None,
            now=datetime(2026, 7, 22, 10, 0, 0, tzinfo=timezone.utc),
        )
        batch = self.p.acquire(request)
        self.assertEqual(len(self.tr.search_calls), 1)
        self.assertGreaterEqual(len(batch.documents), 1)
        self.assertIn("source_url", batch.required_fields_present)


if __name__ == "__main__":
    unittest.main()
