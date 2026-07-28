import fs from "node:fs";
import path from "path";
import { fileURLToPath } from "url";

import { legacyApp } from "./legacy-app.js";
import { WorkflowRepository } from "./repositories/workflow-repository.js";
import { createArtifactRouter } from "./routes/artifacts.js";
import { createDecisionRouter } from "./routes/decisions.js";
import { createMemoryRouter } from "./routes/memories.js";
import { createWorkflowRouter } from "./routes/workflows.js";
import { createRealtimeNewsRouter } from "./routes/realtime-news.js";
import { createMappingRouter } from "./routes/mapping.js";
import { WorkflowProcessService } from "./services/workflow-process.js";
import { WorkflowAuditService } from "./services/workflow-audit-service.js";
import {
  DEFAULT_GOVERNED_WORKFLOW_TIMEOUT_MS,
  GovernedWorkflowRunner,
} from "./services/governed-workflow-runner.js";
import { StockResearchV3Service } from "./services/stock-research-v3-service.js";


const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..");
export const DB_PATH = process.env.SMR_DB_PATH
  ? path.resolve(process.env.SMR_DB_PATH)
  : path.join(PROJECT_ROOT, "01_data", "db", "smr.db");
const ARTIFACT_ROOTS = process.env.SMR_ARTIFACT_ROOTS
  ? process.env.SMR_ARTIFACT_ROOTS.split(path.delimiter).filter(Boolean)
  : [path.join(PROJECT_ROOT, "06_outputs", "workflows")];
const SIBLING_RESEARCH_DB = path.resolve(PROJECT_ROOT, "..", "th_capital_stock", "01_data", "db", "smr.db");
const configuredGovernedTimeoutMs = Number.parseInt(
  process.env.SMR_GOVERNED_WORKFLOW_TIMEOUT_MS || "",
  10,
);
const GOVERNED_WORKFLOW_TIMEOUT_MS = Number.isFinite(configuredGovernedTimeoutMs)
  && configuredGovernedTimeoutMs > 0
  ? configuredGovernedTimeoutMs
  : DEFAULT_GOVERNED_WORKFLOW_TIMEOUT_MS;

function configureResearchSourceDatabase() {
  if (!process.env.SMR_SOURCE_DB_PATH && fs.existsSync(SIBLING_RESEARCH_DB)) {
    // 控制库负责工作流运行状态；大体量研究库只读接入，避免把 300MB+ 证据库复制进 MVP。
    process.env.SMR_SOURCE_DB_PATH = SIBLING_RESEARCH_DB;
  }
}

export function createApp({
  dbPath = DB_PATH,
  artifactRoots = ARTIFACT_ROOTS,
  pythonExecutable,
} = {}) {
  if (legacyApp.locals.workflowRuntimeMounted) return legacyApp;
  configureResearchSourceDatabase();
  const migrationService = new WorkflowProcessService({ dbPath, repository: null, pythonExecutable });
  migrationService.ensureMigrations();
  const repository = new WorkflowRepository(dbPath);
  const processService = new WorkflowProcessService({ dbPath, repository, pythonExecutable });
  const auditService = new WorkflowAuditService({ repository, artifactRoot: artifactRoots[0] });
  const researchSynthesisService = new StockResearchV3Service();
  const governedWorkflowRunner = new GovernedWorkflowRunner({
    repository,
    processService,
    artifactRoots,
    researchSynthesisService,
    timeoutMs: GOVERNED_WORKFLOW_TIMEOUT_MS,
  });
  legacyApp.use(createWorkflowRouter({ repository, processService }));
  legacyApp.use(createArtifactRouter({ repository, allowedRoots: artifactRoots }));
  legacyApp.use(createMemoryRouter({ database: repository.db }));
  legacyApp.use(createDecisionRouter({ database: repository.db }));
  legacyApp.use(createRealtimeNewsRouter());
  legacyApp.use(createMappingRouter());
  legacyApp.locals.workflowRuntimeMounted = true;
  legacyApp.locals.workflowRepository = repository;
  legacyApp.locals.workflowAuditService = auditService;
  legacyApp.locals.workflowProcessService = processService;
  legacyApp.locals.governedWorkflowRunner = governedWorkflowRunner;
  return legacyApp;
}

export const app = createApp();
