import assert from "node:assert/strict";
import test from "node:test";

import { buildGovernedWorkflowInput } from "../../api/services/workflow-engine.js";


test("theme natural-language adapter builds a non-empty auditable supernode universe", () => {
  const input = buildGovernedWorkflowInput("theme_expectation_gap", {
    userQuery: "筛一份当前最强的 AI 算力超节点候选",
    data: {
      routingEnvelope: {
        topic: "AI 算力超节点",
        entities: [],
      },
    },
    input: {},
    currentInput: {},
  });

  assert.equal(input.raw_candidates.length, 4);
  assert.deepEqual(
    new Set(input.raw_candidates.map((item) => item.ticker)),
    new Set(["002396.SZ", "301165.SZ", "000938.SZ", "688629.SH"]),
  );
  assert.ok(input.raw_candidates.every((item) => item.business_purity > 0));
});


test("industry causal adapter fills all eight nodes and seven explicitly inferred edges", () => {
  const input = buildGovernedWorkflowInput("industry_causal_explainer", {
    userQuery: "为什么 DCI 需求明确但 A 股长期没有催化？",
    data: { routingEnvelope: { topic: "DCI" } },
    input: {},
    currentInput: {},
  });

  assert.equal(Object.keys(input.causal_nodes_input).length, 8);
  assert.equal(input.causal_edges_input.length, 7);
  assert.ok(input.causal_edges_input.every((edge) => edge.edge_kind === "inferred"));
  assert.ok(input.alternatives_input.length >= 2);
});


test("claim correction adapter uses re-fetched evidence and recomputes dependent PE", () => {
  const input = buildGovernedWorkflowInput("claim_correction", {
    userQuery: "星网锐捷市值不是199亿元，请按最新权威数据纠正",
    data: {
      currentTicker: "002396.SZ",
      routingEnvelope: {
        entities: [{ ticker: "002396.SZ", name: "星网锐捷", role: "target" }],
        correctionTarget: {
          field: "market_cap",
          previousValue: 199,
          claimedValue: null,
          entity: "002396.SZ",
        },
        confirmedFacts: [
          {
            field: "market_cap",
            value: 199,
            unit: "亿元",
            ticker: "002396.SZ",
            evidenceId: "ev_old",
          },
        ],
      },
      instrumentData: {
        valuation: { marketCap: 26_000_000_000 },
        fundamentals: { netIncome: 1_300_000_000 },
        source: "cross_validated_market_snapshot",
        source_url: "https://example.invalid/authoritative-snapshot",
        fetched_at: "2026-07-23T08:00:00Z",
      },
      evidenceCatalog: [
        { tool_id: "get_stock_data", evidence_id: "E001" },
      ],
    },
    input: {},
    currentInput: {},
  });

  assert.equal(input.correction.new_value, 26_000_000_000);
  assert.equal(input.correction.evidence_id, "E001");
  assert.equal(input.claims.find((claim) => claim.claim_id === "market_cap").value, 19_900_000_000);
  const pe = input.claims.find((claim) => claim.claim_id === "pe_ttm_recomputed");
  assert.equal(pe.value, 19_900_000_000 / 1_300_000_000);
  assert.equal(pe.formula, "market_cap / net_income");
});


test("claim correction adapter refuses to trust a user value that conflicts with re-fetched data", () => {
  assert.throws(
    () => buildGovernedWorkflowInput("claim_correction", {
      userQuery: "星网锐捷市值是260亿元，不是199亿元",
      data: {
        currentTicker: "002396.SZ",
        routingEnvelope: {
          entities: [{ ticker: "002396.SZ" }],
          correctionTarget: {
            field: "market_cap",
            previousValue: 199,
            claimedValue: 260,
            entity: "002396.SZ",
          },
          confirmedFacts: [{ field: "market_cap", value: 199, unit: "亿元", ticker: "002396.SZ" }],
        },
        instrumentData: {
          valuation: { marketCap: 30_000_000_000 },
          source: "verified_snapshot",
        },
        evidenceCatalog: [{ tool_id: "get_stock_data", evidence_id: "E001" }],
      },
      input: {},
      currentInput: {},
    }),
    /仍冲突/,
  );
});
