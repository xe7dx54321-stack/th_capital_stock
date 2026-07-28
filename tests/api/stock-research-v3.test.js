import assert from "node:assert/strict";
import test from "node:test";

import {
  REQUIRED_V3_HEADINGS,
  StockResearchV3Service,
  applyDeterministicEditorialGuards,
  buildResearchSynthesisBrief,
  completeMissingSectionsFromGovernedDraft,
  evaluateResearchReportEligibility,
  finalizeModelResearchReport,
  restoreGovernedResearchTables,
  validateModelResearchReport,
} from "../../api/services/stock-research-v3-service.js";


function packetFixture() {
  return {
    schema_version: "2.0",
    workflow_version: "3.0",
    ticker: "300308.SZ",
    market: "A",
    generated_at: "2026-07-21T00:00:00Z",
    quality: { usable_evidence_ids: ["ev_annual"] },
    research_v3: {
      plan: {
        methodology: ["official_filing_first"],
        sections: REQUIRED_V3_HEADINGS.map((title, index) => ({ section_id: `s${index}`, title, required: true })),
      },
      provider_status: { official_filings: { status: "available" } },
      analysis: {
        annual_financials: { status: "available", periods: ["2025", "2024", "2023"] },
        coverage: { score: 1 },
      },
      context: {
        identity: { ticker: "300308.SZ", company_name: "中际旭创股份有限公司" },
        corpus: {
          filings: [{ filing_id: "doc1", title: "2025年年度报告" }],
          chunks: [{
            chunk_id: "c1",
            section_name: "主要会计数据和财务指标",
            research_topics: ["financials"],
            evidence_id: "ev_annual",
            source_key: "cninfo",
            retrieval_score: 1,
            text: "2025年营业收入和净利润增长。",
          }],
          news: [{ news_id: "n1", evidence_id: "news:n1", title: "产品进展", allowed_usage: "context_only" }],
          events: [{ event_id: "e1", evidence_id: "event:e1", title: "投资者交流" }],
        },
        graph: { peers: ["300502.SZ"] },
        instruments: { target: { daily_bars: [] }, peers: [] },
      },
    },
  };
}

function passingReport(extra = "") {
  const citationIds = ["ev_annual", "news:n1", "event:e1"];
  const sections = REQUIRED_V3_HEADINGS.map((heading, index) =>
    `## ${index + 1}. ${heading}\n\n基于正式披露形成研究判断 [${citationIds[index % citationIds.length]}]。`
  ).join("\n\n");
  const tables = Array.from({ length: 4 }, (_, index) =>
    `| 指标${index + 1} | 数值 |\n|---|---:|\n| 样本 | ${index + 1} |`
  ).join("\n\n");
  return `# 中际旭创深度研究\n\n${sections}\n\n${tables}\n\n中际旭创的公司特异性分析。\n\n${extra || "研究内容".repeat(4_500)}`;
}

test("V3 validator rejects unknown citations and system metadata", () => {
  const report = passingReport().replace("[ev_annual]", "[ev_unknown]")
    + "\n任务编号：run_x\n产品外观 产品特性 应用场景\n√适用 □不适用\n15 / 248";
  const result = validateModelResearchReport(report, packetFixture());
  assert.equal(result.status, "failed");
  assert.ok(result.errors.some((item) => item.code === "unknown_report_citation"));
  assert.ok(result.errors.some((item) => item.code === "system_metadata_in_report"));
  assert.ok(result.errors.some((item) => item.code === "raw_source_noise_in_report"));
  assert.ok(result.errors.some((item) => item.code === "raw_source_layout_noise_in_report"));
});

test("V3 validator only treats a standalone spaced page fraction as layout noise", () => {
  const legitimate = passingReport("产品组合按 400/800 速率演进，经营现金流/净利润用于衡量现金质量。");
  const legitimateResult = validateModelResearchReport(legitimate, packetFixture());
  assert.equal(
    legitimateResult.errors.some((item) => item.code === "raw_source_layout_noise_in_report"),
    false,
  );

  const pageNoise = `${passingReport()}\n15 / 248`;
  const pageNoiseResult = validateModelResearchReport(pageNoise, packetFixture());
  assert.equal(
    pageNoiseResult.errors.some((item) => item.code === "raw_source_layout_noise_in_report"),
    true,
  );
});

