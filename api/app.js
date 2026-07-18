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


const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..");
export const DB_PATH = process.env.SMR_DB_PATH
  ? path.resolve(process.env.SMR_DB_PATH)
  : path.join(PROJECT_ROOT, "01_data", "db", "smr.db");
const ARTIFACT_ROOTS = process.env.SMR_ARTIFACT_ROOTS
  ? process.env.SMR_ARTIFACT_ROOTS.split(path.delimiter).filter(Boolean)
  : [path.join(PROJECT_ROOT, "06_outputs", "workflows")];

export function createApp({
  dbPath = DB_PATH,
  artifactRoots = ARTIFACT_ROOTS,
  pythonExecutable,
} = {}) {
  if (legacyApp.locals.workflowRuntimeMounted) return legacyApp;
  const migrationService = new WorkflowProcessService({ dbPath, repository: null, pythonExecutable });
  migrationService.ensureMigrations();
  const repository = new WorkflowRepository(dbPath);
  const processService = new WorkflowProcessService({ dbPath, repository, pythonExecutable });
  legacyApp.use(createWorkflowRouter({ repository, processService }));
  legacyApp.use(createArtifactRouter({ repository, allowedRoots: artifactRoots }));
  legacyApp.use(createMemoryRouter({ database: repository.db }));
  legacyApp.use(createDecisionRouter({ database: repository.db }));
  legacyApp.use(createRealtimeNewsRouter());
  legacyApp.use(createMappingRouter());
  legacyApp.locals.workflowRuntimeMounted = true;
  legacyApp.locals.workflowRepository = repository;
  return legacyApp;
}

export const app = createApp();
