import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import Database from "better-sqlite3";


function createResearchFixture() {
  const directory = mkdtempSync(path.join(os.tmpdir(), "smr-research-contracts-"));
  const dbPath = path.join(directory, "research.db");
  const db = new Database(dbPath);
  db.exec(`
    CREATE TABLE stock_pool_current (
      ts_code TEXT, sector TEXT, pool_type TEXT, added_date TEXT
    );
    CREATE TABLE daily_bar (
      ts_code TEXT, trade_date TEXT, open REAL, high REAL, low REAL,
      close REAL, vol REAL, pct_chg REAL
    );
    CREATE TABLE us_daily_bar (
      symbol TEXT, trade_date TEXT, open REAL, high REAL, low REAL,
      close REAL, vol REAL, pct_chg REAL
    );
    CREATE TABLE factor_daily (
      ts_code TEXT, factor_name TEXT, factor_value REAL, trade_date TEXT
    );
    CREATE TABLE news_items (
      id TEXT, title TEXT, body TEXT, source_key TEXT, source_name TEXT,
      published_at TEXT, tickers_json TEXT, themes_json TEXT, url TEXT,
      credibility TEXT
    );
    CREATE TABLE risk_alert (
      alert_id TEXT, alert_time TEXT, alert_type TEXT, severity TEXT,
      ts_code TEXT, message TEXT, action TEXT
    );
    CREATE TABLE valuation_snapshot (
      ticker TEXT, pe_ttm REAL, ps_ttm REAL, pb REAL, ev_ebitda_ttm REAL,
      historical_percentile REAL, peer_percentile REAL,
      broker_target_price REAL, current_price REAL,
      valuation_status TEXT, valuation_confidence REAL, generated_at TEXT
    );
    CREATE TABLE fundamentals_snapshot (
      ticker TEXT, market TEXT, revenue REAL, gross_profit REAL,
      operating_income REAL, net_income REAL, total_assets REAL,
      total_liabilities REAL, total_equity REAL, operating_cash_flow REAL,
      free_cash_flow REAL, roe REAL, roa REAL, gross_margin REAL,
      operating_margin REAL, net_margin REAL, debt_to_equity REAL,
      current_ratio REAL, asset_turnover REAL, data_quality REAL,
      source TEXT, period_end TEXT, created_at TEXT
    );
    CREATE TABLE research_claims (
      claim_id TEXT, claim_type TEXT, theme TEXT, claim_text TEXT,
      stance TEXT, importance TEXT, confidence REAL, ticker TEXT,
      created_at TEXT
    );

    INSERT INTO stock_pool_current VALUES
      ('300308.SZ', 'semiconductor_optics', 'watchlist', '2026-07-01');
    INSERT INTO daily_bar VALUES
      ('300308.SZ', '2026-07-10', 100, 106, 99, 105, 1000, 6),
      ('600519.SH', '2026-07-10', 99, 105, 98, 104, 900, 5.2);
    INSERT INTO factor_daily VALUES
      ('300308.SZ', 'pe_ttm', 25, '2026-07-10'),
      ('300308.SZ', 'pb', 3, '2026-07-10'),
      ('300308.SZ', 'roe_reported', 18, '2026-07-10'),
      ('300308.SZ', 'gross_margin', 0.35, '2026-07-10'),
      ('300308.SZ', 'revenue_yoy', 20, '2026-07-10');
    INSERT INTO news_items VALUES
      ('news-1', '公司获得新订单', '公司获得重要客户订单，业绩有望增长。',
       'fixture', '测试资讯', '2026-07-10T09:00:00+08:00',
       '["300308.SZ","600519.SH"]', '["AI"]',
       'https://example.invalid/news-1', 'high');
    INSERT INTO valuation_snapshot VALUES
      ('300308.SZ', 25, 4, 3, 20, 55, 50, 120, 105,
       'fair', 0.8, '2026-07-10T10:00:00+08:00');
    INSERT INTO fundamentals_snapshot VALUES
      ('300308.SZ', 'A', 1000, 350, 180, 120, 2000, 800, 1200,
       150, 100, 0.18, 0.1, 0.35, 0.18, 0.12, 0.67, 1.8, 0.5,
       0.9, 'fixture', '2026-06-30', '2026-07-10T10:00:00+08:00');
  `);
  db.close();
  return { dbPath };
}

