import { readdirSync, readFileSync, existsSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 获取所有 Phase 配置
function loadAllPhaseConfigs() {
  const configDir = path.resolve(__dirname, "..", "..", "config");
  const files = readdirSync(configDir).filter((f) => /^phase\d+.*\.json$/.test(f));
  const phases = [];
  for (const f of files) {
    try {
      const content = readFileSync(path.join(configDir, f), "utf8");
      const json = JSON.parse(content);
      if (json.phase) {
        phases.push({
          phase_id: json.phase,
          strategy: json.strategy || "",
          research_only: json.research_only || false,
        });
      }
    } catch {}
  }
  return phases.sort((a, b) => {
    const na = parseInt(a.phase_id.replace("phase", ""));
    const nb = parseInt(b.phase_id.replace("phase", ""));
    return na - nb;
  });
}

// 获取 scheduler 运行记录中的 phase 状态
function getSchedulerPhaseRuns() {
  const results = {}; // phase_num -> { latest, count }

  // 1. 尝试从 scheduler runs 目录读取
  const schedDir = path.resolve(__dirname, "..", "..", "10_logs", "scheduler", "runs");
  if (existsSync(schedDir)) {
    try {
      const dirs = readdirSync(schedDir).sort().reverse().slice(0, 50); // 最近 50 次调度
      for (const d of dirs) {
        try {
          // 尝试读取 run.md 或 summary 文件
          const runMdPath = path.join(schedDir, d, "run.md");
          if (existsSync(runMdPath)) {
            const content = readFileSync(runMdPath, "utf8");
            // 找 phase151 等关键词
            const phaseMatches = content.match(/phase\d+/gi) || [];
            for (const m of phaseMatches) {
              const num = parseInt(m.replace("phase", ""));
              if (!results[num]) results[num] = { latest: d, count: 0 };
              results[num].count++;
              // 更新最新时间
              if (d > results[num].latest) results[num].latest = d;
            }
          }
        } catch {}
      }
    } catch {}
  }

  // 2. 从 script_runs.jsonl 读取（脚本名包含 phase 号）
  const logPath = path.resolve(__dirname, "..", "..", "10_logs", "script_runs.jsonl");
  if (existsSync(logPath)) {
    try {
      const content = readFileSync(logPath, "utf8");
      const lines = content.trim().split("\n");
      // 只取最近 500 条
      for (const line of lines.slice(-500)) {
        try {
          const entry = JSON.parse(line);
          if (!entry.time) continue;
          // 找脚本名中的 phase 号
          const phaseMatch = (entry.script || "").match(/phase(\d+)/i);
          if (phaseMatch) {
            const num = parseInt(phaseMatch[1]);
            if (!results[num]) results[num] = { latest: entry.time, count: 0 };
            results[num].count++;
            if (entry.time > results[num].latest) results[num].latest = entry.time;
          }
          // 也从 metrics 里找
          const metricsStr = JSON.stringify(entry.metrics || {});
          const metricsPhases = metricsStr.match(/phase(\d+)/gi) || [];
          for (const m of metricsPhases) {
            const num = parseInt(m.replace("phase", ""));
            if (!results[num]) results[num] = { latest: entry.time, count: 0 };
            results[num].count++;
            if (entry.time > results[num].latest) results[num].latest = entry.time;
          }
        } catch {}
      }
    } catch {}
  }

  return results;
}

export { loadAllPhaseConfigs, getSchedulerPhaseRuns };
