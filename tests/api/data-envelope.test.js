import assert from "node:assert/strict";
import test from "node:test";

import {
  createEvidenceEnvelope,
  createEvidenceSnapshot,
  formatEvidenceCatalogForPrompt,
  parseEvidenceDate,
  summarizeDataHealth,
} from "../../api/services/data-envelope.js";

test("evidence envelope normalizes compact trade date and detects fresh market data", () => {
  const evidence = createEvidenceEnvelope({
    evidenceId: "E001",
    toolId: "get_top_gainers",
    capturedAt: "2026-07-19T08:00:00.000Z",
    result: { success: true, message: "获取到实时涨幅榜 1 只（东方财富）", data: [{ trade_date: "20260717", fetched_at: "2026-07-19T08:00:00.000Z", source: "eastmoney_realtime" }] },
  });

  assert.equal(parseEvidenceDate("20260717").toISOString(), "2026-07-17T00:00:00.000Z");
  assert.equal(evidence.source_id, "eastmoney_realtime");
  assert.equal(evidence.as_of, "2026-07-17T00:00:00.000Z");
  assert.equal(evidence.source_fetched_at, "2026-07-19T08:00:00.000Z");
  assert.equal(evidence.expected_trade_date, "2026-07-17");
  assert.equal(evidence.trading_session_lag, 0);
  assert.equal(evidence.freshness, "fresh");
  assert.equal(evidence.item_count, 1);
});

test("evidence snapshot redacts credentials and truncates oversized content", () => {
  const evidence = createEvidenceEnvelope({
    evidenceId: "E001", toolId: "get_latest_news", capturedAt: "2026-07-20T08:00:00.000Z",
    result: { success: true, data: [{ published_at: "2026-07-20", title: "新闻" }] },
  });
  const snapshot = createEvidenceSnapshot({
    evidence,
    result: { success: true, message: "ok", data: { api_key: "should-not-leak", body: "甲".repeat(3_000) } },
  });

  assert.equal(snapshot.data.api_key, "[REDACTED]");
  assert.equal(snapshot.data.body.length, 2_000);
  assert.equal(snapshot.truncated, true);
  assert.match(snapshot.snapshot_sha256, /^[a-f0-9]{64}$/);
});

test("structured source wins over a legacy tool message", () => {
  const evidence = createEvidenceEnvelope({
    evidenceId: "E001",
    toolId: "get_top_gainers",
    capturedAt: "2026-07-20T11:00:00.000Z",
    result: { success: true, message: "获取到实时涨幅榜 1 只（东方财富）", data: [{ trade_date: "2026-07-20", source: "sina_realtime" }] },
  });

  assert.equal(evidence.source_id, "sina_realtime");
  assert.equal(evidence.source_name, "新浪财经实时行情");
});

test("evidence envelope marks stale, empty and failed sources without hiding the reason", () => {
  const capturedAt = "2026-07-20T08:00:00.000Z";
  const stale = createEvidenceEnvelope({
    evidenceId: "E001", toolId: "get_pool_snapshot", capturedAt,
    result: { success: true, message: "本地数据库", data: [{ trade_date: "2026-07-01" }] },
  });
  const empty = createEvidenceEnvelope({
    evidenceId: "E002", toolId: "get_latest_news", capturedAt,
    result: { success: true, message: "未获取到新闻", data: [] },
  });
  const failed = createEvidenceEnvelope({
    evidenceId: "E003", toolId: "get_market_indices", capturedAt,
    result: { success: false, message: "上游超时", data: [] },
  });

  assert.equal(stale.freshness, "stale");
  assert.match(stale.missing_reason, /落后预期交易日/);
  assert.equal(empty.freshness, "missing");
  assert.equal(failed.freshness, "fetch_failed");
  assert.equal(failed.missing_reason, "上游超时");
});

test("market evidence rejects a weekend date even when it was fetched recently", () => {
  const evidence = createEvidenceEnvelope({
    evidenceId: "E001", toolId: "get_market_indices", capturedAt: "2026-07-19T08:00:00.000Z",
    result: { success: true, message: "实时指数", data: [{ trade_date: "2026-07-19", fetched_at: "2026-07-19T08:00:00.000Z", source: "sina_realtime" }] },
  });

  assert.equal(evidence.freshness, "invalid_date");
  assert.equal(evidence.as_of_basis, "market_calendar");
  assert.match(evidence.missing_reason, /不是有效的已完成交易日/);
});

test("market evidence accepts a same-session intraday observation without calling it completed data", () => {
  const evidence = createEvidenceEnvelope({
    evidenceId: "E001", toolId: "get_top_gainers", capturedAt: "2026-07-20T02:00:00.000Z",
    result: { success: true, message: "实时涨幅榜", data: [{ trade_date: "2026-07-20", fetched_at: "2026-07-20T02:00:00.000Z", source: "sina_realtime" }] },
  });

  assert.equal(evidence.freshness, "fresh");
  assert.equal(evidence.as_of_basis, "market_observation");
  assert.equal(evidence.market_session_status, "open");
  assert.equal(evidence.expected_trade_date, "2026-07-17");
});

test("data health blocks current claims when no fresh current-market evidence exists", () => {
  const catalog = [
    { evidence_id: "E001", source_name: "本地行情库", source_urls: [], tool_id: "get_pool_snapshot", as_of: "2026-07-01T00:00:00.000Z", freshness: "stale", item_count: 8, current_market_evidence: true },
    { evidence_id: "E002", source_name: "本地新闻库", source_urls: [], tool_id: "get_latest_news", as_of: null, freshness: "missing", item_count: 0, current_market_evidence: false },
  ];
  const health = summarizeDataHealth(catalog);
  const prompt = formatEvidenceCatalogForPrompt(catalog, health);

  assert.equal(health.status, "blocked");
  assert.equal(health.can_claim_current, false);
  assert.match(prompt, /是否允许声称“当前\/今日”=否/);
  assert.match(prompt, /\[E001\]/);
});

test("stock evidence uses the quote date instead of unrelated nested report timestamps", () => {
  const evidence = createEvidenceEnvelope({
    evidenceId: "E001",
    toolId: "get_stock_data",
    capturedAt: "2026-07-19T08:00:00.000Z",
    result: {
      success: true,
      data: {
        instrumentData: {
          latestDate: "2026-07-17",
          fetched_at: "2026-07-19T08:00:00.000Z",
          source: "tencent_api",
          fundamentals: { createdAt: "2026-07-19T07:00:00.000Z" },
        },
        eastmoneyData: { researchReports: [{ publishDate: "2026-06-24" }] },
      },
    },
  });

  assert.equal(evidence.source_id, "composite_stock_research");
  assert.equal(evidence.as_of, "2026-07-17T00:00:00.000Z");
  assert.equal(evidence.expected_trade_date, "2026-07-17");
  assert.equal(evidence.trading_session_lag, 0);
  assert.equal(evidence.freshness, "fresh");
});
