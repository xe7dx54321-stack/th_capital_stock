import assert from "node:assert/strict";
import test from "node:test";

import { ConversationManager } from "../../api/services/agent-orchestrator.js";
import { extractChatCompletionContent, fetchWithTimeout, getDefaultModel, getProviderConfig } from "../../api/services/llm-service.js";
import { AGENT_TOOLS, TASK_TYPES, WorkflowEngine } from "../../api/services/workflow-engine.js";

test("conversation cleanup timer does not keep Node alive", () => {
  const manager = new ConversationManager();
  assert.equal(manager.cleanupInterval.hasRef(), false);
  manager.close();
});

test("default research flows never write memories or decisions", () => {
  for (const task of Object.values(TASK_TYPES)) {
    assert.equal(task.defaultFlow.includes("save_memory"), false, `${task.id} writes memory by default`);
    assert.equal(task.defaultFlow.includes("create_decision"), false, `${task.id} writes decisions by default`);
  }
});

test("unauthorized write-only flow waits for review without touching storage", async () => {
  const engine = new WorkflowEngine();
  const result = await engine.executeFlow(["save_memory", "create_decision"]);

  assert.equal(result.status, "waiting_review");
  assert.deepEqual(result.workflowSummary, {
    totalSteps: 2,
    completedSteps: 0,
    failedSteps: 0,
    skippedSteps: 2,
    stepDetails: [],
  });
});

test("mixed tool outcomes are reported as partial instead of completed", async (t) => {
  AGENT_TOOLS.__test_success = {
    toolId: "__test_success",
    name: "测试成功工具",
    execute: async () => ({ success: true, data: {}, message: "ok" }),
  };
  AGENT_TOOLS.__test_failure = {
    toolId: "__test_failure",
    name: "测试失败工具",
    execute: async () => ({ success: false, message: "failed" }),
  };
  t.after(() => {
    delete AGENT_TOOLS.__test_success;
    delete AGENT_TOOLS.__test_failure;
  });

  const engine = new WorkflowEngine();
  const result = await engine.executeFlow(["__test_success", "__test_failure"]);

  assert.equal(result.status, "partial");
  assert.equal(result.workflowSummary.completedSteps, 1);
  assert.equal(result.workflowSummary.failedSteps, 1);
});

test("workflow engine records source evidence and updates the current-data gate", () => {
  const engine = new WorkflowEngine({ runId: "run_fixture" });
  const stale = engine.captureEvidence("get_pool_snapshot", {
    success: true,
    message: "获取到本地数据库股票池",
    data: [{ trade_date: "2026-06-01" }],
  }, "2026-07-20T08:00:00.000Z");

  assert.equal(stale.evidence_id, "E001");
  assert.equal(stale.freshness, "stale");
  assert.equal(engine.context.data.dataHealth.status, "blocked");
  assert.equal(engine.context.data.dataHealth.can_claim_current, false);

  const fresh = engine.captureEvidence("get_top_gainers", {
    success: true,
    message: "获取到实时涨幅榜（东方财富）",
    data: [{ trade_date: "2026-07-20", source: "eastmoney_realtime" }],
  }, "2026-07-20T11:00:00.000Z");

  assert.equal(fresh.evidence_id, "E002");
  assert.equal(engine.context.data.dataHealth.status, "warning");
  assert.equal(engine.context.data.dataHealth.can_claim_current, true);
  assert.deepEqual(engine.context.data.evidenceIds, ["E001", "E002"]);
  assert.equal(engine.context.data.evidenceSnapshots.length, 2);
  assert.equal(Object.keys(engine.context.data).includes("evidenceSnapshots"), false);
});

test("configured model slot is the single source of truth", () => {
  const minimax = getProviderConfig("minimax");
  const anthropic = getProviderConfig("anthropic");

  assert.equal(getDefaultModel({ provider: "minimax" }), "MiniMax-M2.7");
  assert.equal(minimax.apiStyle, "anthropic_messages");
  assert.equal(anthropic.apiStyle, "anthropic_messages");
});

