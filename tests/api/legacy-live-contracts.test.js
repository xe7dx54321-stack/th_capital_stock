import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";


const dbPath = process.env.SMR_LEGACY_CONTRACT_DB;
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

test("legacy GET endpoints retain live response shapes", { skip: !dbPath }, async (t) => {
  process.env.SMR_DB_PATH = dbPath;
  process.env.SMR_ARTIFACT_ROOTS = mkdtempSync(path.join(os.tmpdir(), "smr-legacy-artifacts-"));
  process.env.SMR_PYTHON = process.platform === "win32"
    ? path.join(ROOT, ".venv", "Scripts", "python.exe")
    : path.join(ROOT, ".venv", "bin", "python");
  const { app } = await import(`../../api/app.js?legacy-live=${Date.now()}`);
  const server = await new Promise((resolve) => {
    const instance = app.listen(0, "127.0.0.1", () => resolve(instance));
  });
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    app.locals.workflowRepository.close();
  });
  const baseUrl = `http://127.0.0.1:${server.address().port}`;
  const get = async (route) => {
    const response = await fetch(`${baseUrl}${route}`);
    const body = await response.json();
    assert.equal(response.status, 200, `${route}: ${JSON.stringify(body)}`);
    return body;
  };

  assert.equal((await get("/api/health")).status, "ok");
  assert.ok((await get("/api/dashboard")).summary);
  assert.ok(Array.isArray((await get("/api/value-scores")).scores));
  const stock = await get("/api/stock/300308.SZ");
  assert.equal(stock.tsCode, "300308.SZ");
  assert.ok(stock.report);
  assert.ok(Array.isArray((await get("/api/discoveries")).discoveries));
  const news = await get("/api/news");
  assert.ok(Array.isArray(news.items));
  if (news.items[0]) {
    const detail = await get(`/api/news/${encodeURIComponent(news.items[0].id)}`);
    assert.equal(detail.id, news.items[0].id);
    assert.ok(Array.isArray(detail.insights));
  }
  assert.ok(Array.isArray((await get("/api/phases")).phases));
});
