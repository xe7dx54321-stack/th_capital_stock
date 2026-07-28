import crypto from "crypto";
import express from "express";

import { WorkflowConflictError } from "../repositories/workflow-repository.js";
import { streamWorkflowEvents } from "../services/event-stream.js";


export const WORKFLOWS = [
  {
    workflow_id: "daily_brief",
    title: "Daily brief",
    description: "Summarize material changes for the day.",
    enabled: true,
    input_schema: {
      type: "object",
      properties: {
        allow_network: { type: "boolean", default: false },
        run_refresh_job: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "portfolio_review",
    title: "Portfolio review",
    description: "Review paper portfolio risk and decisions.",
    enabled: true,
    input_schema: {
      type: "object",
      properties: {
        allow_network: { type: "boolean", default: false },
        run_refresh_job: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "stock_deep_dive",
    title: "Stock deep dive",
    description: "Build an evidence-backed local company research report.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["ticker"],
      properties: {
        ticker: { type: "string" },
        allow_network: { type: "boolean", default: false },
        acquisition_mode: {
          type: "string",
          enum: ["cache_only", "refresh_if_stale", "force_refresh"],
          default: "refresh_if_stale",
        },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "operating_driver_valuation",
    title: "Operating driver valuation",
    description: "Build a deterministic operating-driver valuation model.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["ticker"],
      properties: {
        ticker: { type: "string" },
        model_template: { type: "string" },
        forecast_years: { type: "array" },
        drivers: { type: "array" },
        revenue_formula: { type: "string" },
        profit_formula: { type: "string" },
        shares_outstanding: { type: "number" },
        current_price: { type: "number" },
        current_market_cap: { type: "number" },
        terminal_pe: { type: "number" },
        forecast_horizon_years: { type: "integer" },
        scenarios: { type: "object" },
        sensitivity: { type: "object" },
        allow_network: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "pair_switch_decision",
    title: "Pair switch decision",
    description: "Compare two securities using a common data cut and deterministic scenarios.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["from_ticker", "to_ticker"],
      properties: {
        from_ticker: { type: "string" },
        to_ticker: { type: "string" },
        from_name: { type: "string" },
        to_name: { type: "string" },
        preference: { type: "object" },
        temporal_threshold_hours: { type: "number" },
        from_holding: { type: "object" },
        phase4_from_json: {},
        phase4_to_json: {},
        allow_network: { type: "boolean", default: false },
      },
      additionalProperties: true,
    },
  },
  {
    workflow_id: "theme_expectation_gap",
    title: "Theme expectation gap",
    description: "Rank a transparent theme universe with deterministic expectation-gap dimensions.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["theme_name", "raw_candidates"],
      properties: {
        theme_name: { type: "string" },
        theme_id: { type: "string" },
        raw_candidates: { type: "array" },
        keyword_hint_list: { type: "array" },
        inclusion_overrides: { type: "object" },
        market_overrides: { type: "object" },
        evidence_overrides: { type: "object" },
        allow_network: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "industry_causal_explainer",
    title: "Industry causal explainer",
    description: "Build an eight-step evidence-aware causal chain with alternatives.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["theme", "question", "causal_nodes_input", "causal_edges_input", "alternatives_input"],
      properties: {
        theme: { type: "string" },
        question: { type: "string" },
        entity_key: { type: "string" },
        causal_nodes_input: { type: "object" },
        causal_edges_input: { type: "array" },
        alternatives_input: { type: "array" },
        allow_network: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "company_signal_plan",
    title: "Company signal plan",
    description: "Create a governed four-state company monitoring plan.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["ticker", "raw_signals"],
      properties: {
        ticker: { type: "string" },
        name: { type: "string" },
        raw_signals: { type: "array" },
        transition_requests: { type: "array" },
        axes: { type: "array" },
        allow_network: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "claim_correction",
    title: "Claim correction",
    description: "Correct an evidence-backed claim and recompute all dependent claims.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["entity_key", "claims", "correction"],
      properties: {
        entity_key: { type: "string" },
        claims: { type: "array" },
        correction: { type: "object" },
        allow_network: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    workflow_id: "thesis_update",
    title: "Thesis update",
    description: "Propose a governed update to an investment thesis.",
    enabled: true,
    input_schema: {
      type: "object",
      required: ["ticker", "updates", "evidence_links"],
      properties: {
        ticker: { type: "string" },
        updates: { type: "object" },
        evidence_links: { type: "array" },
        confidence: { type: "number", minimum: 0, maximum: 1 },
        allow_network: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
];

const WORKFLOW_MAP = new Map(WORKFLOWS.map((workflow) => [workflow.workflow_id, workflow]));
const TICKER_PATTERN = /^(?:\d{6}\.(?:SZ|SH|BJ)|\d{5}\.HK|[A-Z][A-Z0-9.-]{0,9})$/;

function stableHash(value) {
  return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function validateRunRequest(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new TypeError("request body must be an object");
  }
  const keys = Object.keys(body);
  if (keys.some((key) => !["workflow_id", "input"].includes(key))) {
    throw new TypeError("request contains unsupported fields");
  }
  const workflow = WORKFLOW_MAP.get(body.workflow_id);
  if (!workflow) throw new TypeError("unknown workflow_id");
  if (!workflow.enabled) throw new WorkflowConflictError("workflow is not implemented yet");
  const input = body.input ?? {};
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new TypeError("input must be an object");
  }
  if (workflow.workflow_id === "stock_deep_dive") {
    if (Object.keys(input).some((key) => !["ticker", "allow_network", "acquisition_mode"].includes(key))) {
      throw new TypeError("stock_deep_dive input contains unsupported fields");
    }
    const ticker = String(input.ticker || "").trim().toUpperCase();
    if (!TICKER_PATTERN.test(ticker)) throw new TypeError("invalid ticker");
    if (input.allow_network !== undefined && typeof input.allow_network !== "boolean") {
      throw new TypeError("allow_network must be a boolean");
    }
    const allowedModes = new Set(["cache_only", "refresh_if_stale", "force_refresh"]);
    const acquisitionMode = input.acquisition_mode
      ?? (input.allow_network === false ? "cache_only" : "refresh_if_stale");
    if (!allowedModes.has(acquisitionMode)) throw new TypeError("invalid acquisition_mode");
    return {
      workflow,
      input: {
        ticker,
        allow_network: acquisitionMode !== "cache_only",
        acquisition_mode: acquisitionMode,
      },
    };
  }
  if (["daily_brief", "portfolio_review"].includes(workflow.workflow_id)) {
    if (Object.keys(input).some((key) => !["allow_network", "run_refresh_job"].includes(key))) {
      throw new TypeError(`${workflow.workflow_id} input contains unsupported fields`);
    }
    if (input.allow_network !== undefined && typeof input.allow_network !== "boolean") {
      throw new TypeError("allow_network must be a boolean");
    }
    if (input.allow_network === true) throw new TypeError("MVP only supports allow_network=false");
    if (input.run_refresh_job !== undefined && typeof input.run_refresh_job !== "boolean") {
      throw new TypeError("run_refresh_job must be a boolean");
    }
    return {
      workflow,
      input: { allow_network: false, run_refresh_job: input.run_refresh_job === true },
    };
  }
  if (workflow.workflow_id === "thesis_update") {
    if (Object.keys(input).some((key) => !["ticker", "updates", "evidence_links", "confidence", "allow_network"].includes(key))) {
      throw new TypeError("thesis_update input contains unsupported fields");
    }
    const ticker = String(input.ticker || "").trim().toUpperCase();
    if (!TICKER_PATTERN.test(ticker)) throw new TypeError("invalid ticker");
    if (!input.updates || typeof input.updates !== "object" || Array.isArray(input.updates) || Object.keys(input.updates).length === 0) {
      throw new TypeError("updates must be a non-empty object");
    }
    if (!Array.isArray(input.evidence_links) || input.evidence_links.length === 0) {
      throw new TypeError("at least one evidence link is required");
    }
    if (input.allow_network === true) throw new TypeError("MVP only supports allow_network=false");
    if (input.confidence !== undefined && (typeof input.confidence !== "number" || input.confidence < 0 || input.confidence > 1)) {
      throw new TypeError("confidence must be between 0 and 1");
    }
    return { workflow, input: { ...input, ticker, allow_network: false } };
  }
  if ([
    "operating_driver_valuation",
    "pair_switch_decision",
    "theme_expectation_gap",
    "industry_causal_explainer",
    "company_signal_plan",
    "claim_correction",
  ].includes(workflow.workflow_id)) {
    const schema = workflow.input_schema || {};
    const properties = schema.properties || {};
    if (schema.additionalProperties === false
        && Object.keys(input).some((key) => !Object.hasOwn(properties, key))) {
      throw new TypeError(`${workflow.workflow_id} input contains unsupported fields`);
    }
    for (const required of schema.required || []) {
      if (input[required] === undefined || input[required] === null || input[required] === "") {
        throw new TypeError(`${required} is required`);
      }
    }
    if (input.allow_network === true) {
      throw new TypeError(`${workflow.workflow_id} only supports allow_network=false`);
    }
    const normalized = { ...input, allow_network: false };
    for (const key of ["ticker", "from_ticker", "to_ticker"]) {
      if (normalized[key] !== undefined) {
        normalized[key] = String(normalized[key]).trim().toUpperCase();
        if (!TICKER_PATTERN.test(normalized[key])) throw new TypeError(`invalid ${key}`);
      }
    }
    return { workflow, input: normalized };
  }
  return { workflow, input };
}

export function createWorkflowRouter({ repository, processService }) {
  const router = express.Router();

  router.get("/api/workflows", (_req, res) => {
    res.json({ workflows: WORKFLOWS });
  });

  router.post("/api/workflow-runs", (req, res) => {
    try {
      const { workflow, input } = validateRunRequest(req.body);
      const idempotencyKey = req.get("Idempotency-Key")?.trim() || null;
      if (idempotencyKey && idempotencyKey.length > 200) {
        res.status(400).json({ error: "Idempotency-Key is too long" });
        return;
      }
      const runId = `run_${crypto.randomUUID().replaceAll("-", "")}`;
      const requestHash = stableHash({ workflow_id: workflow.workflow_id, input });
      const created = repository.createQueuedRun({
        runId,
        workflowId: workflow.workflow_id,
        input,
        idempotencyKey,
        requestHash,
      });
      if (!created.reused) processService.startExistingRun(runId);
      res.status(created.reused ? 200 : 202).json(created.run);
    } catch (error) {
      if (error instanceof WorkflowConflictError) {
        res.status(409).json({ error: error.message });
      } else if (error instanceof TypeError) {
        res.status(400).json({ error: error.message });
      } else {
        res.status(500).json({ error: error.message });
      }
    }
  });

  router.get("/api/workflow-runs", (req, res) => {
    res.json({ runs: repository.listRuns(req.query.limit) });
  });

  router.get("/api/workflow-runs/:id", (req, res) => {
    const run = repository.getRun(req.params.id);
    if (!run) {
      res.status(404).json({ error: "workflow run not found" });
      return;
    }
    res.json({ ...run, artifacts: repository.listArtifacts(req.params.id) });
  });

  router.post("/api/workflow-runs/:id/cancel", (req, res) => {
    const result = repository.requestCancel(req.params.id);
    if (!result) {
      res.status(404).json({ error: "workflow run not found" });
      return;
    }
    res.status(result.requested ? 202 : 200).json(result);
  });

  router.get("/api/workflow-runs/:id/events", (req, res) => {
    if (!repository.getRun(req.params.id)) {
      res.status(404).json({ error: "workflow run not found" });
      return;
    }
    res.json({ events: repository.listEvents(req.params.id, req.query.after) });
  });

  router.get("/api/workflow-runs/:id/stream", (req, res) => {
    streamWorkflowEvents(req, res, repository);
  });
  return router;
}

export { validateRunRequest };
