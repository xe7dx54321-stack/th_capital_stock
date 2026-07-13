import { spawn, spawnSync } from "child_process";
import { existsSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";


const PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

function defaultPythonExecutable() {
  if (process.env.SMR_PYTHON) return process.env.SMR_PYTHON;
  const windowsVenv = path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe");
  const unixVenv = path.join(PROJECT_ROOT, ".venv", "bin", "python");
  if (existsSync(windowsVenv)) return windowsVenv;
  if (existsSync(unixVenv)) return unixVenv;
  return process.platform === "win32" ? "python" : "python3";
}

export class WorkflowProcessService {
  constructor({ dbPath, repository, pythonExecutable = defaultPythonExecutable() }) {
    this.dbPath = dbPath;
    this.repository = repository;
    this.pythonExecutable = pythonExecutable;
  }

  ensureMigrations() {
    const result = spawnSync(
      this.pythonExecutable,
      ["-m", "smr_app", "migrate", "--db-path", this.dbPath],
      { cwd: PROJECT_ROOT, encoding: "utf8", windowsHide: true, shell: false }
    );
    if (result.status !== 0) {
      throw new Error((result.stderr || result.stdout || "SQLite migration failed").trim());
    }
  }

  startExistingRun(runId) {
    const child = spawn(
      this.pythonExecutable,
      ["-m", "smr_app", "run-existing", "--run-id", runId, "--db-path", this.dbPath],
      { cwd: PROJECT_ROOT, windowsHide: true, shell: false, stdio: ["ignore", "pipe", "pipe"] }
    );
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout = (stdout + chunk.toString("utf8")).slice(-8000); });
    child.stderr.on("data", (chunk) => { stderr = (stderr + chunk.toString("utf8")).slice(-8000); });
    this.repository.setProcessState(runId, child.pid, "running");
    child.on("error", (error) => {
      this.repository.failIfActive(runId, `Unable to start workflow process: ${error.message}`);
    });
    child.on("close", (code) => {
      this.repository.setProcessState(runId, child.pid, code === 0 ? "exited" : "failed");
      if (code !== 0) {
        this.repository.failIfActive(runId, stderr || stdout || `Workflow process exited with code ${code}`);
      }
    });
    return { pid: child.pid };
  }
}

export { defaultPythonExecutable, PROJECT_ROOT };