test("Anthropic-compatible responses skip thinking blocks and collect all text blocks", () => {
  const content = extractChatCompletionContent({
    content: [
      { type: "thinking", thinking: "private reasoning" },
      { type: "text", text: "第一段" },
      { type: "text", text: "第二段" },
    ],
  }, "anthropic_messages");

  assert.equal(content, "第一段\n第二段");
});

test("model requests fail with an explicit timeout", async (t) => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener("abort", () => {
      const error = new Error("aborted");
      error.name = "AbortError";
      reject(error);
    });
  });
  t.after(() => { globalThis.fetch = originalFetch; });

  await assert.rejects(
    fetchWithTimeout("https://example.invalid", {}, 5),
    /模型请求超时（5ms）/,
  );
});

test("opportunity fallback excludes delisting names and passes the citation gate", () => {
  const engine = new WorkflowEngine();
  engine.currentTaskType = "opportunity_scan";
  const evidenceCatalog = [
    ["E001", "get_market_indices", "2026-07-17"],
    ["E002", "get_top_gainers", "2026-07-17"],
    ["E003", "get_top_losers", "2026-07-17"],
    ["E004", "get_volume_surge", "2026-07-17"],
    ["E006", "get_valuation_extremes", "2026-05-31"],
    ["E007", "get_latest_news", "2026-07-19"],
    ["E008", "get_pool_snapshot", "2026-07-08"],
  ].map(([evidence_id, tool_id, as_of]) => ({ evidence_id, tool_id, as_of }));
  engine.context.data = {
    evidenceCatalog,
    dataHealth: { status: "warning", can_claim_current: true },
    marketIndices: [{ name: "上证指数", price: 3865.3, pct_chg: -0.44 }],
    topGainers: [
      { name: "云创退", ts_code: "920305.BJ", trade_date: "2026-07-17", close: 2.02, low: 1.78, pct_chg: 29.49, turnover: 20.8, pe_ttm: -1.8 },
      { name: "样本股份", ts_code: "600000.SH", trade_date: "2026-07-17", close: 20, low: 18, pct_chg: 8, turnover: 6, pe_ttm: 25, total_mv: 8_000_000_000 },
    ],
    topLosers: [{ name: "风险样本", ts_code: "300000.SZ", pct_chg: -8 }],
    volumeSurge: [{ name: "样本股份", ts_code: "600000.SH", pct_chg: 8, turnover: 6, activity_signal: "turnover" }],
    volumeSurgeMode: "turnover",
    latestNews: [{ title: "A股市场样本新闻", published_at: "2026-07-19T01:00:00.000Z" }],
    llmAnalysis: { rawAnalysis: "过短且无证据的回答" },
  };

  const rejectedDraft = engine.context.data.llmAnalysis.rawAnalysis;
  const result = engine.buildResult();
  assert.equal(result.response.includes("云创退"), false);
  assert.match(result.response, /高换手异动/);
  assert.equal(result.data.reportQualityGate.source, "deterministic_fallback");
  assert.equal(result.data.citationValidation.status, "passed");
  assert.equal(result.data.citationValidation.coverage, 1);
  assert.equal(JSON.stringify(result.extractedMemories).includes(rejectedDraft), false);
  assert.ok(result.extractedMemories.length > 0);
});