test("V3 validator rejects broker-only material and research-process prose", () => {
  const packet = packetFixture();
  packet.research_v3.context.corpus.filings = [];
  packet.research_v3.context.corpus.chunks = [];
  packet.research_v3.context.corpus.broker_reports = [{
    evidence_id: "broker:sample",
    title: "样本研报",
    text: "二级研究观点",
  }];
  packet.research_v3.analysis.annual_financials = { status: "unavailable" };
  const eligibility = evaluateResearchReportEligibility(packet);
  assert.equal(eligibility.eligible, false);

  const result = validateModelResearchReport(
    passingReport() + "\n下一步必须补齐正式公告。",
    packet,
  );
  assert.equal(result.status, "failed");
  assert.ok(result.errors.some((item) => item.code === "insufficient_primary_research_evidence"));
  assert.ok(result.errors.some((item) => item.code === "research_process_text_in_report"));
});

test("V3 validator rejects prose that contradicts annual financial directions", () => {
  const packet = packetFixture();
  packet.research_v3.analysis.annual_financials.metrics = {
    revenue: { yoy: 0.10 },
    attributable_net_income: { yoy: -0.28 },
    operating_cash_flow: { yoy: -0.75 },
    weighted_roe: { change_pp: -0.0141 },
  };
  const result = validateModelResearchReport(
    passingReport("利润增速快于收入，三项指标同时上行，较上年提升。" + "研究".repeat(4_500)),
    packet,
  );
  assert.equal(result.status, "failed");
  assert.ok(result.errors.some((item) => item.code === "numeric_narrative_contradiction"));
});

test("V3 validator rejects generic or duplicated long-form filler", () => {
  const generic = passingReport().replaceAll("中际旭创", "目标公司");
  const genericResult = validateModelResearchReport(generic, packetFixture());
  assert.ok(genericResult.errors.some((item) => item.code === "insufficient_company_specificity"));

  const duplicate = "这是一段超过一百个字符的重复正文，用于证明报告不能依靠复制粘贴凑足篇幅。".repeat(6);
  const duplicateResult = validateModelResearchReport(
    passingReport(`${duplicate}\n\n${duplicate}\n\n${"有效研究".repeat(4_500)}`),
    packetFixture(),
  );
  assert.ok(duplicateResult.errors.some((item) => item.code === "duplicate_substantive_paragraphs"));
});

test("synthesis brief bounds raw filing chunks and exposes allowed evidence", () => {
  const packet = packetFixture();
  packet.research_v3.context.corpus.chunks[0].text = "证据".repeat(4_000);
  packet.research_v3.provider_status = { internal_workflow_state: "should not reach the writer" };
  packet.research_v3.analysis.coverage = { score: 1, sections: [{ status: "covered" }] };
  const brief = buildResearchSynthesisBrief(packet);
  assert.ok(brief.document_chunks[0].text.length <= 1_400);
  assert.equal("provider_status" in brief, false);
  assert.equal("coverage" in brief.deterministic_analysis, false);
  assert.deepEqual(new Set(brief.allowed_evidence_ids), new Set(["ev_annual", "news:n1", "event:e1"]));
});

test("governed financial tables are restored and deterministic editorial contradictions are corrected", () => {
  const draft = passingReport();
  const candidate = draft.replace(/\| 指标[\s\S]*?(?=\n\n中际旭创的公司特异性分析)/u, "");
  assert.equal(validateModelResearchReport(candidate, packetFixture()).errors.some(
    (item) => item.code === "insufficient_research_tables",
  ), true);
  const restored = restoreGovernedResearchTables(candidate, draft);
  assert.ok(validateModelResearchReport(restored, packetFixture()).table_count >= 4);

  const packet = packetFixture();
  packet.research_v3.context.instruments.target.valuation = { market_cap: 100 };
  packet.research_v3.context.instruments.peers = [
    { valuation: { market_cap: 200 } },
    { valuation: { market_cap: 300 } },
  ];
  const guarded = applyDeterministicEditorialGuards(
    "传输类产品覆盖长距网络并贡献较稳定的现金流。公司在行业内的规模位次处于中游。公司管理层表示电信市场处于上一轮周期尾端。",
    packet,
  );
  assert.ok(guarded.includes("传输类产品构成公司传统业务收入来源"));
  assert.equal(/传输类产品[^。；\n]{0,80}(?:稳定|贡献)[^。；\n]{0,30}现金流/u.test(guarded), false);
  assert.ok(guarded.includes("市值规模最小"));
  assert.ok(guarded.includes("山西证券研报转述公司管理层表示"));
});

