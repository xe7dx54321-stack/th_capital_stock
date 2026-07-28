import fs from "node:fs";
import path from "node:path";

import {
  StockResearchV3Service,
  finalizeModelResearchReport,
  validateModelResearchReport,
} from "../api/services/stock-research-v3-service.js";


function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}

const packetPath = argument("--packet");
const draftPath = argument("--draft");
const outputDir = argument("--output-dir");
const candidatePath = argument("--candidate");
const writeBackDir = argument("--write-back-dir");
if (!packetPath || !draftPath || !outputDir) {
  throw new Error("usage: node tools/synthesize_stock_deep_dive_v3.js --packet <json> --draft <md> [--candidate <md>] --output-dir <dir>");
}

const packet = JSON.parse(fs.readFileSync(path.resolve(packetPath), "utf8"));
const governedDraft = fs.readFileSync(path.resolve(draftPath), "utf8");
const startedAt = Date.now();
let result;
if (candidatePath) {
  const candidate = fs.readFileSync(path.resolve(candidatePath), "utf8");
  const report = finalizeModelResearchReport(candidate, governedDraft, packet);
  result = {
    report,
    mode: "offline_candidate_finalized",
    attempts: 0,
    validation: validateModelResearchReport(report, packet),
    candidate_report: candidate,
  };
} else {
  const service = new StockResearchV3Service();
  result = await service.synthesize({ packet, governedDraft });
}
const target = path.resolve(outputDir);
fs.mkdirSync(target, { recursive: true });
fs.writeFileSync(path.join(target, "stock_deep_dive_model.md"), result.report, "utf8");
if (result.candidate_report) {
  fs.writeFileSync(path.join(target, "stock_deep_dive_candidate.md"), result.candidate_report, "utf8");
}
fs.writeFileSync(path.join(target, "synthesis-result.json"), JSON.stringify({
  mode: result.mode,
  attempts: result.attempts,
  validation: result.validation,
  model_validation: result.model_validation || null,
  usage: result.usage || null,
  error: result.error || null,
  elapsed_ms: Date.now() - startedAt,
}, null, 2), "utf8");
if (writeBackDir) {
  const runDirectory = path.resolve(writeBackDir);
  const reportPath = path.join(runDirectory, "stock_deep_dive.md");
  const packetPath = path.join(runDirectory, "research_packet.json");
  const auditPath = path.join(runDirectory, "research_audit.json");
  fs.writeFileSync(reportPath, result.report, "utf8");
  const storedPacket = JSON.parse(fs.readFileSync(packetPath, "utf8"));
  const previousSynthesis = storedPacket.research_v3?.report_quality?.synthesis || {};
  const finalizedSynthesis = {
    ...previousSynthesis,
    validation: result.validation,
    postprocess: {
      mode: "deterministic_editorial_finalization",
      source_mode: previousSynthesis.mode || result.mode,
      finalized_at: new Date().toISOString(),
    },
  };
  storedPacket.research_v3 ||= {};
  storedPacket.research_v3.report_quality ||= {};
  storedPacket.research_v3.report_quality.synthesis = finalizedSynthesis;
  fs.writeFileSync(packetPath, JSON.stringify(storedPacket, null, 2), "utf8");
  if (fs.existsSync(auditPath)) {
    const storedAudit = JSON.parse(fs.readFileSync(auditPath, "utf8"));
    storedAudit.model_synthesis = finalizedSynthesis;
    storedAudit.report_validation = result.validation;
    fs.writeFileSync(auditPath, JSON.stringify(storedAudit, null, 2), "utf8");
  }
}
console.log(JSON.stringify({
  mode: result.mode,
  attempts: result.attempts,
  validation: result.validation,
  elapsed_ms: Date.now() - startedAt,
  output_dir: target,
}, null, 2));
if (result.validation?.status !== "passed") process.exitCode = 1;