test("daily brief rejects a weak model draft and produces a fully cited safe report", () => {
  const engine = new WorkflowEngine();
  engine.currentTaskType = "daily_brief";
  engine.context.data = {
    evidenceCatalog: [
      ["E001", "get_market_indices", "2026-07-17"],
      ["E002", "get_top_gainers", "2026-07-17"],
      ["E003", "get_top_losers", "2026-07-17"],
      ["E004", "get_volume_surge", "2026-07-17"],
      ["E005", "get_latest_news", null],
      ["E006", "get_pool_snapshot", "2026-07-08"],
    ].map(([evidence_id, tool_id, as_of]) => ({ evidence_id, tool_id, as_of })),
    dataHealth: { status: "warning", can_claim_current: true },
    marketIndices: [{ name: "上证指数", price: 3865.3, pct_chg: -0.44 }],
    topGainers: [
      { name: "云创退", ts_code: "920305.BJ", trade_date: "2026-07-17", close: 2.02, pct_chg: 29.49, turnover: 20.8 },
      { name: "样本股份", ts_code: "600000.SH", trade_date: "2026-07-17", close: 20, pct_chg: 8, turnover: 6 },
    ],
    topLosers: [{ name: "风险样本", ts_code: "300000.SZ", pct_chg: -8, turnover: 9 }],
    volumeSurge: [{ name: "样本股份", ts_code: "600000.SH", pct_chg: 8, turnover: 6 }],
    latestNews: [],
    llmAnalysis: { rawAnalysis: "__WEAK_DAILY_DRAFT__" },
  };

  const result = engine.buildResult();
  assert.equal(result.data.reportQualityGate.source, "deterministic_fallback");
  assert.match(result.response, /A股每日复盘（确定性报告）/);
  assert.match(result.response, /仅作风险记录，不进入关注清单/);
  assert.equal(result.data.citationValidation.status, "passed");
  assert.equal(result.data.citationValidation.coverage, 1);
  assert.equal(JSON.stringify(result.extractedMemories).includes("__WEAK_DAILY_DRAFT__"), false);
});

test("market news uses a deterministic retrieval flow without model interpretation", () => {
  assert.deepEqual(TASK_TYPES.MARKET_NEWS.defaultFlow, ["get_latest_news"]);
  const engine = new WorkflowEngine();
  engine.currentTaskType = "market_news";
  engine.context.data = {
    evidenceCatalog: [{ evidence_id: "E001", tool_id: "get_latest_news", as_of: "2026-07-19T01:00:00Z" }],
    dataHealth: { status: "healthy", can_claim_current: true },
    latestNews: [{
      title: "样本市场新闻",
      source_name: "权威样本源",
      published_at: "2026-07-19T01:00:00Z",
      url: "https://example.com/news/1",
    }],
  };

  const result = engine.buildResult();
  assert.match(result.response, /这是检索清单/);
  assert.match(result.response, /样本市场新闻/);
  assert.equal(result.data.citationValidation.status, "passed");
  assert.equal(result.data.citationValidation.coverage, 1);
});

test("market attribution has a dedicated deterministic route and never invents causes", () => {
  const engine = new WorkflowEngine();
  assert.equal(engine.detectTaskType("做一份今天涨跌幅前10的归因分析"), "MARKET_ATTRIBUTION");
  assert.deepEqual(TASK_TYPES.MARKET_ATTRIBUTION.defaultFlow, ["get_top_gainers", "get_top_losers", "get_movement_news"]);

  engine.currentTaskType = "market_attribution";
  engine.context.data = {
    evidenceCatalog: [
      { evidence_id: "E001", tool_id: "get_top_gainers", as_of: "2026-07-17T00:00:00Z" },
      { evidence_id: "E002", tool_id: "get_top_losers", as_of: "2026-07-17T00:00:00Z" },
      { evidence_id: "E003", tool_id: "get_movement_news", as_of: "2026-07-17T01:00:00Z" },
    ],
    dataHealth: { status: "healthy", can_claim_current: true },
    topGainers: [{ ts_code: "600001.SH", name: "样本甲", trade_date: "2026-07-17", pct_chg: 10, close: 11 }],
    topLosers: [{ ts_code: "600002.SH", name: "样本乙", trade_date: "2026-07-17", pct_chg: -8, close: 9 }],
    movementNews: [{ ticker: "600001.SH", title: "样本甲发布业绩公告", published_at: "2026-07-17T01:00:00Z" }],
  };

  const result = engine.buildResult();
  assert.match(result.response, /样本甲发布业绩公告/);
  assert.match(result.response, /样本乙[\s\S]*原因未确认/);
  assert.match(result.response, /不证明该公告就是涨跌的唯一原因/);
  assert.doesNotMatch(result.response, /归因状态：[^\n]*(?:主力拉升|机构出货|题材炒作导致)/);
  assert.equal(result.data.citationValidation.status, "passed");
  assert.equal(result.data.citationValidation.coverage, 1);
});