test("finalizer removes a governed table duplicated by a richer table and recalculates asset shares", () => {
  const packet = packetFixture();
  packet.research_v3.analysis.annual_financials.metrics = {
    total_assets: { "2025": 2_853_193_560 },
  };
  const governedTable = [
    "| 科目 | 2025 年末 | 占总资产比例 |",
    "|---|---:|---:|",
    "| 存货 | 5.45 亿元 | 19.10% |",
    "| 在建工程 | 1.83 亿元 | 6.40% |",
  ].join("\n");
  const richerTable = [
    "| 科目 | 2025 年末 | 同比 | 占总资产比例 |",
    "|---|---:|---:|---:|",
    "| 存货 | 5.45 亿元 | +54.06% | 19.10% |",
    "| 在建工程 | 1.83 亿元 | +218.88% | 6.40% |",
    "| 其他流动资产 | 2.12 亿元 | +183.37% | 0.74% |",
  ].join("\n");
  const draft = passingReport().replace(
    "## 6. 财务深度分析",
    `## 6. 财务深度分析\n\n${governedTable}`,
  );
  const candidate = passingReport().replace(
    "## 6. 财务深度分析",
    `## 6. 财务深度分析\n\n${governedTable}\n\n${richerTable}`,
  );
  const finalized = finalizeModelResearchReport(candidate, draft, packet);
  assert.equal(finalized.split(governedTable).length - 1, 0);
  assert.ok(finalized.includes("| 其他流动资产 | 2.12 亿元 | +183.37% | 7.43% |"));
  assert.equal(
    validateModelResearchReport(finalized, packet).errors.some(
      (item) => item.code === "derived_table_value_mismatch",
    ),
    false,
  );
});

test("service repairs a short first draft and accepts the passing second report", async () => {
  const calls = [];
  const service = new StockResearchV3Service({
    minimumCharacters: 2_000,
    modelAvailable: () => true,
    async modelCall(messages, options) {
      calls.push({ messages, options });
      return { content: calls.length === 1 ? "太短" : passingReport("研究内容".repeat(1_200)) };
    },
  });
  const result = await service.synthesize({ packet: packetFixture(), governedDraft: passingReport() });
  assert.equal(result.mode, "model_repaired", JSON.stringify(result));
  assert.equal(result.attempts, 2);
  assert.equal(result.validation.status, "passed", JSON.stringify(result.validation));
  assert.equal(calls.length, 2);
  assert.equal(calls[0].options.slotName, "long_context_secondary");
  assert.equal(calls[0].options.maxTokens, 14_000);
  assert.equal(calls[0].options.timeoutMs, 360_000);
});

test("service completes only missing model sections from the governed draft without rewriting the report", async () => {
  const governedDraft = passingReport();
  const candidate = governedDraft
    .replace(/## 12\. 三种情景[\s\S]*?(?=## 13\.)/u, "")
    .replace(/## 13\. 后续跟踪指标[\s\S]*?(?=## 14\.)/u, "")
    .replace(/## 15\. 证据索引[\s\S]*$/u, "")
    + `\n\n${Array.from({ length: 4 }, (_, index) =>
      `| 指标${index + 1} | 数值 |\n|---|---:|\n| 样本 | ${index + 1} |`
    ).join("\n\n")}\n\n中际旭创的公司特异性分析。\n\n${"有效研究".repeat(4_500)}`;
  const initialValidation = validateModelResearchReport(candidate, packetFixture());
  assert.deepEqual(
    initialValidation.errors.map((item) => item.code),
    ["missing_required_sections"],
  );
  const directlyCompleted = completeMissingSectionsFromGovernedDraft(
    candidate,
    governedDraft,
    initialValidation,
  );
  assert.equal(validateModelResearchReport(directlyCompleted, packetFixture()).status, "passed");

  let calls = 0;
  const service = new StockResearchV3Service({
    modelAvailable: () => true,
    async modelCall() {
      calls += 1;
      return { content: candidate };
    },
  });
  const result = await service.synthesize({ packet: packetFixture(), governedDraft });
  assert.equal(result.mode, "model_completed_with_governed_sections");
  assert.equal(result.validation.status, "passed");
  assert.equal(result.attempts, 1);
  assert.equal(calls, 1);
  assert.ok(result.report.indexOf("三种情景") < result.report.indexOf("结论"));
  assert.ok(result.report.indexOf("证据索引") > result.report.indexOf("结论"));
});

test("model unavailability keeps a useful governed draft", async () => {
  const draft = passingReport();
  const service = new StockResearchV3Service({ modelAvailable: () => false });
  const result = await service.synthesize({ packet: packetFixture(), governedDraft: draft });
  assert.equal(result.mode, "governed_fallback_model_unavailable");
  assert.equal(result.report, draft);
  assert.equal(result.validation.status, "passed");
});