async function startResearchApp(dbPath) {
  process.env.SMR_DB_PATH = dbPath;
  const { legacyApp } = await import(`../../api/legacy-app.js?research-contract=${Date.now()}-${Math.random()}`);
  const server = await new Promise((resolve) => {
    const instance = legacyApp.listen(0, "127.0.0.1", () => resolve(instance));
  });
  return {
    server,
    get: async (route) => {
      const response = await fetch(`http://127.0.0.1:${server.address().port}${route}`);
      const body = await response.json();
      assert.equal(response.status, 200, `${route}: ${JSON.stringify(body)}`);
      return body;
    },
  };
}

test("research endpoints retain their golden response contracts", async (t) => {
  const { dbPath } = createResearchFixture();
  const { server, get } = await startResearchApp(dbPath);
  t.after(() => new Promise((resolve) => server.close(resolve)));

  const dashboard = await get("/api/dashboard");
  assert.deepEqual(Object.keys(dashboard).sort(), ["dataFreshness", "poolByType", "summary", "updatedAt"]);
  assert.deepEqual(Object.keys(dashboard.summary).sort(), [
    "ahCoverage", "newsCount", "poolTotal", "riskAlerts", "usCoverage", "withFundamentals",
  ]);

  const scores = await get("/api/value-scores");
  assert.deepEqual(Object.keys(scores).sort(), ["scores", "updatedAt"]);
  assert.equal(scores.scores[0].tsCode, "300308.SZ");
  assert.deepEqual(Object.keys(scores.scores[0]).sort(), [
    "compositeScore", "fundamentalQuality", "industryPosition", "latestClose",
    "macdSignal", "market", "momentum20d", "momentum5d", "name", "pePercentile",
    "sector", "technicalMomentum", "themeRelevance", "tsCode", "valuationPosition", "verdict",
  ]);

  const stock = await get("/api/stock/300308.SZ");
  assert.equal(stock.tsCode, "300308.SZ");
  assert.ok(stock.report);
  assert.ok(stock.report.deepReport);
  assert.ok(Array.isArray(stock.priceHistory));

  const discoveries = await get("/api/discoveries");
  assert.deepEqual(Object.keys(discoveries).sort(), [
    "discoveries", "newsCandidateCount", "priceSpikeCount", "updatedAt",
  ]);
  assert.ok(discoveries.discoveries.some((item) => item.ticker === "600519.SH"));

  const news = await get("/api/news");
  assert.deepEqual(Object.keys(news).sort(), ["items", "sources", "updatedAt"]);
  assert.deepEqual(Object.keys(news.items[0]).sort(), [
    "credibility", "hasFullBody", "id", "publishedAt", "source", "sourceName",
    "summary", "tickers", "title", "url",
  ]);

  const newsDetail = await get("/api/news/news-1");
  assert.deepEqual(Object.keys(newsDetail).sort(), [
    "body", "credibility", "credibilityText", "id", "insights", "publishedAt",
    "source", "sourceName", "themes", "tickers", "title", "updatedAt", "url",
  ]);
  assert.ok(newsDetail.insights.length > 0);
});

test("classic dashboard degrades to an empty state when legacy tables are absent", async (t) => {
  const directory = mkdtempSync(path.join(os.tmpdir(), "smr-workflow-only-contract-"));
  const dbPath = path.join(directory, "workflow-only.db");
  new Database(dbPath).close();
  const { server, get } = await startResearchApp(dbPath);
  t.after(() => new Promise((resolve) => server.close(resolve)));

  const dashboard = await get("/api/dashboard");
  assert.equal(dashboard.summary.poolTotal, 0);
  assert.equal(dashboard.summary.newsCount, 0);
  assert.deepEqual((await get("/api/value-scores")).scores, []);
  assert.deepEqual((await get("/api/discoveries")).discoveries, []);
  assert.deepEqual((await get("/api/news")).items, []);
});