test("stock research rejects uncited analysis and removes implausible valuation fields", () => {
  const engine = new WorkflowEngine();
  engine.currentTaskType = "stock_deep_analysis";
  engine.context.data = {
    evidenceCatalog: [
      { evidence_id: "E001", tool_id: "get_stock_data", as_of: "2026-07-17T00:00:00Z" },
      { evidence_id: "E002", tool_id: "get_news", as_of: "2026-07-17T01:00:00Z" },
    ],
    dataHealth: { status: "healthy", can_claim_current: true },
    stockEntity: { name: "样本股份", tsCode: "600000.SH" },
    currentTicker: "600000.SH",
    instrumentData: {
      latestDate: "2026-07-17",
      latestPrice: 20,
      changePercent: 1.5,
      valuation: { pe: 25, pb: 3, ps: 1335.6 },
      fundamentals: { period: "2026Q1", revenue: 2_000_000_000, netIncome: 200_000_000, grossMargin: 30, roe: 8 },
      technical: { tradeDate: "2026-07-08", rsi14: 45, macdDif: 0.2, ma20: 19 },
      momentum: { m5d: 2, m20d: -1 },
    },
    eastmoneyData: { fundFlow: [], financialHistory: [], researchReports: [] },
    news: [{ title: "样本公告", source_name: "交易所", published_at: "2026-07-17T01:00:00Z" }],
    llmAnalysis: { rawAnalysis: "__UNCITED_STOCK_DRAFT__" },
  };

  const result = engine.buildResult();
  assert.equal(result.data.reportQualityGate.source, "deterministic_fallback");
  assert.match(result.response, /PS\(TTM\).*已从分析中剔除/);
  assert.match(result.response, /不足以直接形成买入、卖出、目标价或仓位建议/);
  assert.equal(result.data.citationValidation.status, "passed");
  assert.equal(result.data.citationValidation.coverage, 1);
  assert.equal(JSON.stringify(result.extractedMemories).includes("__UNCITED_STOCK_DRAFT__"), false);
});

test("stock research isolates a periodless inconsistent local fundamentals snapshot", () => {
  const engine = new WorkflowEngine();
  engine.currentTaskType = "stock_deep_analysis";
  engine.context.data = {
    evidenceCatalog: [
      { evidence_id: "E001", tool_id: "get_stock_data", as_of: "2026-07-17T00:00:00Z" },
      { evidence_id: "E002", tool_id: "get_news", as_of: "2026-07-17T01:00:00Z" },
    ],
    dataHealth: { status: "healthy", can_claim_current: true },
    currentTicker: "300308.SZ",
    instrumentData: {
      latestDate: "2026-07-17",
      latestPrice: 20,
      changePercent: 1.5,
      valuation: { pe: 25, pb: 3, ps: 5 },
      fundamentals: { period: null, revenue: 38_000_000_000, netIncome: 200_000_000, grossMargin: 7.3, roe: 66.7 },
      technical: { tradeDate: "2026-07-17", rsi14: 45, macdDif: 0.2, ma20: 19 },
      momentum: { m5d: 2, m20d: -1 },
    },
    eastmoneyData: { fundFlow: [], financialHistory: [{ reportName: "2026一季报", grossMargin: 46.1, roe: 17.5 }], researchReports: [] },
    news: [],
    llmAnalysis: { rawAnalysis: "__UNCITED_STOCK_DRAFT__" },
  };

  const result = engine.buildResult();
  assert.match(result.response, /已整体隔离/);
  assert.doesNotMatch(result.response, /营业收入 380\.00 亿元/);
  assert.match(result.response, /中际旭创（300308\.SZ）/);
  assert.equal(result.data.citationValidation.status, "passed");
});
