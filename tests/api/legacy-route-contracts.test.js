import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";


const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const source = readFileSync(path.join(ROOT, "api", "legacy-app.js"), "utf8");
const expectedRoutes = [
  ["/api/health", /\{\s*status:\s*["']ok["'],\s*timestamp:/],
  ["/api/dashboard", /summary:\s*\{/],
  ["/api/value-scores", /app\.get\(["']\/api\/value-scores["']/],
  ["/api/stock/:code", /app\.get\(["']\/api\/stock\/:code["']/],
  ["/api/discoveries", /app\.get\(["']\/api\/discoveries["']/],
  ["/api/news", /return \{ items: processed, sources, updatedAt:/],
  ["/api/news/:id", /app\.get\(["']\/api\/news\/:id["']/],
  ["/api/phases", /return \{ phases: mainPhases, updatedAt:/],
];

test("legacy GET route response contracts remain present after bootstrap split", () => {
  for (const [route, responseContract] of expectedRoutes) {
    assert.match(source, new RegExp(`app\\.get\\(["']${route.replaceAll("/", "\\/").replace(":", "\\:")}["']`));
    assert.match(source, responseContract);
  }
});

test("server bootstrap stays small and delegates application assembly", () => {
  const serverSource = readFileSync(path.join(ROOT, "api", "server.js"), "utf8");
  assert.ok(serverSource.split(/\r?\n/).length < 100);
  assert.match(serverSource, /import \{ app, DB_PATH \} from "\.\/app\.js"/);
});
